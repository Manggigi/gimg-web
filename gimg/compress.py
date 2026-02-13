from __future__ import annotations
"""Compress images by reducing quality/optimizing."""
from pathlib import Path
from .utils import open_image


def process_single(input_path: Path, output_path: Path, *, quality: int = 80, **kwargs) -> None:
    """Compress a single image file."""
    img = open_image(input_path)

    save_kwargs = {"optimize": True}
    out_ext = output_path.suffix.lower()

    if out_ext in ('.jpg', '.jpeg'):
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        save_kwargs["quality"] = quality
        save_kwargs["progressive"] = True
    elif out_ext == '.png':
        save_kwargs["compress_level"] = 9
    elif out_ext == '.webp':
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 6
    else:
        save_kwargs["quality"] = quality

    img.save(output_path, **save_kwargs)
