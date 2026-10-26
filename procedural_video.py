#!/usr/bin/env python3
"""
kkrieger风格 过程生成视频生成器 + 实时预览
纯标准库，整合所有讨论效果
"""
import tkinter as tk
import struct
import math
import random
import colorsys
import threading
import wave
import array

# 尝试导入 pygame 用于音频播放
pygame = None  # type: ignore[assignment] - initialized below
_has_pygame = False
try:
    import pygame as _pygame
    _pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    pygame = _pygame
    _has_pygame = True
except Exception:
    pass
HAS_PYGAME: bool = _has_pygame

# ================== 视频参数 ==================
W, H = 320, 240          # 分辨率
FPS = 15                 # 预览帧率（AVI同步）
DURATION_PER_EFFECT = 6  # 每种效果持续时间（秒）
SAVE_AVI = False          # 是否保存 AVI 文件

# ================== AVI 工具 ==================
class AVIWriter:
    """简化的未压缩 AVI 写入器（DIB 格式）"""
    def __init__(self, filename, w, h, fps):
        self.w, self.h = w, h
        self.fps = fps
        self.row_size = (w * 3 + 3) // 4 * 4
        self.frame_size = self.row_size * h
        self.f = open(filename, 'wb')
        self.offsets = []
        self._write_header()

    def _write_header(self):
        f = self.f
        # RIFF 头（占位）
        f.write(b'RIFF\x00\x00\x00\x00AVI ')
        # hdrl 列表
        f.write(b'LIST')
        f.write(struct.pack('<I', 0)); hdrl_start = f.tell()
        f.write(b'hdrl')
        # avih 块
        f.write(b'avih')
        f.write(struct.pack('<I', 56))
        f.write(struct.pack('<IIIIIIIIIIIIII',
            1000000 // self.fps, 0, 0, 0x10, 0, 0, 1, 0,
            self.w, self.h, 0, 0, 0, 0))   # 末 4 个 DWORD 为 dwReserved（AVIMAINHEADER = 56 字节）
        # strl 列表
        f.write(b'LIST')
        f.write(struct.pack('<I', 0)); strl_start = f.tell()
        f.write(b'strl')
        f.write(b'strh')
        f.write(struct.pack('<I', 56))
        f.write(b'vids')
        f.write(b'DIB ')
        f.write(struct.pack('<IHHIIIII', 0,0,0,0, 1, self.fps, 0, 0))  # dwFlags…dwStart, dwLength
        f.write(struct.pack('<I', self.frame_size))                     # dwSuggestedBufferSize
        f.write(struct.pack('<i', -1)); f.write(struct.pack('<i', 0))
        f.write(struct.pack('<hhhh', 0,0,self.w,self.h))
        f.write(b'strf')
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<IiiHHIIiiII', 40, self.w, self.h,   # biSize 必填 40，缺了会少 4 字节
             1, 24,          # biPlanes 和 biBitCount
             0,              # biCompression
             self.frame_size,  # biSizeImage
             0, 0, 0, 0))   # biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant
        # 回填长度
        pos = f.tell(); f.seek(strl_start-4); f.write(struct.pack('<I', pos-strl_start)); f.seek(pos)
        hdrl_end = f.tell(); f.seek(hdrl_start-4); f.write(struct.pack('<I', hdrl_end-hdrl_start)); f.seek(hdrl_end)
        # movi 列表开始
        f.write(b'LIST')
        f.write(struct.pack('<I', 0)); self.movi_start = f.tell()
        f.write(b'movi')

    def add_frame(self, rgb_bytes):
        """接收 w*h*3 的 RGB 字节，转换为 DIB 帧并写入"""
        dib = bytearray()
        for y in range(self.h-1, -1, -1):
            row_start = y * self.w * 3
            row = bytearray()
            for x in range(self.w):
                off = row_start + x*3
                r, g, b = rgb_bytes[off], rgb_bytes[off+1], rgb_bytes[off+2]
                row.extend([b, g, r])          # BGR 顺序
            row += b'\x00' * (self.row_size - self.w*3)
            dib += row
        self.f.write(b'00dc')
        self.f.write(struct.pack('<I', self.frame_size))
        self.f.write(bytes(dib))
        self.offsets.append(self.f.tell())

    def close(self, total_frames):
        """完成写入，回填头部信息"""
        # 回填 movi 大小
        movi_end = self.f.tell()
        self.f.seek(self.movi_start - 4)
        self.f.write(struct.pack('<I', movi_end - self.movi_start))
        self.f.seek(movi_end)
        # idx1 索引
        self.f.write(b'idx1')
        self.f.write(struct.pack('<I', total_frames * 16))
        for off in self.offsets:
            # off 是写入帧数据后的位置，帧数据从 off - frame_size - 8 开始
            # idx1 偏移量需要相对于 movi chunk 起始位置 (self.movi_start)
            frame_offset = off - 8 - self.frame_size - self.movi_start
            self.f.write(struct.pack('<4sIII', b'00dc', 0x10, frame_offset, self.frame_size))
        # 总文件大小
        final = self.f.tell()
        self.f.seek(4)
        self.f.write(struct.pack('<I', final - 8))
        # 总帧数（在 avih 块内偏移 16）
        self.f.seek(0x30)  # 跳过 'RIFF'大小'AVI LIST'大小'hdrlavih'大小
        self.f.write(struct.pack('<I', total_frames))
        self.f.close()

