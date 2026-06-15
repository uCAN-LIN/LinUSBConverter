"""Hardware tests for the LUC driver.

Single-dongle tests use the ``master_port`` fixture (COM3 by default).
The two-dongle communication test needs both ``master_port`` and
``slave_port`` (COM33 by default). Tests skip automatically if a required
dongle cannot be opened.
"""
import time

import pytest

from ucanlintools.LUC import LUC

BAUD = 19200


# --------------------------------------------------------------------------- #
# Single-dongle tests
# --------------------------------------------------------------------------- #
def test_firmware_version(master_port):
    lin = LUC(master_port, baudrate=BAUD)
    try:
        lin.close()
        fw = lin.requestFirmwareVersion()
        assert fw, "expected a non-empty firmware version string"
        assert all(c in "0123456789abcdefABCDEF" for c in fw), fw
    finally:
        lin.deInitSerial()


def test_mode_switching(master_port):
    lin = LUC(master_port, baudrate=BAUD)
    try:
        assert lin.close() is True
        assert lin.highSpeed() is True
        assert lin.lowSpeed() is True
        assert lin.openAsMaster() is True
        assert lin.close() is True
        assert lin.openAsSlave() is True
        assert lin.close() is True
        assert lin.openAsMonitor() is True
    finally:
        lin.deInitSerial()


def test_monitor_transmit_loopback(master_port):
    """In monitor mode a transmitted frame is echoed back from the bus.

    The converter reports its own transmitted header as a received frame, so
    we assert on the frame id (the looped-back payload is empty by design).
    """
    received = []
    lin = LUC(master_port, baudrate=BAUD)
    lin.set_frame_rx_handler(lambda f: received.append(f.id))
    try:
        lin.close()
        lin.highSpeed()
        assert lin.openAsMonitor() is True
        lin.enable()
        time.sleep(0.1)
        for _ in range(5):
            assert lin.addTransmitFrameToTable(0x16, b"\x11\x22\x33") is True
            time.sleep(0.05)
        time.sleep(0.3)
        lin.disable()
        assert 0x16 in received, received
    finally:
        lin.deInitSerial()


def test_close_and_deinit_are_idempotent(master_port):
    """disable()/deInitSerial() must be safe to call repeatedly (regression)."""
    lin = LUC(master_port, baudrate=BAUD)
    lin.close()
    lin.openAsMonitor()
    lin.enable()
    time.sleep(0.1)
    lin.disable()
    lin.deInitSerial()
    # Second round must not raise.
    lin.disable()
    lin.deInitSerial()


# --------------------------------------------------------------------------- #
# Two-dongle master <-> slave test
# --------------------------------------------------------------------------- #
def test_master_slave_communication(master_port, slave_port):
    """Master transmits frame id 1 = 0x2233; slave must receive it."""
    received = []

    master = LUC(master_port, baudrate=BAUD)
    slave = LUC(slave_port, baudrate=BAUD)
    slave.set_frame_rx_handler(lambda f: received.append(f))
    try:
        master.close()
        slave.close()
        master.lowSpeed()
        slave.lowSpeed()

        assert master.openAsMaster() is True
        assert slave.openAsSlave() is True

        assert master.addTransmitFrameToTable(0x01, 0x2233) is True
        assert slave.addReceptionFrameToTable(0x01, 2) is True

        slave.enable()
        master.enable()

        time.sleep(1.0)

        slave.disable()
        master.disable()

        assert received, "slave received no frames"
        last = received[-1]
        assert last.id == 0x01
        assert int.from_bytes(last.data, "big") == 0x2233
    finally:
        master.deInitSerial()
        slave.deInitSerial()
