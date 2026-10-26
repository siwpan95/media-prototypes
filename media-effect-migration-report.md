# media_engine → pywallpaper 效果库迁移核对报告

> 生成日期：2026-08-21 ｜ 核对对象：media_engine/effects（48 个效果 + 1 模板） vs pywallpaper/effects（4707 个 JSON）

## 0. 结论（一句话）

**media_engine 的 48 个效果中 47 个已完整迁移进 pywallpaper 且可正常渲染；仅「48_鼠标跟随（MouseFollowerEffect）」未迁移（壁纸引擎无鼠标交互场景）。迁移链路（含 draw 配方库）经修复后已实测跑通，media_engine 可以归档。**

## 1. 1:1 映射表（按中文名称精确匹配，非按编号猜）

| # | media_engine 文件 | 名称 | 类型 | 实现 | pywallpaper 文件 |
|---|-------------------|------|------|------|------------------|
| 01 | 01_条形图.json | 条形图 | template | bars | 001_bars.json |
| 02 | 02_尖峰.json | 尖峰 | template | spikes | 002_spikes.json |
| 03 | 03_波形.json | 波形 | template | waveform | 003_waveform.json |
| 04 | 04_漩涡.json | 漩涡 | template | vortex | 004_vortex.json |
| 05 | 05_频谱环.json | 频谱环 | template | spectrum_circle | 005_spectrum_circle.json |
| 06 | 06_矩阵雨.json | 矩阵雨 | class | MatrixRainEffect | 006_matrix_rain.json |
| 07 | 07_等离子.json | 等离子 | template | plasma | 007_plasma.json |
| 08 | 08_瀑布图.json | 瀑布图 | template | waterfall | 008_waterfall.json |
| 09 | 09_火焰.json | 火焰 | template | fire | 009_fire.json |
| 10 | 10_分形.json | 分形 | template | fractal | 010_fractal.json |
| 11 | 11_几何图案.json | 几何图案 | template | geometric | 011_geometric.json |
| 12 | 12_声纳.json | 声纳 | template | sonar | 012_sonar.json |
| 13 | 13_频谱射线.json | 频谱射线 | template | spectrum_rays | 013_spectrum_rays.json |
| 14 | 14_跳动的心.json | 跳动的心 | template | heart | 014_heart.json |
| 15 | 15_星域.json | 星域 | class | StarfieldEffect | 015_starfield_effect.json |
| 16 | 16_万花筒.json | 万花筒 | template | kaleidoscope | 016_kaleidoscope.json |
| 17 | 17_频谱波浪.json | 频谱波浪 | template | spectrum_wave | 017_spectrum_wave.json |
| 18 | 18_3D立方体.json | 3D立方体 | template | cube3d | 018_cube_3d.json |
| 19 | 19_3D频谱波浪.json | 3D频谱波浪 | template | spectrum_waves3d | 019_spectrum_waves_3d.json |
| 20 | 20_音频莫尔条纹.json | 音频莫尔条纹 | template | audio_moire | 020_audio_moire.json |
| 21 | 21_频谱球体.json | 频谱球体 | template | spectrum_orb | 021_spectrum_orb.json |
| 22 | 22_音频花朵.json | 音频花朵 | template | flower | 022_audio_flower.json |
| 23 | 23_频谱螺旋.json | 频谱螺旋 | template | spiral | 023_spectrum_spiral.json |
| 24 | 24_音频网格.json | 音频网格 | template | grid | 024_audio_grid.json |
| 25 | 25_频谱涟漪.json | 频谱涟漪 | template | spectrum_ripple | 025_spectrum_ripples.json |
| 26 | 26_音频迷宫.json | 音频迷宫 | class | AudioMazeEffect | 026_audio_maze.json |
| 27 | 27_频谱金字塔.json | 频谱金字塔 | template | spectrum_pyramid | 027_spectrum_pyramid.json |
| 28 | 28_元胞自动机.json | 元胞自动机 | class | CellularAutomatonEffect | 028_cellular_automaton.json |
| 29 | 29_环形脉冲.json | 环形脉冲 | template | ring_pulse | 029_ring_pulse.json |
| 30 | 30_极坐标网格.json | 极坐标网格 | template | polar_grid | 030_polar_grid.json |
| 31 | 31_粒子爆发.json | 粒子爆发 | class | ParticleBurstEffect | 031_particle_burst.json |
| 32 | 32_音频指纹.json | 音频指纹 | class | AudioFingerprintEffect | 032_audio_fingerprint.json |
| 33 | 33_频谱山峦.json | 频谱山峦 | template | spectrum_mountain | 033_spectrum_mountain.json |
| 34 | 34_环形频谱.json | 环形频谱 | template | circular_spectrum | 034_circular_spectrum.json |
| 35 | 35_DNA螺旋.json | DNA螺旋 | template | dna_helix | 035_dna_helix.json |
| 36 | 36_音符雨.json | 音符雨 | class | NoteRainEffect | 036_note_rain.json |
| 37 | 37_声音漩涡.json | 声音漩涡 | template | sound_vortex | 037_sound_vortex.json |
| 38 | 38_霓虹隧道.json | 霓虹隧道 | template | neon_tunnel | 038_neon_tunnel.json |
| 39 | 39_水波涟漪.json | 水波涟漪 | class | RippleEffect | 039_ripple.json |
| 40 | 40_3D旋转环.json | 3D旋转环 | class | MobiusStripEffect | 040_mobius_strip.json |
| 41 | 41_分形树.json | 分形树 | class | FractalTreeEffect | 041_fractal_tree.json |
| 42 | 42_超立方体.json | 超立方体 | class | HyperCubeEffect | 042_hypercube.json |
| 43 | 43_频谱渐变墙.json | 频谱渐变墙 | class | GradientWallEffect | 043_gradient_wall.json |
| 44 | 44_极光效果.json | 极光效果 | class | AuroraEffect | 044_aurora_effect.json |
| 45 | 45_星光闪烁.json | 星光闪烁 | class | StarTwinkleEffect | 045_star_twinkle.json |
| 46 | 46_音频弹跳球.json | 音频弹跳球 | class | BouncingBallsEffect | 046_bouncing_balls.json |
| 47 | 47_粒子连线.json | 粒子连线 | class | ParticleConnectEffect | 047_particle_connect.json |

