#!/usr/bin/env python3
"""
mcp_server.py -- MCP server that lets an AI agent sniff and drive a LIN bus
through the uCAN USB LIN Converter.

    python -m ucanlintools.mcp_server                   # auto-detect, read-only
    python -m ucanlintools.mcp_server --port COM3
    python -m ucanlintools.mcp_server --allow-transmit  # enable send/master/slave
    python -m ucanlintools.mcp_server --mock            # simulated bus, no hardware

Register it with any MCP client as a stdio server, e.g. in its JSON config:

    "lin": {"command": "python", "args": ["-m", "ucanlintools.mcp_server"]}

Guardrails:
  * read-only by default: monitor_bus, detect_bus and the LDF tools only listen.
    send_frame, run_master and run_slave need --allow-transmit, because
    putting frames on a vehicle bus can move actuators
  * every capture is time-boxed (MAX_DURATION_S) and the converter is put back
    in CONFIG state and the port closed after each tool call, so other
    programs can use the dongle in between

The server talks the converter's ASCII protocol directly (see python_lib/README)
instead of using LUC's threads, so frames arriving back to back are not lost
and each one gets a host timestamp.
"""

from __future__ import annotations

import argparse
import statistics
import threading
import time
from typing import Any

import serial
import serial.tools.list_ports
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

USB_VID, USB_PID = 0x0483, 0x5740
MAX_DURATION_S = 60.0
MAX_CHANGES = 200
MAX_TABLE = 15                 # firmware schedule slots
REPLY_TIMEOUT_S = 0.5
SPEEDS = (19200, 10417, 9600)
IO_ERRORS = (OSError, serial.SerialException)


# --- link to the converter ----------------------------------------------------

class Frame:
    __slots__ = ("t", "id", "data")

    def __init__(self, t: float, fid: int, data: bytes):
        self.t, self.id, self.data = t, fid, data


def parse_frame(line: str) -> Frame | None:
    """'t0' + id(2 hex) + len(1 hex) + data -> Frame, else None."""
    if len(line) < 5 or line[0] != "t":
        return None
    try:
        fid, n = int(line[2:4], 16), int(line[4], 16)
        data = bytes.fromhex(line[5:5 + 2 * n])
    except ValueError:
        return None
    if len(data) != n:
        return None
    return Frame(time.monotonic(), fid, data)


def frame_line(fid: int, data: bytes) -> str:
    return f"t0{fid:02x}{len(data)}{data.hex()}"


class Link:
    """One open session: send commands, collect frames with timestamps."""

    def __init__(self, ser):
        self.ser = ser
        self.buf = b""
        self.pending: list[str] = []

    def _lines(self, timeout: float) -> list[str]:
        """Return complete lines received within timeout (may be empty)."""
        end = time.monotonic() + timeout
        while True:
            n = self.ser.in_waiting
            if n:
                self.buf += self.ser.read(n)
            if b"\r" in self.buf:
                *done, self.buf = self.buf.split(b"\r")
                return [d.decode("ascii", "replace") for d in done]
            if time.monotonic() >= end:
                return []
            time.sleep(0.001)

    def command(self, line: str) -> str:
        """Send a command, return its reply ('' for a bare CR). Frames that
        arrive meanwhile are kept for the next read_frames()."""
        self.ser.write(line.encode() + b"\r")
        end = time.monotonic() + REPLY_TIMEOUT_S
        while time.monotonic() < end:
            for ln in self._lines(end - time.monotonic()):
                if ln.startswith("t"):
                    self.pending.append(ln)
                else:
                    return ln
        raise ToolError(f"converter did not answer {line!r}")

    def read_frames(self, duration_s: float) -> list[Frame]:
        frames = [f for f in map(parse_frame, self.pending) if f]
        self.pending.clear()
        end = time.monotonic() + duration_s
        while time.monotonic() < end:
            for ln in self._lines(min(0.05, max(0.0, end - time.monotonic()))):
                f = parse_frame(ln.lstrip("zZ\x07"))
                if f:
                    frames.append(f)
        # the firmware reports an empty 0x3F header when reception starts or
        # stops; it is not bus traffic
        return [f for f in frames if not (f.id == 0x3F and not f.data)]


