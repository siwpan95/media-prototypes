# wallpaper2（form）— 跨平台壁纸设置工具

纯 Python 壁纸设置函数库：Windows 用 `SystemParametersInfoW`，macOS 用 `osascript`，Linux 用 `gsettings` / `plasma-apply-wallpaperimage` / `feh`。

## 语言 / 类型
Python 3 / 壁纸设置工具（命令行函数库，无 GUI）

## 目录要点
- `form.py` —— `set_wallpaper(path)` 函数与命令行 `main()`
- `form.spec` —— PyInstaller 打包配置

## 运行方式
```bash
python form.py /path/to/image.png
```
直接调用 `set_wallpaper(path)` 亦可；会设置系统壁纸，请谨慎运行。依赖：Python 标准库。

## 测试状态
- `py_compile` 语法检查：通过
- 壁纸设置类，未运行（避免改动系统壁纸）
