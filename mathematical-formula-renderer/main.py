"""
CA 渲染引擎 —— 从 effects/ 目录加载数学公式配方
支持：所有 JSON 配方自动扫描、热切换、数学公式模板生成、循环往复渲染
新增：后处理特效、HUD、颜色预设、自动播放、缩放

用法：
    python main.py                          # 启动可视化
    python main.py --template init          # 打印初始化公式模板
    python main.py --template evolution     # 打印演化规则模板
    python main.py --template color         # 打印颜色映射模板
    python main.py --template all           # 打印全部模板
    python main.py --template-list          # 列出所有模板名称
    python main.py --generate <模板名>      # 交互式生成新配方
    python main.py --composer               # 可视化配方编辑器

循环配置在配方 JSON 中设置：
    "cycle": {"steps": 300}                 # 每300步自动重新初始化
"""

import json
import sys
from pathlib import Path

from templates import FORMULA_TEMPLATES, print_template, list_all_templates
from recipes import generate_recipe_from_templates


def main():
    script_dir = Path(__file__).parent
    effects_dir = script_dir / 'effects'

    if '--template' in sys.argv:
        idx = sys.argv.index('--template')
        ttype = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else 'all'
        print_template(ttype)

    elif '--template-list' in sys.argv:
        list_all_templates()

    elif '--generate' in sys.argv:
        idx = sys.argv.index('--generate')
        args = sys.argv[idx + 1:]
        if len(args) >= 3:
            init, evo, col = args[0], args[1], args[2]
            name = args[3] if len(args) > 3 else f'{init}_{evo}_{col}'
            recipe = generate_recipe_from_templates(init, evo, col, name=name)
            effects_dir.mkdir(exist_ok=True)
            safe_name = name.replace(' ', '_').replace('/', '_')
            out_path = effects_dir / f'{safe_name}.json'
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(recipe, f, indent=2, ensure_ascii=False)
            print(f"[√] 已生成: {out_path}")
        else:
            print("用法: python main.py --generate <初始化模板> <演化模板> <颜色模板> [配方名称]")
            print("示例: python main.py --generate '中心脉冲' '反应扩散（Gray-Scott简化）' '绿紫双色'")

    elif '--composer' in sys.argv:
        from renderer import _launch_composer_only
        _launch_composer_only(effects_dir)

    else:
        from renderer import launch
        launch(effects_dir)


if __name__ == '__main__':
    main()
