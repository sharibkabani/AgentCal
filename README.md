# Calendar AI Agent Backend

An intelligent AI-powered calendar management system built with OpenAI Agents SDK, featuring multi-agent orchestration and Model Context Protocol (MCP) integration for seamless Google Calendar and Google Meet operations.

## 🏗️ Architecture

This backend implements a **hierarchical multi-agent system** with intelligent request routing and specialized agent handoffs:

```
User Request → Triage Agent → Specialist Agents → MCP Servers → Google APIs
```

### Agent Hierarchy

- **Triage Agent**: Routes requests to appropriate specialists based on intent
- **Calendar List Agent**: Handles viewing and querying calendar events
- **Calendar Create Agent**: Creates simple calendar events
- **Meeting Scheduler Agent**: Manages Google Meet video conference scheduling

### MCP Server Integration

The system integrates two isolated MCP servers running in Docker containers:

1. **[Google Calendar MCP](https://github.com/deciduus/calendar-mcp)** (Python/FastAPI)
   - 15+ REST endpoints for calendar operations
   - Advanced scheduling algorithms (mutual availability finder)
   - Analytics and busyness analysis
   - OAuth2 authentication with automatic token refresh

2. **[Google Meet MCP Server](https://github.com/cool-man-vk/google-meet-mcp-server)** (Node.js)
   - Automatic Google Meet link generation
   - Meeting CRUD operations
   - Attendee management
   - Conference data handling

## ✨ Features

- **Natural Language Processing**: Process calendar requests in plain English
- **Real-time Streaming**: Server-Sent Events (SSE) for token-by-token responses
- **Timezone Intelligence**: Automatic timezone detection and handling
- **Smart Scheduling**: Find mutual availability across multiple calendars
- **Agent Handoffs**: Seamless transitions between specialist agents
- **Error Resilience**: Comprehensive error handling and graceful degradation
- **Context Injection**: Automatic date/time and memory context enrichment

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Google Calendar API credentials
- OpenAI API key

### Installation

1. **Clone the repository**

```bash
cd backend
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up MCP servers**

```bash
# Calendar MCP
cd calendar-mcp
cp env.template .env
# Add your Google OAuth credentials to .env
make up

# Google Meet MCP
cd ../google-meet-mcp-server
cp .env.example .env
# Add your Google OAuth credentials to .env
make up
```

4. **Configure environment**

```bash
# Create .env file in backend root
echo "OPENAI_API_KEY=your_key_here" > .env
echo "MCP_CONTAINER_NAME=calendar-mcp" >> .env
echo "GOOGLE_MEET_MCP_CONTAINER=google-meet-mcp" >> .env
```

5. **Run the server**

```bash
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Main Agent Endpoint

**POST** `/agent`

Send natural language requests to the AI agent system.

**Request:**

```json
{
  "user_input": "Schedule a meeting with john@example.com tomorrow at 2pm"
}
```

**Response:** Server-Sent Events stream with:

- Agent handoff events
- Tool execution events
- Real-time text generation
- Final completion event

**Example cURL:**

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show me my meetings for today"}'
```

## 🧠 Agent System

### Routing Logic

The **Triage Agent** routes requests based on keywords:

- **View/List/Check/Find** → Calendar List Agent
- **Create/Add/Schedule** → Calendar Create Agent
- **Meeting/Video/Meet/Conference** → Meeting Scheduler Agent

### Context Injection

Every request is enriched with:

- Current date/time in user's timezone
- IANA timezone identifier
- Relative date interpretation guides ("today", "tomorrow", etc.)
- Relevant memory context

### Timezone Handling

The system detects the server's local timezone and:

- Injects timezone context into agent prompts
- Formats times appropriately for Google APIs
- Handles ISO 8601 datetime parsing
- Preserves timezone information across handoffs

## 🛠️ Technology Stack

### Core

- **FastAPI**: ASGI web framework
- **OpenAI Agents SDK**: Multi-agent orchestration
- **MCP**: Model Context Protocol for tool integration

### Integration

- **Google Calendar API v3**: Calendar operations
- **Google Meet API**: Video conferencing
- **Docker**: MCP server isolation
- **STDIO Transport**: MCP communication

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# MCP Container Names
MCP_CONTAINER_NAME=calendar-mcp
GOOGLE_MEET_MCP_CONTAINER=google-meet-mcp

# Optional: API Port
PORT=8000
```

## 🙏 Acknowledgments

- [Google Calendar MCP](https://github.com/deciduus/calendar-mcp) by deciduus
- [Google Meet MCP Server](https://github.com/cool-man-vk/google-meet-mcp-server) by cool-man-vk
