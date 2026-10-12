"""Firmware tests over the raw serial (SLCAN-style) protocol.

These talk to the converter directly with pyserial instead of going through
``LUC`` so every reply and every reported frame can be checked byte for byte.

Single-dongle tests use ``master_port``. Two-dongle tests need both dongles on
one powered LIN bus: ``master_port`` runs as LIN master, ``slave_port`` as LIN
slave (or as monitor). Run the suite a second time with the ports swapped to
test both converters in both roles.
"""
import time

import pytest
import serial

SPEEDS = ["S1", "S2"]  # 19200 / 9600 baud


class Dongle:
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200, timeout=0.1, write_timeout=1)

    def cmd(self, line, wait=0.04):
        """Send one command, return everything received within ``wait``."""
        self.ser.write(line.encode() + b"\r")
        time.sleep(wait)
        return self.ser.read(500)

    def reset(self):
        self.ser.write(b"r2ff0\r")
        time.sleep(0.05)
        self.cmd("C")
        self.cmd("r30")  # checksum mode survives 'C', back to enhanced
        self.ser.reset_input_buffer()

    def start(self):
        self.ser.write(b"r1ff0\r")

    def drain(self):
        return self.ser.read(200000)

    def close(self):
        self.reset()
        self.ser.close()
        time.sleep(0.05)


def ack(reply):
    """Command reply lines without frame reports streamed by a running dongle."""
    return [l for l in reply.split(b"\r")[:-1] if not l.startswith(b"t")]


def assert_acked(*replies):
    for r in replies:
        assert ack(r) in ([b"z"], [b"Z"]), r


def frames(buf):
    """Parse 't0IILdata' reports -> ({id: [DATA_HEX, ...]}, [unparsable lines])."""
    out, junk = {}, []
    for l in buf.decode("ascii", "replace").split("\r"):
        if not l or l in ("z", "Z"):
            continue
        try:
            fid, n, data = int(l[2:4], 16), int(l[4], 16), l[5:]
            if l[0] == "t" and len(data) == 2 * n:
                out.setdefault(fid, []).append(data.upper())
                continue
        except (ValueError, IndexError):
            pass
        junk.append(l)
    return out, junk


def payload(fid, n):
    return "".join(f"{(fid * 16 + i) & 0xFF:02X}" for i in range(n))


@pytest.fixture
def dongle(master_port):
    d = Dongle(master_port)
    d.reset()
    yield d
    d.close()


@pytest.fixture
def pair(master_port, slave_port):
    m, s = Dongle(master_port), Dongle(slave_port)
    m.reset()
    s.reset()
    yield m, s
    m.close()
    s.close()


def start_bus(m, s, speed, master_rows, slave_rows):
    """Configure slave then master (rows after speed: timeouts depend on baud) and start both."""
    s.cmd(speed)
    s.cmd("L")
    replies = [s.cmd(r) for r in slave_rows]
    m.cmd(speed)
    m.cmd("O")
    replies += [m.cmd(r) for r in master_rows]
    assert_acked(*replies)
    s.start()
    m.start()


def run_for(m, s, seconds):
    time.sleep(seconds)
    return frames(m.drain()), frames(s.drain())


# --------------------------------------------------------------------------- #
# Single dongle: command parser robustness
# --------------------------------------------------------------------------- #
def test_firmware_version_format(dongle):
    reply = dongle.cmd("v")
    assert reply.startswith(b"v") and len(reply) == 6, reply


@pytest.mark.parametrize("line", [
    "t0C2BEEF",  # length 0xB > 8
    "r00B9",     # length 9 > 8
    "t00B1",     # data missing
    "t0ZZ1AA",   # bad id
])
def test_malformed_row_rejected_and_table_still_usable(dongle, line):
    """A rejected row must not leave state behind that blocks later rows (fixed in 3.3)."""
    dongle.cmd("O")
    assert dongle.cmd("t0091AA") == b"z\r"   # longer command first: no stale bytes reused
    assert dongle.cmd(line) == b"\r"
    assert dongle.cmd("t0011A5") == b"z\r"


