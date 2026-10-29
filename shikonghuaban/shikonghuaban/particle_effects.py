"""
时空画板 — 增强粒子特效管理器

基于 particle 工具包的系统:
  - 背景星尘 (Dust)
  - 节拍脉冲 (Pulse)
  - 奇点轨道 (Orbit)
  - 结构边缘流光 (Edge Flow)
  - 奇点曲线发光 (Singularity Flow)
  - 光子环 (Photon Ring) — 新增
  - 吸积坠入流 (Accretion Flow) — 新增

对外暴露 ParticleEffectsManager，VisualEngine 只需调用统一接口。
"""

import math
import random
from dataclasses import dataclass

from .particle.core.particle import (
    ParticleSystem, Emitter, ForceField, EmitterShape, Particle,
    gradient_to_curve, size_curve_fadeout, size_curve_pulse,
    create_vortex, create_turbulence,
)
from .particle.renderers.pygame_renderer import PygameRenderer

from .config import (
    WIDTH, HEIGHT, CENTER, HORIZON, SINGULARITY, COLOR,
    BL_SCHWARZSCHILD_R, BL_PHOTON_SPHERE_R, BL_ISCO_R
)
from .penrose import penrose, to_screen
from .blackhole_physics import (
    dist_to_bh, angle_to_bh, radial_unit, tangential_unit,
    relativistic_orbital_speed, accretion_temperature
)


@dataclass
class Effect:
    """一个可插拔的粒子特效单元（注册表项）。

    解耦 ParticleEffectsManager 对具体特效的硬编码：渲染主循环只遍历
    ``effects`` 列表，无需了解每个特效的内部构造，从而实现可测试、可组合的
    特效层。
    """

    name: str
    ps: object                      # ParticleSystem 实例
    renderer: object                # PygameRenderer 实例
    rms_factor: float = None        # 非 None 时 update 注入 audio_data={'rms': volume*factor}
    trigger_fn: object = None       # 条件触发回调 (volume, elapsed_ms) -> None
    trigger_prob_factor: float = None  # 触发概率 = volume * factor


