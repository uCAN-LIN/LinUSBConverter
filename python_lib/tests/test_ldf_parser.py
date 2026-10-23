"""Offline tests for the LDF parser using a bundled sample LDF (no hardware)."""
from ucanlintools.LDF_parser import parseLDF


def test_parse_frames_by_name_and_id(sample_ldf_path):
    ldf = parseLDF(sample_ldf_path)
    assert ldf.get_message_by_name("FRAME_A").id == 52
    assert ldf.get_message_by_id(54).name == "FRAME_B"


def test_frame_order_preserved(sample_ldf_path):
    ldf = parseLDF(sample_ldf_path)
    assert ldf.frames[0].id == 52


def test_signal_attached_to_frame(sample_ldf_path):
    ldf = parseLDF(sample_ldf_path)
    m = ldf.get_message_by_id(52)
    assert [s["name"] for s in m.signals] == ["SIGNAL_A"]
    assert m.signals[0]["size_bits"] == 8


def test_encode_decode_via_ldf(sample_ldf_path):
    ldf = parseLDF(sample_ldf_path)
    m = ldf.get_message_by_id(52)
    assert m.encode({"SIGNAL_A": 1}) == b"\x01"
    m.decode(b"\x00")
    assert m.diff_str() == "{'SIGNAL_A' : 0}"


SINGLE_FRAME_LDF = """LIN_description_file;
LIN_protocol_version = "2.1";
LIN_language_version = "2.1";
LIN_speed = 19.2 kbps;

Nodes {
  Master: BCM, 5 ms, 0.1 ms;
  Slaves: Seat;
}

Signals {
  vehicle_speed: 16, 0, BCM, Seat;
}

Frames {
  SpeedFrame: 16, BCM, 2 {
    vehicle_speed, 0;
  }
}
"""


def test_single_frame_single_signal_ldf(tmp_path):
    # Regression: a lone frame/signal used to be inlined by the grammar
    # and the parser failed with KeyError: 'frames'.
    p = tmp_path / "single.ldf"
    p.write_text(SINGLE_FRAME_LDF)
    f = parseLDF(str(p)).get_message_by_name("SpeedFrame")
    assert f.encode({"vehicle_speed": 0x1234}) == b"\x34\x12"
    assert f.decode(b"\x78\x56") == (0x5678,)
