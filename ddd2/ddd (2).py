import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
import os
import scipy.ndimage
import wave
import tempfile
import threading
import tkinter as tk
from tkinter import ttk
import queue
from datetime import datetime

# ==================== 视频参数 ====================
WIDTH, HEIGHT = 1280, 720
FPS = 24
DURATION = 20  # 延长到20秒
TOTAL_FRAMES = DURATION * FPS

# ==================== 元胞自动机 (Numba加速) ====================
def _jit_noop(*args, **kwargs):
    """Fallback decorator when numba is not available"""
    def decorator(func):
        return func
    return decorator

try:
    from numba import jit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    jit = _jit_noop
    print("提示: 安装 numba 可加速渲染 (pip install numba)")

CA_SIZE = 50

# 根据 numba 可用性选择合适的 jit 装饰器
_compile_jit = jit if HAS_NUMBA else _jit_noop

@_compile_jit(nopython=True, cache=True)
def update_ca_numba(grid):
    """Numba加速的Game of Life"""
    new_grid = grid.copy()
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            neighbors = (
                grid[(i-1) % grid.shape[0], (j-1) % grid.shape[1]] +
                grid[(i-1) % grid.shape[0], j] +
                grid[(i-1) % grid.shape[0], (j+1) % grid.shape[1]] +
                grid[i, (j-1) % grid.shape[1]] +
                grid[i, (j+1) % grid.shape[1]] +
                grid[(i+1) % grid.shape[0], (j-1) % grid.shape[1]] +
                grid[(i+1) % grid.shape[0], j] +
                grid[(i+1) % grid.shape[0], (j+1) % grid.shape[1]]
            )
            if grid[i, j] == 1:
                new_grid[i, j] = 1 if 2 <= neighbors <= 3 else 0
            else:
                new_grid[i, j] = 1 if neighbors == 3 else 0
    return new_grid

def update_ca_numpy(grid):
    """Numpy版本的Game of Life（无Numba时使用）"""
    new_grid = np.zeros_like(grid)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            neighbors = (
                grid[(i-1) % grid.shape[0], (j-1) % grid.shape[1]] +
                grid[(i-1) % grid.shape[0], j] +
                grid[(i-1) % grid.shape[0], (j+1) % grid.shape[1]] +
                grid[i, (j-1) % grid.shape[1]] +
                grid[i, (j+1) % grid.shape[1]] +
                grid[(i+1) % grid.shape[0], (j-1) % grid.shape[1]] +
                grid[(i+1) % grid.shape[0], j] +
                grid[(i+1) % grid.shape[0], (j+1) % grid.shape[1]]
            )
            if grid[i, j] == 1:
                new_grid[i, j] = 1 if 2 <= neighbors <= 3 else 0
            else:
                new_grid[i, j] = 1 if neighbors == 3 else 0
    return new_grid

update_ca = update_ca_numba if HAS_NUMBA else update_ca_numpy

# 多个CA网格（不同规则）
ca_grids = {
    'gol': np.random.choice([0, 1], size=(CA_SIZE, CA_SIZE), p=[0.75, 0.25]),  # Game of Life
    'lava': np.random.choice([0, 1], size=(CA_SIZE, CA_SIZE), p=[0.6, 0.4]),   # 熔岩灯效果
    'pulse': np.random.choice([0, 1], size=(CA_SIZE, CA_SIZE), p=[0.85, 0.15]), # 脉冲效果
}

def draw_ca_grid(img, ca_grid, x, y, cell_size, color, alpha=120):
    """绘制元胞自动机"""
    r, g, b = color
    for i in range(len(ca_grid)):
        for j in range(len(ca_grid[0])):
            if ca_grid[i, j] == 1:
                for di in range(cell_size):
                    for dj in range(cell_size):
                        px, py = x + j * cell_size + dj, y + i * cell_size + di
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            img.putpixel((px, py), (r, g, b, alpha))

# ==================== 分形几何 - 曼德勃罗集 ====================
def generate_mandelbrot_chunked(width, height, max_iter=50, zoom=1.0, center=(-0.5, 0)):
    """生成曼德勃罗集（简化版用于动画）"""
    result = np.zeros((height, width), dtype=np.float32)
    x_min, x_max = center[0] - 2/zoom, center[0] + 2/zoom
    y_min, y_max = center[1] - 2/zoom, center[1] + 2/zoom
    
    x_scale = np.linspace(x_min, x_max, width)
    y_scale = np.linspace(y_min, y_max, height)
    
    for i, y in enumerate(y_scale):
        for j, x in enumerate(x_scale):
            c = complex(x, y)
            z = 0
            for n in range(max_iter):
                if abs(z) > 2:
                    result[i, j] = n / max_iter
                    break
                z = z * z + c
    return result

