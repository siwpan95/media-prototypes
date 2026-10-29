# -*- coding: utf-8 -*-
"""逐镜生成 zoompan + fade 短片，再 concat copy 合成完整画面轨（低内存、高可靠）。"""
import os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(BASE, "frames")
TMP = os.path.join(BASE, "video_clips")
os.makedirs(TMP, exist_ok=True)
DURATIONS = [40, 55, 45, 50, 45, 50, 55, 50, 40, 50, 45, 45, 30]
FPS = 30
W, H = 1920, 1080
FADE = 0.8
OUT = os.path.join(BASE, "raw_video.mp4")

def run(cmd, capture=True):
    print("$", cmd[0], cmd[1], "...")
    if capture:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode != 0:
            print(r.stdout)
            raise subprocess.CalledProcessError(r.returncode, cmd)
        return
    else:
        subprocess.run(cmd, check=True)

clip_paths = []
for i, d in enumerate(DURATIONS):
    img = os.path.join(FRAMES, f"scene_{i+1:02d}.png")
    clip = os.path.join(TMP, f"clip_{i+1:02d}.mp4")
    clip_paths.append(clip)
    n = int(round(d * FPS))
    zexpr = f"1+0.08*on/{n-1}" if n > 1 else "1"
    out_start = d - FADE
    vf = (
        f"zoompan=z='{zexpr}':d={n}:x=iw/2:y=ih/2:s={W}x{H}:fps={FPS},"
        f"fade=t=in:st=0:d={FADE},"
        f"fade=t=out:st={out_start}:d={FADE}"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", img, "-t", str(d),
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        clip
    ]
    run(cmd)
    print(f"  clip {i+1}/{len(DURATIONS)} -> {clip}")

# concat copy
list_path = os.path.join(TMP, "clips.txt")
with open(list_path, "w", encoding="utf-8") as f:
    for p in clip_paths:
        f.write(f"file '{p.replace(os.sep, '/')}'\n")

run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", list_path,
    "-c", "copy", "-movflags", "+faststart",
    OUT
], capture=False)
print("Wrote", OUT)
