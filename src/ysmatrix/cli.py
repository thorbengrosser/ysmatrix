"""``ysmatrix`` command-line tool. Run ``ysmatrix --help`` or ``ysmatrix <command> --help``."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from . import __version__
from . import commands as cmd
from .client import AsyncClient
from .images import Resize
from .transport import PanelError, scan

NAMED_COLORS = {
    "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), "white": (255, 255, 255),
    "black": (0, 0, 0), "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),
    "orange": (255, 128, 0), "purple": (128, 0, 255), "pink": (255, 80, 160),
}


def color(value: str) -> tuple[int, int, int]:
    """``red``, ``#ff8000``, ``ff8000`` or ``255,128,0``."""
    v = value.strip().lower()
    if v in NAMED_COLORS:
        return NAMED_COLORS[v]
    if "," in v:
        parts = tuple(int(p) for p in v.split(","))
        if len(parts) == 3 and all(0 <= p <= 255 for p in parts):
            return parts  # type: ignore[return-value]
    else:
        h = v.lstrip("#")
        if len(h) == 6:
            return tuple(bytes.fromhex(h))  # type: ignore[return-value]
    raise argparse.ArgumentTypeError(f"not a colour: {value!r} (use a name, #rrggbb or r,g,b)")


def slot_type(value: str) -> int:
    n = int(value)
    if not 0 <= n < cmd.MAX_SLOTS:
        raise argparse.ArgumentTypeError(f"slot must be 0-{cmd.MAX_SLOTS - 1}")
    return n


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ysmatrix",
        description="Control YS…/TL… Bluetooth LED matrix panels (the ones used with the LOY PLAY / LOY SPACE apps). Unofficial.",
        epilog="With several panels, pick one with --name or --address (see 'ysmatrix scan'); "
               "otherwise the first panel found is used. Docs: see the docs/ folder of the project.",
    )
    p.add_argument("-a", "--address", help="BLE address (a UUID on macOS); default: first panel found")
    p.add_argument("-n", "--name", help="advertised name, e.g. YS525228813 (see 'ysmatrix scan')")
    p.add_argument("-v", "--verbose", action="count", default=0, help="-v info, -vv every frame in hex")
    p.add_argument("--version", action="version", version=f"ysmatrix {__version__}")
    sub = p.add_subparsers(dest="command", required=True, metavar="command")

    def add(name, help_):
        return sub.add_parser(name, help=help_, description=help_)

    add("scan", "list nearby panels")
    add("info", "show model, firmware, size, brightness, rotation, clock and stored slots")

    s = add("power", "switch the display on or off")
    s.add_argument("state", choices=["on", "off"])

    s = add("brightness", "set brightness 1-15")
    s.add_argument("level", type=int, choices=range(1, 16), metavar="1-15")

    s = add("rotate", "show or set rotation (n x 90 degrees clockwise, stored on the panel)")
    s.add_argument("quarter_turns", type=int, nargs="?", choices=range(4), metavar="0-3")

    add("sync-time", "set the panel's clock to this computer's time")

    s = add("image", "upload a picture or animated GIF to a slot and show it")
    s.add_argument("path")
    s.add_argument("-s", "--slot", type=slot_type, default=0)
    s.add_argument("--resize", choices=[r.value for r in Resize], default="fit")
    s.add_argument("--no-show", action="store_true", help="store only, keep showing the current slot")

    s = add("text", "upload scrolling or static text (rendered by the panel's own font)")
    s.add_argument("text")
    s.add_argument("-s", "--slot", type=slot_type, default=0)
    s.add_argument("-c", "--color", type=color, default=(255, 0, 0))
    s.add_argument("-b", "--background", type=color, default=(0, 0, 0))
    s.add_argument("--size", type=int, default=16, help="font height in pixels (8 and 16 tested)")
    s.add_argument("--static", action="store_true", help="do not scroll (wraps per character)")
    s.add_argument("--speed", type=int, default=9, help="scroll speed byte (default 9, the app's default)")
    s.add_argument("--align", choices=["left", "center", "right"], default="left")
    s.add_argument("--no-show", action="store_true")

    s = add("clock", "upload a live clock the panel keeps ticking (also syncs the time)")
    s.add_argument("format", nargs="?", default="{hh}:{mm}:{ss}",
                   help="placeholders {YYYY} {YY} {MM} {DD} {hh} {mm} {ss} (default %(default)s)")
    s.add_argument("-s", "--slot", type=slot_type, default=0)
    s.add_argument("-c", "--color", type=color, default=(0, 255, 255))
    s.add_argument("--size", type=int, default=16)

    s = add("builtin-clock", "show the panel's own clock face (style ids not mapped yet)")
    s.add_argument("--style", type=int, default=0)
    s.add_argument("-c", "--color", type=color, default=(255, 255, 255))

    s = add("play", "show a stored slot")
    s.add_argument("slot", type=slot_type)

    s = add("loop", "cycle through stored slots")
    s.add_argument("slots", type=slot_type, nargs="+")

    add("slots", "list stored slots")

    s = add("delete", "delete a stored slot (inferred command)")
    s.add_argument("slot", type=slot_type)

    s = add("fill", "live-draw a filled rectangle (enters drawing mode until you press Enter)")
    s.add_argument("x0", type=int)
    s.add_argument("y0", type=int)
    s.add_argument("x1", type=int)
    s.add_argument("y1", type=int)
    s.add_argument("color", type=color)

    s = add("game", "play a built-in game with the arrow keys (macOS/Linux terminals)")
    s.add_argument("name", choices=["tetris", "snake"])

    s = add("raw", "send a raw payload in hex, e.g. 0402 0001 (for exploring; see docs/protocol.md)")
    s.add_argument("hex", nargs="+")
    s.add_argument("--query", action="store_true", help="send as a query and print the reply")
    s.add_argument("--no-ack", action="store_true")
    return p


