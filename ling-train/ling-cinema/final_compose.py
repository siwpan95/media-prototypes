# -*- coding: utf-8 -*-
"""最终合成：画面轨 + 配音 + 烧录硬字幕，并校验。"""
import os, subprocess, json, sys

BASE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(BASE, "raw_video.mp4")
AUDIO = os.path.join(BASE, "full_audio.mp3")
SRT = os.path.join(BASE, "full.srt")
OUT = os.path.join(BASE, "火车进站_电影史_10分钟.mp4")

STYLE = (
    "FontName=Microsoft YaHei,"
    "FontSize=40,"
    "PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00000000,"
    "Outline=2,"
    "Shadow=0,"
    "BorderStyle=1,"
    "Alignment=2,"
    "MarginV=60"
)

def run(cmd):
    print("$", " ".join(cmd[:5]), "...")
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(r.stdout)
    if r.returncode != 0:
        sys.exit(r.returncode)

# 最终合成（前台单跑）
cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO,
    "-i", AUDIO,
    "-vf", f"subtitles=full.srt:force_style='{STYLE}'",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "veryfast",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    "-shortest",
    OUT
]
run(cmd)
print("Synthesized:", OUT)

# 校验
print("\n--- ffprobe validation ---")
info = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=format_name,size,duration:stream=width,height",
     "-of", "json", OUT],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print(info.stdout)
if info.returncode != 0:
    print("ffprobe stderr:", info.stderr)
    sys.exit(1)
meta = json.loads(info.stdout)
fmt = meta.get("format", {})
streams = meta.get("streams", [])
file_size = fmt.get("size")
duration = fmt.get("duration")
format_name = fmt.get("format_name")
w = streams[0].get("width") if streams else None
h = streams[0].get("height") if streams else None

print(f"size={file_size} bytes  ({int(file_size)/1024/1024:.2f} MB)")
print(f"duration={duration} s")
print(f"format_name={format_name}")
print(f"resolution={w}x{h}")

errors = []
if file_size is None or int(file_size) < 1*1024*1024:
    errors.append("file size < 1MB")
if duration is None or not (570 <= float(duration) <= 640):
    errors.append("duration not in 570-640s")
if w != 1920 or h != 1080:
    errors.append("resolution not 1920x1080")
if format_name is None or "mp4" not in format_name:
    errors.append("format not mp4")

print("\n--- decode stress test ---")
dec = subprocess.run(["ffmpeg", "-v", "error", "-i", OUT, "-f", "null", "-"],
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
if dec.returncode != 0:
    errors.append("ffmpeg decode returned non-zero")
    print(dec.stdout)
else:
    print("decode OK")

if "moov atom not found" in dec.stdout or "moov atom not found" in info.stderr:
    errors.append("moov atom not found")

if errors:
    print("VALIDATION FAILED:", errors)
    sys.exit(1)
print("VALIDATION PASSED")
