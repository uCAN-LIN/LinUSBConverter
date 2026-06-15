"""Offline tests for LINFrame signal encode/decode/diff (no hardware needed)."""
from ucanlintools.LINFrame import LINFrame


def make_frame():
    signals = [
        {"name": "A", "size_bits": 8, "default_val": [0]},
        {"name": "B", "size_bits": 8, "default_val": [0]},
    ]
    return LINFrame(0x10, 2, "TWO_BYTES", signals, "Master")


def test_bitstring_built_from_signal_sizes():
    assert make_frame().bitsting == "u8u8"


def test_encode_packs_signals_in_order():
    f = make_frame()
    assert f.encode({"A": 1, "B": 2}) == b"\x01\x02"


def test_encode_partial_keeps_other_signal():
    f = make_frame()
    f.encode({"A": 7, "B": 9})
    assert f.encode({"A": 3}) == b"\x03\x09"


def test_decode_updates_signal_values():
    f = make_frame()
    f.decode(b"\x03\x04")
    assert f.signals[0]["value"][0] == 3
    assert f.signals[1]["value"][0] == 4


def test_diff_str_reports_all_then_only_changes():
    f = make_frame()
    f.decode(b"\x00\x00")
    first = f.diff_str()
    assert "'A' : 0" in first and "'B' : 0" in first

    f.decode(b"\x05\x00")
    second = f.diff_str()
    assert "'A' : 5" in second
    assert "'B'" not in second
