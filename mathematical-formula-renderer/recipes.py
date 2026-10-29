"""
配方管理模块 —— 从 effects/ 目录加载 JSON 配方，以及从模板组合生成配方。
"""

import json
from pathlib import Path

from templates import FORMULA_TEMPLATES


def load_effects_from_dir(effects_dir, progress_callback=None):
    """扫描目录下所有 .json 配方，返回 {名称: 文件路径}

    Args:
        effects_dir: effects 目录路径
        progress_callback: 可选回调 callback(current, total, filename)
    """
    effects_dir = Path(effects_dir)
    if not effects_dir.exists():
        print(f"[警告] 目录不存在: {effects_dir}")
        return {}

    json_files = sorted(effects_dir.glob('*.json'))
    total = len(json_files)
    recipes = {}
    for i, fpath in enumerate(json_files):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            name = data.get('name', fpath.stem)
            recipes[name] = str(fpath)
            print(f"[加载] {name}  ←  {fpath.name}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"[跳过] {fpath.name}: {e}")
        if progress_callback:
            progress_callback(i + 1, total, fpath.name)
    return recipes


def generate_recipe_from_templates(init_name, evolution_name, color_name,
                                    name='自定义配方', w=256, h=192):
    """从模板组合生成一个完整配方 dict"""
    recipe = {
        'name': name,
        'version': '1.0',
        'grid': {'width': w, 'height': h, 'wrap': True,
                  'initial': {'type': 'formula', 'expression': ''}},
        'evolution': {'rule': '', 'variables': ['c', 'sum_n', 'avg_n', 'x', 'y', 't']},
        'color': {'mode': 'per_channel', 'red': 'v', 'green': 'v', 'blue': 'v'},
    }

    # 初始化公式
    if init_name in FORMULA_TEMPLATES['init']:
        recipe['grid']['initial']['expression'] = FORMULA_TEMPLATES['init'][init_name]['expression']
    else:
        print(f"[警告] 未知初始化模板: {init_name}，使用 random()")
        recipe['grid']['initial']['expression'] = 'random()'

    # 演化规则
    if evolution_name in FORMULA_TEMPLATES['evolution']:
        ev = FORMULA_TEMPLATES['evolution'][evolution_name]
        recipe['evolution']['rule'] = ev['expression']
        if 'variables' in ev:
            recipe['evolution']['variables'] = ev['variables']
    else:
        print(f"[警告] 未知演化模板: {evolution_name}，使用扩散")
        recipe['evolution']['rule'] = 'c + 0.2*(avg_n - c)'

    # 颜色映射
    if color_name in FORMULA_TEMPLATES['color']:
        col = FORMULA_TEMPLATES['color'][color_name]
        recipe['color']['red'] = col['red']
        recipe['color']['green'] = col['green']
        recipe['color']['blue'] = col['blue']
    else:
        print(f"[警告] 未知颜色模板: {color_name}，使用灰阶")

    return recipe
