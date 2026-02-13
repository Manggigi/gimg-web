from __future__ import annotations
"""GIMG CLI — main entry point with argparse subcommands."""
import argparse
import sys
from pathlib import Path

from . import __version__
from .utils import resolve_inputs, resolve_output, validate_input, ensure_parent, run_batch


def cmd_compress(args):
    from .compress import process_single
    inputs = resolve_inputs(args.input)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'compressed', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, quality=args.quality)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'compressed',
                     overwrite=args.overwrite, quality=args.quality)


def cmd_resize(args):
    from .resize import process_single
    inputs = resolve_inputs(args.input)
    kwargs = dict(width=args.width, height=args.height,
                  percentage=args.percentage, max_size=args.max_size)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'resized', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'resized',
                     overwrite=args.overwrite, **kwargs)


def cmd_crop(args):
    from .crop import process_single
    inputs = resolve_inputs(args.input)
    kwargs = dict(x=args.x, y=args.y, width=args.width, height=args.height, ratio=args.ratio)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'cropped', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'cropped',
                     overwrite=args.overwrite, **kwargs)


def cmd_rotate(args):
    from .rotate import process_single
    inputs = resolve_inputs(args.input)
    kwargs = dict(degrees=args.degrees, auto=args.auto)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'rotated', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'rotated',
                     overwrite=args.overwrite, **kwargs)


def cmd_convert(args):
    from .convert import process_single, FORMAT_MAP
    to_fmt = args.to.lower()
    if to_fmt not in FORMAT_MAP:
        print(f"Error: unsupported format '{args.to}'. Supported: {', '.join(FORMAT_MAP.keys())}", file=sys.stderr)
        return 1
    ext = FORMAT_MAP[to_fmt]
    inputs = resolve_inputs(args.input)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'converted', ext=ext, overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, to_format=to_fmt)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'converted',
                     ext=ext, overwrite=args.overwrite, to_format=to_fmt)


def cmd_metadata(args):
    from .metadata import process_single, view_metadata
    inputs = resolve_inputs(args.input)
    if args.strip:
        if len(inputs) == 1:
            validate_input(inputs[0])
            out = resolve_output(inputs[0], args.output, 'clean', overwrite=args.overwrite)
            ensure_parent(out)
            process_single(inputs[0], out, strip=True)
            print(f"✓ Stripped metadata: {inputs[0].name} → {out.name}")
            return 0
        return run_batch(inputs, process_single, args.output, 'clean',
                         overwrite=args.overwrite, strip=True)
    else:
        # View mode
        for inp in inputs:
            try:
                validate_input(inp)
                print(f"\n📷 {inp.name}:")
                process_single(inp, None, strip=False, view=True)
            except Exception as e:
                print(f"✗ {inp.name}: {e}", file=sys.stderr)
        return 0


def cmd_watermark(args):
    from .watermark import process_single
    if not args.text and not args.image_wm:
        print("Error: provide -t TEXT or -i IMAGE for watermark", file=sys.stderr)
        return 1
    inputs = resolve_inputs(args.input)
    kwargs = dict(text=args.text, image_wm=args.image_wm, pos=args.pos,
                  opacity=args.opacity, size=args.size, color=args.color,
                  tile=args.tile, angle=args.angle)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'watermarked', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'watermarked',
                     overwrite=args.overwrite, **kwargs)


def cmd_blur_face(args):
    from .blur_face import process_single
    inputs = resolve_inputs(args.input)
    kwargs = dict(strength=args.strength, largest=args.largest, region=args.region)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'blurred', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'blurred',
                     overwrite=args.overwrite, **kwargs)


def cmd_meme(args):
    from .meme import process_single
    if not args.top and not args.bottom:
        print("Error: provide --top and/or --bottom text", file=sys.stderr)
        return 1
    inputs = resolve_inputs(args.input)
    kwargs = dict(top=args.top, bottom=args.bottom, size=args.size, no_caps=args.no_caps)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'meme', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'meme',
                     overwrite=args.overwrite, **kwargs)


def cmd_remove_bg(args):
    from .remove_bg import process_single
    inputs = resolve_inputs(args.input)
    kwargs = dict(model=args.model, alpha_matting=args.alpha_matting)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'nobg', ext='.png', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'nobg',
                     ext='.png', overwrite=args.overwrite, **kwargs)


def cmd_upscale(args):
    from .upscale import process_single
    inputs = resolve_inputs(args.input)
    kwargs = dict(scale=args.scale, width=args.width, height=args.height, sharpen=args.sharpen)
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'upscaled', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'upscaled',
                     overwrite=args.overwrite, **kwargs)


