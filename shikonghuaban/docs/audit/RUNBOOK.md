# RUNBOOK — 时空画板 (Space-Time Canvas) 运维 / 事故处置手册

面向值班工程师（on-call）的快速处置指南。每条均以 **症状 → 原因 → 处置** 组织，并标注对应代码位置，便于直接定位。

> 全局入口：`shikonghuaban/main.py`（从仓库根目录以 `python -m shikonghuaban` 运行）。运行时日志：`fat.log`（运行目录，由 `shikonghuaban/main.py:21` 的 `FileHandler` 写入）。
> 音频缺失时程序自动降级为纯视觉模式，不会崩溃（`shikonghuaban/main.py:47-54`）。

---

## 0. 总览：先做什么

1. 看画面还是听声音出问题？→ 分别走 §1 / §2。
2. 先看 `fat.log` 有无 `WARNING`/`ERROR`（格式：`时间 [LEVEL] logger: 消息`）。
3. 控制台启动时会打印控制帮助与「音频不可用」等提示，先截图/复制。
4. 改任何源码前确认从**仓库根目录**运行（`python -m shikonghuaban`；源码现已收进 `shikonghuaban/` 包）。

---

## 1. 黑屏 / 无画面

**症状**
- 全屏窗口纯黑，无任何黑洞/网格结构；或窗口一闪而过。
- 控制台无「可视化引擎初始化失败」报错（否则见 §6）。

**原因**
- `config.py:8` 固定 `WIDTH, HEIGHT = 1920, 1080`，`visual_engine.py:36` 以 `pygame.FULLSCREEN` 全屏。若显示器实际分辨率不等于 1920×1080，全屏可能黑屏或超出可视区域。
- 显卡/驱动对 1920×1080 全屏切换异常（偶发）。

**处置**
- **窗口化调试**（最快定位）：临时把 `visual_engine.py:36`
  ```python
  self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
  ```
  改为窗口化：
  ```python
  self.screen = pygame.display.set_mode((WIDTH, HEIGHT))          # 固定窗口
  # 或 self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
  ```
  重启 `python -m shikonghuaban`，确认是否出画面。出画面即说明是分辨率/全屏问题，而非渲染逻辑故障。
- **匹配分辨率**：把 `config.py:8` 的 `WIDTH/HEIGHT` 改为显示器真实分辨率，或降低分辨率后重试。
- 若窗口化也黑屏 → 转 §6（可视化引擎初始化失败 / `fat.log` 的 `ERROR`）。

---

## 2. 无声音

**症状**
- 全屏有画面但完全无声；或启动即打印「⚠ 音频不可用，已切换为纯视觉模式（无声音）。」

**原因**
- PortAudio 缺失或无声卡设备，`sounddevice` 在 `audio_engine.start()`（`audio_engine.py:77-85`）抛异常。
- `shikonghuaban/main.py:47-54` 捕获异常 → 记 `log.warning("音频引擎启动失败，进入纯视觉模式: %s")` 并继续纯视觉运行。这是**预期降级行为**，不是崩溃。

**处置**
- 检查 `fat.log` 是否含 `音频引擎启动失败，进入纯视觉模式` → 确认是音频降级。
- 确认 PortAudio 已安装：
  - Windows：`sounddevice` wheel 通常自带；若仍无声，重装 `pip install sounddevice` 或安装系统 PortAudio。
  - Linux：`apt install portaudio19-dev` 后重装 `sounddevice`。
  - macOS：`brew install portaudio`。
- 检查系统默认输出设备是否可用、未被静音。
- 声音恢复后重启 `python -m shikonghuaban`，控制台应打印「音频引擎已启动」（见 `shikonghuaban/audio_engine.py:86`）。
- 若 `fat.log` 有 `audio callback status: ...`（`audio_engine.py:59`）→ 提示 xrun/underrun，多为设备延迟问题，可忽略或调 `latency`/`blocksize`（`audio_engine.py:83`）。

---

## 3. 分辨率异常

**症状**
- 画面被拉伸、裁切，或全屏后只显示部分内容；HUD 位置错乱。

**原因**
- `config.py:8` 的 `WIDTH/HEIGHT` 与显示器物理分辨率不一致。所有几何（`CENTER`、`BL_*` 半径）和 HUD 定位（`visual_engine.py:196-212`）都基于此常量。

**处置**
- 修改 `config.py:8` 为显示器真实分辨率（如笔记本 1366×768、2K 2560×1440 等）。
- 重启验证；若仅临时调试，配合 §1 的窗口化模式更直观。
- 注意：`BL_*` 黑洞半径以像素计，改分辨率后视觉比例会变化，属预期。

---

## 4. ModuleNotFoundError

**症状**
- 启动报 `ModuleNotFoundError: No module named 'particle'` / `'particle_effects'` / `'penrose'` / `'config'` 等。

