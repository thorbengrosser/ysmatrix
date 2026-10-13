# Using ysmatrix in your own code

## Blocking API

```python
from ysmatrix import Client

with Client() as panel:                     # first panel found; or Client("<address>")
    print(panel.get_device_info().model, panel.get_size())
    panel.set_brightness(10)
    panel.send_image("cat.png", slot=1)     # stored on the panel
    panel.send_text("Hello!", slot=2, color=(0, 255, 0))
    panel.send_clock("{hh}:{mm}", slot=3)
    panel.play_loop([1, 2, 3])
```

## Several panels

Open one client per panel, by advertised name or address:

```python
with Client(name="YS525228813") as left, Client(name="YS525228999") as right:
    left.send_text("left")
    right.send_text("right")
```

## asyncio API

`AsyncClient` has the same methods as coroutines.

```python
import asyncio
from ysmatrix import AsyncClient

async def main():
    async with AsyncClient() as panel:
        await panel.send_text("Hello async")

asyncio.run(main())
```

## Live drawing

Drawing renders immediately inside `drawing()`, which switches the panel into its drawing mode
and back. Coordinates start at the top-left pixel `(0, 0)`.

```python
async with panel.drawing(background=(0, 0, 20)):
    await panel.fill_rect(8, 8, 20, 20, (255, 0, 0))
    await panel.draw_points([(i, i) for i in range(64)], (255, 255, 255))
```

For animation, put several draw commands in one frame and skip acks (~30 fps):

```python
from ysmatrix import commands as cmd

await panel.draw_batch([
    cmd.draw_rect(x0, y0, x1, y1, (0, 0, 20)),            # erase the old position
    cmd.draw_rect(nx0, ny0, nx1, ny1, (255, 160, 0)),     # draw the new one
], ack=False)
```

## Games

```python
await panel.start_game(0)        # 0 Tetris, 1 Snake
await panel.game_key("start")
await panel.game_key("left")
await panel.exit_game()
```

## Errors

| Exception | Meaning |
|---|---|
| `UnsupportedCommand` | The panel answered error 3: this firmware does not implement the command |
| `PanelError` | Any other error code (`.code`) |
| `NoAck` | No acknowledgement after 3 tries |
| `ConnectionError` | No panel found |

## Low level

Every command is a pure function in `ysmatrix.commands` that returns bytes; `send()` and `query()`
take those bytes. This is the easiest way to experiment with things the library does not wrap yet.

```python
from ysmatrix import commands as cmd

await panel.send(cmd.brightness(5))
raw = await panel.query(cmd.query(cmd.TAG_ROTATE))
```

See [the API reference](../reference.md) for every method.