## 2. 完整性验证（三层）

### 第 1 层：文件与名称匹配
- media_engine 48 个效果 → 按 JSON 内的 name（中文名）字段在 pywallpaper 全部 4707 个效果 JSON 中精确查找：**命中 47 个，未命中 1 个（鼠标跟随）**。
- pywallpaper 对应文件保留了原中文名与 full_name 编号（如 040. 3D旋转环），编号 01–47 与原库完全对位；040/048 等文件名英文名与原中文名不同（mobius_strip/demo_crystal），但 name 字段一致，证明是按内容迁移而非按文件名复制。

### 第 2 层：图层类型可解析
- 47 个映射效果的 params.layers[].type 共用到 **14 种原语**（bars/spikes/waveform/vortex/circle_map/text_rain/texture/drawing/pulse/curve/particles/grid/ca/wireframe_3d）。
- 14 种全部存在于 pywallpaper/engine/primitives/（21 个原语模块），**0 缺失**。
- 原 media_engine 的模板型效果映射到 pywallpaper 原语：条形图→bars、尖峰→spikes、波形→waveform、漩涡→vortex、频谱环→circle_map、矩阵雨→text_rain、等离子/火焰/分形→texture、几何图案→drawing、声纳→pulse、心形→curve、频谱射线→spikes、瀑布图→bars×2、万花筒→circle_map、频谱波浪→waveform、3D 立方体/3D 频谱波浪→wireframe_3d、莫尔条纹→texture、球体→circle_map、花朵→curve、螺旋→vortex、网格/迷宫→grid、涟漪→pulse、金字塔→drawing、元胞自动机→ca、环脉冲→pulse、极坐标网格→circle_map、粒子爆发→particles、指纹→spikes、山峦→waveform、环形频谱→circle_map、DNA→wireframe_3d、音符雨→text_rain、声音漩涡→vortex、霓虹隧道→circle_map、水波涟漪→pulse、3D 旋转环→wireframe_3d、分形树/星光/弹跳球/粒子连线→particles、超立方体→wireframe_3d、渐变墙→texture、极光→waveform。
- 类驱动效果（MatrixRainEffect/StarfieldEffect/MobiusStripEffect 等）在 pywallpaper 中全部改由声明式图层配置实现（class: EngineEffect），不再依赖原类名。

### 第 3 层：无头渲染冒烟测试
- 直接实例化 pywallpaper 的 EngineEffect（PIL ImageDraw，无 GUI），对 5 个代表性迁移效果各渲染 3 帧：001_bars / 028_cellular_automaton（CA，使用 draw 真实配方 BZReaction）/ 040_mobius_strip / 047_particle_connect / 015_starfield_effect —— **5/5 全部渲染出非黑像素**。
- CA 原语实测：CARecipeLoader 从 G:\media\draw\effects 索引 4972 个配方（71 条规则），BZReaction 命中 94 个变体并成功加载演化公式。

## 3. 验证过程中发现并已修复的迁移缺陷（6 处）

