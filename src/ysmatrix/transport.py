"""Bluetooth LE connection: discovery, writing frames, matching acks and query replies."""
from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from . import framing

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
NAME_PREFIXES = ("YS", "TL")

log = logging.getLogger("ysmatrix")


class PanelError(Exception):
    """The panel answered a command with an error code."""

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class UnsupportedCommand(PanelError):
    """Error 3: the command exists in the protocol but this panel/firmware does not implement it."""


class NoAck(PanelError):
    """The panel did not acknowledge a command after several attempts."""


async def scan(timeout: float = 8.0) -> list[BLEDevice]:
    """Find nearby panels by advertised name (``YS…``/``TL…``)."""
    devices = await BleakScanner.discover(timeout=timeout)
    return [d for d in devices if d.name and d.name.startswith(NAME_PREFIXES)]


class Connection:
    """One BLE connection. Higher-level code should use :class:`ysmatrix.AsyncClient`."""

    ack_timeout = 3.0
    ack_retries = 3
    unacked_gap = 0.02  # pause after fire-and-forget frames; with none the panel's input overflows

    def __init__(self, target: str | BLEDevice):
        self.target = target
        self.client: BleakClient | None = None
        self.write_size = 180
        self._rx = bytearray()
        self._waiters: dict[int, asyncio.Future] = {}
        self._replies: list[framing.Frame] = []

    async def open(self) -> None:
        self.client = BleakClient(self.target)
        await self.client.connect()
        await self.client.start_notify(NOTIFY_UUID, self._on_notify)
        try:
            size = self.client.services.get_characteristic(WRITE_UUID).max_write_without_response_size
            if size and size > 20:
                self.write_size = min(size, 509)
        except Exception:  # keep the conservative default
            pass

    async def close(self) -> None:
        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(NOTIFY_UUID)
            finally:
                await self.client.disconnect()

    def _on_notify(self, _char, data: bytearray) -> None:
        log.debug("rx %s", bytes(data).hex())
        self._rx += data
        while self._rx:
            try:
                frame = framing.parse_frame(bytes(self._rx))
            except ValueError:
                if self._rx[:2] != framing.MAGIC and len(self._rx) >= 2:
                    del self._rx[:1]  # resynchronise on garbage
                    continue
                return  # wait for the rest of the frame
            del self._rx[:frame.size]
            ack = framing.parse_ack(frame)
            if ack is None:
                self._replies.append(frame)
                continue
            fut = self._waiters.pop(frame.sno, None)
            if fut and not fut.done():
                fut.set_result(ack)

    async def write_frame(self, frame: bytes) -> None:
        assert self.client is not None, "not connected"
        log.debug("tx %s", frame.hex())
        for start in range(0, len(frame), self.write_size):
            await self.client.write_gatt_char(WRITE_UUID, frame[start:start + self.write_size], response=False)

    async def send(self, payload: bytes, *, ack: bool = True) -> None:
        """Send one command payload. With ``ack`` (default) wait for the panel's ack and retry."""
        sno = framing.next_sno()
        if not ack:
            await self.write_frame(framing.build_frame(payload, sno, framing.CLASS_COMMAND, framing.FRAME_TYPE_UNACK))
            await asyncio.sleep(self.unacked_gap)
            return
        frame = framing.build_frame(payload, sno)
        for attempt in range(self.ack_retries):
            fut = asyncio.get_running_loop().create_future()
            self._waiters[sno] = fut
            await self.write_frame(frame)
            try:
                result = await asyncio.wait_for(fut, self.ack_timeout)
            except asyncio.TimeoutError:
                self._waiters.pop(sno, None)
                log.warning("no ack for sno %d (attempt %d)", sno, attempt + 1)
                continue
            if not result.ok:
                exc = UnsupportedCommand if result.error == 3 else PanelError
                raise exc(f"panel returned error {result.error} for tag 0x{payload[0]:02x}", result.error)
            return
        raise NoAck(f"no ack after {self.ack_retries} attempts (tag 0x{payload[0]:02x})")

    async def query(self, payload: bytes, *, timeout: float = 2.0) -> bytes | None:
        """Send a query and return the value of the reply TLV with the same tag (None if empty/no reply)."""
        tag = payload[0]
        self._replies.clear()
        await self.write_frame(framing.build_frame(payload, framing.next_sno(), framing.CLASS_QUERY))
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            for frame in self._replies:
                if frame.cls == framing.CLASS_REPLY and frame.payload[:1] == bytes([tag]):
                    tlvs = framing.parse_tlvs(frame.payload)
                    return tlvs[0][1] if tlvs else None
                if frame.cls == framing.CLASS_REPLY and not frame.payload:
                    return None  # empty reply = not supported
            await asyncio.sleep(0.03)
        return None
