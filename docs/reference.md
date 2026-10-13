# API reference

`Client` (blocking) and `AsyncClient` (asyncio) have the same methods; on `AsyncClient` they are coroutines.

## Connecting

| | |
|---|---|
| `Client(address=None, name=None, scan_timeout=8.0)` | `address`: BLE address/UUID or a bleak `BLEDevice`; `name`: advertised name such as `YS525228813`; neither = first panel found |
| `with Client() as panel:` / `async with AsyncClient() as panel:` | connect and disconnect |
| `connect()`, `disconnect()` | manual control |
| `ysmatrix.scan(timeout=8.0)` | async; list panels (`BLEDevice` objects) |

## Information

| Method | Returns |
|---|---|
| `get_device_info()` | `DeviceInfo(serial, model, firmware, capabilities, raw)`; `.mtu` |
| `get_panel_params()` | `PanelParams(width, height, color_type, raw)` |
| `get_size()` | `(width, height)` |
| `get_power()` / `get_brightness()` / `get_rotation()` | current value or `None` |
| `get_time()` | `datetime` of the panel clock |
| `list_slots(include_empty=False)` | `[Slot(slot, prefix, key)]` |

## Settings

| Method | |
|---|---|
| `set_power(on)`, `power_on()`, `power_off()` | |
| `set_brightness(level)` | 1–15 |
| `set_rotation(quarter_turns)` | 0–3, absolute, stored on the panel |
| `set_time(when=None)` | default: now |

## Content (stored in slots 0–59)

| Method | |
|---|---|
| `send_image(image, slot=0, resize="fit", show=True, loops=1)` | path, bytes or Pillow image; animated input goes to `send_gif` |
| `send_gif(gif, slot=0, resize="fit", show=True, loops=1)` | sent as a GIF file |
| `send_text(text, slot=0, color, background, size=16, scroll=True, speed=9, align, valign, play_seconds=10, show=True)` | |
| `send_clock(fmt="{hh}:{mm}:{ss}", slot=0, color, size=16, set_time=True, align, valign, show=True)` | fields `{YYYY} {YY} {MM} {DD} {hh} {mm} {ss}` |
| `show_builtin_clock(style=0, color)` | |
| `delete_slot(slot)` | |
| `play(slot)` | show one slot |
| `play_loop(slots)` | cycle through slots |

`resize`: `Resize.FIT` (pad), `Resize.FILL` (crop), `Resize.STRETCH`.

## Live drawing

| Method | |
|---|---|
| `drawing(background=(0,0,0))` | context manager: enter/leave drawing mode |
| `fill_rect(x0, y0, x1, y1, color, ack=True)` | inclusive corners |
| `draw_points(points, color, ack=True)` | |
| `draw_bitmap(x, y, rows, color, ack=True)` | rows of 0/1 |
| `draw_batch(payloads, ack=True)` | several `commands.draw_*` in one frame |

## Games

`start_game(game=0)` (0 Tetris, 1 Snake), `game_key(key, ack=True)` (`left up right down start pause done exit`), `exit_game()`.

## Raw access

`send(payload, ack=True)`, `query(payload)`. Payload builders: `ysmatrix.commands`. Framing:
`ysmatrix.framing`. Image codec: `ysmatrix.ystp` (`encode`, `decode`).
