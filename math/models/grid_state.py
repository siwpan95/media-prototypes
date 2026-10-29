"""模型层 - 网格状态管理"""
import numpy as np


class GridState:
    """管理细胞自动机的网格状态"""

    def __init__(self, width: int, height: int, cell_size: int = 2):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.u = None
        self.v = None
        self.iteration = 0
        self.reset()

    def reset(self):
        """重置网格到初始状态"""
        self.u = np.ones((self.height, self.width))
        self.v = np.zeros((self.height, self.width))
        # 中心方形扰动
        r = 10
        cx, cy = self.width // 2, self.height // 2
        self.v[cy - r:cy + r, cx - r:cx + r] = 1.0
        self.iteration = 0

    def set_state(self, u: np.ndarray, v: np.ndarray):
        """设置自定义初始状态"""
        if u.shape != v.shape:
            raise ValueError(f"u/v shape mismatch: {u.shape} vs {v.shape}")
        self.u = np.clip(u, 0, 1)
        self.v = np.clip(v, 0, 1)
        self.iteration = 0

    def update(self, new_u: np.ndarray, new_v: np.ndarray):
        """更新网格状态"""
        self.u = np.clip(new_u, 0, 1)
        self.v = np.clip(new_v, 0, 1)
        self.iteration += 1

    def increment_iteration(self):
        """增加迭代计数"""
        self.iteration += 1
