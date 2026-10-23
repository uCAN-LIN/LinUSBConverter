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


def make_nibble_frame():
    # Buttons_Status from examples/example_LDF.ldf: three 4-bit signals.
    signals = [
        {"name": "button_1", "bit_offset": 0, "size_bits": 4, "default_val": [0]},
        {"name": "button_2", "bit_offset": 4, "size_bits": 4, "default_val": [0]},
        {"name": "backlight_status", "bit_offset": 8, "size_bits": 4, "default_val": [0]},
    ]
    return LINFrame(12, 2, "Buttons_Status", signals, "Slave")


def test_decode_uses_lin_bit_order():
    # LIN packs signals LSB first: bit_offset 0 is the low nibble of byte 0.
    assert make_nibble_frame().decode(b"\x21\x03") == (1, 2, 3)


def test_encode_uses_lin_bit_order_and_frame_length():
    f = make_nibble_frame()
    assert f.encode({"button_1": 1, "button_2": 2, "backlight_status": 3}) == b"\x21\x03"


def test_signal_at_offset_inside_wider_frame():
    signals = [{"name": "level", "bit_offset": 12, "size_bits": 4, "default_val": [0]}]
    f = LINFrame(0x20, 4, "WIDE", signals, "Master")
    assert f.encode({"level": 0xA}) == b"\x00\xa0\x00\x00"
    assert f.decode(b"\x00\x50\x00\x00") == (5,)


def test_decode_does_not_change_ldf_default():
    signals = [{"name": "A", "size_bits": 8, "default_val": [7]}]
    f = LINFrame(0x10, 1, "ONE", signals, "Master")
    f.decode(b"\x01")
    assert signals[0]["default_val"] == [7]
