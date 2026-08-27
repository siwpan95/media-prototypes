# ddd2（元胞自动机视频生成器）

一款使用元胞自动机生成视频、并带 tkinter 界面的应用。

## 语言 / 类型
- Python / tkinter 图形界面 + 视频生成

## 目录要点
- `ddd (2).py` —— 唯一入口（元胞自动机 + tkinter 界面 + moviepy 视频导出）
- `ddd (2).spec` —— PyInstaller 打包配置

## 运行方式与依赖
- 运行：`F:\Python314\python.exe "ddd (2).py"`
- 依赖：numpy、Pillow、moviepy、scipy（numba 可选，缺失时自动降级）

## 测试状态
- py_compile 语法检查通过
- GUI 窗口程序，未运行（仅编译）