mandelbrot_cache = None

def draw_mandelbrot(img, t, x, y, size):
    """绘制动态曼德勃罗集"""
    global mandelbrot_cache
    
    # 每秒更新一次
    zoom = 1.0 + t * 0.1
    max_iter = int(30 + t * 2)
    
    if mandelbrot_cache is None or t < 0.1:
        w, h = size, size
        x_min, x_max = -2.0/zoom, 0.5/zoom
        y_min, y_max = -1.0/zoom, 1.0/zoom
        
        mandelbrot_cache = np.zeros((h, w), dtype=np.float32)
        x_scale = np.linspace(x_min, x_max, w)
        y_scale = np.linspace(y_min, y_max, h)
        
        for i, yc in enumerate(y_scale):
            for j, xc in enumerate(x_scale):
                c = complex(xc, yc)
                z = 0
                for n in range(max_iter):
                    if abs(z) > 2:
                        mandelbrot_cache[i, j] = n / max_iter
                        break
                    z = z * z + c
    
    # 绘制到图像
    cell_size = size // len(mandelbrot_cache[0])
    for i in range(len(mandelbrot_cache)):
        for j in range(len(mandelbrot_cache[0])):
            val = mandelbrot_cache[i, j]
            if val > 0:
                color_r = int(255 * val)
                color_g = int(100 * np.sin(val * 10 + t))
                color_b = int(200 * (1 - val))
                for di in range(cell_size):
                    for dj in range(cell_size):
                        px, py = x + j * cell_size + dj, y + i * cell_size + di
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            img.putpixel((px, py), (color_r, color_g, color_b, 80))

# ==================== CNN 卷积效果（多种滤镜） ====================
def apply_cnn_effect(img_array, effect_type, intensity=0.3):
    """应用多种CNN卷积效果"""
    img_float = img_array.astype(np.float32) / 255.0
    
    if effect_type == 'edge':
        # 边缘检测 (Sobel)
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / 4.0
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / 4.0
        edges = np.zeros_like(img_float)
        for c in range(3):
            ex = scipy.ndimage.convolve(img_float[:,:,c], sobel_x)
            ey = scipy.ndimage.convolve(img_float[:,:,c], sobel_y)
            edges[:,:,c] = np.sqrt(ex**2 + ey**2)
        result = img_float * (1 - intensity) + edges * intensity
        
    elif effect_type == 'blur':
        # 高斯模糊 (使用手动卷积核)
        kernel = np.array([[1, 4, 6, 4, 1], [4, 16, 24, 16, 4], [6, 24, 36, 24, 6], [4, 16, 24, 16, 4], [1, 4, 6, 4, 1]]) / 256.0
        blurred = np.zeros_like(img_float)
        for c in range(3):
            blurred[:,:,c] = scipy.ndimage.convolve(img_float[:,:,c], kernel)
        result = img_float * (1 - intensity) + blurred * intensity
        
    elif effect_type == 'sharpen':
        # 锐化
        sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = np.zeros_like(img_float)
        for c in range(3):
            sharpened[:,:,c] = scipy.ndimage.convolve(img_float[:,:,c], sharpen)
        result = img_float * (1 - intensity) + sharpened * intensity
        
    elif effect_type == 'emboss':
        # 浮雕效果
        emboss = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]])
        embossed = np.zeros_like(img_float)
        for c in range(3):
            embossed[:,:,c] = scipy.ndimage.convolve(img_float[:,:,c], emboss)
        result = img_float * (1 - intensity) + embossed * intensity + 0.5
    else:
        result = img_float
    
    return np.clip(result * 255, 0, 255).astype(np.uint8)

# ==================== 粒子系统 ====================
NUM_PARTICLES = 80
particles = []

def init_particles():
    global particles
    particles = []
    for _ in range(NUM_PARTICLES):
        particles.append({
            'x': np.random.randint(0, WIDTH),
            'y': np.random.randint(0, HEIGHT),
            'vx': np.random.uniform(-3, 3),
            'vy': np.random.uniform(-3, 3),
            'size': np.random.randint(2, 8),
            'color': tuple(np.random.randint(50, 255, 3).tolist()),
            'life': np.random.randint(50, 200)
        })

