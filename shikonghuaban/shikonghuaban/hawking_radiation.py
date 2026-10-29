"""
时空画板 — 霍金辐射效果

模拟黑洞视界边缘的量子效应:
  - 虚粒子对产生与湮灭
  - 逃逸粒子形成微弱辉光
  - 闪烁 / 涨落效果
  - 音频响应
"""

import math
import random
import pygame
from .config import WIDTH, HEIGHT, CENTER, BL_SCHWARZSCHILD_R


class HawkingRadiation:
    """霍金辐射粒子效果"""

    def __init__(self, max_particles: int = 120):
        self.max_particles = max_particles
        self.particles = []  # 每个: {x, y, vx, vy, life, max_life, size, color}
        self._glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._accumulated_time = 0.0

    def update_and_render(self, screen: pygame.Surface, volume: float, dt: float = 1/60):
        """
        更新霍金辐射粒子并渲染。
        
        霍金辐射速率与黑洞质量成反比（小质量黑洞辐射更强）。
        这里用音量作为辐射强度的调制。
        """
        cx, cy = CENTER

        # 发射速率（音频驱动）
        emission_rate = 3 + volume * 15  # 每帧发射粒子数
        self._accumulated_time += dt

        # 发射新粒子
        to_emit = int(emission_rate * self._accumulated_time * 60)
        self._accumulated_time -= to_emit / 60.0

        for _ in range(min(to_emit, self.max_particles - len(self.particles))):
            # 从视界表面随机位置发射
            angle = random.uniform(0, math.pi * 2)
            # 视界边缘的量子涨落
            emit_r = BL_SCHWARZSCHILD_R * (1.0 + random.uniform(-0.05, 0.08))
            x = cx + emit_r * math.cos(angle)
            y = cy + emit_r * math.sin(angle)

            # 速度方向：径向向外（逃逸粒子）或向内（坠落粒子）
            if random.random() < 0.6:  # 60% 逃逸
                speed = random.uniform(0.3, 1.5)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
            else:  # 40% 坠回视界
                speed = random.uniform(0.2, 0.8)
                vx = -math.cos(angle) * speed
                vy = -math.sin(angle) * speed

            # 虚拟粒子（反粒子） — 几乎看不见
            partner_visible = random.random() < 0.3
            if partner_visible:
                # 向内的反粒子，有微弱的互补色辉光
                partner_angle = angle + math.pi + random.uniform(-0.3, 0.3)
                px = cx + emit_r * math.cos(partner_angle)
                py = cy + emit_r * math.sin(partner_angle)
                p_speed = random.uniform(0.2, 0.6)
                self.particles.append({
                    'x': px, 'y': py,
                    'vx': math.cos(partner_angle) * p_speed,
                    'vy': math.sin(partner_angle) * p_speed,
                    'life': 1.0, 'max_life': random.uniform(0.3, 1.0),
                    'size': random.uniform(0.5, 1.0),
                    'color': (60, 40, 100),  # 暗紫
                    'is_escape': False,
                })

            self.particles.append({
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'life': 1.0, 'max_life': random.uniform(0.5, 2.5),
                'size': random.uniform(0.8, 2.0),
                'color': (80, 60, 130) if random.random() < 0.5 else (60, 50, 120),
                'is_escape': True,
            })

        # 更新粒子
        survived = []
        for p in self.particles:
            p['life'] -= dt / p['max_life']
            if p['life'] <= 0:
                continue

            p['x'] += p['vx']
            p['y'] += p['vy']

            # 超出屏幕范围的丢弃
            if not (-50 <= p['x'] < WIDTH + 50 and -50 <= p['y'] < HEIGHT + 50):
                continue

            # 被吸入黑洞
            r = math.hypot(p['x'] - cx, p['y'] - cy)
            if r < BL_SCHWARZSCHILD_R * 0.95 and not p['is_escape']:
                continue
            if r < BL_SCHWARZSCHILD_R * 0.85:
                continue

            survived.append(p)
        self.particles = survived

        # 渲染
        self._glow_surf.fill((0, 0, 0, 0))
        glow_alpha_base = int(25 * (0.5 + volume * 0.5))

        for p in self.particles:
            alpha = int(255 * p['life'] * 0.4)
            if alpha < 3:
                continue
            alpha = min(255, alpha)

            size = p['size'] * (0.5 + p['life'] * 0.5)
            color = p['color']

            pygame.draw.circle(self._glow_surf,
                               (*color, alpha),
                               (int(p['x']), int(p['y'])),
                               max(1, int(size)))

        # 视界辉光
        if glow_alpha_base > 0:
            for glow_r_offset in range(3):
                glow_r = BL_SCHWARZSCHILD_R + glow_r_offset * 4
                glow_alpha = glow_alpha_base - glow_r_offset * 8
                if glow_alpha > 0:
                    pygame.draw.circle(self._glow_surf,
                                       (80, 60, 140, glow_alpha),
                                       CENTER, int(glow_r), width=1)

        screen.blit(self._glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)
