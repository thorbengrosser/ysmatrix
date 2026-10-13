"""Payload builders: pure functions that return the bytes for one command.

Nothing here talks to Bluetooth; pass the result to ``AsyncClient.send``/``query`` or use
the high-level client methods. Every builder states how much we know about it:

* **verified**: seen working on a real panel (and, where noted, byte-identical to the
  official app's traffic)
* **inferred**: built from studying the official app, accepted by the panel, but its
  meaning is only partly confirmed
* **unsupported**: the tested panel (firmware V2.9.1) rejects it (ack error 3) or ignores it

See ``docs/status.md`` for the full table.
"""
from __future__ import annotations

import hashlib
import struct
import time
from datetime import datetime
from typing import Iterable, Sequence

from .framing import tlv

RGB = tuple[int, int, int]

# --- tags ----------------------------------------------------------------------------

TAG_POWER = 4
TAG_SET_TIME = 5
TAG_BRIGHTNESS = 6
TAG_DELETE = 8
TAG_PROGRAM_FLAG = 9
TAG_DEVICE_INFO = 10
TAG_PROGRAM = 12
TAG_RECT = 13
TAG_ITEM = 14
TAG_ITEM_TYPE = 17
TAG_CHUNK_INFO = 18
TAG_CHUNK_DATA = 19
TAG_ANIMATION = 20
TAG_PANEL_PARAMS = 27
TAG_PROGRAM_TIMING = 28
TAG_RECT_GEOMETRY = 29
TAG_ROTATE = 47
TAG_GAME = 48
TAG_DRAW = 50
TAG_BUILTIN = 51
TAG_PROGRAM_KEY = 53
TAG_PLAY = 54
TAG_TRANSITION = 56
TAG_CHANNEL_ORDER = 57
TAG_MIRROR = 58

MAX_SLOTS = 60  # program slots 0..59
CHUNK_SIZE = 960  # bytes of image/text data per upload frame

ITEM_TEXT = 6
ITEM_GRAPHIC = 10

ANIM_SCROLL_LEFT = 0
ANIM_STATIC = 1

PLAY_LOOP = 0
PLAY_SINGLE = 1
PLAY_INDEX_NONE = 255

GAME_TETRIS = 0
GAME_SNAKE = 1
GAME_DRAW = 16  # live-drawing mode used by the official app's drawing board
GAME_KEYS = {"left": 37, "up": 38, "right": 39, "down": 40,
             "start": 115, "pause": 112, "done": 100, "exit": 101}

_ALIGN = {"left": 0, "top": 0, "center": 1, "right": 2, "bottom": 2}
_CLOCK_FIELDS = {"{YYYY}": (4, 0), "{YY}": (2, 0), "{MM}": (2, 1), "{DD}": (2, 2),
                 "{hh}": (2, 3), "{mm}": (2, 4), "{ss}": (2, 5)}


def _kv(tag: int, value: int) -> bytes:
    return bytes([tag, 1, value])


# --- settings -------------------------------------------------------------------------


def power(on: bool) -> bytes:
    """Panel on/off. **verified** (byte-identical to the app)."""
    return bytes([TAG_POWER, 2, 0, 1 if on else 0])


def brightness(level: int) -> bytes:
    """Brightness 1-15. **verified** (byte-identical to the app)."""
    if not 1 <= level <= 15:
        raise ValueError("brightness must be 1-15")
    return bytes([TAG_BRIGHTNESS, 2, 0, level])


def rotate(quarter_turns: int) -> bytes:
    """Absolute display rotation, n x 90 degrees clockwise (0-3). Stored on the panel. **verified**"""
    return bytes([TAG_ROTATE, 1, quarter_turns % 4])


