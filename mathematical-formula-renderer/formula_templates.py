"""
数学公式模板生成器 & 配方工作室
====================================
从 main.py 的模板库中选取初始化/演化/颜色公式，
组合生成新的 JSON 配方写入 effects/ 目录。

用法:
    python formula_templates.py                          # 交互模式
    python formula_templates.py --browse                 # 浏览所有模板
    python formula_templates.py --batch                  # 批量生成 6 个预配示例
    python formula_templates.py --combo <i> <e> <c> <n>  # 指定组合

变量速查:
    初始化:  x, y (归一化坐标 0~1), i, j (像素坐标), random
    演化:    c (当前值), sum_n (邻域和), avg_n (邻域均值), x, y, t (步数), i, j
    颜色:    v (细胞值 0~1), x, y (归一化坐标)
"""

import json
import sys
from pathlib import Path

# 导入 main.py 的模板库
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from main import FORMULA_TEMPLATES, generate_recipe_from_templates, print_template

EFFECTS_DIR = SCRIPT_DIR / 'effects'


# ============================================================
#  预配组合 —— 已验证效果不错的配方
# ============================================================
PRESET_COMBOS = [
    # (初始化, 演化, 颜色, 名称, 网格尺寸)
    ('稀疏随机', 'Game of Life', '反转灰阶', 'Game_of_Life_经典', (300, 200)),
    ('正弦条纹', '反应扩散（Gray-Scott简化）', '绿紫双色', '反应扩散_正弦种子', (256, 256)),
    ('中心脉冲', '激发介质', '霓虹热感', '激发介质_螺旋波', (300, 200)),
    ('Perlin噪声近似', '湍流混合', '彩虹', '湍流_彩虹噪声', (300, 200)),
    ('双高斯斑点', '竞争扩散', '日落', '竞争扩散_双斑点', (256, 192)),
    ('同心环', '各向异性扩散', '位置着色', '各向异性_环纹', (256, 256)),
    ('中心脉冲', '纯扩散', '暖色渐变', '热扩散_脉冲', (200, 150)),
    ('全零', '伪Mandelbrot迭代', '彩虹', '分形_Mandelbrot', (400, 300)),
    ('梯度', '逻辑斯蒂映射耦合', '冷色渐变', '逻辑斯蒂_梯度', (256, 192)),
    ('棋盘格', 'Smooth Life', '反转灰阶', 'SmoothLife_棋盘', (200, 150)),
]


def interactive_mode():
    """交互式选择模板组合"""
    print("\n" + "=" * 60)
    print("  数学公式配方生成器")
    print("=" * 60)

    # 步骤 1: 选初始化
    print("\n【初始化公式】")
    init_names = list(FORMULA_TEMPLATES['init'].keys())
    for i, name in enumerate(init_names, 1):
        tpl = FORMULA_TEMPLATES['init'][name]
        print(f"  {i:2d}. {name:12s}  {tpl['expression']}")
        print(f"      {'':12s}  → {tpl['notes']}")

    while True:
        try:
            choice = input(f"\n  选择 (1-{len(init_names)}): ").strip()
            if not choice:
                init_idx = 0
            else:
                init_idx = int(choice) - 1
            if 0 <= init_idx < len(init_names):
                init_name = init_names[init_idx]
                break
            print(f"  输入 1-{len(init_names)}")
        except ValueError:
            print(f"  请输入数字 1-{len(init_names)}")
        except (EOFError, KeyboardInterrupt):
            print("\n  已取消")
            return

    # 步骤 2: 选演化
    print(f"\n【演化规则】（当前初始化: {init_name}）")
    evo_names = list(FORMULA_TEMPLATES['evolution'].keys())
    for i, name in enumerate(evo_names, 1):
        tpl = FORMULA_TEMPLATES['evolution'][name]
        print(f"  {i:2d}. {name}")
        print(f"      公式: {tpl['expression']}")
        print(f"      → {tpl['notes']}")

    while True:
        try:
            choice = input(f"\n  选择 (1-{len(evo_names)}): ").strip()
            if not choice:
                evo_idx = 0
            else:
                evo_idx = int(choice) - 1
            if 0 <= evo_idx < len(evo_names):
                evo_name = evo_names[evo_idx]
                break
            print(f"  输入 1-{len(evo_names)}")
        except ValueError:
            print(f"  请输入数字 1-{len(evo_names)}")
        except (EOFError, KeyboardInterrupt):
            print("\n  已取消")
            return

    # 步骤 3: 选颜色
    print(f"\n【颜色映射】（当前: {init_name} + {evo_name}）")
    col_names = list(FORMULA_TEMPLATES['color'].keys())
    for i, name in enumerate(col_names, 1):
        tpl = FORMULA_TEMPLATES['color'][name]
        print(f"  {i:2d}. {name}")
        print(f"      R={tpl['red']}, G={tpl['green']}, B={tpl['blue']}")
        print(f"      → {tpl['notes']}")

    while True:
        try:
            choice = input(f"\n  选择 (1-{len(col_names)}): ").strip()
            if not choice:
                col_idx = 0
            else:
                col_idx = int(choice) - 1
            if 0 <= col_idx < len(col_names):
                col_name = col_names[col_idx]
                break
            print(f"  输入 1-{len(col_names)}")
        except ValueError:
            print(f"  请输入数字 1-{len(col_names)}")
        except (EOFError, KeyboardInterrupt):
            print("\n  已取消")
            return

    # 步骤 4: 命名 & 网格
    default_name = f'{init_name}_{evo_name}_{col_name}'
    print(f"\n【配方名称 & 网格】")
    name = input(f"  配方名称 [默认: {default_name}]: ").strip()
    if not name:
        name = default_name

    # 显示效果预览信息
    print(f"\n{'='*60}")
    print(f"  配方预览")
    print(f"{'='*60}")
    print(f"  名称: {name}")
    print(f"  初始化: {init_name}")
    print(f"    → {FORMULA_TEMPLATES['init'][init_name]['expression']}")
    print(f"  演化: {evo_name}")
    print(f"    → {FORMULA_TEMPLATES['evolution'][evo_name]['expression']}")
    print(f"  颜色: {col_name}")
    for ch in ['red', 'green', 'blue']:
        print(f"    {ch}: {FORMULA_TEMPLATES['color'][col_name][ch]}")

    confirm = input(f"\n  生成? [Y/n]: ").strip().lower()
    if confirm and confirm != 'y':
        print("  已取消")
        return

    # 生成
    recipe = generate_recipe_from_templates(init_name, evo_name, col_name, name=name)
    EFFECTS_DIR.mkdir(exist_ok=True)
    safe_name = name.replace(' ', '_').replace('/', '_')
    out_path = EFFECTS_DIR / f'{safe_name}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)
    print(f"\n  [√] 已生成: {out_path}")
    print(f"  [→] 运行 python main.py 即可查看")


