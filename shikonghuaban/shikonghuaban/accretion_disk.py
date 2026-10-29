"""
时空画板 — 吸积盘可视化

模拟史瓦西黑洞周围的薄吸积盘:
  - 多层同心环，温度从内到外递减
  - 相对论多普勒束流（旋转方向一侧更亮/蓝）
  - 引力红移衰减
  - 音频响应驱动亮度和旋转速度
"""

import math
import random
import pygame
from .config import (
    WIDTH, HEIGHT, CENTER, BG,
    BL_SCHWARZSCHILD_R, BL_ISCO_R, BL_DISK_OUTER_R,
    BL_DOPPLER_STRENGTH
)
from .blackhole_physics import (
    dist_to_bh, angle_to_bh, radial_unit, tangential_unit,
    accretion_temperature, relativistic_doppler
)


class AccretionDisk:
    """史瓦西黑洞吸积盘"""

    def __init__(self, num_rings: int = 60, particles_per_ring: int = 200):
        self.num_rings = num_rings
        self.particles_per_ring = particles_per_ring
        self.rotation_angle = 0.0  # 整体旋转角度（音频驱动）

        # 预计算各环参数
        self.rings = []
        for i in range(num_rings):
            t = i / (num_rings - 1)  # 0=内圈, 1=外圈
            r = BL_ISCO_R + t * (BL_DISK_OUTER_R - BL_ISCO_R)
            # 环的粒子数（内圈更密）
            n = int(particles_per_ring * (1.0 - t * 0.7))
            # 环上各粒子的角度偏移（随机分布）
            offsets = [random.uniform(0, math.pi * 2) for _ in range(n)]
            self.rings.append({
                'radius': r,
                'count': n,
                'offsets': offsets,
                'temp': accretion_temperature(r),
            })

        # 粒子表面缓存（用于添加式混合）
        self._glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # ═══════════════════════════════════════════════════════════
    #  温度 → 颜色
    # ═══════════════════════════════════════════════════════════

    def _temp_to_color(self, temp: float, doppler_factor: float = 1.0) -> tuple:
        """
        温度 + 多普勒因子 → RGB 颜色
        高温: 蓝白 (20000K+)
        中温: 黄白 (~8000K)
        低温: 橙红 (~3000K)
        """
        # 基础温度映射
        if temp > 0.85:
            r, g, b = 180, 200, 255  # 蓝白 (内盘)
        elif temp > 0.7:
            r, g, b = 230, 240, 255  # 白
        elif temp > 0.5:
            r, g, b = 255, 240, 200  # 黄白
        elif temp > 0.3:
            r, g, b = 255, 200, 120  # 橙黄
        elif temp > 0.15:
            r, g, b = 255, 140, 60  # 橙
        else:
            r, g, b = 220, 80, 30  # 红 (外盘)

        # 多普勒束流调整
        if doppler_factor > 1.0:
            # 蓝移/增亮侧
            bright = min(1.5, doppler_factor)
            b = int(min(255, b * bright))
            g = int(min(255, g * bright))
            r = int(r * (1.0 - (bright - 1.0) * 0.3))  # 去红
        else:
            # 红移/变暗侧
            dim = max(0.3, doppler_factor)
            r = int(r * dim)
            g = int(g * dim * 0.6)
            b = int(b * dim * 0.3)

        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        )

    # ═══════════════════════════════════════════════════════════
    #  渲染
    # ═══════════════════════════════════════════════════════════

    def render(self, screen: pygame.Surface, volume: float, time_ms: int):
        """
        渲染吸积盘。
        
        参数:
            volume: 音频 RMS 音量 [0, 1]，驱动亮度和旋转速度
        """
        cx, cy = CENTER

        # 旋转速度（音频驱动）
        angular_speed = 0.008 + volume * 0.04
        self.rotation_angle += angular_speed

        # 先绘制光晕底层（添加式混合）
        self._glow_surf.fill((0, 0, 0, 0))

        # 从外向内绘制环
        for ring in self.rings:
            r = ring['radius']
            temp = ring['temp']
            n = ring['count']
            if n == 0:
                continue

            # 轨道速度比例（内圈转得快 — 差速旋转）
            # v ∝ 1/sqrt(r)，角速度 ∝ v/r ∝ r^{-3/2}
            kepler_factor = (BL_ISCO_R / r) ** 1.5

            for j in range(n):
                angle = ring['offsets'][j] + self.rotation_angle * kepler_factor
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)

                if not (0 <= px < WIDTH and 0 <= py < HEIGHT):
                    continue

                # 多普勒束流：粒子运动方向相对观测者
                # 假设观测者在屏幕下方（+y方向），粒子在盘面旋转
                # 朝向观测者 (向下) → 蓝移；远离观测者 (向上) → 红移
                observer_dir = angle_to_bh(px, py)  # 粒子 → BH 方向
                motion_dir = angle + math.pi / 2  # 切向运动方向
                # theta = 粒子速度方向与视线方向的夹角
                theta = abs(motion_dir + math.pi / 2) % (math.pi * 2)

                doppler = relativistic_doppler(r, theta, 0.8)
                doppler_eff = 1.0 + (doppler - 1.0) * BL_DOPPLER_STRENGTH
                color = self._temp_to_color(temp, doppler_eff)

                # 亮度随体积变化
                alpha = int(150 * (0.6 + volume * 0.8) * temp * doppler_eff)
                alpha = max(0, min(255, alpha))

                size = 1.5 + temp * 1.5 + volume * 0.5
                if size > 0.5:
                    pygame.draw.circle(self._glow_surf, (*color, alpha),
                                       (int(px), int(py)), max(1, int(size)))

        # 用添加式混合渲染光晕
        screen.blit(self._glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    # ═══════════════════════════════════════════════════════════
    #  盘面辉光线渲染（内盘边缘）
    # ═══════════════════════════════════════════════════════════

    def render_inner_glow(self, screen: pygame.Surface, volume: float):
        """渲染 ISCO 内侧的明亮辉光带（最热物质在坠入前的最后光芒）"""
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # ISCO 处的明亮环
        r_isco = BL_ISCO_R
        for r_offset in [0, 3, 6, 10]:
            r = r_isco + r_offset
            alpha = int(60 * (1.0 - r_offset / 15) * (0.5 + volume * 0.5))
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                pygame.draw.circle(glow, (255, 200, 150, alpha),
                                   CENTER, int(r), width=2)

        screen.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)
