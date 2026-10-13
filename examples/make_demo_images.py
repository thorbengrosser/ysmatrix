"""Generate two original 64x64 demo images with Pillow and a hand-made 5x7 pixel font.

    python examples/make_demo_images.py          # writes examples/images/*.gif|png (+ 8x previews)
    ysmatrix image examples/images/all_your_base.gif --slot 20
    ysmatrix image examples/images/led_backpack.png --slot 21
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

W = H = 64
OUT = Path(__file__).parent / "images"

# 5x7 font: each glyph is 7 rows of 5 bits (MSB = leftmost pixel)
FONT = {
    "A": [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11], "B": [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
    "C": [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E], "D": [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E],
    "E": [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F], "F": [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10],
    "G": [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F], "H": [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    "I": [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E], "J": [0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C],
    "K": [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11], "L": [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F],
    "M": [0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11], "N": [0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11],
    "O": [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E], "P": [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10],
    "Q": [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D], "R": [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11],
    "S": [0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E], "T": [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04],
    "U": [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E], "V": [0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04],
    "W": [0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A], "X": [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11],
    "Y": [0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04], "Z": [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F],
    "!": [0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04], ".": [0, 0, 0, 0, 0, 0x0C, 0x0C],
    "-": [0, 0, 0, 0x1F, 0, 0, 0], " ": [0] * 7,
}


def text_width(text: str, scale: int = 1) -> int:
    return len(text) * 6 * scale - scale


def draw_text(img: Image.Image, text: str, x: int, y: int, color, scale: int = 1, shadow=None) -> None:
    px = img.load()
    for layer, (dx, dy, c) in enumerate([(1, 1, shadow), (0, 0, color)]):
        if c is None:
            continue
        cx = x + dx
        for ch in text.upper():
            for row, bits in enumerate(FONT.get(ch, FONT[" "])):
                for col in range(5):
                    if bits & (0x10 >> col):
                        for sy in range(scale):
                            for sx in range(scale):
                                X, Y = cx + col * scale + sx, y + dy + row * scale + sy
                                if 0 <= X < W and 0 <= Y < H:
                                    px[X, Y] = c
            cx += 6 * scale


# --- 1. ALL YOUR BASE ARE BELONG TO US (animated) ------------------------------------

SHIP = [  # original 11x7 sprite: 1 hull, 2 cockpit, 3 engine glow
    "....11.....",
    "...1111....",
    "3311221111.",
    "33111111111",
    "3311221111.",
    "...1111....",
    "....11.....",
]
SHIP_COLORS = {"1": (170, 180, 200), "2": (60, 200, 255), "3": (255, 140, 0)}


def all_your_base() -> list[Image.Image]:
    rng = random.Random(1989)
    stars = [[rng.randrange(W), rng.randrange(0, 40), rng.choice([1, 1, 2])] for _ in range(28)]
    lines = ["ALL YOUR BASE", "ARE BELONG", "TO US!"]
    phrase = "ALL YOUR BASE ARE BELONG TO US!"
    span = text_width(phrase) + W
    frames = []
    for f in range(span // 2):
        img = Image.new("RGB", (W, H), (0, 0, 8))
        px = img.load()
        for s in stars:  # parallax starfield
            s[0] = (s[0] - s[2]) % W
            b = 255 if s[2] == 2 else 120
            px[s[0], s[1]] = (b, b, b)
        bob = round(math.sin(f / 6) * 2)
        for r, row in enumerate(SHIP):
            for c, v in enumerate(row):
                if v in SHIP_COLORS:
                    color = SHIP_COLORS[v]
                    if v == "3" and f % 4 < 2:
                        color = (255, 220, 60)  # flickering engine
                    px[24 + c, 14 + bob + r] = color
        d = ImageDraw.Draw(img)
        d.rectangle([0, 43, W - 1, 55], fill=(0, 40, 0))  # retro subtitle bar
        draw_text(img, phrase, W - 2 * f, 46, (90, 255, 90), shadow=(0, 90, 0))
        if (f // 20) % 2 == 0:  # blinking warning
            draw_text(img, "WARNING", 11, 2, (255, 60, 60))
        frames.append(img)
    return frames


# --- 2. LED BACKPACK (synthwave still) -------------------------------------------------


def led_backpack() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    horizon = 44
    for y in range(horizon):  # sky gradient: deep purple -> magenta -> orange
        t = y / horizon
        px_row = (int(40 + 215 * t), int(10 + 70 * t * t), int(90 - 40 * t))
        for x in range(W):
            px[x, y] = px_row
    cx, cy, r = 32, horizon, 15  # striped sun
    for y in range(cy - r, cy):
        if y > cy - 8 and (cy - y) % 3 == 0:
            continue
        half = int(math.sqrt(r * r - (y - cy) ** 2))
        t = (y - (cy - r)) / r
        for x in range(cx - half, cx + half + 1):
            px[x, y] = (255, int(230 - 120 * t), int(60 + 40 * t))
    for y in range(horizon, H):  # floor + perspective grid
        for x in range(W):
            px[x, y] = (20, 0, 35)
    d = ImageDraw.Draw(img)
    for i in range(-8, 9):
        d.line([(32 + i * 3, horizon), (32 + i * 14, H - 1)], fill=(255, 40, 200))
    y, step = horizon, 1
    while y < H:
        d.line([(0, y), (W - 1, y)], fill=(255, 40, 200))
        y, step = y + step, step + 1
    led_x = (W - text_width("LED", 3)) // 2
    draw_text(img, "LED", led_x, 4, (0, 255, 255), scale=3, shadow=(80, 0, 120))
    draw_text(img, "BACKPACK", (W - text_width("BACKPACK")) // 2, 28, (255, 255, 255), shadow=(120, 0, 90))
    return img


def main() -> None:
    OUT.mkdir(exist_ok=True)
    frames = all_your_base()
    frames[0].save(OUT / "all_your_base.gif", save_all=True, append_images=frames[1:], duration=60, loop=0)
    big = [f.resize((W * 8, H * 8), Image.NEAREST) for f in frames]
    big[0].save(OUT / "all_your_base_preview.gif", save_all=True, append_images=big[1:], duration=60, loop=0)
    still = led_backpack()
    still.save(OUT / "led_backpack.png")
    still.resize((W * 8, H * 8), Image.NEAREST).save(OUT / "led_backpack_preview.png")
    print(f"wrote {OUT}: all_your_base.gif ({len(frames)} frames), led_backpack.png")


if __name__ == "__main__":
    main()
