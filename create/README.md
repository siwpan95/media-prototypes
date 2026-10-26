# create — 手动构造 PNG 图片生成器

用 Pillow 绘制文字后，手动拼装 PNG 数据块（IHDR / IDAT / tEXt / IEND），在图片中嵌入 tEXt 注释，文件名由内容 SHA-256 哈希决定以避免覆盖。

## 语言 / 类型
Python 3 / 命令行工具（无 GUI）

## 目录要点
- `create.py` —— 主程序（`make_png_with_text` 函数 + demo）
- `output/` —— 输出目录示例

## 运行方式
```bash
python create.py
```
默认输出到当前目录（生成 `img_<hash>.png`）。依赖：`Pillow`。

## 测试状态
- `py_compile` 语法检查：通过
- 命令行试运行：成功（生成 2 张 PNG）
