import pytest

from ysmatrix.cli import build_parser, color


def test_colours():
    assert color("red") == (255, 0, 0)
    assert color("#ff8000") == (255, 128, 0)
    assert color("1,2,3") == (1, 2, 3)
    with pytest.raises(Exception):
        color("nope")


def test_parser_accepts_documented_commands():
    p = build_parser()
    assert p.parse_args(["text", "Hi", "-c", "green", "--static"]).static
    assert p.parse_args(["loop", "0", "10", "9"]).slots == [0, 10, 9]
    assert p.parse_args(["-a", "XX", "brightness", "8"]).level == 8
    with pytest.raises(SystemExit):
        p.parse_args(["brightness", "16"])


def test_name_option():
    assert build_parser().parse_args(["-n", "YS123", "play", "1"]).name == "YS123"
