from __future__ import annotations
"""Detect and blur faces in images."""
from pathlib import Path
import numpy as np
from PIL import Image
from .utils import open_image


def _ensure_odd(n: int) -> int:
    return n if n % 2 == 1 else n + 1


def process_single(input_path: Path, output_path: Path, *,
                   strength: int = 25, largest: bool = False,
                   region: str | None = None, **kwargs) -> None:
    import cv2

    img = open_image(input_path).convert('RGB')
    arr = np.array(img)
    arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    ksize = _ensure_odd(max(3, strength))

    if region:
        # Manual region: x,y,w,h
        parts = [int(v.strip()) for v in region.split(',')]
        if len(parts) != 4:
            raise ValueError("Region must be x,y,w,h (e.g. 100,100,200,200)")
        x, y, rw, rh = parts
        roi = arr_bgr[y:y+rh, x:x+rw]
        arr_bgr[y:y+rh, x:x+rw] = cv2.GaussianBlur(roi, (ksize, ksize), 0)
    else:
        # Face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        gray = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            print(f"⚠ No faces detected in {input_path.name} — saving unchanged")
        else:
            if largest and len(faces) > 1:
                faces = [max(faces, key=lambda f: f[2] * f[3])]
            for (x, y, fw, fh) in faces:
                roi = arr_bgr[y:y+fh, x:x+fw]
                arr_bgr[y:y+fh, x:x+fw] = cv2.GaussianBlur(roi, (ksize, ksize), 0)

    result = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2RGB)
    out_img = Image.fromarray(result)

    out_ext = output_path.suffix.lower()
    if out_ext in ('.jpg', '.jpeg') and out_img.mode == 'RGBA':
        out_img = out_img.convert('RGB')
    out_img.save(output_path)
