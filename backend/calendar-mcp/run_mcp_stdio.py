#!/usr/bin/env python3
"""
Simple entry point to run the MCP server via stdio transport.
This is used when the MCP server is called by an MCP client.
"""
import sys
import os
from pathlib import Path

# Add the mcp directory to the path
mcp_dir = Path(__file__).parent
if str(mcp_dir) not in sys.path:
    sys.path.insert(0, str(mcp_dir))

# Set PYTHONPATH for imports
os.environ["PYTHONPATH"] = f"{mcp_dir}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"

# Import and run the MCP server
from src.mcp_bridge import create_mcp_server

if __name__ == "__main__":
    mcp = create_mcp_server()
    mcp.run(transport="stdio")

