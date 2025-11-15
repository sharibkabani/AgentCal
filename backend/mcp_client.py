"""
MCP (Model Context Protocol) client helper for calling MCP server tools.
Connects to the Dockerized MCP server instance.
"""

import logging
import os
import subprocess
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_mcp_tool(
    tool_name: str,
    tool_args: dict,
    use_docker: bool = True,
    server_name: str = "calendar",
):
    """
    Generic helper to call any MCP tool.

    Args:
        tool_name: Name of the MCP tool to call
        tool_args: Arguments to pass to the tool
        use_docker: If True, connects to Docker container. If False, runs local script.
        server_name: Name of the MCP server to connect to ("calendar" or "google-meet")
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"🔧 Calling MCP tool: {tool_name} with args: {tool_args} on server: {server_name}"
    )

    # Server configuration mapping
    server_configs = {
        "calendar": {
            "container_name": os.getenv("MCP_CONTAINER_NAME", "calendar-mcp"),
            "command": ["python", "/app/run_mcp_stdio.py"],
            "local_path": "calendar-mcp/run_mcp_stdio.py",
            "setup_instructions": "cd backend/calendar-mcp && make up",
        },
        "google-meet": {
            "container_name": os.getenv("GOOGLE_MEET_MCP_CONTAINER", "google-meet-mcp"),
            "command": ["node", "src/index.js"],
            "local_path": None,  # No local fallback for Node server
            "setup_instructions": "cd google-meet-mcp-server && make up",
        },
    }

    if server_name not in server_configs:
        raise ValueError(
            f"Unknown server name: {server_name}. Available: {list(server_configs.keys())}"
        )

    server_config = server_configs[server_name]

    if use_docker:
        # Connect to the MCP server running in Docker container
        logger.info(f"🐳 Connecting to {server_name} MCP server in Docker container")

        container_name = server_config["container_name"]
        command_args = server_config["command"]

        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", container_name] + command_args,
            env=None,
        )

        logger.debug(
            f"MCP command: docker exec -i {container_name} {' '.join(command_args)}"
        )

        # Check if container is running
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            if container_name not in result.stdout:
                raise RuntimeError(
                    f"Docker container '{container_name}' is not running. "
                    f"Start it with: {server_config['setup_instructions']}"
                )
            logger.info(f"✅ Container '{container_name}' is running")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check Docker container status: {e}")
            raise RuntimeError("Docker is not available or not running")

    else:
        # Fallback to local script execution
        logger.info(f"💻 Running {server_name} MCP server locally")

        if server_config["local_path"] is None:
            raise RuntimeError(
                f"Local execution not supported for {server_name} MCP server. "
                f"Please use Docker: {server_config['setup_instructions']}"
            )

        backend_dir = Path(__file__).parent
        mcp_server_path = backend_dir / server_config["local_path"]

        import sys

        python_executable = sys.executable

        server_params = StdioServerParameters(
            command=python_executable, args=[str(mcp_server_path)], env=None
        )

        logger.debug(f"MCP command: {python_executable} {mcp_server_path}")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logger.info("📡 MCP session established")

                # Initialize the session
                await session.initialize()
                logger.info("✅ MCP session initialized successfully")

                # Call the tool
                logger.info(f"🔍 Calling {tool_name} tool")
                result = await session.call_tool(tool_name, tool_args)
                logger.info(
                    f"✅ MCP call successful, got result: {str(result)[:200]}..."
                )
                return result
    except Exception as e:
        logger.error(f"❌ Error calling MCP server: {e}", exc_info=True)
        raise
