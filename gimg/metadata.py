from __future__ import annotations
"""View and strip EXIF metadata from images."""
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from .utils import open_image


def _format_exif(img: Image.Image) -> dict:
    """Extract EXIF data as a human-readable dict."""
    exif_data = img.getexif()
    if not exif_data:
        return {}
    result = {}
    for tag_id, value in exif_data.items():
        tag = TAGS.get(tag_id, tag_id)
        # Skip binary blobs
        if isinstance(value, bytes) and len(value) > 100:
            value = f"<{len(value)} bytes>"
        result[str(tag)] = str(value)
    return result


def view_metadata(input_path: Path) -> dict:
    """View EXIF metadata for an image."""
    img = open_image(input_path)
    return _format_exif(img)


def process_single(input_path: Path, output_path: Path, *,
                   strip: bool = False, view: bool = False, **kwargs) -> None:
    """Process metadata for a single image. If strip=True, remove all EXIF data."""
    if strip:
        img = open_image(input_path)
        # Create a clean copy without EXIF
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))

        out_ext = output_path.suffix.lower()
        if out_ext in ('.jpg', '.jpeg') and clean.mode in ('RGBA', 'P', 'LA'):
            clean = clean.convert('RGB')

        clean.save(output_path, optimize=True)
    else:
        # View mode — just print, no output file needed
        data = view_metadata(input_path)
        if data:
            max_key = max(len(k) for k in data)
            for k, v in sorted(data.items()):
                print(f"  {k:<{max_key}}  {v}")
        else:
            print(f"  No EXIF metadata found in {input_path.name}")
