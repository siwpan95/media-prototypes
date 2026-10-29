"""
生成恶搞版（joke mode）音效 — 程序化生成，不依赖外网下载
用 numpy 生成各种莫名其妙的音效替换风扇声音
"""
import numpy as np
import os
import struct
import wave

OUT_DIR = "D:/allin/lap/project1/assets/sfx_joke"
SR = 22050  # 采样率（较低以减小文件）

os.makedirs(f"{OUT_DIR}/fan", exist_ok=True)
os.makedirs(f"{OUT_DIR}/transient", exist_ok=True)
os.makedirs(f"{OUT_DIR}/fault", exist_ok=True)
os.makedirs(f"{OUT_DIR}/env", exist_ok=True)


def save_wav(path, samples):
    samples = np.clip(samples, -32768, 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(samples.tobytes())


def gen_purr(duration=3.0):
    """猫打呼噜声 — 替代 idle"""
    t = np.linspace(0, duration, int(SR * duration))
    # 25Hz 低频 + 振幅调制
    sig = (np.sin(2 * np.pi * 25 * t) *
           (1 + 0.5 * np.sin(2 * np.pi * 5 * t)))
    return (sig * 16000).astype(np.float64)


def gen_buzz(duration=3.0):
    """蜜蜂嗡嗡 — 替代 low"""
    t = np.linspace(0, duration, int(SR * duration))
    sig = np.sin(2 * np.pi * 200 * t) * (1 + 0.3 * np.sin(2 * np.pi * 30 * t))
    return sig * 12000


def gen_siren(duration=3.0):
    """警笛声 — 替代 medium"""
    t = np.linspace(0, duration, int(SR * duration))
    freq = 600 + 400 * np.sin(2 * np.pi * 2 * t)  # 频率在 200~1000 之间摆动
    sig = np.sin(2 * np.pi * freq * t)
    return sig * 10000


def gen_jet_fart(duration=3.0):
    """喷气+放屁声 — 替代 high"""
    t = np.linspace(0, duration, int(SR * duration))
    # 白噪声 + 低通滤波效果（用滑动平均模拟）
    noise = np.random.uniform(-1, 1, len(t))
    # 频率下降（像放屁）
    freq_env = np.exp(-3 * t)
    sig = noise * freq_env
    # 加个低频震动
    sig += 0.5 * np.sin(2 * np.pi * 80 * t) * freq_env
    return sig * 18000


def gen_rising_beep(duration=1.5):
    """上升哔声 — 启动音"""
    t = np.linspace(0, duration, int(SR * duration))
    freq = 200 + 600 * (t / duration)  # 200Hz -> 800Hz
    sig = np.sin(2 * np.pi * freq * t)
    return sig * 14000


def gen_falling_trombone(duration=1.5):
    """下降滑音（悲调）— 关闭音"""
    t = np.linspace(0, duration, int(SR * duration))
    freq = 800 * np.exp(-2.5 * t / duration)  # 指数下降
    sig = np.sin(2 * np.pi * freq * t)
    return sig * 14000


def gen_click(duration=0.1):
    """咔哒 — 用短噪声代替"""
    t = np.linspace(0, duration, int(SR * duration))
    sig = np.random.uniform(-1, 1, len(t)) * np.exp(-30 * t)
    return sig * 20000


def gen_wobble_ding(duration=1.0):
    """金属叮当 — 叶片故障"""
    t = np.linspace(0, duration, int(SR * duration))
    sig = np.sin(2 * np.pi * 1200 * t) * np.exp(-8 * t)
    sig += 0.5 * np.sin(2 * np.pi * 2400 * t) * np.exp(-10 * t)
    return sig * 18000


def gen_scrape_squeak(duration=1.2):
    """黑板刮擦声 — 轴承故障"""
    t = np.linspace(0, duration, int(SR * duration))
    # 高频正弦 + 随机频率调制 = 刺耳
    freq = 3000 + 1500 * np.sin(2 * np.pi * 20 * t)
    sig = np.sin(2 * np.pi * freq * t)
    sig *= (1 + 0.5 * np.sin(2 * np.pi * 7 * t))  # 振幅调制增加刺耳感
    return sig * 12000


def gen_motor_boom(duration=1.5):
    """低沉爆炸声 — 电机过载"""
    t = np.linspace(0, duration, int(SR * duration))
    sig = np.sin(2 * np.pi * 60 * t) * np.exp(-4 * t)
    sig += np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-6 * t)
    return sig * 24000


def gen_wind_howl(duration=3.0):
    """狼嚎/风声 — 环境音"""
    t = np.linspace(0, duration, int(SR * duration))
    # 两个频率接近的正弦 = 拍频效果（像风声）
    sig = (np.sin(2 * np.pi * 180 * t) +
           np.sin(2 * np.pi * 185 * t))
    sig *= (1 + 0.4 * np.sin(2 * np.pi * 0.8 * t))
    return sig * 8000


# ── 生成全部 ──────────────────────────────────────────────
sounds = {
    "fan/idle_1.wav":       gen_purr(3.0),
    "fan/low_2.wav":        gen_buzz(3.0),
    "fan/medium_3.wav":     gen_siren(3.0),
    "fan/high_4.wav":       gen_jet_fart(3.0),
    "transient/startup.wav":   gen_rising_beep(1.5),
    "transient/shutdown.wav":  gen_falling_trombone(1.5),
    "transient/click_on.wav":  gen_click(0.1),
    "transient/click_off.wav": gen_click(0.1),
    "fault/wobble.wav":        gen_wobble_ding(1.0),
    "fault/scrape.wav":        gen_scrape_squeak(1.2),
    "fault/bearing_fail.wav":  gen_motor_boom(1.5),
    "env/room_tone.wav":       np.zeros(int(SR * 2), dtype=np.float64),  # 静音
    "env/wind_noise.wav":      gen_wind_howl(3.0),
}

for rel_path, samples in sounds.items():
    full = os.path.join(OUT_DIR, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    save_wav(full, samples)
    print(f"  ✓ {rel_path}  ({int(os.path.getsize(full)//1024)}KB)")

print(f"\n全部完成！共 {len(sounds)} 个恶搞音效 → {OUT_DIR}")
