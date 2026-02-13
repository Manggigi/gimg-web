from __future__ import annotations
"""Crop images by coordinates or aspect ratio."""
from pathlib import Path
from .utils import open_image


def process_single(input_path: Path, output_path: Path, *,
                   x: int = 0, y: int = 0,
                   width: int | None = None, height: int | None = None,
                   ratio: str | None = None, **kwargs) -> None:
    """Crop a single image."""
    img = open_image(input_path)
    img_w, img_h = img.size

    if ratio:
        # Parse ratio like "16:9"
        parts = ratio.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid ratio format: {ratio} (expected W:H, e.g. 16:9)")
        rw, rh = float(parts[0]), float(parts[1])
        target_ratio = rw / rh
        current_ratio = img_w / img_h

        if current_ratio > target_ratio:
            # Too wide, crop width
            new_w = int(img_h * target_ratio)
            new_h = img_h
        else:
            # Too tall, crop height
            new_w = img_w
            new_h = int(img_w / target_ratio)

        cx = (img_w - new_w) // 2
        cy = (img_h - new_h) // 2
        box = (cx, cy, cx + new_w, cy + new_h)
    else:
        if width is None or height is None:
            raise ValueError("Specify --width and --height, or --ratio")
        box = (x, y, x + width, y + height)
        # Clamp to image bounds
        box = (max(0, box[0]), max(0, box[1]), min(img_w, box[2]), min(img_h, box[3]))

    cropped = img.crop(box)

    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg') and cropped.mode in ('RGBA', 'P', 'LA'):
        cropped = cropped.convert('RGB')

    cropped.save(output_path, optimize=True)
