#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片 → 视频 生成器 GUI（Tkinter）。

模式：
  1. 网格拼贴定格   2. 横向长图滚动   3. 纵向长图滚动
  4. 幻灯片淡入淡出   5. KenBurns 推镜   6. 逐张高亮
"""

import os
import math
import shutil
import subprocess
import tempfile
import threading

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

from core import even, find_ffmpeg, load_images, pi_duration
from compositors import make_grid_image, make_strip_image, make_highlight_assets
from ffmpeg_utils import run_ffmpeg_with_progress


# --------------------------------------------------------------------------- #
# GUI
# --------------------------------------------------------------------------- #
class App(tk.Tk):
    MODES = ["grid", "h", "v", "slideshow", "kenburns", "highlight"]
    NAMES = ["grid_video.mp4", "hstrip_video.mp4", "vstrip_video.mp4",
             "slideshow.mp4", "kenburns.mp4", "highlight.mp4"]

    def __init__(self):
        super().__init__()
        self.title("图片 → 视频 生成器（网格/滚动/幻灯片/KenBurns/高亮）")
        self.geometry("800x700")
        self.image_paths = []
        self.preview_img = None

        self.ffmpeg = find_ffmpeg()
        if not self.ffmpeg:
            messagebox.showwarning("缺少 ffmpeg",
                                   "未检测到 ffmpeg，视频导出将不可用。\n请安装 ffmpeg 并加入 PATH。")

        self._build_widgets()
        self._refresh_status()

    def _build_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Button(top, text="打开文件", command=self._open_files).pack(side="left", padx=4)
        ttk.Button(top, text="打开文件夹", command=self._open_folder).pack(side="left", padx=4)
        ttk.Button(top, text="清空", command=self._clear).pack(side="left", padx=4)
        self.count_var = tk.StringVar(value="尚未导入图片")
        ttk.Label(top, textvariable=self.count_var).pack(side="right")

        left = ttk.LabelFrame(self, text="已导入图片")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=4)
        self.listbox = tk.Listbox(left)
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)

        right = ttk.Frame(self)
        right.pack(side="right", fill="y", padx=10, pady=4)

        # 公共设置
        pub = ttk.LabelFrame(right, text="公共设置")
        pub.pack(fill="x", pady=4)
        self.gap_var = tk.StringVar(value="10")
        self.bg_var = tk.StringVar(value="#000000")
        self.dur_var = tk.StringVar(value="10")
        self.fps_var = tk.StringVar(value="25")
        for label, var in (("间距(px)", self.gap_var),
                           ("背景色(#hex)", self.bg_var),
                           ("视频时长(秒)*", self.dur_var),
                           ("帧率(fps)", self.fps_var)):
            r = ttk.Frame(pub)
            r.pack(fill="x", padx=6, pady=2)
            ttk.Label(r, text=label, width=14).pack(side="left")
            ttk.Entry(r, textvariable=var, width=12).pack(side="right")
        ttk.Button(pub, text="选背景色", command=self._pick_color).pack(padx=6, pady=3)
        ttk.Label(pub, text="* 网格/滚动模式用此时长；幻灯片/KenBurns/高亮由各自参数推算",
                  foreground="#666", font=("TkDefaultFont", 8)).pack(padx=6)

        # 模式标签页
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="x", pady=4)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._update_preview())

        # 1. 网格定格
        f1 = ttk.Frame(self.notebook)
        self.notebook.add(f1, text="网格定格")
        self.cols_var = tk.StringVar(value="0")
        self.gcell_var = tk.StringVar(value="400")
        self.fit_var = tk.StringVar(value="contain")
        self._row(f1, "列数(0=自动)", self.cols_var)
        self._row(f1, "格子尺寸(px)", self.gcell_var)
        self._row_menu(f1, "缩放方式", self.fit_var, ["contain", "fill"])

        # 2. 横向滚动
        f2 = ttk.Frame(self.notebook)
        self.notebook.add(f2, text="横向滚动")
        self.hcell_var = tk.StringVar(value="500")
        self.houtw_var = tk.StringVar(value="1280")
        self.hspeed_var = tk.StringVar(value="160")
        self._row(f2, "统一高度(px)", self.hcell_var)
        self._row(f2, "视频宽度(px)", self.houtw_var)
        self._row(f2, "滚动速度(px/秒,0=自动限频)", self.hspeed_var)
        ttk.Label(f2, text="输出高=图高(含边距)；速度越小越慢越稳", foreground="#666").pack(padx=6)

        # 3. 纵向滚动
        f3 = ttk.Frame(self.notebook)
        self.notebook.add(f3, text="纵向滚动")
        self.wcell_var = tk.StringVar(value="500")
        self.vouth_var = tk.StringVar(value="720")
        self.vspeed_var = tk.StringVar(value="160")
        self._row(f3, "统一宽度(px)", self.wcell_var)
        self._row(f3, "视频高度(px)", self.vouth_var)
        self._row(f3, "滚动速度(px/秒,0=自动限频)", self.vspeed_var)
        ttk.Label(f3, text="输出宽=图宽(含边距)；速度越小越慢越稳", foreground="#666").pack(padx=6)

        # 4. 幻灯片
        f4 = ttk.Frame(self.notebook)
        self.notebook.add(f4, text="幻灯片")
        self.dwell_var = tk.StringVar(value="2.5")
        self.xfade_var = tk.StringVar(value="1.0")
        self.sw_var = tk.StringVar(value="1280")
        self.sh_var = tk.StringVar(value="720")
        self.pi_slideshow_var = tk.BooleanVar(value=False)
        self._row(f4, "停留(秒)", self.dwell_var)
        self._row(f4, "转场(秒)", self.xfade_var)
        self._row(f4, "视频宽度(px)", self.sw_var)
        self._row(f4, "视频高度(px)", self.sh_var)
        ttk.Checkbutton(f4, text="π 律动（每张秒数按 π 小数位：3,1,4,1,5,9…）",
                        variable=self.pi_slideshow_var).pack(padx=6, pady=4, anchor="w")

        # 5. KenBurns
        f5 = ttk.Frame(self.notebook)
        self.notebook.add(f5, text="KenBurns")
        self.kdwell_var = tk.StringVar(value="3.0")
        self.kxfade_var = tk.StringVar(value="1.0")
        self.kw_var = tk.StringVar(value="1280")
        self.kh_var = tk.StringVar(value="720")
        self.pi_kenburns_var = tk.BooleanVar(value=False)
        self._row(f5, "停留(秒)", self.kdwell_var)
        self._row(f5, "转场(秒)", self.kxfade_var)
        self._row(f5, "视频宽度(px)", self.kw_var)
        self._row(f5, "视频高度(px)", self.kh_var)
        ttk.Label(f5, text="放大系数固定 1.12，缓慢平移", foreground="#666").pack(padx=6)
        ttk.Checkbutton(f5, text="π 律动（每张秒数按 π 小数位：3,1,4,1,5,9…）",
                        variable=self.pi_kenburns_var).pack(padx=6, pady=4, anchor="w")

        # 6. 逐张高亮
        f6 = ttk.Frame(self.notebook)
        self.notebook.add(f6, text="逐张高亮")
        self.hlcell_var = tk.StringVar(value="400")
        self.hlstep_var = tk.StringVar(value="0.8")
        self.hlw_var = tk.StringVar(value="1280")
        self.hlh_var = tk.StringVar(value="720")
        self._row(f6, "格子尺寸(px)", self.hlcell_var)
        self._row(f6, "每格间隔(秒)", self.hlstep_var)
        self._row(f6, "视频宽度(px)", self.hlw_var)
        self._row(f6, "视频高度(px)", self.hlh_var)
        ttk.Label(f6, text="列数自动；间距/背景色取公共设置", foreground="#666").pack(padx=6)

        ttk.Button(right, text="刷新预览", command=self._update_preview).pack(fill="x", padx=6, pady=4)

        prevf = ttk.LabelFrame(right, text="预览（素材概览）")
        prevf.pack(fill="x", pady=4)
        self.preview_label = ttk.Label(prevf)
        self.preview_label.pack(padx=6, pady=6)

        # 导出 + 进度条
        genf = ttk.LabelFrame(right, text="导出")
        genf.pack(fill="x", pady=4)
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(genf, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=6, pady=(6, 2))
        self.progress_label = ttk.Label(genf, text="进度：0%")
        self.progress_label.pack(fill="x", padx=6, pady=(0, 2))
        ttk.Button(genf, text="生成视频…", command=self._generate).pack(fill="x", padx=6, pady=(2, 6))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self, textvariable=self.status_var, relief="sunken").pack(
            side="bottom", fill="x", padx=10, pady=4)

    def _row(self, parent, label, var):
        r = ttk.Frame(parent)
        r.pack(fill="x", padx=6, pady=2)
        ttk.Label(r, text=label, width=16).pack(side="left")
        ttk.Entry(r, textvariable=var, width=12).pack(side="right")

    def _row_menu(self, parent, label, var, opts):
        r = ttk.Frame(parent)
        r.pack(fill="x", padx=6, pady=2)
        ttk.Label(r, text=label, width=16).pack(side="left")
        ttk.OptionMenu(r, var, opts[0], *opts).pack(side="right")

    # ---- 交互 ----
    def _open_files(self):
        paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp *.webp *.gif *.tif *.tiff"),
                       ("所有文件", "*.*")])
        if paths:
            self._add_images(list(paths))

    def _open_folder(self):
        d = filedialog.askdirectory(title="选择图片文件夹")
        if d:
            self._add_images([d])

    def _add_images(self, paths):
        valid, skipped = load_images(self.image_paths + list(paths))
        self.image_paths = valid
        self.listbox.delete(0, tk.END)
        for p in valid:
            self.listbox.insert(tk.END, os.path.basename(p))
        self._refresh_status()
        self._update_preview()
        if skipped:
            messagebox.showinfo("已跳过", f"跳过了 {len(skipped)} 个非图片文件")

    def _clear(self):
        self.image_paths = []
        self.listbox.delete(0, tk.END)
        self.preview_label.configure(image="")
        self._refresh_status()

    def _pick_color(self):
        c = colorchooser.askcolor(initialcolor=self.bg_var.get())
        if c and c[1]:
            self.bg_var.set(c[1])
            self._update_preview()

    def _refresh_status(self):
        self.count_var.set(f"共 {len(self.image_paths)} 张图片")
        if self.ffmpeg:
            self.status_var.set(f"ffmpeg: {os.path.basename(self.ffmpeg)} | 就绪")
        else:
            self.status_var.set("警告：未检测到 ffmpeg，无法导出视频")

    def _read_common(self):
        gap = max(0, int(self.gap_var.get() or 10))
        dur = max(1, float(self.dur_var.get() or 10))
        fps = max(1, int(self.fps_var.get() or 25))
        return gap, dur, fps

    # ---- 命令构造 ----
    def _build_command(self, out):
        gap, dur, fps = self._read_common()
        bg = self.bg_var.get()
        mode = self.MODES[self.notebook.index("current")]
        ff = self.ffmpeg

        if mode == "grid":
            cols = int(self.cols_var.get() or 0)
            cell = max(32, int(self.gcell_var.get() or 400))
            img = make_grid_image(self.image_paths, cols=cols, cell=cell, gap=gap, bg=bg,
                                   fit=self.fit_var.get())
            return self._cmd_static(img, "grid", dur, fps, None, None, out), dur, []

        if mode == "h":
            cell = max(32, int(self.hcell_var.get() or 500))
            ow = even(int(self.houtw_var.get() or 1280))
            img = make_strip_image(self.image_paths, "h", cell, gap, bg)
            iw, ih = img.size
            travel = max(0, iw - ow)
            dur_h = self._scroll_duration(travel, self.hspeed_var, dur)
            return self._cmd_static(img, "h", dur_h, fps, ow, None, out), dur_h, []

        if mode == "v":
            cell = max(32, int(self.wcell_var.get() or 500))
            oh = even(int(self.vouth_var.get() or 720))
            img = make_strip_image(self.image_paths, "v", cell, gap, bg)
            iw, ih = img.size
            travel = max(0, ih - oh)
            dur_v = self._scroll_duration(travel, self.vspeed_var, dur)
            return self._cmd_static(img, "v", dur_v, fps, None, oh, out), dur_v, []

        if mode in ("slideshow", "kenburns"):
            raise RuntimeError("slideshow/kenburns 由 _render_slideshow 处理")

        # highlight
        cell = max(32, int(self.hlcell_var.get() or 400))
        step = max(0.2, float(self.hlstep_var.get() or 0.8))
        W = even(int(self.hlw_var.get() or 1280))
        H = even(int(self.hlh_var.get() or 720))
        grid_path, subpaths, layout, tmpdir = make_highlight_assets(
            self.image_paths, cols=0, cell=cell, gap=gap, bg=bg)
        cmd, total = self._cmd_highlight(grid_path, subpaths, layout, cell, step, fps, W, H, out)
        return cmd, total, [tmpdir]

    def _scroll_duration(self, travel, speed_var, fallback_dur):
        if travel <= 0:
            return fallback_dur
        try:
            speed = float(speed_var.get() or 0)
        except Exception:
            speed = 0.0
        if speed > 0:
            return max(1.0, travel / speed)
        SAFE_MAX = 300.0
        return max(fallback_dur, travel / SAFE_MAX)

    def _cmd_static(self, img, mode, duration, fps, ow, oh, out):
        tmp = out + ".tmp.png"
        img.save(tmp, "PNG")
        iw, ih = img.size
        if mode == "grid":
            vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1"
        elif mode == "h":
            ow = even(ow or 1280)
            oh = even(ih)
            if iw > ow:
                S = 2 if iw <= 8000 else 1
                vf = (f"scale={iw * S}:{ih * S},"
                      f"crop={ow * S}:{ih * S}:x='({iw * S}-{ow * S})*t/{duration}':y=0,"
                      f"scale={ow}:{oh},setsar=1")
            else:
                vf = f"scale={ow}:-1,scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1"
        else:  # v
            oh = even(oh or 720)
            ow2 = even(iw)
            if ih > oh:
                S = 2 if ih <= 8000 else 1
                vf = (f"scale={iw * S}:{ih * S},"
                      f"crop={iw * S}:{oh * S}:x=0:y='({ih * S}-{oh * S})*t/{duration}',"
                      f"scale={ow2}:{oh},setsar=1")
            else:
                vf = f"scale=-1:{oh},scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1"
        return [self.ffmpeg, "-loop", "1", "-i", tmp, "-t", str(duration),
                "-r", str(fps), "-vf", vf, "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]

    def _render_slideshow(self, imgs, mode, dwell, xfade, fps, W, H, out, progress_cb,
                          pi_rhythm=False):
        """幻灯片 / KenBurns：两遍法 xfade 链交叉淡入淡出。"""
        N = len(imgs)
        fps = max(1, int(fps))

        if pi_rhythm:
            seg_durs = [max(0.2, round(float(pi_duration(i)) * fps) / fps)
                        for i in range(N)]
        else:
            base = max(0.2, round(float(dwell) * fps) / fps)
            seg_durs = [base] * N

        T = max(0.1, min(float(xfade), min(seg_durs) * 0.9))
        T = round(T * fps) / fps

        tmpdir = tempfile.mkdtemp(prefix="pv_sl_")
        try:
            seg_files = []
            for i, p in enumerate(imgs):
                seg = os.path.join(tmpdir, f"seg_{i:04d}.mp4")
                seg_files.append(seg)
                sd = seg_durs[i]
                if mode == "kenburns":
                    # cover 缩放：按图片宽高比放大到 1.12 倍，确保缩放后
                    # 尺寸 >= W*1.12 x H*1.12，crop 永不越界（宽/扁图也可编码）。
                    try:
                        with Image.open(p) as _im:
                            _iw, _ih = _im.size
                    except Exception:
                        _iw, _ih = W, H
                    if _iw / _ih > W / H:
                        sw, sh = -1, int(H * 1.12)
                    else:
                        sw, sh = int(W * 1.12), -1
                    vf = (f"scale={sw}:{sh},"
                          f"crop={W}:{H}:x='(iw-{W})*t/{sd}':y='(ih-{H})*t/{sd}',"
                          f"setsar=1")
                else:
                    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1")
                seg_cmd = [self.ffmpeg, "-y", "-loop", "1", "-t", str(sd), "-i", p,
                           "-vf", vf, "-r", str(fps), "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", seg]
                try:
                    r = subprocess.run(seg_cmd, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, timeout=600)
                except subprocess.TimeoutExpired:
                    raise RuntimeError(f"第 {i + 1}/{N} 张编码超时（疑似卡死，已终止）")
                if r.returncode != 0:
                    raise RuntimeError(f"第 {i + 1}/{N} 张编码失败 (ffmpeg 退出 {r.returncode})")
                if progress_cb:
                    progress_cb((i + 1) / N * 0.8)

            if N == 1:
                total = seg_durs[0]
                fade_d = min(0.5, total / 2)
                fc = [f"[0]fade=t=in:d={fade_d:.3f},"
                      f"fade=t=out:st={total - fade_d:.3f}:d={fade_d:.3f}[outv]"]
            else:
                total = sum(seg_durs) - (N - 1) * T
                fc = []
                cum = 0.0
                for i in range(1, N):
                    cum += seg_durs[i - 1] - T
                    off = round(cum * fps) / fps
                    if i == 1:
                        fc.append(f"[0][1]xfade=transition=fade:duration={T:.3f}:"
                                  f"offset={off:.3f}[x1]")
                        prev = "x1"
                    else:
                        fc.append(f"[{prev}][{i}]xfade=transition=fade:duration={T:.3f}:"
                                  f"offset={off:.3f}[x{i}]")
                        prev = f"x{i}"
                fade_d = min(0.5, total / 2)
                fc.append(f"[{prev}]fade=t=in:d={fade_d:.3f},"
                          f"fade=t=out:st={total - fade_d:.3f}:d={fade_d:.3f}[outv]")

            cmd = []
            for s in seg_files:
                cmd += ["-i", s]
            cmd += ["-filter_complex", ";".join(fc), "-map", "[outv]",
                    "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", out]

            def cb(frac):
                if progress_cb:
                    progress_cb(0.8 + frac * 0.2)

            run_ffmpeg_with_progress(cmd, total, cb, self.ffmpeg, fps=fps)
            if progress_cb:
                progress_cb(1.0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _cmd_highlight(self, grid_path, subpaths, layout, cell, step, fps, W, H, out):
        N = len(subpaths)
        total = N * step
        cw = ch = cell
        zcw = int(cw * 1.08)
        zch = int(ch * 1.08)
        border = 8
        cmd = [self.ffmpeg, "-loop", "1", "-t", str(total), "-i", grid_path]
        for sp in subpaths:
            cmd += ["-loop", "1", "-t", str(total), "-i", sp]
        fc = ["[0:v]format=rgba[base]"]
        prev = "base"
        for k in range(N):
            X, Y = layout[k]
            tk = k * step
            fc.append(f"[{k+1}:v]scale={zcw}:-1,"
                      f"pad={zcw+border*2}:{zch+border*2}:(ow-iw)/2:(oh-ih)/2:color=white@1,"
                      f"format=rgba,fade=t=in:st={tk}:d=0.4[s{k}]")
            fc.append(f"[{prev}][s{k}]overlay=x={X-border}:y={Y-border}:"
                      f"enable='gte(t,{tk:.3f})'[b{k}]")
            prev = f"b{k}"
        fc.append(f"[{prev}]scale={W}:{H}:force_original_aspect_ratio=decrease,"
                  f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1[outv]")
        cmd += ["-filter_complex", ";".join(fc), "-map", "[outv]",
                "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", out]
        return cmd, total

    # ---- 预览 ----
    def _update_preview(self):
        if not self.image_paths:
            return
        try:
            gap, _, _ = self._read_common()
            bg = self.bg_var.get()
            mode = self.MODES[self.notebook.index("current")]
            if mode == "grid":
                img = make_grid_image(self.image_paths, cols=int(self.cols_var.get() or 0),
                                      cell=max(32, int(self.gcell_var.get() or 400)),
                                      gap=gap, bg=bg, fit=self.fit_var.get())
            elif mode == "h":
                img = make_strip_image(self.image_paths, "h",
                                       max(32, int(self.hcell_var.get() or 500)), gap, bg)
            elif mode == "v":
                img = make_strip_image(self.image_paths, "v",
                                       max(32, int(self.wcell_var.get() or 500)), gap, bg)
            else:
                img = make_grid_image(self.image_paths, cols=0, cell=300, gap=gap, bg=bg)
        except Exception as e:
            messagebox.showerror("预览失败", str(e))
            return
        max_box = 460
        scale = min(max_box / img.width, max_box / img.height, 1.0)
        self.preview_img = ImageTk.PhotoImage(img.resize(
            (max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS))
        self.preview_label.configure(image=self.preview_img)
        self.status_var.set(f"预览: {img.width}x{img.height} px, {len(self.image_paths)} 张")

    # ---- 生成 ----
    def _generate(self):
        if not self.image_paths:
            messagebox.showwarning("无图片", "请先导入图片")
            return
        if not self.ffmpeg:
            messagebox.showerror("缺少 ffmpeg", "未检测到 ffmpeg，无法导出视频")
            return
        tab = self.notebook.index("current")
        mode = self.MODES[tab]
        out = filedialog.asksaveasfilename(
            title="保存视频", defaultextension=".mp4",
            initialfile=self.NAMES[tab], filetypes=[("MP4", "*.mp4")])
        if not out:
            return
        gap, dur, fps = self._read_common()
        bg = self.bg_var.get()

        def progress_cb(frac):
            v = int(min(1.0, max(0.0, frac)) * 100)
            self.after(0, self.progress_var.set, v)
            self.after(0, lambda: self.progress_label.config(text=f"进度：{v}%"))

        def worker():
            try:
                if mode in ("slideshow", "kenburns"):
                    if mode == "slideshow":
                        dwell = max(0.2, float(self.dwell_var.get() or 2.5))
                        xfade = max(0.1, float(self.xfade_var.get() or 1.0))
                        W = even(int(self.sw_var.get() or 1280))
                        H = even(int(self.sh_var.get() or 720))
                        pi_rhythm = self.pi_slideshow_var.get()
                    else:
                        dwell = max(0.2, float(self.kdwell_var.get() or 3.0))
                        xfade = max(0.1, float(self.kxfade_var.get() or 1.0))
                        W = even(int(self.kw_var.get() or 1280))
                        H = even(int(self.kh_var.get() or 720))
                        pi_rhythm = self.pi_kenburns_var.get()
                    self._render_slideshow(self.image_paths, mode, dwell, xfade,
                                           fps, W, H, out, progress_cb,
                                           pi_rhythm=pi_rhythm)
                else:
                    cmd, total, tmps = self._build_command(out)
                    try:
                        run_ffmpeg_with_progress(cmd, total, progress_cb, self.ffmpeg, fps=fps)
                    finally:
                        for t in tmps:
                            if os.path.isdir(t):
                                shutil.rmtree(t, ignore_errors=True)
                            elif os.path.isfile(t):
                                try:
                                    os.remove(t)
                                except OSError:
                                    pass
                size = os.path.getsize(out)
                self.after(0, self.progress_var.set, 100)
                self.after(0, lambda: self.progress_label.config(text="进度：100%"))
                self.after(0, lambda: messagebox.showinfo(
                    "完成", f"已生成视频：\n{out}\n大小：{size/1024/1024:.2f} MB"))
                self.after(0, lambda: self.status_var.set(f"完成：{os.path.basename(out)}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("导出失败", str(e)))
                self.after(0, lambda: self.status_var.set("导出失败"))

        threading.Thread(target=worker, daemon=True).start()
        self.status_var.set("正在导出视频（后台处理中）…")
