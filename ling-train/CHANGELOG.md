# Changelog

本项目所有值得注意的变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- 三代入库（历史遗留收口）：ling-cinema/（v2 电影史版）与 ling-cinema/ling-cinema-v2/（v3 真实影像版）整目录纳入版本控制，README 记三代谱系（ling-train → ling-cinema → ling-cinema-v2）。
- .gitignore：中间产物与原始素材（ai_images/audio_wav/frames/seg_*/public_domain/raw_video/full_audio 等）与历史发布包 release/ 本地保留不入库。

### Fixed

- v3 脚本路径修复：generate_base.py / generate_audio.py 原硬编码 WorkBuddy 旧目录，改为随仓库推导（__file__）。

## [1.0.0] - 2026-08-27

### Added

- 首个发行版：便携源码 zip（剔除 .venv/构建产物/输出物，依赖见 README）。
- 发布面：gitee [siwpan/ling-train](https://gitee.com/siwpan/ling-train) release `v1.0.0`（ling-train v1.0.0）。