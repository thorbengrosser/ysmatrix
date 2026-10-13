from datetime import datetime

import pytest

from ysmatrix import commands as cmd
from ysmatrix import framing


def test_set_time_layout():
    t = cmd.set_time(datetime(2026, 10, 13, 9, 5, 7, 123000))
    assert t == bytes([5, 9, 26, 0, 10, 13, 9, 5, 7]) + (123).to_bytes(2, "little")


def test_draw_rect_and_bitmap():
    assert cmd.draw_rect(1, 2, 3, 4, (9, 8, 7)) == bytes([50, 13, 1, 9, 8, 7, 0, 1, 0, 2, 0, 3, 0, 4, 0])
    bm = cmd.draw_bitmap(0, 0, [[1, 0, 1, 0, 0, 0, 0, 0, 1]], (1, 2, 3))
    assert framing.parse_tlvs(bm)[0][1][12:] == bytes([0b10100000, 0b10000000])


def test_draw_points_bounding_box():
    value = framing.parse_tlvs(cmd.draw_points([(5, 5), (6, 7)], (1, 1, 1)))[0][1]
    assert value[4:12] == bytes([5, 0, 5, 0, 6, 0, 7, 0])


def test_games_and_settings():
    assert cmd.game_start(cmd.GAME_DRAW) == bytes([48, 1, 144])
    assert cmd.game_key("exit") == bytes([48, 1, 101])
    assert cmd.rotate(6) == bytes([47, 1, 2])
    with pytest.raises(ValueError):
        cmd.brightness(0)
