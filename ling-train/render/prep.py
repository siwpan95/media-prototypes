import json, os

base = os.environ.get("LING_TRAIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 仓根：环境变量 LING_TRAIN_ROOT 覆盖，否则由本脚本所在 render/ 上溯推导（去本地化，原硬编码绝对路径已失效）
pack = json.load(open(os.path.join(base, "phase2_production_pack.json"), encoding="utf-8"))

audio_dir = os.path.join(base, "render", "audio")
os.makedirs(audio_dir, exist_ok=True)

# Scene time windows (cumulative starts) per the production pack
starts = [0, 30, 70, 140, 195, 250, 310, 360, 410, 465, 515, 560]
full = []
for i, s in enumerate(pack["scenes"]):
    idx = i + 1
    txt = s["narration"].strip()
    full.append(txt)
    with open(os.path.join(audio_dir, f"scene_{idx:02d}.txt"), "w", encoding="utf-8") as f:
        f.write(txt)

# full narration text (single file)
with open(os.path.join(audio_dir, "full.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(full))

print("scenes:", len(pack["scenes"]))
print("total chars:", sum(len(s["narration"]) for s in pack["scenes"]))
print("starts:", starts)
print("duration sum:", sum(s["duration_sec"] for s in pack["scenes"]))
