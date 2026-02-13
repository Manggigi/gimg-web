from __future__ import annotations
"""Display image information: dimensions, format, size, color mode."""
from pathlib import Path
from .utils import open_image, detect_format


def show_info(input_path: Path) -> dict:
    """Get image info as a dict."""
    file_size = input_path.stat().st_size
    fmt = detect_format(input_path)
    img = open_image(input_path)
    w, h = img.size

    return {
        'file': str(input_path),
        'format': fmt or 'Unknown',
        'dimensions': f"{w} x {h}",
        'width': w,
        'height': h,
        'mode': img.mode,
        'file_size': file_size,
        'file_size_human': _human_size(file_size),
    }


def _human_size(nbytes: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def process_single(input_path: Path, output_path: Path = None, **kwargs) -> None:
    """Display info for a single image (no output file produced)."""
    info = show_info(input_path)
    print(f"  File:       {info['file']}")
    print(f"  Format:     {info['format']}")
    print(f"  Dimensions: {info['dimensions']}")
    print(f"  Mode:       {info['mode']}")
    print(f"  File size:  {info['file_size_human']}")
