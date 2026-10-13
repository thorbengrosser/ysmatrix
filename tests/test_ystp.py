from ysmatrix import ystp


def _bpp(colors):
    return ystp.encode([b"".join(bytes(c) for c in colors)], len(colors), 1)[14]


def test_colour_depth_steps():
    assert _bpp([(0, 0, 0), (1, 1, 1)]) == 1
    assert _bpp([(i, 0, 0) for i in range(3)]) == 2
    assert _bpp([(i, 0, 0) for i in range(5)]) == 4
    assert _bpp([(i, 0, 0) for i in range(17)]) == 8
    assert _bpp([(i % 256, i // 256, 0) for i in range(257)]) == 24


def test_roundtrip_with_odd_width():
    page = bytes((x * 40) % 256 for x in range(7 * 3 * 3))
    img = ystp.decode(ystp.encode([page], 7, 3))
    assert img.pages == [page]


def test_top_left_pixel_first():
    page = bytes([255, 0, 0]) + bytes(3 * 3)
    blob = ystp.encode([page], 2, 2)
    assert blob[15:18] == b"\xff\x00\x00"  # palette entry 0 = first pixel scanned
