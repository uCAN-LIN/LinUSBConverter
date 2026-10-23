"""Builds ucan-lin-mcp with its own copy of the server and LDF modules.

The source of truth is python_lib/ucanlintools. When building from the repo,
the files below are copied into ucan_lin_mcp/ first; a build from the sdist
uses the copies the sdist already contains.
"""
import shutil
from pathlib import Path

from setuptools import setup

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "python_lib" / "ucanlintools"
DST = HERE / "ucan_lin_mcp"
FILES = ("mcp_server.py", "LDF_parser.py", "LINFrame.py")

if SRC.is_dir():
    DST.mkdir(exist_ok=True)
    for name in FILES:
        shutil.copyfile(SRC / name, DST / name)
    (DST / "__init__.py").write_text(
        '"""MCP server for the uCAN USB LIN Converter (copied from ucanlintools)."""\n')

setup()
