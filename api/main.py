"""GIMG Web API — FastAPI wrapper for all 14 gimg CLI tools."""
from __future__ import annotations

import os
import sys
import tempfile
import shutil
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Ensure gimg package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gimg.utils import detect_format
from gimg import compress, resize, crop, rotate, convert, metadata, info, watermark, blur_face, meme, editor, upscale

try:
    from gimg import remove_bg as remove_bg_mod
    HAS_REMBG = True
except Exception:
    HAS_REMBG = False

MAX_UPLOAD = 20 * 1024 * 1024  # 20 MB

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="GIMG Web API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOOLS = [
    {"name": "compress", "description": "Compress images by reducing quality"},
    {"name": "resize", "description": "Resize images by dimensions or percentage"},
    {"name": "crop", "description": "Crop images by coordinates or aspect ratio"},
    {"name": "rotate", "description": "Rotate images by degrees or auto-orient"},
    {"name": "convert", "description": "Convert images between formats"},
    {"name": "info", "description": "Get image info (dimensions, format, size, mode)"},
    {"name": "metadata", "description": "View or strip EXIF metadata"},
    {"name": "watermark", "description": "Add text or image watermarks"},
    {"name": "blur-face", "description": "Detect and blur faces"},
    {"name": "remove-bg", "description": "Remove image background"},
    {"name": "upscale", "description": "Upscale images with LANCZOS resampling"},
    {"name": "meme", "description": "Add meme text (top/bottom)"},
    {"name": "edit", "description": "Photo editor: brightness, contrast, filters, borders, etc."},
    {"name": "html-to-img", "description": "Screenshot a URL (not available in web mode)"},
]

ALLOWED_MAGIC = {
    b'\xff\xd8\xff': 'jpg',
    b'\x89PNG': 'png',
    b'GIF8': 'gif',
    b'RIFF': 'webp',
    b'BM': 'bmp',
    b'II': 'tiff',
    b'MM': 'tiff',
}


def _validate_upload(data: bytes) -> None:
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, f"File too large (max {MAX_UPLOAD // 1024 // 1024}MB)")
    for magic in ALLOWED_MAGIC:
        if data[:len(magic)] == magic:
            return
    raise HTTPException(415, "Unsupported image format")


