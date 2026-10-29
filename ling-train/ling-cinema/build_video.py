# -*- coding: utf-8 -*-
"""用 ffmpeg 将 13 张卡拼成带 zoompan + xfade 的画面轨。"""
import os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(BASE, "frames")
DURATIONS = [40, 55, 45, 50, 45, 50, 55, 50, 40, 50, 45, 45, 30]
FPS = 30
W, H = 1920, 1080
OVERLAP = 0.8
OUT = os.path.join(BASE, "raw_video.mp4")

inputs = []
filters = []
for i, d in enumerate(DURATIONS):
    img = os.path.join(FRAMES, f"scene_{i+1:02d}.png")
    inputs += ["-loop", "1", "-i", img]
    n_frames = int(round(d * FPS))
    # zoompan: 1 -> 1.08, 中心居中
    zexpr = f"1+0.08*on/{n_frames-1}" if n_frames > 1 else "1"
    filters.append(f"[{i}:v]zoompan=z='{zexpr}':d={n_frames}:x=iw/2:y=ih/2:s={W}x{H}:fps={FPS}[f{i}]")

# xfade 链
acc = "f0"
for i in range(1, len(DURATIONS)):
    offset = sum(DURATIONS[:i]) - i * OVERLAP
    prev = f"v{i-1:02d}" if i > 1 else acc
    out = f"v{i:02d}"
    filters.append(f"[{prev}][f{i}]xfade=transition=fade:duration={OVERLAP}:offset={offset:.3f}[{out}]")
    acc = out

filter_complex = ";".join(filters)

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_complex,
    "-map", f"[{acc}]",
    "-r", str(FPS),
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    OUT
]

print("Command length:", len(cmd))
print("\n".join(cmd[:5]) + " ...\n")
print("filter_complex:\n", filter_complex[:500], "...")

res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print(res.stdout)
print(res.stderr if res.stderr else "")
if res.returncode != 0:
    sys.exit(res.returncode)
print("Wrote", OUT)
