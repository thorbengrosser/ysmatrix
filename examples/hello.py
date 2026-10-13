"""The basics with the blocking client: info, brightness, text."""
from ysmatrix import Client

with Client() as panel:
    info = panel.get_device_info()
    print(f"{info.model} {info.firmware}, {panel.get_size()}")
    panel.set_brightness(10)
    panel.send_text("Hello from ysmatrix", slot=0, color=(0, 255, 0))
