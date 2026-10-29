# -*- coding: utf-8 -*-
"""生成并分镜对齐的配音 MP3 与 SRT（单脚本自动化）。"""
import os, json, re, subprocess, sys, asyncio

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "audio")
os.makedirs(OUT_DIR, exist_ok=True)

VOICE = "zh-CN-XiaoxiaoNeural"
PYTHON = "C:/Users/13122/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
DURATIONS = [40, 55, 45, 50, 45, 50, 55, 50, 40, 50, 45, 45, 30]
SCENE_START = [0]
for d in DURATIONS[:-1]:
    SCENE_START.append(SCENE_START[-1] + d)

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def to_srt_time(t):
    """秒 -> SRT HH:MM:SS,mmm"""
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    ms = int(round((s % 1) * 1000)); s = int(s)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return None

def run_ffmpeg(args):
    cmd = ["ffmpeg", "-y"] + args
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

async def gen_scene(idx, text, target_dur):
    media = os.path.join(OUT_DIR, f"scene_{idx+1:02d}.mp3")
    sub = os.path.join(OUT_DIR, f"scene_{idx+1:02d}.srt")
    print(f"[scene {idx+1}] TTS generating ...")
    cmd = [
        PYTHON, "-m", "edge_tts",
        "--voice", VOICE,
        "--write-media", media,
        "--write-subtitles", sub,
        "--text", text
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        print(out.decode("utf-8", errors="ignore"))
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    dur = get_duration(media)
    print(f"[scene {idx+1}] speech {dur:.2f}s / target {target_dur:.1f}s")
    return media, sub, dur

def pad_scene(idx, media, speech_dur, target_dur):
    final = os.path.join(OUT_DIR, f"scene_{idx+1:02d}_final.mp3")
    # 用 apad 把音频补足到目标分镜时长，精确裁剪
    run_ffmpeg([
        "-i", media,
        "-af", f"apad=pad_dur={target_dur}",
        "-t", str(target_dur),
        "-acodec", "libmp3lame", "-b:a", "128k", final
    ])
    return final

def parse_srt(path):
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    # 兼容多种换行
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", txt.strip())
    cues = []
    for b in blocks:
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        # 时间行含 " --> "
        time_line = None
        for l in lines:
            if " --> " in l:
                time_line = l; break
        if not time_line:
            continue
        start_s, end_s = time_line.split(" --> ")
        text = " ".join([l for l in lines if l != time_line and not l.isdigit()])
        cues.append((start_s, end_s, text))
    return cues

def srt_to_sec(t):
    t = t.replace(",", ".")
    parts = t.split(":")
    if len(parts) == 3:
        h, m, s = parts; return int(h)*3600 + int(m)*60 + float(s)
    return 0.0

def shift_srt(src, offset, out_path, start_cue):
    cues = parse_srt(src)
    with open(out_path, "a", encoding="utf-8") as f:
        for i, (s, e, text) in enumerate(cues, start=start_cue):
            ns = srt_to_sec(s) + offset
            ne = srt_to_sec(e) + offset
            f.write(f"{i}\n{to_srt_time(ns)} --> {to_srt_time(ne)}\n{text}\n\n")
        return start_cue + len(cues)

async def main():
    pack = read_json(os.path.join(BASE, "phase2_production_pack.json"))
    narrations = [s["narration"] for s in pack["scenes"]]
    # 生成所有配音（顺序）
    results = []
    for i, txt in enumerate(narrations):
        r = await gen_scene(i, txt, DURATIONS[i])
        results.append(r)
    # 逐镜 pad
    final_audios = []
    for i, (media, sub, dur) in enumerate(results):
        fa = pad_scene(i, media, dur, DURATIONS[i])
        final_audios.append(fa)
    # 合并音频（concat demuxer）
    list_path = os.path.join(OUT_DIR, "concat.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for p in final_audios:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    full_audio = os.path.join(BASE, "full_audio.mp3")
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_path, "-acodec", "libmp3lame", "-b:a", "128k", full_audio])
    # 合并 SRT 并加偏移
    full_srt = os.path.join(BASE, "full.srt")
    if os.path.exists(full_srt): os.remove(full_srt)
    cue_idx = 1
    for i, (_, sub, _) in enumerate(results):
        cue_idx = shift_srt(sub, SCENE_START[i], full_srt, cue_idx)
    print("Wrote", full_audio)
    print("Wrote", full_srt)
    print("Total audio duration:", get_duration(full_audio))

if __name__ == "__main__":
    asyncio.run(main())