def _save_upload(data: bytes, suffix: str = ".img") -> Path:
    """Save upload bytes to a temp file, return path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.write(fd, data)
    os.close(fd)
    return Path(path)


def _output_path(input_path: Path, new_ext: str | None = None) -> Path:
    ext = new_ext or input_path.suffix or ".png"
    fd, path = tempfile.mkstemp(suffix=ext)
    os.close(fd)
    return Path(path)


def _guess_ext(filename: str | None) -> str:
    if filename:
        ext = Path(filename).suffix.lower()
        if ext:
            return ext
    return ".jpg"


def _file_response(path: Path, filename: str = "output") -> FileResponse:
    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        filename=filename + path.suffix,
        background=None,  # Don't delete before sending
    )


# ── Health & Tools ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/tools")
async def tools():
    return TOOLS


# ── Compress ─────────────────────────────────────────────────────────────────

@app.post("/api/compress")
@limiter.limit("30/minute")
async def api_compress(request: Request, file: UploadFile = File(...), quality: int = Form(80)):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        compress.process_single(inp, out, quality=quality)
        return _file_response(out, "compressed")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Resize ───────────────────────────────────────────────────────────────────

@app.post("/api/resize")
@limiter.limit("30/minute")
async def api_resize(
    request: Request,
    file: UploadFile = File(...),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    percentage: Optional[float] = Form(None),
    max_size: Optional[int] = Form(None),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        resize.process_single(inp, out, width=width, height=height, percentage=percentage, max_size=max_size)
        return _file_response(out, "resized")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Crop ─────────────────────────────────────────────────────────────────────

@app.post("/api/crop")
@limiter.limit("30/minute")
async def api_crop(
    request: Request,
    file: UploadFile = File(...),
    x: Optional[int] = Form(None),
    y: Optional[int] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    ratio: Optional[str] = Form(None),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        kwargs = {}
        if x is not None: kwargs['x'] = x
        if y is not None: kwargs['y'] = y
        if width is not None: kwargs['width'] = width
        if height is not None: kwargs['height'] = height
        if ratio is not None: kwargs['ratio'] = ratio
        crop.process_single(inp, out, **kwargs)
        return _file_response(out, "cropped")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Rotate ───────────────────────────────────────────────────────────────────

@app.post("/api/rotate")
@limiter.limit("30/minute")
async def api_rotate(
    request: Request,
    file: UploadFile = File(...),
    degrees: Optional[float] = Form(None),
    auto: bool = Form(False),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        rotate.process_single(inp, out, degrees=degrees, auto=auto)
        return _file_response(out, "rotated")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Convert ──────────────────────────────────────────────────────────────────

@app.post("/api/convert")
@limiter.limit("30/minute")
async def api_convert(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form(...),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    target_ext = f".{format.lower().strip('.')}"
    out = _output_path(inp, target_ext)
    try:
        convert.process_single(inp, out, to_format=format)
        return _file_response(out, "converted")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Info ─────────────────────────────────────────────────────────────────────

@app.post("/api/info")
@limiter.limit("30/minute")
async def api_info(request: Request, file: UploadFile = File(...)):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    try:
        result = info.show_info(inp)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Metadata ─────────────────────────────────────────────────────────────────

@app.post("/api/metadata")
@limiter.limit("30/minute")
async def api_metadata(
    request: Request,
    file: UploadFile = File(...),
    strip: bool = Form(False),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    if strip:
        out = _output_path(inp)
        try:
            metadata.process_single(inp, out, strip=True)
            return _file_response(out, "stripped")
        except Exception as e:
            out.unlink(missing_ok=True)
            raise HTTPException(500, str(e))
        finally:
            inp.unlink(missing_ok=True)
    else:
        try:
            result = metadata.view_metadata(inp)
            return JSONResponse(result)
        except Exception as e:
            raise HTTPException(500, str(e))
        finally:
            inp.unlink(missing_ok=True)


# ── Watermark ────────────────────────────────────────────────────────────────

@app.post("/api/watermark")
@limiter.limit("30/minute")
async def api_watermark(
    request: Request,
    file: UploadFile = File(...),
    text: Optional[str] = Form(None),
    position: str = Form("bottom-right"),
    opacity: float = Form(0.3),
    size: Optional[int] = Form(None),
    color: str = Form("white"),
    tile: bool = Form(False),
    angle: float = Form(0),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        watermark.process_single(
            inp, out, text=text, pos=position, opacity=opacity,
            size=size, color=color, tile=tile, angle=angle,
        )
        return _file_response(out, "watermarked")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Blur Face ────────────────────────────────────────────────────────────────

@app.post("/api/blur-face")
@limiter.limit("30/minute")
async def api_blur_face(
    request: Request,
    file: UploadFile = File(...),
    strength: int = Form(25),
    region: Optional[str] = Form(None),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        blur_face.process_single(inp, out, strength=strength, region=region)
        return _file_response(out, "blurred")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Remove BG ────────────────────────────────────────────────────────────────

@app.post("/api/remove-bg")
@limiter.limit("30/minute")
async def api_remove_bg(
    request: Request,
    file: UploadFile = File(...),
    model: str = Form("u2net"),
):
    if not HAS_REMBG:
        raise HTTPException(501, "remove-bg not available (rembg not installed)")
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp, ".png")
    try:
        remove_bg_mod.process_single(inp, out, model=model)
        return _file_response(out, "nobg")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Upscale ──────────────────────────────────────────────────────────────────

@app.post("/api/upscale")
@limiter.limit("30/minute")
async def api_upscale(
    request: Request,
    file: UploadFile = File(...),
    scale: int = Form(2),
    sharpen: bool = Form(True),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        upscale.process_single(inp, out, scale=scale, sharpen=sharpen)
        return _file_response(out, "upscaled")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Meme ─────────────────────────────────────────────────────────────────────

@app.post("/api/meme")
@limiter.limit("30/minute")
async def api_meme(
    request: Request,
    file: UploadFile = File(...),
    top: Optional[str] = Form(None),
    bottom: Optional[str] = Form(None),
    size: Optional[int] = Form(None),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        meme.process_single(inp, out, top=top, bottom=bottom, size=size)
        return _file_response(out, "meme")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── Edit ─────────────────────────────────────────────────────────────────────

@app.post("/api/edit")
@limiter.limit("30/minute")
async def api_edit(
    request: Request,
    file: UploadFile = File(...),
    brightness: Optional[float] = Form(None),
    contrast: Optional[float] = Form(None),
    saturation: Optional[float] = Form(None),
    sharpness: Optional[float] = Form(None),
    filter: Optional[str] = Form(None),
    border: Optional[int] = Form(None),
    border_color: Optional[str] = Form(None),
    frame: Optional[str] = Form(None),
    flip: Optional[str] = Form(None),
    auto_enhance: bool = Form(False),
    thumbnail: Optional[int] = Form(None),
):
    data = await file.read()
    _validate_upload(data)
    ext = _guess_ext(file.filename)
    inp = _save_upload(data, ext)
    out = _output_path(inp)
    try:
        kwargs = {}
        if brightness is not None: kwargs['brightness'] = brightness
        if contrast is not None: kwargs['contrast'] = contrast
        if saturation is not None: kwargs['saturation'] = saturation
        if sharpness is not None: kwargs['sharpness'] = sharpness
        if filter is not None: kwargs['filter_name'] = filter
        if border is not None: kwargs['border'] = border
        if border_color is not None: kwargs['border_color'] = border_color
        if frame is not None: kwargs['frame'] = frame
        if flip is not None: kwargs['flip'] = flip
        if auto_enhance: kwargs['auto_enhance'] = True
        if thumbnail is not None: kwargs['thumbnail'] = thumbnail
        editor.process_single(inp, out, **kwargs)
        return _file_response(out, "edited")
    except Exception as e:
        out.unlink(missing_ok=True)
        raise HTTPException(500, str(e))
    finally:
        inp.unlink(missing_ok=True)


# ── HTML to Image ────────────────────────────────────────────────────────────

@app.post("/api/html-to-img")
@limiter.limit("30/minute")
async def api_html_to_img(request: Request):
    raise HTTPException(501, "html-to-img is not available in web mode (requires Chromium)")


# ── Serve Frontend ───────────────────────────────────────────────────────────

frontend_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
