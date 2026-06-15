# ucanlintools — Python library for the uCAN LIN USB Converter

`ucanlintools` is a Python 3 library for driving the
[uCAN LIN USB Converter](https://ucandevices.github.io/ulc.html) and for
working with LIN Description Files (LDF). It lets a PC act as a LIN **master**,
**slave**, or passive **monitor**, transmit/receive LIN frames, and
encode/decode signals described in an LDF.

It works on Windows, Linux and macOS. The converter enumerates as a USB CDC
virtual serial port (STMicroelectronics VID `0483` / PID `5740`).

---

## Installation

```bash
pip install ucanlintools          # from PyPI
# or, from a checkout of this repo:
pip install pyserial lark bitstruct
```

Dependencies: `pyserial` (serial I/O), `lark` (LDF grammar), `bitstruct`
(signal packing). `lark` and `bitstruct` are only needed if you use the LDF /
signal features; `LUC` itself needs only `pyserial`.

---

## Mental model (read this first)

A LIN converter is configured in three phases. **Order matters.**

1. **Configure (port is "closed" / in CONFIG state).**
   Open the port, pick a mode (`openAsMaster` / `openAsSlave` /
   `openAsMonitor`), set bus speed, and register frames in the schedule table.
   In this phase every command **reads and verifies its reply**, so the
   methods return `True`/`False` reliably.

2. **Run.** Call `enable()`. This starts two background threads that
   continuously read the serial port and dispatch received frames to your
   handler(s). **In master/slave mode this also starts the schedule.**

3. **Stop.** Call `disable()` to stop the threads, then `deInitSerial()` to
   close the port.

> ⚠️ **Key concurrency rule.** Once `enable()` has been called, the background
> rx thread owns all serial reads. Commands you send while running
> (e.g. `addTransmitFrameToTable` to update a payload) are written to the
> device but their reply is consumed by the rx thread, so those calls return
> `True` immediately without confirmation. **Do all table setup *before*
> `enable()` when you need a confirmed result.**

The three modes:

| Mode    | Method            | Role on the bus                                                                 |
|---------|-------------------|---------------------------------------------------------------------------------|
| Master  | `openAsMaster()`  | Sends headers on a schedule; transmits its table frames and polls slave frames. |
| Slave   | `openAsSlave()`   | Responds to a master's headers with the frames in its transmit table.           |
| Monitor | `openAsMonitor()` | Passive listener; can also inject a single frame on demand (see below).         |

---

## API reference (`ucanlintools.LUC`)

```python
from ucanlintools.LUC import LUC
lin = LUC(port, timeout=0.02, baudrate=9600)
```

`LUC(port, timeout=0.02, baudrate=9600)` — open the converter on `port`
(e.g. `"COM3"` or `"/dev/ttyACM0"`). **Use `baudrate=19200`**; the default
`9600` is known to corrupt frames (see *Troubleshooting*).

### Configuration commands (call before `enable()`)

| Method | Sends | Returns | Notes |
|--------|-------|---------|-------|
| `requestFirmwareVersion()` | `v` | firmware string, e.g. `"0300"` | |
| `close()` | `C` | `True` on ack | Returns the converter to CONFIG state. Safe to call first. |
| `highSpeed()` | `S1` | `True` on ack | 19200 baud LIN bus. |
| `lowSpeed()` | `S2` | `True` on ack | 9600 baud LIN bus. |
| `openAsMaster()` | `O` | `True` on ack | |
| `openAsSlave()` | `L` | `True` on ack | |
| `openAsMonitor()` | `l` | `True` on ack | |
| `addTransmitFrameToTable(id, data)` | `t…` | `True` on ack | Register a frame the node will send. `data` is `bytes` (preferred) or `int`. |
| `addReceptionFrameToTable(id, length)` | `r…` | `True` on ack | Register a frame id (and its byte `length`) the node should receive. |

### Runtime commands

| Method | Description |
|--------|-------------|
| `enable()` | Start the rx threads and (master/slave) the schedule. Returns `1`. Call exactly once per `LUC` instance. |
| `disable()` | Stop the rx threads and reception. Idempotent. *(In monitor mode its return value is unreliable — see Limitations — but it still stops correctly.)* |
| `deInitSerial()` | Flush and close the serial port. Idempotent. |
| `isRunning()` | `True` while the rx thread is alive. Handy for blocking main loops. |

### Reception handlers

| Method | When the handler fires |
|--------|------------------------|
| `set_frame_rx_handler(fn)` | On **every** received frame. |
| `set_new_frame_rx_handler(fn)` | Only when a frame's **data changed** since the last time that id was seen. |

The handler receives a frame object with `.id` (int) and `.data` (bytes).
Handlers run in the rx thread.

---

## Example: Master mode

```python
import time
from ucanlintools.LUC import LUC

def on_frame(f):
    print(f"0x{f.id:02x}: {f.data.hex()}")

lin = LUC("COM3", baudrate=19200)
lin.set_new_frame_rx_handler(on_frame)

# --- configure (verified) ---
lin.close()
lin.highSpeed()
lin.openAsMaster()
lin.addTransmitFrameToTable(0x01, b"\x22\x33")  # master sends id 1 = 22 33
lin.addReceptionFrameToTable(0x34, 8)           # master polls id 0x34 (8 bytes)

# --- run ---
lin.enable()              # schedule starts now
time.sleep(2)

# Update a payload while running (fire-and-forget, returns True):
lin.addTransmitFrameToTable(0x01, b"\xAA\x55")
time.sleep(2)

# --- stop ---
lin.disable()
lin.deInitSerial()
```

## Example: Slave mode

```python
import time
from ucanlintools.LUC import LUC

lin = LUC("COM33", baudrate=19200)
lin.set_new_frame_rx_handler(lambda f: print("from master:", f.data.hex()))

lin.close()
lin.lowSpeed()
lin.openAsSlave()
lin.addReceptionFrameToTable(0x0B, 1)   # listen for id 0x0B from the master
lin.addTransmitFrameToTable(0x0C, b"\x00\x00")  # respond to id 0x0C
lin.enable()

time.sleep(5)
lin.disable()
lin.deInitSerial()
```

## Example: Monitor mode (passive sniff + frame injection)

```python
import time
from ucanlintools.LUC import LUC

lin = LUC("COM3", baudrate=19200)
lin.set_frame_rx_handler(lambda f: print(f"0x{f.id:02x}: {f.data.hex()}"))

lin.close()
lin.highSpeed()
lin.openAsMonitor()
lin.enable()

# In monitor mode, addTransmitFrameToTable injects ONE frame immediately:
lin.addTransmitFrameToTable(0x16, b"\x11\x22\x33")

time.sleep(2)
lin.disable()
lin.deInitSerial()
```

> **Monitor self-loopback note:** because the LIN transceiver also reads the
> bus while driving it, a frame you inject in monitor mode is echoed back to
> your handler — but only its **header** (the id with an *empty* payload), not
> the data bytes. To verify full data payloads you need a second node (a master
> or slave) on the bus.

## Example: clean shutdown on Ctrl-C

```python
import time

def listen(lin):
    try:
        while lin.isRunning():
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        lin.disable()
        lin.deInitSerial()
```

---

## LDF parsing and signal encode/decode

```python
from ucanlintools.LDF_parser import parseLDF

ldf = parseLDF("my_network.ldf")
frame = ldf.get_message_by_name("FRAME_A")    # or .get_message_by_id(52)

# Encode named signals into the raw payload bytes:
payload = frame.encode({"SIGNAL_A": 1})        # -> b'\x01'

# Decode raw bytes back into signal values:
frame.decode(b"\x00")
print(frame.diff_str())                        # -> {'SIGNAL_A' : 0}
```

`diff_str()` returns only the signals whose value changed since the previous
call (useful for compact logging).

Tie it together — decode received frames against an LDF:

```python
frame = ldf.get_message_by_id(52)

def on_new(f):
    if f.id == frame.id:
        frame.decode(f.data)
        print(frame.diff_str())

lin.set_new_frame_rx_handler(on_new)
```

---

## Limitations / gotchas

- **Use `baudrate=19200`.** The default `9600` causes intermittent frame
  corruption (frames silently dropped on a parse error).
- **Configure before `enable()`** for verified table setup; calls made after
  `enable()` return `True` without confirmation (rx thread owns reads).
- **Monitor mode:** injected frames loop back as headers only (no payload);
  and `disable()` may return `False` in monitor mode even though it stopped
  correctly (the stop command is itself echoed on the bus, contaminating the
  reply). The threads are still stopped.
- **LDF support is partial:** only `Signals` and `Frames` sections are used;
  schedule tables, encoding types and node attributes are parsed but ignored.
  Maximum signal size is 1 byte.
- `enable()` may be called only once per `LUC` instance (threads can't be
  restarted). Create a new `LUC` to run again.

---

## Tests

The test suite is pytest-based and lives in `tests/`:

- **Offline tests** (no hardware): `test_ldf_parser.py`, `test_linframe.py`,
  `test_luc_encoding.py`.
- **Hardware tests** (`test_luc_hardware.py`): single-dongle tests use the
  port from `LUC_MASTER_PORT` (default `COM3`); the two-dongle master↔slave
  test also needs `LUC_SLAVE_PORT` (default `COM33`). Hardware tests **skip
  automatically** if the required dongle can't be opened.

```bash
cd python_lib
pip install pytest
# run everything that doesn't need hardware + any reachable dongles:
PYTHONPATH=. pytest tests -v
# point at your dongles:
LUC_MASTER_PORT=COM3 LUC_SLAVE_PORT=COM33 PYTHONPATH=. pytest tests -v
```

On Windows PowerShell, set the env vars with `$env:PYTHONPATH="."` etc.

---

## Underlying serial (SLCAN-style) protocol — reference for tooling

Commands are ASCII, terminated by `\r`. Replies are terminated by `\r`.

| Command | Meaning | Reply |
|---------|---------|-------|
| `v` | firmware version | `vMMmm` |
| `V` | hardware version | `VMMmm` |
| `O` / `L` / `l` | open master / slave / monitor | `\r` |
| `C` | close (back to config) | `\r` |
| `S1` / `S2` | bus speed 19200 / 9600 | `\r` |
| `t0<id><len><data…>` | transmit frame (table entry, or immediate in monitor) | `z\r` |
| `r0<id><len>` | reception table entry | `z\r` |
| `r1ff0` | start schedule / reception (sent by `enable()`) | `z\r` |
| `r2ff0` | stop (sent by `disable()`) | `z\r` |
| received frame | reported by the device | `t0<id><len><data…>\r` |

`<id>` is 2 hex digits, `<len>` is 1 hex digit (0–8), `<data…>` is `len` bytes
as hex pairs.

## More info

- Hardware & docs: https://ucandevices.github.io
- Source: https://github.com/uCAN-LIN/LinUSBConverter/tree/master/python_lib