async def run(args: argparse.Namespace) -> None:
    if args.command == "scan":
        found = await scan()
        if not found:
            print("No panels found. Is it switched on and not connected to the phone app?")
        for d in found:
            print(f"{d.name}\t{d.address}")
        return

    async with AsyncClient(args.address, name=args.name) as panel:
        c = args.command
        if c == "info":
            info = await panel.get_device_info()
            w, h = await panel.get_size()
            rows = [
                ("model", info.model), ("firmware", info.firmware), ("serial", info.serial),
                ("size", f"{w}x{h}"), ("capabilities", ", ".join(info.capabilities)),
                ("power", await panel.get_power()), ("brightness", await panel.get_brightness()),
                ("rotation", await panel.get_rotation()), ("clock", await panel.get_time()),
                ("slots", ", ".join(str(s.slot) for s in await panel.list_slots()) or "none"),
            ]
            for label, value in rows:
                print(f"{label:<13}{value}")
        elif c == "power":
            await panel.set_power(args.state == "on")
        elif c == "brightness":
            await panel.set_brightness(args.level)
        elif c == "rotate":
            if args.quarter_turns is not None:
                await panel.set_rotation(args.quarter_turns)
            print("rotation", await panel.get_rotation())
        elif c == "sync-time":
            await panel.set_time()
            print("panel clock:", await panel.get_time())
        elif c == "image":
            await panel.send_image(args.path, args.slot, resize=args.resize, show=not args.no_show)
        elif c == "text":
            await panel.send_text(args.text, args.slot, color=args.color, background=args.background,
                                  size=args.size, scroll=not args.static, speed=args.speed, align=args.align,
                                  show=not args.no_show)
        elif c == "clock":
            await panel.send_clock(args.format, args.slot, color=args.color, size=args.size)
        elif c == "builtin-clock":
            await panel.show_builtin_clock(args.style, args.color)
        elif c == "play":
            await panel.play(args.slot)
        elif c == "loop":
            await panel.play_loop(args.slots)
        elif c == "slots":
            for s in await panel.list_slots():
                print(f"slot {s.slot:2d}  key {s.key.hex()}")
        elif c == "delete":
            await panel.delete_slot(args.slot)
        elif c == "fill":
            async with panel.drawing():
                await panel.fill_rect(args.x0, args.y0, args.x1, args.y1, args.color)
                await asyncio.get_running_loop().run_in_executor(None, input, "Drawn. Press Enter to leave drawing mode. ")
        elif c == "game":
            await play_game(panel, cmd.GAME_TETRIS if args.name == "tetris" else cmd.GAME_SNAKE)
        elif c == "raw":
            payload = bytes.fromhex("".join(args.hex))
            if args.query:
                reply = await panel.query(payload)
                print(reply.hex() if reply else "(empty reply)")
            else:
                await panel.send(payload, ack=not args.no_ack)
                print("ok")


async def play_game(panel: AsyncClient, game: int) -> None:
    import termios
    import tty

    keys = {b"\x1b[A": "up", b"\x1b[B": "down", b"\x1b[C": "right", b"\x1b[D": "left",
            b"s": "start", b"\n": "start", b"\r": "start", b"p": "pause"}
    await panel.start_game(game)
    print("arrows move, s/Enter start, p pause, q quit", flush=True)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    tty.setcbreak(fd)
    loop.add_reader(fd, lambda: queue.put_nowait(os.read(fd, 16)))
    try:
        while True:
            data = await queue.get()
            if b"q" in data:
                break
            i = 0
            while i < len(data):
                chunk = data[i:i + 3] if data[i:i + 1] == b"\x1b" else data[i:i + 1]
                i += max(1, len(chunk))
                if chunk in keys:
                    await panel.game_key(keys[chunk], ack=False)
    finally:
        loop.remove_reader(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        await panel.exit_game()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    level = logging.WARNING if args.verbose == 0 else logging.INFO if args.verbose == 1 else logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")
    try:
        asyncio.run(run(args))
    except (PanelError, ConnectionError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
