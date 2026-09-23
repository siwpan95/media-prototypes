# procedural_video

> 仓库：<https://gitee.com/siwpan/procedural-video> ｜ 许可：MIT（见 [LICENSE](LICENSE)）

kkrieger 风格的**过程生成视频生成器**，附带实时预览，几乎纯标准库实现（可整合多种视觉效果）。

## 语言 / 类型

- 语言：Python 3
- 类型：桌面 GUI 程序（tkinter 实时预览）

## 目录要点

- `procedural_video.py`：唯一源码，包含视频参数、AVI 写入器、效果生成与 tkinter 预览界面

## 运行方式与依赖

基本依赖为标准库（`tkinter`、`struct`、`math`、`wave` 等）；音频播放可选 `pygame`（缺失时自动降级）。

```bash
python procedural_video.py
```

启动后为 tkinter 实时预览窗口。

## 测试状态

- 语法检查：通过（`compile` 校验无语法错误）
- 运行：GUI 程序，未实际运行