class Converter:
    """Opens the dongle for one tool call and always leaves it closed."""

    def __init__(self, port: str | None, mock: bool):
        self.port, self.mock = port, mock
        self.lock = threading.Lock()

    def _open(self):
        if self.mock:
            return MockSerial()
        port = self.port
        if port is None:
            found = [p.device for p in serial.tools.list_ports.comports()
                     if (p.vid, p.pid) == (USB_VID, USB_PID)]
            if not found:
                raise ToolError("no LIN converter found (USB 0483:5740). Plug it in "
                                "or start the server with --port.")
            if len(found) > 1:
                raise ToolError(f"several possible converters: {', '.join(found)}. "
                                "Start the server with --port to pick one.")
            port = found[0]
        try:
            return serial.Serial(port, baudrate=115200, timeout=0)
        except IO_ERRORS as exc:
            raise ToolError(f"cannot open {port}: {exc}. Is another program "
                            "using the converter?") from exc

    def session(self, mode: str, speed: int, checksum: str,
                transmit: dict[int, bytes] | None = None,
                receive: dict[int, int] | None = None,
                duration_s: float = 0.0, inject: list[tuple[int, bytes]] | None = None
                ) -> tuple[list[Frame], str]:
        """Configure, run for duration_s, stop. Returns (frames, firmware)."""
        with self.lock:
            ser = self._open()
            link = Link(ser)
            try:
                link.command("C")
                fw = link.command("v").lstrip("v")
                link.command(speed_command(speed))
                if link.command("t31" if checksum == "classic" else "t30") != "Z":
                    raise ToolError("converter rejected the checksum mode")
                if link.command({"master": "O", "slave": "L", "monitor": "l"}[mode]) != "":
                    raise ToolError(f"converter rejected {mode} mode")
                for fid, data in (transmit or {}).items():
                    if link.command(frame_line(fid, data)) != "z":
                        raise ToolError(f"converter rejected transmit frame 0x{fid:02X}")
                for fid, n in (receive or {}).items():
                    if link.command(f"r0{fid:02x}{n}") != "z":
                        raise ToolError(f"converter rejected receive frame 0x{fid:02X}")
                link.command("r1ff0")
                t0 = time.monotonic()
                for fid, data in inject or []:
                    link.ser.write(frame_line(fid, data).encode() + b"\r")
                    time.sleep(0.02)
                frames = link.read_frames(max(0.0, duration_s - (time.monotonic() - t0)))
                return frames, fw
            except IO_ERRORS as exc:
                raise ToolError(f"converter I/O failed: {exc}") from exc
            finally:
                try:
                    # one command per write: the firmware handles only one
                    # command per USB packet
                    for cmd in (b"r2ff0\r", b"C\r"):
                        ser.write(cmd)
                        time.sleep(0.03)
                    ser.close()
                except IO_ERRORS:
                    pass


def speed_command(speed: int) -> str:
    if speed == 19200:
        return "S1"
    if speed == 9600:
        return "S2"
    if not 1000 <= speed <= 20000:
        raise ToolError("speed must be 1000-20000 baud (LIN uses 19200, 10417 or 9600)")
    return f"t04{speed:04X}"


# --- simulated bus (--mock) -----------------------------------------------------

MOCK_LDF = """\
LIN_description_file;
LIN_protocol_version = "2.1";
LIN_language_version = "2.1";
LIN_speed = 19.2 kbps;

Nodes {
  Master: BCM, 5 ms, 0.1 ms;
  Slaves: SeatModule;
}

Signals {
  backlight_level: 4, 0, BCM, SeatModule;
  button_up: 1, 0, SeatModule, BCM;
  button_down: 1, 0, SeatModule, BCM;
  heater_level: 2, 0, SeatModule, BCM;
  seat_temp: 8, 0, SeatModule, BCM;
}

Frames {
  Backlight: 11, BCM, 1 {
    backlight_level, 0;
  }
  SeatStatus: 12, SeatModule, 2 {
    button_up, 0;
    button_down, 1;
    heater_level, 2;
    seat_temp, 8;
  }
}
"""


