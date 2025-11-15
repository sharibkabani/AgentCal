"""
Calendar tool functions for the agent system.
"""

from agents import function_tool
from mcp_client import call_mcp_tool


@function_tool
async def list_events_tool(
    start_date: str, end_date: str, calendar_id: str = "primary"
):
    """List calendar events from Google Calendar between start_date and end_date.

    Args:
        start_date: Start time in ISO format (e.g., "2024-01-01T00:00:00Z")
        end_date: End time in ISO format (e.g., "2024-01-31T23:59:59Z")
        calendar_id: Calendar identifier (default: "primary")
    """
    result = await call_mcp_tool(
        "find_events",
        {
            "calendar_id": calendar_id,
            "time_min": start_date,
            "time_max": end_date,
        },
    )
    return result


@function_tool
async def create_event_tool(
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
):
    """Create a new event in Google Calendar.

    Args:
        summary: Title of the event
        start_time: Start time in ISO format (e.g., "2024-01-01T10:00:00Z")
        end_time: End time in ISO format (e.g., "2024-01-01T11:00:00Z")
        calendar_id: Calendar identifier (default: "primary")
    """
    tool_args = {
        "calendar_id": calendar_id,
        "summary": summary,
        "start_time": start_time,
        "end_time": end_time,
    }

    result = await call_mcp_tool("create_event", tool_args)
    return result
