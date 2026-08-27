"""安装包启动器（PyInstaller 顶层入口）。

shikonghuaban/__main__.py 使用包相对导入（from .main import main），
打包时不能直接作为顶层脚本；此启动器以绝对导入调用包入口。
"""

from shikonghuaban.main import main

if __name__ == "__main__":
    main()
