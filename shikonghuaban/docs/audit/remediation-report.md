# 时空画板（shikonghuaban）治理报告（最终版）

- **治理日期**：2026-07-27 → 2026-07-28（跨会话收口）
- **治理人**：Senior Developer（高级开发工程师）
- **对象**：`G:\shikonghuaban`（Python 物理可视化引擎，pygame + sounddevice）
- **债务基线**：`docs/audit/architecture-audit.md`（架构师 Archi 出具，债 #1–#12，本报告的验收来源）

---

## 0. 文档导航与范围

- **本文**（治理报告）：治理项 A–I 的计划、执行结果、验证、遗留。
- **`architecture-audit.md`**（基线）：债务清单 #1–#12 的权威来源；本文 §2 将其逐条映射到治理项并标注状态。
- **评估方法**：交叉阅读 `README.md` / `RUNBOOK.md` / `CONTRIBUTING.md` 与架构审计；逐文件读取核心源码与各特效模块；全仓 `grep` 校验死代码引用；首步已完成根目录归档整理。

---

## 1. 概览与结论

**结论：项目从「可用但有债（🟡 黄）」进入「结构干净、可维护、可打包」状态。原 P0/P1 债已全部清零。**

- 最严重的两项 🔴 债（双体单体分叉、每帧全屏 Surface 分配）在 P0 阶段已落地。
- 首批治理 A/B/C/D 与深水区 E/F/G/H/I 全部完成并通过 headless 验证。
- 唯一未做项审计 #7（`SharedState` 依赖注入，P2）显式列为遗留，非遗漏。

---

## 2. 债务总账：审计债 #1–#12 ↔ 治理项 ↔ 状态

> 这是本报告的核心索引表——把架构审计的 1–12 编号与治理动作的 A–I 编号对齐，避免两份文档割裂。

| 审计 # | 严重度 | 债务（摘要） | 治理项 | 状态 |
|---|---|---|---|---|
| 1 | 🔴 | 双体单体分叉：`fat*` 未被引用、`fat.spec` 旧路径 | 归档 `fat*` 至 `archive/` + `fat.spec` 入口改 `main.py` | ✅ DONE（P0） |
| 2 | 🔴 | 每帧数百次全屏 Surface 分配 | `visual_engine.py` 离屏复用 + 批量 `draw.line` | ✅ DONE（P0） |
| 3 | 🟠 | 渲染分层硬编码、`VisualEngine` 上帝对象 | **F** `Effect` 注册表解耦 | ✅ DONE |
| 4 | 🟠 | 死代码：透镜函数 `lens_*` 等无引用 | **B** 删除死函数 | ✅ DONE |
| 5 | 🟠 | `config` 硬编码、不可注入 | **E** `Config` dataclass 对象化 | ✅ DONE |
| 6 | 🟠 | 生产粒子纯 Python 未向量化 | **G** numpy 合力向量化 | ✅ DONE |
| 7 | 🟡 | `SharedState` 全局单例耦合、难测 | （依赖注入改造） | ⏸ **遗留（P2，未做）** |
| 8 | 🟡 | 脆弱导入：`sys.path.insert` 注入 `particle` | **H** + **I** 正式包化去 hack | ✅ DONE |
| 9 | 🟡 | 死导入：`penrose` / `accretion_disk` | **C** 删除未调用函数与导入 | ✅ DONE |
| 10 | 🟡 | 可观测性 / 健壮性（日志、降级） | **A** `env(n)` 修复 + P0 日志/降级/清理 | 🟡 部分 DONE |
| 11 | 🟡 | 测试债（0 测试） | **I** headless 冒烟 + A/B/C/D 单测 | ✅ DONE（显著改善） |
| 12 | 🟢 | 文档 / 品牌不一致（时空滑板 vs 画板） | **D** 品牌统一 | ✅ DONE |

---

## 3. 治理明细

### 3.1 首批治理（P0 落地 + A / B / C / D）

P0（审计 #1/#2 及音频相位连续、日志/降级/清理）在评估前已确认落地，核验依据：

