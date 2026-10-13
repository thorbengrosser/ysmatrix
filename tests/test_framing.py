"""Frames we build must match bytes the official app put on the wire."""
from ysmatrix import commands as cmd
from ysmatrix import framing

import vectors as v


def _rebuild(raw: bytes, payload: bytes) -> bytes:
    return framing.build_frame(payload, framing.parse_frame(raw).sno)


def test_captured_frames_have_valid_checksums():
    for raw in [v.FRAME_POWER_ON, v.FRAME_POWER_OFF, v.FRAME_BRIGHTNESS_11, v.FRAME_PLAY_SINGLE_3,
                v.FRAME_PLAY_LOOP_ALL, v.NOTIFY_ACK_OK, *v.UPLOAD_SLOT9_FRAMES]:
        assert framing.parse_frame(raw).checksum_ok


def test_power_brightness_play_match_the_app():
    assert _rebuild(v.FRAME_POWER_ON, cmd.power(True)) == v.FRAME_POWER_ON
    assert _rebuild(v.FRAME_POWER_OFF, cmd.power(False)) == v.FRAME_POWER_OFF
    assert _rebuild(v.FRAME_BRIGHTNESS_11, cmd.brightness(11)) == v.FRAME_BRIGHTNESS_11
    assert _rebuild(v.FRAME_PLAY_SINGLE_3, cmd.play(3)) == v.FRAME_PLAY_SINGLE_3
    loop_ids = list(framing.parse_frame(v.FRAME_PLAY_LOOP_ALL).payload[4:])
    assert _rebuild(v.FRAME_PLAY_LOOP_ALL, cmd.play_loop(loop_ids)) == v.FRAME_PLAY_LOOP_ALL


def test_ack_parses():
    ack = framing.parse_ack(framing.parse_frame(v.NOTIFY_ACK_OK))
    assert ack is not None and ack.ok


def test_tlv_lengths_roundtrip():
    for n in (0, 5, 127, 128, 255, 256, 960):
        payload = framing.tlv(19, bytes(n))
        assert framing.parse_tlvs(payload) == [(19, bytes(n))]


def test_split_frames():
    stream = v.FRAME_POWER_ON + v.FRAME_BRIGHTNESS_11
    assert [f.payload for f in framing.split_frames(stream)] == [cmd.power(True), cmd.brightness(11)]
