import os
import struct
import zlib
import hashlib
from PIL import Image, ImageDraw, ImageFont


def _make_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    chunk_len = struct.pack('>I', len(data))
    chunk_crc = struct.pack('>I', zlib.crc32(chunk_type + data))
    return chunk_len + chunk_type + data + chunk_crc


def make_png_with_text(
    text_comment: str = "Hello, 这是隐藏在图片里的文字！",
    output_dir: str = ".",          # 改为输出目录
    width: int = 1920,
    height: int = 1080,
    bg_color: tuple[int, int, int] = (255, 255, 255),
    text_color: tuple[int, int, int] = (0, 0, 0),
    font_size: int = 60,
) -> None:
    """生成带可见文字的 PNG，文件名由内容哈希决定，避免覆盖。

    参数:
        text_comment: 显示的文字（及嵌入的 tEXt 注释）
        output_dir:   输出目录（默认当前目录）
        width, height: 图片尺寸
        bg_color:     背景色
        text_color:   文字颜色
        font_size:    文字大小
    """
    # --- 1. 用 Pillow 绘制图像 ---
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 尝试使用中文字体，失败则用默认字体（可能不支持中文）
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
        print("⚠ 未找到中文字体，将使用默认字体（可能无法显示中文）")

    # 居中绘制文字
    bbox = draw.textbbox((0, 0), text_comment, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) // 2
    y = (height - th) // 2
    draw.text((x, y), text_comment, fill=text_color, font=font)

    # --- 2. 提取原始 RGB 像素数据 ---
    raw_data = bytearray()
    for y_ in range(height):
        raw_data.append(0)  # filter: None
        for x_ in range(width):
            pixel = img.getpixel((x_, y_))
            raw_data.extend(bytes(pixel))

    # --- 3. 手动构建 PNG（包含 IHDR, IDAT, tEXt, IEND）---
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = _make_png_chunk(b'IHDR', ihdr_data)
    idat = _make_png_chunk(b'IDAT', zlib.compress(bytes(raw_data)))
    text_chunk = _make_png_chunk(
        b'tEXt',
        b'Comment\x00' + text_comment.encode('utf-8')
    )
    iend = _make_png_chunk(b'IEND', b'')
    final_png = signature + ihdr + idat + text_chunk + iend

    # --- 4. 用 PNG 数据的哈希值生成唯一文件名 ---
    sha256 = hashlib.sha256(final_png).hexdigest()
    short_hash = sha256[:12]  # 取前 12 位，极低碰撞概率
    filename = f"img_{short_hash}.png"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # --- 5. 写出文件 ---
    with open(filepath, 'wb') as f:
        f.write(final_png)

    file_size = os.path.getsize(filepath)
    print(f"已生成 {filepath}（{file_size} 字节，{width}x{height}）")
    print(f"可见文字：「{text_comment}」，颜色 {text_color}，背景 {bg_color}")


if __name__ == '__main__':
    # 第一次运行
    make_png_with_text(
        text_comment="你好，世界！",
        bg_color=(255, 255, 255),
        text_color=(255, 0, 0),
        font_size=72
    )
    # 第二次运行（不同文字，不会覆盖前一个文件）
    make_png_with_text(
        text_comment="Hello, PNG!",
        bg_color=(0, 0, 0),
        text_color=(0, 255, 0),
        font_size=72
    )