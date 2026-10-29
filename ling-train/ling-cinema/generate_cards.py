# -*- coding: utf-8 -*-
"""生成 13 张复古棕褐胶片质感分镜卡 (1920x1080)。"""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUT_DIR, exist_ok=True)
W, H = 1920, 1080

FONT_TITLE = "C:/Windows/Fonts/simhei.ttf"        # 黑体（粗，标题）
FONT_BODY  = "C:/Windows/Fonts/msyh.ttc"          # 微软雅黑（正文）

random.seed(20250714)

def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)

def vgrad(size, top, bottom):
    w, h = size
    base = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(base)
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0]*(1-t) + bottom[0]*t)
        g = int(top[1]*(1-t) + bottom[1]*t)
        b = int(top[2]*(1-t) + bottom[2]*t)
        d.line([(0, y), (0, y)], fill=(r, g, b))
    return base.resize((w, h))

def vignette_mask(size, inner=0.55, outer=1.0):
    w, h = 256, 144
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    cx, cy = w/2, h/2
    rx, ry = w/2, h/2
    for y in range(h):
        for x in range(w):
            dx = (x-cx)/rx; dy = (y-cy)/ry
            dist = math.sqrt(dx*dx + dy*dy)
            v = max(0.0, min(1.0, (dist - inner)/(outer - inner)))
            d.point((x, y), fill=int(v*255))
    return m.resize((size[0], size[1]), Image.BILINEAR)

def add_vignette(img):
    mask = vignette_mask((W, H))
    black = Image.new("RGB", (W, H), (8, 5, 3))
    return Image.composite(black, img, mask)

def add_grain(img, amount=0.07):
    noise = Image.effect_noise((W, H), 24).convert("RGB")
    return Image.blend(img, noise, amount)

