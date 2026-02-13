from __future__ import annotations
"""Photo editor with combinable adjustments, filters, borders, frames, and more."""
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
import numpy as np

from .utils import open_image


# ─── Validation ──────────────────────────────────────────────────────────────

def _clamp(val, lo, hi, name):
    """Validate a numeric value is within range."""
    if val < lo or val > hi:
        raise ValueError(f"{name} must be between {lo} and {hi}, got {val}")
    return val


def _parse_color(color_str: str):
    """Parse a color string (name or hex) safely."""
    if not color_str:
        return "white"
    s = color_str.strip().strip("'\"")
    # Basic validation: allow named colors and hex
    if s.startswith('#'):
        clean = s[1:]
        if len(clean) not in (3, 4, 6, 8) or not all(c in '0123456789abcdefABCDEF' for c in clean):
            raise ValueError(f"Invalid hex color: {s}")
    return s


# ─── Adjustments ─────────────────────────────────────────────────────────────

def apply_brightness(img: Image.Image, factor: float) -> Image.Image:
    _clamp(factor, 0.0, 10.0, "brightness")
    return ImageEnhance.Brightness(img).enhance(factor)


def apply_contrast(img: Image.Image, factor: float) -> Image.Image:
    _clamp(factor, 0.0, 10.0, "contrast")
    return ImageEnhance.Contrast(img).enhance(factor)


def apply_saturation(img: Image.Image, factor: float) -> Image.Image:
    _clamp(factor, 0.0, 10.0, "saturation")
    return ImageEnhance.Color(img).enhance(factor)


def apply_sharpness(img: Image.Image, factor: float) -> Image.Image:
    _clamp(factor, 0.0, 10.0, "sharpness")
    return ImageEnhance.Sharpness(img).enhance(factor)


def apply_hue(img: Image.Image, degrees: float) -> Image.Image:
    """Shift hue by degrees (-180 to 180)."""
    _clamp(degrees, -180, 180, "hue")
    if img.mode != 'RGB':
        img = img.convert('RGB')
    arr = np.array(img, dtype=np.float32)
    # Convert to HSV-like by shifting in numpy
    from colorsys import rgb_to_hsv, hsv_to_rgb
    flat = arr.reshape(-1, 3) / 255.0
    shifted = np.empty_like(flat)
    shift = degrees / 360.0
    for i in range(len(flat)):
        h, s, v = rgb_to_hsv(flat[i, 0], flat[i, 1], flat[i, 2])
        h = (h + shift) % 1.0
        r, g, b = hsv_to_rgb(h, s, v)
        shifted[i] = [r, g, b]
    result = (shifted * 255).clip(0, 255).astype(np.uint8).reshape(arr.shape)
    return Image.fromarray(result)


# ─── Filters ─────────────────────────────────────────────────────────────────

VALID_FILTERS = [
    'grayscale', 'sepia', 'blur', 'emboss', 'contour', 'sharpen', 'smooth',
    'invert', 'posterize', 'solarize', 'vintage', 'dramatic', 'warm', 'cool',
]


def apply_filter(img: Image.Image, name: str) -> Image.Image:
    """Apply a named filter preset."""
    if name not in VALID_FILTERS:
        raise ValueError(f"Unknown filter '{name}'. Choose from: {', '.join(VALID_FILTERS)}")
    fn = _FILTER_MAP[name]
    return fn(img)


def _grayscale(img):
    return ImageOps.grayscale(img).convert('RGB')


def _sepia(img):
    grey = ImageOps.grayscale(img)
    arr = np.array(grey, dtype=np.float32)
    sepia = np.stack([
        (arr * 1.2).clip(0, 255),
        (arr * 1.0).clip(0, 255),
        (arr * 0.8).clip(0, 255),
    ], axis=-1).astype(np.uint8)
    return Image.fromarray(sepia)


def _blur(img):
    return img.filter(ImageFilter.GaussianBlur(radius=3))


def _emboss(img):
    return img.filter(ImageFilter.EMBOSS)


def _contour(img):
    return img.filter(ImageFilter.CONTOUR)


def _sharpen(img):
    return img.filter(ImageFilter.SHARPEN)


def _smooth(img):
    return img.filter(ImageFilter.SMOOTH_MORE)


def _invert(img):
    if img.mode == 'RGBA':
        r, g, b, a = img.split()
        rgb = Image.merge('RGB', (r, g, b))
        rgb = ImageOps.invert(rgb)
        r2, g2, b2 = rgb.split()
        return Image.merge('RGBA', (r2, g2, b2, a))
    return ImageOps.invert(img.convert('RGB'))


def _posterize(img):
    return ImageOps.posterize(img.convert('RGB'), 3)


