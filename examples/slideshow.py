"""Upload every picture/GIF in a folder to its own slot and cycle through them.

    python examples/slideshow.py ~/Pictures/panel
"""
import sys
from pathlib import Path

from ysmatrix import Client

folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp"})[:60]

with Client() as panel:
    for slot, path in enumerate(files):
        print(f"slot {slot}: {path.name}")
        panel.send_image(path, slot=slot, show=False)
    panel.play_loop(range(len(files)))
