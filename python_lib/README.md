# LIN Python lib

Library is under development API will change

## Features

- LIN frame transmission / reception
- LDF signals encoding / decoding (only signal and frames currently working, schedule table parsing not implemented, max signal size is 1 byte)
- Works on windows, linux, mac. Supported hardware , [uCAN LIN USB CONVERTER](https://ucandevices.github.io/ulc.html)

## Installation

```python
pip install ucanlintools
```

## Example usage

To load ldf

```python
from ucanlintools.LDF_parser import parseLDF
ldf = parseLDF("D:\\ldfe.ldf") 
message = ldf.get_message_by_name('FRAME_A')
print(message.signals)
```

To decode/ encode frame

```python
aaa = message.encode({'SIGNAL_A': 1})
bbb = b'\x00\x00\x00\x00\x00\x00'
message.decode(bbb)
```

To setup LIN USB Converter

```python

lin = ucanlintools.LUC('COM7')
lin.set_frame_rx_handler(rx_any)
lin.set_new_frame_rx_handler(rx_new_data)

lin.openAsMaster()

lin.addReceptionFrameToTable(52,8)
lin.addReceptionFrameToTable(54,8)
lin.enable()

```

Example data reception handler

```python

def rx_new_data(f):
        global message
        print (hex(f.id) + ": " +(f.data.hex()))
        if (message.id == f.id):
                message.decode(f.data)
                print(message.diff_str())
```

## For more info see

https://ucandevices.github.io