from __future__ import annotations
"""Remove background from images using rembg."""
from pathlib import Path


def process_single(input_path: Path, output_path: Path, *, model: str = 'u2net',
                   alpha_matting: bool = False) -> None:
    try:
        from rembg import remove
    except ImportError:
        raise ImportError("rembg is required: pip install rembg")

    from .utils import open_image
    img = open_image(input_path)

    kwargs = dict(session=None)
    if alpha_matting:
        kwargs['alpha_matting'] = True
        kwargs['alpha_matting_foreground_threshold'] = 240
        kwargs['alpha_matting_background_threshold'] = 10

    # rembg accepts model name
    try:
        from rembg import new_session
        session = new_session(model)
        kwargs['session'] = session
    except Exception:
        pass

    result = remove(img, **kwargs)
    # Always save as PNG for transparency
    out = Path(str(output_path))
    if out.suffix.lower() != '.png':
        out = out.with_suffix('.png')
    result.save(out)