| 债项 | 要求 | 核验结果 |
|---|---|---|
| 统一真相 | `fat*` 归档、`fat.spec` 指向 `main.py` | ✅ `archive/` 含 `fat.py`/`fat_original.py`；`fat.spec` 入口 `['main.py']`，`datas=[('particle','particle')]`，`hiddenimports=collect_submodules('particle')+['particle_effects']` |
| 离屏复用 | 不在热路径每帧分配全屏 Surface | ✅ `visual_engine.py:68-83` 预建 `_core_scratch/_photon_scratch/_structure_glow/_curve_surf`；`draw_structure` 曲线循环改用批量 `draw.line` + 复用 `_curve_surf` |
| 音频相位连续 | 消除爆音 | ✅ `audio_engine.py:66-68` 连续累加 `self.phase` |
| 日志/降级/清理 | `main.py` 日志 + 音频降级 + 退出清理 | ✅ `main.py` 已含 `logging`/`excepthook`/资源清理 |
| 单元测试 | 补物理纯函数单测 | ✅ `tests/` 含 `conftest` + 3 个测试文件（`blackhole_physics` / `audio_engine` / `particle_core`） |

A/B/C/D 修复清单：

| 项 | 文件 | 改动 |
|---|---|---|
| A | `audio_engine.py` | `env(n)` 的 `att`/`rel` 下限取 `1`，杜绝 `n<5` 崩溃；生产 `blocksize=1024` 行为不变 |
| A | `tests/test_audio_engine.py` | `xfail` 用例改为正式断言 `test_env_tiny_n_does_not_crash`；移除已无用的 `import pytest` |
| B | `blackhole_physics.py` | 删除死函数 `lens_deflection_angle`/`lens_displacement`/`is_visible_after_lensing`/`einstein_ring_radius`/`accretion_velocity_ratio`/`doppler_color_shift`；移除不再使用的 `BL_LENS_STRENGTH` 导入 |
| C | `accretion_disk.py` | 移除未使用导入 `doppler_color_shift` |
| C | `penrose.py` | 删除未调用函数 `penrose_inverse`/`penrose_compactified`/`schwarzschild_to_screen`；移除不再使用的 `BL_SCHWARZSCHILD_R` 导入 |
| D | 12 个源文件 + `README.md` | 品牌名「时空滑板」统一为「时空画板」（含窗口标题、启动打印等可见字符串） |

> 注：`gravitational_lensing.py` 自带 `_lens_position`/`_secondary_image` 透镜实现（仅依赖 `dist_to_bh`/`angle_to_bh`），不受影响，行为与删除前一致。

### 3.2 深水区治理（E / F / G / H / I）

均通过 headless 验证（SDL dummy + sounddevice 桩，托管 venv python 3.13 + numpy/pygame/sounddevice/pytest）：

| 项 | 文件 | 改动 | 验证 |
|---|---|---|---|
| **E** 配置外部化 | `shikonghuaban/config.py` + `tests/test_config.py` | `Config` dataclass 单一真相 + `from_dict`/`from_toml`/`load_config`/`get_config` 单例；保留全部模块级常量向后兼容 | 6 测试通过 |
| **F** Effect 注册表解耦 | `shikonghuaban/particle_effects.py` + `tests/test_effects_registry.py` | 7 套硬编码特效改为 `Effect` dataclass 注册表（`self.effects` 列表即渲染层序），去 `sys.path` hack 改包内相对导入 | 4 测试通过 |
| **G** 粒子力场向量化 | `shikonghuaban/particle/core/particle.py` + `tests/test_vectorized_forces.py` | `ForceField.get_force_numpy` 对 gravity/wind/attraction/vortex/turbulence 真向量化；`ParticleSystem.update` 在粒子循环**外**批量算合力（`USE_NUMPY_FORCES` 默认开，标量 fallback 保留）；noise/magnet 走标量兜底 | 7 测试通过（逐力场 `atol=1e-9` 严格等价 + 系统级双路径一致） |
| **H** 脆弱导入 | `particle_effects.py` / `__init__.py` / 9 个外围文件 | 去除全部 `sys.path` 注入，改包内相对导入 | `py_compile` + 9 模块 import 冒烟全绿 |
| **I** 正式包化 | 全仓重组 + `pyproject.toml` + `fat.spec` + `conftest` | `particle` 收为 `shikonghuaban.particle` 正式子包，运行方式 `python -m shikonghuaban` | 全图导入 + 全量 pytest 通过 |

