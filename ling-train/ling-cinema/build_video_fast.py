# -*- coding: utf-8 -*-
"""用单条 ffmpeg filter_complex（zoompan + fade + concat，无 xfade）快速生成 600s 画面轨。"""
import os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(BASE, "frames")
DURATIONS = [40, 55, 45, 50, 45, 50, 55, 50, 40, 50, 45, 45, 30]
FPS = 30
W, H = 1920, 1080
FADE = 0.8
OUT = os.path.join(BASE, "raw_video.mp4")

inputs = []
filters = []
for i, d in enumerate(DURATIONS):
    img = os.path.join(FRAMES, f"scene_{i+1:02d}.png")
    inputs += ["-loop", "1", "-i", img]
    n = int(round(d * FPS))
    zexpr = f"1+0.08*on/{n-1}" if n > 1 else "1"
    fade_out_start = d - FADE
    filt = (
        f"[{i}:v]zoompan=z='{zexpr}':d={n}:x=iw/2:y=ih/2:s={W}x{H}:fps={FPS},"
        f"fade=t=in:st=0:d={FADE},fade=t=out:st={fade_out_start}:d={FADE}[f{i}]"
    )
    filters.append(filt)

concat_in = "".join([f"[f{i}]" for i in range(len(DURATIONS))])
filters.append(f"{concat_in}concat=n={len(DURATIONS)}:v=1:a=0[out]")

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", ";".join(filters),
    "-map", "[out]",
    "-r", str(FPS),
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    OUT
]

print("Building video...")
print("\n".join(cmd[:3]) + " ...")
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print(res.stdout)
if res.returncode != 0:
    sys.exit(res.returncode)
print("Wrote", OUT)