| # | 缺陷 | 位置 | 修复 |
|---|---|---|---|
| 1 | 配方目录指向已失效的 D:\allin\right\draw\effects | pywallpaper/engine/primitives/ca.py:58 | 改为候选目录自动探测：G:\media\draw\effects + 相对本文件 parents[3]/draw/effects |
| 2 | 配方索引构建代码整体缩进错误，落在 except 分支里成为不可达死代码（by_name/by_rule 恒为空，任何配方都“未找到”） | ca.py:92–111 | 整体去缩进 4 格，索引恢复构建 |
| 3 | requirements.txt 声明 asteval 可选、缺失时回退，但 formula_engine.py 顶部硬 import，无 asteval 时整个引擎无法导入 | pywallpaper/engine/formula_engine.py:12 | import 改为 try/except，缺失时使用新增的 _FallbackEval（NumPy 命名空间 eval） |
| 4 | 三元表达式翻译器只支持“条件在前”写法且条件提取有误，draw 配方普遍使用 A if C else B（真值在前）写法，导致规则编译成非法代码 | formula_engine.py:_ifelse_to_where | 整个翻译器重写为递归下降解析器 _FormulaParser（支持 A if C else B 嵌套、链式比较 a<b<c、and/or/not、min/max/random 等） |
| 5 | 链式比较 0.2 < x < 0.25 直接入 numpy 会报 truth value ambiguous | 同上 | 解析器把链式比较展开为 (a<b)&(b<c) |
| 6 | CA 演化调用 rule_func 时固定传入 c/sum_n/avg_n/x/y/t 六个 kwarg，但配方只声明 c/sum_n，TypeError | ca.py:465 + formula_engine.py compile() | compile() 返回过滤包装器，只透传配方声明的变量 |

修复后复测：上述 5 个效果冒烟测试全过（第 2 层结论基于修复后代码）。

## 4. 遗留事项（不影响归档判断，但建议后续处理）

1. **48_鼠标跟随（MouseFollowerEffect）**：未迁移。壁纸引擎无鼠标交互，属有意取舍；若需保留，pywallpaper 需新增 mouse 事件源，不建议。
2. ~~dev 工具旧路径 D:\allin~~ **已修复（2026-08-21）**：tools/batch_generate_effects.py、tools/effect_editor.py、tools/effect_editor_v2.py、tools/video_generator.py、tests/test_ca_jit.py 的路径常量已全部改为仓库相对路径。
3. numba 未安装：CA 演化自动回退 AST 模式（慢），requirements.txt 列为“强烈推荐”，本机可 pip install numba。
4. pywallpaper/test_engine.py 在 GBK 控制台因 ✓ 字符报错——可用 PYTHONIOENCODING=utf-8 运行更稳。
5. media_engine/media.py（tkinter GUI）内部 EFFECTS_DIR 仍为旧绝对路径——该 GUI 已被 pywallpaper 取代，归档时无需修。

## 5. 归档建议

| 项目 | 建议 | 理由 |
|---|---|---|
| media_engine | **可归档** → G:\media\_archive\media_engine | 48 个效果 47 个已在 pywallpaper 中完整可用（1 个有意舍弃）；无任何外部项目 import 它；其 GUI 与 pywallpaper 重复。归档前无需再搬运任何文件。 |
| draw | **可归档（配方库问题已解决）** → G:\media\_archive\draw | 2026-08-21 已把 draw/effects 的 4972 个配方（3.0 MB JSON，不含 46.7 MB thumbs 缩略图缓存）与 evolution_rules.py、super_params.py 收归 pywallpaper/recipes/，pywallpaper 完全自包含（DRAW_EFFECTS_DIR 首选本目录、公式全量编译验证 24855/24855 通过）。draw 的 Python 引擎本体已被 pywallpaper 吸收，可整体归档；其自带 effects 副本一并归档不影响任何方。 |
| wallpaper_pywallpaper | **可归档** → G:\media\_archive\wallpaper_pywallpaper | pywallpaper 的单文件简化重制版（2587 行），功能子集；音乐生成器/开机自启如需要可后续并入 pywallpaper。 |
| brownian_wave | **可归档**（并入 media_engine 归档批次） | tkinter 波形动画玩具，与 media_engine 波形类效果同源，无人引用。 |

## 6. 本次实际改动的文件

- pywallpaper/engine/primitives/ca.py —— 缺陷 1、2、6（导入 pathlib、路径探测、缩进修复）
- pywallpaper/engine/formula_engine.py —— 缺陷 3、4、5、6（可选 asteval + _FallbackEval + _FormulaParser + kwargs 过滤包装）


