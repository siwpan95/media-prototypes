# art — 软件三角形光栅化渲染器

用 numpy + Pillow 实现的纯 Python 软件光栅化示例：透视投影、视口变换、Z-buffer 深度测试与重心坐标颜色插值，把单个三角形渲染成 PNG。

## 语言 / 类型
Python 3 / 命令行图形渲染示例（无 GUI）

## 目录要点
- `main.py` —— 光栅化器（`Rasterizer` 类）与 demo，运行后输出 `triangle.png`
- `triangle.png` —— 已生成的示例输出

## 运行方式
```bash
python main.py
```
依赖：`numpy`、`Pillow`。

## 测试状态
- `py_compile` 语法检查：通过
- 命令行试运行：成功（生成 `triangle.png`）