class MockSerial:
    """Fake converter on a small bus: a BCM master polling a seat module.
    Only 19200 baud with enhanced checksum produces traffic, like a real bus
    that the converter is configured for correctly or not."""

    def __init__(self):
        self.out = b""
        self.speed, self.classic, self.mode = 19200, False, "master"
        self.running, self.receive, self.next_slot, self.t0 = False, {}, 0.0, time.monotonic()

    def _bus(self, t: float) -> dict[int, bytes]:
        el = t - self.t0
        up = 1 if int(el / 1.5) % 4 == 1 else 0
        down = 1 if int(el / 1.5) % 4 == 3 else 0
        heat = int(el / 4) % 4
        return {0x0B: bytes([int(el / 2) % 16]),
                0x0C: bytes([up | down << 1 | heat << 2, 30 + int(el / 3) % 5])}

    @property
    def in_waiting(self) -> int:
        now = time.monotonic()
        if self.running and self.speed == 19200 and not self.classic:
            while self.next_slot <= now:
                bus = self._bus(self.next_slot)
                for fid, data in bus.items():
                    if self.mode == "monitor" or fid in self.receive:
                        self.out += f"t0{fid:02X}{len(data)}{data.hex().upper()}\r".encode()
                self.next_slot += 0.02
        else:
            self.next_slot = now
        return len(self.out)

    def read(self, n: int) -> bytes:
        data, self.out = self.out[:n], self.out[n:]
        return data

    def write(self, data: bytes) -> None:
        for line in data.decode().split("\r")[:-1]:
            self.out += self._reply(line).encode() + b"\r"

    def _reply(self, line: str) -> str:
        c = line[:1]
        if c == "C":
            self.running, self.receive = False, {}
            return ""
        if c == "v":
            return "v0303"
        if c == "S":
            self.speed = 9600 if line[1:2] == "2" else 19200
            return ""
        if c in "OLl":
            self.mode = {"O": "master", "L": "slave", "l": "monitor"}[c]
            return ""
        if line.startswith("t3"):
            self.classic = line[2:3] == "1"
            return "Z"
        if line.startswith("t04") and len(line) == 7:
            self.speed = int(line[3:], 16)
            return "Z"
        if line == "r1ff0":
            self.running, self.next_slot = True, time.monotonic()
            return "z"
        if line == "r2ff0":
            self.running = False
            return "z"
        if c == "r":
            self.receive[int(line[2:4], 16)] = int(line[4], 16)
            return "z"
        if c == "t":
            if self.mode == "monitor" and self.running:
                return f"z\rt0{line[2:4].upper()}0"   # header echo, like the hardware
            return "z"
        return "\x07"

    def close(self) -> None:
        pass


# --- LDF ----------------------------------------------------------------------------

class Ldf:
    """Frames and signals from an LDF, decoded with LIN bit order (LSB first)."""

    def __init__(self, path: str, frames: list[dict]):
        self.path = path
        self.frames = frames
        self.by_id = {f["id"]: f for f in frames}
        self.by_name = {f["name"].lower(): f for f in frames}

    @classmethod
    def load(cls, path: str, text: str | None = None) -> "Ldf":
        from .LDF_parser import parseLDF
        if text is not None:
            import os
            import tempfile
            fd, tmp = tempfile.mkstemp(suffix=".ldf")
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
            try:
                parsed = parseLDF(tmp)
            finally:
                os.unlink(tmp)
        else:
            parsed = parseLDF(path)
        frames = []
        for f in parsed.frames:
            frames.append({
                "id": f.id, "name": f.name, "length": f.len, "publisher": f.publisher,
                "signals": [{"name": s["name"], "bit_offset": s["bit_offset"],
                             "size_bits": s["size_bits"],
                             "default": s["default_val"][0] if isinstance(s["default_val"], list)
                             else s["default_val"]}
                            for s in f.signals]})
        return cls(path, frames)

    def decode(self, fid: int, data: bytes) -> dict | None:
        f = self.by_id.get(fid)
        if f is None:
            return None
        raw = int.from_bytes(data, "little")
        return {s["name"]: (raw >> s["bit_offset"]) & ((1 << s["size_bits"]) - 1)
                for s in f["signals"]}

    def encode(self, name: str, values: dict[str, int]) -> tuple[dict, bytes]:
        f = self.by_name.get(name.lower())
        if f is None:
            raise ToolError(f"no frame {name!r} in the LDF; frames are: "
                            + ", ".join(x["name"] for x in self.frames))
        known = {s["name"] for s in f["signals"]}
        unknown = set(values) - known
        if unknown:
            raise ToolError(f"frame {f['name']} has no signal(s) {sorted(unknown)}; "
                            f"its signals are {sorted(known)}")
        raw = 0
        for s in f["signals"]:
            v = int(values.get(s["name"], s["default"]))
            if not 0 <= v < 1 << s["size_bits"]:
                raise ToolError(f"{s['name']} must be 0-{(1 << s['size_bits']) - 1}")
            raw |= v << s["bit_offset"]
        return f, raw.to_bytes(f["length"], "little")