# ================== 视觉效果生成器 ==================
class EffectBase:
    """所有效果的基类"""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.reset()

    def reset(self):
        """重置内部状态（用于有状态的效果）"""
        pass

    def get_frame(self, t, frame_idx):
        """返回 RGB 字节串 (w*h*3)，t 为效果内归一化时间 0..1"""
        raise NotImplementedError

class EffectPlasma(EffectBase):
    """等离子体（经典 sin 叠加）"""
    def get_frame(self, t, frame_idx):
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                u = x / self.w * 4 - 2
                v = y / self.h * 3 - 1.5
                ft = t * math.pi * 2
                val = math.sin(u*5 + ft) + math.sin(v*6 + ft*0.7)
                val += math.sin((u*1.5+v*2)*4 + ft*1.3)
                val += math.sin(math.sqrt(u*u+v*v)*8 + ft*0.5)
                val = val / 4 + 0.5
                hue = val % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
                data.extend([int(r*255), int(g*255), int(b*255)])
        return bytes(data)

class EffectClouds(EffectBase):
    """分形布朗运动（云/烟雾）"""
    def hash2d(self, x, y, seed):
        n = (x*157 + y*113 + seed*7) & 0x7fffffff
        n = (n << 13) ^ n
        return (n * (n * n * 60493 + 19990303) + 1376312589) & 0x7fffffff

    def value_noise(self, x, y, seed):
        ix, iy = int(x), int(y)
        fx, fy = x - ix, y - iy
        fx = fx*fx*(3-2*fx); fy = fy*fy*(3-2*fy)
        v00 = self.hash2d(ix, iy, seed) / 0x7fffffff
        v10 = self.hash2d(ix+1, iy, seed) / 0x7fffffff
        v01 = self.hash2d(ix, iy+1, seed) / 0x7fffffff
        v11 = self.hash2d(ix+1, iy+1, seed) / 0x7fffffff
        return (v00*(1-fx) + v10*fx)*(1-fy) + (v01*(1-fx) + v11*fx)*fy

    def fbm(self, x, y, t):
        v = 0.0; amp = 1.0; freq = 1.0; total = 0.0
        for i in range(5):
            v += amp * self.value_noise(x*freq + t*0.3*(i+1),
                                        y*freq + t*0.2*(i+1), i)
            total += amp
            freq *= 2.0; amp *= 0.5
        return v / total

    def get_frame(self, t, frame_idx):
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                nx = x / self.w * 5.0
                ny = y / self.h * 5.0
                v = self.fbm(nx, ny, t*3)
                # 冷色到暖色映射
                if v < 0.4:
                    r, g, b = 0, 0, int(128 + v/0.4*127)
                elif v < 0.6:
                    s = (v-0.4)/0.2
                    r, g, b = int(255*s), int(255*s), 255
                elif v < 0.8:
                    s = (v-0.6)/0.2
                    r, g, b = 255, int(255*(1-s)), int(255*(1-s))
                else:
                    s = (v-0.8)/0.2
                    r, g, b = 255, 255, int(255*s)
                data.extend([r, g, b])
        return bytes(data)

