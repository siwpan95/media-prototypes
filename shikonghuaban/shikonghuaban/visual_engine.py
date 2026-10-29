"""
时空画板 — 可视化引擎 (黑洞视界模拟增强版)

Pygame 全屏渲染: 黑洞视界 + 吸积盘 + 引力透镜 + 霍金辐射
                + Penrose 几何结构 + 路径粒子 + 增强粒子特效。
"""

import math
import random
import time
import pygame
from collections import deque

from .config import (
    WIDTH, HEIGHT, CENTER, BG, HORIZON, SINGULARITY,
    BL_SCHWARZSCHILD_R, BL_PHOTON_SPHERE_R, BL_ISCO_R, BL_DISK_OUTER_R
)
from .penrose import PenroseParticle, penrose, to_screen
from .particle_effects import ParticleEffectsManager
from .blackhole_physics import dist_to_bh, shadow_alpha, region_of
from .accretion_disk import AccretionDisk
from .gravitational_lensing import GravitationalLensing
from .hawking_radiation import HawkingRadiation
from .spacetime_grid import SpacetimeGrid
from .state import shared_state


class VisualEngine:
    """全屏可视化引擎，管理渲染循环"""

    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mouse.set_visible(False)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("时空画板 — 黑洞视界模拟")

        self.clock = pygame.time.Clock()
        self.start_time = time.time()

        # — 增强粒子特效 —
        self.fx = ParticleEffectsManager(self.screen)

        # — 黑洞物理可视化模块 —
        self.accretion_disk = AccretionDisk(num_rings=60, particles_per_ring=250)
        self.lensing = GravitationalLensing(num_stars=800)
        self.hawking = HawkingRadiation(max_particles=120)
        self.spacetime_grid = SpacetimeGrid(radial_lines=48, circles=24)

        # — 路径粒子 —
        self.particles = [PenroseParticle() for _ in range(30)]

        # — 性能 —
        self.fps_history = deque(maxlen=60)
        self.last_volume = 0.5

        # — 显示模式控制 —
        self.show_grid = True   # 空格键切换
        self.show_lensing = True
        self.show_hawking = True

        # — 字体缓存 —
        self._font_large = pygame.font.Font(None, 36)
        self._font_small = pygame.font.Font(None, 28)
        self._font_tiny = pygame.font.Font(None, 20)

        # — 离屏缓存 Surface（避免每帧分配全屏 SRCALPHA） —
        self._core_scratch = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._photon_scratch = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._structure_glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._curve_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # — 黑洞阴影预渲染（静态径向渐变，与音量/时间无关） —
        max_r = int(BL_PHOTON_SPHERE_R + BL_SCHWARZSCHILD_R * 0.5)
        self._bh_max_r = max_r
        bh_sprite = pygame.Surface((2 * max_r, 2 * max_r), pygame.SRCALPHA)
        bh_center = (max_r, max_r)
        for r in range(max_r, int(BL_SCHWARZSCHILD_R * 0.3), -2):
            alpha = shadow_alpha(r)
            if alpha > 0:
                pygame.draw.circle(bh_sprite, (0, 0, 0, alpha), bh_center, r)
        self._bh_shadow = bh_sprite

    # ================================================================
    #  黑洞核心渲染
    # ================================================================

    def draw_black_hole_core(self, volume: float, time_ms: int):
        """绘制黑洞本身：视界阴影 + 光子球光环"""
        cx, cy = CENTER
        r_s = BL_SCHWARZSCHILD_R
        max_r = self._bh_max_r

        # 静态径向阴影（预渲染精灵，每帧仅 blit）
        self.screen.blit(self._bh_shadow, (cx - max_r, cy - max_r))

        # 视界边缘微弱辉光（霍金辐射暗示，依赖音量）
        self._core_scratch.fill((0, 0, 0, 0))
        for offset in [0, 1, 2]:
            glow_r = int(r_s) + offset
            glow_alpha = int(8 * (1.0 - offset * 0.3) * (0.5 + volume * 0.5))
            if glow_alpha > 0:
                pygame.draw.circle(self._core_scratch, (60, 40, 100, glow_alpha),
                                   CENTER, glow_r, width=1)
        self.screen.blit(self._core_scratch, (0, 0))

        # 光子球明亮光环（EHT 风格的亮环，依赖音量）
        self._photon_scratch.fill((0, 0, 0, 0))
        r_ph = BL_PHOTON_SPHERE_R
        ring_alpha = int(50 * (0.6 + volume * 0.8))
        if ring_alpha > 0:
            pygame.draw.circle(self._photon_scratch, (150, 180, 240, ring_alpha),
                               CENTER, int(r_ph), width=3)
            pygame.draw.circle(self._photon_scratch, (100, 130, 200, ring_alpha // 3),
                               CENTER, int(r_ph + 8), width=6)
        self.screen.blit(self._photon_scratch, (0, 0), special_flags=pygame.BLEND_ADD)

    # ================================================================
    #  结构绘制
    # ================================================================

    def draw_structure(self, volume, time_factor):
        pulse = 1 + volume * 0.8
        max_angle = 1.35 * pulse * (1 + 0.1 * math.sin(time_factor * 0.001))

        horizon_color = (
            int(HORIZON[0] * (1 + volume * 0.3)),
            int(HORIZON[1] * (1 + volume * 0.2)),
            int(HORIZON[2] * (1 + volume * 0.4)),
        )

        # — 对角线 —
        a = to_screen(-max_angle, -max_angle)
        b = to_screen(max_angle, max_angle)
        c = to_screen(max_angle, -max_angle)

        # 发光层 (BLEND_ADD)
        line_glow = self._structure_glow
        line_glow.fill((0, 0, 0, 0))
        glow_a = int(40 * (1 + volume))
        pygame.draw.line(line_glow, (*horizon_color, glow_a), a, b, 4)
        pygame.draw.line(line_glow, (*horizon_color, glow_a), a, c, 4)
        self.screen.blit(line_glow, (0, 0), special_flags=pygame.BLEND_ADD)

        # 实线层
        pygame.draw.line(self.screen, horizon_color, a, b, 2)
        pygame.draw.line(self.screen, horizon_color, a, c, 2)

        # — 奇点曲线 —
        pts_up, pts_down = [], []
        curve_points = 80
        for i in range(curve_points):
            u = (1 + i * 0.05) * pulse
            v = math.sqrt(max(u * u - 1, 0))
            pts_up.append(to_screen(*penrose(u, v)))
            pts_down.append(to_screen(*penrose(u, -v)))

        # 复用单一离屏 Surface 批量绘制，避免每帧 79 次全屏分配
        curve_surf = self._curve_surf
        curve_surf.fill((0, 0, 0, 0))
        for i in range(len(pts_up) - 1):
            alpha = int(200 * (1 - i / curve_points) * (0.5 + volume * 0.5))
            rgba = (*SINGULARITY, alpha)
            pygame.draw.line(curve_surf, rgba, pts_up[i], pts_up[i + 1], 2)
            pygame.draw.line(curve_surf, rgba, pts_down[i], pts_down[i + 1], 2)
        self.screen.blit(curve_surf, (0, 0))

    # ================================================================
    #  HUD
    # ================================================================

    def draw_hud(self, elapsed_ms):
        h = int(elapsed_ms // 3600000)
        m = int((elapsed_ms % 3600000) // 60000)
        s = int((elapsed_ms % 60000) // 1000)

        time_surf = self._font_large.render(f"{h:02d}:{m:02d}:{s:02d}", True, (150, 150, 150))
        self.screen.blit(time_surf, (20, 20))

        fps = self.clock.get_fps()
        fps_surf = self._font_small.render(f"FPS: {fps:.1f}", True, (100, 100, 100))
        self.screen.blit(fps_surf, (20, 60))

        total = len(self.particles) + self.fx.total_count
        count_surf = self._font_small.render(f"Particles: {total}", True, (100, 100, 100))
        self.screen.blit(count_surf, (20, 90))

        # 黑洞物理信息
        bh_info = [
            f"Schwarzschild   r_s = {BL_SCHWARZSCHILD_R:.0f} px",
            f"Photon Sphere   r_ph = {BL_PHOTON_SPHERE_R:.0f} px",
            f"ISCO            r_isco = {BL_ISCO_R:.0f} px",
            f"Disk Outer      r_out = {BL_DISK_OUTER_R:.0f} px",
        ]
        y_offset = HEIGHT - 90
        for line in bh_info:
            info_surf = self._font_tiny.render(line, True, (80, 80, 100))
            self.screen.blit(info_surf, (20, y_offset))
            y_offset += 18

        # 显示模式指示
        mode_str = ""
        if self.show_grid:
            mode_str += "[G]网格 "
        if self.show_lensing:
            mode_str += "[L]透镜 "
        if self.show_hawking:
            mode_str += "[H]霍金 "
        if mode_str:
            mode_surf = self._font_tiny.render(f"SPACE切换: {mode_str.strip()}", True, (60, 60, 80))
            self.screen.blit(mode_surf, (WIDTH - 300, HEIGHT - 24))

    # ================================================================
    #  主循环
    # ================================================================

    def run(self):
        running = True

        while running:
            # ═══ 事件 ═══
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    elif e.key == pygame.K_UP:
                        with shared_state.lock:
                            shared_state.volume = min(shared_state.volume + 0.1, 1.0)
                    elif e.key == pygame.K_DOWN:
                        with shared_state.lock:
                            shared_state.volume = max(shared_state.volume - 0.1, 0.0)
                    elif e.key == pygame.K_SPACE:
                        # 循环切换显示模式
                        if self.show_grid and self.show_lensing and self.show_hawking:
                            self.show_lensing = False
                        elif self.show_grid and not self.show_lensing and self.show_hawking:
                            self.show_grid = False
                            self.show_lensing = True
                        elif not self.show_grid and self.show_lensing and self.show_hawking:
                            self.show_hawking = False
                        elif not self.show_grid and self.show_lensing and not self.show_hawking:
                            self.show_grid = True
                            self.show_lensing = False
                        elif self.show_grid and not self.show_lensing and not self.show_hawking:
                            self.show_lensing = True
                            self.show_hawking = True
                        elif not self.show_grid and not self.show_lensing and self.show_hawking:
                            self.show_grid = True
                            self.show_hawking = False
                        else:
                            self.show_grid = True
                            self.show_lensing = True
                            self.show_hawking = True

            # ═══ 音量读取 + 平滑 ═══
            with shared_state.lock:
                raw_volume = shared_state.volume
            volume = self.last_volume * 0.9 + raw_volume * 0.1
            self.last_volume = volume

            speed = 0.5 + volume * 2.0
            elapsed_ms = int((time.time() - self.start_time) * 1000)

            # ═══ 动态粒子数量 ═══
            target = int(20 + volume * 60)
            while len(self.particles) < target:
                self.particles.append(PenroseParticle())
            while len(self.particles) > target:
                self.particles.pop()

            # ═══ 渲染 ═══
            self.screen.fill(BG)

            # 0. 背景星场 + 引力透镜效果
            if self.show_lensing:
                self.lensing.render(self.screen, volume, elapsed_ms)
            else:
                self.lensing.render(self.screen, 0.2, elapsed_ms)

            # 1. 弯曲时空网格
            if self.show_grid:
                self.spacetime_grid.render(self.screen, volume, elapsed_ms)

            # 2. 吸积盘（在黑洞核心之后绘制）
            #    （在增强粒子系统之间分层）
            self.fx.update_and_render(volume, elapsed_ms)

            # 3. 吸积盘渲染
            self.accretion_disk.render(self.screen, volume, elapsed_ms)

            # 4. 黑洞核心（视界阴影 + 光子球光环）
            self.draw_black_hole_core(volume, elapsed_ms)

            # 5. 吸积盘内缘辉光
            self.accretion_disk.render_inner_glow(self.screen, volume)

            # 6. 霍金辐射
            if self.show_hawking:
                self.hawking.update_and_render(self.screen, volume)

            # 7. 结构线条
            self.draw_structure(volume, elapsed_ms)

            # 8. 路径粒子
            for p in self.particles:
                p.update(speed)
                p.draw(self.screen, volume)

            # 9. 节拍检测
            self.fx.tick_beat(volume)

            # 10. HUD
            self.draw_hud(elapsed_ms)

            pygame.display.flip()
            self.clock.tick(60)
            self.fps_history.append(self.clock.get_fps())

        pygame.quit()
