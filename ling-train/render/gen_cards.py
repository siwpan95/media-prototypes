from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, os

base = os.environ.get("LING_TRAIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 仓根：环境变量 LING_TRAIN_ROOT 覆盖，否则由本脚本所在 render/ 上溯推导（去本地化，原硬编码绝对路径已失效）
pack = json.load(open(base + "\\phase2_production_pack.json", encoding="utf-8"))
img_dir = base + "\\render\\images"
os.makedirs(img_dir, exist_ok=True)

font_path = "C:/Windows/Fonts/msyh.ttc"
font_bold = "C:/Windows/Fonts/msyhbd.ttc"
W, H = 1920, 1080

def font(size, bold=False):
    return ImageFont.truetype(font_bold if bold else font_path, size)

themes = {
 'cool': dict(bg_top=(11,18,32), bg_bottom=(20,35,63), glow=(40,90,160), accent=(86,199,248), title=(237,242,247), sub=(150,180,210)),
 'warm': dict(bg_top=(26,18,8), bg_bottom=(58,36,16), glow=(200,120,40), accent=(244,176,84), title=(252,245,236), sub=(222,192,162)),
}
warm_scenes = {6,7,8,10,12}

highlights = {
 1:"暑运首日 · 4151万人次",
 2:"从绿皮车到复兴号",
 3:"西十高铁 · 257km · 350km/h · 2h41m",
 4:"佛山站 · 高铁开进市中心 · 98趟",
 5:"西康高铁 · 385km/h · 逐级提速",
 6:"雪夜 · 45秒 · 播放破5000万",
 7:"东京站 · 4K ASMR · 安静的治愈",
 8:"日本 · 发车音乐 · 进站仪式感",
 9:"世界车站 · 美与文明",
 10:"无锡 · 老站变身城市客厅",
 11:"OpenRails · 开源复现进站",
 12:"硬核与温柔 · 每一次进站都是归来",
}

def vgrad(top, bottom):
    img = Image.new("RGB", (W, H))
    d = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(top[0] + (bottom[0]-top[0])*t)
        g = int(top[1] + (bottom[1]-top[1])*t)
        b = int(top[2] + (bottom[2]-top[2])*t)
        for x in range(W):
            d[x, y] = (r, g, b)
    return img

def wrap(text, n):
    return [text[i:i+n] for i in range(0, len(text), n)]

for s in pack["scenes"]:
    i = s["index"]
    th = themes['warm'] if i in warm_scenes else themes['cool']
    img = vgrad(th['bg_top'], th['bg_bottom'])
    # radial glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([int(W*0.5), int(H*0.05), int(W*1.2), int(H*1.0)], fill=th['glow']+(95,))
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)
    # faint giant scene number
    big = font(560, bold=True)
    bn = f"{i:02d}"
    bb = draw.textbbox((0, 0), bn, font=big)
    bw = bb[2]-bb[0]; bh = bb[3]-bb[1]
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((W-bw-70, H-bh-10), bn, font=big, fill=th['accent']+(55,))
    img = Image.alpha_composite(img.convert("RGBA"), tmp).convert("RGB")
    draw = ImageDraw.Draw(img)
    # top accent rule
    draw.rectangle([120, 118, 380, 126], fill=th['accent'])
    # brand + episode
    draw.text((120, 148), "灵枢 · 火车进站", font=font(40, True), fill=th['sub'])
    draw.text((W-120, 148), f"EP.{i:02d} / 12", font=font(40, True), fill=th['sub'], anchor="ra")
    # title
    lines = wrap(s["subtitle"], 18)
    ty = 350
    tf = font(84, True)
    for ln in lines:
        draw.text((120, ty), ln, font=tf, fill=th['title'])
        ty += 104
    # highlight
    draw.text((124, ty+18), highlights[i], font=font(46, True), fill=th['accent'])
    # bottom rule + caption
    draw.rectangle([120, H-122, W-120, H-114], fill=th['accent'])
    draw.text((120, H-100), "中国速度的硬核与温柔", font=font(34), fill=th['sub'])
    img.save(f"{img_dir}\\scene_{i:02d}.png")
    print("saved scene", i)
print("DONE cards")