def set_time(when: datetime) -> bytes:
    """Set the panel's clock. **verified** (read back with the time query)."""
    return (bytes([TAG_SET_TIME, 9]) + (when.year - 2000).to_bytes(2, "little")
            + bytes([when.month, when.day, when.hour, when.minute, when.second])
            + (when.microsecond // 1000).to_bytes(2, "little"))


# --- playback --------------------------------------------------------------------------


def play(slot: int) -> bytes:
    """Show one stored slot and stay on it. **verified** (byte-identical to the app)."""
    return bytes([TAG_PLAY, 2 + MAX_SLOTS, PLAY_SINGLE, slot, *range(MAX_SLOTS)])


def play_loop(slots: Iterable[int]) -> bytes:
    """Cycle through these slots, each for its own play time. **verified**"""
    ids = list(slots)
    return bytes([TAG_PLAY, 2 + len(ids), PLAY_LOOP, PLAY_INDEX_NONE, *ids])


def delete_slot(slot: int) -> bytes:
    """Delete one stored program. **inferred** (the app sends this as the first part of every upload)."""
    return bytes([TAG_DELETE, 2, 0, slot])


# --- program upload (images, GIFs, text) -------------------------------------------------


def _prefix(slot: int, item: bool = False) -> bytes:
    out = _kv(TAG_PROGRAM_FLAG, 1) + _kv(TAG_PROGRAM, slot)
    return out + _kv(TAG_RECT, 0) + _kv(TAG_ITEM, 0) if item else out


def program_create(slot: int, width: int, height: int, *, loops: int = 1, play_seconds: int = 3) -> bytes:
    """First upload frame: delete the slot, declare a program with one full-panel region. **verified**

    ``play_seconds`` is how long the program shows before a loop playlist moves on.
    """
    return (delete_slot(slot) + _prefix(slot)
            + bytes([TAG_PROGRAM_TIMING, 6, 0, 0]) + struct.pack("<HH", loops, play_seconds)
            + _kv(TAG_RECT, 0) + bytes([TAG_RECT_GEOMETRY, 9]) + struct.pack("<HHHH", 0, 0, width, height)
            + b"\x00")


def graphic_header(slot: int, *, animation: int = ANIM_STATIC, speed: int = 13, stay: int = 3,
                   loops: int = 1) -> bytes:
    """Second upload frame for an image/GIF item. **verified** (defaults are the app's)."""
    return (_prefix(slot, item=True) + bytes([TAG_ANIMATION, 3, animation, speed, stay])
            + bytes([TAG_ITEM_TYPE, 4, 0]) + loops.to_bytes(2, "little") + bytes([ITEM_GRAPHIC]))


def text_header(slot: int, *, animation: int = ANIM_SCROLL_LEFT, speed: int = 9, stay: int = 3,
                gap: int = 64, size: int = 16, loops: int = 1) -> bytes:
    """Second upload frame for a text item. **verified** (scroll and static; speed scale inferred)."""
    return (_prefix(slot, item=True) + bytes([TAG_ANIMATION, 3, animation, speed, stay])
            + bytes([TAG_ITEM_TYPE, 10, 0]) + loops.to_bytes(2, "little")
            + bytes([ITEM_TEXT, 1, 0, size, 0]) + gap.to_bytes(2, "little"))


def text_body(text: str, *, color: RGB = (255, 0, 0), background: RGB = (0, 0, 0), size: int = 16,
              align: str = "left", valign: str = "top", clock_fields: bool = False) -> bytes:
    """Data for a text item: alignment, colours and font, then the text. **verified**

    With ``clock_fields`` the placeholders {YYYY} {YY} {MM} {DD} {hh} {mm} {ss} become live
    fields the panel updates itself. Text is encoded as GB18030 (same as ASCII for ASCII text).
    """
    body = text.encode("gb18030", errors="replace")
    if clock_fields:
        for name, (digits, field) in _CLOCK_FIELDS.items():
            body = body.replace(name.encode(), bytes([6, digits, field]))
    return (bytes([3, 0, _ALIGN[valign], 3, 1, _ALIGN[align]]) + bytes([0, *color, *background])
            + bytes([1, 1, 0, size]) + body)


def data_chunks(slot: int, data: bytes) -> list[bytes]:
    """Upload frames 3..n: ``data`` in 960-byte pieces, each tagged with count/index. **verified**"""
    n = max(1, (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE)
    return [_prefix(slot, item=True) + bytes([TAG_CHUNK_INFO, 7]) + struct.pack("<HHH", n, i, CHUNK_SIZE)
            + b"\x00" + tlv(TAG_CHUNK_DATA, data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]) for i in range(n)]


def slot_id_prefix(slot: int) -> int:
    """The u32 the app puts before the content key: slot+1 as decimal digits, read as hex. **verified**"""
    return int.from_bytes(bytes.fromhex((str(slot + 1) + "0000000")[:8]), "little")


def content_key(data: bytes) -> bytes:
    """16-byte content key (MD5 of the data as spaced hex). The panel stores it but does not check it."""
    return hashlib.md5(" ".join(f"{b:02x}" for b in data).encode()).digest()


def program_commit(slot: int, key: bytes, *, prefix: int | None = None, timestamp: int | None = None) -> bytes:
    """Last upload frame: ``[slot][u32 prefix][16-byte key][u32 unix time]``. **verified**"""
    if len(key) != 16:
        raise ValueError("key must be 16 bytes")
    prefix = slot_id_prefix(slot) if prefix is None else prefix
    ts = int(time.time()) if timestamp is None else timestamp
    return tlv(TAG_PROGRAM_KEY, bytes([slot]) + struct.pack("<I", prefix) + key + struct.pack("<I", ts))


def graphic_upload(slot: int, data: bytes, width: int, height: int, *, loops: int = 1,
                   play_seconds: int | None = None, stay: int = 3, key: bytes | None = None,
                   prefix: int | None = None, timestamp: int | None = None) -> list[bytes]:
    """Every payload, in order, to store a YSTP01 image or a raw GIF in ``slot``. **verified**"""
    return [program_create(slot, width, height, loops=loops,
                           play_seconds=loops * stay if play_seconds is None else play_seconds),
            graphic_header(slot, stay=stay),
            *data_chunks(slot, data),
            program_commit(slot, key or content_key(data), prefix=prefix, timestamp=timestamp)]


def text_upload(slot: int, body: bytes, width: int, height: int, *, scroll: bool = True, speed: int = 9,
                size: int = 16, play_seconds: int = 10) -> list[bytes]:
    """Every payload, in order, to store a text (or live clock) program in ``slot``. **verified**"""
    return [program_create(slot, width, height, play_seconds=play_seconds),
            text_header(slot, animation=ANIM_SCROLL_LEFT if scroll else ANIM_STATIC, speed=speed,
                        gap=width, size=size),
            *data_chunks(slot, body),
            program_commit(slot, content_key(body))]


# --- live drawing (only renders immediately in GAME_DRAW mode) ---------------------------


def draw_rect(x0: int, y0: int, x1: int, y1: int, color: RGB) -> bytes:
    """Filled rectangle, inclusive corners. **verified**"""
    return tlv(TAG_DRAW, bytes([1, *color, 0]) + struct.pack("<HHHH", x0, y0, x1, y1))


def draw_bitmap(x0: int, y0: int, rows: Sequence[Sequence[int]], color: RGB) -> bytes:
    """1-bit mask (rows of 0/1) drawn in one colour at (x0, y0). **verified**"""
    h, w = len(rows), len(rows[0])
    data = bytearray()
    for row in rows:
        acc = bits = 0
        for v in row:
            acc, bits = (acc << 1) | (1 if v else 0), bits + 1
            if bits == 8:
                data.append(acc)
                acc = bits = 0
        if bits:
            data.append(acc << (8 - bits))
    return tlv(TAG_DRAW, bytes([0, *color]) + struct.pack("<HHHH", x0, y0, x0 + w - 1, y0 + h - 1) + bytes(data))


def draw_points(points: Iterable[tuple[int, int]], color: RGB) -> bytes:
    """Individual pixels in one colour. **verified**"""
    pts = list(points)
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
    rows = [[0] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
    for x, y in pts:
        rows[y - y0][x - x0] = 1
    return draw_bitmap(x0, y0, rows, color)


# --- games ------------------------------------------------------------------------------


def game_start(game_id: int) -> bytes:
    """Enter a built-in game/mode: 0 Tetris, 1 Snake, 16 live drawing. **verified**"""
    return bytes([TAG_GAME, 1, game_id + 128])


def game_key(key: str) -> bytes:
    """left/up/right/down/start/pause/done/exit. **verified** (Tetris rotation key unknown)."""
    return bytes([TAG_GAME, 1, GAME_KEYS[key]])


# --- built-in content -------------------------------------------------------------------


def builtin_clock(fmt: int = 0, clock: int = 0, date: int = 0, color: RGB = (255, 255, 255)) -> bytes:
    """Panel's own clock face. **inferred** (a digital face shows; style ids unmapped)."""
    return bytes([TAG_BUILTIN, 7, 0, fmt, clock, date, *color])


def builtin_effect(style: int, speed: int = 255, colors: Sequence[RGB] = ()) -> bytes:
    """Built-in light effect. **unsupported** on the tested panel (acked, nothing visible)."""
    body = bytes([5, 0, style, speed]) + b"".join(bytes(c) for c in list(colors)[:8])
    return bytes([TAG_BUILTIN, len(body)]) + body


def transition(effect: int | None = None, speed: int | None = None, stay: int | None = None) -> bytes:
    """Global transition between programs. **unsupported** on the tested panel (error 3)."""
    flags = (effect is not None) | (speed is not None) << 1 | (stay is not None) << 2
    return bytes([TAG_TRANSITION, 4, flags, effect or 0, speed or 0, stay or 0])


def mirror(value: int) -> bytes:
    """Mirror mode. **unsupported** on the tested panel (error 3)."""
    return bytes([TAG_MIRROR, 1, value])


def channel_order(value: int) -> bytes:
    """RGB channel order. **untested**: may change colours persistently."""
    return bytes([TAG_CHANNEL_ORDER, 1, value])


# --- queries (send with class 3; the reply is a TLV with the same tag) ------------------


def query(tag: int, *args: int) -> bytes:
    return bytes([tag, len(args), *args])


def query_slots(slots: Iterable[int]) -> bytes:
    return query(TAG_PROGRAM_KEY, *slots)
