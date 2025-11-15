# Calendar MCP Server

A Google Calendar MCP (Model Context Protocol) server running in Docker.

## Container Name

**Container Name:** `calendar-mcp`

## Quick Start

```bash
# 1. Setup environment
make setup
# Edit .env with your Google OAuth credentials

# 2. Build and start
make build
make up

# 3. Verify it's running
docker ps | grep calendar-mcp
make health
```

## Available Commands

```bash
make help       # Show all available commands
make build      # Build the Docker image
make up         # Start the container
make down       # Stop the container
make restart    # Restart the container
make logs       # View logs
make shell      # Open shell in container
make health     # Check server health
make offerings  # List available MCP tools
make clean      # Remove everything
make rebuild    # Clean rebuild
```

## Container Status

Check if the container is running:

```bash
docker ps | grep calendar-mcp
```

## Environment Variables

Create a `.env` file with:

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar
TOKEN_FILE_PATH=token.json
OAUTH_CALLBACK_PORT=8080
HOST=0.0.0.0
PORT=8001
RELOAD=false
```

## Connecting from Python

The MCP client automatically connects to the `calendar-mcp` container:

```python
import asyncio
from mcp_client import call_mcp_tool

async def main():
    result = await call_mcp_tool("list_calendars", {})
    print(result)

asyncio.run(main())
```

## Ports

- **8001**: HTTP API Server
- **8080**: OAuth Callback

## Volumes

The following are persisted via Docker volumes:

- `./token.json` - OAuth credentials
- `./.gcp-saved-tokens.json` - Alternative token storage
- `./logs/` - Application logs
- `./calendar_mcp.log` - Main log file

## Architecture

```
Python Backend (mcp_client.py)
    ↓
docker exec -i calendar-mcp
    ↓
MCP Bridge (FastMCP)
    ↓
FastAPI Server (port 8001)
    ↓
Google Calendar API
```

## Troubleshooting

### Container not found

```bash
# Check if running
docker ps -a | grep calendar-mcp

# Rebuild if needed
make rebuild
```

### Port conflicts

Edit `.env` and change:

```env
PORT=8002  # Change to different port
```

### View logs

```bash
make logs
# or
docker logs -f calendar-mcp
```

## Health Check

The container includes automatic health checks:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{
  "status": "ok",
  "authentication": "authenticated"
}
```
