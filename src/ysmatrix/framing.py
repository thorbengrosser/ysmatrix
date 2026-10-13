"""Over-the-air framing: every message to and from the panel is one of these frames.

::

    AA 55 | FF FF | len u16 | sno u16 | type u8 | class u8 | payload ... | checksum u16

* ``len``      = payload length + 6 (sno, type, class and checksum)
* ``sno``      = sequence number; the panel echoes it in its ack
* ``type``     = 0xC1 "please ack" or 0x81 "fire and forget" (bit 7 = checksum present)
* ``class``    = 2 command, 3 query; replies use 0x82/0x84 (ack) and 0x83 (query answer)
* ``checksum`` = 16-bit sum of every preceding byte

All integers are little-endian. The payload is a sequence of TLVs (see :func:`tlv`).
"""
from __future__ import annotations

import itertools
import struct
from dataclasses import dataclass
from typing import Iterator

MAGIC = b"\xaa\x55"
RESERVED = b"\xff\xff"

FRAME_TYPE_ACK = 0xC1
FRAME_TYPE_UNACK = 0x81

CLASS_COMMAND = 2
CLASS_QUERY = 3
CLASS_ACK = (0x82, 0x84)
CLASS_REPLY = 0x83

_sno_counter = itertools.count(1)


def next_sno() -> int:
    """Sequence number for the next outgoing frame (wraps at 16 bits)."""
    return next(_sno_counter) & 0xFFFF


def build_frame(
    payload: bytes, sno: int, cls: int = CLASS_COMMAND, frame_type: int = FRAME_TYPE_ACK
) -> bytes:
    """Wrap a TLV payload in a frame ready to be written to the panel."""
    has_checksum = bool(frame_type & 0x80)
    body = bytearray(MAGIC + RESERVED)
    body += (len(payload) + (2 if has_checksum else 0) + 4).to_bytes(2, "little")
    body += (sno & 0xFFFF).to_bytes(2, "little")
    body += bytes([frame_type, cls])
    body += payload
    if has_checksum:
        body += (sum(body) & 0xFFFF).to_bytes(2, "little")
    return bytes(body)


@dataclass
class Frame:
    sno: int
    frame_type: int
    cls: int
    payload: bytes
    checksum_ok: bool | None  # None when the frame carries no checksum
    size: int  # bytes this frame occupies in the stream


def parse_frame(data: bytes) -> Frame:
    """Parse one frame from the start of ``data``; raises ValueError if incomplete or invalid."""
    if len(data) < 10 or data[:2] != MAGIC:
        raise ValueError("not a frame")
    length, sno = struct.unpack_from("<HH", data, 4)
    total = 6 + length
    if len(data) < total:
        raise ValueError("incomplete frame")
    frame_type, cls = data[8], data[9]
    if frame_type & 0x80:
        checksum = struct.unpack_from("<H", data, total - 2)[0]
        ok = (sum(data[: total - 2]) & 0xFFFF) == checksum
        payload = bytes(data[10 : total - 2])
    else:
        ok, payload = None, bytes(data[10:total])
    return Frame(sno, frame_type, cls, payload, ok, total)


def split_frames(stream: bytes) -> Iterator[Frame]:
    i = 0
    while i < len(stream):
        frame = parse_frame(stream[i:])
        yield frame
        i += frame.size


@dataclass
class Ack:
    sno: int
    ok: bool
    error: int  # 0 when ok; 3 = command not supported by this panel


def parse_ack(frame: Frame) -> Ack | None:
    """Interpret a frame as an ack (class 0x82/0x84), or return None."""
    if frame.cls in CLASS_ACK and frame.payload:
        return Ack(frame.sno, frame.payload[0] == 0, frame.payload[0])
    return None


# --- TLV -----------------------------------------------------------------------


def encode_length(n: int) -> bytes:
    """TLV length: 1 byte below 128, ``81 nn`` below 256, else ``82 lo hi``."""
    if n < 128:
        return bytes([n])
    if n < 256:
        return bytes([0x81, n])
    return bytes([0x82, n & 0xFF, n >> 8])


def tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + encode_length(len(value)) + value


def parse_tlvs(payload: bytes) -> list[tuple[int, bytes]]:
    out, i = [], 0
    while i < len(payload):
        tag, n = payload[i], payload[i + 1]
        i += 2
        if n == 0x81:
            n = payload[i]
            i += 1
        elif n == 0x82:
            n = payload[i] | (payload[i + 1] << 8)
            i += 2
        out.append((tag, bytes(payload[i : i + n])))
        i += n
    return out
