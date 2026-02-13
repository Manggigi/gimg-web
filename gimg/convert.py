from __future__ import annotations
"""Convert images between formats."""
from pathlib import Path
from .utils import open_image

FORMAT_MAP = {
    'jpg': '.jpg', 'jpeg': '.jpeg', 'png': '.png', 'gif': '.gif',
    'webp': '.webp', 'bmp': '.bmp', 'tiff': '.tiff', 'tif': '.tif',
}


def process_single(input_path: Path, output_path: Path, *,
                   to_format: str | None = None, **kwargs) -> None:
    """Convert a single image to a different format."""
    img = open_image(input_path)

    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg'):
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=95, optimize=True)
    elif out_ext == '.png':
        img.save(output_path, 'PNG', optimize=True)
    elif out_ext == '.webp':
        img.save(output_path, 'WEBP', quality=90, method=4)
    elif out_ext == '.gif':
        img.save(output_path, 'GIF')
    elif out_ext == '.bmp':
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(output_path, 'BMP')
    elif out_ext in ('.tiff', '.tif'):
        img.save(output_path, 'TIFF')
    else:
        raise ValueError(f"Unsupported output format: {out_ext}")
