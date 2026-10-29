"""模型层 - 公式引擎"""
import numpy as np
import os
import importlib.util
import inspect
from typing import Callable, Optional, Tuple, Any
from tkinter import Tk, filedialog


class FormulaEngine:
    """公式加载和执行引擎"""

    def __init__(self):
        self.update_func: Optional[Callable] = None
        self.display_func: Optional[Callable] = None
        self.init_func: Optional[Callable] = None
        self.formula_name: str = "Gray-Scott"
        self._set_default_formula()

    def _set_default_formula(self):
        """设置默认的 Gray-Scott 公式"""
        def laplacian(grid, dx):
            return (np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
                    np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) -
                    4 * grid) / (dx**2)

        def gray_scott_update(u, v, Du, Dv, F, k, dt, dx):
            Lu = laplacian(u, dx)
            Lv = laplacian(v, dx)
            uvv = u * v * v
            new_u = u + (Du * Lu - uvv + F * (1 - u)) * dt
            new_v = v + (Dv * Lv + uvv - (F + k) * v) * dt
            return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)

        self.update_func = gray_scott_update
        self.formula_name = "Gray-Scott"
        self.display_func = None
        self.init_func = None

    def restore_default(self):
        """恢复默认公式"""
        self._set_default_formula()

    def load_from_file(self) -> bool:
        """从文件加载公式，返回是否成功"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title="Select Python Formula File",
            filetypes=[("Python files", "*.py")]
        )
        root.destroy()

        if not file_path:
            return False

        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            formula_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(formula_module)

            if not hasattr(formula_module, 'update'):
                raise AttributeError("Formula file missing 'update' function")

            new_func = formula_module.update
            sig = inspect.signature(new_func)
            params = list(sig.parameters.keys())

            if len(params) == 2:
                def wrapper(u, v, Du, Dv, F, k, dt, dx):
                    return new_func(u, v)
                self.update_func = wrapper
            else:
                self.update_func = new_func

            self.formula_name = getattr(formula_module, 'NAME', os.path.basename(file_path))
            self.display_func = getattr(formula_module, 'get_display', None)
            self.init_func = getattr(formula_module, 'init_state', None)

            print(f"Loaded formula: {self.formula_name}")
            return True

        except Exception as e:
            print(f"Formula load error: {e}")
            return False

    def generate_template(self, file_path: str) -> bool:
        """生成公式模板"""
        if not file_path:
            return False

        template_content = '''# Custom Cellular Automata Formula
import numpy as np

NAME = "My Model"   # Optional, displayed on the UI

def update(u, v, Du, Dv, F, k, dt, dx):
    """
    Called every frame, return new (u, v)
    Parameters:
        u, v : current state (2D numpy arrays)
        Du, Dv, F, k, dt, dx : predefined parameters (can be ignored)
    Notes:
        - Do not hardcode grid size, use u.shape
        - Return values will be clipped to [0, 1] (optional)
    """
    # Example: simple diffusion + reaction
    Lu = (np.roll(u, 1, 0) + np.roll(u, -1, 0) +
          np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4*u) / dx**2
    new_u = u + Du * Lu * dt
    new_v = v * 0.99  # slow decay
    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)

# Optional: custom display content (default displays v)
# def get_display(v):
#     return v * 0.5  # can return u, v, u*v, etc.

# Optional: custom initial state
# def init_state(H, W):
#     u = np.random.rand(H, W)
#     v = np.zeros((H, W))
#     v[H//2-5:H//2+5, W//2-5:W//2+5] = 1.0
#     return u, v
'''
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"Template saved to: {file_path}")
            return True
        except Exception as e:
            print(f"Template save error: {e}")
            return False

    def execute_update(self, u: np.ndarray, v: np.ndarray,
                       Du: float, Dv: float, F: float,
                       k: float, dt: float, dx: float) -> Tuple[np.ndarray, np.ndarray]:
        """执行公式更新"""
        return self.update_func(u, v, Du, Dv, F, k, dt, dx)

    def get_display_array(self, v: np.ndarray) -> np.ndarray:
        """获取显示用的数组"""
        if self.display_func is not None:
            try:
                return self.display_func(v)
            except:
                return v
        return v

    def get_init_state(self, H: int, W: int) -> Tuple[np.ndarray, np.ndarray]:
        """获取初始化状态"""
        if self.init_func is not None:
            try:
                return self.init_func(H, W)
            except:
                pass
        return None, None
