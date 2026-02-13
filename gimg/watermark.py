from __future__ import annotations
"""Add text or image watermarks to images."""
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from .utils import open_image

MAX_TEXT_LEN = 500

COLOR_MAP = {
    'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0),
    'green': (0, 128, 0), 'blue': (0, 0, 255), 'yellow': (255, 255, 0),
    'gray': (128, 128, 128), 'grey': (128, 128, 128),
}


def _sanitize_text(text: str) -> str:
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return text[:MAX_TEXT_LEN]


def _parse_color(color_str: str) -> tuple:
    c = color_str.strip().lower()
    if c in COLOR_MAP:
        return COLOR_MAP[c]
    c = color_str.strip().lstrip('#')
    if re.match(r'^[0-9a-fA-F]{6}$', c):
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    raise ValueError(f"Unknown color: {color_str}. Use a name (white, red, ...) or hex (#FF0000)")


def _get_font(size: int):
    for name in ['DejaVuSans-Bold.ttf', 'DejaVuSans.ttf', 'Arial.ttf', 'Helvetica.ttf']:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    # macOS system fonts
    for p in ['/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/SFNSText.ttf']:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _calc_position(pos: str, img_w: int, img_h: int, wm_w: int, wm_h: int, margin: int = 10):
    positions = {
        'center': ((img_w - wm_w) // 2, (img_h - wm_h) // 2),
        'top-left': (margin, margin),
        'top-right': (img_w - wm_w - margin, margin),
        'bottom-left': (margin, img_h - wm_h - margin),
        'bottom-right': (img_w - wm_w - margin, img_h - wm_h - margin),
    }
    return positions.get(pos, positions['bottom-right'])


def process_single(input_path: Path, output_path: Path, *,
                   text: str | None = None, image_wm: str | None = None,
                   pos: str = 'bottom-right', opacity: float = 0.3,
                   size: int | None = None, color: str = 'white',
                   tile: bool = False, angle: float = 0, **kwargs) -> None:
    img = open_image(input_path).convert('RGBA')
    w, h = img.size

    if text:
        text = _sanitize_text(text)
        font_size = size or max(16, min(w, h) // 15)
        font = _get_font(font_size)
        rgb = _parse_color(color)
        alpha = int(opacity * 255)

        # Measure text
        tmp = Image.new('RGBA', (1, 1))
        draw = ImageDraw.Draw(tmp)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        if tile:
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            txt_img = Image.new('RGBA', (tw + 20, th + 20), (0, 0, 0, 0))
            ImageDraw.Draw(txt_img).text((10, 10), text, font=font, fill=(*rgb, alpha))
            if angle:
                txt_img = txt_img.rotate(angle, expand=True, resample=Image.BICUBIC)
            tw2, th2 = txt_img.size
            spacing_x, spacing_y = tw2 + 40, th2 + 40
            for yi in range(-th2, h + th2, spacing_y):
                for xi in range(-tw2, w + tw2, spacing_x):
                    overlay.paste(txt_img, (xi, yi), txt_img)
            img = Image.alpha_composite(img, overlay)
        else:
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            x, y = _calc_position(pos, w, h, tw, th)
            ImageDraw.Draw(overlay).text((x, y), text, font=font, fill=(*rgb, alpha))
            img = Image.alpha_composite(img, overlay)

    elif image_wm:
        wm = Image.open(image_wm).convert('RGBA')
        # Scale watermark to ~20% of image width
        max_wm_w = w // 5
        if wm.width > max_wm_w:
            ratio = max_wm_w / wm.width
            wm = wm.resize((int(wm.width * ratio), int(wm.height * ratio)), Image.LANCZOS)
        # Apply opacity
        if opacity < 1.0:
            alpha_channel = wm.split()[3]
            alpha_channel = alpha_channel.point(lambda p: int(p * opacity))
            wm.putalpha(alpha_channel)

        if tile:
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            spacing_x, spacing_y = wm.width + 40, wm.height + 40
            for yi in range(0, h, spacing_y):
                for xi in range(0, w, spacing_x):
                    overlay.paste(wm, (xi, yi), wm)
            img = Image.alpha_composite(img, overlay)
        else:
            x, y = _calc_position(pos, w, h, wm.width, wm.height)
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            overlay.paste(wm, (x, y), wm)
            img = Image.alpha_composite(img, overlay)

    # Save - convert back to RGB for JPEG
    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg'):
        img = img.convert('RGB')
    img.save(output_path)
