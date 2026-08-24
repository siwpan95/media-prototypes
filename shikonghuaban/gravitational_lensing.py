"""
时空画板 — 引力透镜效果

基于史瓦西黑洞的简化引力透镜渲染:
  - 背景星场光线弯曲
  - 爱因斯坦环
  - 多重成像效果
  - 音频响应星场闪烁
"""

import math
import random
import pygame
from .config import (
    WIDTH, HEIGHT, CENTER, BG,
    BL_SCHWARZSCHILD_R, BL_PHOTON_SPHERE_R, BL_LENS_STRENGTH
)
from .blackhole_physics import dist_to_bh, angle_to_bh


class GravitationalLensing:
    """黑洞引力透镜效果"""

    def __init__(self, num_stars: int = 800):
        self.num_stars = num_stars
        self.stars = self._generate_starfield(num_stars)

        # 爱因斯坦环粒子
        self.einstein_particles = []
        self.ring_angle = 0.0

    def _generate_starfield(self, n: int) -> list:
        """生成随机背景星场"""
        stars = []
        cx, cy = CENTER
        for _ in range(n):
            # 在整个屏幕上均匀分布
            x = random.uniform(0, WIDTH)
            y = random.uniform(0, HEIGHT)
            # 但远离黑洞中心区域要足够密，以显示透镜效果
            r = math.hypot(x - cx, y - cy)
            brightness = random.uniform(0.3, 1.0)
            size = random.uniform(0.5, 2.0)
            # 颜色变化 (白/蓝白/黄白)
            color_choice = random.random()
            if color_choice < 0.6:
                color = (255, 255, 255)
            elif color_choice < 0.85:
                color = (180, 200, 255)
            else:
                color = (255, 240, 200)

            stars.append({
                'true_x': x,
                'true_y': y,
                'true_r': r,
                'brightness': brightness,
                'size': size,
                'color': color,
            })
        return stars

    def _lens_position(self, true_x: float, true_y: float) -> tuple:
        """
        计算星点的透镜后视位置。
        返回 (apparent_x, apparent_y) 或 None (被黑洞遮蔽)。
        """
        r = dist_to_bh(true_x, true_y)

        # 视界内/太近 — 被遮蔽
        if r < BL_SCHWARZSCHILD_R * 1.02:
            return None

        theta = angle_to_bh(true_x, true_y)
        cx, cy = CENTER

        # 偏折角计算 (小角度近似)
        # α ≈ 2r_s / b   (b = 碰撞参数)
        if r > BL_SCHWARZSCHILD_R * 1.02:
            alpha = (2.0 * BL_SCHWARZSCHILD_R) / r
        else:
            alpha = math.pi

        alpha = min(alpha * BL_LENS_STRENGTH * 0.5, math.pi * 0.8)

        # 视位置: 光线向外弯曲
        # 靠近光子球的区域会产生爱因斯坦环效果
        if r < BL_PHOTON_SPHERE_R * 1.3:
            # 光子球附近 — 产生环效应
            apparent_r = BL_PHOTON_SPHERE_R + (r - BL_SCHWARZSCHILD_R) * 3.0
            apparent_r = min(apparent_r, BL_PHOTON_SPHERE_R * 2.0)
        else:
            # 正常偏折
            apparent_r = r + alpha * BL_SCHWARZSCHILD_R * 0.8

        ax = cx + apparent_r * math.cos(theta)
        ay = cy + apparent_r * math.sin(theta)

        return ax, ay

    def _secondary_image(self, true_x: float, true_y: float) -> tuple:
        """
        计算二次像（光子绕黑洞半圈后到达的像）。
        只有离黑洞足够近的源才会产生明显的二次像。
        """
        r = dist_to_bh(true_x, true_y)

        if r > BL_PHOTON_SPHERE_R * 2.5 or r < BL_SCHWARZSCHILD_R * 1.1:
            return None

        theta = angle_to_bh(true_x, true_y)
        cx, cy = CENTER

        # 二次像在黑洞另一侧，更暗
        r2 = BL_PHOTON_SPHERE_R * 1.1
        ax = cx + r2 * math.cos(theta + math.pi)
        ay = cy + r2 * math.sin(theta + math.pi)

        return ax, ay

    def render(self, screen: pygame.Surface, volume: float, time_ms: int):
        """
        渲染引力透镜效果。
        """
        cx, cy = CENTER

        # 更新爱因斯坦环角度
        self.ring_angle += 0.002 + volume * 0.01

        # 绘制透镜后的星场
        for star in self.stars:
            result = self._lens_position(star['true_x'], star['true_y'])
            if result is None:
                # 可能产生爱因斯坦环效果
                r = dist_to_bh(star['true_x'], star['true_y'])
                if r < BL_SCHWARZSCHILD_R * 1.5 and r > BL_SCHWARZSCHILD_R:
                    # 在光子球附近形成环
                    ring_r = BL_PHOTON_SPHERE_R * 1.1 + random.uniform(-3, 3)
                    theta = angle_to_bh(star['true_x'], star['true_y']) + self.ring_angle * 0.5
                    ax = cx + ring_r * math.cos(theta)
                    ay = cy + ring_r * math.sin(theta)
                else:
                    continue
            else:
                ax, ay = result

            if not (0 <= ax < WIDTH and 0 <= ay < HEIGHT):
                continue

            # 亮度：透镜可以放大亮度
            r = star['true_r']
            if r < BL_PHOTON_SPHERE_R * 2.0:
                magnification = max(0.3, (BL_PHOTON_SPHERE_R / max(r, BL_SCHWARZSCHILD_R)))
            else:
                magnification = 1.0

            alpha = int(255 * star['brightness'] * magnification * (0.8 + volume * 0.4))
            alpha = max(0, min(255, alpha))
            size = star['size'] * (1.0 + (magnification - 1.0) * 0.3)

            if size > 0.3 and alpha > 5:
                color = star['color']
                if size >= 1.5:
                    pygame.draw.circle(screen, (*color, alpha),
                                       (int(ax), int(ay)), max(1, int(size)))
                else:
                    # 小星点用单个像素
                    screen.set_at((int(ax), int(ay)),
                                  (min(255, color[0]), min(255, color[1]),
                                   min(255, color[2]), alpha))

            # 绘制二次像（如果存在）
            sec = self._secondary_image(star['true_x'], star['true_y'])
            if sec:
                sx, sy = sec
                if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                    sec_alpha = int(alpha * 0.15)
                    if sec_alpha > 3:
                        pygame.draw.circle(screen,
                                           (*star['color'], sec_alpha),
                                           (int(sx), int(sy)), 1)

        # 爱因斯坦环高亮
        self._render_einstein_ring(screen, volume)

    def _render_einstein_ring(self, screen: pygame.Surface, volume: float):
        """渲染爱因斯坦环（光子球处的不稳定光环）"""
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        cx, cy = CENTER

        # 主环
        ring_r = BL_PHOTON_SPHERE_R * 1.05
        ring_alpha = int(30 * (0.6 + volume * 0.8))
        if ring_alpha > 0:
            pygame.draw.circle(glow, (180, 200, 255, ring_alpha),
                               CENTER, int(ring_r), width=3)

        # 外环晕
        outer_r = ring_r + 15
        outer_alpha = int(15 * (0.5 + volume * 0.5))
        if outer_alpha > 0:
            pygame.draw.circle(glow, (150, 170, 240, outer_alpha),
                               CENTER, int(outer_r), width=5)

        screen.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)
