"""Sync the panel clock and show date and time in two lines."""
from ysmatrix import Client

with Client() as panel:
    panel.send_clock("{DD}.{MM}.  {hh}:{mm}", slot=0, size=16, color=(0, 200, 255))
