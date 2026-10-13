"""Parsed replies to queries."""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DeviceInfo:
    """Answer to the device-info query, e.g. ``123456789,EXYB-AS#GGMJXZ180,V2.9.1#V16,...``."""

    serial: str
    model: str
    firmware: str
    capabilities: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def mtu(self) -> int | None:
        for cap in self.capabilities:
            if cap.startswith("MTU:"):
                return int(cap[4:])
        return None

    @classmethod
    def parse(cls, value: bytes) -> "DeviceInfo":
        text = value.decode("ascii", "replace")
        parts = text.split(",")
        return cls(parts[0], parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "",
                   parts[3:], text)


@dataclass
class PanelParams:
    """Answer to the panel-parameter query. Only width/height/colour type are understood."""

    width: int
    height: int
    color_type: int
    raw: bytes

    @classmethod
    def parse(cls, value: bytes) -> "PanelParams":
        if len(value) < 8 or value[0] != 0:
            raise ValueError("unexpected panel-parameter reply")
        w, h = struct.unpack_from("<HH", value, 1)
        return cls(w, h, value[7], value)


@dataclass
class Slot:
    """One stored program, as reported by the slot query."""

    slot: int
    prefix: int  # slot+1 as digits, written by the uploader
    key: bytes  # 16-byte content key written by the uploader

    @property
    def empty(self) -> bool:
        return self.prefix == 0 and not any(self.key)

    @classmethod
    def parse_many(cls, value: bytes) -> list["Slot"]:
        return [cls(value[i], struct.unpack_from("<I", value, i + 1)[0], bytes(value[i + 5:i + 21]))
                for i in range(0, len(value) - 20, 21)]


def parse_time(value: bytes) -> datetime | None:
    """Answer to the time query: ``year u16, month, day, hour, minute, second, ms u16``.

    A set clock reports the year as an offset from 2000 (26 = 2026); a never-set clock
    reported the raw value 2000, so both forms are accepted. Returns None if unparseable.
    """
    if len(value) < 9:
        return None
    year = struct.unpack_from("<H", value, 0)[0]
    year = year if year >= 2000 else 2000 + year
    month, day, hour, minute, second = value[2:7]
    ms = struct.unpack_from("<H", value, 7)[0] if len(value) >= 9 else 0
    try:
        return datetime(year, month, day, hour, minute, second, ms * 1000)
    except ValueError:
        return None
