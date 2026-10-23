# MCP server (python_lib/ucanlintools/mcp_server.py) in a container.
# No USB access here, so it runs against the simulated bus (--mock).
# To use a real converter, run ucanlin-mcp on the host instead, or pass the
# device through: docker run -i --device /dev/ttyACM0 IMAGE --port /dev/ttyACM0
FROM python:3.12-slim

WORKDIR /app
COPY python_lib/ python_lib/
RUN pip install --no-cache-dir "./python_lib[mcp]"

ENTRYPOINT ["ucanlin-mcp"]
CMD ["--mock"]
