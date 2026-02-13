from __future__ import annotations
"""Rotate images by degrees or auto-orient from EXIF."""
from pathlib import Path
from PIL import ImageOps
from .utils import open_image


def process_single(input_path: Path, output_path: Path, *,
                   degrees: float | None = None, auto: bool = False,
                   expand: bool = True, **kwargs) -> None:
    """Rotate a single image."""
    img = open_image(input_path)

    if auto:
        img = ImageOps.exif_transpose(img)
    elif degrees is not None:
        img = img.rotate(-degrees, expand=expand, resample=3)  # PIL rotates counter-clockwise
    else:
        raise ValueError("Specify -d/--degrees or --auto")

    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg') and img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')

    img.save(output_path, optimize=True)