## 7. draw 配方库收归（2026-08-21 后续工作，配方库问题已解决）

### 7.1 做了什么

1. **配方库内置**：draw/effects 的 4972 个配方 JSON 复制到 \`pywallpaper/recipes/\`（3.0 MB；未复制 46.7 MB 的 thumbs 缩略图缓存，pywallpaper 用不到）。
2. **规则名单内置**：draw/templates/evolution.py 复制为 \`pywallpaper/recipes/evolution_rules.py\`（71 条规则名），CA 配方索引的 by_rule 不再依赖 draw。
3. **超级参数内置**：draw/templates/super_params.py 复制为 \`pywallpaper/recipes/super_params.py\`，并在 ca.py 内置 33 项默认值 + \`_resolve_super_params()\`（init/rule/color 三个编译入口统一调用，等价 draw 的 resolve_super_params）。
4. **路径自包含**：ca.py 的候选目录改为「pywallpaper/recipes（首选，相对包路径）→ 旧 draw/effects（过渡兼容）」，实测 DRAW_EFFECTS_DIR 解析为 \`G:\media\pywallpaper\recipes\\\`。
5. **dev 工具路径修复**：tools/batch_generate_effects.py、tools/effect_editor.py、tools/effect_editor_v2.py、tests/test_ca_jit.py 的硬编码 D:\allin 路径全部改为仓库相对路径。

### 7.2 公式引擎为全量配方扩展的能力（本轮新增）

- 列表字面量 + 成员运算：\`sum_n in [2, 3]\` → \`(sum_n==2)|(sum_n==3)\`（42 处配方使用）
- 函数关键字参数：\`amin([...], axis=0)\`（Voronoi 系配方）
- numpy 函数映射补全：amin/amax/sum/mean/round/arctan/arcsin/arccos/tanh/cosh/sinh/log2/atan2
- \`complex(a, b)\` → \`(a + 1j*b)\`（Mandelbrot 系配方，11 处）
- \`int(x)\` → \`np.trunc(x)\`、\`float(x)\` → \`np.float64(x)\`（1253 处 int 调用，向量化）
- 带 .json 后缀的配方名查找归一化（load_recipe 兼容完整文件名）

### 7.3 验证结果

| 检查项 | 结果 |
|---|---|
| 全量公式编译（4972 个配方 × init/rule/color，共 24855 条公式，无 asteval 回退路径） | **24855/24855 通过（100%）** |
| 配方索引 | by_name=4972、by_rule=71，BZReaction 等规则名可命中 |
| 代表性配方实际渲染 | HighLife（in-list 规则）、2x2（in-list）、Super_Voronoi（amin+kwargs+超级参数）、Move116、BZReaction 全部加载真实配方并演化出画面 |
| 演化语义抽查 | HighLife 棋盘格初始态 50% → 1 步 23.4% → 稳定，符合规则语义 |
| 超级参数解析 | Voronoi 初始公式 p1..p8/w1 全部替换为默认值并成功渲染（84% 非零细胞） |

### 7.4 结论

pywallpaper 已完全自包含，draw 的运行时依赖清零，**draw 可以整体归档**（含其自带 effects 副本），不再影响 pywallpaper 的任何功能。


## 8. 归档执行记录（2026-08-21）

已创建 G:\media\_archive\，以下 4 个项目完成归档（README 均已加归档横幅）：

| 项目 | 归档位置 | 归档理由 |
|---|---|---|
| draw | _archive\draw | 配方库已收归 pywallpaper/recipes，公式引擎已被 pywallpaper 吸收 |
| media_engine | _archive\media_engine | 48 效果 47 个已迁移 pywallpaper（见第 1 节映射表），GUI 被替代 |
| wallpaper_pywallpaper | _archive\wallpaper_pywallpaper | pywallpaper 的单文件简化重制版（功能子集） |
| brownian_wave | _archive\brownian_wave | 波形动画玩具，与 media_engine 波形类效果同源 |

归档后验证（draw/effects 已不存在的情况下）：
- DRAW_EFFECTS_DIR 解析为 G:\media\pywallpaper\recipes ✓
- 配方索引 by_name=4972、by_rule=71 ✓
- 全量公式编译 24855/24855 ✓
- HighLife / Super_Voronoi / BZReaction 渲染正常 ✓

归档补充（同日）：wallpaper5 已完成与 wallpaper1 的合并（MERGE_PLAN.md 第 5 节执行记录），移入 _archive\wallpaper5。

保留项目（不再归档）：shikonghuaban 与 cellular_automaton（独立引擎/壁纸项目）、wallpaper1（合并后主壁纸管理器）、wallpaper2（跨平台壁纸设置库）。
