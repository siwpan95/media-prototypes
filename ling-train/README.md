# ling-train ——《火车进站》主题短视频自动化制作流水线（三代迭代）

围绕《火车进站》（电影史）主题的短视频自动化制作流水线。本仓库实际承载**三代迭代项目**（历史遗留，2026-08-28 收口入库）：

| 代 | 目录 | 说明 | 成片 |
|---|---|---|---|
| **v1 · ling-train** | 仓库根 + `render/` | 初代流水线：素材采集 → 脚本 → 配音 → 字幕 → 帧图 → 成片；报告 `phase1_collection_report.md` / `phase2_production_pack.json` | `火车进站_10分钟.mp4`（30MB） |
| **v2 · ling-cinema** | `ling-cinema/` | 电影史版演进：`audio_gen.py` / `build_video*.py` / `generate_cards.py` / `final_compose.py`；报告为演进版（同名文件，更大） | `ling-cinema/火车进站_电影史_10分钟.mp4`（45MB） |
| **v3 · ling-cinema-v2** | `ling-cinema/ling-cinema-v2/` | 真实影像版：`generate_base.py`（公共领域影像 + AI 图 → 底帧）+ `generate_audio.py`（edge-tts 配音 + 静音填充 → 音频/字幕）；场景表共享 v2 的 `phase2_production_pack.json` | `火车进站_电影史_真实影像版.mp4`（51.8MB）与配乐版（55.5MB） |

## 语言 / 类型

- 语言：Python 3（编排脚本）+ 媒体资产（mp4 / mp3 / wav / png / srt）
- 类型：离线视频制作流水线（依赖 ffmpeg / edge-tts 等外部工具）

## 运行方式与依赖

- 外部依赖：`ffmpeg`（合成）、v3 配音需 `edge-tts`（联网 TTS）、`PIL`；
- **原始素材与中间产物本地保留不入库**（`.gitignore`：`ai_images/`、`audio_wav/`、`frames/`、`seg_*/`、`public_domain/`、`raw_video.mp4`、`full_audio.mp3`、`release/` 等）——重跑流水线前需先补回本地资产。

```bash
# v1（渲染辅助脚本）
python render/gen_cards.py
# v2（电影史版合成，依赖 ling-cinema/ 内 raw_video/full_audio/full.srt）
python ling-cinema/final_compose.py
# v3（真实影像版，两阶段：底帧 → 配音/字幕，随后外部 ffmpeg 合成）
python ling-cinema/ling-cinema-v2/generate_base.py
python ling-cinema/ling-cinema-v2/generate_audio.py
```

## 平台登记（allin-platform）

- registry 条目 `ling-train` 的 launch 指向 **v3 入口** `python ling-cinema\ling-cinema-v2\generate_base.py`（启动 = 最新一代第一阶段）。

## 如何新增下一代

1. 仓库内新建 `ling-cinema/<新代目录>/`，脚本路径一律随仓库推导（`os.path.dirname(os.path.abspath(__file__))`，禁止写死绝对路径）；
2. 成片进仓（单文件 <100MB），中间产物与原始素材继续走 .gitignore；
3. 在本文「三代迭代」表追加一行谱系，按 Keep a Changelog 记一笔；
4. 如需平台「启动」指向新代，更新 `<PATH>` 的 launch；
5. commit + push（先 `git ls-remote` 核对默认分支）。

## 测试状态

- 语法检查：通过；运行：需 ffmpeg 与本地媒体资产，未实际运行。

## 发布面

- gitee [siwpan/ling-train](https://gitee.com/siwpan/ling-train)（master，公开 + MIT）；release `v1.0.0`（ling-train v1.0.0 便携源码 zip）。
