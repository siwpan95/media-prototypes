#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""常量、π 律动、通用工具函数。"""

import os
import math
import shutil

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tif", ".tiff"}

# π 前 200 位（足够任意幻灯片使用）
_PI_DIGITS = [int(c) for c in (
    "31415926535897932384626433832795028841971693993751058209749445"
    "92307816406286208998628034825342117067982148086513282306647093"
    "84460955058223172535940812848111745028410270193852110555964462"
    "2948954930381964428810975"
)]


def pi_duration(index: int) -> int:
    """第 index 张图的秒数 = π 的第 index 位（0 → 1 秒保底）。"""
    d = _PI_DIGITS[index % len(_PI_DIGITS)]
    return max(1, d)


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def even(x):
    """向上取到偶数（yuv420p 要求输出宽高偶数）。"""
    return max(2, (int(x) // 2) * 2)


def find_ffmpeg():
    """在 PATH 和常见 Windows 目录探测 ffmpeg。"""
    p = shutil.which("ffmpeg")
    if p:
        return p
    for c in (r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"):
        if os.path.isfile(c):
            return c
    return None


def load_images(paths):
    """从文件/文件夹路径中加载图片路径，去重并跳过非图片文件。"""
    valid, seen, skipped = [], set(), []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTS:
                    fp = os.path.join(p, f)
                    if fp not in seen:
                        seen.add(fp)
                        valid.append(fp)
        elif os.path.isfile(p):
            ext = os.path.splitext(p)[1].lower()
            if ext in IMAGE_EXTS:
                if p not in seen:
                    seen.add(p)
                    valid.append(p)
            else:
                skipped.append(p)
    return valid, skipped


def parse_color(bg):
    """解析颜色：hex 字符串、RGB 元组 → (R, G, B)。"""
    if isinstance(bg, (tuple, list)) and len(bg) >= 3:
        return (int(bg[0]), int(bg[1]), int(bg[2]))
    try:
        s = str(bg).lstrip("#").strip()
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (0, 0, 0)