# --- server -------------------------------------------------------------------------

conv: Converter                 # set in main()
allow_tx = False
ldf: Ldf | None = None

mcp = MCPServer(
    "lin-converter",
    instructions=(
        "Sniffs and drives a LIN bus (automotive body electronics: switches, seats, "
        "lights, mirrors) through the uCAN USB LIN Converter. Start with monitor_bus; "
        "if it sees nothing on a live bus, run detect_bus to find the speed and "
        "checksum. To reverse-engineer a signal, run monitor_bus while the user "
        "operates the control and look at changing_bits and the change log. "
        "load_ldf adds signal names. Transmit tools only work if the server was "
        "started with --allow-transmit; ask the user before sending anything on a "
        "vehicle bus."),
)


def check_duration(duration_s: float) -> None:
    if not 0.1 <= duration_s <= MAX_DURATION_S:
        raise ToolError(f"duration_s must be 0.1-{MAX_DURATION_S}")


def check_checksum(checksum: str) -> str:
    checksum = checksum.lower()
    if checksum not in ("enhanced", "classic"):
        raise ToolError("checksum must be 'enhanced' (LIN 2.x) or 'classic' (LIN 1.x)")
    return checksum


def parse_id(fid: Any) -> int:
    try:
        v = int(fid, 0) if isinstance(fid, str) else int(fid)
    except ValueError as exc:
        raise ToolError(f"bad frame id {fid!r}") from exc
    if not 0 <= v <= 0x3F:
        raise ToolError(f"frame id must be 0x00-0x3F, got {fid!r}")
    return v


def parse_data(data: str) -> bytes:
    try:
        b = bytes.fromhex(data.replace(" ", ""))
    except ValueError as exc:
        raise ToolError(f"data must be hex bytes like '01 a0 ff', got {data!r}") from exc
    if len(b) > 8:
        raise ToolError("a LIN frame carries at most 8 data bytes")
    return b


def need_tx() -> None:
    if not allow_tx:
        raise ToolError("transmitting is disabled. Restart the server with "
                        "--allow-transmit (only on a bus where that is safe).")


def summarize(frames: list[Frame], duration_s: float, ids: set[int] | None = None) -> dict:
    """Per-id statistics plus a log of data changes, for reverse engineering."""
    if ids is not None:
        frames = [f for f in frames if f.id in ids]
    t0 = frames[0].t if frames else 0.0
    per: dict[int, list[Frame]] = {}
    headers: dict[int, int] = {}       # header seen, no response (or our own echo)
    changes, last = [], {}
    for f in frames:
        if not f.data:
            headers[f.id] = headers.get(f.id, 0) + 1
            continue
        per.setdefault(f.id, []).append(f)
        if last.get(f.id) != f.data:
            if f.id in last and len(changes) < MAX_CHANGES:
                entry = {"t_s": round(f.t - t0, 3), "id": f"0x{f.id:02X}",
                         "from": last[f.id].hex(" "), "to": f.data.hex(" ")}
                if ldf:
                    entry["signals"] = ldf.decode(f.id, f.data)
                changes.append(entry)
            last[f.id] = f.data
    out = []
    for fid in sorted(set(per) | set(headers)):
        fs = per.get(fid)
        if not fs:
            out.append({"id": f"0x{fid:02X}", "count": 0, "headers_only": headers[fid],
                        "note": "header only: no node answered this id "
                                "(or it is the converter's echo of its own frame)"})
            continue
        first = fs[0].data
        n = max(len(f.data) for f in fs)
        mask = bytearray(n)
        for f in fs:
            for i, b in enumerate(f.data):
                mask[i] |= b ^ (first[i] if i < len(first) else 0)
        gaps = [b.t - a.t for a, b in zip(fs, fs[1:])]
        row = {
            "id": f"0x{fid:02X}", "count": len(fs), "length": n,
            "period_ms": round(statistics.median(gaps) * 1000, 1) if gaps else None,
            "last_data": fs[-1].data.hex(" "),
            "distinct_values": len({f.data for f in fs}),
            "changing_bits": mask.hex(" ") if any(mask) else None,
        }
        if fid in headers:
            row["headers_only"] = headers[fid]
        if ldf:
            fr = ldf.by_id.get(fid)
            if fr:
                row["name"] = fr["name"]
                row["signals"] = ldf.decode(fid, fs[-1].data)
        out.append(row)
    return {"duration_s": duration_s, "frames": len(frames), "ids": out,
            "changes": changes,
            "changes_truncated": len(changes) >= MAX_CHANGES}