class EffectSwirl(EffectBase):
    """扭曲漩涡（类似 WMP 氛围）"""
    def get_frame(self, t, frame_idx):
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                u = (x/self.w - 0.5) * 2
                v = (y/self.h - 0.5) * 2
                cx, cy = 0.3*math.sin(t*4.4), 0.3*math.cos(t*3.8)
                dx, dy = u - cx, v - cy
                dist = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx) + dist*3.0 + t*7.5
                nx = dist * math.cos(angle) + cx
                ny = dist * math.sin(angle) + cy
                pattern = (math.sin(nx*10 + t*6) * math.cos(ny*10 + t*5)) * 0.5 + 0.5
                r = int(60 + 120*pattern)
                g = int(30 + 80*pattern)
                b = int(180 + 75*pattern)
                data.extend([r, g, b])
        return bytes(data)

class EffectKaleidoscope(EffectBase):
    """万花筒对称分形"""
    def get_frame(self, t, frame_idx):
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                u = x/self.w - 0.5
                v = y/self.h - 0.5
                r = math.sqrt(u*u + v*v)
                angle = math.atan2(v, u)
                sym = 5 + int(r*6) % 4
                angle = (angle * sym + t*12.5) % (2*math.pi)
                val = (math.sin(r*15 - t*18) * math.cos(angle*3)) * 0.5 + 0.5
                hue = (val + t*0.5) % 1.0
                rgb = colorsys.hsv_to_rgb(hue, 0.9, val*0.8+0.2)
                data.extend([int(c*255) for c in rgb])
        return bytes(data)

class EffectTunnel(EffectBase):
    """伪 3D 隧道飞行"""
    def get_frame(self, t, frame_idx):
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                u = (x - self.w/2) / (self.w/2)
                v = (y - self.h/2) / (self.h/2)
                dist = math.sqrt(u*u + v*v)
                angle = math.atan2(v, u)
                z = 1.0/(dist+0.1)*2.0 + t*12.0
                tex = math.sin(angle*8 + z*5) * math.cos(z*7)
                tex = (tex + 1)/2
                r = int(30 + tex*50)
                g = int(20 + tex*80)
                b = int(100 + tex*155)
                data.extend([r, g, b])
        return bytes(data)

