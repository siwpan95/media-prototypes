# gan

> 仓库：<https://gitee.com/siwpan/gan> ｜ 许可：MIT（见 [LICENSE](LICENSE)）

基于多种经典模型混合的**随机视频生成器**：用马尔可夫链、元胞自动机（Gray-Scott）、CNN / RNN / GNN 逐帧合成视频画面。

## 语言 / 类型

- 语言：Python 3
- 类型：命令行程序 + OpenCV 实时预览（GUI 窗口）

## 目录要点

- `gan.py`：唯一源码，包含全部生成逻辑与命令行入口
- `random_video.mp4`：示例输出视频

## 运行方式与依赖

依赖第三方库：

- `numpy`
- `opencv-python`（`cv2`）

用法：

```bash
python gan.py                     # 实时预览（按 ESC 退出）
python gan.py -o out.mp4 -f 300   # 导出 300 帧视频
```

## 测试状态

- 语法检查：通过（`compile` 校验无语法错误）
- 运行：本机未安装 `cv2`（OpenCV），未实际运行
