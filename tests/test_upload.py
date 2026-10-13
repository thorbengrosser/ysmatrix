"""A whole still-image upload, rebuilt from scratch, must equal the app's six frames."""
import struct

from ysmatrix import commands as cmd
from ysmatrix import framing, ystp

import vectors as v


def test_still_upload_is_byte_identical():
    frames = [framing.parse_frame(raw) for raw in v.UPLOAD_SLOT9_FRAMES]
    tlvs = [dict(framing.parse_tlvs(f.payload)) for f in frames]
    blob = b"".join(t[cmd.TAG_CHUNK_DATA] for t in tlvs if cmd.TAG_CHUNK_DATA in t)
    commit = tlvs[-1][cmd.TAG_PROGRAM_KEY]
    slot, key, ts = commit[0], commit[5:21], struct.unpack_from("<I", commit, 21)[0]

    image = ystp.decode(blob)
    reencoded = ystp.encode(image.pages, image.width, image.height)
    assert reencoded == blob

    payloads = cmd.graphic_upload(slot, reencoded, image.width, image.height, key=key, timestamp=ts)
    assert [framing.build_frame(p, f.sno) for p, f in zip(payloads, frames)] == v.UPLOAD_SLOT9_FRAMES


def test_slot_prefix_matches_the_app():
    commit = dict(framing.parse_tlvs(framing.parse_frame(v.UPLOAD_SLOT9_FRAMES[-1]).payload))[cmd.TAG_PROGRAM_KEY]
    assert struct.unpack_from("<I", commit, 1)[0] == cmd.slot_id_prefix(9) == 0x10
    assert cmd.slot_id_prefix(7) == 0x80


def test_text_upload_structure():
    body = cmd.text_body("Hi {hh}:{mm}", clock_fields=True)
    assert body.endswith(b"Hi \x06\x02\x03:\x06\x02\x04")
    payloads = cmd.text_upload(4, body, 64, 64)
    header = dict(framing.parse_tlvs(payloads[1]))
    assert header[cmd.TAG_ITEM_TYPE][3] == cmd.ITEM_TEXT
    data = b"".join(dict(framing.parse_tlvs(p))[cmd.TAG_CHUNK_DATA] for p in payloads[2:-1])
    assert data == body


def test_large_data_is_chunked():
    chunks = cmd.data_chunks(0, bytes(2500))
    assert len(chunks) == 3
    assert [len(dict(framing.parse_tlvs(c))[cmd.TAG_CHUNK_DATA]) for c in chunks] == [960, 960, 580]
