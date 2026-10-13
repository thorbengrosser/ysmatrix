from datetime import datetime

from ysmatrix import framing
from ysmatrix.models import DeviceInfo, PanelParams, Slot, parse_time

import vectors as v


def _value(reply):
    return framing.parse_tlvs(reply)[0][1]


def test_device_info():
    info = DeviceInfo.parse(_value(v.DEVICE_INFO_REPLY))
    assert (info.serial, info.model, info.firmware) == ("123456789", "EXYB-AS#GGMJXZ180", "V2.9.1#V16")
    assert info.mtu == 512 and "HS:2" in info.capabilities


def test_panel_params():
    p = PanelParams.parse(_value(v.PARAM_DEV_REPLY))
    assert (p.width, p.height, p.color_type) == (64, 64, 3)


def test_slots():
    slots = Slot.parse_many(_value(v.SLOTS_0_9_REPLY))
    assert [s.slot for s in slots] == list(range(10))
    assert slots[9].key.hex() == "5abc3f9232693773d9ace159f15b2e4c"  # same key the app committed
    assert not slots[0].empty
    assert Slot(11, 0, bytes(16)).empty


def test_time():
    assert parse_time(_value(v.TIME_REPLY)) == datetime(2026, 10, 13, 14, 54, 55)
    assert parse_time(_value(v.TIME_REPLY_UNSET)) == datetime(2000, 1, 1, 0, 20, 25)
