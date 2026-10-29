#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拼图合成函数：网格拼贴、长条拼接、高亮素材准备。"""

import os
import math
import tempfile

from PIL import Image

from core import parse_color


def make_grid_image(image_paths, cols=0, cell=400, gap=10, bg="#000000",
                    fit="contain"):
    """多图拼成网格大图。"""
    if not image_paths:
        raise ValueError("没有图片可拼贴")
    n = len(image_paths)
    cols = max(1, min(cols or math.ceil(math.sqrt(n)), n))
    rows = math.ceil(n / cols)
    bg_rgb = parse_color(bg)
    canvas = Image.new("RGB", (cols * cell + (cols + 1) * gap,
                                rows * cell + (rows + 1) * gap), bg_rgb)
    thumbs = []
    for p in image_paths:
        try:
            im = Image.open(p).convert("RGBA")
        except Exception as e:
            print(f"[跳过] 无法读取 {p}: {e}")
            thumbs.append(None)
            continue
        if fit == "fill":
            thumb = im.resize((cell, cell), Image.LANCZOS)
        else:
            im.thumbnail((cell, cell), Image.LANCZOS)
            thumb = Image.new("RGBA", (cell, cell), bg_rgb + (255,))
            thumb.paste(im, ((cell - im.width) // 2, (cell - im.height) // 2), im)
        thumbs.append(thumb)
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break
            thumb = thumbs[idx]
            if thumb is not None:
                canvas.paste(thumb, (gap + c * (cell + gap), gap + r * (cell + gap)), thumb)
            idx += 1
    return canvas.convert("RGB")


def make_strip_image(image_paths, direction="h", cell=720, gap=10, bg="#000000"):
    """拼成横向/纵向长条图。"""
    if not image_paths:
        raise ValueError("没有图片可拼贴")
    bg_rgb = parse_color(bg)
    thumbs = []
    for p in image_paths:
        try:
            im = Image.open(p).convert("RGBA")
        except Exception as e:
            print(f"[跳过] 无法读取 {p}: {e}")
            continue
        if direction == "h":
            ratio = (cell / im.height) if im.height else 1
            thumbs.append(im.resize((max(1, int(round(im.width * ratio))), cell), Image.LANCZOS))
        else:
            ratio = (cell / im.width) if im.width else 1
            thumbs.append(im.resize((cell, max(1, int(round(im.height * ratio)))), Image.LANCZOS))
    if not thumbs:
        raise ValueError("没有有效图片可拼贴")
    if direction == "h":
        total_w = sum(t.width for t in thumbs) + gap * (len(thumbs) + 1)
        canvas = Image.new("RGB", (total_w, cell + 2 * gap), bg_rgb)
        x = gap
        for t in thumbs:
            canvas.paste(t, (x, gap), t)
            x += t.width + gap
    else:
        total_h = sum(t.height for t in thumbs) + gap * (len(thumbs) + 1)
        canvas = Image.new("RGB", (cell + 2 * gap, total_h), bg_rgb)
        y = gap
        for t in thumbs:
            canvas.paste(t, (gap, y), t)
            y += t.height + gap
    return canvas.convert("RGB")


def make_highlight_assets(image_paths, cols=0, cell=400, gap=10, bg="#000000"):
    """为「逐张高亮」模式准备素材。

    返回：
      - grid_path  网格底图路径
      - subpaths   每张图的透明前景路径列表
      - layout     每格左上角坐标列表 [(X,Y), ...]
      - tmpdir     临时目录（调用方负责清理）
    """
    if not image_paths:
        raise ValueError("没有图片可拼贴")
    n = len(image_paths)
    cols = max(1, min(cols or math.ceil(math.sqrt(n)), n))
    rows = math.ceil(n / cols)
    bg_rgb = parse_color(bg)
    grid_w = cols * cell + (cols + 1) * gap
    grid_h = rows * cell + (rows + 1) * gap
    canvas = Image.new("RGB", (grid_w, grid_h), bg_rgb)
    layout, subpaths = [], []
    tmpdir = tempfile.mkdtemp(prefix="pv_hl_")
    for idx, p in enumerate(image_paths):
        r, c = divmod(idx, cols)
        X = gap + c * (cell + gap)
        Y = gap + r * (cell + gap)
        layout.append((X, Y))
        try:
            im = Image.open(p).convert("RGBA")
            im.thumbnail((cell, cell), Image.LANCZOS)
        except Exception as e:
            print(f"[跳过] 无法读取 {p}: {e}")
            im = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        sub = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        sub.paste(im, ((cell - im.width) // 2, (cell - im.height) // 2), im)
        sp = os.path.join(tmpdir, f"sub_{idx:04d}.png")
        sub.save(sp)
        subpaths.append(sp)
        canvas.paste(sub, (X, Y), sub)
    grid_path = os.path.join(tmpdir, "grid.png")
    canvas.save(grid_path)
    return grid_path, subpaths, layout, tmpdir
