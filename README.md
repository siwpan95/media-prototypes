# 时空画板 (Space-Time Canvas)

> 仓库：<https://gitee.com/siwpan/shikonghuaban> ｜ 许可：MIT（见 [LICENSE](LICENSE)）

全屏音频可视化引擎：以黑洞 / Penrose 几何为主题，用 `pygame` 渲染吸积盘、引力透镜、霍金辐射与 Penrose 结构路径粒子，并通过 `sounddevice` 实时合成锯齿波音符。

> 项目正式名称以 **时空画板 / shikonghuaban** 为准；各模块 docstring 已统一品牌命名为「时空画板」（见 `docs/audit/architecture-audit.md` 第 12 项；治理结论见 `docs/audit/remediation-report.md`）。

## 项目简介

- 入口 `main.py` 启动 **音频引擎**（`audio_engine.py`，独立线程回调合成）与 **可视化引擎**（`visual_engine.py`，60fps 主循环）。
- 两线程通过 `state.SharedState`（全局单例 + `Lock`）桥接，音频侧写入 RMS 音量，渲染侧读取并驱动画面强度。
- 黑色主题：黑洞视界阴影 + 光子球亮环 + 弯曲时空网格 + 吸积盘 + 霍金辐射 + Penrose 几何 + 路径粒子 + 增强粒子特效（基于 `particle/` 工具包）。
- **音频不可用时不崩溃**：`main.py` 捕获音频启动异常，自动降级为「纯视觉模式」。

## 环境要求

- **Python 3.12+**
- 依赖见 `requirements.txt`：`numpy>=1.24`、`pygame>=2.5`、`sounddevice>=0.4`、`pillow>=10.0`
- **声音必需 PortAudio**：`sounddevice` 依赖系统 PortAudio 库。Windows 上 `sounddevice` 自带 wheel 通常已包含；Linux/macOS 需自行安装（如 `apt install portaudio19-dev` / `brew install portaudio`）。缺 PortAudio → 无声但程序照常运行（纯视觉模式）。
- 显示器建议支持 **1920×1080** 全屏（见 `配置概览`）。

## 安装

```bash
cd <repo-root>
python -m venv .venv && source .venv/bin/activate   # 可选但推荐
pip install -r requirements.txt
```

> 源码已收为 `shikonghuaban/` 标准 Python 包。所有应用模块与 `particle/` 子包现位于 `shikonghuaban/` 内，从仓库根目录以 `python -m shikonghuaban` 运行即可（无需再把模块摊在根目录）。

## 运行

### 方式一：源码运行

```bash
cd <repo-root>
python -m shikonghuaban
```

### 方式二：构建并运行 fat.exe

```bash
pyinstaller fat.spec        # 入口 shikonghuaban/main.py；打包 shikonghuaban/particle 子包
dist/fat/fat.exe            # 产物位置
```

构建说明详见 `RUNBOOK.md`「重新构建 exe」一节。`fat.spec` 入口已指向 `shikonghuaban/main.py`，`collect_submodules('shikonghuaban')` 覆盖全部模块与 `particle` 工具包，`datas=[('shikonghuaban/particle','shikonghuaban/particle')]` 打包资源。

## 控制说明

程序启动时会打印控制帮助，实际按键如下（以 `shikonghuaban/main.py:42-44` 与 `shikonghuaban/visual_engine.py:227-256` 为准）：

| 按键 | 作用 |
|---|---|
| `ESC` | 退出程序 |
| `↑` / `↓` | 调节音量（驱动画面响应强度） |
| `SPACE` | 切换显示模式：在 网格 / 引力透镜 / 霍金辐射 各图层间循环开关 |

> `SPACE` 循环顺序：全开 → 关透镜 → 关网格 → 关霍金 → … → 复位全开。右下角 HUD 实时显示当前开启的图层（`[G]网格 [L]透镜 [H]霍金`）。

## 配置概览

核心常量集中在 `config.py`，按用途分组：

