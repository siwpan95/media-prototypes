# 3D Spiral Projection Formula
import numpy as np

NAME = "3D Spiral"

# 时间计数器
_t = 0

def update(u, v, Du, Dv, F, k, dt, dx):
    global _t
    _t += dt * 2  # 调整速度

    H, W = u.shape
    y, x = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')

    cx, cy = W // 2, H // 2
    dx_grid = x - cx
    dy_grid = y - cy

    angle = np.arctan2(dy_grid, dx_grid)
    radius = np.sqrt(dx_grid**2 + dy_grid**2)

    # 3D螺旋线参数
    a = 3.0      # 螺旋密度
    b = 15       # 旋转速度

    # 随时间变化的螺旋线
    spiral = np.sin(b * angle + a * radius * 0.1 + _t)

    # 拉普拉斯扩散
    Lu = (np.roll(u, 1, 0) + np.roll(u, -1, 0) +
          np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4*u) / dx**2
    Lv = (np.roll(v, 1, 0) + np.roll(v, -1, 0) +
          np.roll(v, 1, 1) + np.roll(v, -1, 1) - 4*v) / dx**2

    # 螺旋引导
    new_u = u + Du * Lu * dt + 0.15 * (spiral - u) * dt
    new_v = v + Dv * Lv * dt + 0.15 * (spiral - v) * dt

    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)
