import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 路径随仓库走（原硬编码 WorkBuddy 旧目录，2026-08-28 修复）
BASE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(BASE, "public_domain")
AI = os.path.join(BASE, "ai_images")
OUT = os.path.join(BASE, "seg_png")
os.makedirs(OUT, exist_ok=True)

FONT = "C:/Windows/Fonts/simhei.ttf"
W, H = 1920, 1080

def get_font(size):
    return ImageFont.truetype(FONT, size)

def fit_image(img, mode):
    img = img.convert("RGB")
    iw, ih = img.size
    if mode == "cover":
        scale = max(W / iw, H / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - W) // 2
        top = (nh - H) // 2
        return img.crop((left, top, left + W, top + H))
    else:  # contain
        scale = min(W / iw, H / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), (18, 12, 9))
        left = (W - nw) // 2
        top = (H - nh) // 2
        canvas.paste(img, (left, top))
        return canvas

def tint(img, r, g, b, temp=1.0, contrast=1.08, sat=0.82):
    # multiply tint
    rchan, gchan, bchan = img.split()
    rchan = rchan.point(lambda p: min(255, int(p * r)))
    gchan = gchan.point(lambda p: min(255, int(p * g)))
    bchan = bchan.point(lambda p: min(255, int(p * b)))
    img = Image.merge("RGB", (rchan, gchan, bchan))
    # contrast + saturation
    img = ImageEnhance_Contrast(img, contrast)
    img = ImageEnhance_Color(img, sat)
    return img

def ImageEnhance_Contrast(img, f):
    from PIL import ImageEnhance
    return ImageEnhance.Contrast(img).enhance(f)

def ImageEnhance_Color(img, f):
    from PIL import ImageEnhance
    return ImageEnhance.Color(img).enhance(f)

def vignette(img, strength=0.6):
    mask = Image.new("L", (W, H), 0)
    px = mask.load()
    cx, cy = W / 2, H / 2
    maxd = math.hypot(cx, cy)
    step = 12
    for y in range(0, H, step):
        for x in range(0, W, step):
            d = math.hypot(x - cx, y - cy) / maxd
            v = int(min(255, max(0, (d - 0.55) / 0.45 * 255 * strength)))
            for yy in range(y, min(y + step, H)):
                for xx in range(x, min(x + step, W)):
                    px[xx, yy] = v
    vig = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, vig, mask)
    return img

def grain(img, amount=10):
    noise = Image.effect_noise((W, H), amount).convert("L")
    noise_img = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(img, noise_img, 0.06)

def text_block(draw, lines, font, x, y, line_h, fill, stroke):
    for i, ln in enumerate(lines):
        draw.text((x, y + i * line_h), ln, font=font, fill=fill,
                  stroke_width=stroke, stroke_fill=(0, 0, 0), anchor="mm")

def wrap(text, font, max_w):
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if draw.textbbox((0, 0), t, font=font)[2] <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def band(draw, lines, font, cx, y, line_h, pad=26):
    widths = [draw.textbbox((0, 0), ln, font=font)[2] for ln in lines]
    bw = max(widths) + pad * 2
    bh = len(lines) * line_h + pad * 2
    x0 = int(cx - bw / 2)
    y0 = int(y - bh / 2)
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18,
                           fill=(0, 0, 0, 150))

# Scene config: idx, path, mode, tint(r,g,b), title, sub, inset
CFG = [
    (1, f"{AI}/1890s_Paris_cafe_basement__a_c_2026-07-14T01-53-51.png", "cover", (1.06, 0.96, 0.80),
     "你以为的世界第一部电影，其实迟到了", None, None),
    (2, f"{PUB}/grand_cafe.jpg", "cover", (1.05, 0.96, 0.82),
     None, "1法郎 · 单日2500法郎 · 队伍1/4英里", None),
    (3, f"{PUB}/early_cinema_poster.jpg", "contain", (1.05, 0.97, 0.84),
     None, "No.653 · 1896里昂", None),
    (4, f"{AI}/Side_by_side_vintage_technical_2026-07-14T01-53-04.png", "cover", (1.05, 0.97, 0.82),
     None, "1000+磅 vs 9kg · 46→16帧/秒", None),
    (5, f"{AI}/Vintage_schematic_illustration_2026-07-14T01-54-21.png", "cover", (1.06, 0.97, 0.82),
     None, "缝纫机 → 胶片抓爪 · 46→16帧/秒", f"{PUB}/cinematographe.jpg"),
    (7, f"{AI}/1890s_Paris_cafe_basement__a_c_2026-07-14T01-53-51.png", "cover", (0.86, 0.96, 1.08),
     None, "无警局报告 / 无报纸报道", None),
    (8, f"{PUB}/lumiere_brothers.jpg", "contain", (1.05, 0.97, 0.84),
     None, "群演被要求不看镜头 · 家族成员出镜", None),
    (9, f"{PUB}/steam_locomotive.jpg", "cover", (1.05, 0.96, 0.80),
     None, "高尔基：一列火车朝你冲来——小心！", None),
    (11, f"{AI}/Abstract_stylized_vintage_stea_2026-07-14T01-54-01.png", "cover", (1.07, 0.98, 0.82),
     None, "它开进了2024巴黎奥运会开幕式", None),
    (12, f"{PUB}/early_cinema_poster.jpg", "contain", (1.05, 0.97, 0.84),
     None, "1895 → 2025 · 世界电影日", None),
    (13, f"{AI}/Vintage_steam_train_silhouette_2026-07-14T01-53-51.png", "cover", (1.08, 0.98, 0.82),
     "始于一趟迟到的火车", None, None),
]

for idx, path, mode, tintc, title, sub, inset in CFG:
    img = Image.open(path)
    img = fit_image(img, mode)
    img = tint(img, *tintc)
    img = vignette(img)
    img = grain(img)
    if inset:
        ins = Image.open(inset).convert("RGB").resize((420, 308), Image.LANCZOS)
        # border
        bw, bh = 420, 308
        img.paste(ins, (W - bw - 60, H - bh - 60))
        d = ImageDraw.Draw(img)
        d.rectangle([W - bw - 60, H - bh - 60, W - 60, H - 60], outline=(230, 220, 200), width=4)
    d = ImageDraw.Draw(img, "RGBA")
    cx = W / 2
    if title:
        tf = get_font(78)
        lines = wrap(title, tf, W - 240)
        band(d, lines, tf, cx, H / 2 - 20, 100)
        text_block(d, lines, tf, cx, H / 2 - 20, 100, (255, 255, 255), 4)
    if sub:
        sf = get_font(52)
        lines = wrap(sub, sf, W - 360)
        y = H - 150 if not title else H / 2 + 70
        band(d, lines, sf, cx, y, 70)
        text_block(d, lines, sf, cx, y, 70, (255, 248, 235), 3)
    out = os.path.join(OUT, f"seg{idx:02d}_base.png")
    img.save(out)
    print("saved", out)
print("DONE")
