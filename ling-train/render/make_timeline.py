import json, os, re

base = os.environ.get("LING_TRAIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 仓根：环境变量 LING_TRAIN_ROOT 覆盖，否则由本脚本所在 render/ 上溯推导（去本地化，原硬编码绝对路径已失效）
pack = json.load(open(base + "\\phase2_production_pack.json", encoding="utf-8"))
render = base + "\\render"
audio_dir = render + "\\audio"
seg_dir = render + "\\segments"
sub_dir = render + "\\subtitles"
for d in [sub_dir]:
    os.makedirs(d, exist_ok=True)

scenes = pack["scenes"]
# scene planned durations (from production pack)
plan_dur = {s["index"]: s["duration_sec"] for s in scenes}
starts = {}
cum = 0
for s in scenes:
    idx = s["index"]
    starts[idx] = cum
    cum += plan_dur[idx]
TOTAL = cum
print(f"total planned duration: {TOTAL}s")

# ---- shift/concatenate SRTs ----
def srt_time_to_sec(ts):
    ts = ts.strip()
    m = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", ts)
    if not m:
        raise ValueError(f"bad srt time {ts}")
    h,mn,sc,ms = map(int, m.groups())
    return h*3600 + mn*60 + sc + ms/1000

def sec_to_srt_time(t):
    total_ms = max(0, int(round(t * 1000)))
    h = total_ms // 3600000
    m = (total_ms % 3600000) // 60000
    s = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

entries = []
for s in scenes:
    idx = s["index"]
    offset = starts[idx]
    srt_path = f"{audio_dir}\\scene_{idx:02d}.srt"
    raw = open(srt_path, encoding="utf-8-sig").read().strip()
    if not raw:
        continue
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    for b in blocks:
        lines = b.splitlines()
        if len(lines) < 2:
            continue
        timing = lines[1]
        text = "\n".join(lines[2:])
        start_str, end_str = timing.split(" --> ")
        start = srt_time_to_sec(start_str) + offset
        end = srt_time_to_sec(end_str) + offset
        entries.append((start, end, text))

entries.sort(key=lambda x: x[0])
out_srt = f"{sub_dir}\\full.srt"
with open(out_srt, "w", encoding="utf-8") as f:
    for i, (st, en, txt) in enumerate(entries, start=1):
        f.write(f"{i}\n{sec_to_srt_time(st)} --> {sec_to_srt_time(en)}\n{txt}\n\n")
print(f"wrote {out_srt} with {len(entries)} entries")

# ---- audio concat list ----
audio_concat = f"{audio_dir}\\concat.txt"
with open(audio_concat, "w", encoding="utf-8") as f:
    for idx in sorted(plan_dur.keys()):
        f.write(f"file 'scene_{idx:02d}_pad.m4a'\n")

# ---- build audio shell ----
audio_build = f"{audio_dir}\\build_audio.sh"
with open(audio_build, "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\nset -e\ncd \"$(dirname \"$0\")\"\n")
    for idx in sorted(plan_dur.keys()):
        d = plan_dur[idx]
        f.write(f"ffmpeg -y -i scene_{idx:02d}.mp3 -af \"apad=whole_dur={d}\" -c:a aac -ar 48000 -b:a 192k scene_{idx:02d}_pad.m4a\n")
    f.write(f"ffmpeg -y -f concat -safe 0 -i concat.txt -af \"apad=whole_dur={TOTAL}\" -c:a aac -ar 48000 -b:a 192k full_audio.m4a\n")

# ---- build video segments shell ----
seg_build = f"{seg_dir}\\build_segments.sh"
with open(seg_build, "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\nset -e\ncd \"$(dirname \"$0\")\"\n")
    for idx in sorted(plan_dur.keys()):
        d = plan_dur[idx]
        N = d * 30
        fade_in = "fade=t=in:st=0:d=1," if idx != 1 else ""
        fade_out = f"fade=t=out:st={d-1}:d=1"
        f.write(f"ffmpeg -y -loop 1 -i ../images/scene_{idx:02d}.png -t {d} -vf \"zoompan=z='1.0+0.10*(on/{N})':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,format=pix_fmts=yuv420p,{fade_in}{fade_out}\" -r 30 -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 23 -movflags +faststart scene_{idx:02d}.mp4\n")
    f.write("ffmpeg -y -f concat -safe 0 -i concat.txt -c copy raw_video.mp4\n")

# ---- video concat list ----
seg_concat = f"{seg_dir}\\concat.txt"
with open(seg_concat, "w", encoding="utf-8") as f:
    for idx in sorted(plan_dur.keys()):
        f.write(f"file 'scene_{idx:02d}.mp4'\n")

# ---- final mux shell ----
final_out = f"{base}\\火车进站_10分钟.mp4"
final_script = f"{render}\\build_final.sh"
with open(final_script, "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\nset -e\ncd \"$(dirname \"$0\")\"\n")
    f.write(f"ffmpeg -y -i segments/raw_video.mp4 -i audio/full_audio.m4a -vf \"subtitles=subtitles/full.srt:force_style='FontName=Microsoft YaHei,FontSize=40,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=3,Shadow=0,Alignment=2,MarginV=70,BorderStyle=1'\" -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 23 -c:a copy -shortest \"{final_out}\"\n")

print("scripts written:")
print(audio_build)
print(seg_build)
print(final_script)
print(f"final target: {final_out}")
