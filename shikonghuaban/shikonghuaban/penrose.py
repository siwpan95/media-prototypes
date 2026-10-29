"""
时空画板 — Penrose 几何 + 路径粒子

Penrose 坐标变换用于将无限大的史瓦西时空压缩到有限区域:
  原始范围  u ∈ (-∞, ∞), v ∈ (-∞, ∞)
  变换后    P = arctan(u) ∈ (-π/2, π/2), Q = arctan(v) ∈ (-π/2, π/2)

这类似于 Penrose-Carter 图的紧致化 (compactification)，
将类光无限远映射到有限边界。

同时还提供沿 Penrose 几何路径运动的粒子系统。
"""

import math
import random
import pygame
from collections import deque
from .config import WIDTH, HEIGHT, CENTER, COLOR


# ============================================================
#  Penrose 坐标变换（模块级函数，无状态）
# ============================================================

def penrose(u, v):
    """
    Penrose 变换: (u, v) → (P, Q)
    
    使用 arctan 将无限域压缩到有限域:
    P = arctan(u) ∈ (-π/2, π/2)
    Q = arctan(v) ∈ (-π/2, π/2)
    
    在原数学中，(u, v) 是 Kruskal-Szekeres 坐标，
    经过 Penrose 紧致化后映射到有限区域。
    """
    return math.atan(u), math.atan(v)


def to_screen(P, Q):
    """
    Penrose 坐标 → 屏幕坐标
    
    将 (-π/2, π/2) × (-π/2, π/2) 映射到屏幕，
    以黑洞中心为原点。
    """
    scale = min(WIDTH, HEIGHT) * 0.28
    cx, cy = CENTER
    return int(cx + P * scale), int(cy - Q * scale)


# ============================================================
#  路径粒子 — 沿 Penrose 几何路径运动
# ============================================================

class PenroseParticle:
    """
    沿 Penrose 几何路径运动的粒子。
    
    路径类型:
    1. 对角线 (45° 线) — 类光测地线
    2. 奇点曲线 (u² - v² = 1) — 史瓦西时空中 r=0 的边界
    """

    # 预渲染光晕精灵的基础半径（27 圈需要按比例缩放）
    GLOW_BASE = 48

    def __init__(self):
        self.reset()
        self.trail = deque(maxlen=25)
        # 预渲染光晕精灵（白色实心圆，按音量缩放/调 alpha 复用）
        g = PenroseParticle.GLOW_BASE
        self._glow_sprite = pygame.Surface((g * 2, g * 2), pygame.SRCALPHA)
        pygame.draw.circle(self._glow_sprite, (*COLOR, 255), (g, g), g)

    def reset(self):
        self.age = 0
        self.max_age = random.randint(300, 800)
        self.t = 0
        self.dt = random.uniform(0.001, 0.005)
        self.path = random.choice([
            # 路径1：45° 对角线 (类光方向)
            lambda t: (0.2 + t * 3, 0.2 + t * 3),
            # 路径2：45° 对角线 (另一方向)
            lambda t: (0.2 + t * 3, -0.2 - t * 3),
            # 路径3：奇点曲线 (r=0 边界)
            lambda t: (1 + t * 2, math.sqrt((1 + t * 2) ** 2 - 1))
        ])
        self.size = random.uniform(0.8, 1.5)

    def update(self, speed=1.0):
        self.age += 1
        self.t += self.dt * speed
        if self.t > 1 or self.age > self.max_age:
            self.reset()
            return

        u, v = self.path(self.t)
        P, Q = penrose(u, v)
        x, y = to_screen(P, Q)
        self.trail.append((x, y, self.age / self.max_age))

    def draw(self, surf, volume=0.5):
        if not self.trail:
            return

        # ── 光晕效果（缩放预渲染精灵，避免每帧新建 Surface） ──
        if len(self.trail) >= 2:
            last_x, last_y, _ = self.trail[-1]
            glow_size = int(self.size * 6 * (1 + volume * 0.8))
            if glow_size > 2:
                glow_alpha = int(20 * (1 + volume * 0.5))
                scaled = pygame.transform.scale(
                    self._glow_sprite, (glow_size, glow_size)
                )
                scaled.set_alpha(glow_alpha)
                surf.blit(scaled,
                          (int(last_x) - glow_size // 2, int(last_y) - glow_size // 2),
                          special_flags=pygame.BLEND_ADD)

        # ── 拖尾粒子（直接绘制，零 Surface 分配） ──
        for i, (x, y, alpha_ratio) in enumerate(self.trail):
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                continue

            t = i / len(self.trail)
            alpha = int(255 * alpha_ratio * t * (0.8 + volume * 0.4))

            # 颜色随生命周期和音频变化
            life_t = 1.0 - (self.age / self.max_age)
            r = int(min(255, COLOR[0] * (1.0 + life_t * 0.4 + volume * 0.3)))
            g = int(min(255, COLOR[1] * (0.9 + life_t * 0.2 + volume * 0.2)))
            b = int(min(255, COLOR[2] * (0.9 + life_t * 0.2 + volume * 0.2)))

            size = int(self.size * t * 3 * (1 + volume * 0.5))
            if size > 0:
                pygame.draw.circle(surf, (r, g, b, alpha),
                                   (int(x), int(y)), max(1, size // 2))
