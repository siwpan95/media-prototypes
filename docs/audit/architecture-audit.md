# 时空画板（shikonghuaban）架构评估与架构债盘点
**评估人：** 系统架构师 Archi ｜ **对象：** G:\shikonghuaban（Python 物理可视化引擎）

> 本文为 **2026-07-27 架构基线审计**（评估人 Archi）。各项债务的最终处置、验证与遗留见同目录 `remediation-report.md`（审计债 #1–#12 ↔ 治理项 A–I 映射表）。

---

## 一、高层设计概述

### 1.1 当前架构（分层 / 组件 / 依赖方向）

项目整体呈「**入口 → 音频子系统 → 共享状态桥 → 物理核心 → 可视化/特效 → 编排器**」的结构。模块化版本（`main.py` + 各分文件）是当前真正被 `main.py` 引用的生产代码；`fat.py` / `fat_original.py` 为早期/中间的**单体分叉**，并未被 `main.py` 引用。

依赖方向（自上而下，叶子在底部）：

```
                         main.py
                        /       \
               audio_engine.py   visual_engine.py (编排/上帝对象)
                   |                |  \
                   |                |   +-- particle_effects.ParticleEffectsManager
                   |                |            |
              state.SharedState     |         particle/ (核心工具包)
                   |                |            core.particle, renderers.pygame_renderer
              config (叶子)         |
              (WIDTH/HEIGHT/        +-- blackhole_physics.py ── config
               BL_半径/NOTES)       +-- accretion_disk.py ── config + blackhole_physics
                                    +-- gravitational_lensing.py ── config + blackhole_physics
                                    +-- hawking_radiation.py ── config
                                    +-- spacetime_grid.py ── config
                                    +-- penrose.py ── config

  说明：config.py 为最底层叶子，被几乎所有模块直接 import；
        particle/ 作为独立可复用工具包，仅被 particle_effects.py 引入（core + pygame_renderer 子集）。
```

**关键事实（已用 grep/Read 校验）：**
- `main.py:8-9` 仅 `from audio_engine / visual_engine`；`fat.py`、`fat_original.py` 不在任何运行路径中（仅 `fat.spec` 引用一个旧路径 `C:\Users\13122\Desktop\allin\faty\fat.py`，属历史打包产物）。
- **无循环依赖**：可视化各模块均只向下依赖 `config` 与 `blackhole_physics`/`penrose`，没有任何模块反依赖 `visual_engine`。依赖方向是健康的。
- 物理计算（`blackhole_physics.py` 纯函数、`penrose.py`）与渲染（`*_disk/_lensing/_hawking/_grid`）**职责分离意图清晰**，是架构上的亮点。

### 1.2 组件职责一览
| 模块 | 职责 | 评价 |
|---|---|---|
| `config.py` | 全局常量（分辨率/黑洞几何/音频/音符） | 单例式硬编码，不可注入 |
| `state.py` | `SharedState` 全局单例 + `Lock`，桥接音频线程与渲染线程 | 全局可变状态，隐藏数据流 |
| `audio_engine.py` | `sounddevice` 回调线程里合成锯齿波音符，写入 RMS 音量 | 与真实音频设备/pygame 强耦合 |
| `blackhole_physics.py` | 史瓦西度规下的距离/势/时间膨胀/红移/轨道速度/多普勒/区域/阴影/温度 | 含一批**死代码**透镜函数 |
| `penrose.py` | Penrose 变换、`to_screen`、`PenroseParticle` 路径粒子 | 含未调用的紧致化函数 |
| `accretion_disk / gravitational_lensing / hawking_radiation / spacetime_grid` | 各渲染「效应」模块，含 `render/update` | 各自 new 全屏 Surface，性能堪忧 |
| `particle_effects.py` | `ParticleEffectsManager` 把 particle 工具包封装成 7 套命名特效 | `sys.path` 注入导入，脆弱 |
| `visual_engine.py` | `VisualEngine` 上帝对象：持有 pygame、实例化全部特效、跑 60fps 主循环、处理事件、硬编码分层 | 编排与业务纠缠，扩展需改核心 |
| `particle/`（工具包） | `core.particle`(ParticleSystem/Emitter/ForceField/Particle)、`renderers`、以及**未被使用的** `particle_numpy`/`pil_renderer`/`systems`/`components` | 能力远超应用实际使用 |

---

## 二、架构债清单

