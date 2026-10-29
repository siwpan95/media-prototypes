---
name: shikonghuaban
description: Maintain shikonghuaban space-time canvas (本 SKILL.md 所在仓库根). pygame audio-visual engine with black hole/Penrose theme.
agent_created: true
---

# 时空画板（shikonghuaban）维护

## 概述
全屏音频可视化引擎（黑洞/Penrose 主题）：pygame 渲染 + sounddevice 实时合成锯齿波音符；两线程经 SharedState 桥接；音频不可用自动降级纯视觉模式。品牌名统一"时空画板"。

## 结构
- main.py：入口（音频引擎 + 可视化引擎）
- audio_engine.py / visual_engine.py：双引擎线程
- state.SharedState：全局单例 + Lock
- particle/：粒子子包（内联副本，复制优于共享）

## 常用命令
- python -m shikonghuaban（源码运行）；pyinstaller fat.spec 打包

## 已知陷阱
- 声音需 PortAudio（缺则静音但不崩）
- 环境要求 Python 3.12+；全屏 1920×1080
