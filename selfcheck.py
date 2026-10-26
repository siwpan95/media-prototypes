#!/usr/bin/env python3
"""无头自检：元胞自动机演化、Mandelbrot 分形、程序化音频与电平提取。

`ddd (2).py` 没有 `if __name__ == "__main__"` 守卫，一 import 就会创建 Tkinter
窗口并开始渲染视频，因此本自检只从源码中提取「纯定义」（函数 / 类 / 常量），
在独立命名空间里执行，不触发 GUI、不写视频文件。
运行：python selfcheck.py
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "ddd (2).py"

# 纯逻辑不需要、且导入后会拉起渲染/GUI 的模块
SKIP_IMPORTS = {"moviepy", "tkinter"}


def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _root_module(node):
    if isinstance(node, ast.Import):
        return {alias.name.split(".")[0] for alias in node.names}
    return {(node.module or "").split(".")[0]}


def _safe_constant_assign(node):
    """只保留纯常量赋值，避免执行 np.random.* / init_particles() 等运行时语句。"""
    if not all(isinstance(t, ast.Name) for t in node.targets):
        return False
    return not any(
        isinstance(n, (ast.Call, ast.Attribute, ast.Subscript)) for n in ast.walk(node.value)
    )


def load_logic_namespace():
    if not ENTRY.is_file():
        fail(f"找不到入口文件: {ENTRY}")
    tree = ast.parse(ENTRY.read_text(encoding="utf-8"), filename=str(ENTRY))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if _root_module(node) & SKIP_IMPORTS:
                continue
            body.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body.append(node)
        elif isinstance(node, ast.Assign) and _safe_constant_assign(node):
            body.append(node)

    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "__name__": "ddd2_logic",
        "__file__": str(ENTRY),
        # 与「未安装 numba」时的降级路径一致
        "HAS_NUMBA": False,
        "jit": None,
    }
    try:
        exec(compile(module, str(ENTRY), "exec"), namespace)
    except Exception as exc:  # pragma: no cover
        fail(f"执行入口纯逻辑定义失败: {exc!r}")
    return namespace


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover
        fail(f"缺少 numpy: {exc}")

    ns = load_logic_namespace()
    for name in ("update_ca_numpy", "generate_mandelbrot_chunked",
                 "make_audio_clip", "get_audio_levels"):
        if name not in ns:
            fail(f"入口中未找到核心函数: {name}")

    update_ca = ns["update_ca"]

    # ---------- 1. Game of Life 演化（状态推进） ----------
    blinker = np.zeros((5, 5), dtype=np.uint8)
    blinker[2, 1:4] = 1
    after_one = update_ca(blinker)
    expected = np.zeros((5, 5), dtype=np.uint8)
    expected[1:4, 2] = 1
    if not np.array_equal(after_one, expected):
        fail("闪烁器（blinker）第一步演化结果不符")
    if not np.array_equal(update_ca(after_one), blinker):
        fail("闪烁器（blinker）第二步未回到初始形态（周期 2 失败）")

    block = np.zeros((5, 5), dtype=np.uint8)
    block[1:3, 1:3] = 1
    if not np.array_equal(update_ca(block), block):
        fail("方块（block）静物未保持不变")

    # ---------- 2. Mandelbrot 分形数值 ----------
    fr = ns["generate_mandelbrot_chunked"](60, 40, max_iter=30)
    if fr.shape != (40, 60) or fr.dtype != np.float32:
        fail(f"Mandelbrot 形状/类型不符: {fr.shape} {fr.dtype}")
    if float(fr.min()) < 0.0 or float(fr.max()) > 1.0 or not np.all(np.isfinite(fr)):
        fail("Mandelbrot 取值越界")
    if float(fr[18:22, 28:32].max()) != 0.0:
        fail("Mandelbrot 集合内部点应为 0（未被截断）")
    if float(fr.max()) == 0.0:
        fail("Mandelbrot 全为 0，外部点未计算")
    fr2 = ns["generate_mandelbrot_chunked"](60, 40, max_iter=30)
    if not np.array_equal(fr, fr2):
        fail("Mandelbrot 相同参数结果不稳定")

    # ---------- 3. 程序化音频 + 电平提取 ----------
    audio, sample_rate = ns["make_audio_clip"]()
    if sample_rate != 44100 or audio.shape != (44100 * ns["DURATION"], 2):
        fail(f"音频形状/采样率不符: {audio.shape} @ {sample_rate}")
    # 单声道先 clip 到 [-1,1]，再乘 0.9~1.1 的立体声摆幅，故峰值上限为 1.1
    if not np.all(np.isfinite(audio)) or float(np.max(np.abs(audio))) > 1.1 + 1e-6:
        fail("音频含 NaN 或超出 [-1.1, 1.1] 限幅")
    if np.array_equal(audio[:, 0], audio[:, 1]):
        fail("左右声道完全相同，立体声处理未生效")
    peak, rms = ns["get_audio_levels"](audio[:, 0], 1.0, sample_rate)
    if peak <= 0 or rms <= 0 or rms > peak:
        fail(f"电平提取异常: peak={peak}, rms={rms}")
    if ns["get_audio_levels"](audio[:, 0], 10_000.0, sample_rate) != (0, 0):
        fail("超出音频末尾时电平应为 (0, 0)")

    duration = ns["DURATION"]
    print(
        f"selfcheck ok: Game of Life 演化（闪烁器周期2/方块静物）、"
        f"Mandelbrot 40x60 数值边界与可复现、{duration}s 立体声音频生成与峰值/RMS 提取"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