def test_table_holds_16_rows_and_rejects_17th(dongle):
    dongle.cmd("O")
    for i in range(16):
        assert dongle.cmd(f"t0{i:02X}1AA") == b"z\r"
    assert dongle.cmd("t0201AA") == b"\r"
    assert dongle.cmd("t0011BB") == b"z\r"   # updating an existing row still works


def test_invalid_custom_baudrate_rejected(dongle):
    assert b"Z" not in dongle.cmd("t04ZZZZ")


# --------------------------------------------------------------------------- #
# Two dongles: master <-> slave
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("speed", SPEEDS)
def test_all_lengths_both_directions(pair, speed):
    """Full 16-row table: master publishes ids 1..8 (len 1..8), slave answers 0x11..0x18 (len 1..8)."""
    m, s = pair
    master_rows = [f"t0{i:02X}{i}{payload(i, i)}" for i in range(1, 9)] + \
                  [f"r0{0x10 + i:02X}{i}" for i in range(1, 9)]
    slave_rows = [f"r0{i:02X}{i}" for i in range(1, 9)] + \
                 [f"t0{0x10 + i:02X}{i}{payload(0x10 + i, i)}" for i in range(1, 9)]
    start_bus(m, s, speed, master_rows, slave_rows)
    (mf, mjunk), (sf, sjunk) = run_for(m, s, 4)
    assert not mjunk and not sjunk
    for i in range(1, 9):
        assert set(sf.get(i, [])) == {payload(i, i)}, f"slave rx id {i:#x}"
        assert set(mf.get(0x10 + i, [])) == {payload(0x10 + i, i)}, f"master rx id {0x10 + i:#x}"
        assert len(sf[i]) >= 3 and len(mf[0x10 + i]) >= 3


@pytest.mark.parametrize("speed", SPEEDS)
def test_live_data_update(pair, speed):
    m, s = pair
    start_bus(m, s, speed, ["t0011A5", "r0111"], ["r0011", "t0111C3"])
    run_for(m, s, 0.5)
    m.cmd("t00115A")
    s.cmd("t0111EE")
    (mf, _), (sf, _) = run_for(m, s, 1.0)
    assert sf[0x01][-1] == "5A"
    assert mf[0x11][-1] == "EE"


@pytest.mark.parametrize("speed", SPEEDS)
def test_diagnostic_frames(pair, speed):
    """0x3C master request / 0x3D slave response, 8 bytes (classic checksum)."""
    m, s = pair
    start_bus(m, s, speed, ["t03C80102030405060708", "r03D8"], ["r03C8", "t03D81122334455667788"])
    (mf, _), (sf, _) = run_for(m, s, 2)
    assert set(sf.get(0x3C, [])) == {"0102030405060708"}
    assert set(mf.get(0x3D, [])) == {"1122334455667788"}


@pytest.mark.parametrize("speed", SPEEDS)
def test_unanswered_header_does_not_stall_schedule(pair, speed):
    m, s = pair
    start_bus(m, s, speed, ["t0051A5", "r0062", "t0071C3"], ["r0051", "r0071"])
    (_, _), (sf, _) = run_for(m, s, 2)
    assert len(sf.get(0x05, [])) >= 5 and len(sf.get(0x07, [])) >= 5


@pytest.mark.parametrize("speed", SPEEDS)
def test_extended_row_format_period(pair, speed):
    """'T'/'R' rows with explicit period 0x64 (100 ms) and timeout 0x30 ms."""
    m, s = pair
    start_bus(m, s, speed, ["T00A643001A5", "R00B643002"], ["r00A1", "t00B2CAFE"])
    (mf, _), (sf, _) = run_for(m, s, 2)
    assert 6 <= len(sf.get(0x0A, [])) <= 14
    assert set(mf.get(0x0B, [])) == {"CAFE"} and 6 <= len(mf[0x0B]) <= 14


def test_checksum_mode_command(dongle):
    assert dongle.cmd("r31") == b"Z\r"
    assert dongle.cmd("r30") == b"Z\r"
    assert dongle.cmd("t31") == b"Z\r"