def batch_generate():
    """批量生成预配示例"""
    EFFECTS_DIR.mkdir(exist_ok=True)
    print(f"\n批量生成 {len(PRESET_COMBOS)} 个预设配方到 {EFFECTS_DIR}/\n")

    for init_name, evo_name, col_name, name, (w, h) in PRESET_COMBOS:
        # 跳过已有文件
        safe_name = name.replace(' ', '_').replace('/', '_')
        out_path = EFFECTS_DIR / f'{safe_name}.json'
        if out_path.exists():
            print(f"  [跳过] {name} (已存在)")
            continue

        recipe = generate_recipe_from_templates(
            init_name, evo_name, col_name, name=name, w=w, h=h
        )
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)
        print(f"  [√] {name} ← {init_name} + {evo_name} + {col_name}")

    print(f"\n完成！运行 python main.py 启动引擎")


def browse_templates():
    """非交互式浏览所有模板（详细打印）"""
    print_template('all')
    print(f"\n{'='*60}")
    print(f"  可用变量参考")
    print(f"{'='*60}")
    print(f"  初始化公式可用变量:")
    print(f"    x, y   — 归一化网格坐标 (0~1)")
    print(f"    i, j   — 像素坐标 (整数)")
    print(f"    random — 随机数 (0~1)")
    print(f"\n  演化规则可用变量:")
    print(f"    c      — 当前细胞值 (0~1)")
    print(f"    sum_n  — 邻域和")
    print(f"    avg_n  — 邻域均值 (0~1)")
    print(f"    x, y   — 归一化坐标")
    print(f"    t      — 演化步数")
    print(f"    i, j   — 像素坐标")
    print(f"\n  颜色映射可用变量:")
    print(f"    v      — 细胞值 (0~1)")
    print(f"    x, y   — 归一化坐标")
    print(f"\n  内置数学函数: sin, cos, exp, abs, sqrt, random, clip, min, max")


def combo_generate(init_name, evo_name, col_name, recipe_name):
    """指定组合直接生成"""
    recipe = generate_recipe_from_templates(init_name, evo_name, col_name, name=recipe_name)
    EFFECTS_DIR.mkdir(exist_ok=True)
    safe_name = recipe_name.replace(' ', '_').replace('/', '_')
    out_path = EFFECTS_DIR / f'{safe_name}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)
    print(f"[√] 已生成: {out_path}")


# ============================================================
#  入口
# ============================================================
if __name__ == '__main__':
    if '--browse' in sys.argv:
        browse_templates()
    elif '--batch' in sys.argv:
        batch_generate()
    elif '--combo' in sys.argv:
        idx = sys.argv.index('--combo')
        args = sys.argv[idx + 1:]
        if len(args) >= 4:
            combo_generate(args[0], args[1], args[2], args[3])
        else:
            print("用法: --combo <初始化模板> <演化模板> <颜色模板> <配方名>")
    else:
        interactive_mode()