| 序号 | 严重度 | 维度 | 位置 | 问题描述 | 建议 |
|---|---|---|---|---|---|
| 1 | 🔴严重 | 重复/分叉 | `fat.py`(1-640)、`fat_original.py`(1-324) | 三套实现并存：`fat_original.py`（无粒子工具包的单体）、`fat.py`（内联复制了 config/state/audio/visual 并调用 particle 工具包的单体）、模块化分文件。`main.py` 只引用模块化分文件，前两者是**未引用的分叉单体**，且 `fat.py` 还把物理/音频逻辑又抄了一遍。源真相不唯一，改一处不会联动另一处。 | 明确以**模块化分文件为唯一生产真相**；将 `fat.py`/`fat_original.py` 移入 `archive/` 或删除；更新 `fat.spec` 入口指向 `main.py`。 |
| 2 | 🔴严重 | 性能/渲染 | `visual_engine.py:142-157`（`draw_structure` 奇点曲线循环） | 循环内为每段曲线 `pygame.Surface((WIDTH,HEIGHT), SRCALPHA)` 各 new 一张 **1920×1080 全屏离屏 Surface** 再 blit（约 80 段/帧）；`draw_black_hole_core` 也创建多张全屏 Surface。每帧数百次全屏 Surface 分配，GC 与显存压力极大，直接威胁 60fps 实时性。 | 预创建单张离屏 Surface 作为类成员复用；曲线改用批量 `pygame.draw.lines`；绝不在热路径每帧分配全屏 Surface。 |
| 3 | 🟠高 | 可扩展性 | `visual_engine.py:264-306` | `run()` 中渲染分层顺序（星场→网格→粒子→吸积盘→核心→霍金→结构→路径粒子→HUD）**硬编码**；新增物理效应/渲染模式必须改 `VisualEngine`。无插件/策略注册表。 | 抽象 `Effect` 接口（`render(ctx, dt)` + enable 开关），用有序列表/注册表管理；`VisualEngine` 只负责调度，新增效果对核心零改动。 |
| 4 | 🟠高 | 重复/死代码 | `blackhole_physics.py:201,219,247,253,305` | `lens_deflection_angle / lens_displacement / is_visible_after_lensing / einstein_ring_radius / accretion_velocity_ratio` 均**未被任何模块引用**；而 `gravitational_lensing.py:63/101` 自带 `_lens_position/_secondary_image` 重新实现透镜逻辑（仅 import `dist_to_bh/angle_to_bh`）。两套引力透镜逻辑并存，易分歧。 | 收敛到 `blackhole_physics` 单一真源，让 `gravitational_lensing` 复用；删除 grep 确认无引用的函数。 |
| 5 | 🟠高 | 配置管理 | `config.py:8-43` | 全部为模块级常量（分辨率 1920×1080、黑洞几何、音频、音符序列），**硬编码且不可注入**；不支持窗口化/分辨率/物理参数调整，也难做单元测试（导入即绑定全局）。 | 引入 `Config` dataclass/字典 + 默认加载；通过构造参数注入；支持 JSON/YAML/环境变量覆盖；`config.py` 仅保留为默认值来源。 |
| 6 | 🟠高 | 性能 | `particle/core/particle.py`（生产路径）vs `particle/core/particle_numpy.py`(563行) | 生产用纯 Python `ParticleSystem`（逐粒子 update/loop），而 `particle_numpy.py`（SoA 向量化，文档称 30~100× 提速）**未被任何生产代码使用**。 | 评估以 `ParticleSystemNumpy` 替换热路径（需补齐拖尾/生命曲线/光照兼容，或先用于星尘/霍金等高频低复杂度系统）。 |
| 7 | 🟡中 | 耦合/可测试性 | `state.py:29` | 全局单例 `shared_state` + `threading.Lock` 被 `audio_engine`/`visual_engine` 直接 import 使用；跨线程可变全局状态，隐藏数据流，测试难替换/断言。 | 将 `SharedState` 作为依赖注入到构造；保留单例为默认装配，测试可传 mock。 |
| 8 | 🟡中 | 耦合/脆弱导入 | `particle_effects.py:21-24`、`fat.py:14-16` | 用 `sys.path.insert(0, particle_dir)` 注入路径后 `from core.particle import ...`；依赖脚本工作目录，部署/打包易碎。 | 将 `particle` 提升为正式包（顶层 import 或 pip 安装）；改用包内绝对/相对导入，移除 `sys.path` 操作。 |
| 9 | 🟡中 | 死代码/导入 | `penrose.py:39,44,81`；`accretion_disk.py:21` | `penrose_inverse / penrose_compactified / schwarzschild_to_screen` 仅定义从未调用；`accretion_disk.py:21` 导入 `doppler_color_shift` 却从未使用（仅用 `relativistic_doppler`）。 | 删除未调用函数与未使用导入（用 ruff/flake8 F401 自动检出）。 |
| 10 | 🟡中 | 可观测性/健壮性 | `main.py:13+`、`audio_engine.py:86/93` | 仅 `print`；`audio_engine` 未处理设备缺失/权限异常（`sounddevice` 抛错即崩）；无日志等级、无指标、无启动自检。 | 引入 `logging`；音频设备初始化 `try/except` 并降级；暴露 FPS/粒子数/音量等指标。 |
| 11 | 🟡中 | 测试债 | 全仓库 | 0 测试；纯函数物理模块（`blackhole_physics`/`penrose`）本易单测但无；可视化层因 `pygame` 全局初始化难测。 | 为 `blackhole_physics`、`penrose`、`config` 加单测；`VisualEngine` 用依赖注入 + headless 模式做冒烟测试。 |
| 12 | 🟢低 | 文档/品牌 | 各模块 docstring、`particle/docs/API.md` | 模块 docstring 自称「时空滑板」，与项目名「时空画板」不一致；`particle/docs/API.md` 标注「待创建」；`particle/README` 的 NumPy 优化章节仍是 TODO。 | 统一命名；补全 API 文档；清理 spec 注释。 |