@mcp.tool()
def device_info() -> dict:
    """Converter port, firmware version, whether transmitting is allowed, and
    the loaded LDF (if any)."""
    _, fw = conv.session("monitor", 19200, "enhanced")
    return {"port": "mock" if conv.mock else (conv.port or "auto"), "firmware": fw,
            "transmit_allowed": allow_tx,
            "ldf": {"path": ldf.path, "frames": len(ldf.frames)} if ldf else None}


@mcp.tool()
def monitor_bus(duration_s: float = 5.0, speed: int = 19200, checksum: str = "enhanced",
                ids: list[str] | None = None) -> dict:
    """Listen to the bus passively and summarize what is on it.

    Per frame id: count, period, last data, how many distinct values were
    seen and changing_bits (a per-byte mask of bits that changed). 'changes'
    lists every data change in time order, so asking the user to press a
    button during the capture shows which id and bit it drives.
    speed: 19200 (most cars), 10417 or 9600. checksum: 'enhanced' (LIN 2.x)
    or 'classic' (LIN 1.x); frames with the other checksum are dropped by the
    converter. ids: optional filter, e.g. ["0x0C"]."""
    check_duration(duration_s)
    frames, _ = conv.session("monitor", speed, check_checksum(checksum),
                             duration_s=duration_s)
    want = {parse_id(i) for i in ids} if ids else None
    result = summarize(frames, duration_s, want)
    if not frames:
        result["hint"] = ("no frames. Check the LIN side has 12 V (4.5-28 V) and "
                          "ground, then try detect_bus for speed/checksum.")
    return result


@mcp.tool()
def detect_bus(seconds_per_try: float = 1.5) -> dict:
    """Try every speed and checksum combination and report which one sees
    valid frames. Use when monitor_bus shows nothing on a live bus."""
    if not 0.3 <= seconds_per_try <= 10:
        raise ToolError("seconds_per_try must be 0.3-10")
    tries = []
    for speed in SPEEDS:
        for checksum in ("enhanced", "classic"):
            frames, _ = conv.session("monitor", speed, checksum, duration_s=seconds_per_try)
            data_frames = [f for f in frames if f.data]
            tries.append({"speed": speed, "checksum": checksum, "frames": len(frames),
                          "frames_with_data": len(data_frames),
                          "ids": sorted({f"0x{f.id:02X}" for f in frames})})
    best = max(tries, key=lambda t: (t["frames_with_data"], t["frames"]))
    return {"best": best if best["frames"] else None, "tries": tries}


@mcp.tool()
def load_ldf(path: str) -> dict:
    """Load a LIN Description File so captures show signal names and values.
    Returns its frames and signals. Pass path "mock" with a --mock server to
    load the simulated bus's LDF."""
    global ldf
    try:
        if path == "mock" and conv.mock:
            ldf = Ldf.load("mock", MOCK_LDF)
        else:
            ldf = Ldf.load(path)
    except FileNotFoundError as exc:
        raise ToolError(f"no such file: {path}") from exc
    except Exception as exc:          # lark raises many parse error types
        raise ToolError(f"could not parse the LDF: {exc}") from exc
    return {"path": ldf.path, "frames": [
        {"id": f"0x{f['id']:02X}", "name": f["name"], "length": f["length"],
         "publisher": f["publisher"],
         "signals": [{k: s[k] for k in ("name", "bit_offset", "size_bits")}
                     for s in f["signals"]]} for f in ldf.frames]}


@mcp.tool()
def decode_frame(id: str, data: str) -> dict:
    """Decode raw frame bytes into signal values with the loaded LDF.
    id like "0x0C", data hex like "05 1e"."""
    if ldf is None:
        raise ToolError("no LDF loaded; call load_ldf first")
    fid = parse_id(id)
    values = ldf.decode(fid, parse_data(data))
    if values is None:
        raise ToolError(f"id 0x{fid:02X} is not in the LDF")
    return {"id": f"0x{fid:02X}", "name": ldf.by_id[fid]["name"], "signals": values}


