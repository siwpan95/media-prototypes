# CONTRIBUTING — 时空画板 (Space-Time Canvas)

参与开发前请先读 `README.md`（项目简介 / 运行 / 控制 / 配置）与 `RUNBOOK.md`（运维处置）。

## 仓库布局

```
shikonghuaban/                      # 仓库根目录（repo root）
├── README.md / RUNBOOK.md / CONTRIBUTING.md
├── pyproject.toml / requirements.txt / fat.spec
├── shikonghuaban/                  # 应用源码包（import 入口）
│   ├── __init__.py                 # 包标记 + 版本号（已去除 sys.path 注入）
│   ├── __main__.py                 # `python -m shikonghuaban` 入口
│   ├── main.py                     # 入口：日志、音频启动（含降级）、可视化主循环调度
│   ├── config.py                   # 全局常量（分辨率/黑洞几何/音频/音符序列）—— 最底层叶子
│   ├── state.py                    # SharedState 全局单例 + Lock，桥接音频线程与渲染线程
│   ├── audio_engine.py             # sounddevice 锯齿波合成器（独立回调线程）
│   ├── visual_engine.py           # VisualEngine 编排器：实例化全部特效、60fps 主循环
│   ├── blackhole_physics.py        # 黑洞物理纯函数（距离/势/红移/区域/阴影/温度）
│   ├── penrose.py                  # Penrose 变换、to_screen、PenroseParticle 路径粒子
│   ├── accretion_disk.py           # 吸积盘渲染
│   ├── gravitational_lensing.py    # 引力透镜 / 背景星场渲染
│   ├── hawking_radiation.py        # 霍金辐射粒子渲染
│   ├── spacetime_grid.py           # 弯曲时空网格渲染
│   ├── particle_effects.py         # ParticleEffectsManager：封装 particle/ 为 7 套命名特效
│   └── particle/                   # 粒子工具包（独立可复用子包）
│       ├── __init__.py             # 包标记（当前为空占位文件）
│       ├── core/                   # ParticleSystem / Emitter / ForceField / Particle 等
│       ├── renderers/              # pygame_renderer 等
│       └── ...                     # docs/ examples/ systems/ components/
├── archive/                        # 已退役的单体分叉：fat.py、fat_original.py（不再被运行路径引用）
├── docs/
│   └── audit/
│       ├── architecture-audit.md        # 架构债盘点（基线，来源）
│       └── remediation-report.md        # 治理报告：执行结果 + 验证 + 遗留
└── tests/                          # pytest 单元测试

```

> **单一生产真相**：`shikonghuaban/` 包内的 `main.py` + 上述分文件是现行生产代码。`archive/fat.py`、`archive/fat_original.py` 为早期/中间单体分叉，已被明确退役，请勿在其上修改（详见 `docs/audit/` 第 1、12 项）。

## 如何新增一个渲染模块

当前渲染由各「效应」模块（`accretion_disk` / `gravitational_lensing` / `hawking_radiation` / `spacetime_grid`）和 `particle_effects` 组成，`VisualEngine` 在 `visual_engine.py:46-72` 实例化、在 `run()`（`visual_engine.py:264-317`）按硬编码顺序分层绘制。

新增步骤：

1. **新建模块**（如 `my_effect.py`），接收 `screen` 与运行参数，提供 `render(self, screen, volume, elapsed_ms)`（或 `update_and_render(...)`）接口。物理计算尽量放纯函数，与渲染分离（参考 `blackhole_physics.py`）。
2. **在 `visual_engine.py` 中接入**：
   - 在 `__init__`（`visual_engine.py:46-72`）实例化并持有引用；
   - 在 `run()` 的分层区（`visual_engine.py:264-317`）按其层级调用 `render(...)`。
   - 若需可开关，仿照 `self.show_grid / show_lensing / show_hawking`（`visual_engine.py:59-61`）增加开关，并在 `K_SPACE` 循环（`visual_engine.py:235-256`）与 HUD（`visual_engine.py:202-212`）中登记。
3. **避免热路径每帧分配全屏 Surface**：复用类成员离屏 `Surface`（参考 `visual_engine.py:69-72` 的 `_core_scratch` 等预创建缓存）。这是 P0 已落地的性能修复，新增代码须遵守。
4. **如需新粒子**：优先通过 `particle_effects.ParticleEffectsManager` 复用 `particle/` 工具包；若需底层能力，使用 `particle/core`。
5. **打包**：若新模块引入新子包，更新 `fat.spec` 的 `datas` / `hiddenimports`（`fat.spec:5,11`），并本地 `pyinstaller fat.spec` 验证。

> 已知架构债：渲染分层硬编码、`VisualEngine` 偏「上帝对象」、`config` 不可注入（见 `docs/audit/` 第 3、5 项）。长期方向是抽象 `Effect` 接口 + 注册表，使新增效果对核心零改动——欢迎按此方向重构。

## 测试约定

- 框架：**pytest**，用例置于仓库根 `tests/`（与源码同级）。
- 依赖：物理纯函数模块（`blackhole_physics.py`、`penrose.py`、`config.py`）应优先补单测。
- **可视化 / pygame 代码需 headless**：测试前设置 SDL 哑驱动环境变量，避免在无显示环境初始化失败：
  ```bash
  export SDL_VIDEODRIVER=dummy
  export SDL_AUDIODRIVER=dummy
  pytest tests/
  ```
  （Windows PowerShell：`$env:SDL_VIDEODRIVER="dummy"; $env:SDL_AUDIODRIVER="dummy"; pytest tests/`）
- `VisualEngine` 等重 GUI 对象建议用依赖注入 + headless 冒烟测试，避免直接 `pygame.init()` 全量初始化。
- 提交前确保全量 `python -m py_compile` 通过（P0 已验证）。
- 运行测试请从仓库根目录执行（`shikonghuaban/` 包与 bundled `particle` 路径由 `tests/conftest.py` 自动接入）。

## 当前状态与债追踪

- **P0 修复已全部落地**（见 `docs/audit/` 与团队任务看板）：统一代码真源（归档 `fat*`、修正 `fat.spec` 入口）、渲染去每帧全屏分配（离屏复用）、音频相位连续化修爆音、启动兜底 + 日志 + 资源清理、补充单元测试。
- **P1 / P2  backlog** 在架构审计报告 `docs/audit/architecture-audit.md` 中持续追踪（配置外部化与可注入、粒子向量化、死代码清理、消除双体单体残余、文档/品牌统一等）；其中已治理项见 `docs/audit/remediation-report.md`。
- 改动涉及 P0 已修复区域时，请同步回归对应测试与 `RUNBOOK.md`；新发现的架构债请补充到审计报告的债清单。

## 提交与沟通

- 不改 `archive/` 下退役文件；不新建与 `shikonghuaban/main.py` 并行的单体入口。
- 涉及文档（README / RUNBOOK / 本文件）与实际代码行为不一致时，以**代码为准**并同步更新文档。
- 重大重构（如引入 `Effect` 注册表、配置对象化）建议先读 `docs/audit/` 对应 ADR 并与维护者对齐。