def cmd_html_to_img(args):
    from .html_to_img import process_single, _default_output_name
    source = args.source
    fmt = args.format
    if args.output:
        out = Path(args.output)
    else:
        out = Path.cwd() / _default_output_name(source, fmt)
    ensure_parent(out)
    process_single(source, out, width=args.width, height=args.height,
                   full_page=args.full_page, fmt=fmt, quality=args.quality)
    print(f"✓ {source} → {out.name}")
    return 0


def cmd_edit(args):
    from .editor import process_single, VALID_FILTERS
    # Validate at least one edit flag is provided
    has_edit = any([
        args.brightness is not None, args.contrast is not None,
        args.saturation is not None, args.sharpness is not None,
        args.hue is not None, args.filter, args.flip, args.auto_enhance,
        args.border, args.frame, args.thumbnail,
    ])
    if not has_edit:
        print("Error: provide at least one edit flag (e.g. --brightness, --filter, --flip)", file=sys.stderr)
        return 1
    inputs = resolve_inputs(args.input)
    kwargs = dict(
        brightness=args.brightness, contrast=args.contrast,
        saturation=args.saturation, sharpness=args.sharpness,
        hue=args.hue, filter_name=args.filter, flip=args.flip,
        auto_enhance=args.auto_enhance, border=args.border,
        border_color=args.border_color, frame=args.frame,
        thumbnail=args.thumbnail,
    )
    if len(inputs) == 1:
        validate_input(inputs[0])
        out = resolve_output(inputs[0], args.output, 'edited', overwrite=args.overwrite)
        ensure_parent(out)
        process_single(inputs[0], out, **kwargs)
        print(f"✓ {inputs[0].name} → {out.name}")
        return 0
    return run_batch(inputs, process_single, args.output, 'edited',
                     overwrite=args.overwrite, **kwargs)


