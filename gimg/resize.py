from __future__ import annotations
"""Resize images by dimensions or percentage."""
from pathlib import Path
from PIL import Image
from .utils import open_image


def process_single(input_path: Path, output_path: Path, *,
                   width: int | None = None, height: int | None = None,
                   percentage: float | None = None, max_size: int | None = None,
                   **kwargs) -> None:
    """Resize a single image."""
    img = open_image(input_path)
    orig_w, orig_h = img.size

    if percentage is not None:
        new_w = int(orig_w * percentage / 100)
        new_h = int(orig_h * percentage / 100)
    elif max_size is not None:
        ratio = min(max_size / orig_w, max_size / orig_h)
        if ratio >= 1:
            new_w, new_h = orig_w, orig_h
        else:
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
    elif width and height:
        new_w, new_h = width, height
    elif width:
        ratio = width / orig_w
        new_w = width
        new_h = int(orig_h * ratio)
    elif height:
        ratio = height / orig_h
        new_w = int(orig_w * ratio)
        new_h = height
    else:
        raise ValueError("Specify -w/--width, -h/--height, -p/--percentage, or --max-size")

    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Handle format conversion for save
    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg') and resized.mode in ('RGBA', 'P', 'LA'):
        resized = resized.convert('RGB')

    resized.save(output_path, optimize=True)
