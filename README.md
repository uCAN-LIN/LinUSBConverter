# USB LIN Converter (uLC)

[![Buy on Tindie](https://img.shields.io/badge/Tindie-Buy_USB_LIN_Converter-fb5b1b?logo=tindie&logoColor=white)](https://www.tindie.com/products/lll7/usb-lin-converter/)
[![Buy on Lectronz](https://img.shields.io/badge/Lectronz-Buy_in_EU-5468ff)](https://lectronz.com/stores/ucandevices)
[![Product page](https://img.shields.io/badge/docs-ucandevices.github.io-1f6feb)](https://ucandevices.github.io/ulc.html)

> **Open source USB ↔ LIN bus dongle. LIN 2.1 master, slave or monitor. SLCAN-compatible virtual COM port - works on Windows, Linux and macOS with no proprietary drivers.**

<p align="center">
  <img src="https://ucandevices.github.io/img/products/ulc.png" alt="USB LIN Converter (uLC) - dongle photo" width="60%">
</p>

The **USB LIN Converter (uLC)** is a small open-source USB dongle (STM32F042C6, ~31 × 18 mm) that lets a PC act as a LIN bus master, slave or passive monitor. It enumerates as a USB CDC virtual COM port and speaks an SLCAN-style ASCII protocol, so it bridges into Linux SocketCAN via `slcand` and works with parts of can-utils.

A commercial automotive LIN analyzer typically costs hundreds to thousands of euros. This one is around **$27** on [Tindie](https://www.tindie.com/products/lll7/usb-lin-converter/).

The LIN protocol implementation is based on [openLIN](https://github.com/open-LIN).

---

## Features

- LIN 2.1 support
- **Monitor mode** - full frame reception plus single-frame transmission
- **Master mode** - up to 15 scheduled frame slots
- **Slave mode** - up to 15 scheduled frame slots for slave simulation
- 9600 / 19200 baud rate selection
- **Optical isolation** between LIN and the USB / PC side
- Software-controlled termination resistors
- External 4.5 - 28 V powers the LIN transceiver
- Device size 31 × 18 mm (without USB connector)
- USB DFU bootloader for firmware updates
- No proprietary drivers - Linux / macOS / Windows

---

## Where to buy

| Where | Region | Link |
|---|---|---|
| **Tindie** | Worldwide | https://www.tindie.com/products/lll7/usb-lin-converter/ |
| **Lectronz** | EU | https://lectronz.com/stores/ucandevices |
| **Elty** | Poland / EU | https://elty.pl/ |
| **Kamami** | Poland / EU | https://kamami.pl/ |

---

## Quickstart

1. Plug the device into a USB port. It enumerates as a virtual COM port (`COM3` on Windows, `/dev/ttyACM0` on Linux, `/dev/cu.usbmodem*` on macOS).
2. On Windows, install the [ST Virtual COM Port driver](https://www.st.com/en/development-tools/stsw-stm32102.html). On Linux and macOS no driver is required.
3. Open the port at any baud rate (USB CDC ignores baud). Line ending must be CR (`0x0D`).
4. Power the LIN side with 4.5 - 28 V on the external supply pin.
5. Send `S0` to select 19200 baud, then `l` to enter monitor mode. Bus traffic will start to appear.

### Linux SocketCAN bridge

```bash
sudo slcand -o -s8 -t hw -S 921600 /dev/ttyACM0 slcan0
sudo ip link set slcan0 up
candump slcan0
```

### Python (pyserial) sniff snippet

```python
import serial
ser = serial.Serial('/dev/ttyACM0', timeout=1)
ser.write(b'S0\r')   # 19200 baud
ser.write(b'l\r')    # monitor mode
while True:
    line = ser.readline()
    if line:
        print(line.decode(errors='replace').strip())
```

A higher-level Python library is provided in [`python_lib/`](python_lib/) (package `ucanlintools`).

---

## ASCII command reference

All commands are ASCII terminated with CR (`0x0D`). Errors return `0x07` (BEL).

| Command | Description |
|---|---|
| `O` | Open in master mode |
| `L` | Open in slave mode |
| `l` | Open in monitor mode |
| `C` | Close LIN port |
| `Sx` | Baud: `S2` = 9600, others = 19200 |
| `V` / `v` / `N` | Hardware / firmware version / serial number query |
| `tiiildd...` | Transmit full header + data frame (id, length, data) |
| `r0iil` | Header only request (slave answers) |
| `r1ff0` | Master mode: start sending frames from schedule table |
| `r2ff0` | Clear schedule table |
| `xm` | Switch checksum: `x2` classic, `x1` enhanced |
| `T0iit1t1t2t2ldd...` | Custom frame with explicit offset (`t1`) and response wait time (`t2`) |

Full command reference and examples: https://ucandevices.github.io/ulc.html

---

## Repository layout

| Directory | Contents |
|---|---|
| [`embedded/`](embedded/) | STM32F042C6 firmware sources (STM32CubeMX project `LUCEmbedded.ioc`, Atollic TrueSTUDIO project under `embedded/TrueSTUDIO/`). USB layer generated with STM32CubeMX. |
| [`pcb/`](pcb/) | Open-hardware KiCad project for the LIN_USB_CONVERTER board, Gerbers and 1-click BOM. |
| [`python_lib/`](python_lib/) | `ucanlintools` Python package with high-level master / slave / monitor helpers and examples. |
| [`doc/`](doc/) | LIN 2.2A specification, MCU datasheet, LIN transceiver datasheet and supporting documents. |

---

## Build

Source is pure C. The firmware can be imported directly into **Atollic TrueSTUDIO for STM32 9.0.0** from `embedded/TrueSTUDIO/`. The USB CDC layer was generated with STM32CubeMX from `embedded/LUCEmbedded.ioc`.

## Bootloader

The STM32F042 has an embedded ROM USB DFU bootloader. To enter it from a running device send `boot\r` over the virtual COM port. See this [tutorial](https://www.youtube.com/watch?v=-gnX25AGyI0) for the flashing flow.

---

## FAQ

**What is the cheapest USB LIN bus converter that works on Linux?**
The uCanDevices USB LIN Converter (uLC) is an open source dongle around $27 that enumerates as a USB CDC virtual COM port on Linux, macOS and Windows. It uses an SLCAN-style ASCII protocol so it bridges into SocketCAN via `slcand`.

**Does it support master and slave mode?**
Yes - monitor (full reception plus single-frame transmission), master (up to 15 scheduled slots) and slave (up to 15 slots for slave simulation). Modes are selected with the `O`, `L` and `l` commands.

**Is the LIN side optically isolated from the USB host?**
Yes. The LIN transceiver is optically isolated from the PC side, protecting the host from automotive transients. The LIN side needs an external 4.5 - 28 V supply since USB only powers the MCU.

**Which LIN baud rates and LIN version are supported?**
LIN 2.1, with selectable 9600 and 19200 baud. Classic and enhanced checksum are switchable with the `xm` command. Custom frame timing is supported in master mode.

**Can I use it to flash an ECU over LIN?**
It is a generic LIN interface. ECU flashing depends entirely on the target ECU's own LIN bootloader; if that bootloader is documented or already supported by an existing tool, you can drive it through this dongle.

**Is the firmware open source?**
Yes - this repository contains firmware (`embedded/`), hardware (`pcb/`) and the Python helper library (`python_lib/`). The device also has a USB DFU bootloader for in-field updates.

---

## Related projects

- LIN protocol implementation: [openLIN](https://github.com/open-LIN)
- Sibling products: [USB CAN Converter (UCCB)](https://ucandevices.github.io/uccb.html), [CAN FD USB Converter (CFUC)](https://ucandevices.github.io/cfuc.html), [SENT (J2716) USB Converter](https://ucandevices.github.io/sentusb.html)

## Links

- Product page: https://ucandevices.github.io/ulc.html
- All uCanDevices products: https://ucandevices.github.io/
- Contact: devices.ucan@gmail.com

## License

See [LICENSE](LICENSE).