**G 项关键澄清**：`test_system_numpy_matches_scalar_fallback` 此前看似「浮点累积误差不收敛」，根因实为**测试缺陷**——两套系统各自 `create_turbulence()` 生成了**不同随机种子**的湍流场（`ForceField.__init__` 内 `_noise_time_offset = random.uniform(0,1000)`），并非实现差异。修复为两系统**共享同一组力场对象**（深拷贝），双路径在 double 精度下严格一致（`atol=1e-9`），证明向量化与标量力学完全等价。

**H 项收尾**：清除 `particle/` 下 9 个外围文件残留的 `sys.path.insert`（含 `make_fireworks_video.py` 的硬编码 `PARTICLE_ROOT="D:/allin/tools/particle"`）：
`components/effects.py`、`systems/{combat_effects,fireworks_system,weather_system}.py`、`examples/{demo_v3_all_features,demo_enhanced_features,fireworks,make_fireworks_video,test_fireworks_headless}.py`。全仓仅剩 `tests/conftest.py`（注入 REPO_ROOT 供测试发现包，属合理做法）与 `archive/fat.py`（已退役）。

**I 项源码收包重组**（用户要求重新整理）：新建 `shikonghuaban/` 标准包，将 12 个应用模块与 `particle/` 子包整体移入；模块间互导由顶层 `from config import` 改写为包内相对导入 `from .config import`；新增 `shikonghuaban/__main__.py` 作为 `python -m shikonghuaban` 入口；同步更新 `fat.spec`、`pyproject.toml`、`tests/conftest.py` 与根文档的运行说明。

---

## 4. 验证总览（headless）

验证在与项目隔离的托管 venv（`C:\Users\13122\.workbuddy\binaries\python\envs\default`，Python 3.13.14，安装 `numpy/pygame/sounddevice/pillow/pytest`）中进行，不影响项目目录。本机默认 Python 3.14 缺失 `sounddevice`，故沿用该 venv 以对齐历次结论。

| 检查 | 命令 | 结果 |
|---|---|---|
| 全量编译 | `python -m compileall -q .` | ✅ 全部通过 |
| 单元 + 冒烟测试 | `python -m pytest -q` | ✅ **32/32 通过**（config / effects_registry / vectorized_forces / audio_engine / particle_core / blackhole_physics） |
| 外围模块导入冒烟 | `import shikonghuaban.particle.{components,systems,examples}.*` | ✅ **9/9 通过**（`demo_v3_all_features` 自带 47 项内部特性自检全过） |

另：全仓 grep 校验——被删符号（`doppler_color_shift` / `lens_*` / `einstein_ring_radius` / `accretion_velocity_ratio` / `penrose_inverse` / `penrose_compactified` / `schwarzschild_to_screen`）在源码中**零悬空引用**（仅历史 `archive/` 与 `docs/` 中出现）。

---

## 5. 已知遗留与后续建议

| 项 | 来源 | 状态 | 说明 |
|---|---|---|---|
| `SharedState` 依赖注入 | 审计 #7 | ⏸ 遗留（P2） | 全局单例 + `Lock` 跨线程可变状态，测试难替换；建议改为构造注入，保留单例为默认装配 |
| 持续 lint | 审计 #10 | 💡 建议 | 引入 `ruff`/`flake8` 自动检出 F401 死导入，防止债复发 |
| 版本管理 | 审计 #10 | 💡 建议 | 当前目录无 `.git`，建议初始化仓库纳入版本控制 |
| `archive/fat.py` | 审计 #1 | 保留 | 已退役单体分叉，未被任何运行路径引用，留作历史参考 |

> 审计 #10（可观测性/健壮性）已部分落地：A 项修复 `env(n)` 崩溃 + P0 阶段补齐 `logging`/音频降级/退出清理。剩余为指标暴露与告警，非阻塞。
