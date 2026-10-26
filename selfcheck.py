#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""photovideo（图片转视频生成器）无头自检。

只导入无窗口的纯逻辑层：core（π 律动时长 / 尺寸对齐 / 颜色 / 图片收集）与
compositors（网格拼贴 / 长条拼接 / 高亮素材），不导入 app.main / main（Tkinter GUI），
也不调用需要 ffmpeg 的视频合成路径。

验证点：
  1. π 律动算法：第 i 张图时长 = π 第 i 位数字（0 保底 1 秒），前 32 位与标准值逐位
     一致，且超出位数后按周期取模；
  2. 工具函数：even() 向上取偶且下限 2、parse_color() 支持 hex/短 hex/RGB 元组并
     对非法输入回退黑色、load_images() 去重并按扩展名过滤；
  3. 拼图算法结果：make_grid_image 画布尺寸 = cols*cell + (cols+1)*gap，每格中心
     像素等于对应源图颜色、缝隙填背景色；make_strip_image 长条尺寸与每格位置正确；
     make_highlight_assets 的 layout 网格坐标与输出素材（grid + 每张前景）齐全。

只读写系统临时目录，不落盘到项目；Pillow 已在 requirements.txt 中，不新增依赖。
"""
import os
import shutil
import sys
import tempfile
import time
import traceback

PI_DECIMALS_32 = "31415926535897932384626433832795"


def _setup_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def run_checks():
    from PIL import Image

    import core
    import compositors

    checks = []

    # --- 1. π 律动时长 -------------------------------------------------------
    expected = [max(1, int(ch)) for ch in PI_DECIMALS_32]
    actual = [core.pi_duration(i) for i in range(len(PI_DECIMALS_32))]
    if actual != expected:
        raise AssertionError(f"π 前 32 位时长不符: {actual} != {expected}")
    if core.pi_duration(0) != 3:
        raise AssertionError(f"首图时长应为 π 首位 3: {core.pi_duration(0)}")
    period = len(core._PI_DIGITS)  # 周期取自身表长
    if not all(1 <= core.pi_duration(i) <= 9 for i in range(period)):
        raise AssertionError("π 时长越界（应在 1..9 秒）")
    if core.pi_duration(period) != core.pi_duration(0) or core.pi_duration(period + 5) != core.pi_duration(5):
        raise AssertionError("π 位数用尽后未按周期回绕")
    checks.append(f"π 律动：前 32 张时长 {actual[:8]}... 与 π 小数逐位一致，回绕正常")

    # --- 2. 工具函数 ---------------------------------------------------------
    if (core.even(101), core.even(100), core.even(0), core.even(3.9)) != (100, 100, 2, 2):
        raise AssertionError(f"even() 错误: {core.even(101)}, {core.even(100)}, {core.even(0)}, {core.even(3.9)}")
    if any(core.even(n) % 2 for n in (1, 3, 7, 999)):
        raise AssertionError("even() 未返回偶数")
    if core.parse_color("#ff0000") != (255, 0, 0):
        raise AssertionError("parse_color 六位 hex 错误")
    if core.parse_color("0f0") != (0, 255, 0):
        raise AssertionError("parse_color 三位 hex 错误")
    if core.parse_color((10, 20, 30)) != (10, 20, 30) or core.parse_color([1, 2, 3]) != (1, 2, 3):
        raise AssertionError("parse_color 元组/列表错误")
    if core.parse_color("not-a-color") != (0, 0, 0):
        raise AssertionError("parse_color 非法输入未回退黑色")

    tmpdir = tempfile.mkdtemp(prefix="photovideo_selfcheck_")
    try:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        names = ["00_red.png", "01_green.png", "02_blue.png", "03_yellow.png"]
        for name, color in zip(names, colors):
            Image.new("RGB", (40, 40), color).save(os.path.join(tmpdir, name))
        with open(os.path.join(tmpdir, "note.txt"), "w", encoding="utf-8") as f:
            f.write("not an image")

        first = os.path.join(tmpdir, names[0])
        note = os.path.join(tmpdir, "note.txt")
        valid, skipped = core.load_images([tmpdir, first, first, note])
        if len(valid) != 4:
            raise AssertionError(f"load_images 未去重/过滤: {len(valid)} 个有效")
        if skipped != [os.path.abspath(note)]:
            raise AssertionError(f"load_images 跳过列表错误: {skipped}")
        if [os.path.basename(p) for p in valid] != names:
            raise AssertionError(f"load_images 排序/顺序错误: {[os.path.basename(p) for p in valid]}")
        checks.append(f"工具函数：even/parse_color 判定正确，load_images 去重后 {len(valid)} 张图、跳过 1 个非图片")

        # --- 3. 网格拼贴 -----------------------------------------------------
        cell, gap = 100, 10
        grid = compositors.make_grid_image(valid, cols=2, cell=cell, gap=gap, bg="#123456", fit="fill")
        if grid.size != (2 * cell + 3 * gap, 2 * cell + 3 * gap):
            raise AssertionError(f"网格画布尺寸错误: {grid.size}")
        if grid.mode != "RGB":
            raise AssertionError(f"网格输出应为 RGB: {grid.mode}")
        if grid.getpixel((0, 0)) != (0x12, 0x34, 0x56):
            raise AssertionError(f"网格背景色错误: {grid.getpixel((0, 0))}")
        for idx, color in enumerate(colors):
            row, col = divmod(idx, 2)
            cx = gap + col * (cell + gap) + cell // 2
            cy = gap + row * (cell + gap) + cell // 2
            got = grid.getpixel((cx, cy))
            if got != color:
                raise AssertionError(f"第 {idx} 格中心颜色错误: {got} != {color}")

        # --- 4. 长条拼接 -----------------------------------------------------
        strip = compositors.make_strip_image(valid, direction="h", cell=cell, gap=gap, bg="#000000")
        expected_w = len(valid) * cell + gap * (len(valid) + 1)
        if strip.size != (expected_w, cell + 2 * gap):
            raise AssertionError(f"横向长条尺寸错误: {strip.size} != {(expected_w, cell + 2 * gap)}")
        for idx, color in enumerate(colors):
            if strip.getpixel((gap + idx * (cell + gap) + cell // 2, gap + cell // 2)) != color:
                raise AssertionError(f"长条第 {idx} 格颜色错误")

        vstrip = compositors.make_strip_image(valid, direction="v", cell=cell, gap=gap, bg="#000000")
        expected_h = len(valid) * cell + gap * (len(valid) + 1)
        if vstrip.size != (cell + 2 * gap, expected_h):
            raise AssertionError(f"纵向长条尺寸错误: {vstrip.size}")

        # --- 5. 高亮素材 -----------------------------------------------------
        grid_path, subpaths, layout, hl_tmp = compositors.make_highlight_assets(
            valid, cols=2, cell=cell, gap=gap, bg="#000000")
        try:
            if len(subpaths) != len(valid) or len(layout) != len(valid):
                raise AssertionError("高亮素材数量与图片数不一致")
            expected_layout = [(gap + c * (cell + gap), gap + r * (cell + gap))
                               for r in range(2) for c in range(2)]
            if layout != expected_layout:
                raise AssertionError(f"高亮 layout 坐标错误: {layout}")
            if not os.path.isfile(grid_path) or not all(os.path.isfile(p) for p in subpaths):
                raise AssertionError("高亮素材文件缺失")
            hl_grid = Image.open(grid_path)
            if hl_grid.size != (2 * cell + 3 * gap, 2 * cell + 3 * gap):
                raise AssertionError(f"高亮底图尺寸错误: {hl_grid.size}")
            for idx, color in enumerate(colors):
                cx, cy = layout[idx][0] + cell // 2, layout[idx][1] + cell // 2
                if hl_grid.getpixel((cx, cy)) != color:
                    raise AssertionError(f"高亮底图第 {idx} 格颜色错误: {hl_grid.getpixel((cx, cy))}")
            hl_size = hl_grid.size
        finally:
            shutil.rmtree(hl_tmp, ignore_errors=True)
        checks.append(f"拼图算法：网格 {grid.size}、横/纵长条 {strip.size}/{vstrip.size} 每格取色正确，"
                      f"高亮底图 {hl_size} 与 layout 一致")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return checks


def main() -> int:
    _setup_stdout()
    started = time.time()
    try:
        checks = run_checks()
    except Exception as exc:
        print(f"selfcheck FAIL: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1

    print(f"selfcheck ok: photovideo 无头核心逻辑（{'; '.join(checks)}）"
          f" [{time.time() - started:.2f}s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
