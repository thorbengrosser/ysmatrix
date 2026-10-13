"""High-level clients: :class:`AsyncClient` (asyncio) and :class:`Client` (blocking)."""
from __future__ import annotations

import asyncio
import functools
import inspect
import math
import threading
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Iterable, Sequence

from bleak.backends.device import BLEDevice

from . import commands as cmd
from .images import ImageSource, Resize, is_animated, open_image, to_gif, to_still
from .models import DeviceInfo, PanelParams, Slot, parse_time
from .transport import Connection, scan

RGB = tuple[int, int, int]


class AsyncClient:
    """Control one panel over BLE.

    ``address`` is the BLE address (a UUID on macOS) or a ``BLEDevice``; ``name`` picks a panel by
    its advertised name instead (e.g. ``"YS525228813"``). With neither, the first panel found by a
    scan is used::

        async with AsyncClient() as panel:
            await panel.send_text("Hello")
    """

    def __init__(self, address: str | BLEDevice | None = None, *, name: str | None = None,
                 scan_timeout: float = 8.0):
        self.address = address
        self.name = name
        self.scan_timeout = scan_timeout
        self.conn: Connection | None = None
        self._size: tuple[int, int] | None = None

    # --- connection --------------------------------------------------------------------

    async def connect(self) -> None:
        target = self.address
        if target is None:
            found = await scan(self.scan_timeout)
            if self.name:
                found = [d for d in found if d.name and d.name.lower() == self.name.lower()]
            if not found:
                which = f"named {self.name!r}" if self.name else "(names starting YS/TL)"
                raise ConnectionError(f"no panel found {which}; is it on and not connected to a phone?")
            target = found[0]
        self.conn = Connection(target)
        await self.conn.open()

    async def disconnect(self) -> None:
        if self.conn:
            await self.conn.close()

    async def __aenter__(self) -> "AsyncClient":
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.disconnect()

    async def send(self, payload: bytes, *, ack: bool = True) -> None:
        """Send a raw command payload (see :mod:`ysmatrix.commands`)."""
        assert self.conn, "not connected"
        await self.conn.send(payload, ack=ack)

    async def query(self, payload: bytes) -> bytes | None:
        """Send a raw query payload and return the reply value (None if empty)."""
        assert self.conn, "not connected"
        return await self.conn.query(payload)

    # --- information -----------------------------------------------------------------

    async def get_device_info(self) -> DeviceInfo:
        value = await self.query(cmd.query(cmd.TAG_DEVICE_INFO))
        if value is None:
            raise RuntimeError("no device-info reply")
        return DeviceInfo.parse(value)

    async def get_panel_params(self) -> PanelParams:
        value = await self.query(cmd.query(cmd.TAG_PANEL_PARAMS))
        if value is None:
            raise RuntimeError("no panel-parameter reply")
        return PanelParams.parse(value)

    async def get_size(self) -> tuple[int, int]:
        """Panel size in pixels (cached after the first call)."""
        if self._size is None:
            p = await self.get_panel_params()
            self._size = (p.width, p.height)
        return self._size

    async def get_brightness(self) -> int | None:
        value = await self.query(cmd.query(cmd.TAG_BRIGHTNESS))
        return value[-1] if value else None

    async def get_power(self) -> bool | None:
        value = await self.query(cmd.query(cmd.TAG_POWER))
        return bool(value[-1]) if value else None

    async def get_rotation(self) -> int | None:
        value = await self.query(cmd.query(cmd.TAG_ROTATE))
        return value[-1] if value else None

    async def get_time(self) -> datetime | None:
        value = await self.query(cmd.query(cmd.TAG_SET_TIME))
        return parse_time(value) if value else None

    async def list_slots(self, include_empty: bool = False) -> list[Slot]:
        """Stored programs (asked 10 slots at a time, like the official app)."""
        found: list[Slot] = []
        for start in range(0, cmd.MAX_SLOTS, 10):
            value = await self.query(cmd.query_slots(range(start, min(start + 10, cmd.MAX_SLOTS))))
            if value:
                found += [s for s in Slot.parse_many(value) if include_empty or not s.empty]
        return found

    # --- settings ----------------------------------------------------------------------

    async def set_power(self, on: bool) -> None:
        await self.send(cmd.power(on))

    async def power_on(self) -> None:
        await self.set_power(True)

    async def power_off(self) -> None:
        await self.set_power(False)

    async def set_brightness(self, level: int) -> None:
        """1 (dim) to 15 (brightest)."""
        await self.send(cmd.brightness(level))

    async def set_rotation(self, quarter_turns: int) -> None:
        """Absolute rotation, n x 90 degrees clockwise. Stored on the panel; read it first to restore."""
        await self.send(cmd.rotate(quarter_turns))

    async def set_time(self, when: datetime | None = None) -> None:
        """Set the panel's clock (default: now, local time)."""
        await self.send(cmd.set_time(when or datetime.now()))

    # --- content -------------------------------------------------------------------------

    async def _upload(self, payloads: Sequence[bytes], slot: int, show: bool) -> None:
        if not 0 <= slot < cmd.MAX_SLOTS:
            raise ValueError(f"slot must be 0-{cmd.MAX_SLOTS - 1}")
        for p in payloads:
            await self.send(p)
        if show:
            await self.play(slot)

    async def send_image(self, image: ImageSource, slot: int = 0, *, resize: Resize | str = Resize.FIT,
                         show: bool = True, loops: int = 1) -> None:
        """Store a picture (or animated GIF) in ``slot`` and show it. Survives power cycles."""
        img = open_image(image)
        if is_animated(img):
            await self.send_gif(image, slot, resize=resize, show=show, loops=loops)
            return
        size = await self.get_size()
        data = to_still(img, size, Resize(resize))
        await self._upload(cmd.graphic_upload(slot, data, *size, loops=loops), slot, show)

    async def send_gif(self, gif: ImageSource, slot: int = 0, *, resize: Resize | str = Resize.FIT,
                       show: bool = True, loops: int = 1) -> None:
        """Store an animation. The GIF is sent as a file and decoded by the panel."""
        size = await self.get_size()
        data, seconds = to_gif(gif, size, Resize(resize))
        await self._upload(cmd.graphic_upload(slot, data, *size, loops=loops,
                                              play_seconds=max(1, math.ceil(seconds * loops))), slot, show)

    async def send_text(self, text: str, slot: int = 0, *, color: RGB = (255, 0, 0), background: RGB = (0, 0, 0),
                        size: int = 16, scroll: bool = True, speed: int = 9, align: str = "left",
                        valign: str = "top", play_seconds: int = 10, show: bool = True) -> None:
        """Store a text program. The panel renders the text with its own font.

        ``size`` is the font height (8 and 16 tested). Static text wraps per character.
        """
        w, h = await self.get_size()
        body = cmd.text_body(text, color=color, background=background, size=size, align=align, valign=valign)
        await self._upload(cmd.text_upload(slot, body, w, h, scroll=scroll, speed=speed, size=size,
                                           play_seconds=play_seconds), slot, show)

    async def send_clock(self, fmt: str = "{hh}:{mm}:{ss}", slot: int = 0, *, color: RGB = (0, 255, 255),
                         size: int = 16, set_time: bool = True, align: str = "left", valign: str = "top",
                         show: bool = True) -> None:
        """A live clock the panel keeps updating. Fields: {YYYY} {YY} {MM} {DD} {hh} {mm} {ss}."""
        if set_time:
            await self.set_time()
        w, h = await self.get_size()
        body = cmd.text_body(fmt, color=color, size=size, align=align, valign=valign, clock_fields=True)
        await self._upload(cmd.text_upload(slot, body, w, h, scroll=False, size=size), slot, show)

    async def show_builtin_clock(self, style: int = 0, color: RGB = (255, 255, 255)) -> None:
        """The panel's own clock face (style ids are not mapped yet)."""
        await self.send(cmd.builtin_clock(style, 0, 0, color))

    async def delete_slot(self, slot: int) -> None:
        await self.send(cmd.delete_slot(slot))

    # --- playback ------------------------------------------------------------------------

    async def play(self, slot: int) -> None:
        """Show one stored slot."""
        await self.send(cmd.play(slot))

    async def play_loop(self, slots: Iterable[int]) -> None:
        """Cycle through stored slots; each shows for the play time it was uploaded with."""
        await self.send(cmd.play_loop(slots))

    # --- live drawing --------------------------------------------------------------------

    @asynccontextmanager
    async def drawing(self, background: RGB = (0, 0, 0)):
        """Enter live-drawing mode; drawing commands render immediately inside the block."""
        await self.send(cmd.game_start(cmd.GAME_DRAW))
        await asyncio.sleep(0.3)
        w, h = await self.get_size()
        await self.fill_rect(0, 0, w - 1, h - 1, background)
        try:
            yield self
        finally:
            await self.send(cmd.game_key("exit"))

    async def fill_rect(self, x0: int, y0: int, x1: int, y1: int, color: RGB, *, ack: bool = True) -> None:
        await self.send(cmd.draw_rect(x0, y0, x1, y1, tuple(color)), ack=ack)

    async def draw_points(self, points: Iterable[tuple[int, int]], color: RGB, *, ack: bool = True) -> None:
        await self.send(cmd.draw_points(points, tuple(color)), ack=ack)

    async def draw_bitmap(self, x: int, y: int, rows: Sequence[Sequence[int]], color: RGB, *, ack: bool = True) -> None:
        await self.send(cmd.draw_bitmap(x, y, rows, tuple(color)), ack=ack)

    async def draw_batch(self, payloads: Sequence[bytes], *, ack: bool = True) -> None:
        """Several draw payloads in one frame (faster). ``ack=False``: ~30 fps, errors not reported."""
        await self.send(b"".join(payloads), ack=ack)

    # --- games ---------------------------------------------------------------------------

    async def start_game(self, game: int = cmd.GAME_TETRIS) -> None:
        """0 = Tetris, 1 = Snake. Press ``start`` to begin."""
        await self.send(cmd.game_start(game))

    async def game_key(self, key: str, *, ack: bool = True) -> None:
        """left, up, right, down, start, pause, done, exit."""
        await self.send(cmd.game_key(key), ack=ack)

    async def exit_game(self) -> None:
        await self.send(cmd.game_key("exit"))


class Client:
    """Blocking version of :class:`AsyncClient` with the same methods::

        with Client() as panel:
            panel.set_brightness(10)
            panel.send_image("cat.png")
    """

    def __init__(self, address: str | BLEDevice | None = None, **kw):
        self._async = AsyncClient(address, **kw)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def __getattr__(self, name):
        attr = getattr(self._async, name)
        if inspect.iscoroutinefunction(attr):
            @functools.wraps(attr)
            def wrapper(*args, **kw):
                return self._run(attr(*args, **kw))
            return wrapper
        return attr

    @contextmanager
    def drawing(self, background: RGB = (0, 0, 0)):
        cm = self._async.drawing(background)
        self._run(cm.__aenter__())
        try:
            yield self
        finally:
            self._run(cm.__aexit__(None, None, None))

    def __enter__(self) -> "Client":
        self._run(self._async.connect())
        return self

    def __exit__(self, *exc) -> None:
        try:
            self._run(self._async.disconnect())
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2)