class EffectGameOfLife(EffectBase):
    """元胞自动机 - 生命游戏"""
    state: list[list[int]] = []  # 状态矩阵：每个元素为 0 或 1

    def reset(self):
        # 随机初始化
        self.state = [[random.randint(0,1) for _ in range(self.w)] for _ in range(self.h)]

    def get_frame(self, t, frame_idx):
        if frame_idx == 0:
            self.reset()
        # 演化一代
        new = [[0]*self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                n = 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        if dx==0 and dy==0: continue
                        n += self.state[(y+dy)%self.h][(x+dx)%self.w]
                if self.state[y][x] == 1:
                    new[y][x] = 1 if 2 <= n <= 3 else 0
                else:
                    new[y][x] = 1 if n == 3 else 0
        self.state = new
        # 生成图像
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                if self.state[y][x]:
                    data.extend([180, 255, 80])   # 亮绿
                else:
                    data.extend([10, 10, 35])     # 深蓝
        return bytes(data)

class EffectParticles(EffectBase):
    """粒子旋涡"""

    def __init__(self, w: int, h: int) -> None:
        super().__init__(w, h)
        self.particles: list[tuple[float, float]] = []
        self.vels: list[tuple[float, float]] = []

    def reset(self):
        self.particles = [(random.random()*self.w, random.random()*self.h) for _ in range(200)]
        self.vels = [(random.random()*2-1, random.random()*2-1) for _ in range(200)]

    def get_frame(self, t, frame_idx):
        if frame_idx == 0:
            self.reset()
        # 引力点绕圈
        ax = self.w/2 + math.sin(t*8)*self.w/3
        ay = self.h/2 + math.cos(t*8)*self.h/3
        # 全黑背景
        canvas = bytearray([0,0,0] * (self.w * self.h))
        for i, (px, py) in enumerate(self.particles):
            vx, vy = self.vels[i]
            dx, dy = ax - px, ay - py
            dist = math.hypot(dx, dy) + 0.1
            vx += dx/dist * 0.25
            vy += dy/dist * 0.25
            vx *= 0.98; vy *= 0.98
            px += vx; py += vy
            # 边界回弹
            if px < 0 or px >= self.w: vx*=-1; px = max(0, min(px, self.w-1))
            if py < 0 or py >= self.h: vy*=-1; py = max(0, min(py, self.h-1))
            self.particles[i] = (px, py)
            self.vels[i] = (vx, vy)
            # 绘制光点
            ix, iy = int(px), int(py)
            off = (iy * self.w + ix) * 3
            if 0 <= off < len(canvas)-2:
                hue = (math.atan2(vy, vx)/math.pi + 1)/2 + t*0.3
                r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 0.9, 1.0)
                canvas[off]   = min(255, canvas[off] + int(r*180))
                canvas[off+1] = min(255, canvas[off+1] + int(g*180))
                canvas[off+2] = min(255, canvas[off+2] + int(b*180))
        return bytes(canvas)

