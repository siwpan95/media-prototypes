"""
MVC架构 - 细胞自动机模拟器
入口文件

架构说明:
- models/: 数据模型层 (GridState, FormulaEngine)
- views/: 视图层 (MainView, SidebarView)
- controllers/: 控制器层 (AppController)
- constants.py: 配置常量
"""

from controllers import AppController


def main():
    """应用入口"""
    app = AppController()
    app.run()


if __name__ == "__main__":
    main()