def _solarize(img):
    return ImageOps.solarize(img.convert('RGB'), threshold=128)


def _vintage(img):
    """Warm vintage: sepia tint + vignette + grain."""
    img = img.convert('RGB')
    # Sepia tint
    arr = np.array(img, dtype=np.float32)
    grey = np.mean(arr, axis=2)
    arr[:, :, 0] = (grey * 1.15).clip(0, 255)
    arr[:, :, 1] = (grey * 1.0).clip(0, 255)
    arr[:, :, 2] = (grey * 0.85).clip(0, 255)
    # Blend with original (50%)
    orig = np.array(img, dtype=np.float32)
    arr = (arr * 0.5 + orig * 0.5).clip(0, 255)
    # Add grain
    noise = np.random.normal(0, 10, arr.shape)
    arr = (arr + noise).clip(0, 255).astype(np.uint8)
    result = Image.fromarray(arr)
    # Vignette
    return _add_vignette(result, strength=0.4)


def _dramatic(img):
    """High contrast B&W with slight grain."""
    grey = ImageOps.grayscale(img)
    enhanced = ImageOps.autocontrast(grey, cutoff=2)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.5)
    arr = np.array(enhanced, dtype=np.float32)
    noise = np.random.normal(0, 8, arr.shape)
    arr = (arr + noise).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert('RGB')


def _warm(img):
    """Warm color shift."""
    img = img.convert('RGB')
    arr = np.array(img, dtype=np.float32)
    arr[:, :, 0] = (arr[:, :, 0] * 1.1).clip(0, 255)  # More red
    arr[:, :, 1] = (arr[:, :, 1] * 1.05).clip(0, 255)  # Slightly more green
    arr[:, :, 2] = (arr[:, :, 2] * 0.9).clip(0, 255)   # Less blue
    return Image.fromarray(arr.astype(np.uint8))


