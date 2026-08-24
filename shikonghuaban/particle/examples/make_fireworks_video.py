"""
烟花秀视频生成器 v2.0
基于 D:/allin/tools/particle 粒子系统

v2.0 变化：
- render_particles_to_layer 改用引擎的 LayeredPILRenderer（P6）
- apply_bloom 改用引擎内置 post_process_bloom（P5）
- 粒子渲染自动使用 Additive 混合 + Catmull-Rom 平滑拖尾（P2/P7）
- example 代码量大幅减少
"""

import os
import math
import random
import struct
import wave
import subprocess
import tempfile
import shutil
import numpy as np
from PIL import Image, ImageDraw

# ====== 路径设置 ======
from ..systems.fireworks_system import FireworksSystem
from ..renderers.pil_renderer import LayeredPILRenderer, post_process_bloom

# ====== 视频参数 ======
WIDTH, HEIGHT = 1280, 720
FPS = 30
DURATION = 32          # 秒
TOTAL_FRAMES = FPS * DURATION
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(tempfile.gettempdir(), "_fw_frames")
FRAMES_DIR = TEMP_DIR
AUDIO_PATH = os.path.join(OUTPUT_DIR, "Fireworks  Royalty-free Music.mp3")
VIDEO_TMP = os.path.join(TEMP_DIR, "fireworks_noaudio.mp4")
VIDEO_OUT = os.path.join(OUTPUT_DIR, "fireworks_show.mp4")


# ============================================================
#  合成音效（保留原版，未改动）
# ============================================================

def synthesize_fireworks_audio(duration_sec: float, sample_rate: int = 44100) -> np.ndarray:
    total_samples = int(duration_sec * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float64)
    rng = np.random.default_rng(42)

    def add_explosion(t_sec, intensity=1.0, duration_ms=300):
        t_start = int(t_sec * sample_rate)
        dur = int(duration_ms / 1000 * sample_rate)
        if t_start >= total_samples: return
        dur = min(dur, total_samples - t_start)
        noise = rng.uniform(-1.0, 1.0, dur)
        env = np.exp(-np.linspace(0, 12, dur))
        t_arr = np.arange(dur) / sample_rate
        boom_freq = rng.uniform(55, 100)
        boom = 0.6 * np.sin(2 * math.pi * boom_freq * t_arr) * env
        audio[t_start:t_start + dur] += intensity * (noise * env * 0.7 + boom)

    def add_whistle(t_sec, intensity=0.5):
        t_start = int(t_sec * sample_rate)
        dur = int(0.8 * sample_rate)
        if t_start >= total_samples: return
        dur = min(dur, total_samples - t_start)
        t_arr = np.arange(dur) / sample_rate
        freq = 400.0 + (1200.0 - 400.0) * (t_arr / (dur / sample_rate))
        phase = 2 * math.pi * np.cumsum(freq) / sample_rate
        env = np.sin(np.pi * t_arr / (dur / sample_rate)) ** 0.3
        audio[t_start:t_start + dur] += intensity * np.sin(phase) * env

    def add_crackle(t_sec, intensity=0.4, duration_sec_=1.5):
        t_start = int(t_sec * sample_rate)
        dur = int(duration_sec_ * sample_rate)
        if t_start >= total_samples: return
        dur = min(dur, total_samples - t_start)
        num_pops = int(duration_sec_ * 40)
        signal = np.zeros(dur)
        for _ in range(num_pops):
            pos = rng.integers(0, dur)
            amp = rng.uniform(0.1, 1.0) * intensity
            pop_dur = rng.integers(10, 80)
            pop_dur = min(pop_dur, dur - pos)
            t_pop = np.arange(pop_dur) / sample_rate
            env = np.exp(-np.linspace(0, 8, pop_dur))
            freq = rng.uniform(600, 3000)
            signal[pos:pos + pop_dur] += amp * np.sin(2 * math.pi * freq * t_pop) * env
        overall_env = np.exp(-np.linspace(0, 4, dur))
        signal *= overall_env
        audio[t_start:t_start + dur] += signal

    def add_crowd(duration_sec_, intensity=0.08):
        dur = total_samples
        noise = rng.uniform(-1.0, 1.0, dur)
        t_arr = np.arange(dur) / sample_rate
        hum = (np.sin(2 * math.pi * 240 * t_arr) * 0.3 +
               np.sin(2 * math.pi * 380 * t_arr) * 0.2 +
               np.sin(2 * math.pi * 520 * t_arr) * 0.15)
        mod = 0.5 + 0.5 * np.sin(2 * math.pi * 0.3 * t_arr)
        env = np.linspace(0, 1, dur) ** 0.3
        audio[:] += intensity * noise * 0.4 * env
        audio[:] += intensity * hum * mod * env

    launch_times = []
    t = 1.0
    while t < duration_sec - 3:
        launch_times.append(t)
        t += random.uniform(0.8, 2.0)

    add_crowd(duration_sec)
    for lt in launch_times:
        add_whistle(lt, intensity=rng.uniform(0.3, 0.6))
        explode_t = lt + random.uniform(0.6, 1.0)
        add_explosion(explode_t, intensity=rng.uniform(0.7, 1.2),
                      duration_ms=rng.uniform(200, 400))
        add_crackle(explode_t + 0.1, intensity=rng.uniform(0.2, 0.5),
                    duration_sec_=rng.uniform(1.0, 2.5))

    finale_start = duration_sec - 6
    for i in range(8):
        t_ = finale_start + i * 0.6
        add_whistle(t_, intensity=0.5)
        add_explosion(t_ + 0.5, intensity=1.3, duration_ms=500)
        add_crackle(t_ + 0.6, intensity=0.6, duration_sec_=2.0)

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.9
    return (audio * 32767).astype(np.int16)