@pytest.mark.parametrize("speed", SPEEDS)
def test_classic_checksum_both_sides(pair, speed):
    m, s = pair
    m.cmd("r31")
    s.cmd("r31")
    start_bus(m, s, speed, ["t0011A5", "r0112"], ["r0011", "t0112BEEF"])
    (mf, _), (sf, _) = run_for(m, s, 1.5)
    assert set(sf.get(0x01, [])) == {"A5"} and len(sf[0x01]) >= 10
    assert set(mf.get(0x11, [])) == {"BEEF"} and len(mf[0x11]) >= 10


@pytest.mark.parametrize("speed", SPEEDS)
def test_checksum_mismatch_rejected(pair, speed):
    """Master classic, slave enhanced: normal frames fail the checksum on both sides
    (fixed in 3.3, the mode used to be ignored). Diagnostic frames are always classic."""
    m, s = pair
    m.cmd("r31")
    start_bus(m, s, speed, ["t0011A5", "r0112", "t03C80102030405060708"],
              ["r0011", "t0112BEEF", "r03C8"])
    (mf, _), (sf, _) = run_for(m, s, 1.5)
    assert 0x01 not in sf
    assert 0x11 not in mf
    assert set(sf.get(0x3C, [])) == {"0102030405060708"}


def test_monitor_checksum_mode(pair):
    """A monitor only reports frames whose checksum matches its own mode."""
    m, mon = pair
    m.cmd("r31")
    m.cmd("S1")
    m.cmd("O")
    assert_acked(m.cmd("t0011A5"))
    mon.cmd("S1")
    mon.cmd("l")
    m.start()
    time.sleep(1)
    enhanced, _ = frames(mon.drain())
    mon.cmd("r31")
    mon.drain()
    time.sleep(1)
    classic, _ = frames(mon.drain())
    assert 0x01 not in enhanced
    assert set(classic.get(0x01, [])) == {"A5"}


def test_custom_baudrate(pair):
    """10417 baud (0x28B1) on both sides, 8-byte frames in both directions."""
    m, s = pair
    assert ack(s.cmd("t0428B1")) == [b"Z"]
    assert ack(m.cmd("t0428B1")) == [b"Z"]
    s.cmd("L")
    replies = [s.cmd("r0018"), s.cmd("t0118" + payload(0x11, 8))]
    m.cmd("O")
    replies += [m.cmd("t0018" + payload(1, 8)), m.cmd("r0118")]
    assert_acked(*replies)
    s.start()
    m.start()
    (mf, _), (sf, _) = run_for(m, s, 2)
    assert set(sf.get(0x01, [])) == {payload(1, 8)}
    assert set(mf.get(0x11, [])) == {payload(0x11, 8)}
    m.cmd("S1")
    s.cmd("S1")


# --------------------------------------------------------------------------- #
# Two dongles: monitor mode
# --------------------------------------------------------------------------- #
def test_monitor_sees_master_frames(pair):
    m, mon = pair
    mon.cmd("S1")
    mon.cmd("l")
    m.cmd("S1")
    m.cmd("O")
    assert_acked(m.cmd("t0013112233"), m.cmd("t03C80102030405060708"))
    m.start()
    time.sleep(2)
    f, junk = frames(mon.drain())
    assert set(f.get(0x01, [])) == {"112233"}
    assert set(f.get(0x3C, [])) == {"0102030405060708"}
    assert not junk


def test_monitor_transmit_received_by_slave(pair):
    other, mon = pair
    mon.cmd("S1")
    mon.cmd("l")
    other.cmd("S1")
    other.cmd("L")
    assert_acked(other.cmd("r0162"))
    other.start()
    for _ in range(5):
        assert ack(mon.cmd("t0162AA55", wait=0.1))[:1] == [b"z"]
    time.sleep(0.3)
    f, _ = frames(other.drain())
    assert set(f.get(0x16, [])) == {"AA55"} and len(f[0x16]) >= 4
