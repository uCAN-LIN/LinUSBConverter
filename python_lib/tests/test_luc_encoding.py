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


# --- reception parsing ---------------------------------------------------------

import sys  # noqa: E402
import time  # noqa: E402

# the package re-exports the LUC class under the module's name
luc_module = sys.modules[LUC.__module__]


def test_parse_frame_line():
    f = LUC._parse_frame_line("t00C20128")
    assert (f.id, f.data) == (0x0C, b"\x01\x28")


def test_parse_frame_line_skips_reply_prefix_and_junk():
    assert LUC._parse_frame_line("zt0160").data == b""          # echo after a 'z' reply
    assert LUC._parse_frame_line("z") is None
    assert LUC._parse_frame_line("t00C2") is None              # data missing
    assert LUC._parse_frame_line("t0zz101") is None


class _FakeSerial:
    """Serial port that delivers all its bytes in one read, like a busy bus
    filling a USB packet with several frames."""

    def __init__(self, *args, **kwargs):
        self.rx = b"t00B105\rt00C20128\rz\rt00B106\r"

    @property
    def in_waiting(self):
        return len(self.rx)

    def read(self, n):
        data, self.rx = self.rx[:n], self.rx[n:]
        return data

    def write(self, data):
        pass

    def reset_input_buffer(self):
        pass

    def reset_output_buffer(self):
        pass

    def readline(self):
        return b"z\r"

    def flush(self):
        pass

    def close(self):
        pass


def test_back_to_back_frames_are_all_delivered(monkeypatch):
    monkeypatch.setattr(luc_module.serial, "Serial", _FakeSerial)
    lin = LUC("FAKE")
    got = []
    lin.set_frame_rx_handler(lambda f: got.append((f.id, f.data)))
    lin.enable()
    deadline = time.time() + 2
    while len(got) < 3 and time.time() < deadline:
        time.sleep(0.01)
    lin.disable()
    lin.deInitSerial()
    assert got == [(0x0B, b"\x05"), (0x0C, b"\x01\x28"), (0x0B, b"\x06")]