def cmd_info(args):
    from .info import process_single
    inputs = resolve_inputs(args.input)
    for inp in inputs:
        try:
            validate_input(inp)
            print(f"\n📷 {inp.name}:")
            process_single(inp)
        except Exception as e:
            print(f"✗ {inp.name}: {e}", file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog='gimg',
        description="GIMG — Gigi's Image Toolkit. A local CLI clone of iLoveIMG.",
    )
    parser.add_argument('--version', action='version', version=f'gimg {__version__}')
    sub = parser.add_subparsers(dest='command', help='Available tools')

    # --- compress ---
    p = sub.add_parser('compress', help='Compress images (reduce file size)')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('-q', '--quality', type=int, default=80, help='Quality 1-100 (default: 80)')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true', help='Allow overwriting input file')
    p.set_defaults(func=cmd_compress)

    # --- resize ---
    p = sub.add_parser('resize', help='Resize images')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('-w', '--width', type=int, help='Target width in pixels')
    p.add_argument('-H', '--height', type=int, help='Target height in pixels')
    p.add_argument('-p', '--percentage', type=float, help='Scale by percentage')
    p.add_argument('--max-size', type=int, help='Fit within max dimension')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_resize)

    # --- crop ---
    p = sub.add_parser('crop', help='Crop images')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('-x', type=int, default=0, help='Left offset (default: 0)')
    p.add_argument('-y', type=int, default=0, help='Top offset (default: 0)')
    p.add_argument('-w', '--width', type=int, help='Crop width')
    p.add_argument('-H', '--height', type=int, help='Crop height')
    p.add_argument('--ratio', help='Aspect ratio (e.g. 16:9)')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_crop)

    # --- rotate ---
    p = sub.add_parser('rotate', help='Rotate images')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('-d', '--degrees', type=float, help='Rotation degrees (clockwise)')
    p.add_argument('--auto', action='store_true', help='Auto-orient from EXIF')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_rotate)

    # --- convert ---
    p = sub.add_parser('convert', help='Convert image format')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('--to', required=True, help='Target format (jpg, png, webp, gif, bmp, tiff)')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_convert)

    # --- metadata ---
    p = sub.add_parser('metadata', help='View or strip EXIF metadata')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('--strip', action='store_true', help='Strip all metadata')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_metadata)

    # --- info ---
    p = sub.add_parser('info', help='Show image info (dimensions, format, size, mode)')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.set_defaults(func=cmd_info)

    # --- watermark ---
    p = sub.add_parser('watermark', help='Add text or image watermark')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('-t', '--text', help='Watermark text')
    p.add_argument('-i', '--image-wm', help='Watermark image file')
    p.add_argument('--pos', default='bottom-right',
                   choices=['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
                   help='Position (default: bottom-right)')
    p.add_argument('--opacity', type=float, default=0.3, help='Opacity 0.0-1.0 (default: 0.3)')
    p.add_argument('--size', type=int, help='Font size (default: auto)')
    p.add_argument('--color', default='white', help='Text color (default: white)')
    p.add_argument('--tile', action='store_true', help='Tile watermark across image')
    p.add_argument('--angle', type=float, default=0, help='Rotation angle for text (default: 0)')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_watermark)

    # --- blur-face ---
    p = sub.add_parser('blur-face', help='Detect and blur faces')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('--strength', type=int, default=25, help='Blur strength (default: 25)')
    p.add_argument('--largest', action='store_true', help='Blur only the largest face')
    p.add_argument('--region', help='Manual region x,y,w,h (skip face detection)')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_blur_face)

    # --- remove-bg ---
    p = sub.add_parser('remove-bg', help='Remove image background (AI)')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('--model', default='u2net', choices=['u2net', 'u2netp', 'isnet-general-use'],
                   help='AI model (default: u2net)')
    p.add_argument('--alpha-matting', action='store_true', help='Use alpha matting for cleaner edges')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_remove_bg)

    # --- upscale ---
    p = sub.add_parser('upscale', help='Upscale images (LANCZOS)')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('-s', '--scale', type=int, default=2, choices=[2, 4], help='Scale factor (default: 2)')
    p.add_argument('-w', '--width', type=int, help='Target width')
    p.add_argument('-H', '--height', type=int, help='Target height')
    p.add_argument('--sharpen', action=argparse.BooleanOptionalAction, default=True,
                   help='Sharpen after upscale (default: on)')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_upscale)

    # --- html-to-img ---
    p = sub.add_parser('html-to-img', help='Screenshot a URL or HTML file')
    p.add_argument('source', help='URL (http/https) or local HTML file')
    p.add_argument('--width', type=int, default=1280, help='Viewport width (default: 1280)')
    p.add_argument('--height', type=int, help='Viewport height')
    p.add_argument('--full-page', action=argparse.BooleanOptionalAction, default=True,
                   help='Capture full scrollable page (default: on)')
    p.add_argument('--format', choices=['png', 'jpg'], default='png', help='Output format')
    p.add_argument('--quality', type=int, default=85, help='JPEG quality (default: 85)')
    p.add_argument('-o', '--output', help='Output file path')
    p.set_defaults(func=cmd_html_to_img)

    # --- meme ---
    p = sub.add_parser('meme', help='Add meme text (Impact style)')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('--top', help='Top text')
    p.add_argument('--bottom', help='Bottom text')
    p.add_argument('--size', type=int, help='Font size (default: auto)')
    p.add_argument('--no-caps', action='store_true', help='Disable auto uppercase')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_meme)

    # --- edit ---
    p = sub.add_parser('edit', help='Photo editor (adjustments, filters, borders, frames)')
    p.add_argument('input', help='Image file, folder, or glob pattern')
    p.add_argument('--brightness', type=float, help='Brightness multiplier (1.0 = unchanged)')
    p.add_argument('--contrast', type=float, help='Contrast multiplier (1.0 = unchanged)')
    p.add_argument('--saturation', type=float, help='Saturation multiplier (0 = grayscale, 1.0 = unchanged)')
    p.add_argument('--sharpness', type=float, help='Sharpness multiplier (1.0 = unchanged)')
    p.add_argument('--hue', type=float, help='Hue shift in degrees (-180 to 180)')
    p.add_argument('--filter', choices=[
        'grayscale', 'sepia', 'blur', 'emboss', 'contour', 'sharpen', 'smooth',
        'invert', 'posterize', 'solarize', 'vintage', 'dramatic', 'warm', 'cool',
    ], help='Apply a preset filter')
    p.add_argument('--border', type=int, help='Solid border width in pixels')
    p.add_argument('--border-color', default='white', help='Border color (default: white)')
    p.add_argument('--frame', choices=['polaroid', 'rounded', 'shadow'], help='Preset frame style')
    p.add_argument('--flip', choices=['horizontal', 'vertical'], help='Flip image')
    p.add_argument('--auto-enhance', action='store_true', help='Auto adjust brightness/contrast')
    p.add_argument('--thumbnail', type=int, help='Create square thumbnail of given size')
    p.add_argument('-o', '--output', help='Output file or directory')
    p.add_argument('--overwrite', action='store_true')
    p.set_defaults(func=cmd_edit)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        rc = args.func(args)
        sys.exit(rc or 0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