@mcp.tool()
def encode_frame(frame: str, signals: dict[str, int]) -> dict:
    """Build frame bytes from signal values with the loaded LDF. Signals not
    given keep their LDF default. Returns id and data ready for send_frame."""
    if ldf is None:
        raise ToolError("no LDF loaded; call load_ldf first")
    f, data = ldf.encode(frame, signals)
    return {"id": f"0x{f['id']:02X}", "name": f["name"], "data": data.hex(" ")}


@mcp.tool()
def send_frame(id: str, data: str, repeat: int = 1, speed: int = 19200,
               checksum: str = "enhanced") -> dict:
    """Inject a complete frame (header + data) on the bus from monitor mode,
    `repeat` times about 20 ms apart, and capture the bus for a moment after.
    Needs --allow-transmit. The converter echoes only the header of its own
    frame back, so check the effect in the following traffic."""
    need_tx()
    if not 1 <= repeat <= 50:
        raise ToolError("repeat must be 1-50")
    fid, payload = parse_id(id), parse_data(data)
    frames, _ = conv.session("monitor", speed, check_checksum(checksum),
                             duration_s=0.5 + repeat * 0.02,
                             inject=[(fid, payload)] * repeat)
    result = summarize(frames, 0.5)
    result["sent"] = {"id": f"0x{fid:02X}", "data": payload.hex(" "), "repeat": repeat}
    return result


def parse_table(rows: list[dict] | None, key: str) -> dict:
    table = {}
    for r in rows or []:
        fid = parse_id(r.get("id"))
        if key == "data":
            table[fid] = parse_data(str(r.get("data", "")))
        else:
            n = int(r.get("length", 8))
            if not 0 <= n <= 8:
                raise ToolError("length must be 0-8")
            table[fid] = n
    return table


@mcp.tool()
def run_master(duration_s: float = 3.0, transmit: list[dict] | None = None,
               receive: list[dict] | None = None, speed: int = 19200,
               checksum: str = "enhanced") -> dict:
    """Act as the LIN master for duration_s: run a schedule that sends the
    `transmit` frames ([{"id": "0x0B", "data": "05"}]) and polls the
    `receive` ids ([{"id": "0x0C", "length": 2}]), then summarize the slave
    responses. Use only with the real master disconnected. Needs --allow-transmit."""
    need_tx()
    check_duration(duration_s)
    tx, rx = parse_table(transmit, "data"), parse_table(receive, "length")
    if not tx and not rx:
        raise ToolError("give at least one transmit or receive frame")
    if len(tx) + len(rx) > MAX_TABLE:
        raise ToolError(f"the converter's schedule holds at most {MAX_TABLE} frames")
    frames, _ = conv.session("master", speed, check_checksum(checksum), tx, rx, duration_s)
    result = summarize(frames, duration_s)
    missing = sorted(f"0x{i:02X}" for i in rx if i not in {f.id for f in frames if f.data})
    if missing:
        result["no_response"] = missing
    return result


@mcp.tool()
def run_slave(duration_s: float = 3.0, respond: list[dict] | None = None,
              listen: list[dict] | None = None, speed: int = 19200,
              checksum: str = "enhanced") -> dict:
    """Simulate a slave node for duration_s: answer the master's headers for
    the `respond` ids with fixed data ([{"id": "0x0C", "data": "01 1e"}]) and
    capture the `listen` ids the master sends ([{"id": "0x0B", "length": 1}]).
    Use only with the real slave disconnected. Needs --allow-transmit."""
    need_tx()
    check_duration(duration_s)
    tx, rx = parse_table(respond, "data"), parse_table(listen, "length")
    if not tx and not rx:
        raise ToolError("give at least one respond or listen frame")
    if len(tx) + len(rx) > MAX_TABLE:
        raise ToolError(f"the converter's table holds at most {MAX_TABLE} frames")
    frames, _ = conv.session("slave", speed, check_checksum(checksum), tx, rx, duration_s)
    return summarize(frames, duration_s)


def main(argv=None) -> int:
    global conv, allow_tx
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", help="serial port; default is auto-detect")
    p.add_argument("--allow-transmit", action="store_true",
                   help="enable send_frame, run_master and run_slave")
    p.add_argument("--mock", action="store_true", help="run against a simulated bus")
    args = p.parse_args(argv)
    conv = Converter(args.port, args.mock)
    allow_tx = args.allow_transmit
    mcp.run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
