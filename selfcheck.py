#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""procedural-video 无头自检（不创建 tkinter 窗口）。

procedural_video.py 是单文件程序：GUI 只在 ProceduralVideoApp.__init__ 里 tk.Tk()，
模块顶层只 import tkinter / pygame(mixer)。因此可以 import 模块并直接驱动
纯算法的效果生成器、音效生成器与 AVI 写入器，全程不开窗口。

验证四件事：
  1. 13 种视觉效果都能产出 w*h*3 的 RGB 帧，非纯色；无状态效果可复现；
  2. 生命游戏按 Conway 规则演化（与自检里的参考实现逐格比对）；
  3. 未压缩 AVI 写入器可往返解析：RIFF/avih 头、帧数、idx1 索引、BGR 底向上像素；
  4. 13 种音效都产出合法 16 位 PCM（长度/类型/非全零/时间推进），且与效果表一一对应。

用法：python selfcheck.py
退出码：0 成功 / 1 失败。
"""

import array
import inspect
import os
import shutil
import struct
import sys
import tempfile

# 无头：禁用 pygame 的真实音频设备与启动横幅（只影响本自检进程）
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:  # 统一按 UTF-8 输出，避免 GBK 控制台把中文自检结果打成乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

import procedural_video as pv  # noqa: E402

W, H = 40, 24
DETERMINISTIC = {"EffectClouds", "EffectKaleidoscope", "EffectPlasma", "EffectPulse",
                 "EffectSwirl", "EffectTunnel", "EffectWaves"}


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def expect(cond, msg):
    if not cond:
        fail(msg)


def effect_classes():
    return {name: cls for name, cls in inspect.getmembers(pv, inspect.isclass)
            if issubclass(cls, pv.EffectBase) and cls is not pv.EffectBase}


def check_effects():
    classes = effect_classes()
    expect(len(classes) == 13, "效果类数量不是 13：%d" % len(classes))
    for name in sorted(classes):
        cls = classes[name]
        fx = cls(W, H)
        # 契约：frame_idx=0 是每种效果的首帧（有状态效果据此 reset）
        first = fx.get_frame(0.0, 0)
        second = fx.get_frame(0.3, 1)
        for tag, frame in (("首帧", first), ("次帧", second)):
            expect(isinstance(frame, bytes) and len(frame) == W * H * 3,
                   "%s %s 长度不对：%d" % (name, tag, len(frame)))
            expect(len(set(frame)) > 1, "%s %s 是纯色帧（未渲染出内容）" % (name, tag))
        if name in DETERMINISTIC:
            again = cls(W, H)
            again.get_frame(0.0, 0)
            expect(again.get_frame(0.3, 1) == second, "%s 无状态效果不可复现" % name)
    return len(classes), len(DETERMINISTIC)


def conway_step(state, w, h):
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    n += state[(y + dy) % h][(x + dx) % w]
            if state[y][x] == 1:
                out[y][x] = 1 if 2 <= n <= 3 else 0
            else:
                out[y][x] = 1 if n == 3 else 0
    return out


def check_game_of_life():
    w, h = 12, 9
    fx = pv.EffectGameOfLife(w, h)
    fx.get_frame(0.0, 0)                      # 首帧：随机初始化
    seed = [row[:] for row in fx.state]
    expected = conway_step(seed, w, h)
    frame = fx.get_frame(0.0, 1)              # 演化一代
    expect(fx.state == expected, "生命游戏演化结果与 Conway 规则不符")
    expect(any(cell for row in expected for cell in row), "生命游戏一代后全灭（初始随机不应必然全灭）")

    # 颜色映射：活 (180,255,80) / 死 (10,10,35)
    for y in range(h):
        for x in range(w):
            off = (y * w + x) * 3
            want = bytes([180, 255, 80]) if expected[y][x] else bytes([10, 10, 35])
            expect(frame[off:off + 3] == want, "生命游戏像素映射不对 @(%d,%d)" % (x, y))

    # 已知图形：「闪光灯」（横三连）应进入周期 2
    w2, h2 = 10, 10
    fx2 = pv.EffectGameOfLife(w2, h2)
    fx2.state = [[0] * w2 for _ in range(h2)]
    for x, y in [(4, 5), (5, 5), (6, 5)]:                   # blinker
        fx2.state[y][x] = 1
    s0 = [row[:] for row in fx2.state]
    fx2.get_frame(0.0, 1)
    s1 = [row[:] for row in fx2.state]
    fx2.get_frame(0.0, 2)
    s2 = [row[:] for row in fx2.state]
    expect(s1 != s0, "闪光灯第一个世代未变化")
    expect(s2 == s0, "闪光灯未按周期 2 回归")
    alive = sum(c for row in s1 for c in row)
    return len(seed) * len(seed[0]), alive


def check_avi_roundtrip():
    w, h, fps, n = 10, 6, 15, 3
    row_size = (w * 3 + 3) // 4 * 4
    frame_size = row_size * h
    tmp = tempfile.mkdtemp(prefix="pv-selfcheck-")
    path = os.path.join(tmp, "check.avi")
    frames = []
    try:
        writer = pv.AVIWriter(path, w, h, fps)
        for i in range(n):
            # 每帧一个可辨认的渐变：R = x*20+i, G = y*30, B = 7
            rgb = bytearray()
            for y in range(h):
                for x in range(w):
                    rgb.extend([x * 20 + i, y * 30, 7])
            rgb = bytes(rgb)
            frames.append(rgb)
            writer.add_frame(rgb)
        writer.close(n)

        with open(path, "rb") as f:
            blob = f.read()

        def u32(off):
            return struct.unpack_from("<I", blob, off)[0]

        # 严格按 chunk 长度字段逐块走：能走通才算写出结构合法的 AVI
        expect(blob[0:4] == b"RIFF" and blob[8:12] == b"AVI ", "AVI 缺少 RIFF/AVI 魔数")
        expect(u32(4) == len(blob) - 8, "RIFF 长度字段与文件大小不符")

        expect(blob[12:16] == b"LIST" and blob[20:24] == b"hdrl", "hdrl 列表缺失")
        hdrl_end = 12 + 8 + u32(16)
        pos = 24
        expect(blob[pos:pos + 4] == b"avih", "hdrl 里第一个块不是 avih")
        expect(u32(pos + 4) == 56, "avih 块长不是 56：%d" % u32(pos + 4))
        avih = pos + 8
        expect(u32(avih) == 1000000 // fps, "avih 的 dwMicroSecPerFrame 不对")
        expect(u32(avih + 16) == n, "avih 里的总帧数不是 %d：%d" % (n, u32(avih + 16)))
        expect(u32(avih + 32) == w and u32(avih + 36) == h, "avih 的宽高不对")
        pos = avih + 56

        expect(blob[pos:pos + 4] == b"LIST", "strl 列表缺失")
        strl_end = pos + 8 + u32(pos + 4)
        expect(blob[pos + 8:pos + 12] == b"strl", "LIST 类型不是 strl")
        p = pos + 12
        expect(blob[p:p + 4] == b"strh", "strl 里第一个块不是 strh")
        expect(u32(p + 4) == 56, "strh 块长不是 56：%d" % u32(p + 4))
        strh = p + 8
        expect(blob[strh:strh + 4] == b"vids" and blob[strh + 4:strh + 8] == b"DIB ",
               "strh 的 fccType/fccHandler 不对")
        expect(u32(strh + 20) == 1, "strh 的 dwScale 不是 1")
        expect(u32(strh + 24) == fps, "strh 的 dwRate 不等于 fps")
        expect(u32(strh + 36) == frame_size, "strh 的 dwSuggestedBufferSize 不对")
        p = strh + 56
        expect(blob[p:p + 4] == b"strf", "strh 之后不是 strf")
        expect(u32(p + 4) == 40, "strf 块长不是 40：%d" % u32(p + 4))
        strf = p + 8
        expect(u32(strf) == 40, "BITMAPINFOHEADER.biSize 不是 40")
        expect(struct.unpack_from("<ii", blob, strf + 4) == (w, h), "strf 的宽高不对")
        expect(struct.unpack_from("<HH", blob, strf + 12) == (1, 24), "strf 的 planes/bitcount 不对")
        expect(u32(strf + 16) == 0, "strf.biCompression 不是 0（未压缩）")
        expect(u32(strf + 20) == frame_size, "strf.biSizeImage 不对")
        expect(strf + 40 == strl_end, "strl 的长度字段与实际块长不符")
        expect(strl_end == hdrl_end, "hdrl 的长度字段与实际块长不符")

        expect(blob[hdrl_end:hdrl_end + 4] == b"LIST", "movi 列表缺失")
        movi_fourcc = hdrl_end + 8
        expect(blob[movi_fourcc:movi_fourcc + 4] == b"movi", "LIST 类型不是 movi")
        movi_end = movi_fourcc + u32(hdrl_end + 4)
        pos = movi_fourcc + 4
        decoded, chunk_offsets = [], []
        for _ in range(n):
            expect(blob[pos:pos + 4] == b"00dc", "movi 里不是 00dc 帧块")
            size = u32(pos + 4)
            expect(size == frame_size, "帧块大小不对：%d != %d" % (size, frame_size))
            chunk_offsets.append(pos - movi_fourcc)
            decoded.append(blob[pos + 8:pos + 8 + size])
            pos += 8 + size
        expect(pos == movi_end, "movi 的长度字段没有恰好覆盖 %d 帧" % n)

        expect(blob[pos:pos + 4] == b"idx1", "帧数据之后没有 idx1 索引")
        idx_size = u32(pos + 4)
        expect(idx_size == n * 16, "idx1 大小不对：%d" % idx_size)
        expect(pos + 8 + idx_size == len(blob), "idx1 之后还有多余字节")
        for i in range(n):
            cid, flags, off, size = struct.unpack_from("<4sIII", blob, pos + 8 + i * 16)
            expect(cid == b"00dc" and flags == 0x10 and size == frame_size,
                   "idx1 第 %d 项字段不对" % i)
            expect(off == chunk_offsets[i], "idx1 第 %d 项的偏移不对" % i)
            expect(blob[movi_fourcc + off:movi_fourcc + off + 4] == b"00dc",
                   "idx1 第 %d 项的偏移没有指向帧块" % i)
            expect(blob[movi_fourcc + off + 8:movi_fourcc + off + 8 + size] == decoded[i],
                   "idx1 第 %d 项指向的帧内容不一致" % i)

        # DIB 是底向上 + BGR，且每行按 4 字节对齐补零
        for fi in range(n):
            dib = decoded[fi]
            for y in range(h):
                base = (h - 1 - y) * row_size          # DIB 行 0 = 原图最底行
                for x in range(w):
                    off = (y * w + x) * 3
                    r, g, b = frames[fi][off:off + 3]
                    got = dib[base + x * 3:base + x * 3 + 3]
                    expect(got == bytes([b, g, r]),
                           "第 %d 帧 (%d,%d) 像素往返不对：%r" % (fi, x, y, got))
                pad = dib[base + w * 3:base + row_size]
                expect(pad == b"\x00" * (row_size - w * 3), "行尾补零不对")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return n, frame_size


def check_sounds():
    classes = effect_classes()
    expect(set(pv.SOUND_MAP) == set(classes),
           "音效映射与效果类不一一对应：缺 %r / 多 %r"
           % (sorted(set(classes) - set(pv.SOUND_MAP)), sorted(set(pv.SOUND_MAP) - set(classes))))
    n = 12000
    for name in sorted(pv.SOUND_MAP):
        gen = pv.SOUND_MAP[name]()
        samples = gen.get_samples(n)
        expect(isinstance(samples, array.array) and samples.typecode == "h",
               "%s 未返回 16 位整数数组" % name)
        expect(len(samples) == n, "%s 样本数不对：%d" % (name, len(samples)))
        expect(any(samples), "%s 产出全零静音" % name)
        expect(max(abs(s) for s in samples) <= 32767, "%s 样本超出 int16" % name)
        expect(abs(gen.t - n / gen.sample_rate) < 1e-9, "%s 的时间轴未按采样率推进" % name)
    return len(pv.SOUND_MAP), n


def main():
    n_fx, n_det = check_effects()
    cells, alive = check_game_of_life()
    n_frames, frame_size = check_avi_roundtrip()
    n_snd, n_samples = check_sounds()
    print("selfcheck ok: %d 种效果各出 %dx%d RGB 帧（%d 种无状态可复现）/ 生命游戏 %d 格按 Conway 规则演化"
          "（振荡子周期 2）/ AVI %d 帧往返（DIB 底向上 BGR + idx1 索引，帧 %d 字节）/ "
          "%d 种音效各 %d 个 16 位样本"
          % (n_fx, W, H, n_det, cells, n_frames, frame_size, n_snd, n_samples))


if __name__ == "__main__":
    main()
