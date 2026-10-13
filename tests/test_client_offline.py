"""Drive the high-level clients against a fake connection (no Bluetooth needed)."""
import asyncio
import io

from PIL import Image

from ysmatrix import AsyncClient, Client
from ysmatrix import commands as cmd
from ysmatrix import framing

import vectors as v


class FakeConnection:
    def __init__(self):
        self.sent: list[bytes] = []

    async def send(self, payload, *, ack=True):
        self.sent.append(payload)

    async def query(self, payload):
        replies = {cmd.TAG_PANEL_PARAMS: v.PARAM_DEV_REPLY, cmd.TAG_DEVICE_INFO: v.DEVICE_INFO_REPLY,
                   cmd.TAG_SET_TIME: v.TIME_REPLY}
        reply = replies.get(payload[0])
        return framing.parse_tlvs(reply)[0][1] if reply else None

    async def close(self):
        pass


def _client():
    c = AsyncClient("fake")
    c.conn = FakeConnection()
    return c


def test_send_image_uploads_then_plays():
    c = _client()
    asyncio.run(c.send_image(Image.new("RGB", (32, 20), (255, 0, 0)), slot=5))
    sent = c.conn.sent
    assert sent[0][:4] == bytes([cmd.TAG_DELETE, 2, 0, 5])
    assert sent[-3][0] == cmd.TAG_PROGRAM_KEY
    assert sent[-2:] == [cmd.power(True), cmd.play(5)]  # showing switches the display on
    blob = b"".join(dict(framing.parse_tlvs(p))[cmd.TAG_CHUNK_DATA] for p in sent[2:-3])
    assert blob[:6] == b"YSTP01" and blob[6:10] == bytes([64, 0, 64, 0])  # resized to the panel


def test_animated_input_is_sent_as_gif():
    frames = [Image.new("RGB", (64, 64), c) for c in ((255, 0, 0), (0, 0, 255))]
    buf = io.BytesIO()
    frames[0].save(buf, "GIF", save_all=True, append_images=frames[1:], duration=500, loop=0)
    c = _client()
    asyncio.run(c.send_image(buf.getvalue(), slot=1, show=False))
    timing = dict(framing.parse_tlvs(c.conn.sent[0]))[cmd.TAG_PROGRAM_TIMING]
    assert timing[4:6] == (1).to_bytes(2, "little")  # 2 x 0.5 s -> 1 s play time
    data = dict(framing.parse_tlvs(c.conn.sent[2]))[cmd.TAG_CHUNK_DATA]
    assert data[:6] == b"GIF89a"


def test_info_and_time():
    c = _client()
    assert asyncio.run(c.get_size()) == (64, 64)
    assert asyncio.run(c.get_device_info()).firmware == "V2.9.1#V16"
    assert asyncio.run(c.get_time()).year == 2026


def test_sync_client_proxies_methods(monkeypatch):
    async def fake_connect(self):
        self.conn = FakeConnection()

    monkeypatch.setattr(AsyncClient, "connect", fake_connect)
    with Client() as panel:
        panel.set_brightness(7)
        with panel.drawing():
            panel.fill_rect(0, 0, 3, 3, (1, 2, 3))
        sent = panel._async.conn.sent
    assert sent[0] == cmd.brightness(7)
    assert sent[1] == cmd.game_start(cmd.GAME_DRAW) and sent[-1] == cmd.game_key("exit")