def write_wav(path, samples, sample_rate=44100):
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


# ============================================================
#  背景生成（保留原版）
# ============================================================

def make_gradient_sky(width, height, t_norm):
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    phase = t_norm * 2 * math.pi
    top_r = int(5 + 8 * math.sin(phase * 0.7))
    top_g = int(5 + 10 * math.sin(phase * 0.5 + 1.0))
    top_b = int(20 + 25 * math.sin(phase * 0.3))
    bot_r = int(15 + 20 * math.sin(phase * 0.4 + 0.5))
    bot_g = int(8 + 12 * math.sin(phase * 0.6))
    bot_b = int(30 + 35 * math.sin(phase * 0.2 + 2.0))
    for y in range(height):
        t = y / height
        r = max(0, min(255, int(top_r + (bot_r - top_r) * t)))
        g = max(0, min(255, int(top_g + (bot_g - top_g) * t)))
        b = max(0, min(255, int(top_b + (bot_b - top_b) * t)))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def make_city_silhouette(width, height):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(12345)
    horizon_y = int(height * 0.82)
    x = 0
    while x < width:
        bw = rng.randint(40, 120)
        bh = rng.randint(50, 200)
        by = horizon_y - bh
        building_r = rng.randint(15, 35)
        building_g = rng.randint(12, 30)
        building_b = rng.randint(20, 40)
        draw.rectangle([x, by, x + bw, height], fill=(building_r, building_g, building_b, 255))
        num_floors = bh // 15
        num_cols = bw // 12
        for row in range(num_floors):
            for col in range(num_cols):
                if rng.random() < 0.35:
                    wx = x + col * 12 + 3
                    wy = by + row * 15 + 3
                    wr = rng.randint(200, 255)
                    wg = rng.randint(160, 220)
                    wb = rng.randint(80, 160)
                    draw.rectangle([wx, wy, wx + 5, wy + 7], fill=(wr, wg, wb, 200))
        x += bw + rng.randint(0, 20)
    draw.rectangle([0, horizon_y, width, height], fill=(10, 8, 15, 255))
    return img