class EffectMatrix(EffectBase):
    """黑客帝国风格字符雨"""

    def __init__(self, w: int, h: int) -> None:
        super().__init__(w, h)
        self.cols: list[list[int]] = []

    def reset(self):
        col_count = max(1, self.w // 12)
        self.cols = [[random.randint(0, self.h) for _ in range(10)] for _ in range(col_count)]

    def get_frame(self, t, frame_idx):
        if frame_idx == 0:
            self.reset()
        canvas = bytearray([0] * (self.w * self.h * 3))
        char_set = "01010101010111011100101110010111010111010001000101010000011110110111001010"
        # 更新下落
        for col in self.cols:
            if random.random() < 0.03:
                col.insert(0, 0)
                col.pop()
            else:
                col.insert(0, col[0] + 1)
                col.pop()
        # 绘制
        for i, col in enumerate(self.cols):
            x = i * 12 + 4
            if x >= self.w:
                continue
            for j, y in enumerate(col):
                if 0 <= y < self.h:
                    brightness = max(80, 255 - j * 25)
                    r = brightness // 4
                    g = brightness
                    b = 0
                    off = (y * self.w + x) * 3
                    if off + 2 < len(canvas):
                        canvas[off] = r
                        canvas[off + 1] = g
                        canvas[off + 2] = b
        return bytes(canvas)

class EffectFire(EffectBase):
    """火焰效果"""
    heat: list[list[float]]

    def __init__(self, w: int, h: int) -> None:
        super().__init__(w, h)
        self.heat = []

    def reset(self):
        self.heat = [[0.0] * self.w for _ in range(self.h)]
        # 底部热源
        for x in range(self.w):
            self.heat[self.h - 1][x] = 1.0

    def get_frame(self, t, frame_idx):
        if frame_idx == 0:
            self.reset()
        # 火焰向上传播
        new_heat = [[0.0] * self.w for _ in range(self.h)]
        for y in range(self.h - 1):
            for x in range(self.w):
                avg = self.heat[y][x]
                if x > 0:
                    avg += self.heat[y][x - 1]
                if x < self.w - 1:
                    avg += self.heat[y][x + 1]
                avg /= 3.0
                new_heat[y - 1][x] = min(1.0, avg * 1.1)
        # 底部随机火焰
        for x in range(self.w):
            if random.random() < 0.3:
                new_heat[self.h - 1][x] = 1.0
            else:
                new_heat[self.h - 1][x] = max(0, new_heat[self.h - 1][x] - 0.1)
        self.heat = new_heat
        # 渲染
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                h = self.heat[y][x]
                if h < 0.3:
                    r = int(h * 300)
                    g, b = 0, 0
                elif h < 0.6:
                    r = int(80 + (h - 0.3) * 400)
                    g = int((h - 0.3) * 200)
                    b = 0
                else:
                    r = 255
                    g = int(100 + (h - 0.6) * 200)
                    b = int((h - 0.6) * 100)
                data.extend([min(255, r), min(255, g), min(255, b)])
        return bytes(data)

class EffectWaves(EffectBase):
    """多层波浪效果"""
    def get_frame(self, t, frame_idx):
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                u = x / self.w * 2 - 1
                v = y / self.h * 2 - 1
                # 多层波浪叠加
                wave1 = math.sin(u * 8 + t * 3) * 0.3
                wave2 = math.sin(v * 6 - t * 2) * 0.3
                wave3 = math.sin((u + v) * 5 + t * 4) * 0.2
                wave4 = math.sin(math.sqrt(u*u + v*v) * 10 - t * 5) * 0.15
                val = (wave1 + wave2 + wave3 + wave4) * 0.5 + 0.5
                # 颜色映射：海洋蓝到青绿
                r = int(20 + val * 40)
                g = int(80 + val * 120)
                b = int(150 + val * 100)
                data.extend([r, g, b])
        return bytes(data)

class EffectGalaxy(EffectBase):
    """星空银河效果"""
    stars: list[tuple[float, float, float]]

    def __init__(self, w: int, h: int) -> None:
        super().__init__(w, h)
        self.stars = []

    def reset(self):
        self.stars = [(random.random() * self.w, random.random() * self.h,
                       random.random() * 3 + 0.5) for _ in range(150)]

    def get_frame(self, t, frame_idx):
        if frame_idx == 0:
            self.reset()
        canvas = bytearray([10, 5, 25] * (self.w * self.h))  # 深蓝背景
        # 绘制星星
        for i, (sx, sy, speed) in enumerate(self.stars):
            sy += speed * 0.5
            if sy >= self.h:
                sy = 0
                sx = random.random() * self.w
            self.stars[i] = (sx, sy, speed)
            # 星星闪烁
            brightness = 0.5 + 0.5 * math.sin(t * 5 + i)
            ix, iy = int(sx), int(sy)
            if 0 <= ix < self.w and 0 <= iy < self.h:
                off = (iy * self.w + ix) * 3
                canvas[off] = min(255, int(200 * brightness))
                canvas[off + 1] = min(255, int(220 * brightness))
                canvas[off + 2] = min(255, int(255 * brightness))
        # 中心光晕
        cx, cy = self.w / 2, self.h / 2
        for y in range(self.h):
            for x in range(self.w):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                glow = max(0, 1 - dist / (self.w * 0.4)) * 0.3
                off = (y * self.w + x) * 3
                canvas[off] = min(255, canvas[off] + int(100 * glow))
                canvas[off + 1] = min(255, canvas[off + 1] + int(80 * glow))
                canvas[off + 2] = min(255, canvas[off + 2] + int(200 * glow))
        return bytes(canvas)

class EffectPulse(EffectBase):
    """脉冲波效果"""
    def get_frame(self, t, frame_idx):
        data = bytearray()
        cx, cy = self.w / 2, self.h / 2
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = x - cx, y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                # 多层脉冲
                pulse1 = math.sin(dist * 0.15 - t * 4) * 0.5 + 0.5
                pulse2 = math.sin(dist * 0.08 + t * 2) * 0.5 + 0.5
                pulse3 = math.sin(dist * 0.05 - t * 1.5 + math.sin(t * 3)) * 0.5 + 0.5
                val = (pulse1 + pulse2 + pulse3) / 3
                # 颜色：紫到粉到白
                hue = (t * 0.2 + dist * 0.001) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.3 + val * 0.7)
                data.extend([int(r * 255), int(g * 255), int(b * 255)])
        return bytes(data)

