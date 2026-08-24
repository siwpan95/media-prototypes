"""
时空画板 — 时空弯曲网格可视化

模拟黑洞周围弯曲的时空:
  - 极坐标网格（径向线 + 同心圆）
  - Flamm 抛物体嵌入图的二维映射
  - 越靠近视界，网格越密集
  - 音频响应变形强度
"""

import math
import pygame
from .config import (
    WIDTH, HEIGHT, CENTER, BG,
    BL_SCHWARZSCHILD_R, BL_PHOTON_SPHERE_R, BL_ISCO_R, BL_DISK_OUTER_R
)


class SpacetimeGrid:
    """弯曲时空网格"""

    def __init__(self, radial_lines: int = 36, circles: int = 20):
        self.radial_lines = radial_lines
        self.circles = circles
        self._grid_surf = None

        # 网格线颜色
        self.line_color = (30, 30, 60)
        self.highlight_color = (50, 50, 90)

    def _flamm_embedding(self, r: float, r_s: float) -> float:
        """
        Flamm 抛物体嵌入函数。
        
        史瓦西度规的空间部分等效于一个抛物体在更高维的嵌入:
        z² = 8 * r_s * (r - r_s)
        
        这里返回嵌入导致的径向坐标"拉伸"因子。
        """
        if r <= r_s:
            return float('inf')
        # dz/dr = sqrt(r_s / (r - r_s))
        # 这是径向线在嵌入空间的斜率
        stretch = math.sqrt(r_s / (r - r_s))
        return stretch

    def _warped_r(self, screen_r: float) -> float:
        """
        屏幕径向坐标 → 弯曲时空中的有效径向坐标。
        
        越靠近视界，坐标被压缩得越厉害。
        """
        r_s = BL_SCHWARZSCHILD_R
        if screen_r <= r_s:
            return 0.0

        # 用 Flamm 嵌入计算 warp 因子
        flamm = self._flamm_embedding(screen_r, r_s)

        # 映射：大 r 时接近原始值，近 r_s 时急剧压缩
        # 使用对数尺度映射，使网格在视界附近更密集
        log_base = math.log(BL_DISK_OUTER_R / r_s)
        if log_base <= 0:
            return screen_r

        # 对数映射
        log_r = math.log(max(screen_r, r_s * 1.001) / r_s)
        warped = log_r / log_base * BL_DISK_OUTER_R

        return warped

    def render(self, screen: pygame.Surface, volume: float, time_ms: int):
        """
        渲染弯曲时空网格。
        绘制径向线和同心圆，受弯曲时空影响而变形。
        """
        cx, cy = CENTER
        r_s = BL_SCHWARZSCHILD_R

        # 脉冲效果（音频驱动网格抖动）
        pulse = 1.0 + volume * 0.03

        # 绘制同心圆
        for i in range(1, self.circles + 1):
            circle_r = i * (BL_DISK_OUTER_R / self.circles) * pulse
            warped_r = self._warped_r(circle_r)

            # 在视界内不绘制
            if warped_r < r_s * 0.5:
                continue

            # 越靠近视界越暗
            alpha = int(60 * min(1.0, (warped_r - r_s * 0.5) / r_s))
            alpha = max(5, min(80, alpha))

            if alpha > 0:
                # 高亮 ISCO 和光子球圆
                if abs(circle_r - BL_ISCO_R) < r_s * 0.15:
                    color = (*self.highlight_color, alpha * 2)
                    width = 2
                elif abs(circle_r - BL_PHOTON_SPHERE_R) < r_s * 0.1:
                    color = (*self.highlight_color, alpha * 2)
                    width = 2
                else:
                    color = (*self.line_color, alpha)
                    width = 1

                # 绘制变形后的圆
                pts = []
                segments = 120
                for j in range(segments):
                    angle = 2.0 * math.pi * j / segments
                    x = cx + warped_r * math.cos(angle)
                    y = cy + warped_r * math.sin(angle)
                    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                        pts.append((int(x), int(y)))

                if len(pts) >= 2:
                    pygame.draw.lines(screen, color, True, pts, width)

        # 绘制径向线
        for i in range(self.radial_lines):
            angle = 2.0 * math.pi * i / self.radial_lines
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            # 从视界外缘开始画
            pts = []
            steps = 80
            for j in range(steps):
                t = j / steps
                # 从视界到外缘
                screen_r = r_s * 1.01 + t * (BL_DISK_OUTER_R - r_s * 1.01) * pulse
                warped_r = self._warped_r(screen_r)

                x = cx + warped_r * cos_a
                y = cy + warped_r * sin_a

                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    # 越靠近视界越暗
                    proximity = min(1.0, t * 3)
                    alpha = int(40 * proximity)
                    pts.append((int(x), int(y), alpha))

            # 分段绘制（不同 alpha 需要不同线段）
            if len(pts) >= 2:
                current_seg = [pts[0]]
                current_alpha = pts[0][2]
                for pt in pts[1:]:
                    if abs(pt[2] - current_alpha) < 10:
                        current_seg.append(pt)
                    else:
                        if len(current_seg) >= 2:
                            seg_pts = [(p[0], p[1]) for p in current_seg]
                            avg_alpha = sum(p[2] for p in current_seg) // len(current_seg)
                            color = (*self.line_color, max(5, min(80, avg_alpha)))
                            pygame.draw.lines(screen, color, False, seg_pts, 1)
                        current_seg = [pt]
                        current_alpha = pt[2]

                if len(current_seg) >= 2:
                    seg_pts = [(p[0], p[1]) for p in current_seg]
                    avg_alpha = sum(p[2] for p in current_seg) // len(current_seg)
                    color = (*self.line_color, max(5, min(80, avg_alpha)))
                    pygame.draw.lines(screen, color, False, seg_pts, 1)
