from __future__ import annotations
"""Classic meme text generator — white Impact text with black outline."""
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .utils import open_image

MAX_TEXT_LEN = 200


def _sanitize_text(text: str) -> str:
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)[:MAX_TEXT_LEN]


def _get_impact_font(size: int):
    candidates = [
        'Impact.ttf', 'impact.ttf',
        '/Library/Fonts/Impact.ttf',
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        'C:\\Windows\\Fonts\\impact.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Impact.ttf',
        'DejaVuSans-Bold.ttf',
    ]
    # macOS system paths
    candidates += [
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines = []
    current = ''
    for word in words:
        test = f'{current} {word}'.strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def _draw_outlined_text(draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
                        font, fill=(255, 255, 255), outline=(0, 0, 0), outline_width: int = 2):
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def process_single(input_path: Path, output_path: Path, *,
                   top: str | None = None, bottom: str | None = None,
                   size: int | None = None, no_caps: bool = False, **kwargs) -> None:
    if not top and not bottom:
        raise ValueError("Provide --top and/or --bottom text")

    img = open_image(input_path).convert('RGBA')
    w, h = img.size

    font_size = size or max(20, w // 12)
    font = _get_impact_font(font_size)
    outline_w = max(1, font_size // 15)
    draw = ImageDraw.Draw(img)
    margin = w // 30

    for text, is_top in [(top, True), (bottom, False)]:
        if not text:
            continue
        text = _sanitize_text(text)
        if not no_caps:
            text = text.upper()

        lines = _wrap_text(text, font, w - margin * 2, draw)
        line_height = draw.textbbox((0, 0), 'Ay', font=font)[3] + 4
        block_h = line_height * len(lines)

        if is_top:
            y_start = margin
        else:
            y_start = h - block_h - margin

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            x = (w - lw) // 2
            y = y_start + i * line_height
            _draw_outlined_text(draw, x, y, line, font, outline_width=outline_w)

    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg'):
        img = img.convert('RGB')
    img.save(output_path)