class EffectRipple(EffectBase):
    """水波纹效果"""
    drops: list[tuple[float, float, float]]

    def __init__(self, w: int, h: int) -> None:
        super().__init__(w, h)
        self.drops = []

    def reset(self):
        self.drops = []

    def get_frame(self, t, frame_idx):
        # 随机添加水滴
        if random.random() < 0.1:
            self.drops.append((random.random() * self.w,
                              random.random() * self.h,
                              t))
        # 移除过期波纹
        self.drops = [(x, y, start) for x, y, start in self.drops if t - start < 3]
        data = bytearray()
        for y in range(self.h):
            for x in range(self.w):
                height = 0.0
                for dx, dy, start in self.drops:
                    dist = math.sqrt((x - dx)**2 + (y - dy)**2)
                    age = t - start
                    # 波纹半径随时间扩展
                    radius = age * 40
                    width = 8
                    if radius - width < dist < radius + width:
                        wave = math.cos((dist - radius) / width * math.pi)
                        height += wave * (1 - age / 3)
                height = max(-1.0, min(1.0, height))
                # 水面颜色（确保值在 0-255 范围内）
                if height > 0:
                    r = min(255, int(30 + height * 80))
                    g = min(255, int(100 + height * 120))
                    b = min(255, int(180 + height * 75))
                else:
                    r = max(0, int(30 + height * 30))
                    g = max(0, int(100 + height * 50))
                    b = max(0, int(180 + height * 80))
                data.extend([r, g, b])
        return bytes(data)

# ================== 音效生成器 ==================
class SoundGenerator:
    """音效生成器基类"""
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.t = 0.0

    def reset(self):
        self.t = 0.0

    def get_samples(self, num_samples):
        """生成音频样本，返回 16 位整数数组"""
        samples = []
        for _ in range(num_samples):
            samples.append(self._get_sample())
            self.t += 1.0 / self.sample_rate
        return array.array('h', samples)

    def _get_sample(self):
        """返回单个样本值 -1.0 到 1.0"""
        raise NotImplementedError

class SoundPlasma(SoundGenerator):
    """等离子体音效 - 扫描频率合成"""
    def _get_sample(self):
        freq = 100 + math.sin(self.t * 0.5) * 50
        val = math.sin(self.t * freq * math.pi * 2)
        val += math.sin(self.t * freq * 1.5 * math.pi * 2) * 0.5
        return int(val * 8000)

class SoundClouds(SoundGenerator):
    """云效果音效 - 低频噪声"""
    noise = 0.0
    def _get_sample(self):
        self.noise += 0.1
        n = math.sin(self.noise * 137) * 0.5
        val = n * math.sin(self.t * 60 * math.pi * 2)
        return int(val * 6000)

class SoundSwirl(SoundGenerator):
    """漩涡音效 - 环形调制"""
    def _get_sample(self):
        freq = 150 + math.sin(self.t * 2) * 80
        mod = math.sin(self.t * 0.3) * 50
        val = math.sin((freq + mod) * self.t * math.pi * 2)
        return int(val * 7000)

class SoundKaleidoscope(SoundGenerator):
    """万花筒音效 - 泛音合成"""
    def _get_sample(self):
        base = 200 + self.t * 10
        val = 0.0
        for i in range(1, 6):
            val += math.sin(base * i * self.t * math.pi * 2) / i
        return int(val * 5000)

class SoundTunnel(SoundGenerator):
    """隧道音效 - 低频脉冲"""
    def _get_sample(self):
        pulse = math.sin(self.t * 8) > 0.8
        freq = 80 if pulse else 40
        val = math.sin(freq * self.t * math.pi * 2)
        val *= 0.3 if pulse else 0.8
        return int(val * 8000)

class SoundGameOfLife(SoundGenerator):
    """生命游戏音效 - 随机脉冲"""
    def __init__(self):
        super().__init__()
        self.attack = 0.0
        self.last_beat = 0.0

    def _get_sample(self):
        if self.t - self.last_beat > 0.15 and random.random() < 0.03:
            self.last_beat = self.t
            self.attack = 0.5
        self.attack *= 0.95
        val = random.uniform(-1, 1) * self.attack
        return int(val * 4000)

