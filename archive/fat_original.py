import math
import random
import struct
import numpy as np
import pygame
import sounddevice as sd
import threading
import time
from collections import deque

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
        print("🔊 音频引擎已启动")
    
    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("🔇 音频引擎已停止")

# ==================== 可视化引擎 ====================
class VisualEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mouse.set_visible(False)
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("24-Hour Spacetime Audio")
        
        self.DOT = pygame.Surface((3, 3), pygame.SRCALPHA)
        pygame.draw.circle(self.DOT, (255, 255, 255), (1, 1), 1)
        
        self.particles = [self.Particle() for _ in range(30)]
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        
        # 性能监控
        self.fps_history = deque(maxlen=60)
    
    class Particle:
        def __init__(self):
            self.reset()
            self.trail = deque(maxlen=20)
            
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
        
        def draw(self, surf):
            if not self.trail:
                return
                
            for i, (x, y, alpha_ratio) in enumerate(self.trail):
                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    alpha = int(255 * alpha_ratio * (i / len(self.trail)))
                    size = int(self.size * (i / len(self.trail)) * 3)
                    if size > 0:
                        dot = pygame.Surface((size, size), pygame.SRCALPHA)
                        color_with_alpha = (*COLOR, alpha)
                        pygame.draw.circle(dot, color_with_alpha, (size//2, size//2), size//2)
                        surf.blit(dot, (x - size//2, y - size//2))
        
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
        
        font = pygame.font.Font(None, 36)
        time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        text_surface = font.render(time_text, True, (150, 150, 150))
        self.screen.blit(text_surface, (20, 20))
        
        # FPS显示
        fps = self.clock.get_fps()
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = font.render(fps_text, True, (100, 100, 100))
        self.screen.blit(fps_surface, (20, 60))
    
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
            
            # 动态调整粒子数量
            target_particles = int(20 + volume * 60)
            while len(self.particles) < target_particles:
                self.particles.append(self.Particle())
            while len(self.particles) > target_particles:
                self.particles.pop()
            
            elapsed_ms = int((time.time() - self.start_time) * 1000)
            
            self.screen.fill(BG)
            self.draw_structure(volume, elapsed_ms)
            
            for p in self.particles:
                p.update(speed)
                p.draw(self.screen)
            
            self.draw_time_display(elapsed_ms)
            
            pygame.display.flip()
            self.clock.tick(60)
            self.fps_history.append(self.clock.get_fps())
        
        pygame.quit()

# ==================== 主程序 ====================
def main():
    print("🛹 启动 24 小时时空滑板系统...")
    print("=" * 50)
    print("控制说明:")
    print("  ESC - 退出")
    print("  ↑/↓ - 调节音量")
    print("=" * 50)
    
    # 创建并启动音频引擎
    audio_engine = AudioEngine()
    audio_engine.start()
    
    # 创建并启动可视化引擎
    visual_engine = VisualEngine()
    
    try:
        visual_engine.run()
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
    finally:
        audio_engine.stop()
        print("✅ 系统已安全关闭")

if __name__ == "__main__":
    main()