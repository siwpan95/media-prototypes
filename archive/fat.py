import math
import random
import struct
import numpy as np
import pygame
import sounddevice as sd
import threading
import time
from collections import deque
import sys
import os

# ==================== 粒子工具包集成 ====================
PARTICLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'particle')
if PARTICLE_DIR not in sys.path:
    sys.path.insert(0, PARTICLE_DIR)

from core.particle import (
    ParticleSystem, Emitter, ForceField, EmitterShape, Particle,
    gradient_to_curve, size_curve_fadeout, size_curve_pulse,
    create_vortex, create_turbulence,
)
from renderers.pygame_renderer import PygameRenderer

# ==================== 全局配置 ====================
WIDTH, HEIGHT = 1920, 1080
BG = (0, 0, 0)
HORIZON = (80, 80, 100)
SINGULARITY = (140, 35, 35)
COLOR = (180, 70, 70)

# 音频参数
SR = 44100
BPM = 118
BEAT = 60 / BPM
VOL = 0.12

# 音符频率
NOTES = {
    "C4": 261.63, "Eb": 311.13, "E": 329.63,
    "Gb": 369.99, "G": 392.00, "A": 440.00,
    "Bb": 466.16, "B": 493.88, "C5": 523.25
}

RIFF = ["C4", "Eb", "E", "Gb", "G", "A", "Bb", "C5"]
VERSE = ["A", "A", "A", "G", None, "E", "G", "G"]
CHORUS = ["C5", "C5", "C5", "B", "C5", "A", "G", "E"]

# ==================== 线程安全共享数据 ====================
class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.volume = 0.5
        self.beat = 0
        self.section = 0
        self.patterns = [
            (RIFF, -1),
            (VERSE, 0),
            (CHORUS, 0),
            (RIFF, 1),
            (CHORUS, 0),
        ]

shared_state = SharedState()

# ==================== 音频引擎 ====================
class AudioEngine:
    def __init__(self):
        self.stream = None
        self.running = False
        
    def saw(self, t, f):
        return 2 * ((t * f) % 1.0) - 1
    
    def env(self, n):
        att = int(0.01 * n)
        rel = int(0.2 * n)
        e = np.ones(n)
        e[:att] = np.linspace(0, 1, att)
        e[-rel:] = np.linspace(1, 0, rel)
        return e
    
    def get_next_note(self):
        with shared_state.lock:
            pat, octv = shared_state.patterns[shared_state.section]
            idx = int(shared_state.beat) % len(pat)
            note = pat[idx]
            
            shared_state.beat += 0.5
            if shared_state.beat >= len(pat) * 2:
                shared_state.beat = 0
                shared_state.section = (shared_state.section + 1) % len(shared_state.patterns)
            
            return note, octv
    
    def audio_callback(self, outdata, frames, time_info, status):
        """sounddevice 回调函数 - 在音频线程中执行"""
        t = np.linspace(0, frames / SR, frames)
        out = np.zeros(frames)
        
        note, octv = self.get_next_note()
        if note is None:
            outdata[:] = out.reshape(-1, 1)
            return
        
        f = NOTES[note] * (2 ** octv)
        sig = self.saw(t, f)
        sig *= self.env(frames)
        out += sig
        
        # 计算RMS并更新共享状态
        rms = np.sqrt(np.mean(sig ** 2))
        with shared_state.lock:
            shared_state.volume = min(rms * 5.0, 1.0)
        
        outdata[:] = (out * VOL).reshape(-1, 1)
    
    def start(self):
        self.running = True
        self.stream = sd.OutputStream(
            samplerate=SR,
            channels=1,
            dtype='float32',
            callback=self.audio_callback,
            blocksize=1024,
            latency='low'
        )
        self.stream.start()
        print("音频引擎已启动")
    
    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("音频引擎已停止")

