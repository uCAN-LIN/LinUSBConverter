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
