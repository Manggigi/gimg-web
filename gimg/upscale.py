from __future__ import annotations
"""Upscale images using Pillow LANCZOS resampling."""
from pathlib import Path
from PIL import Image, ImageFilter

from .utils import open_image


def process_single(input_path: Path, output_path: Path, *, scale: int = 2,
                   width: int | None = None, height: int | None = None,
                   sharpen: bool = True) -> None:
    img = open_image(input_path)

    if width or height:
        orig_w, orig_h = img.size
        if width and height:
            new_size = (width, height)
        elif width:
            ratio = width / orig_w
            new_size = (width, round(orig_h * ratio))
        else:
            ratio = height / orig_h
            new_size = (round(orig_w * ratio), height)
    else:
        new_size = (img.size[0] * scale, img.size[1] * scale)

    img = img.resize(new_size, Image.LANCZOS)

    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=50, threshold=3))

    img.save(output_path)
