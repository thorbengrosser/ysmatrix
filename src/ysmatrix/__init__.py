"""ysmatrix: control YS…/TL… Bluetooth LED matrix panels (LOY PLAY / LOY SPACE app compatible). Unofficial.

Quick start::

    from ysmatrix import Client

    with Client() as panel:          # first panel found; or Client("<address>")
        panel.set_brightness(10)
        panel.send_text("Hello!")

See the docs/ folder for the CLI, the library API and the protocol.
"""
from . import commands, framing, ystp
from .__version__ import __version__
from .client import AsyncClient, Client
from .images import Resize
from .models import DeviceInfo, PanelParams, Slot
from .transport import NoAck, PanelError, UnsupportedCommand, scan

__all__ = [
    "AsyncClient", "Client", "Resize", "DeviceInfo", "PanelParams", "Slot",
    "PanelError", "UnsupportedCommand", "NoAck", "scan", "commands", "framing", "ystp", "__version__",
]