**原因**
- 未在**仓库根目录**运行：`shikonghuaban/` 为包，须以 `python -m shikonghuaban` 运行；直接 `python shikonghuaban/main.py` 或 IDE 以子目录为工作目录会因相对导入失败而报 `ModuleNotFoundError`。
- `shikonghuaban/particle/` 子包缺失或 `__init__.py` 丢失：`shikonghuaban/particle_effects.py` 与 `shikonghuaban/__init__.py` 通过 `sys.path.insert(0, <pkg>/particle)` 注入后 `from core.particle import ...`，依赖 `shikonghuaban/particle/` 存在。
- 打包产物未包含 `particle` / `particle_effects`（`fat.spec` 配置问题，见 §5）。

**处置**
- 确认当前目录是仓库根：`ls` 应能看到 `shikonghuaban/` 包（含 `__init__.py`、各应用模块与 `particle/` 子包）。否则 `cd` 到根目录再 `python -m shikonghuaban`。
- 确认 `shikonghuaban/particle/__init__.py` 存在（`ls shikonghuaban/particle/__init__.py`，当前为 0 字节占位文件，已足够使 `particle` 成为包）。缺失则补回空文件或从版本库恢复。
- 若运行 `fat.exe` 报此错 → 见 §5 重新构建。
- 勿用 `python shikonghuaban/main.py`（应 `python -m shikonghuaban`）；或 IDE 以子目录为工作目录启动。

---

## 5. 重新构建 exe

**场景**
- 改了源码要发版；或运行 `fat.exe` 报 §4 的 `ModuleNotFoundError`；或需更新打包。

**步骤**
```bash
cd <repo-root>
pyinstaller fat.spec
```
- `fat.spec` 入口为 `shikonghuaban/main.py`（已修正，不再指向历史 `fat.py`）。
- `fat.spec` `datas=[('shikonghuaban/particle','shikonghuaban/particle')]` 打包粒子资源；`hiddenimports = collect_submodules('shikonghuaban')` 保证全部模块与 `particle` 工具包被收集。
- 产物：`dist/fat/fat.exe`（`fat.spec:28` `name='fat'`，`console=False` 即窗口程序）。
- 验证：双击 `dist/fat/fat.exe`，确认出画面且（若 PortAudio 可用）有声；检查无 `ModuleNotFoundError`。

---

## 6. 可视化引擎初始化失败

**症状**
- 启动即打印「❌ 可视化引擎初始化失败，程序退出。」并退出；`fat.log` 有 `可视化引擎初始化失败`（异常回溯）。

**原因**
- `VisualEngine.__init__`（`visual_engine.py:31-83`）中 `pygame.init()` / `set_mode` / 字体加载等任一环节异常（常见于无显示环境、SDL 库缺失、字体不可用）。

**处置**
- 看 `fat.log` 中 `可视化引擎初始化失败` 后的完整 traceback，定位具体哪一行。
- 无显示环境（服务器/SSH）：本程序需图形界面，无法 headless 运行；请在带显示器的机器运行。
- SDL/pygame 安装问题：`pip install --upgrade pygame` 重装，确认系统有 SDL2。
- 字体问题：`visual_engine.py:64-66` 用 `pygame.font.Font(None, …)`（默认字体），一般无需外部字体文件；若被定制过则恢复默认。
- 修复后重新 §5 或 `python -m shikonghuaban` 验证。

---

## 7. 日志位置与看什么

**位置**
- 运行目录下的 `fat.log`（相对路径，由 `shikonghuaban/main.py:21` `logging.FileHandler("fat.log", encoding="utf-8")` 写入；同时 `StreamHandler` 也打到控制台）。
- 级别 `INFO`，格式：`%(asctime)s [%(levelname)s] %(name)s: %(message)s`。

**重点关注的行**
| 日志内容 | 含义 | 处置指向 |
|---|---|---|
| `音频引擎启动失败，进入纯视觉模式: <err>` | 音频降级，纯视觉运行 | §2 |
| `音频引擎已启动` | 音频正常 | — |
| `可视化引擎初始化失败` + traceback | 渲染初始化失败 | §6 |
| `audio callback status: <status>` | 音频 xrun/underrun 等 | §2（通常可忽略） |
| `未捕获异常` + traceback | 主线程未捕获异常 | 看 traceback 定位，必要时反馈开发 |
| `system closed` | 正常退出 | — |

**排查顺序建议**
1. 复现问题，取 `fat.log` 与控制台输出。
2. 先判音频降级（§2）还是渲染失败（§6）。
3. 黑屏先窗口化（§1），再核对分辨率（§3）。
4. 导入错误先查 CWD 与 `particle/`（§4）。

---

## 8. 常用命令速查

```bash
# 运行（务必从仓库根目录）
python -m shikonghuaban

# 窗口化调试：临时改 visual_engine.py:36 去掉 FULLSCREEN

# 重新构建
pyinstaller fat.spec
# 产物：dist/fat/fat.exe

# 查看日志
cat fat.log        # Linux/macOS
type fat.log       # Windows

# 依赖安装
pip install -r requirements.txt
```

> 所有代码位置以当前仓库为准；如与本文不符，以 `shikonghuaban/main.py` / `shikonghuaban/config.py` / `fat.spec` / `shikonghuaban/visual_engine.py` / `shikonghuaban/audio_engine.py` 实际内容为准。
