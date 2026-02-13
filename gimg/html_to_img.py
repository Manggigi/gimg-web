from __future__ import annotations
"""Capture screenshots of URLs or local HTML files using Playwright."""
import re
from pathlib import Path
from urllib.parse import urlparse


def _validate_url(url: str) -> str:
    """Validate and sanitize URL. Only http/https allowed."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Unsupported URL scheme '{parsed.scheme}'. Only http:// and https:// allowed.")
    return url


def _default_output_name(source: str, fmt: str) -> str:
    """Generate default output filename from source."""
    p = Path(source)
    if p.exists():
        return f"screenshot_{p.stem}.{fmt}"
    parsed = urlparse(source)
    domain = parsed.hostname or 'page'
    domain = re.sub(r'[^\w.-]', '_', domain)
    return f"screenshot_{domain}.{fmt}"


def process_single(source: str, output_path: Path, *, width: int = 1280,
                   height: int | None = None, full_page: bool = True,
                   fmt: str = 'png', quality: int = 85) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "playwright is required: pip install playwright && python -m playwright install chromium"
        )

    # Determine URL
    p = Path(source)
    if p.exists() and p.is_file():
        url = f"file://{p.resolve()}"
    else:
        url = _validate_url(source)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        vp = {'width': width, 'height': height or 720}
        page = browser.new_page(viewport=vp)
        page.goto(url, wait_until='networkidle', timeout=30000)

        screenshot_kwargs = {'path': str(output_path), 'full_page': full_page}
        if fmt == 'jpg' or fmt == 'jpeg':
            screenshot_kwargs['type'] = 'jpeg'
            screenshot_kwargs['quality'] = quality
        else:
            screenshot_kwargs['type'] = 'png'

        page.screenshot(**screenshot_kwargs)
        browser.close()
