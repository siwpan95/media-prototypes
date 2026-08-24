"""
Pygame 渲染器 v3.0 — 全功能版

支持：
- 粒子圆形/精灵绘制
- 拖尾渲染（Trail）
- 旋转指示线
- 网格体（Sprite/Image）绑定渲染
- 纹理帧动画显示
"""

import pygame
import math
from ..core.particle import Particle, Renderer


class PygameRenderer(Renderer):
    """Pygame 渲染器 v3.0"""

    def __init__(self, screen: pygame.Surface,
                 trail_width: int = 1,
                 trail_alpha_decay: float = 0.7,
                 show_rotation_indicator: bool = True):
        """
        Args:
            screen               : Pygame 屏幕表面
            trail_width          : 拖尾线宽
            trail_alpha_decay    : 拖尾透明度衰减系数
            show_rotation_indicator : 是否显示旋转指示线
        """
        self.screen = screen
        self.trail_width = trail_width
        self.trail_alpha_decay = trail_alpha_decay
        self.show_rotation_indicator = show_rotation_indicator

    def render(self, particles: list):
        """渲染粒子列表"""
        for p in particles:
            if not p.is_alive():
                continue

            # --- 1. 拖尾渲染 ---
            if p.trail_enabled and len(p.trail_history) >= 2:
                self._render_trail(p)

            # --- 2. 主体渲染 ---
            x = int(p.x)
            y = int(p.y)
            alpha = p.alpha
            
            # 根据模式选择渲染方式
            if p.mesh_mode == 'sprite' and p.mesh_surface is not None:
                self._render_sprite(p, x, y, alpha)
            elif p.mesh_mode == 'image' and p.get_current_texture() is not None:
                self._render_texture_frame(p, x, y, alpha)
            else:
                self._render_circle(p, x, y, alpha)

            # --- 3. 旋转指示线 ---
            if (self.show_rotation_indicator and 
                (p.angular_velocity != 0.0 or p.rotation != 0.0) and
                p.mesh_mode == 'circle'):
                self._render_rotation_indicator(p, x, y)

    def _render_circle(self, p: Particle, x: int, y: int, alpha: float):
        """渲染圆形粒子"""
        radius = int(max(1, p.size * alpha))
        color = (
            int(p.color[0] * alpha),
            int(p.color[1] * alpha),
            int(p.color[2] * alpha),
        )
        if radius > 0:
            pygame.draw.circle(self.screen, color, (x, y), radius)

    def _render_sprite(self, p: Particle, x: int, y: int, alpha: float):
        """渲染精灵/Surface 网格体"""
        surf = p.mesh_surface
        if not isinstance(surf, pygame.Surface):
            return

        # 缩放 Surface 到粒子大小
        size = int(max(2, p.size))
        try:
            scaled = pygame.transform.scale(surf, (size * 2, size * 2))
        except Exception:
            scaled = surf

        # 应用颜色调制和透明度
        mod_color = (
            int(min(255, p.color[0])),
            int(min(255, p.color[1])),
            int(min(255, p.color[2])),
        )
        scaled.fill((*mod_color, int(alpha * 255)), special_flags=pygame.BLEND_RGB_MULT)

        rect = scaled.get_rect(center=(x, y))
        self.screen.blit(scaled, rect)

    def _render_texture_frame(self, p: Particle, x: int, y: int, alpha: float):
        """渲染纹理动画当前帧"""
        frame = p.get_current_texture()
        if not isinstance(frame, pygame.Surface):
            return
        
        size = int(max(2, p.size))
        try:
            scaled = pygame.transform.scale(frame, (size * 2, size * 2))
        except Exception:
            scaled = frame

        rect = scaled.get_rect(center=(x, y))
        self.screen.blit(scaled, rect)

    def _render_trail(self, p: Particle):
        """渲染拖尾（从历史位置到当前位置的渐变连线）"""
        points = p.get_trail_points()
        if len(points) < 2:
            return

        n = len(points)
        for i in range(n - 1):
            # 透明度随拖尾位置递减（越旧越淡）
            t = i / (n - 1)
            trail_alpha = t ** self.trail_alpha_decay * p.alpha
            
            r = int(p.color[0] * trail_alpha)
            g = int(p.color[1] * trail_alpha)
            b = int(p.color[2] * trail_alpha)
            
            p1 = (int(points[i][0]), int(points[i][1]))
            p2 = (int(points[i + 1][0]), int(points[i + 1][1]))
            
            # 线宽也随距离衰减
            width = max(1, int(self.trail_width * t))
            pygame.draw.line(self.screen, (r, g, b), p1, p2, width)

    def _render_rotation_indicator(self, p: Particle, x: int, y: int):
        """渲染旋转指示线"""
        radius = max(int(p.size * p.alpha), 1)
        line_len = radius * 1.8
        end_x = x + math.cos(p.rotation) * line_len
        end_y = y + math.sin(p.rotation) * line_len
        
        alpha = p.alpha
        color = tuple(int(c * alpha) for c in p.color[:3])
        line_color = tuple(max(0, c - 50) for c in color)
        
        pygame.draw.line(
            self.screen, line_color,
            (x, y), (int(end_x), int(end_y)), 1
        )