def update_particles():
    global particles
    for p in particles:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
        if p['life'] <= 0 or p['x'] < 0 or p['x'] > WIDTH or p['y'] < 0 or p['y'] > HEIGHT:
            p['x'] = np.random.randint(0, WIDTH)
            p['y'] = np.random.randint(0, HEIGHT)
            p['vx'] = np.random.uniform(-3, 3)
            p['vy'] = np.random.uniform(-3, 3)
            p['life'] = np.random.randint(100, 300)
            p['color'] = tuple(np.random.randint(50, 255, 3).tolist())

def draw_particles(img, t):
    """绘制粒子系统"""
    global particles
    if int(t * 12) > int((t - 1/FPS) * 12):
        update_particles()
    
    for p in particles:
        life_ratio = p['life'] / 300.0
        glow_size = max(1, int(p['size'] * life_ratio))
        color = p['color']
        
        for i in range(-glow_size, glow_size + 1):
            for j in range(-glow_size, glow_size + 1):
                dist = (i**2 + j**2) ** 0.5
                if 0 < dist <= glow_size:
                    px, py = int(p['x'] + i), int(p['y'] + j)
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        alpha = int(200 * (1 - dist/glow_size) * life_ratio)
                        img.putpixel((px, py), (*color, alpha))

# ==================== 音频生成（鼓点+Bass+合成器） ====================
def make_audio_clip():
    """生成完整音频：旋律 + 鼓点 + Bass + 合成器Pad"""
    sample_rate = 44100
    t = np.linspace(0, DURATION, int(sample_rate * DURATION), dtype=np.float32)
    audio = np.zeros(len(t), dtype=np.float32)
    
    # ==================== 旋律 ====================
    melody_freqs = [
        220, 247, 262, 294, 330, 349, 392, 440, 392, 349, 330, 294,
        262, 294, 330, 294, 262, 247, 262, 294, 330, 349, 392, 440,
        196, 220, 247, 262, 294, 330, 349, 392, 440, 392, 349, 330,
        294, 262, 247, 220, 196, 220, 247, 262, 294, 330, 349, 392,
    ]
    
    note_len = int(0.35 * sample_rate)
    num_notes = int(len(t) / note_len)
    
    for note_idx in range(num_notes):
        freq = melody_freqs[note_idx % len(melody_freqs)]
        start = note_idx * note_len
        end = min((note_idx + 1) * note_len, len(t))
        note_t = t[start:end] - t[start]
        
        # 合成器音色 (Saw Wave)
        note = 0.6 * (2 * (freq * note_t % 1) - 1)
        note += 0.3 * np.sin(2 * np.pi * freq * note_t)
        note += 0.15 * np.sin(2 * np.pi * freq * 2 * note_t)
        
        # ADSR 包络
        note_len_actual = end - start
        attack = int(0.01 * sample_rate)
        decay = int(0.04 * sample_rate)
        sustain_level = 0.75
        release = int(0.1 * sample_rate)
        
        envelope = np.ones(note_len_actual)
        if note_len_actual > attack + decay + release:
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[attack:attack+decay] = np.linspace(1, sustain_level, decay)
            envelope[attack+decay:-release] = sustain_level
            envelope[-release:] = np.linspace(sustain_level, 0, release)
        else:
            envelope = np.linspace(0, 1, note_len_actual) * np.linspace(1, 0, note_len_actual)
        
        audio[start:end] += note * envelope * 0.4
    
    # ==================== 鼓点 ====================
    # Kick (低频鼓点)
    kick_pattern = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]  # 每4拍
    kick_len = int(0.15 * sample_rate)
    for beat_idx in range(int(DURATION * 4)):
        if kick_pattern[beat_idx % len(kick_pattern)]:
            kick_start = int(beat_idx * sample_rate / 4)
            kick_t = np.linspace(0, 0.15, kick_len)
            kick = np.sin(2 * np.pi * 60 * kick_t * np.exp(-kick_t * 15))
            kick *= np.exp(-kick_t * 20)
            kick_end = min(kick_start + kick_len, len(audio))
            audio[kick_start:kick_end] += kick[:kick_end - kick_start] * 0.5
    
    # Snare (高频鼓点)
    snare_pattern = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
    snare_len = int(0.1 * sample_rate)
    for beat_idx in range(int(DURATION * 4)):
        if snare_pattern[beat_idx % len(snare_pattern)]:
            snare_start = int(beat_idx * sample_rate / 4)
            snare_t = np.linspace(0, 0.1, snare_len)
            snare = np.random.randn(snare_len) * np.exp(-snare_t * 30)
            snare += np.sin(2 * np.pi * 200 * snare_t) * np.exp(-snare_t * 40)
            snare_end = min(snare_start + snare_len, len(audio))
            audio[snare_start:snare_end] += snare[:snare_end - snare_start] * 0.3
    
    # Hi-Hat (踩镲)
    hihat_pattern = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    hihat_len = int(0.05 * sample_rate)
    for beat_idx in range(int(DURATION * 8)):
        if hihat_pattern[beat_idx % len(hihat_pattern)]:
            hihat_start = int(beat_idx * sample_rate / 8)
            hihat_t = np.linspace(0, 0.05, hihat_len)
            hihat = np.random.randn(hihat_len) * np.exp(-hihat_t * 100)
            hihat_end = min(hihat_start + hihat_len, len(audio))
            audio[hihat_start:hihat_end] += hihat[:hihat_end - hihat_start] * 0.15
    
    # ==================== Bass ====================
    bass_notes = [55, 55, 73, 73, 65, 65, 82, 82]  # A1, D2, C2, E2
    bass_pattern_len = len(bass_notes)
    bass_len = int(0.5 * sample_rate)
    for bar_idx in range(int(DURATION * 2)):
        for note_idx, bass_freq in enumerate(bass_notes):
            bass_start = int((bar_idx * bass_pattern_len + note_idx) * sample_rate / 2)
            if bass_start >= len(audio):
                break
            bass_end = min(bass_start + bass_len, len(audio))
            bass_t = t[:bass_end - bass_start] - t[0]
            
            # Bass音色 (正弦波 + 一点谐波)
            bass_wave = np.sin(2 * np.pi * bass_freq * bass_t)
            bass_wave += 0.3 * np.sin(2 * np.pi * bass_freq * 2 * bass_t)
            bass_wave += 0.1 * np.sin(2 * np.pi * bass_freq * 3 * bass_t)
            
            # Bass包络
            bass_env = np.ones(bass_end - bass_start)
            bass_attack = int(0.02 * sample_rate)
            bass_decay = int(0.08 * sample_rate)
            bass_sustain = int(0.3 * sample_rate)
            bass_release = int(0.1 * sample_rate)
            
            if bass_end - bass_start > bass_attack + bass_decay + bass_sustain + bass_release:
                bass_env[:bass_attack] = np.linspace(0, 1, bass_attack)
                bass_env[bass_attack:bass_attack+bass_decay] = np.linspace(1, 0.7, bass_decay)
                bass_env[bass_attack+bass_decay:bass_attack+bass_decay+bass_sustain] = 0.7
                bass_env[-bass_release:] = np.linspace(0.7, 0, bass_release)
            
            audio[bass_start:bass_end] += bass_wave * bass_env * 0.35
    
    # ==================== 合成器Pad ====================
    pad_freqs = [110, 138.6, 164.8, 220]  # Am7 和弦
    for pad_idx, pad_freq in enumerate(pad_freqs):
        pad = 0.08 * np.sin(2 * np.pi * pad_freq * t)
        pad += 0.04 * np.sin(2 * np.pi * pad_freq * 2 * t)
        # LFO调制
        lfo = 1 + 0.2 * np.sin(2 * np.pi * 0.3 * t + pad_idx)
        audio += pad * lfo
    
    # ==================== 混响效果 ====================
    delay_samples = int(0.08 * sample_rate)
    reverb = np.zeros_like(audio)
    reverb[delay_samples:] = audio[:-delay_samples] * 0.25
    reverb[delay_samples*2:] += audio[:-delay_samples*2] * 0.15
    audio += reverb
    
    # 全局限幅
    audio = np.clip(audio, -1, 1)
    
    # 转换为立体声
    left = audio * (1 + 0.1 * np.sin(2 * np.pi * 0.5 * t))
    right = audio * (1 + 0.1 * np.sin(2 * np.pi * 0.5 * t + np.pi/6))
    stereo = np.column_stack([left, right])
    
    return stereo, sample_rate

