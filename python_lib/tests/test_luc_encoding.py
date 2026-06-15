"""Offline tests for the SLCAN transmit-line encoding (no hardware needed)."""
from ucanlintools.LUC import LUC


def test_format_bytes():
    assert LUC._format_transmit_line(0x16, b"\x11\x22\x33") == b"t0163112233\r"


def test_format_int_even_length():
    # Matches the documented frame 't00122233' (id 1, two data bytes 0x22 0x33).
    assert LUC._format_transmit_line(0x1, 0x2233) == b"t00122233\r"


def test_format_int_small_keeps_leading_zero():
    # Regression: a small int (0x05) must encode as one byte '05', not '5'.
    assert LUC._format_transmit_line(0x0C, 0x05) == b"t00c105\r"


def test_format_empty_payload():
    assert LUC._format_transmit_line(0x10, b"") == b"t0100\r"


def test_format_full_eight_bytes():
    data = bytes(range(8))
    assert LUC._format_transmit_line(0x3F, data) == b"t03f80001020304050607\r"