**显示**
| 常量 | 值 | 作用 |
|---|---|---|
| `WIDTH`, `HEIGHT` | `1920`, `1080` | 全屏分辨率（`visual_engine.py:36` 用作 `set_mode` 尺寸）。需与显示器匹配。 |
| `CENTER` | `(960, 540)` | 黑洞几何中心 |
| `BG` | `(0,0,0)` | 背景色（纯黑） |
| `HORIZON` / `SINGULARITY` / `COLOR` | RGB 三元组 | 视界结构线、奇点曲线、默认结构色 |

**黑洞物理（屏幕像素尺度，`config.py:15-27`）**
| 常量 | 默认值 | 作用 |
|---|---|---|
| `BL_SCHWARZSCHILD_R` | `180.0` | 史瓦西半径（事件视界），其余半径以此推导 |
| `BL_PHOTON_SPHERE_R` | `270.0` (1.5×rs) | 光子球半径 |
| `BL_ISCO_R` | `540.0` (3×rs) | 最内稳定圆轨道 |
| `BL_DISK_OUTER_R` | `1800.0` (10×rs) | 吸积盘外缘 |
| `BL_LENS_STRENGTH` | `2.0` | 引力透镜缩放强度 |
| `BL_DOPPLER_STRENGTH` | `0.6` | 多普勒束流强度 |

**音频（`config.py:29-43`）**
| 常量 | 值 | 作用 |
|---|---|---|
| `SR` | `44100` | 采样率 |
| `BPM` | `118` | 节拍速度 |
| `BEAT` | `60/118` | 单拍秒数（派生） |
| `VOL` | `0.12` | 输出音量上限（音频振幅系数） |
| `NOTES` | 9 音字典 | 音符名 → 频率（Hz） |
| `RIFF` / `VERSE` / `CHORUS` | 音符序列 | 预编播放段落（`state.py` 中按顺序编排） |

## 常见问题 FAQ

**Q: 没有声音？**
A: 先确认 PortAudio 已安装（`sounddevice` 依赖它）。若缺失，`shikonghuaban/main.py` 会捕获异常并进入纯视觉模式，控制台打印「⚠ 音频不可用，已切换为纯视觉模式（无声音）。」，同时 `fat.log` 记录 `音频引擎启动失败，进入纯视觉模式`。有声画面正常即说明降级成功，非程序故障。

**Q: 黑屏 / 无画面？**
A: 多为全屏分辨率与显示器不匹配（`config.py` 固定 1920×1080）。见 `RUNBOOK.md`「黑屏/无画面」按窗口化模式调试。注意程序隐藏鼠标、全屏黑底，启动后需稍候数秒出现黑洞结构。

**Q: `ModuleNotFoundError: No module named 'particle'` / `'particle_effects'` / `'penrose'`？**
A: 从仓库根目录运行 `python -m shikonghuaban`（`shikonghuaban/` 为包，含 `__init__.py`、各应用模块与 `particle/` 子包）。若运行打包后的 `fat.exe` 报此错，需 `pyinstaller fat.spec` 重新构建（见 RUNBOOK）。

**Q: 构建出来的 exe 运行报错？**
A: 用 `pyinstaller fat.spec` 重新构建，确保 `fat.spec` 入口为 `shikonghuaban/main.py`、`collect_submodules('shikonghuaban')` 覆盖全部模块、`datas` 含 `shikonghuaban/particle`。

**Q: 日志在哪？怎么看？**
A: 日志写入运行目录下的 `fat.log`（`main.py:21`，`FileHandler`）。排查时重点看 `WARNING`/`ERROR` 级与「音频引擎启动失败」「可视化引擎初始化失败」「未捕获异常」等字样。详见 `RUNBOOK.md`「日志位置」。

---

相关文档：`RUNBOOK.md`（事故处置）、`CONTRIBUTING.md`（贡献指南）、`docs/audit/architecture-audit.md`（架构债盘点）、`docs/audit/remediation-report.md`（治理报告与验证）。
