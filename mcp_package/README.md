# ucan-lin-mcp

MCP server for the [uCAN USB LIN Converter](https://ucandevices.github.io/ulc.html):
lets an AI agent sniff and reverse-engineer a LIN bus.

<!-- mcp-name: io.github.uCAN-LIN/lin-usb-converter -->

The server is `ucanlintools.mcp_server` from this repo's Python library,
bundled here so `uvx ucan-lin-mcp` works on its own.

```bash
uvx ucan-lin-mcp --mock                 # simulated bus, no hardware
uvx ucan-lin-mcp --port COM3            # real converter, read-only
uvx ucan-lin-mcp --port COM3 --allow-transmit
```

MCP client config:

```json
{
  "mcpServers": {
    "lin": {"command": "uvx", "args": ["ucan-lin-mcp", "--port", "COM3"]}
  }
}
```

Tools: `device_info`, `monitor_bus` (per-id period, changing bits, change log),
`detect_bus` (speed and checksum), `load_ldf`, `decode_frame`, `encode_frame`,
and with `--allow-transmit` `send_frame`, `run_master`, `run_slave`.

Hardware, firmware and docs: https://github.com/uCAN-LIN/LinUSBConverter