# ==================== 音频可视化数据 ====================
def get_audio_levels(audio_data, t, sample_rate):
    """获取音频电平用于可视化"""
    start_idx = max(0, int(t * sample_rate))
    end_idx = min(len(audio_data), start_idx + int(sample_rate * 0.05))
    if end_idx > start_idx:
        chunk = audio_data[start_idx:end_idx]
        return np.max(np.abs(chunk)), np.mean(np.abs(chunk))
    return 0, 0

# ==================== 颜色和字体 ====================
COLOR_THEMES = [
    ((20, 20, 60), (100, 20, 80)),    # 深紫蓝
    ((60, 20, 80), (20, 60, 100)),     # 紫青
    ((20, 60, 50), (60, 100, 80)),     # 青绿
    ((100, 40, 20), (140, 80, 40)),    # 暖橙
    ((30, 20, 100), (60, 40, 150)),    # 靛蓝
]

font_title = None
font_body = None
try:
    font_title = ImageFont.truetype("arial.ttf", 80)
    font_body = ImageFont.truetype("arial.ttf", 50)
except IOError:
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()

FONT_TITLE = font_title
FONT_BODY = font_body

init_particles()

# ==================== 文字内容 ====================
TEXT_SEGMENTS = [
    ("Hello, World!", 0, 3, "edge"),
    ("Welcome to the", 3, 5, "blur"),
    ("Future of", 5, 7, "sharpen"),
    ("AI Generation", 7, 9, "emboss"),
    ("Cellular Automata", 10, 12, "edge"),
    ("Neural Networks", 12, 14, "blur"),
    ("Fractal Geometry", 14, 16, "sharpen"),
    ("Audio Visualization", 16, 18, "emboss"),
    ("Thank You!", 18, 20, "edge"),
]

