# wallpaper1（carboy）↔ wallpaper5（playUI）合并方案

> 生成日期：2026-08-21 ｜ 比对方式：difflib 逐行 + 结构级（class/def）比对

## 0. 总体结论

- wallpaper1/carboy.py：539 行，**功能超集**（多出 WorkerW 动态壁纸、渲染器抽象、GIF→PNG 首帧提取）。
- wallpaper5/playUI.py：439 行，**UI 细节更稳**（pack_propagate 修正布局、Unsupported system 分支、预览帧数/尺寸显示）。
- 两文件前 13 行 import **完全一致**，SequenceMatcher.ratio = 0.2025——主体实现写法不同，但功能面高度重叠（列表管理 / 预览 / 设壁纸 / 自动轮换 / 托盘 / 快捷键 / 状态栏几乎一一对应）。
- **结论：以 wallpaper1/carboy.py 为基底合并，把 playUI 的 3 个改进点移植进来；wallpaper5 归档。**

## 1. 结构对照（类与方法）

| 能力 | carboy.py（wallpaper1） | playUI.py（wallpaper5） | 取谁 |
|---|---|---|---|
| 静态/GIF/文件夹选择、列表加载、选中回调 | ✅ | ✅（逻辑等价） | carboy |
| 预览（静态图） | StaticImageRenderer（按画布实际尺寸缩放） | show_static_preview（硬编码 600×350） | carboy |
| 预览（GIF 动画） | GIFRenderer（按每帧 duration 播放） | animate_gif（固定 100ms/帧） | carboy |
| 设置壁纸 | ✅ 多系统 + **GIF 自动转首帧 PNG** | ✅ 多系统 + Unsupported 分支 | carboy + playUI 的 else 分支 |
| 自动轮换（toggle/start/switch/next） | ✅ | ✅（逐行等价） | 任意（等价） |
| 托盘图标 | ✅ + 额外 "Stop Rendering" 菜单 | ✅ | carboy |
| 全局快捷键 | ✅ Ctrl+Alt+N + **Esc 停止渲染** | ✅ 仅 Ctrl+Alt+N | carboy |
| 系统检测 | ✅ | ✅（等价） | 任意（等价） |
| **真·动态壁纸（WorkerW 挂载）** | ✅ WindowsWallpaper + create_dynamic_wallpaper | ❌ 无 | carboy（独有，必须保留） |
| 预览显示分辨率/帧数 | ❌ | ✅ 状态栏显示 (WxH) / (N frames) | 移植 playUI |
| 布局稳定 | ❌ 无 pack_propagate | ✅ toolbar/left_panel pack_propagate(False) | 移植 playUI |
| FPS / Memory 指示器 | ⚠️ 有 UI 但**从不更新**（死代码） | ❌ 无 | 删除 |
| Unsupported system 提示 | ❌ | ✅ | 移植 playUI |

## 2. 逐项差异明细（行号 = 各文件原行号）

| 位置 | carboy.py | playUI.py | 处置 |
|---|---|---|---|
| L16–49 | WindowsWallpaper（find_workerw + SetParent 挂载） | 无 | **保留**（合并后唯一真动态壁纸能力） |
| L51–139 | WallpaperRenderer/StaticImageRenderer/GIFRenderer 三层渲染抽象 | 无（逻辑内联在 show_*_preview） | **保留** |
| L165–267 | setup_ui：950×600、画布 650×400、多 "🎬 Dynamic Wallpaper" 按钮、FPS/Memory 标签 | setup_ui：900×550、画布 600×350、pack_propagate(False)×2 | 保留 carboy 骨架；**补 pack_propagate(False)**；**删 FPS/Memory 两个从未赋值的标签** |
| L268–288 | create_dynamic_wallpaper：全屏无边框 Tk 窗口 → WorkerW | 无 | **保留** |
| L388–423 | set_wallpaper：GIF → 提取首帧存 PNG 再设壁纸（正确，Windows 不吃 GIF） | set_wallpaper：GIF 原路径直接传给 SystemParametersInfoW（不可靠）；但含 else: Unsupported system 分支 | 以 carboy 为基底；**补 playUI 的 Unsupported 分支** |
| L465–481 | next_wallpaper（与 playUI 等价） | 同 | 不动 |
| L483–507 | 托盘含 "Stop Rendering"；快捷键 Esc → stop_current_renderer | 托盘无该项；无 Esc | 保留 carboy |
| L520–534 | on_close/exit_app 会停渲染器、销毁 dynamic_window | 无对应清理 | 保留 carboy |
| — | 无 | show_gif_preview 状态栏显示帧数、show_static_preview 显示尺寸 | **移植**：在 start_static_renderer/start_gif_renderer 的 status.config 文案中追加 (WxH) / (N frames) |

## 3. 合并步骤（落到 wallpaper1/carboy.py）

1. **UI 稳定性**（来自 playUI）：setup_ui 中给 toolbar 与 left_panel 各加一行 pack_propagate(False)。
2. **删除死代码**（carboy）：删除 fps_label、memory_label 两个 Label 及其容器（从创建到整个生命周期无任何 config(text=...) 调用）。
3. **Unsupported 分支**（来自 playUI）：set_wallpaper 的 if/elif 链末尾加
   else: self.update_status("Unsupported system: ..."); return。
4. **预览信息**（来自 playUI）：静态预览状态栏追加 (img_w x img_h)；
   GIF 预览状态栏追加 (N frames)（在 GIFRenderer.load_frames 之后取 len(self.frames)）。
5. 其余全部保持 carboy 现状（WorkerW、渲染器、Esc、托盘、GIF 首帧提取均不动）。

## 4. 归档与产物

- 合并后单文件：wallpaper1/carboy.py（预计 ~550 行）。
- wallpaper5/ 整个目录 → G:\media\_archive\wallpaper5（连同 form.spec、README，README 头部加一行“已并入 wallpaper1/carboy.py，2026-08-21”）。
- 两项目共有的壁纸设置逻辑（SystemParametersInfoW(20,0,path,3) 等）后续应改为
  import wallpaper2/form.py 的 set_wallpaper()（wallpaper2 是唯一跨平台实现），
  但这属于下一次“公共库抽取”，不在本次合并范围。
- 验证：py_compile 通过；手动启动后依次验证 静态预览 / GIF 预览（帧率跟随 duration）/
  “🎬 Dynamic Wallpaper”挂载 WorkerW / 自动轮换 / Ctrl+Alt+N / Esc / 托盘退出。


## 5. 执行记录（2026-08-21 已执行）

- 第 1 步 ✅：toolbar 与 left_panel 均加 pack_propagate(False)
- 第 2 步 ✅：删除 FPS/Memory 两个从未更新的标签（死代码）
- 第 3 步 ✅：set_wallpaper 补 else: Unsupported system 分支
- 第 4 步 ✅：静态预览状态栏显示原图尺寸 (WxH)，GIF 预览显示帧数 (N frames)
- 第 5 步 ✅：其余保持 carboy 原状（WorkerW 动态壁纸 / 渲染器抽象 / Esc / 托盘 / GIF 首帧提取）
- 验证：py_compile 通过；合并后 carboy.py 共 540 行
- 归档：wallpaper5 已移入 G:\media\_archive\wallpaper5（README 已加归档横幅）