def draw_stars(draw, width, height, star_list, frame_idx):
    for (sx, sy, sbrightness, sphase) in star_list:
        if sy > height * 0.75:
            continue
        flicker = 0.7 + 0.3 * math.sin(frame_idx * 0.05 + sphase)
        bright = max(0, min(255, int(sbrightness * flicker)))
        if sbrightness > 180:
            draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(bright, bright, bright))
            draw.line([(sx-3, sy), (sx+3, sy)], fill=(bright//2, bright//2, bright//2))
            draw.line([(sx, sy-3), (sx, sy+3)], fill=(bright//2, bright//2, bright//2))
        else:
            draw.point((sx, sy), fill=(bright, bright, bright))


# ============================================================
#  主渲染流程（v2.0 — 使用引擎能力）
# ============================================================

def render_frames():
    os.makedirs(FRAMES_DIR, exist_ok=True)

    print(f"初始化烟花系统 ({WIDTH}x{HEIGHT})...")
    fw = FireworksSystem(
        width=WIDTH, height=HEIGHT,
        auto_launch=True,
        launch_interval=1.0,
        max_active=8,
    )

    # v2.0：创建分层渲染器（P6），自带 Bloom（P5）、Additive 混合（P2）、平滑拖尾（P7）
    layered_renderer = LayeredPILRenderer(
        width=WIDTH, height=HEIGHT,
        bloom=True,
        bloom_radius=10,
        bloom_strength=0.5,
        bloom_threshold=150,
        glow_scale=2.5,
        glow_alpha=0.3,
        smooth_trail=True,
    )

    print("生成星空...")
    rng_stars = random.Random(999)
    stars = []
    for _ in range(300):
        stars.append((
            rng_stars.randint(0, WIDTH),
            rng_stars.randint(0, int(HEIGHT * 0.75)),
            rng_stars.randint(80, 255),
            rng_stars.uniform(0, 2 * math.pi),
        ))

    print("生成城市剪影...")
    city = make_city_silhouette(WIDTH, HEIGHT)

    dt = 1.0 / FPS
    print(f"开始渲染 {TOTAL_FRAMES} 帧...")

    for frame_idx in range(TOTAL_FRAMES):
        t_norm = frame_idx / TOTAL_FRAMES

        # 1. 更新粒子
        fw.update(dt)

        # 2. 夜空背景
        bg = make_gradient_sky(WIDTH, HEIGHT, t_norm)
        draw_bg = ImageDraw.Draw(bg)

        # 3. 星空
        draw_stars(draw_bg, WIDTH, HEIGHT, stars, frame_idx)

        # 4. 城市剪影
        bg_rgba = bg.convert('RGBA')
        bg_rgba = Image.alpha_composite(bg_rgba, city)
        bg_rgb = bg_rgba.convert('RGB')

        # 5. v2.0: 分层渲染粒子（引擎内置 Additive + Bloom）
        result_rgb = layered_renderer.render_to_image(
            fw.particles,
            background=bg_rgb,
        )

        # 6. 火箭亮点（保留，轻量绘制）
        draw_result = ImageDraw.Draw(result_rgb)
        for rocket in fw.rockets:
            rx, ry = int(rocket['x']), int(rocket['y'])
            draw_result.ellipse([rx-2, ry-2, rx+2, ry+2], fill=(255, 220, 120))

        # 7. 保存帧
        frame_path = os.path.join(FRAMES_DIR, f"frame_{frame_idx:05d}.jpg")
        result_rgb.save(frame_path, quality=92)

        if frame_idx % 30 == 0:
            pct = frame_idx / TOTAL_FRAMES * 100
            print(f"  [{pct:.1f}%] 帧 {frame_idx}/{TOTAL_FRAMES} "
                  f"— 粒子数: {fw.particle_count}, 火箭数: {fw.rocket_count}")

    print(f"帧渲染完成！共 {TOTAL_FRAMES} 帧")


def encode_video():
    print("编码视频（无音频）...")
    frame_pattern = os.path.join(FRAMES_DIR, "frame_%05d.jpg")
    cmd_video = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", frame_pattern,
        "-vcodec", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        VIDEO_TMP,
    ]
    result = subprocess.run(cmd_video, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg stderr:", result.stderr[-2000:])
        raise RuntimeError("视频编码失败")
    print(f"视频编码完成: {VIDEO_TMP}")

    print("合并音频...")
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", VIDEO_TMP,
        "-i", AUDIO_PATH,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        VIDEO_OUT,
    ]
    result = subprocess.run(cmd_audio, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg stderr:", result.stderr[-2000:])
        raise RuntimeError("音视频合并失败")
    print(f"最终视频: {VIDEO_OUT}")


def cleanup():
    print("清理临时帧...")
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    if os.path.exists(VIDEO_TMP):
        os.remove(VIDEO_TMP)
    print("清理完成")


if __name__ == "__main__":
    import time
    t0 = time.time()

    print("=" * 60)
    print("  烟花秀视频生成器 v2.0")
    print("  基于 D:/allin/tools/particle 粒子系统")
    print("=" * 60)

    assert os.path.exists(AUDIO_PATH), f"音效文件不存在: {AUDIO_PATH}"
    print(f"使用真实音效: {os.path.basename(AUDIO_PATH)}")

    render_frames()
    encode_video()
    cleanup()

    elapsed = time.time() - t0
    print(f"\n完成！总耗时: {elapsed:.1f} 秒")
    print(f"输出视频: {VIDEO_OUT}")