---

## 三、关键决策记录（ADR 式建议）

### ADR-1：消除「双体单体」分叉，确立唯一生产真相
- **背景**：`fat.py` / `fat_original.py` 两套未引用单体与主模块分文件并存，且重复 config/state/audio/visual 逻辑（约 880 行重复）。`main.py` 实际只引用模块化分文件；`fat.spec` 仍指向历史路径 `C:\Users\13122\Desktop\allin\faty\fat.py`。
- **选项分析**：
  - A 保留 `fat.py` 作为打包入口并长期维护 → 维护成本翻倍，源真相持续分裂。
  - B 以模块化分文件为唯一真相，归档/删除 `fat*` → 维护成本最低，消除歧义。（推荐）
  - C 把 `fat.py` 的 particle 集成反向合回模块化 → 工作量大，收益有限。
- **决策**：采用 **B**。
- **后果**：需改 `fat.spec` 入口指向 `main.py`；短期核实无外部把 `fat.py` 当入口（仅 build 产物残留旧路径）；长期收益是「改一处即全量生效」，并消灭最严重的重复债。

### ADR-2：渲染性能治理（离屏 Surface 复用 + 粒子向量化）
- **背景**：每帧数百次全屏 Surface 分配（`visual_engine.py:142-157`）+ 纯 Python 粒子循环；1080p/60fps 压力下帧时间极易超标。
- **选项分析**：
  - A 仅做离屏 Surface 复用 → 低风险、高收益，几乎消除全屏分配。（必须）
  - B 同时迁移到 `ParticleSystemNumpy` → 高收益但需补齐 trails/生命曲线/光照兼容，风险中高。
  - C 维持现状 → 实时性质量属性不可靠。
- **决策**：**先 A 后 B**。A 作为必修项立即执行；B 列入后续性能冲刺，优先用于星尘/霍金等高频低复杂度系统做灰度。
- **后果**：A 几乎零风险显著降低 GC/显存抖动；B 解锁数量级吞吐但需兼容性工作。

### ADR-3：配置外部化与可注入
- **背景**：`config.py` 全局常量不可配、不可测（导入即绑定 1920×1080 与黑洞几何），导致分辨率/物理参数无法调整，且阻碍单测。
- **选项分析**：
  - A `Config` 对象 + 构造注入 + 文件/环境变量覆盖 → 解锁可配与可测。（推荐）
  - B 仅加 JSON 加载到现有常量 → 改动小但不解决可注入/可测。
  - C 维持 → 技术债持续。
- **决策**：采用 **A**，但为降低改动面，采取「`Config` dataclass 持有当前常量 + 工厂默认值 + 可选文件覆盖 + 通过构造注入」，并保留模块级常量作为向后兼容别名。
- **后果**：分辨率/物理参数可调、纯函数模块可单测；需改造各模块构造签名（因依赖已相对集中，改动面可控）。

---

## 四、整体架构健康度评级

**🟡 黄（中等 / 可用但存在显著债务）**

- **正向**：依赖方向健康、无循环依赖；物理计算与渲染职责分离意图清晰；`particle/` 工具包设计完整（形状/力场/拖尾/光照/LOD/事件系统齐全）。
- **负向（2 项 🔴）**：① 三套实现并存（`fat.py`/`fat_original.py` 分叉）造成源真相分裂与约 880 行重复；② `visual_engine.py` 每帧数百次全屏 Surface 分配，直接威胁「实时渲染」这一核心质量属性。
- **风险预警**：若不处理上述两项 🔴 债务（尤其渲染热路径），在更高分辨率/更复杂场景下会滑向 🔴。建议本季度以「删分叉 + 离屏复用」为 P0，配置外部化与粒子向量化列为 P1。

---
*附：已用 Read/grep 校验的关键事实——`main.py` 不引用 `fat*`；`blackhole_physics` 的 `lens_*`/`einstein_ring_radius`/`accretion_velocity_ratio` 无外部引用；`penrose` 的 `penrose_inverse/penrose_compactified/schwarzschild_to_screen` 仅定义未调用；生产仅用 `particle` 的 `core`+`pygame_renderer` 子集。*
