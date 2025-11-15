"""
Calendar agents for handling different calendar operations.
"""

from agents import Agent
from tool_definitions.calendar_tools import list_events_tool, create_event_tool
from agent_definitions.meeting_agents import create_meeting_agent


# Define specialist agents
list_events_agent = Agent(
    name="Calendar List Agent",
    handoff_description="Specialist agent for listing and viewing calendar events",
    instructions="""You help users view their calendar events. 
    
    IMPORTANT: You will receive the current date/time at the start of each request. Use this to:
    - Calculate date ranges for relative dates (today, tomorrow, next week, etc.)
    - Convert relative dates to absolute ISO format dates
    
    When listing events, use the list_events_tool with proper date ranges.
    Always format dates in ISO format (YYYY-MM-DDTHH:MM:SSZ).
    For "today", use 00:00:00 to 23:59:59 of the current date.
    For "tomorrow", add 1 day to the current date.
    For "next week", use the upcoming Monday to Sunday.
    If a clear date range is not provided, assume the user is asking for events for the current week.
    
    Provide clear, formatted summaries of the events found.""",
    tools=[list_events_tool],
)

create_event_agent = Agent(
    name="Calendar Create Agent",
    handoff_description="Specialist agent for creating new calendar events",
    instructions="""You help users create new calendar events.
    
    IMPORTANT: You will receive the current date/time at the start of each request. Use this to:
    - Calculate actual dates for relative dates (today, tomorrow, next Tuesday, etc.)
    - Set appropriate default times if not specified
    - Convert all dates to ISO format (YYYY-MM-DDTHH:MM:SSZ)
    
    Extract event details like summary, start time, end time.
    If the user says "tomorrow at 2 PM", calculate tomorrow's date based on the current date provided.
    If no end time is specified, default to 1 hour after start time.
    
    After creating, provide a clear confirmation message with the full event details.""",
    tools=[create_event_tool],
)

# Define triage agent that routes to specialist agents
triage_agent = Agent(
    name="Calendar Triage Agent",
    instructions="""You are a calendar assistant that routes requests to the appropriate specialist.
    
    IMPORTANT: You will receive the current date/time at the start of each request. Pass this information to specialist agents.
    
    Routing rules:
    - If the user wants to VIEW, LIST, CHECK, or FIND events, hand off to the Calendar List Agent
    - If the user wants to CREATE, ADD, SCHEDULE, or BOOK a simple calendar event WITHOUT a meeting/video conference, hand off to the Calendar Create Agent
    - If the user wants to schedule a MEETING, VIDEO CALL, VIDEO CONFERENCE, ZOOM, MEET, or mentions "Google Meet", hand off to the Meeting Scheduler Agent
    
    Keywords for Meeting Scheduler Agent: meeting, meet, video call, video conference, conference call, zoom, virtual meeting, online meeting, call
    
    Always hand off to the appropriate specialist agent based on the user's intent.
    Do not try to handle calendar operations yourself.""",
    handoffs=[list_events_agent, create_event_agent, create_meeting_agent],
)
