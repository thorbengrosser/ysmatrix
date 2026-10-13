"""YSTP01: the palette-indexed image/animation container the panel displays.

Layout (all integers little-endian), verified byte-for-byte against uploads
captured from the official app and confirmed on a real panel:

    0   6   magic "YSTP01"
    6   2   width
    8   2   height
    10  2   page (frame) count; >1 is an animation
    12  2   "len_valid" (the app always sends the panel width)
    14  1   bits per pixel: 1, 2, 4, 8 (palette) or 24 (raw RGB, no palette)
    15  3*2**bpp   palette as RGB triples (only when bpp <= 8; unused slots 0)
    ... pixel rows, top row first, each row padded to a whole byte,
        pixels packed LSB-first within a byte

The palette is built in first-seen order scanning every page top-to-bottom,
left-to-right. bpp steps 1 -> 2 -> 4 -> 8 as distinct colours exceed 2, 4, 16
and 256 respectively; beyond 256 colours the image is stored as 24 bpp.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Sequence

MAGIC = b"YSTP01"
HEADER_SIZE = 15


@dataclass
class Image:
    width: int
    height: int
    pages: list[bytes]  # each is width*height*3 bytes of RGB, top row first

    @property
    def animated(self) -> bool:
        return len(self.pages) > 1


def _bits_for(n_colors: int) -> int:
    if n_colors <= 2:
        return 1
    if n_colors <= 4:
        return 2
    if n_colors <= 16:
        return 4
    if n_colors <= 256:
        return 8
    return 24


def encode(pages: Sequence[bytes], width: int, height: int) -> bytes:
    """Encode one or more RGB pages (width*height*3 bytes each) as a YSTP01 blob."""
    if not pages:
        raise ValueError("need at least one page")
    expected = width * height * 3
    for p in pages:
        if len(p) != expected:
            raise ValueError(f"page is {len(p)} bytes, expected {expected} for {width}x{height} RGB")

    palette: dict[bytes, int] = {}
    for page in pages:
        for i in range(0, expected, 3):
            c = bytes(page[i : i + 3])
            if c not in palette:
                palette[c] = len(palette)
                if len(palette) > 256:
                    break
        if len(palette) > 256:
            break
    bpp = _bits_for(len(palette))

    out = bytearray(MAGIC)
    out += struct.pack("<HHHHB", width, height, len(pages), width, bpp)
    if bpp <= 8:
        pal = bytearray(3 * (1 << bpp))
        for color, idx in palette.items():
            pal[3 * idx : 3 * idx + 3] = color
        out += pal
        stride = (width * bpp + 7) // 8
        for page in pages:
            for y in range(height):
                row = bytearray(stride)
                for x in range(width):
                    o = (y * width + x) * 3
                    v = palette[bytes(page[o : o + 3])]
                    bit = x * bpp
                    row[bit // 8] |= v << (bit % 8)
                out += row
    else:
        for page in pages:
            out += page
    return bytes(out)


def decode(blob: bytes) -> Image:
    if blob[:6] != MAGIC:
        raise ValueError("not a YSTP01 blob")
    width, height, n_pages, _len_valid, bpp = struct.unpack_from("<HHHHB", blob, 6)
    off = HEADER_SIZE
    pages: list[bytes] = []
    if bpp <= 8:
        n = 1 << bpp
        pal = [bytes(blob[off + 3 * i : off + 3 * i + 3]) for i in range(n)]
        off += 3 * n
        stride = (width * bpp + 7) // 8
        mask = (1 << bpp) - 1
        for _ in range(n_pages):
            page = bytearray()
            for _y in range(height):
                row = blob[off : off + stride]
                off += stride
                for x in range(width):
                    bit = x * bpp
                    page += pal[(row[bit // 8] >> (bit % 8)) & mask]
            pages.append(bytes(page))
    else:
        size = width * height * 3
        for _ in range(n_pages):
            pages.append(bytes(blob[off : off + size]))
            off += size
    return Image(width, height, pages)


def apply_gamma(page: bytes, gamma: float) -> bytes:
    """The app's colour curve: out = 256*((v+.5)/256)**gamma - .5.

    The official app applies gamma 1.6 only when its "gray" option is set (default 1.0,
    i.e. no change), so encode() never applies it for you.
    """
    lut = bytes(max(0, min(255, int(256 * ((v + 0.5) / 256) ** gamma - 0.5))) for v in range(256))
    return page.translate(lut)


def from_pil(img, size: tuple[int, int] | None = None, *, gamma: float | None = None) -> Image:
    """Convert a Pillow image (animated GIFs yield one page per frame)."""
    from PIL import Image as PILImage, ImageSequence  # optional dependency

    frames = [f.copy() for f in ImageSequence.Iterator(img)] or [img]
    pages = []
    w = h = None
    for f in frames:
        f = f.convert("RGB")
        if size and f.size != size:
            f = f.resize(size, PILImage.NEAREST)
        w, h = f.size
        data = f.tobytes()
        pages.append(apply_gamma(data, gamma) if gamma else data)
    return Image(w, h, pages)