def add_scratches(img, n=10):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(n):
        x = random.randint(0, W-1)
        y0 = random.randint(0, H//4)
        y1 = random.randint(H*3//4, H)
        a = random.randint(18, 55)
        wdt = random.choice([1, 1, 2])
        d.line([(x + random.randint(-3,3), y0), (x, y1)],
               fill=(230, 220, 200, a), width=wdt)
    # 偶尔几条横向划痕
    for _ in range(2):
        y = random.randint(0, H-1)
        d.line([(0, y), (W, y)], fill=(235,225,205, random.randint(10,30)), width=1)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def wrap_text(text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append(""); continue
        cur = ""
        for ch in para:
            test = cur + ch
            if fnt.getlength(test) <= max_w:
                cur = test
            else:
                lines.append(cur); cur = ch
        lines.append(cur)
    return lines

def draw_centered(d, text, fnt, cx, y, fill, max_w=None, line_h=None, anchor="mm"):
    if max_w is None:
        d.text((cx, y), text, font=fnt, fill=fill, anchor=anchor, align="center")
        return fnt.size
    lines = wrap_text(text, fnt, max_w)
    lh = line_h or int(fnt.size * 1.28)
    total = lh * len(lines)
    yy = y - total/2
    for ln in lines:
        d.text((cx, yy + lh/2), ln, font=fnt, fill=fill, anchor="mm", align="center")
        yy += lh
    return total

def frame_border(img):
    """胶片暗角边框 + 内侧装饰线。"""
    d = ImageDraw.Draw(img)
    # 外侧暗边
    d.rectangle([0,0,W-1,H-1], outline=(20,14,9), width=18)
    # 内侧米黄细线
    d.rectangle([40,40,W-41,H-41], outline=(190,170,130), width=2)
    d.rectangle([50,50,W-51,H-51], outline=(120,95,60), width=1)
    return img

# 分镜内容
SCENES = [
    dict(kicker="分镜 01 · 开场认知反转", title=["你以为的世界第一部电影", "其实，迟到了"],
         body=["卢米埃尔《火车进站》——被写进教科书的开端", "可它没赶上 1895 那场首映"],
         accent=["世界第一部电影？", "却没赶上首映"], quote=None, quote_src=None),
    dict(kicker="分镜 02 · 人类第一次买票", title=["1 法郎", "第一次为「会动的影像」付费"],
         body=["1895.12.28  巴黎·卡普辛大道14号 大咖啡馆地下室", "一天 20 场，从早 10 点放到凌晨 1 点半"],
         accent=["单日票房 2500 法郎", "购票队伍 1/4 英里"], quote=None, quote_src=None),
    dict(kicker="分镜 03 · 迟到的主角", title=["首映没有它", "编号 No.653"],
         body=["第一次公开亮相：1896 年 1 月，里昂", "1895 首映十部片单 · 本片缺席"],
         accent=["目录编号 No.653", "今最常见为 1897 重拍版"], quote=None, quote_src=None),
    dict(kicker="分镜 04 · 机器之争", title=["1 吨的箱子", "vs  9 公斤的手摇机"],
         body=["爱迪生活动电影摄影机：靠电，>1000 磅 / 453kg", "卢米埃尔 Cinématographe：手摇，不足 20 磅 / 9kg"],
         accent=[">1000 磅", "≈ 9 kg"], quote=None, quote_src=None),
    dict(kicker="分镜 05 · 心脏：爪式机构", title=["灵感来自缝纫机", "46 → 16 帧/秒"],
         body=["让胶片一格格停顿曝光的抓爪机构", "拍摄·洗印·放映，一台机器全包"],
         accent=["46 帧/秒 → 16 帧/秒", "一部不到一分钟"], quote=None, quote_src=None),
    dict(kicker="分镜 06 · 影片本体", title=["50 秒 / 35mm", "1.33 : 1 · 约 17 米"],
         body=["取景地：法国南部 拉西奥塔车站", "机车考据：巴黎-里昂-地中海铁路 PLM 121 型"],
         accent=["单镜头·连续实时", "旅客多为摆拍群演"], quote=None, quote_src=None),
    dict(kicker="分镜 07 · 查证① 恐慌神话", title=["观众被吓退？", "无据的都市传说"],
         body=["学者洛伊珀丁格：既无警局报告，也无报纸报道", "当年银幕仅约 7 英尺宽，无声、带颗粒"],
         accent=["无警局报告", "无报纸报道"], quote="所谓「吓退观众」，是后人形容电影逼真的修辞。", quote_src="— 洛伊珀丁格 (Loiperdinger)"),
    dict(kicker="分镜 08 · 查证② 摆拍现场", title=["连「纪录片」", "都是摆拍的"],
         body=["站台旅客与下车者，皆为卢米埃尔安排", "被叮嘱：不要看镜头"],
         accent=["群演被要求不看镜头", "画面中有卢米埃尔家族成员"], quote="我们以为的「真实瞬间」，是精心导演的前置场景。", quote_src=None),
    dict(kicker="分镜 09 · 文学见证", title=["高尔基 1896", "火车朝你冲来——小心！"],
         body=["作家高尔基观影后写下的惊骇", "哪怕恐慌是后人添的，文字里的震撼是真的"],
         accent=["1896 · 高尔基", "「冲成一袋碎裂的皮肉与骨头」"], quote="一列火车径直朝你冲来——小心！仿佛要把你撞碎。", quote_src="— 马克西姆·高尔基 (1896)"),
    dict(kicker="分镜 10 · 修复与传承", title=["1422 部", "世界记忆名录 2005"],
         body=["卢米埃尔兄弟直接制作影片多达 1422 部", "博洛尼亚 4K 扫描复活；民间 AI 插帧至 4K/60fps"],
         accent=["1422 部", "2005 入选世界记忆名录"], quote=None, quote_src=None),
    dict(kicker="分镜 11 · 当代致敬", title=["2024 巴黎奥运", "冲出银幕的火车"],
         body=["跑酷火炬手踏入奥赛博物馆", "一列火车作为转场，冲破光影与现实的隔阂"],
         accent=["奥赛博物馆", "法国递给世界的文化名片"], quote=None, quote_src=None),
    dict(kicker="分镜 12 · 世界电影日", title=["2025 · 电影诞生", "130 周年"],
         body=["每年 12 月 28 日定为「世界电影日」", "从中国到拉西奥塔，从澳门到纽约，仍在放映"],
         accent=["12.28 世界电影日", "130 周年纪念"], quote=None, quote_src=None),
    dict(kicker="分镜 13 · 收束", title=["始于一趟", "迟到的火车"],
         body=["从 9 公斤手摇机，到今天每一块银幕", "这趟车，已经开了整整一百三十年"],
         accent=["我是灵枢", "下期，继续在光影里考古"], quote=None, quote_src=None),
]

def make_card(s, idx):
    # 底色：棕褐做旧暖调渐变
    base = vgrad((W, H), (74, 56, 38), (33, 24, 16))
    # 中心暖光
    glow = Image.new("RGB", (W, H), (0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W*0.18, H*0.12, W*0.82, H*0.88], fill=(60, 44, 28))
    base = Image.blend(base, glow, 0.35)
    d = ImageDraw.Draw(base)

    CREAM = (238, 224, 196)
    WHITE = (244, 238, 226)
    ACCENT = (214, 158, 86)   # 暖金
    DIM = (180, 160, 125)

    cx = W // 2
    ft_kick = font(FONT_BODY, 34, index=0)
    ft_title = font(FONT_TITLE, 92)
    ft_body = font(FONT_BODY, 40, index=0)
    ft_acc = font(FONT_TITLE, 56)
    ft_quote = font(FONT_BODY, 44, index=0)
    ft_src = font(FONT_BODY, 32, index=0)

    # 顶部 kicker
    d.text((cx, 110), s["kicker"], font=ft_kick, fill=DIM, anchor="mm", align="center")

    # 标题（2 行）
    ty = 300
    for i, line in enumerate(s["title"]):
        y = ty + i * 120
        # 标题描边
        d.text((cx, y), line, font=ft_title, fill=(18,12,8), anchor="mm", align="center")
        d.text((cx, y), line, font=ft_title, fill=WHITE, anchor="mm", align="center")

    # 正文
    by = 590
    for i, line in enumerate(s["body"]):
        d.text((cx, by + i*54), line, font=ft_body, fill=CREAM, anchor="mm", align="center")

    # 引文卡
    if s["quote"]:
        qy = 770
        qbox = [W*0.16, qy-60, W*0.84, qy+60]
        d.rectangle(qbox, outline=ACCENT, width=2)
        # 左侧引号竖条
        d.rectangle([W*0.16, qy-60, W*0.16+8, qy+60], fill=ACCENT)
        draw_centered(d, s["quote"], ft_quote, cx+10, qy, CREAM, max_w=W*0.62)
        if s["quote_src"]:
            d.text((cx, qy+92), s["quote_src"], font=ft_src, fill=ACCENT, anchor="mm", align="center")

    # 强调数据（双栏）
    if s["accent"]:
        ay = 940
        a = s["accent"]
        if len(a) == 2:
            d.text((W*0.30, ay), a[0], font=ft_acc, fill=ACCENT, anchor="mm", align="center")
            d.text((W*0.70, ay), a[1], font=ft_acc, fill=ACCENT, anchor="mm", align="center")
        else:
            d.text((cx, ay), "  ·  ".join(a), font=ft_acc, fill=ACCENT, anchor="mm", align="center")

    # 胶片质感
    img = add_vignette(base)
    img = add_grain(img, 0.08)
    img = add_scratches(img, n=10)
    img = frame_border(img)
    # 轻微模糊柔化，更复古
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    path = os.path.join(OUT_DIR, f"scene_{idx+1:02d}.png")
    img.save(path, "PNG")
    return path

if __name__ == "__main__":
    for i, s in enumerate(SCENES):
        p = make_card(s, i)
        print("saved", p)
    print("DONE", len(SCENES), "cards")
