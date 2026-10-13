"""Turn files and Pillow images into what the panel accepts.

Stills become a YSTP01 blob (see :mod:`ysmatrix.ystp`). Animations are sent as a GIF file,
exactly like the official app does; the panel decodes the GIF itself.
"""
from __future__ import annotations

import io
from enum import Enum
from pathlib import Path
from typing import Union

from PIL import Image, ImageOps, ImageSequence

from . import ystp

ImageSource = Union[str, Path, bytes, Image.Image]


class Resize(str, Enum):
    FIT = "fit"  # keep aspect ratio, pad with black
    FILL = "fill"  # keep aspect ratio, crop the overflow
    STRETCH = "stretch"  # ignore aspect ratio


def open_image(source: ImageSource) -> Image.Image:
    if isinstance(source, Image.Image):
        return source
    if isinstance(source, (bytes, bytearray)):
        return Image.open(io.BytesIO(source))
    return Image.open(source)


def _resize(frame: Image.Image, size: tuple[int, int], mode: Resize) -> Image.Image:
    frame = frame.convert("RGB")
    if frame.size == size:
        return frame
    if mode == Resize.STRETCH:
        return frame.resize(size, Image.LANCZOS)
    if mode == Resize.FILL:
        return ImageOps.fit(frame, size, Image.LANCZOS)
    canvas = Image.new("RGB", size)
    fitted = ImageOps.contain(frame, size, Image.LANCZOS)
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def is_animated(img: Image.Image) -> bool:
    return getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1


def to_still(source: ImageSource, size: tuple[int, int], mode: Resize = Resize.FIT) -> bytes:
    """A YSTP01 blob of the first frame, resized to the panel."""
    frame = _resize(open_image(source), size, Resize(mode))
    return ystp.encode([frame.tobytes()], *size)


def to_gif(source: ImageSource, size: tuple[int, int], mode: Resize = Resize.FIT) -> tuple[bytes, float]:
    """GIF bytes sized for the panel, plus the animation's length in seconds.

    A GIF that already has the panel's size is passed through unchanged.
    """
    raw = source if isinstance(source, (bytes, bytearray)) else None
    if raw is None and isinstance(source, (str, Path)):
        raw = Path(source).read_bytes()
    img = open_image(raw if raw is not None else source)
    durations = [f.info.get("duration", 100) or 100 for f in ImageSequence.Iterator(img)]
    seconds = sum(durations) / 1000
    if raw is not None and img.format == "GIF" and img.size == size:
        return bytes(raw), seconds
    frames = [_resize(f.copy(), size, Resize(mode)) for f in ImageSequence.Iterator(img)]
    out = io.BytesIO()
    frames[0].save(out, "GIF", save_all=True, append_images=frames[1:], loop=0, duration=durations)
    return out.getvalue(), seconds