def _cool(img):
    """Cool/blue color shift."""
    img = img.convert('RGB')
    arr = np.array(img, dtype=np.float32)
    arr[:, :, 0] = (arr[:, :, 0] * 0.9).clip(0, 255)
    arr[:, :, 2] = (arr[:, :, 2] * 1.15).clip(0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def _add_vignette(img: Image.Image, strength: float = 0.5) -> Image.Image:
    """Add a radial vignette effect."""
    w, h = img.size
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_r = np.sqrt(cx ** 2 + cy ** 2)
    vignette = 1.0 - strength * (r / max_r) ** 2
    vignette = vignette.clip(0, 1)
    arr = np.array(img, dtype=np.float32)
    for c in range(3):
        arr[:, :, c] *= vignette
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


_FILTER_MAP = {
    'grayscale': _grayscale, 'sepia': _sepia, 'blur': _blur,
    'emboss': _emboss, 'contour': _contour, 'sharpen': _sharpen,
    'smooth': _smooth, 'invert': _invert, 'posterize': _posterize,
    'solarize': _solarize, 'vintage': _vintage, 'dramatic': _dramatic,
    'warm': _warm, 'cool': _cool,
}


# ─── Flip ────────────────────────────────────────────────────────────────────

def apply_flip(img: Image.Image, direction: str) -> Image.Image:
    if direction == 'horizontal':
        return ImageOps.mirror(img)
    elif direction == 'vertical':
        return ImageOps.flip(img)
    else:
        raise ValueError(f"flip must be 'horizontal' or 'vertical', got '{direction}'")


# ─── Auto-enhance ────────────────────────────────────────────────────────────

def apply_auto_enhance(img: Image.Image) -> Image.Image:
    """Auto adjust brightness/contrast using ImageOps.autocontrast."""
    if img.mode == 'RGBA':
        r, g, b, a = img.split()
        rgb = Image.merge('RGB', (r, g, b))
        rgb = ImageOps.autocontrast(rgb, cutoff=1)
        r2, g2, b2 = rgb.split()
        return Image.merge('RGBA', (r2, g2, b2, a))
    return ImageOps.autocontrast(img.convert('RGB'), cutoff=1)


# ─── Borders & Frames ───────────────────────────────────────────────────────

def apply_border(img: Image.Image, width: int, color: str = 'white') -> Image.Image:
    """Add a solid color border."""
    _clamp(width, 1, 500, "border")
    color = _parse_color(color)
    return ImageOps.expand(img, border=width, fill=color)


def apply_frame_polaroid(img: Image.Image) -> Image.Image:
    """Polaroid-style frame: white border, bottom thicker, subtle shadow."""
    img = img.convert('RGB')
    w, h = img.size
    border_side = max(int(min(w, h) * 0.04), 10)
    border_bottom = border_side * 3
    # Canvas with shadow
    cw = w + border_side * 2 + 6
    ch = h + border_side + border_bottom + 6
    canvas = Image.new('RGB', (cw, ch), '#f0f0f0')
    # Shadow
    shadow = Image.new('RGB', (w + border_side * 2, h + border_side + border_bottom), '#cccccc')
    canvas.paste(shadow, (6, 6))
    # White frame
    frame = Image.new('RGB', (w + border_side * 2, h + border_side + border_bottom), '#fafafa')
    canvas.paste(frame, (0, 0))
    # Image
    canvas.paste(img, (border_side, border_side))
    return canvas


def apply_frame_rounded(img: Image.Image) -> Image.Image:
    """Round the corners of the image."""
    img = img.convert('RGBA')
    w, h = img.size
    radius = max(int(min(w, h) * 0.05), 8)
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    img.putalpha(mask)
    # Paste onto white background for non-PNG output
    bg = Image.new('RGB', (w, h), 'white')
    bg.paste(img, mask=img.split()[3])
    return bg


def apply_frame_shadow(img: Image.Image) -> Image.Image:
    """Drop shadow frame."""
    img = img.convert('RGB')
    w, h = img.size
    offset = max(int(min(w, h) * 0.02), 5)
    padding = offset * 3
    cw = w + padding * 2
    ch = h + padding * 2
    canvas = Image.new('RGB', (cw, ch), '#f5f5f5')
    # Shadow (blurred dark rectangle)
    shadow = Image.new('RGB', (w, h), '#888888')
    canvas.paste(shadow, (padding + offset, padding + offset))
    canvas = canvas.filter(ImageFilter.GaussianBlur(radius=offset))
    # Paste original on top
    canvas.paste(img, (padding, padding))
    return canvas


FRAME_MAP = {
    'polaroid': apply_frame_polaroid,
    'rounded': apply_frame_rounded,
    'shadow': apply_frame_shadow,
}


def apply_frame(img: Image.Image, name: str) -> Image.Image:
    if name not in FRAME_MAP:
        raise ValueError(f"Unknown frame '{name}'. Choose from: {', '.join(FRAME_MAP.keys())}")
    return FRAME_MAP[name](img)


# ─── Thumbnail ───────────────────────────────────────────────────────────────

def apply_thumbnail(img: Image.Image, size: int) -> Image.Image:
    """Create a square center-cropped thumbnail."""
    _clamp(size, 16, 4096, "thumbnail size")
    img = img.convert('RGB')
    w, h = img.size
    # Center crop to square
    short = min(w, h)
    left = (w - short) // 2
    top = (h - short) // 2
    img = img.crop((left, top, left + short, top + short))
    img = img.resize((size, size), Image.LANCZOS)
    return img


# ─── Main processor ─────────────────────────────────────────────────────────

def process_single(input_path: Path, output_path: Path, **kwargs) -> None:
    """Apply edits to a single image. Operations applied in order:
    auto-enhance → adjustments → filter → flip → border/frame → thumbnail.
    """
    img = open_image(input_path)
    if img.mode == 'P':
        img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')

    # 1. Auto-enhance
    if kwargs.get('auto_enhance'):
        img = apply_auto_enhance(img)

    # 2. Adjustments
    if kwargs.get('brightness') is not None:
        img = apply_brightness(img, kwargs['brightness'])
    if kwargs.get('contrast') is not None:
        img = apply_contrast(img, kwargs['contrast'])
    if kwargs.get('saturation') is not None:
        img = apply_saturation(img, kwargs['saturation'])
    if kwargs.get('sharpness') is not None:
        img = apply_sharpness(img, kwargs['sharpness'])
    if kwargs.get('hue') is not None:
        img = apply_hue(img, kwargs['hue'])

    # 3. Filter
    if kwargs.get('filter_name'):
        img = apply_filter(img, kwargs['filter_name'])

    # 4. Flip
    if kwargs.get('flip'):
        img = apply_flip(img, kwargs['flip'])

    # 5. Border
    if kwargs.get('border'):
        img = apply_border(img, kwargs['border'], kwargs.get('border_color', 'white'))

    # 6. Frame
    if kwargs.get('frame'):
        img = apply_frame(img, kwargs['frame'])

    # 7. Thumbnail (last)
    if kwargs.get('thumbnail'):
        img = apply_thumbnail(img, kwargs['thumbnail'])

    # Save
    if img.mode == 'RGBA' and output_path.suffix.lower() in ('.jpg', '.jpeg'):
        bg = Image.new('RGB', img.size, 'white')
        bg.paste(img, mask=img.split()[3])
        img = bg
    img.save(output_path, quality=95)
