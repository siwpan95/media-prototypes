import os, asyncio, json, subprocess, re

# 路径随仓库走（原硬编码 WorkBuddy 旧目录，2026-08-28 修复）；
# PK 引用 v2（ling-cinema）的生产包——v3 场景表与 v2 共享。
BASE = os.path.dirname(os.path.abspath(__file__))
PK = os.path.join(os.path.dirname(BASE), "phase2_production_pack.json")
VOICE = "zh-CN-XiaoxiaoNeural"
WAVDIR = os.path.join(BASE, "audio_wav")
os.makedirs(WAVDIR, exist_ok=True)

with open(PK, encoding="utf-8") as f:
    pack = json.load(f)
scenes = pack["scenes"]
starts = []
t = 0.0
for s in scenes:
    starts.append(t)
    t += s["duration_sec"]
TOTAL = t  # 600

def ffprobe_dur(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.decode().strip())

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def to_wav(mp3, wav):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", "24000",
         "-ac", "1", "-c:a", "pcm_s16le", wav])

def make_silence(wav, dur):
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "anullsrc=r=24000:cl=mono", "-t", f"{dur:.3f}",
         "-c:a", "pcm_s16le", wav])

def split_sentences(text):
    parts = re.split(r"([。！？；])", text)
    out, cur = [], ""
    for p in parts:
        if not p:
            continue
        cur += p
        if p in "。！？；":
            out.append(cur.strip())
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return [o for o in out if o]

async def main():
    wavs = []
    srt_entries = []  # (start, end, text)
    for i, s in enumerate(scenes):
        idx = s["index"]
        dur = s["duration_sec"]
        s_start = starts[i]
        s_end = s_start + dur
        mp3 = os.path.join(WAVDIR, f"tts{idx:02d}.mp3")
        wav = os.path.join(WAVDIR, f"tts{idx:02d}.wav")
        # TTS
        import edge_tts
        comm = edge_tts.Communicate(s["narration"], VOICE)
        await comm.save(mp3)
        to_wav(mp3, wav)
        d_i = ffprobe_dur(wav)
        # silence to fill scene window
        sil = max(0.0, dur - d_i)
        silwav = os.path.join(WAVDIR, f"sil{idx:02d}.wav")
        make_silence(silwav, sil)
        wavs.append(wav)
        wavs.append(silwav)
        # subtitles: split narration across scene window proportionally by char count
        sents = split_sentences(s["narration"])
        if not sents:
            sents = [s["narration"]]
        total_chars = sum(len(x) for x in sents) or 1
        pos = s_start
        for sent in sents:
            frac = len(sent) / total_chars
            seg_dur = max(1.0, (s_end - s_start) * frac)
            seg_end = min(s_end, pos + seg_dur)
            srt_entries.append((pos, seg_end, sent))
            pos = seg_end
    # concat all wavs
    listf = os.path.join(WAVDIR, "list.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for w in wavs:
            f.write(f"file '{w.replace(chr(92), '/')}'\n")
    fullwav = os.path.join(WAVDIR, "full.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", listf, "-c:a", "pcm_s16le", fullwav])
    fullmp3 = os.path.join(BASE, "full_audio.mp3")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", fullwav, "-b:a", "128k",
         "-ar", "44100", "-ac", "2", fullmp3])
    total_dur = ffprobe_dur(fullwav)
    # write SRT
    def fmt(sec):
        h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        if ms == 1000:
            ms = 0; s += 1
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    srt = os.path.join(BASE, "full.srt")
    with open(srt, "w", encoding="utf-8") as f:
        for n, (a, b, txt) in enumerate(srt_entries, 1):
            f.write(f"{n}\n{fmt(a)} --> {fmt(b)}\n{txt}\n\n")
    print(f"audio total={total_dur:.2f}s (scene sum={TOTAL}), srt cues={len(srt_entries)}")
    print("full_audio.mp3 + full.srt written")

asyncio.run(main())