class SoundParticles(SoundGenerator):
    """粒子音效 - 粒子轨迹音"""
    def _get_sample(self):
        freq = 300 + math.sin(self.t * 4) * 200
        val = math.sin(freq * self.t * math.pi * 2)
        val += math.sin(freq * 2 * self.t * math.pi * 2) * 0.3
        return int(val * 4000)

class SoundMatrix(SoundGenerator):
    """矩阵音效 - 数字脉冲"""
    def _get_sample(self):
        if random.random() < 0.02:
            freq = random.randint(200, 800)
            return int(math.sin(self.t * freq * math.pi * 2) * 10000)
        return 0

class SoundFire(SoundGenerator):
    """火焰音效 - 粉红噪声"""
    b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
    def _get_sample(self):
        white = random.uniform(-1, 1)
        self.b0 = 0.99886 * self.b0 + white * 0.0555179
        self.b1 = 0.99332 * self.b1 + white * 0.0750759
        self.b2 = 0.96900 * self.b2 + white * 0.1538520
        self.b3 = 0.86650 * self.b3 + white * 0.3104856
        self.b4 = 0.55000 * self.b4 + white * 0.5329522
        self.b5 = -0.7616 * self.b5 - white * 0.0168980
        pink = (self.b0 + self.b1 + self.b2 + self.b3 + self.b4 + self.b5 + self.b6 + white * 0.5362) * 0.11
        self.b6 = white * 0.115926
        return int(pink * 12000)

class SoundWaves(SoundGenerator):
    """波浪音效 - 水声合成"""
    def _get_sample(self):
        wave1 = math.sin(self.t * 100 * math.pi * 2)
        wave2 = math.sin(self.t * 103 * math.pi * 2)
        val = (wave1 + wave2) * 0.5 * 0.4
        val += random.uniform(-0.1, 0.1)
        return int(val * 8000)

class SoundGalaxy(SoundGenerator):
    """星空音效 - 空灵泛音"""
    def _get_sample(self):
        val = 0.0
        for i, f in enumerate([262, 330, 392, 523]):
            val += math.sin(f * self.t * math.pi * 2 + i * 0.5) / (i + 1)
        val *= 0.3 + 0.1 * math.sin(self.t * 0.5)
        return int(val * 6000)

class SoundPulse(SoundGenerator):
    """脉冲音效 - 电子脉冲"""
    def _get_sample(self):
        pulse = (math.sin(self.t * 20) > 0.9)
        if pulse:
            val = math.sin(self.t * 400 * math.pi * 2)
            val += math.sin(self.t * 800 * math.pi * 2) * 0.5
        else:
            val = random.uniform(-0.3, 0.3)
        return int(val * 7000)

class SoundRipple(SoundGenerator):
    """波纹音效 - 水滴泛音"""
    drops = []
    last_drop = 0.0
    def _get_sample(self):
        if self.t - self.last_drop > 0.3 and random.random() < 0.05:
            self.drops.append((self.t, random.uniform(400, 800)))
            self.last_drop = self.t
        val = 0.0
        new_drops = []
        for drop_t, freq in self.drops:
            age = self.t - drop_t
            if age < 1.0:
                env = math.exp(-age * 3)
                val += math.sin(freq * (1 + age * 2) * (self.t - drop_t) * math.pi * 2) * env
                new_drops.append((drop_t, freq))
        self.drops = new_drops
        return int(val * 6000)

# 音效生成器映射
SOUND_MAP = {
    'EffectPlasma': SoundPlasma,
    'EffectClouds': SoundClouds,
    'EffectSwirl': SoundSwirl,
    'EffectKaleidoscope': SoundKaleidoscope,
    'EffectTunnel': SoundTunnel,
    'EffectGameOfLife': SoundGameOfLife,
    'EffectParticles': SoundParticles,
    'EffectMatrix': SoundMatrix,
    'EffectFire': SoundFire,
    'EffectWaves': SoundWaves,
    'EffectGalaxy': SoundGalaxy,
    'EffectPulse': SoundPulse,
    'EffectRipple': SoundRipple,
}

