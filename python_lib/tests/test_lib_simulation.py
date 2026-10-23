"""Library-level master/slave simulation (scripted examples/MasterSimulation.py + SlaveSimulation.py).

Master publishes ``Backlight`` (LDF-encoded), slave answers ``Buttons_Status``.
Both sides change their data while the bus is running. Needs both dongles on
one powered LIN bus.
"""
import os
import time

import pytest

from ucanlintools.LDF_parser import parseLDF
from ucanlintools.LUC import LUC

EXAMPLE_LDF = os.path.join(os.path.dirname(__file__), "..", "examples", "example_LDF.ldf")


@pytest.mark.parametrize("speed", ["high", "low"])
def test_ldf_master_slave_simulation(master_port, slave_port, speed):
    ldf = parseLDF(EXAMPLE_LDF)
    backlight = ldf.get_message_by_name("Backlight")
    buttons = ldf.get_message_by_name("Buttons_Status")

    master_rx, master_new, slave_rx = [], [], []
    master = LUC(master_port, baudrate=19200)
    slave = LUC(slave_port, baudrate=19200)
    master.set_frame_rx_handler(lambda f: master_rx.append((f.id, bytes(f.data))))
    master.set_new_frame_rx_handler(lambda f: master_new.append((f.id, bytes(f.data))))
    slave.set_frame_rx_handler(lambda f: slave_rx.append((f.id, bytes(f.data))))
    try:
        for d in (master, slave):
            d.close()
            assert (d.lowSpeed() if speed == "low" else d.highSpeed()) is True

        assert slave.openAsSlave() is True
        assert slave.addReceptionFrameToTable(backlight.id, backlight.len) is True
        assert slave.addTransmitFrameToTable(buttons.id, b"\x00\x00") is True
        assert master.openAsMaster() is True
        assert master.addReceptionFrameToTable(buttons.id, buttons.len) is True
        assert master.addTransmitFrameToTable(backlight.id, backlight.encode({"backlight_level": 1})) is True

        slave.enable()
        master.enable()
        time.sleep(1.0)
        slave.addTransmitFrameToTable(buttons.id, (0x0301).to_bytes(2, "little"))   # buttons pressed
        master.addTransmitFrameToTable(backlight.id, backlight.encode({"backlight_level": 7}))
        time.sleep(1.0)
        slave.disable()
        master.disable()
    finally:
        master.deInitSerial()
        slave.deInitSerial()
        time.sleep(0.2)

    bl = [d for i, d in slave_rx if i == backlight.id]
    bs = [d for i, d in master_rx if i == buttons.id]
    assert len(bl) >= 20 and len(bs) >= 20
    assert bl[0] == bytes(backlight.encode({"backlight_level": 1}))
    assert bl[-1] == bytes(backlight.encode({"backlight_level": 7}))
    assert bs[0] == b"\x00\x00" and bs[-1] == b"\x01\x03"

    # LIN bit order: byte 0 = 0x01 -> button_1 (bits 0-3) = 1, button_2 (bits 4-7) = 0,
    # byte 1 = 0x03 -> backlight_status (bits 8-11) = 3
    assert buttons.decode(bs[-1]) == (1, 0, 3)
    assert "'button_1' : 1" in buttons.diff_str()
    # new-frame handler fires once per distinct payload only
    assert [d for i, d in master_new if i == buttons.id] == [b"\x00\x00", b"\x01\x03"]
