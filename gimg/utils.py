from __future__ import annotations
"""Shared utilities for GIMG tools."""
import glob
import os
import sys
from pathlib import Path

from PIL import Image

# Magic bytes for supported formats
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'JPEG',
    b'\x89PNG\r\n\x1a\n': 'PNG',
    b'GIF87a': 'GIF',
    b'GIF89a': 'GIF',
    b'RIFF': 'WEBP',  # WEBP starts with RIFF....WEBP
    b'BM': 'BMP',
    b'II\x2a\x00': 'TIFF',
    b'MM\x00\x2a': 'TIFF',
    b'\x00\x00\x00': 'HEIC',  # ftyp box (checked further below)
    b'<?xml': 'SVG',
    b'<svg': 'SVG',
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

SUPPORTED_READ = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.heic', '.heif', '.svg'}
SUPPORTED_WRITE = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}


def detect_format(path: Path) -> str | None:
    """Detect image format via magic bytes."""
    try:
        with open(path, 'rb') as f:
            header = f.read(32)
    except (OSError, IOError):
        return None

    if header[:3] == b'\xff\xd8\xff':
        return 'JPEG'
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return 'PNG'
    if header[:6] in (b'GIF87a', b'GIF89a'):
        return 'GIF'
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'WEBP'
    if header[:2] == b'BM':
        return 'BMP'
    if header[:4] in (b'II\x2a\x00', b'MM\x00\x2a'):
        return 'TIFF'
    # HEIC/HEIF: ftyp box
    if len(header) >= 12 and header[4:8] == b'ftyp':
        brand = header[8:12]
        if brand in (b'heic', b'heix', b'hevc', b'mif1', b'msf1', b'avif'):
            return 'HEIC'
    # SVG
    stripped = header.lstrip()
    if stripped[:5] == b'<?xml' or stripped[:4] == b'<svg':
        return 'SVG'

    return None


def validate_input(path: Path, max_size: int = MAX_FILE_SIZE) -> None:
    """Validate that the input file exists, is within size limits, and is a supported image."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    size = path.stat().st_size
    if size > max_size:
        raise ValueError(f"File too large: {size / 1024 / 1024:.1f}MB (max {max_size / 1024 / 1024:.0f}MB)")
    fmt = detect_format(path)
    if fmt is None:
        raise ValueError(f"Unsupported or unrecognized image format: {path}")


def open_image(path: Path) -> Image.Image:
    """Open an image, handling HEIC and SVG specially."""
    fmt = detect_format(path)

    if fmt == 'HEIC':
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            raise ImportError("pillow-heif is required for HEIC/HEIF support: pip install pillow-heif")
        return Image.open(path)

    if fmt == 'SVG':
        try:
            import cairosvg
            import io
            png_data = cairosvg.svg2png(url=str(path))
            return Image.open(io.BytesIO(png_data))
        except ImportError:
            raise ImportError("cairosvg is required for SVG support: pip install cairosvg")

    return Image.open(path)


def default_output(input_path: Path, suffix: str, ext: str | None = None) -> Path:
    """Generate default output path: {name}_{suffix}.{ext}"""
    stem = input_path.stem
    extension = ext if ext else input_path.suffix
    if not extension.startswith('.'):
        extension = '.' + extension
    return input_path.parent / f"{stem}_{suffix}{extension}"


def resolve_inputs(input_arg: str) -> list[Path]:
    """Resolve a single file, directory, or glob pattern to a list of paths."""
    p = Path(input_arg)
    if p.is_file():
        return [p]
    if p.is_dir():
        files = []
        for ext in SUPPORTED_READ:
            files.extend(p.glob(f'*{ext}'))
            files.extend(p.glob(f'*{ext.upper()}'))
        return sorted(set(files))
    # Try glob
    matches = glob.glob(input_arg)
    if matches:
        return sorted(Path(m) for m in matches if Path(m).is_file())
    raise FileNotFoundError(f"No files found matching: {input_arg}")


def resolve_output(input_path: Path, output_arg: str | None, tool_suffix: str,
                   ext: str | None = None, overwrite: bool = False) -> Path:
    """Determine the output path for a single file."""
    if output_arg:
        out = Path(output_arg)
        if out.is_dir():
            name = default_output(input_path, tool_suffix, ext).name
            return out / name
        return out
    out = default_output(input_path, tool_suffix, ext)
    if out == input_path and not overwrite:
        raise ValueError(f"Output would overwrite input. Use --overwrite or -o to specify output.")
    return out


def ensure_parent(path: Path) -> None:
    """Create parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)


def run_batch(inputs: list[Path], process_fn, output_arg: str | None,
              tool_suffix: str, overwrite: bool = False, ext: str | None = None, **kwargs):
    """Run a processing function over a batch of files with progress output."""
    total = len(inputs)
    success = 0
    errors = []

    # If output_arg is a directory (or batch mode), ensure it exists
    if output_arg and total > 1:
        Path(output_arg).mkdir(parents=True, exist_ok=True)

    for i, inp in enumerate(inputs, 1):
        try:
            validate_input(inp)
            out = resolve_output(inp, output_arg, tool_suffix, ext=ext, overwrite=overwrite)
            ensure_parent(out)
            process_fn(inp, out, **kwargs)
            print(f"[{i}/{total}] ✓ {inp.name} → {out.name}")
            success += 1
        except Exception as e:
            print(f"[{i}/{total}] ✗ {inp.name}: {e}", file=sys.stderr)
            errors.append((inp, str(e)))

    print(f"\nDone: {success}/{total} succeeded", end="")
    if errors:
        print(f", {len(errors)} failed")
        return 2
    print()
    return 0