# ================== 主程序 ==================
class ProceduralVideoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("过程生成视频播放器 [空格切换效果]")
        self.label = tk.Label(self.root)
        self.label.pack()

        self.effects = [
            EffectPlasma(W, H),
            EffectClouds(W, H),
            EffectSwirl(W, H),
            EffectKaleidoscope(W, H),
            EffectTunnel(W, H),
            EffectGameOfLife(W, H),
            EffectParticles(W, H),
            EffectMatrix(W, H),
            EffectFire(W, H),
            EffectWaves(W, H),
            EffectGalaxy(W, H),
            EffectPulse(W, H),
            EffectRipple(W, H)
        ]
        self.current_effect_idx = 0
        self.effect = self.effects[0]
        self.effect_start_frame = 0
        self.frame_count = 0

        # 初始化音效
        self.sound_enabled = HAS_PYGAME
        self.sound_generator = None
        self.sound_channel = None
        if self.sound_enabled:
            self._init_sound()

        # 初始化 AVI 写入器
        self.avi = None
        if SAVE_AVI:
            self.avi = AVIWriter("kkrieger_output.avi", W, H, FPS)

        # 空格键手动切换效果
        self.root.bind("<space>", self.next_effect)

        # 开始帧循环
        self.update()

    def _init_sound(self):
        """初始化音效生成器"""
        effect_name = type(self.effect).__name__
        sound_class = SOUND_MAP.get(effect_name)
        if sound_class:
            self.sound_generator = sound_class()
            self.sound_generator.reset()
            self._play_sound()

    def _play_sound(self):
        """播放音效"""
        if not self.sound_enabled or not self.sound_generator or not HAS_PYGAME:
            return
        try:
            # 生成约0.5秒的音频
            samples = self.sound_generator.get_samples(self.sound_generator.sample_rate // 2)
            # 转换为 pygame Sound 对象并播放
            _pygame = pygame  # type: ignore[assignment]
            sound = _pygame.mixer.Sound(array=_pygame.sndarray.array('h', samples))
            if self.sound_channel and self.sound_channel.get_busy():
                self.sound_channel.queue(sound)
            else:
                self.sound_channel = sound.play()
            # 继续播放
            self.root.after(100, self._play_sound)
        except Exception:
            pass

    def next_effect(self, event=None):
        self.current_effect_idx = (self.current_effect_idx + 1) % len(self.effects)
        self.effect = self.effects[self.current_effect_idx]
        self.effect.reset()
        self.effect_start_frame = self.frame_count
        print(f"切换至效果: {type(self.effect).__name__}")
        # 切换音效
        if self.sound_enabled:
            self._init_sound()

    def update(self):
        # 计算当前效果内的相对时间
        frames_in_effect = self.frame_count - self.effect_start_frame
        effect_duration_frames = FPS * DURATION_PER_EFFECT
        # 自动切换效果
        if frames_in_effect >= effect_duration_frames:
            self.next_effect()
            frames_in_effect = 0

        # 归一化时间 t (0..1)，对于无状态效果使用；有状态效果内部可能忽略 t 或用 t 影响
        t = frames_in_effect / max(1, effect_duration_frames - 1)
        # 生成 RGB 帧数据
        rgb_bytes = self.effect.get_frame(t, frames_in_effect)

        # Tkinter 显示：构建 PPM P6 数据
        ppm_header = f"P6\n{W} {H}\n255\n".encode()
        img_data = ppm_header + rgb_bytes
        photo = tk.PhotoImage(data=img_data)
        self.label.config(image=photo)
        self.label.image = photo  # type: ignore[attr-defined] - 保持引用

        # 写入 AVI
        if self.avi:
            self.avi.add_frame(rgb_bytes)

        self.frame_count += 1
        delay_ms = int(1000 / FPS)
        self.root.after(delay_ms, self.update)

    def run(self):
        self.root.mainloop()
        # 窗口关闭后，清理 AVI
        if self.avi:
            self.avi.close(self.frame_count)
            print("视频已保存至 kkrieger_output.avi")

if __name__ == "__main__":
    app = ProceduralVideoApp()
    app.run()