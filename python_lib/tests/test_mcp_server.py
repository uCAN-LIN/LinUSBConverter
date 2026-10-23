"""Offline tests for the MCP server against its simulated bus (no hardware needed)."""
import pytest

pytest.importorskip("mcp")

from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

import ucanlintools.mcp_server as srv  # noqa: E402


@pytest.fixture(autouse=True)
def mock_server():
    srv.conv = srv.Converter(None, mock=True)
    srv.allow_tx = False
    srv.ldf = None
    yield


def test_monitor_sees_simulated_frames():
    r = srv.monitor_bus(0.5)
    ids = {row["id"]: row for row in r["ids"]}
    assert set(ids) == {"0x0B", "0x0C"}
    assert ids["0x0C"]["length"] == 2
    assert 15 <= ids["0x0C"]["period_ms"] <= 25


def test_wrong_speed_sees_nothing_and_detect_finds_it():
    assert srv.monitor_bus(0.3, speed=9600)["frames"] == 0
    best = srv.detect_bus(0.3)["best"]
    assert (best["speed"], best["checksum"]) == (19200, "enhanced")


def test_ldf_decode_is_lsb_first():
    srv.load_ldf("mock")
    v = srv.decode_frame("0x0C", "05 28")["signals"]
    assert v == {"button_up": 1, "button_down": 0, "heater_level": 1, "seat_temp": 40}


def test_encode_roundtrip_and_defaults():
    srv.load_ldf("mock")
    out = srv.encode_frame("SeatStatus", {"button_down": 1, "seat_temp": 30})
    assert out == {"id": "0x0C", "name": "SeatStatus", "data": "02 1e"}
    with pytest.raises(ToolError):
        srv.encode_frame("SeatStatus", {"heater_level": 4})


def test_transmit_needs_flag():
    with pytest.raises(ToolError):
        srv.send_frame("0x0B", "01")
    with pytest.raises(ToolError):
        srv.run_master(0.2, receive=[{"id": "0x0C", "length": 2}])


def test_send_frame_echo_is_header_only():
    srv.allow_tx = True
    r = srv.send_frame("0x16", "11 22 33", repeat=2)
    row = next(x for x in r["ids"] if x["id"] == "0x16")
    assert row["count"] == 0 and row["headers_only"] == 2


def test_master_polls_slave_and_reports_missing():
    srv.allow_tx = True
    r = srv.run_master(0.5, receive=[{"id": "0x0C", "length": 2},
                                     {"id": "0x20", "length": 4}])
    assert [x["id"] for x in r["ids"]] == ["0x0C"]
    assert r["no_response"] == ["0x20"]


def test_rejects_bad_input():
    srv.allow_tx = True
    for call in (lambda: srv.monitor_bus(0),
                 lambda: srv.monitor_bus(1, checksum="crc"),
                 lambda: srv.send_frame("0x40", "00"),
                 lambda: srv.send_frame("0x10", "00 11 22 33 44 55 66 77 88")):
        with pytest.raises(ToolError):
            call()
