"""
Meeting tool functions for the agent system.
Integrates with Google Meet MCP server.
"""

from agents import function_tool
from mcp_client import call_mcp_tool


@function_tool
async def create_meeting_tool(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    attendees: list[str] = None,
    time_zone: str = "America/New_York",
):
    """Create a new Google Meet meeting with calendar event.

    This automatically creates a Google Calendar event with an attached Google Meet video conferencing link.

    Args:
        summary: Title of the meeting
        start_time: Start time in ISO format (e.g., "2024-01-01T10:00:00")
        end_time: End time in ISO format (e.g., "2024-01-01T11:00:00")
        description: Description for the meeting (optional)
        attendees: List of email addresses for attendees (optional)
        time_zone: IANA timezone (e.g., "America/New_York", "America/Los_Angeles", default: "America/New_York")
    """
    if attendees is None:
        attendees = []

    result = await call_mcp_tool(
        "create_meeting",
        {
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "attendees": attendees,
            "time_zone": time_zone,
        },
        server_name="google-meet",
    )
    return result


@function_tool
async def list_meetings_tool(max_results: int = 10, time_min: str = None):
    """List upcoming Google Meet meetings.

    Args:
        max_results: Maximum number of results to return (default: 10)
        time_min: Start time in ISO format (optional, defaults to now)
    """
    tool_args = {"max_results": max_results}
    if time_min:
        tool_args["time_min"] = time_min

    result = await call_mcp_tool(
        "list_meetings",
        tool_args,
        server_name="google-meet",
    )
    return result


@function_tool
async def get_meeting_tool(meeting_id: str):
    """Get details of a specific Google Meet meeting.

    Args:
        meeting_id: ID of the meeting to retrieve
    """
    result = await call_mcp_tool(
        "get_meeting",
        {"meeting_id": meeting_id},
        server_name="google-meet",
    )
    return result


@function_tool
async def update_meeting_tool(
    meeting_id: str,
    summary: str = None,
    description: str = None,
    start_time: str = None,
    end_time: str = None,
    attendees: list[str] = None,
):
    """Update an existing Google Meet meeting.

    Args:
        meeting_id: ID of the meeting to update
        summary: Updated title of the meeting (optional)
        description: Updated description for the meeting (optional)
        start_time: Updated start time in ISO format (optional)
        end_time: Updated end time in ISO format (optional)
        attendees: Updated list of email addresses for attendees (optional)
    """
    tool_args = {"meeting_id": meeting_id}

    if summary is not None:
        tool_args["summary"] = summary
    if description is not None:
        tool_args["description"] = description
    if start_time is not None:
        tool_args["start_time"] = start_time
    if end_time is not None:
        tool_args["end_time"] = end_time
    if attendees is not None:
        tool_args["attendees"] = attendees

    result = await call_mcp_tool(
        "update_meeting",
        tool_args,
        server_name="google-meet",
    )
    return result


@function_tool
async def delete_meeting_tool(meeting_id: str):
    """Delete a Google Meet meeting.

    Args:
        meeting_id: ID of the meeting to delete
    """
    result = await call_mcp_tool(
        "delete_meeting",
        {"meeting_id": meeting_id},
        server_name="google-meet",
    )
    return result

