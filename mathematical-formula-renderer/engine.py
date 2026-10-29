"""
CA 渲染引擎核心模块 —— 与具体规则/公式完全无关的演化引擎。
负责：JSON 配方解析、公式编译、网格演化、颜色映射。
"""

import json
import re

import numpy as np
from scipy.ndimage import convolve
from asteval import Interpreter


class CARenderEngine:
    """连续细胞自动机渲染引擎。

    通过 JSON 配方配置，支持：
    - 数学公式初始化网格
    - 数学公式演化规则
    - 数学公式颜色映射
    - 周期循环重置
    - 可配置邻域核
    """

    def __init__(self, config_path=None):
        self._compile_cache = {}
        self.config = {}
        self.grid = None
        self.rule_func = None
        self.color_funcs = {}
        self.t = 0
        self.w, self.h = 0, 0
        self.wrap = True
        self.kernel = None
        self.fps = 30
        self.steps_per_frame = 1
        self.x_grid = None
        self.y_grid = None
        self.cycle_steps = 0
        self.init_func = None
        self.init_expr = None
        self._rgb_hw = None
        self._rgb_wh = None
        self._total_cycles = 0  # 已完成的循环次数
        if config_path is not None:
            self.load_config(config_path)

    # ================================================================
    #  配置加载
    # ================================================================
    def load_config(self, path):
        """热插拔入口：从 JSON 加载完整配方"""
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # --- 网格参数 ---
        g = self.config['grid']
        self.w, self.h = g['width'], g['height']
        self.wrap = g.get('wrap', True)

        # --- 初始状态公式 ---
        init_expr = g['initial']['expression']
        self.init_expr = init_expr
        self.init_func = self._compile(init_expr, ['x', 'y', 'i', 'j', 'random'])
        self._reset_grid()

        # --- 演化规则公式 ---
        ev = self.config['evolution']
        var_names = ev.get('variables', ['c', 'sum_n', 'avg_n', 'x', 'y', 't'])
        self.rule_func = self._compile(ev['rule'], var_names)

        # --- 颜色映射公式 ---
        col = self.config['color']
        self.color_funcs = {}
        for channel in ['red', 'green', 'blue']:
            expr = col.get(channel, '0.0')
            self.color_funcs[channel] = self._compile(expr, ['v', 'x', 'y'])

        # --- 邻域核 ---
        nb = self.config.get('neighborhood', {})
        radius = nb.get('radius', 1)
        size = 2 * radius + 1
        self.kernel = np.ones((size, size), dtype=np.float32)
        self.kernel[radius, radius] = 0

        # --- Tick 配置 ---
        tick = self.config.get('tick', {})
        self.fps = tick.get('fps', 30)
        self.steps_per_frame = tick.get('steps_per_frame', 1)

        # --- 循环配置 ---
        cycle = self.config.get('cycle', {})
        self.cycle_steps = cycle.get('steps', 0)

        self.t = 0
        self._total_cycles = 0
        self._build_coordinate_grids()
        self._prealloc_color_arrays()

        cycle_info = f", cycle={self.cycle_steps}步" if self.cycle_steps > 0 else ""
        desc = self.config.get('description', '')
        print(f"[引擎] 配方已加载: {self.config.get('name', '未命名')} "
              f"({self.w}×{self.h}, t={self.t}{cycle_info})")
        if desc:
            print(f"       {desc}")

    def _build_coordinate_grids(self):
        """预计算归一化坐标网格"""
        self.x_grid = np.broadcast_to(
            np.linspace(0, 1, self.w, endpoint=False, dtype=np.float64).reshape(1, -1),
            (self.h, self.w)
        ).copy()
        self.y_grid = np.broadcast_to(
            np.linspace(0, 1, self.h, endpoint=False, dtype=np.float64).reshape(-1, 1),
            (self.h, self.w)
        ).copy()

    def _prealloc_color_arrays(self):
        """预分配颜色输出数组"""
        self._rgb_hw = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        self._rgb_wh = np.zeros((self.w, self.h, 3), dtype=np.uint8)

    # ================================================================
    #  公式编译器
    # ================================================================
    def _compile(self, expr, var_names):
        """编译数学表达式 —— 纯数学用 numpy 向量化求值，含 and/or 的退回逐像素"""
        cache_key = (expr, tuple(var_names))
        if cache_key in self._compile_cache:
            return self._compile_cache[cache_key]

        has_logic = bool(re.search(r'\b(and|or|not)\b', expr))

        processed = expr
        for _ in range(5):
            new_expr = re.sub(
                r'(.+)\s+if\s+(.+?)\s+else\s+(.+)',
                r'where(\2, \1, \3)',
                processed
            )
            if new_expr == processed:
                break
            processed = new_expr

        processed = re.sub(r'\bmin\(', 'minimum(', processed)
        processed = re.sub(r'\bmax\(', 'maximum(', processed)

        if has_logic:
            func = self._compile_logic(processed, var_names)
        else:
            func = self._compile_numeric(processed)

        self._compile_cache[cache_key] = func
        return func

    def _compile_logic(self, processed, var_names):
        ae = Interpreter()
        ae.symtable['sin'] = np.sin
        ae.symtable['cos'] = np.cos
        ae.symtable['exp'] = np.exp
        ae.symtable['abs'] = abs
        ae.symtable['sqrt'] = np.sqrt
        ae.symtable['random'] = np.random.random
        ae.symtable['clip'] = np.clip
        ae.symtable['min'] = min
        ae.symtable['max'] = max
        ae.symtable['where'] = np.where

        def func(**kwargs):
            first_val = next(iter(kwargs.values()), None)
            if isinstance(first_val, np.ndarray) and first_val.ndim == 2:
                h, w = first_val.shape
                result = np.zeros((h, w), dtype=np.float64)
                for i in range(h):
                    for j in range(w):
                        for k in var_names:
                            v = kwargs.get(k)
                            ae.symtable[k] = v[i, j] if isinstance(v, np.ndarray) and v.ndim == 2 else v
                        try:
                            result[i, j] = ae.eval(processed) or 0.0
                        except Exception:
                            result[i, j] = 0.0
                return result
            else:
                for k in var_names:
                    if k in kwargs:
                        ae.symtable[k] = kwargs[k]
                try:
                    return np.float64(ae.eval(processed) or 0.0)
                except Exception:
                    return np.float64(0.0)
        return func

    def _compile_numeric(self, processed):
        ns = {
            'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
            'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
            'abs': np.abs, 'pi': np.pi, 'e': np.e,
            'minimum': np.minimum, 'maximum': np.maximum,
            'where': np.where, 'clip': np.clip,
        }

        def func(**kwargs):
            try:
                result = eval(processed, {"__builtins__": {}}, {**ns, **kwargs})
                return np.asarray(result, dtype=np.float64)
            except KeyboardInterrupt:
                raise
            except Exception:
                return np.float64(0.0)
        return func

    # ================================================================
    #  网格操作
    # ================================================================
    def _reset_grid(self):
        """用初始化公式重新生成网格"""
        self.grid = np.zeros((self.h, self.w), dtype=np.float32)
        for i in range(self.h):
            for j in range(self.w):
                x = j / self.w
                y = i / self.h
                val = self.init_func(x=x, y=y, i=i, j=j, random=np.random.random)
                self.grid[i, j] = np.clip(val, 0.0, 1.0)

    def reset(self):
        """公开重置接口"""
        self._reset_grid()
        self.t = 0
        self._total_cycles = 0

    # ================================================================
    #  演化
    # ================================================================
    def step(self):
        """演化一步，若配置了 cycle_steps 则在达到周期时自动重置"""
        if self.cycle_steps > 0 and self.t >= self.cycle_steps:
            self._reset_grid()
            self.t = 0
            self._total_cycles += 1
            return

        mode = 'wrap' if self.wrap else 'constant'
        sum_n = convolve(self.grid, self.kernel, mode=mode, cval=0.0, axes=(-2, -1))
        avg_n = sum_n / self.kernel.sum()

        val = self.rule_func(
            c=self.grid, sum_n=sum_n, avg_n=avg_n,
            x=self.x_grid, y=self.y_grid, t=np.float64(self.t),
            i=self.y_grid * self.h, j=self.x_grid * self.w
        )
        val = np.asarray(val, dtype=np.float32)
        if val.shape != (self.h, self.w):
            val = np.broadcast_to(val.ravel()[0:1], (self.h, self.w)).astype(np.float32)
        self.grid = np.clip(val, 0.0, 1.0)
        self.t += 1

    def step_n(self, n):
        """演化 n 步（批量）"""
        for _ in range(n):
            self.step()

    def get_grid_stats(self):
        """获取网格统计信息"""
        return {
            'min': float(self.grid.min()),
            'max': float(self.grid.max()),
            'mean': float(self.grid.mean()),
            'std': float(self.grid.std()),
            'alive': float((self.grid > 0.01).mean()),
        }

    # ================================================================
    #  颜色映射
    # ================================================================
    def _eval_channel(self, func, v):
        """计算单个颜色通道，返回 (h, w) 的 0~1 float64 数组"""
        ch = func(v=v, x=self.x_grid, y=self.y_grid)
        ch = np.asarray(ch, dtype=np.float64)
        if ch.shape != (self.h, self.w):
            ch = np.broadcast_to(ch.ravel()[0:1], (self.h, self.w)).astype(np.float64)
        return np.clip(ch, 0.0, 1.0)

    def get_color_array(self):
        """返回形状 (h, w, 3) 的 uint8 RGB 数组"""
        v = self.grid.astype(np.float64)
        r = self._eval_channel(self.color_funcs['red'], v)
        g = self._eval_channel(self.color_funcs['green'], v)
        b = self._eval_channel(self.color_funcs['blue'], v)
        arr = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        arr[:, :, 0] = (r * 255).astype(np.uint8)
        arr[:, :, 1] = (g * 255).astype(np.uint8)
        arr[:, :, 2] = (b * 255).astype(np.uint8)
        return arr

    def fill_color_wh(self, out):
        """把当前帧颜色直接写到 out 数组，out 必须是 (w, h, 3) uint8。"""
        v = self.grid.astype(np.float64)
        r = self._eval_channel(self.color_funcs['red'], v)
        g = self._eval_channel(self.color_funcs['green'], v)
        b = self._eval_channel(self.color_funcs['blue'], v)
        out[:, :, 0] = (r.T * 255).astype(np.uint8)
        out[:, :, 1] = (g.T * 255).astype(np.uint8)
        out[:, :, 2] = (b.T * 255).astype(np.uint8)
