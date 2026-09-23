---
name: cellular-automaton-wallpaper
description: Maintain the cellular_automaton wallpaper (本 SKILL.md 所在仓库根). pygame+numpy CA with 142 rules and wallpaper mode.
agent_created: true
---

# cellular_automaton（CA 壁纸）维护

## 概述
2D 元胞自动机桌面壁纸：142 条规则（4 大类）、7 主题、11 图案、连续状态 CA、反应-扩散、辉光后处理、自动轮换壁纸。

## 常用命令
- python main.py --rule lenia --theme ocean --windowed
- python main.py --auto-cycle
- python wallpaper.py（壁纸模式）
- python run_tests.py（全量测试）

## 已知陷阱
- 依赖 pygame + numpy；壁纸模式会修改系统壁纸
- 与 pywallpaper 的 CA 能力重叠（引擎整合规划 S2 合并去重候选）