# ==================== 可视化引擎 ====================
class VisualEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mouse.set_visible(False)
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("24-Hour Spacetime Audio — 粒子增强版")
        
        self.DOT = pygame.Surface((3, 3), pygame.SRCALPHA)
        pygame.draw.circle(self.DOT, (255, 255, 255), (1, 1), 1)
        
        # 原始 Penrose 路径粒子
        self.particles = [self.Particle() for _ in range(30)]
        
        # === 增强: 粒子工具包系统 ===
        self._init_enhanced_particles()
        
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        
        # 性能监控
        self.fps_history = deque(maxlen=60)
        
        # 节拍检测
        self.beat_cooldown = 0.0
        self.last_volume = 0.5
        
        # 缓存字体（避免每帧创建）
        self._font_large = pygame.font.Font(None, 36)
        self._font_small = pygame.font.Font(None, 28)
    
    def _init_enhanced_particles(self):
        """初始化增强粒子系统（基于 particle 工具包）"""
        
        # === 1. 背景星尘 ===
        # 大量微小粒子，缓慢漂移，营造深邃空间感
        self.dust_ps = ParticleSystem(max_particles=500)
        dust_emitter = Emitter(
            x=WIDTH / 2, y=HEIGHT / 2,
            rate=50,
            spread=math.pi * 2,
            speed=0.4,
            life=12.0,
            size=1.2,
            color=(30, 30, 50),
            shape=EmitterShape('sphere', radius=800, emit_from_volume=True),
        )
        self.dust_ps.add_emitter(dust_emitter)
        self.dust_ps.add_force_field(
            ForceField('turbulence', strength=0.3, turb_scale=100.0, turb_strength=0.3)
        )
        self.dust_renderer = PygameRenderer(
            self.screen, trail_width=1, trail_alpha_decay=0.2, show_rotation_indicator=False
        )
        
        # === 2. 节拍脉冲 ===
        # 强节拍时从中心爆发，带拖尾和颜色渐变
        self.pulse_ps = ParticleSystem(max_particles=400)
        self.pulse_ps.add_force_field(
            ForceField('attraction', x=WIDTH / 2, y=HEIGHT / 2, strength=20.0)
        )
        self.pulse_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.5, show_rotation_indicator=False
        )
        
        # === 3. 奇点轨道 ===
        # 围绕中心漩涡运动，带长拖尾
        self.orbit_ps = ParticleSystem(max_particles=150)
        vortex = create_vortex(WIDTH / 2, HEIGHT / 2, strength=3.0, clockwise=True)
        self.orbit_ps.add_force_field(vortex)
        self.orbit_ps.add_force_field(
            ForceField('turbulence', strength=0.5, turb_scale=60.0, turb_strength=0.5)
        )
        orbit_emitter = Emitter(
            x=WIDTH / 2, y=HEIGHT / 2,
            rate=8,
            spread=math.pi * 2,
            speed=1.8,
            life=8.0,
            size=2.5,
            color=(200, 75, 75),
            trail_enabled=True,
            trail_length=14,
            color_over_lifetime=gradient_to_curve([
                (255, 140, 100), (200, 75, 75), (140, 45, 45), (60, 20, 20)
            ]),
            size_over_lifetime=size_curve_fadeout(2.5),
            shape=EmitterShape('sphere', radius=30, emit_from_volume=True),
        )
        self.orbit_ps.add_emitter(orbit_emitter)
        self.orbit_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.6, show_rotation_indicator=False
        )
        
        # === 4. 结构边缘流光 ===
        # 沿 Penrose 结构对角线缓慢移动
        self.edge_ps = ParticleSystem(max_particles=200)
        self.edge_ps.add_force_field(
            ForceField('turbulence', strength=0.4, turb_scale=40.0, turb_strength=0.4)
        )
        self.edge_renderer = PygameRenderer(
            self.screen, trail_width=1, trail_alpha_decay=0.7, show_rotation_indicator=False
        )
        
        # === 5. 奇点曲线发光 ===
        # 沿奇点曲线缓慢飘动
        self.singularity_ps = ParticleSystem(max_particles=100)
        singularity_emitter = Emitter(
            x=WIDTH / 2, y=HEIGHT / 2,
            rate=5,
            spread=math.pi * 2,
            speed=0.8,
            life=5.0,
            size=2.0,
            color=(160, 50, 50),
            trail_enabled=True,
            trail_length=8,
            color_over_lifetime=gradient_to_curve([
                (200, 80, 80), (160, 50, 50), (100, 30, 30)
            ]),
            size_over_lifetime=size_curve_pulse(2.0, peak_at=0.3),
            shape=EmitterShape('circle', radius=60, emit_from_shell=True),
        )
        self.singularity_ps.add_emitter(singularity_emitter)
        self.singularity_ps.add_force_field(
            ForceField('attraction', x=WIDTH / 2, y=HEIGHT / 2, strength=10.0)
        )
        self.singularity_renderer = PygameRenderer(
            self.screen, trail_width=2, trail_alpha_decay=0.5, show_rotation_indicator=False
        )
    
    def _trigger_pulse(self, volume: float):
        """触发节拍脉冲爆发"""
        intensity = volume
        count = int(40 + intensity * 60)
        base_speed = 4.0 + intensity * 7.0
        life = 0.6 + intensity * 1.0
        
        # 颜色随强度变化
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
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            p = Particle(
                x=WIDTH / 2 + random.uniform(-5, 5),
                y=HEIGHT / 2 + random.uniform(-5, 5),
                vx=vx, vy=vy,
                life=1.0, max_life=life * random.uniform(0.8, 1.2),
                size=2.0 + intensity * 2.5,
                color=bright_color,
                alpha=1.0,
                trail_enabled=True,
                trail_max_length=10,
                color_over_lifetime=gradient_to_curve([bright_color, COLOR, dark_color]),
                size_over_lifetime=size_curve_pulse(2.0 + intensity * 2.5, peak_at=0.2),
            )
            p.enable_trail(10)
            self.pulse_ps.particles.append(p)
    
    def _trigger_edge_flow(self, volume: float, elapsed_ms: int):
        """沿结构边缘发射流光粒子"""
        pulse = 1 + volume * 0.8
        max_angle = 1.35 * pulse * (1 + 0.1 * math.sin(elapsed_ms * 0.001))
        
        a = self.Particle.to_screen(-max_angle, -max_angle)
        b = self.Particle.to_screen(max_angle, max_angle)
        c = self.Particle.to_screen(max_angle, -max_angle)
        
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
                color=HORIZON,
                alpha=0.6,
                trail_enabled=True,
                trail_max_length=5,
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
            P, Q = self.Particle.penrose(u, v * sign)
            x, y = self.Particle.to_screen(P, Q)
            
            # 沿曲线切线方向
            tangent_u = 0.05
            tangent_v = (u * tangent_u) / max(v, 0.1)
            tangent_P, tangent_Q = self.Particle.penrose(u + tangent_u, (v + tangent_v) * sign)
            tx, ty = self.Particle.to_screen(tangent_P, tangent_Q)
            dx = (tx - x) * 0.1
            dy = (ty - y) * 0.1
            
            color = SINGULARITY
            bright_color = (
                int(min(255, color[0] * (1.2 + volume * 0.3))),
                int(min(255, color[1] * (0.8 + volume * 0.2))),
                int(min(255, color[2] * (0.8 + volume * 0.2))),
            )
            
            p = Particle(
                x=x, y=y,
                vx=dx + random.uniform(-0.5, 0.5),
                vy=dy + random.uniform(-0.5, 0.5),
                life=1.0, max_life=random.uniform(1.5, 3.5),
                size=random.uniform(1.5, 3.0),
                color=bright_color,
                alpha=0.8,
                trail_enabled=True,
                trail_max_length=6,
                color_over_lifetime=gradient_to_curve([bright_color, color, (60, 20, 20)]),
                size_over_lifetime=size_curve_fadeout(2.5),
            )
            p.enable_trail(6)
            self.singularity_ps.particles.append(p)
    
    class Particle:
        def __init__(self):
            self.reset()
            self.trail = deque(maxlen=25)
            
        def reset(self):
            self.age = 0
            self.max_age = random.randint(300, 800)
            self.t = 0
            self.dt = random.uniform(0.001, 0.005)
            self.path = random.choice([
                lambda t: (0.2 + t * 3, 0.2 + t * 3),
                lambda t: (0.2 + t * 3, -0.2 - t * 3),
                lambda t: (1 + t * 2, math.sqrt((1 + t * 2) ** 2 - 1))
            ])
            self.size = random.uniform(0.8, 1.5)
        
        def update(self, speed=1.0):
            self.age += 1
            self.t += self.dt * speed
            if self.t > 1 or self.age > self.max_age:
                self.reset()
                
            u, v = self.path(self.t)
            P, Q = self.penrose(u, v)
            x, y = self.to_screen(P, Q)
            self.trail.append((x, y, self.age / self.max_age))
        
        def draw(self, surf, volume=0.5):
            if not self.trail:
                return
            
            # 增强: 光晕效果（大范围的微弱发光）
            if len(self.trail) >= 2:
                last_x, last_y, _ = self.trail[-1]
                glow_size = int(self.size * 6 * (1 + volume * 0.8))
                if glow_size > 2:
                    glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                    glow_alpha = int(20 * (1 + volume * 0.5))
                    glow_color = (*COLOR, glow_alpha)
                    pygame.draw.circle(glow, glow_color, (glow_size // 2, glow_size // 2), glow_size // 2)
                    surf.blit(glow, (int(last_x) - glow_size // 2, int(last_y) - glow_size // 2), special_flags=pygame.BLEND_ADD)
            
            for i, (x, y, alpha_ratio) in enumerate(self.trail):
                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    t = i / len(self.trail)
                    alpha = int(255 * alpha_ratio * t * (0.8 + volume * 0.4))
                    
                    # 增强: 颜色随生命周期和音频变化
                    life_t = 1.0 - (self.age / self.max_age)
                    r = int(min(255, COLOR[0] * (1.0 + life_t * 0.4 + volume * 0.3)))
                    g = int(min(255, COLOR[1] * (0.9 + life_t * 0.2 + volume * 0.2)))
                    b = int(min(255, COLOR[2] * (0.9 + life_t * 0.2 + volume * 0.2)))
                    
                    size = int(self.size * t * 3 * (1 + volume * 0.5))
                    if size > 0:
                        dot = pygame.Surface((size, size), pygame.SRCALPHA)
                        color_with_alpha = (r, g, b, alpha)
                        pygame.draw.circle(dot, color_with_alpha, (size // 2, size // 2), max(1, size // 2))
                        surf.blit(dot, (int(x) - size // 2, int(y) - size // 2))
        
        @staticmethod
        def penrose(u, v):
            return math.atan(u), math.atan(v)
        
        @staticmethod
        def to_screen(P, Q):
            scale = min(WIDTH, HEIGHT) * 0.28
            return int(WIDTH / 2 + P * scale), int(HEIGHT / 2 - Q * scale)
    
    def draw_structure(self, volume, time_factor):
        pulse = 1 + volume * 0.8
        max_angle = 1.35 * pulse * (1 + 0.1 * math.sin(time_factor * 0.001))
        
        # 动态颜色
        horizon_color = (
            int(HORIZON[0] * (1 + volume * 0.3)),
            int(HORIZON[1] * (1 + volume * 0.2)),
            int(HORIZON[2] * (1 + volume * 0.4))
        )
        
        # 对角线
        a = self.Particle.to_screen(-max_angle, -max_angle)
        b = self.Particle.to_screen(max_angle, max_angle)
        c = self.Particle.to_screen(max_angle, -max_angle)
        
        # 增强: 线条发光效果
        line_glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(line_glow, (*horizon_color, int(40 * (1 + volume))), a, b, 4)
        pygame.draw.line(line_glow, (*horizon_color, int(40 * (1 + volume))), a, c, 4)
        self.screen.blit(line_glow, (0, 0), special_flags=pygame.BLEND_ADD)
        
        pygame.draw.line(self.screen, horizon_color, a, b, 2)
        pygame.draw.line(self.screen, horizon_color, a, c, 2)
        
        # 奇点曲线
        pts_up, pts_down = [], []
        curve_points = 80
        for i in range(curve_points):
            u = (1 + i * 0.05) * pulse
            v = math.sqrt(max(u * u - 1, 0))
            pts_up.append(self.Particle.to_screen(*self.Particle.penrose(u, v)))
            pts_down.append(self.Particle.to_screen(*self.Particle.penrose(u, -v)))
        
        for i in range(len(pts_up)-1):
            alpha = int(200 * (1 - i/curve_points) * (0.5 + volume * 0.5))
            color_up = (*SINGULARITY, alpha)
            color_down = (*SINGULARITY, alpha)
            
            line_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(line_surf, color_up, pts_up[i], pts_up[i+1], 2)
            pygame.draw.line(line_surf, color_down, pts_down[i], pts_down[i+1], 2)
            self.screen.blit(line_surf, (0, 0))
    
    def draw_time_display(self, elapsed_ms):
        hours = int(elapsed_ms // 3600000)
        minutes = int((elapsed_ms % 3600000) // 60000)
        seconds = int((elapsed_ms % 60000) // 1000)
        
        time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        text_surface = self._font_large.render(time_text, True, (150, 150, 150))
        self.screen.blit(text_surface, (20, 20))
        
        # FPS显示
        fps = self.clock.get_fps()
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = self._font_small.render(fps_text, True, (100, 100, 100))
        self.screen.blit(fps_surface, (20, 60))
        
        # 增强: 显示总粒子数量
        total = (len(self.particles) + self.dust_ps.get_particle_count() +
                 self.pulse_ps.get_particle_count() + self.orbit_ps.get_particle_count() +
                 self.edge_ps.get_particle_count() + self.singularity_ps.get_particle_count())
        count_text = f"Particles: {total}"
        count_surface = self._font_small.render(count_text, True, (100, 100, 100))
        self.screen.blit(count_surface, (20, 90))
    
    def run(self):
        running = True
        last_volume = 0.5
        
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP:
                        with shared_state.lock:
                            shared_state.volume = min(shared_state.volume + 0.1, 1.0)
                    elif e.key == pygame.K_DOWN:
                        with shared_state.lock:
                            shared_state.volume = max(shared_state.volume - 0.1, 0.0)
            
            # 从共享状态获取音量
            with shared_state.lock:
                volume = shared_state.volume
            
            # 平滑音量变化
            volume = last_volume * 0.9 + volume * 0.1
            last_volume = volume
            
            speed = 0.5 + volume * 2.0
            
            # 动态调整原始粒子数量
            target_particles = int(20 + volume * 60)
            while len(self.particles) < target_particles:
                self.particles.append(self.Particle())
            while len(self.particles) > target_particles:
                self.particles.pop()
            
            elapsed_ms = int((time.time() - self.start_time) * 1000)
            
            # === 渲染帧 ===
            self.screen.fill(BG)
            
            # 1. 背景星尘（最底层）
            self.dust_ps.update(1/60, audio_data={'rms': volume * 0.3})
            self.dust_ps.render(self.dust_renderer)
            
            # 2. 结构线条
            self.draw_structure(volume, elapsed_ms)
            
            # 3. 奇点曲线流光
            if random.random() < volume * 0.3:
                self._trigger_singularity_flow(volume, elapsed_ms)
            self.singularity_ps.update(1/60)
            self.singularity_ps.render(self.singularity_renderer)
            
            # 4. 边缘流光
            if random.random() < volume * 0.2:
                self._trigger_edge_flow(volume, elapsed_ms)
            self.edge_ps.update(1/60)
            self.edge_ps.render(self.edge_renderer)
            
            # 5. 奇点轨道
            self.orbit_ps.update(1/60, audio_data={'rms': volume * 0.5})
            self.orbit_ps.render(self.orbit_renderer)
            
            # 6. 原始 Penrose 路径粒子
            for p in self.particles:
                p.update(speed)
                p.draw(self.screen, volume)
            
            # 7. 节拍脉冲（最顶层）
            self.beat_cooldown -= 1/60
            if volume > 0.5 and self.beat_cooldown <= 0 and self.last_volume <= 0.5:
                self._trigger_pulse(volume)
                self.beat_cooldown = 0.25  # 250ms 冷却
            
            self.pulse_ps.update(1/60)
            self.pulse_ps.render(self.pulse_renderer)
            
            self.last_volume = volume
            
            self.draw_time_display(elapsed_ms)
            
            pygame.display.flip()
            self.clock.tick(60)
            self.fps_history.append(self.clock.get_fps())
        
        pygame.quit()

# ==================== 主程序 ====================
def main():
    print("启动 24 小时时空滑板系统 — 粒子增强版...")
    print("=" * 50)
    print("控制说明:")
    print("  ESC - 退出")
    print("  上/下 - 调节音量")
    print("=" * 50)
    
    # 创建并启动音频引擎
    audio_engine = AudioEngine()
    audio_engine.start()
    
    # 创建并启动可视化引擎
    visual_engine = VisualEngine()
    
    try:
        visual_engine.run()
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        audio_engine.stop()
        print("系统已安全关闭")

if __name__ == "__main__":
    main()
