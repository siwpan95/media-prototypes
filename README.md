# Cellular Automaton Wallpaper

一个功能丰富的 2D 元胞自动机桌面壁纸程序，基于 **pygame + numpy** 实现，包含 **142 条规则**（涵盖 4 大类）、7 种颜色主题、11 种预定义图案，支持连续状态 CA、反应-扩散系统、辉光后处理与自动轮换壁纸模式。

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Rules](https://img.shields.io/badge/rules-142-orange)
![Themes](https://img.shields.io/badge/themes-7-purple)

---

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 直接运行（默认：全屏，Game of Life，Neon主题）
python main.py

# 指定规则和主题
python main.py --rule lenia --theme ocean

# 窗口模式 + 指定分辨率和帧率
python main.py --windowed --cell-size 4 --fps 30

# 开启自动轮换（每60秒切换规则，每90秒切换主题）
python main.py --auto-cycle

# 运行壁纸模式（自动轮换规则与主题）
python wallpaper.py

# 运行全量测试
python run_tests.py
```

---

## 两种运行模式

### 标准模式 `main.py`

交互式全屏/窗口 CA 模拟器，手动切换规则和主题，或开启自动轮换。

```bash
python main.py --rule smooth_life --theme plasma
python main.py --auto-cycle --cycle-interval 45
```

| 按键 | 功能 |
|:---:|---|
| `ESC` | 退出 |
| `SPACE` | 暂停 / 继续 |
| `R` | 随机化网格 |
| `C` | 清空网格 |
| `G` | 切换网格线 |
| `TAB` | 下一条规则 |
| `T` | 下一个主题 |
| `A` | 开关自动轮换 |
| `M` | 开关音频 |

### 壁纸模式 `wallpaper.py`

无边框全屏桌面壁纸，自动轮换规则（每 60 秒）和主题（每 90 秒），精选视觉效果最好的规则。手动切换后暂停自动轮换 5 分钟。

```bash
python wallpaper.py
python wallpaper.py --rule bz_reaction --theme sunset
```

| 按键 | 功能 |
|:---:|---|
| `ESC` | 退出 |
| `SPACE` | 暂停 / 继续 |
| `H` | 切换 HUD 显示 |
| `S` | 保存截图到 `screenshots/` 目录 |
| `R` | 随机化网格 |
| `TAB` | 下一条规则（暂停自动轮换 5 分钟） |
| `T` | 下一个主题（暂停自动轮换 5 分钟） |
| `[` / `]` | 减小 / 增大单元格尺寸 |
| `-` / `+` | 减小 / 增大目标帧率 |
| `M` | 开关音频 |

---

## 鼠标控制

| 鼠标 | 功能 |
|:---:|---|
| **左键** | 绘制活细胞 / 循环多状态 |
| **右键** | 擦除细胞 |
| **拖拽** | 按住持续绘制 |

---

## CLI 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--cell-size` | int | `6` | 单元格像素大小 |
| `--density` | float | `0.25` | 初始细胞密度 |
| `--rule` | str | `game_of_life` | 规则名称 |
| `--theme` | str | `neon` | 颜色主题 |
| `--fps` | int | `60` | 目标帧率 |
| `--lang` | str | `en` | UI 语言（`en` / `zh`） |
| `--windowed` | flag | — | 窗口模式（默认全屏） |
| `--no-audio` | flag | — | 禁用音频 |
| `--audio-volume` | float | `0.12` | 音量 0.0–1.0 |
| `--no-smooth-scale` | flag | — | 禁用抗锯齿平滑缩放 |
| `--no-glow` | flag | — | 禁用辉光/bloom 后处理 |
| `--glow-intensity` | float | `0.35` | 辉光强度 0.0–1.0 |
| `--config` | str | — | JSON 配置文件路径 |
| `--auto-cycle` | flag | — | 开启规则/主题自动轮换 |
| `--cycle-interval` | float | `60` | 自动轮换间隔（秒） |

可通过 `config.json` 覆盖额外字段：`fade_speed`、`max_age`、`trail_enabled`、`trail_length`、`show_grid`、`fullscreen`、`window_width`、`window_height`、`smooth_scale`、`glow_enabled`、`glow_intensity`、`glow_blur_size`、`vsync`、`auto_cycle_rules`、`auto_cycle_interval`、`auto_cycle_theme_interval`、`auto_cycle_pause_after_manual`。

---

## 全部规则（141 条）

规则定义与参数已从 Python 代码中拆分到 JSON 文件（`rules/json/` 目录），由 `RuleManager` 统一管理。添加新规则只需修改 JSON，无需改动 Python 逻辑。

### 分类统计

| 类别 | 规则数 | 说明 |
|------|:------:|------|
| **Life-like** | 63 | 2 态 B/S 规则（Conway 等） |
| **Multi-state** | 9 | 3+ 态规则（Wireworld 等） |
| **Complex** | 11 | 自复制环、雪花晶、螺旋波 |
| **Continuous** | 58 | 反应扩散、Lenia、SmoothLife、LtL、1D |

### Life-like 规则（63 条，2 态 B/S 记法）

| 规则名 | B/S | 描述 |
|--------|-----|------|
| `game_of_life` | B3/S23 | Conway 经典生命游戏 |
| `highlife` | B36/S23 | 支持 replicator 模式 |
| `day_and_night` | B3678/S34678 | 黑白反转对称 |
| `seeds` | B2/S∅ | 仅诞生，无存活条件 |
| `maze` | B3/S12345 | 迷宫结构 |
| `mazectric` | B3/S1234 | 迷宫（更直的通道） |
| `34_life` | B34/S34 | 爆炸式增长 |
| `long_life` | B345/S5 | 长寿振荡器 |
| `replicator` | B1357/S1357 | 奇偶对称自复制 |
| `anneal` | B3678/S34678 | Vote 4/5 多数投票 |
| `diamoeba` | B35678/S5678 | 变形虫状菱形图案 |
| `2x2` | B36/S125 | 2×2 方块传递特性 |
| `morley` | B368/S245 | Move — 慢速飞船 |
| `fredkin` | B1357/S02468 | Replicator 变体 2 |
| `flakes` | B3/S012345678 | 无死亡生命 — 雪花增长 |
| `walled_city` | B45678/S2345 | 墙壁城市结构 |
| `live_free_or_die` | B2/S0 | 仅诞生，必死 |
| `gnarl` | B1/S1 | 单细胞爆炸增长 |
| `serviettes` | B234/S∅ | 波斯地毯图案 |
| `coral` | B3/S45678 | 珊瑚状缓慢增长 |
| `drylife` | B37/S23 | 有限飞船选项 |
| `pedestrian_life` | B38/S23 | 独特自然生长图案 |
| `flock` | B3/S12 | 快速稳定多米诺图案 |
| `assimilation` | B345/S4567 | 永久菱形图案 |
| `stains` | B3678/S235678 | 填充有界区域 |
| `coagulations` | B378/S235678 | 浓稠粘液增长 |
| `grounded_life` | B35/S23 | 稳定变体 |
| `eppstein` | B35/S236 | 爆炸增长 |
| `bacteria` | B34/S456 | 细菌增长 |
| `holstein` | B35678/S4678 | 自互补多飞船 |
| `cheerios` | B35678/S34567 | 麦圈图案 |
| `amoeba` | B357/S1358 | 狂野边界变形虫 |
| `pseudo_life` | B357/S238 | 假生命（不稳定滑翔机） |
| `geology` | B3578/S24678 | 大陆→岛屿地质演化 |
| `dotlife` | B3/S023 | 无限增长点图案 |
| `star_trek` | B3/S0248 | 多速度飞船 |
| `iceballs` | B25678/S5678 | 冰球闪烁集群 |
| `magnezones` | B3/S123678 | 四晶体液体 |
| `oscillators_rule` | B45/S1235 | 微型振荡器 |
| `majority` | B5678/S45678 | Vichniac 多数投票 |
| `sandpile` | 4态 | 阿贝尔沙堆模型 |
| ... | ... | _共 63 条，详见 `rules/json/life_rules.json`_ |

### 多状态规则（9 条）

| 规则名 | 态数 | 描述 |
|--------|:--:|------|
| `brians_brain` | 3 | Brian's Brain：波动滑翔机 |
| `wireworld` | 4 | 模拟逻辑电路 |
| `forest_fire` | 3 | 森林火灾模型 |
| `forest_fire_fast` | 3 | 快速蔓延森林火灾 |
| `forest_fire_dense` | 3 | 密集森林火灾 |
| `crystal_growth` | 3 | 晶体生长/雪花图案 |
| `crystal_growth_fast` | 3 | 快速晶体生长 |
| `crystal_growth_sparse` | 3 | 稀疏晶体生长 |
| `sandpile` | 4 | 阿贝尔沙堆模型 |

### 复杂规则（11 条）

| 规则名 | 态数 | 描述 |
|--------|:--:|------|
| `langtons_loop` | 8 | Langton 自复制环 |
| `snowflake` | 8 | 6 重对称树枝晶 |
| `snowflake_dense` | 8 | 密集雪花晶 |
| `snowflake_smooth` | 16 | 平滑梯度雪花 |
| `cyclic` | 14 | Greenberg-Hastings 螺旋波 |
| `cyclic_3` | 3 | 3 色 spiral waves |
| `cyclic_6` | 6 | 6 色 spiral waves |
| `cyclic_24` | 24 | 24 色 spiral waves (threshold 2) |
| `hodgepodge` | 20 | BZ 反应扩散螺旋波 |
| `hodgepodge_fast` | 10 | 快速 hodgepodge |
| `hodgepodge_dense` | 30 | 密集 hodgepodge |

### 连续 CA：Gray-Scott 反应扩散（23 条）

| 规则名 | Preset | f | k | 图案 |
|--------|--------|:---:|:---:|------|
| `gray_scott` / `gray_scott_spots` | spots | 0.035 | 0.065 | 静止斑点 |
| `gray_scott_stripes` | stripes | 0.030 | 0.062 | 条纹/迷宫 |
| `gray_scott_maze` | maze | 0.025 | 0.060 | 有丝分裂迷宫 |
| `gray_scott_waves` | waves | 0.040 | 0.060 | 行波 |
| `gray_scott_pulsating` | pulsating | 0.050 | 0.065 | 呼吸斑点 |
| `gray_scott_chaos` | chaos | 0.020 | 0.055 | 混沌湍流 |
| `gray_scott_bubbles` | bubbles | 0.012 | 0.050 | 大气泡 |
| `gray_scott_tendrils` | tendrils | 0.027 | 0.058 | 触丝/丝状 |
| `gray_scott_solitons` | solitons | 0.030 | 0.057 | 孤立点 |
| `gray_scott_coral` | coral | 0.038 | 0.058 | 珊瑚分支 |
| `gray_scott_u_skate` | u_skate | 0.025 | 0.060 | U-skate 移动孤子 |
| `gray_scott_alpha` | Pearson α | 0.010 | 0.047 | 缓慢扩展斑点 |
| `gray_scott_beta` | Pearson β | 0.020 | 0.048 | 增长条纹网络 |
| `gray_scott_gamma` | Pearson γ | 0.025 | 0.048 | 分裂斑点 |
| `gray_scott_soap` | soap | 0.090 | 0.059 | 六角肥皂泡 |
| `gray_scott_moving` | moving | 0.014 | 0.054 | 移动孤子 |
| `gray_scott_self_rep` | self_rep | 0.026 | 0.061 | 自复制图案 |
| ... | ... | ... | ... | _共 23 条，详见 JSON_ |

### 连续 CA：Lenia（6 条）

| 规则名 | Species | 参数 | 描述 |
|--------|---------|------|------|
| `lenia` | orbium | R=10, μ=0.15, σ=0.015 | 经典 Orbium |
| `lenia_hydro` | hydro | R=20, μ=0.12, σ=0.018 | 流动有机 |
| `lenia_parasite` | parasite | R=15, μ=0.18, σ=0.012 | 虫群有机 |
| `lenia_frother` | frother | R=8, μ=0.20, σ=0.014 | 泡沫有机 |
| `lenia_geminium` | geminium | R=12, μ=0.14, σ=0.016 | 双生有机 |
| `lenia_scedaseum` | scedaseum | R=18, μ=0.11, σ=0.020 | 扩散有机 |

### 连续 CA：Larger than Life（9 条）

| 规则名 | Preset | 半径 | 描述 |
|--------|--------|:---:|------|
| `larger_than_life` | bugs | R5 | 大型虫子滑翔机 |
| `ltl_bugs2` | bugs2 | R3 | 小型滑翔机 |
| `ltl_brain` | brain | R4 | 脑状结构 |
| `ltl_sand` | sand | R2 | 流沙纹理 |
| `ltl_cities` | cities | R3 | 城市方块 |
| `ltl_worms` | worms | R7 | 蠕虫状生物 |
| `ltl_bubbles` | bubbles | R4 | 扩展气泡 |
| `ltl_sea` | sea | R5 | 海浪 |
| `ltl_confetti` | confetti | R2 | 五彩碎纸 |

### 1D 初等规则 Wolfram（15 条）

| 规则名 | Wolfram 号 | 描述 |
|--------|:--------:|------|
| `elementary_1d` | 30 | 混沌（默认） |
| `wolfram_30` | 30 | 随机数生成 |
| `wolfram_90` | 90 | Sierpiński 三角形 |
| `wolfram_110` | 110 | 图灵完备 |
| `wolfram_184` | 184 | 交通流模型 |
| `wolfram_54` | 54 | 复杂滑翔机结构 |
| `wolfram_22` | 22 | 生长三角形 |
| `wolfram_126` | 126 | 分形增长 |
| `wolfram_150` | 150 | XOR 图案 |
| ... | ... | _共 15 条_ |

### 其他连续 CA（5 条）

| 规则名 | 参数 | 描述 |
|--------|------|------|
| `smooth_life` | R=5, b1-b2, d1-d2 | 连续域生命游戏 |
| `smooth_life_soft` | 柔化参数 | 柔化边缘 SmoothLife |
| `bz_reaction` | N=16 | BZ 化学反应螺旋波 |
| `bz_reaction_fast` | N=8 | 快速 BZ 反应 |
| `bz_reaction_smooth` | N=24 | 平滑梯度 BZ 反应 |

---

## 颜色主题（7 种）

| 主题 | 背景 | 风格 |
|------|------|------|
| `neon` | 深蓝黑 | 青→紫→粉 霓虹渐变 |
| `ocean` | 深海蓝 | 浅蓝→青绿 海洋渐变 |
| `ember` | 暗红棕 | 黄→橙→红 火焰渐变 |
| `matrix` | 暗绿黑 | 亮绿矩阵风格 |
| `aurora` | 暗紫 | 青→紫→粉→蓝 极光渐变 |
| `plasma` | 深紫黑 | 品红→紫→青→金 等离子渐变 |
| `sunset` | 暗红黑 | 红→橙→金→粉 日落暖色渐变 |

---

## 预定义图案

| 图案 | 类型 | 尺寸 | 适用规则 |
|------|------|:--:|------|
| `glider` | 飞船 | 3×3 | Life-like |
| `blinker` | 振荡器 | 1×3 | Life-like |
| `block` | 静物 | 2×2 | Life-like |
| `beehive` | 静物 | 3×4 | Life-like |
| `beacon` | 振荡器 | 4×4 | Life-like |
| `pulsar` | 振荡器 | 15×17 | Life-like |
| `lwss` | 飞船 | 4×5 | Life-like |
| `mwss` | 飞船 | 7×5 | Life-like |
| `glider_gun` | 振荡器 | 11×36 | Life-like |
| `langton_loop` | 自复制器 | 17×15 | Langton's Loop |
| `wire_diode` | 逻辑门 | 6×7 | Wireworld |

---

## 渲染管线

增强后的渲染管线采用多阶段处理，兼顾性能与视觉质量：

```
CA 引擎 (grid/age/trail)
      │
      ▼
numpy uint8 像素数组 (cols×rows×3)     ← 向量化构建，含特殊渲染器
      │
      ▼
pygame.surfarray.make_surface()        ← numpy → Surface
      │
      ▼
.convert()                             ← 匹配显示格式，加速 blit
      │
      ▼
smoothscale / scale                    ← 抗锯齿平滑缩放至屏幕分辨率
      │
      ▼
Glow / Bloom 后处理                    ← 降采样→模糊→加法混合 (BLEND_ADD)
      │
      ▼
网格线 + HUD 叠加                       ← 可选覆盖层
      │
      ▼
display.flip() (vsync=1)              ← 垂直同步刷新
```

### 特殊渲染器

| 规则类型 | 渲染方式 |
|----------|----------|
| 2 态 CA | 背景 + age 调色板 + trail 拖尾渐变 |
| 多态 CA | 按 state 索引 state_colors 数组 |
| Gray-Scott | 热力图：R=V(抑制子), G=U(活化子), B=U-V |
| Lenia | 有机渐变：青→品红→黄 |
| SmoothLife | 暖色梯度：深红→橙→黄→白 |

### 辉光/Bloom 后处理

通过降采样-模糊-加法混合实现低成本 bloom 效果：

1. 将当前帧缩放到 1/4 尺寸
2. 多次 smoothscale 模拟高斯模糊
3. 放大回全分辨率
4. 用 `BLEND_ADD` 模式叠加到屏幕，强度由 `glow_intensity` 控制

可通过 `--no-glow` 禁用或 `--glow-intensity 0.5` 调节。

---

## 规则管理架构

```
rules/
├── __init__.py            ← 统一导出 RULES registry + 辅助函数
├── rule_manager.py        ← RuleManager: 读取 JSON → 动态创建规则实例
├── base.py                ← CARule / OuterTotalisticRule + 邻域计数
├── life_rules.py          ← (已弃用，规则在 JSON 中定义)
├── multi_state_rules.py   ← 多态规则 Python 逻辑
├── complex_rules.py       ← 复杂规则 Python 逻辑
├── continuous_rules.py    ← 连续规则 Python 逻辑
├── SandpileRule           ← 在 rule_manager.py 中定义
├── json/                  ← 所有规则定义数据（JSON）
│   ├── life_rules.json        ← 63 条 Life-like B/S 规则
│   ├── multi_state_rules.json ← 9 条多态规则参数
│   ├── complex_rules.json     ← 11 条复杂规则参数
│   ├── gray_scott_rules.json  ← 23 条 Gray-Scott 预设
│   ├── lenia_rules.json       ← 6 条 Lenia species
│   ├── ltl_rules.json         ← 9 条 Larger than Life 预设
│   ├── elementary_1d_rules.json ← 15 条 Wolfram 1D 规则
│   └── other_continuous_rules.json ← 5 条 SmoothLife/BZ 参数
```

**设计原则：** Python 类只负责计算逻辑（`step()` 方法），规则数据（名称、参数、预设、描述）全部在 JSON 中定义。添加新规则只需编辑 JSON 文件，无需修改 Python 代码。

---

## 字体加载

优先加载项目根目录下的本地字体文件 `dinglieciweifont20250217-2.ttf`，确保跨平台一致的 HUD 渲染效果。

回退链：本地 TTF → 系统等宽字体 → pygame 默认字体。

---

## 项目结构

```
cellular_automaton/
├── main.py                          # 标准模式入口（支持自动轮换）
├── wallpaper.py                     # 壁纸模式入口（自动轮换）
├── config.py                        # 配置管理（CLI + JSON + auto_cycle）
├── requirements.txt                 # 依赖：pygame, numpy, scipy
├── run_tests.py                     # 统一测试运行器
├── dinglieciweifont20250217-2.ttf   # 本地中文字体文件
├── core/                            # 核心 CA 引擎
│   └── automaton.py                 # 网格状态管理、演化、图案加载
├── rules/                           # 规则系统
│   ├── rule_manager.py              # RuleManager（JSON → 规则实例）
│   ├── base.py                      # 基类 + convolve2d 邻域计数
│   ├── multi_state_rules.py         # 多态规则计算逻辑
│   ├── complex_rules.py             # 复杂规则计算逻辑
│   ├── continuous_rules.py          # 连续规则计算逻辑
│   └── json/                        # 所有规则定义数据
│       ├── life_rules.json          # 63 条 B/S 规则
│       ├── multi_state_rules.json   # 9 条多态规则
│       ├── complex_rules.json       # 11 条复杂规则
│       ├── gray_scott_rules.json    # 23 条 Gray-Scott 预设
│       ├── lenia_rules.json         # 6 条 Lenia species
│       ├── ltl_rules.json           # 9 条 LtL 预设
│       ├── elementary_1d_rules.json # 15 条 Wolfram 1D
│       └── other_continuous_rules.json # 5 条 SmoothLife/BZ
├── rendering/                       # 渲染层
│   ├── renderer.py                  # 增强渲染管线（smoothscale + glow）
│   ├── color_themes.py              # 7 种颜色主题
│   └── patterns.py                  # 11 种预定义图案
├── ui/                              # 用户交互
│   └── input_handler.py             # 键盘/鼠标 + AutoCycleState
├── audio/                           # 音频系统
│   └── audio_manager.py             # 程序化环境无人机音效
├── screenshots/                     # 壁纸模式截图输出目录
└── tests/                           # 测试套件
    ├── test_rules.py                # 规则注册、步进、正确性
    ├── test_automaton.py            # 核心引擎操作
    ├── test_config.py               # 配置解析
    ├── test_patterns.py             # 图案有效性
    └── test_renderer.py             # 颜色插值/主题
```

---

## 技术特点

- **142 条规则**：涵盖 4 大类别，由 JSON 驱动、Python 执行
- **RuleManager 架构**：JSON 数据 + Python 逻辑彻底分离，添加规则零代码修改
- **自动轮换**：标准模式和壁纸模式均支持，按 A 键切换或 `--auto-cycle` 启动
- **convolve2d 优化**：scipy 加速邻域计数，无 scipy 时自动回退 np.roll
- **连续状态引擎**：Gray-Scott、Lenia、SmoothLife 维护 float32 内部状态
- **抗锯齿平滑缩放**：smoothscale + bloom 后处理
- **垂直同步**：SCALED + vsync=1 消除撕裂
- **本地字体**：内置 TTF 保证跨平台一致性
- **壁纸模式**：Win32 桌面嵌入 + 自动轮换 + 截图导出
- **程序化音频**：5 正弦波叠加，密度驱动音高
- **国际化**：中英文 HUD

---

## 依赖

| 包 | 最低版本 | 用途 |
|----|----------|------|
| `pygame` | ≥2.0 | 图形渲染、事件处理 |
| `numpy` | ≥1.20 | 网格运算 |
| `scipy` | ≥1.7 | 卷积加速（可选，无 scipy 也能运行） |

---

## 运行测试

```bash
# 运行所有测试
python run_tests.py

# 只运行特定模块
python run_tests.py --module rules
python run_tests.py --module automaton
python run_tests.py --module config
python run_tests.py --module patterns
python run_tests.py --module renderer
```

---

## License

MIT
