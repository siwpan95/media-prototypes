# wallpaper1（carboy）— Windows 动态壁纸

基于 tkinter + ctypes 的 Windows 动态壁纸：将窗口挂载到 WorkerW 实现 GIF 动态壁纸，支持托盘图标与快捷键。

> 合并说明（2026-08-21）：已按 MERGE_PLAN.md 吸收 wallpaper5（playUI）的全部独有改进——
> pack_propagate 布局修正、Unsupported system 分支、预览状态栏显示尺寸/帧数；
> wallpaper5 已归档至 G:\media\_archive\wallpaper5。

## 语言 / 类型
Python 3 / GUI 动态壁纸（Windows）

## 目录要点
- `carboy.py` —— 主程序（WindowsWallpaper + GUI）
- `carboy.spec` —— PyInstaller 打包配置

## 运行方式
```bash
python carboy.py
```
会修改系统壁纸，请在预期环境运行。依赖：`Pillow`、`pystray`、`keyboard`（需自行安装）。

## 测试状态
- `py_compile` 语法检查：通过（合并后复检，2026-08-21）
- 壁纸设置类 GUI，未运行（避免改动系统壁纸）
