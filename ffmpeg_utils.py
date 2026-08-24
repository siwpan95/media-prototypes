#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ffmpeg 子进程执行 + 双路进度解析（避免 xfade 滤镜链卡进度条）。"""

import re
import subprocess
import threading

from core import find_ffmpeg


# 预编译正则：从 stderr 统计行中提取 time=HH:MM:SS.MS
_RE_TIME = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")


def run_ffmpeg_with_progress(cmd, total_duration, progress_cb=None, ffmpeg=None,
                              fps=None):
    """执行 ffmpeg，双路进度解析。

    - stdout(-progress pipe:1)：首选，解析 out_time_ms（精确到 ms）。
    - stderr：后备，解析 time=HH:MM:SS.MS（编码期间持续输出，xfade
      滤镜链的 out_time_ms 常等到末尾才批量吐出，stderr 能补上中间进度）。
    - 若提供 fps，额外解析 frame= 行作为第三路进度源。
    """
    ffmpeg = ffmpeg or find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("未找到 ffmpeg，请安装并加入系统 PATH")
    if cmd and cmd[0] == ffmpeg:
        full = [ffmpeg, "-y", "-progress", "pipe:1"] + cmd[1:]
    else:
        full = [ffmpeg, "-y", "-progress", "pipe:1"] + list(cmd)
    proc = subprocess.Popen(full, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", bufsize=1)

    _total_frames = total_duration * fps if (fps and fps > 0
                                             and total_duration > 0) else None

    def _parse_time(line):
        """从 stderr 统计行提取 time=HH:MM:SS.MS，转为 0..1 比例。"""
        m = _RE_TIME.search(line)
        if not m:
            return None
        try:
            secs = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            return secs / total_duration if total_duration > 0 else 0.0
        except Exception:
            return None

    def _parse_frame(line):
        """从 stderr 统计行提取 frame=N，转为 0..1 比例。"""
        if _total_frames is None:
            return None
        if not line.startswith("frame="):
            return None
        try:
            rest = line[6:].strip()
            fn = int(rest.split()[0])
            return fn / _total_frames
        except Exception:
            return None

    last_frac = 0.0
    _lock = threading.Lock()

    def _report(frac):
        nonlocal last_frac
        with _lock:
            frac = min(1.0, max(0.0, frac))
            if frac > last_frac:
                last_frac = frac
        if progress_cb:
            progress_cb(frac)

    def _read_stderr():
        for line in proc.stderr:
            f = _parse_time(line) or _parse_frame(line)
            if f is not None:
                _report(f)

    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    try:
        for line in proc.stdout:
            if line.startswith("out_time_ms="):
                try:
                    ms = int(line.strip().split("=")[1])
                except Exception:
                    continue
                frac = ms / 1e6 / total_duration if total_duration > 0 else 0
                _report(frac)
    finally:
        proc.stdout.close()
        rc = proc.wait()
        stderr_thread.join(timeout=2)
        if rc != 0:
            raise RuntimeError(f"ffmpeg 退出码 {rc}")
    return True