# ==================== 章节切换效果 ====================
def draw_transition(img, t, start_t, duration=0.5):
    """绘制章节切换动画"""
    if start_t <= t <= start_t + duration:
        progress = (t - start_t) / duration
        # 扫描线效果
        scan_y = int(progress * HEIGHT)
        draw = ImageDraw.Draw(img)
        for y in range(max(0, scan_y - 20), min(HEIGHT, scan_y + 20)):
            alpha = int(255 * (1 - abs(y - scan_y) / 20))
            draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, alpha))
        return True
    return False

# ==================== 主帧生成函数 ====================
audio_cache = None

def make_frame(t):
    """生成视频帧"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # 主题颜色
    theme_idx = int(t / 4) % len(COLOR_THEMES)
    bg_start, bg_end = COLOR_THEMES[theme_idx]
    
    # 获取音频电平
    global audio_cache
    if audio_cache is None:
        audio_cache, _ = make_audio_clip()
    peak, rms = get_audio_levels(audio_cache[:, 0], t, 44100)
    
    # 1. 动态渐变背景（音频响应）
    phase = (t % 4) / 4
    r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * phase + rms * 50)
    g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * phase)
    b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * phase + peak * 30)
    draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(r, g, b))
    
    # 2. 音频可视化 - 频谱条
    bar_count = 32
    bar_width = WIDTH // bar_count - 4
    for i in range(bar_count):
        # 模拟频谱
        freq = 0.5 + i * 0.3
        bar_height = int((50 + 100 * abs(np.sin(t * freq + i * 0.2)) + rms * 200) * (1 + peak * 0.5))
        bar_height = min(bar_height, 150)
        
        hue = (i * 10 + int(t * 50)) % 360
        bar_r = int(128 + 127 * np.sin(hue * np.pi / 180))
        bar_g = int(128 + 127 * np.sin((hue + 120) * np.pi / 180))
        bar_b = int(128 + 127 * np.sin((hue + 240) * np.pi / 180))
        
        x = i * (bar_width + 4) + 20
        y = HEIGHT - 60 - bar_height
        draw.rectangle([(x, y), (x + bar_width, HEIGHT - 40)], 
                      fill=(bar_r, bar_g, bar_b, 150),
                      outline=(255, 255, 255, 100))
    
    # 3. 动态网格
    grid_spacing = 50
    grid_offset = int(t * 40) % grid_spacing
    for x in range(-grid_offset, WIDTH, grid_spacing):
        alpha = 20 + int(15 * np.sin(t + x * 0.02))
        draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, alpha))
    for y in range(-grid_offset, HEIGHT, grid_spacing):
        alpha = 20 + int(15 * np.sin(t + y * 0.02))
        draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, alpha))
    
    # 4. 元胞自动机
    ca_update_rate = 6
    if int(t * ca_update_rate) > int((t - 1/FPS) * ca_update_rate):
        ca_grids['gol'][:] = update_ca(ca_grids['gol'])
        if t > 5:
            ca_grids['lava'][:] = update_ca(ca_grids['lava'])
        if t > 10:
            ca_grids['pulse'][:] = update_ca(ca_grids['pulse'])
    
    draw_ca_grid(img, ca_grids['gol'], 20, 20, 5, (0, 255, 180), 100)  # 左上
    if t > 5:
        draw_ca_grid(img, ca_grids['lava'], WIDTH - CA_SIZE*5 - 20, 20, 5, (255, 100, 50), 100)  # 右上
    if t > 10:
        draw_ca_grid(img, ca_grids['pulse'], 20, HEIGHT - CA_SIZE*5 - 80, 5, (180, 50, 255), 100)  # 左下
    
    # 5. 曼德勃罗分形
    if t > 8:
        draw_mandelbrot(img, t, WIDTH - CA_SIZE*5 - 20, HEIGHT - CA_SIZE*5 - 80, CA_SIZE*5)
    
    # 6. 粒子系统
    draw_particles(img, t)
    
    # 7. 几何图形组合
    center_x, center_y = WIDTH // 2, HEIGHT // 2 - 50
    
    # 外层旋转矩形
    outer_size = 200 + int(40 * np.sin(t * 2.5) + peak * 100)
    outer_angle = t * 60
    rect_outer = Image.new('RGBA', (outer_size, outer_size), (0, 0, 0, 0))
    rect_draw = ImageDraw.Draw(rect_outer)
    rect_draw.rectangle([(0, 0), (outer_size, outer_size)], outline=(0, 255, 150, 180), width=4)
    rotated_outer = rect_outer.rotate(outer_angle, expand=True)
    img.paste(rotated_outer, (center_x - rotated_outer.width//2, center_y - rotated_outer.height//2), rotated_outer)
    
    # 中层旋转多边形
    poly_size = 140 + int(25 * np.cos(t * 3))
    poly_angle = -t * 45
    poly_img = Image.new('RGBA', (poly_size*2, poly_size*2), (0, 0, 0, 0))
    poly_draw = ImageDraw.Draw(poly_img)
    points = []
    sides = 5
    for i in range(sides):
        angle = poly_angle + i * 2 * np.pi / sides
        px = poly_size*2//2 + int(poly_size * np.cos(angle))
        py = poly_size*2//2 + int(poly_size * np.sin(angle))
        points.append((px, py))
    poly_draw.polygon(points, fill=(255, 150, 50, 80), outline=(255, 200, 100, 180))
    img.paste(poly_img, (center_x - poly_size, center_y - poly_size), poly_img)
    
    # 内层圆形
    inner_size = 80 + int(15 * np.sin(t * 4 + peak * 50))
    inner_angle = t * 90
    circle_img = Image.new('RGBA', (inner_size*2, inner_size*2), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    circle_draw.ellipse([(0, 0), (inner_size*2, inner_size*2)], 
                       fill=(200, 100, 255, 120), outline=(255, 200, 100, 200), width=3)
    rotated_circle = circle_img.rotate(inner_angle, expand=True)
    img.paste(rotated_circle, (center_x - inner_size, center_y - inner_size), rotated_circle)
    
    # 8. 环绕粒子（音频响应）
    orbit_count = 12
    for i in range(orbit_count):
        base_radius = 250 + 40 * np.sin(t * 2 + i * 0.5)
        orbit_radius = base_radius + peak * 80
        orbit_angle = t * 1.5 + i * np.pi / (orbit_count / 2)
        px = int(center_x + orbit_radius * np.cos(orbit_angle))
        py = int(center_y + orbit_radius * np.sin(orbit_angle))
        
        hue = (i * 30 + int(t * 60)) % 360
        pr = int(255 * np.sin(hue * np.pi / 180))
        pg = int(255 * np.sin((hue + 120) * np.pi / 180))
        pb = int(255 * np.sin((hue + 240) * np.pi / 180))
        
        particle_size = 6 + int(peak * 20)
        for dx in range(-particle_size, particle_size + 1):
            for dy in range(-particle_size, particle_size + 1):
                if dx*dx + dy*dy <= particle_size * particle_size:
                    if 0 <= px+dx < WIDTH and 0 <= py+dy < HEIGHT:
                        img.putpixel((px+dx, py+dy), (pr, pg, pb, 200))
    
    # 9. 当前段文字
    current_text = ""
    current_start = 0
    current_effect = "edge"
    for text, start_t, end_t, effect in TEXT_SEGMENTS:
        if start_t <= t < end_t:
            current_text = text
            current_start = start_t
            current_effect = effect
            break
    
    # 章节切换动画
    for text, start_t, end_t, effect in TEXT_SEGMENTS:
        draw_transition(img, t, start_t)
    
    if current_text:
        char_progress = min(1.0, (t - current_start) * 5)
        visible_chars = int(len(current_text) * char_progress)
        display_text = current_text[:visible_chars]
        
        text_bbox = draw.textbbox((0, 0), display_text, font=FONT_TITLE)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        text_x = (WIDTH - text_w) // 2
        text_y = HEIGHT - 150
        
        # 发光效果
        glow_colors = [(255, 200, 100, x) for x in [60, 80, 100]]
        for i, gc in enumerate(glow_colors):
            draw.text((text_x - 2 + i, text_y), display_text, fill=gc, font=FONT_TITLE)
        draw.text((text_x, text_y), display_text, fill=(255, 255, 255), font=FONT_TITLE)
    
    # 10. 进度条
    progress = t / DURATION
    bar_y = HEIGHT - 25
    draw.rectangle([(100, bar_y), (WIDTH - 100, bar_y + 12)], fill=(40, 40, 40, 150), outline=(80, 80, 80, 100))
    draw.rectangle([(100, bar_y), (100 + int((WIDTH - 200) * progress), bar_y + 12)], 
                   fill=(0, 255, 200, 200))
    
    # 时间戳
    time_text = f"{int(t)}s / {DURATION}s"
    time_bbox = draw.textbbox((0, 0), time_text, font=FONT_BODY)
    draw.text((WIDTH - time_bbox[2] - 20, 20), time_text, fill=(255, 255, 255, 120), font=FONT_BODY)
    
    # CNN 效果
    result = np.array(img)
    effect_type = current_effect if current_text else 'edge'
    cnn_intensity = 0.1 + 0.15 * np.sin(t * 2) + peak * 0.2
    result = apply_cnn_effect(result, effect_type, min(0.5, cnn_intensity))
    
    return result

# ==================== 主程序 ====================
# ==================== 进度监控GUI ====================
class ProgressGUI:
    def __init__(self, total_frames: int):
        self.total_frames: int = total_frames
        self.root: 'tk.Tk | None' = None
        self.progress_var: 'tk.DoubleVar | None' = None
        self.info_label: 'tk.Label | None' = None
        self.status_label: 'tk.Label | None' = None
        self.time_label: 'tk.Label | None' = None
        self.title_label: 'tk.Label | None' = None
        self.start_time: 'np.datetime64 | None' = None
        self.cancelled: bool = False
        self.completed: bool = False
        self._queue: queue.Queue[tuple] = queue.Queue()
        
    def create_window(self):
        """在主线程创建窗口"""
        import tkinter as tk
        from tkinter import ttk
        
        self.root = tk.Tk()
        self.root.title("视频生成进度")
        self.root.geometry("500x200")
        self.root.resizable(False, False)
        
        # 居中窗口
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 200) // 2
        self.root.geometry(f"500x200+{x}+{y}")
        
        # 标题
        self.title_label = tk.Label(self.root, text="正在生成视频...", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=15)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, length=400, mode='determinate', 
                                           variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10)
        
        # 帧数+状态标签（更有用）
        self.info_label = tk.Label(self.root, text="0 / 480 帧", font=("Arial", 11))
        self.info_label.pack()
        
        # 状态标签
        self.status_label = tk.Label(self.root, text="准备中...", font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=5)
        
        # 时间标签
        self.time_label = tk.Label(self.root, text="预计剩余时间: 计算中...", font=("Arial", 9), fg="gray")
        self.time_label.pack()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        if self.root is None:
            return
        if self.completed:
            self.root.destroy()
        else:
            self.cancelled = True
            try:
                self.root.destroy()
            except:
                pass
    
    def start(self):
        self.start_time = np.datetime64('now')
        self._process_queue()
        self.root.mainloop()
    
    def _process_queue(self):
        """处理队列中的更新请求（必须在主线程调用）"""
        try:
            while True:
                msg = self._queue.get_nowait()
                if msg[0] == 'progress':
                    _, frame, total_frames, status = msg
                    self._do_update_progress(frame, total_frames, status)
                elif msg[0] == 'complete':
                    _, success, message = msg
                    self._do_complete(success, message)
        except queue.Empty:
            pass
        # 每 50ms 检查一次队列
        if self.root is not None:
            self.root.after(50, self._process_queue)
    
    def _do_update_progress(self, frame, total_frames, status):
        """实际执行进度更新"""
        if self.root is None:
            return
        if total_frames is None:
            total_frames = self.total_frames
        progress = (frame / total_frames) * 100
        try:
            self.progress_var.set(progress)
            self.info_label.config(text=f"{frame} / {total_frames} 帧 ({int(progress)}%)")
            if status:
                self.status_label.config(text=status)
            
            # 计算剩余时间
            if self.start_time is not None and frame > 0:
                elapsed = (np.datetime64('now') - self.start_time) / np.timedelta64(1, 's')
                eta = (elapsed / frame) * (total_frames - frame)
                if self.time_label is not None:
                    if eta > 60:
                        self.time_label.config(text=f"预计剩余时间: {int(eta/60)}分{int(eta%60)}秒")
                    else:
                        self.time_label.config(text=f"预计剩余时间: {int(eta)}秒")
            
            self.root.update()
        except:
            pass
    
    def _do_complete(self, success, message):
        """实际执行完成回调"""
        self.completed = True
        if self.root is None:
            return
        try:
            self.progress_var.set(100)
            if success:
                self.title_label.config(text="生成完成!", fg="green")
                self.info_label.config(text=f"{self.total_frames} / {self.total_frames} 帧")
                self.status_label.config(text=message, fg="green")
                if self.time_label is not None:
                    self.time_label.config(text="视频已保存")
            else:
                self.title_label.config(text="生成失败", fg="red")
                self.status_label.config(text=message, fg="red")
            
            self.root.after(3000, self.root.destroy)
        except Exception:
            pass
    
    def update_progress(self, frame, total_frames=None, status=""):
        """线程安全地发送进度更新（可从任何线程调用）"""
        self._queue.put(('progress', frame, total_frames, status))
        return not self.cancelled
    
    def complete(self, success=True, message="完成!"):
        """线程安全地发送完成通知（可从任何线程调用）"""
        self._queue.put(('complete', success, message))

# ==================== 带进度的视频写入 ====================
class ProgressCallback:
    def __init__(self, gui, total_frames):
        self.gui = gui
        self.total_frames = total_frames
        self.last_update = -1
        
    def __call__(self, frame=None, total=None):
        if frame is not None:
            if total is not None:
                self.total_frames = total
            # 每5%更新一次
            progress_pct = (frame / self.total_frames) * 100
            if progress_pct - self.last_update >= 5 or frame == self.total_frames - 1:
                self.last_update = progress_pct
                status = f"正在渲染第 {frame}/{self.total_frames} 帧"
                if not self.gui.update_progress(frame, self.total_frames, status):
                    raise Exception("用户取消")
        return True

# ==================== 主程序 ====================
print(f"正在生成视频（时长: {DURATION}秒）...")

# 创建GUI（在主线程）
gui = ProgressGUI(TOTAL_FRAMES)
gui.create_window()

gui.update_progress(0, TOTAL_FRAMES, "正在生成视频...")

def generate_video():
    """在子线程中生成视频"""
    try:
        clip = VideoClip(make_frame, duration=DURATION)
        gui.update_progress(0, TOTAL_FRAMES, "正在生成音频...")

        print("正在生成音频...")
        audio_data, sample_rate = make_audio_clip()
        gui.update_progress(0, TOTAL_FRAMES, "正在保存音频...")

        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav.close()

        with wave.open(temp_wav.name, 'w') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())

        script_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(script_dir, f"auto_generated_video_{timestamp}.mp4")
        gui.update_progress(0, TOTAL_FRAMES, "正在渲染视频（这可能需要几分钟）...")

        print("正在渲染视频...")

        # 手动渲染并监控进度
        gui.update_progress(0, TOTAL_FRAMES, "开始渲染...")
        
        writer = FFMPEG_VideoWriter(output_path, (WIDTH, HEIGHT), FPS, codec="libx264", audiofile=temp_wav.name)
        
        for i, t in enumerate(np.linspace(0, DURATION, TOTAL_FRAMES, endpoint=False)):
            frame = make_frame(t)
            writer.write_frame(frame)
            gui.update_progress(i + 1, TOTAL_FRAMES, f"渲染中: {int((i+1)/TOTAL_FRAMES*100)}%")
        
        writer.close()
        
        # writer 关闭后再删除临时文件，避免文件锁定冲突
        os.unlink(temp_wav.name)
        gui.complete(True, os.path.abspath(output_path))
        print(f"视频已生成：{os.path.abspath(output_path)}")
    except Exception as e:
        gui.complete(False, str(e))
        print(f"生成失败: {e}")

# 在子线程中运行视频生成（mainloop 必须在主线程）
video_thread = threading.Thread(target=generate_video, daemon=True)
video_thread.start()

# 主线程运行 GUI 主循环
gui.start()
