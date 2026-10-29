"""
MVC架构 - 细胞自动机模拟器
├── models/          # 数据模型层
│   ├── __init__.py
│   ├── grid_state.py    # 网格状态管理
│   └── formula_engine.py # 公式引擎
├── views/           # 视图层
│   ├── __init__.py
│   ├── main_view.py     # 主视图
│   └── sidebar_view.py  # 侧边栏视图
├── controllers/     # 控制器层
│   ├── __init__.py
│   └── app_controller.py # 应用控制器
└── main.py          # 入口文件
"""

from .grid_state import GridState
from .formula_engine import FormulaEngine

__all__ = ['GridState', 'FormulaEngine']
