"""A bouncing square drawn live at ~30 fps (asyncio, fire-and-forget frames)."""
import asyncio
import time

from ysmatrix import AsyncClient
from ysmatrix import commands as cmd

BG, FG, R = (0, 0, 20), (255, 160, 0), 3


async def main(seconds: float = 15) -> None:
    async with AsyncClient() as panel:
        w, h = await panel.get_size()
        async with panel.drawing(background=BG):
            x, y, dx, dy = 10, 20, 2, 1
            end = time.time() + seconds
            while time.time() < end:
                erase = cmd.draw_rect(x - R, y - R, x + R, y + R, BG)
                x, y = x + dx, y + dy
                if not R <= x <= w - 1 - R:
                    dx, x = -dx, min(max(x, R), w - 1 - R)
                if not R <= y <= h - 1 - R:
                    dy, y = -dy, min(max(y, R), h - 1 - R)
                await panel.draw_batch([erase, cmd.draw_rect(x - R, y - R, x + R, y + R, FG)], ack=False)


asyncio.run(main())