class ParticleEffectsManager:
    """
    增强粒子特效管理器。

    使用方式:
        fx = ParticleEffectsManager(screen)
        while running:
            fx.update_and_render(volume, elapsed_ms)
            fx.tick_beat(volume)      # 在主循环中检测节拍
    """

    def __init__(self, screen):
        self.screen = screen
        self._init_dust()
        self._init_pulse()
        self._init_orbit()
        self._init_edge()
        self._init_singularity()
        self._init_photon_ring()
        self._init_accretion_flow()

        # 节拍冷却
        self._beat_cooldown = 0.0

        # ── 特效注册表（解耦：列表顺序即渲染层序，可插拔、可测试）──
        self.effects = [
            Effect("dust", self.dust_ps, self.dust_renderer, rms_factor=0.3),
            Effect("accretion", self.accretion_ps, self.accretion_renderer,
                   rms_factor=0.6, trigger_fn=self._trigger_accretion_particle,
                   trigger_prob_factor=0.4),
            Effect("singularity", self.singularity_ps, self.singularity_renderer,
                   trigger_fn=self._trigger_singularity_flow, trigger_prob_factor=0.3),
            Effect("edge", self.edge_ps, self.edge_renderer,
                   trigger_fn=self._trigger_edge_flow, trigger_prob_factor=0.2),
            Effect("orbit", self.orbit_ps, self.orbit_renderer, rms_factor=0.5),
            Effect("photon", self.photon_ps, self.photon_renderer, rms_factor=0.3),
            Effect("pulse", self.pulse_ps, self.pulse_renderer),
        ]

    # ─────────────────────────────────────────────
    #  初始化各系统
    # ─────────────────────────────────────────────

    def _init_dust(self):
        """背景星尘 — 大量微小粒子缓慢漂移"""
        self.dust_ps = ParticleSystem(max_particles=500)
        em = Emitter(
            x=WIDTH / 2, y=HEIGHT / 2,
            rate=50, spread=math.pi * 2, speed=0.4,
            life=12.0, size=1.2, color=(30, 30, 50),
            shape=EmitterShape('sphere', radius=800, emit_from_volume=True),
        )
        self.dust_ps.add_emitter(em)
        self.dust_ps.add_force_field(
            ForceField('turbulence', strength=0.3, turb_scale=100.0, turb_strength=0.3)
        )
        self.dust_renderer = PygameRenderer(
            self.screen, trail_width=1, trail_alpha_decay=0.2, show_rotation_indicator=False
        )

    def _init_pulse(self):
        """节拍脉冲 — 强节拍时从中心爆发"""
        self.pulse_ps = ParticleSystem(max_particles=400)
        self.pulse_ps.add_force_field(
            ForceField('attraction', x=WIDTH / 2, y=HEIGHT / 2, strength=20.0)
        )
        self.pulse_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.5, show_rotation_indicator=False
        )

    def _init_orbit(self):
        """奇点轨道 — 围绕中心漩涡运动"""
        self.orbit_ps = ParticleSystem(max_particles=150)
        vortex = create_vortex(WIDTH / 2, HEIGHT / 2, strength=3.0, clockwise=True)
        self.orbit_ps.add_force_field(vortex)
        self.orbit_ps.add_force_field(
            ForceField('turbulence', strength=0.5, turb_scale=60.0, turb_strength=0.5)
        )
        em = Emitter(
            x=WIDTH / 2, y=HEIGHT / 2,
            rate=8, spread=math.pi * 2, speed=1.8,
            life=8.0, size=2.5, color=(200, 75, 75),
            trail_enabled=True, trail_length=14,
            color_over_lifetime=gradient_to_curve([
                (255, 140, 100), (200, 75, 75), (140, 45, 45), (60, 20, 20)
            ]),
            size_over_lifetime=size_curve_fadeout(2.5),
            shape=EmitterShape('sphere', radius=30, emit_from_volume=True),
        )
        self.orbit_ps.add_emitter(em)
        self.orbit_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.6, show_rotation_indicator=False
        )

    def _init_edge(self):
        """结构边缘流光 — 沿 Penrose 对角线缓慢移动"""
        self.edge_ps = ParticleSystem(max_particles=200)
        self.edge_ps.add_force_field(
            ForceField('turbulence', strength=0.4, turb_scale=40.0, turb_strength=0.4)
        )
        self.edge_renderer = PygameRenderer(
            self.screen, trail_width=1, trail_alpha_decay=0.7, show_rotation_indicator=False
        )

    def _init_singularity(self):
        """奇点曲线发光 — 沿奇点曲线缓慢飘动"""
        self.singularity_ps = ParticleSystem(max_particles=100)
        em = Emitter(
            x=WIDTH / 2, y=HEIGHT / 2,
            rate=5, spread=math.pi * 2, speed=0.8,
            life=5.0, size=2.0, color=(160, 50, 50),
            trail_enabled=True, trail_length=8,
            color_over_lifetime=gradient_to_curve([
                (200, 80, 80), (160, 50, 50), (100, 30, 30)
            ]),
            size_over_lifetime=size_curve_pulse(2.0, peak_at=0.3),
            shape=EmitterShape('circle', radius=60, emit_from_shell=True),
        )
        self.singularity_ps.add_emitter(em)
        self.singularity_ps.add_force_field(
            ForceField('attraction', x=WIDTH / 2, y=HEIGHT / 2, strength=10.0)
        )
        self.singularity_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.5, show_rotation_indicator=False
        )

    def _init_photon_ring(self):
        """光子环 — 光子在光子球附近做不稳定轨道运动"""
        self.photon_ps = ParticleSystem(max_particles=200)
        # 强吸引力场（模拟黑洞引力）
        self.photon_ps.add_force_field(
            ForceField('attraction', x=CENTER[0], y=CENTER[1], strength=30.0)
        )
        # 湍流模拟光子球的不稳定性
        self.photon_ps.add_force_field(
            ForceField('turbulence', strength=0.2, turb_scale=30.0, turb_strength=0.2)
        )
        em = Emitter(
            x=CENTER[0], y=CENTER[1],
            rate=4, spread=math.pi * 2, speed=2.5,
            life=6.0, size=1.5, color=(100, 150, 255),
            trail_enabled=True, trail_length=10,
            color_over_lifetime=gradient_to_curve([
                (180, 220, 255), (100, 150, 255), (40, 60, 150), (10, 10, 40)
            ]),
            size_over_lifetime=size_curve_pulse(1.5, peak_at=0.2),
            shape=EmitterShape('circle', radius=BL_PHOTON_SPHERE_R, emit_from_shell=True),
        )
        self.photon_ps.add_emitter(em)
        self.photon_renderer = PygameRenderer(
            self.screen, trail_width=1, trail_alpha_decay=0.3, show_rotation_indicator=False
        )

    def _init_accretion_flow(self):
        """吸积坠入流 — 粒子从 ISCO 附近螺旋坠向视界"""
        self.accretion_ps = ParticleSystem(max_particles=300)
        # 漩涡力场模拟差速旋转
        vortex = create_vortex(CENTER[0], CENTER[1], strength=5.0, clockwise=True)
        self.accretion_ps.add_force_field(vortex)
        # 强吸引力将粒子拉向视界
        self.accretion_ps.add_force_field(
            ForceField('attraction', x=CENTER[0], y=CENTER[1], strength=40.0)
        )
        # 湍流
        self.accretion_ps.add_force_field(
            ForceField('turbulence', strength=0.6, turb_scale=50.0, turb_strength=0.5)
        )
        em = Emitter(
            x=CENTER[0], y=CENTER[1],
            rate=6, spread=math.pi * 2, speed=1.2,
            life=5.0, size=2.0, color=(255, 160, 60),
            trail_enabled=True, trail_length=12,
            color_over_lifetime=gradient_to_curve([
                (255, 200, 100),  # 高温橙黄（刚离开 ISCO）
                (255, 120, 40),   # 红橙
                (200, 50, 20),    # 暗红（靠近视界）
                (40, 10, 5),      # 几乎消失
            ]),
            size_over_lifetime=size_curve_fadeout(2.0),
            shape=EmitterShape('circle', radius=BL_ISCO_R * 0.8, emit_from_volume=True),
        )
        self.accretion_ps.add_emitter(em)
        self.accretion_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.7, show_rotation_indicator=False
        )

    # ─────────────────────────────────────────────
    #  节拍检测入口
    # ─────────────────────────────────────────────

    def tick_beat(self, volume, dt=1/60):
        """每帧调用，检测节拍并触发脉冲。返回 True 表示触发了脉冲。"""
        self._beat_cooldown -= dt
        if volume > 0.5 and self._beat_cooldown <= 0:
            self._trigger_pulse(volume)
            self._beat_cooldown = 0.25  # 250ms 冷却
            return True
        return False

    # ─────────────────────────────────────────────
    #  统一更新+渲染
    # ─────────────────────────────────────────────

    def update_and_render(self, volume, elapsed_ms):
        """按注册表顺序更新并渲染所有增强粒子系统（解耦于具体特效）。"""

        dt = 1 / 60
        for eff in self.effects:
            # 条件触发（部分特效按音量概率喷射）
            if eff.trigger_fn is not None and eff.trigger_prob_factor is not None:
                if random.random() < volume * eff.trigger_prob_factor:
                    eff.trigger_fn(volume, elapsed_ms)

            # 带音频能量的更新
            if eff.rms_factor is not None:
                eff.ps.update(dt, audio_data={'rms': volume * eff.rms_factor})
            else:
                eff.ps.update(dt)
            eff.ps.render(eff.renderer)

    # ─────────────────────────────────────────────
    #  粒子计数（用于HUD）
    # ─────────────────────────────────────────────

    @property
    def total_count(self):
        return sum(eff.ps.get_particle_count() for eff in self.effects)

    # ================================================================
    #  触发方法
    # ================================================================

    def _trigger_pulse(self, volume: float):
        """节拍脉冲爆发"""
        intensity = volume
        count = int(40 + intensity * 60)
        base_speed = 4.0 + intensity * 7.0
        life = 0.6 + intensity * 1.0

        bright_color = (
            int(min(255, COLOR[0] * (1.2 + intensity * 0.5))),
            int(min(255, COLOR[1] * (1.0 + intensity * 0.3))),
            int(min(255, COLOR[2] * (1.0 + intensity * 0.2))),
        )
        dark_color = (
            int(COLOR[0] * 0.4),
            int(COLOR[1] * 0.3),
            int(COLOR[2] * 0.3),
        )

        available = self.pulse_ps.max_particles - len(self.pulse_ps.particles)
        for _ in range(min(count, available)):
            angle = random.uniform(0, math.pi * 2)
            speed = base_speed * random.uniform(0.6, 1.4)

            p = Particle(
                x=WIDTH / 2 + random.uniform(-5, 5),
                y=HEIGHT / 2 + random.uniform(-5, 5),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=1.0, max_life=life * random.uniform(0.8, 1.2),
                size=2.0 + intensity * 2.5,
                color=bright_color, alpha=1.0,
                trail_enabled=True, trail_max_length=10,
                color_over_lifetime=gradient_to_curve([bright_color, COLOR, dark_color]),
                size_over_lifetime=size_curve_pulse(2.0 + intensity * 2.5, peak_at=0.2),
            )
            p.enable_trail(10)
            self.pulse_ps.particles.append(p)

    def _trigger_edge_flow(self, volume: float, elapsed_ms: int):
        """沿结构对角线发射流光粒子"""
        pulse = 1 + volume * 0.8
        max_angle = 1.35 * pulse * (1 + 0.1 * math.sin(elapsed_ms * 0.001))

        a = to_screen(-max_angle, -max_angle)
        b = to_screen(max_angle, max_angle)
        c = to_screen(max_angle, -max_angle)

        for start, end in [(a, b), (a, c)]:
            if random.random() > 0.6:
                continue
            t = random.random()
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t

            dx = (end[0] - start[0]) / max(abs(end[0] - start[0]), 1) * 0.3
            dy = (end[1] - start[1]) / max(abs(end[1] - start[1]), 1) * 0.3

            p = Particle(
                x=x, y=y,
                vx=dx + random.uniform(-0.3, 0.3),
                vy=dy + random.uniform(-0.3, 0.3),
                life=1.0, max_life=random.uniform(2.0, 4.0),
                size=random.uniform(1.5, 3.5),
                color=HORIZON, alpha=0.6,
                trail_enabled=True, trail_max_length=5,
                size_over_lifetime=size_curve_fadeout(2.5),
            )
            p.enable_trail(5)
            self.edge_ps.particles.append(p)

    def _trigger_singularity_flow(self, volume: float, elapsed_ms: int):
        """沿奇点曲线发射发光粒子"""
        curve_points = 60
        pulse = 1 + volume * 0.8

        for _ in range(2):
            i = random.randint(0, curve_points - 2)
            u = (1 + i * 0.05) * pulse
            v = math.sqrt(max(u * u - 1, 0))

            sign = random.choice([-1, 1])
            P, Q = penrose(u, v * sign)
            x, y = to_screen(P, Q)

            # 沿曲线切线方向
            tangent_u = 0.05
            tangent_v = (u * tangent_u) / max(v, 0.1)
            tangent_P, tangent_Q = penrose(u + tangent_u, (v + tangent_v) * sign)
            tx, ty = to_screen(tangent_P, tangent_Q)
            dx = (tx - x) * 0.1
            dy = (ty - y) * 0.1

            bright_color = (
                int(min(255, SINGULARITY[0] * (1.2 + volume * 0.3))),
                int(min(255, SINGULARITY[1] * (0.8 + volume * 0.2))),
                int(min(255, SINGULARITY[2] * (0.8 + volume * 0.2))),
            )

            p = Particle(
                x=x, y=y,
                vx=dx + random.uniform(-0.5, 0.5),
                vy=dy + random.uniform(-0.5, 0.5),
                life=1.0, max_life=random.uniform(1.5, 3.5),
                size=random.uniform(1.5, 3.0),
                color=bright_color, alpha=0.8,
                trail_enabled=True, trail_max_length=6,
                color_over_lifetime=gradient_to_curve(
                    [bright_color, SINGULARITY, (60, 20, 20)]
                ),
                size_over_lifetime=size_curve_fadeout(2.5),
            )
            p.enable_trail(6)
            self.singularity_ps.particles.append(p)

    def _trigger_accretion_particle(self, volume: float, elapsed_ms: int = 0):
        """从 ISCO 附近发射吸积坠入粒子"""
        angle = random.uniform(0, math.pi * 2)
        # 发射位置：ISCO 附近
        emit_r = BL_ISCO_R * random.uniform(0.7, 1.1)
        cx, cy = CENTER
        x = cx + emit_r * math.cos(angle)
        y = cy + emit_r * math.sin(angle)

        # 轨道速度方向（切向）
        tux, tuy = tangential_unit(x, y)
        orb_speed = relativistic_orbital_speed(emit_r) * 15.0
        # 加上向内的径向速度（螺旋坠入）
        rux, ruy = radial_unit(x, y)
        inward = 0.3 + volume * 1.0

        vx = tux * orb_speed - rux * inward
        vy = tuy * orb_speed - ruy * inward

        temp = accretion_temperature(emit_r)
        r = int(min(255, 200 + temp * 55))
        g = int(min(255, 60 + temp * 120))
        b = int(min(255, 30 + temp * 60))

        p = Particle(
            x=x, y=y,
            vx=vx + random.uniform(-0.3, 0.3),
            vy=vy + random.uniform(-0.3, 0.3),
            life=1.0, max_life=random.uniform(2.0, 5.0),
            size=random.uniform(1.5, 3.0),
            color=(r, g, b), alpha=0.7,
            trail_enabled=True, trail_max_length=8,
            color_over_lifetime=gradient_to_curve([
                (r, g, b), (r // 2, g // 3, b // 3), (20, 5, 3)
            ]),
            size_over_lifetime=size_curve_fadeout(2.5),
        )
        p.enable_trail(8)
        self.accretion_ps.particles.append(p)
