# media-tools

媒体 / 视觉方向的小工具集 —— 五个各自独立的小项目，共享一份仓便于统一治理与检索。

> 本仓 2026-10-26 由 `G:\local\media-archive` 归位而来（原为该目录下的归档区）。
> 归位原因：同批归位的 5 个项目各自带「**已归档（2026-08-21）**」声明、功能已被
> [`pywallpaper`](https://gitee.com/siwpan/pywallpaper) 吸收，故随那批一并清理；
> 而下列 5 个**未声明归档、仍独立可用**的项目则建仓纳入 allin 治理。

## 子项目

| 子目录 | 项目 | 说明 |
|---|---|---|
| `art/` | art | 软件三角形光栅化渲染器 —— numpy + Pillow 实现透视投影、视口变换、Z-buffer 深度测试与重心坐标颜色插值 |
| `create/` | create | 手动构造 PNG 图片生成器 —— 用 Pillow 画字后手动拼装 PNG 数据块（IHDR/IDAT/tEXt/IEND），文件名取内容 SHA-256 以避免覆盖 |
| `lap/` | lap | 工业级风扇仿真系统 —— tkinter GUI 仿真小工具 |
| `wallpaper1/` | wallpaper1 (carboy) | Windows 动态壁纸 —— tkinter + ctypes 把窗口挂载到 WorkerW，支持托盘图标与快捷键 |
| `wallpaper2/` | wallpaper2 (form) | 跨平台壁纸设置工具 —— Windows `SystemParametersInfoW` / macOS `osascript` / Linux `gsettings`·`plasma-apply-wallpaper` |

## 附档

- `media-effect-migration-report.md` —— 媒体效果迁移报告（48 个效果中 47 个迁往 pywallpaper 的依据）

## 运行

各子项目自带 `requirements.txt`（`art` / `create` / `lap` 需 numpy、Pillow 等），
`wallpaper1` / `wallpaper2` 以 tkinter 为主。彼此独立，按需单独安装即可。

## 仓库说明

- 只入库源码与文档；各子项目自带的 `.venv` / `build` / `dist` / `__pycache__` 由 `.gitignore` 排除。
- MIT 许可（见 `LICENSE`）。
