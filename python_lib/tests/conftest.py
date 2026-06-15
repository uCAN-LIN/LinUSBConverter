"""Shared pytest fixtures for the ucanlintools test suite.

Hardware tests need uCAN LIN USB converters. By default the master dongle is
expected on COM3 and the slave dongle on COM33; override with the environment
variables ``LUC_MASTER_PORT`` and ``LUC_SLAVE_PORT``. Any hardware test whose
required port cannot be opened is skipped rather than failed, so the offline
tests always run.
"""
import os
import time

import pytest
import serial

HERE = os.path.dirname(__file__)
SAMPLE_LDF = os.path.join(HERE, "fixtures", "sample.ldf")

MASTER_PORT = os.environ.get("LUC_MASTER_PORT", "COM3")
SLAVE_PORT = os.environ.get("LUC_SLAVE_PORT", "COM33")


def _port_available(port):
    """Return True if the serial port can actually be opened."""
    try:
        s = serial.Serial(port, timeout=0.1, baudrate=19200)
    except Exception:
        return False
    s.close()
    # Windows can briefly hold the handle after close; give it a moment so the
    # test that follows can reopen the port.
    time.sleep(0.05)
    return True


@pytest.fixture(scope="session")
def sample_ldf_path():
    return SAMPLE_LDF


@pytest.fixture
def master_port():
    if not _port_available(MASTER_PORT):
        pytest.skip(f"master LIN dongle {MASTER_PORT} not available")
    return MASTER_PORT


@pytest.fixture
def slave_port():
    if not _port_available(SLAVE_PORT):
        pytest.skip(f"slave LIN dongle {SLAVE_PORT} not available")
    return SLAVE_PORT
