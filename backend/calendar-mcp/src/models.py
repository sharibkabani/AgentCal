import datetime # Import the module itself
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
# from datetime import datetime, date # Keep original import commented for reference

# Based on Google Calendar API v3 Event resource documentation:
# https://developers.google.com/calendar/api/v3/reference/events#resource

class EventDateTime(BaseModel):
    """Represents the start or end time of an event."""
    date: Optional[datetime.date] = None
    dateTime: Optional[datetime.datetime] = None  # Renamed from 'date_time' to match API JSON
    timeZone: Optional[str] = None  # Renamed from 'time_zone'

    class Config:
        populate_by_name = True  # Changed from allow_population_by_field_name
        # orm_mode = True # Removed, orm_mode is deprecated in Pydantic V2, use from_attributes=True

class EventAttendee(BaseModel):
    """Represents an attendee of an event."""
    id: Optional[str] = None
    email: Optional[EmailStr] = None
    displayName: Optional[str] = None  # Renamed from 'display_name'
    organizer: Optional[bool] = None
    self: Optional[bool] = None
    resource: Optional[bool] = None
    optional: Optional[bool] = None
    responseStatus: Optional[str] = None  # Renamed from 'response_status'
    comment: Optional[str] = None
    additionalGuests: Optional[int] = None  # Renamed from 'additional_guests'

    class Config:
        populate_by_name = True  # Changed from allow_population_by_field_name
        # orm_mode = True # Removed, orm_mode is deprecated in Pydantic V2, use from_attributes=True

class EventCreator(BaseModel):
    """Represents the creator of an event."""
    id: Optional[str] = None
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, alias='displayName')
    self: Optional[bool] = None # Whether the creator corresponds to the calendar on which this copy of the event appears.

    class Config:
        populate_by_name = True

class EventOrganizer(BaseModel):
    """Represents the organizer of an event."""
    id: Optional[str] = None
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, alias='displayName')
    self: Optional[bool] = None # Whether the organizer corresponds to the calendar on which this copy of the event appears.

    class Config:
        populate_by_name = True

class EventReminderOverride(BaseModel):
    method: Optional[str] = None
    minutes: Optional[int] = None

    class Config:
        populate_by_name = True  # Changed from allow_population_by_field_name
        # orm_mode = True # Removed, orm_mode is deprecated in Pydantic V2, use from_attributes=True

class EventReminders(BaseModel):
    useDefault: bool = Field(..., alias="useDefault")  # Renamed from 'use_default'
    overrides: Optional[List[EventReminderOverride]] = None

    class Config:
        populate_by_name = True  # Changed from allow_population_by_field_name
        # orm_mode = True # Removed, orm_mode is deprecated in Pydantic V2, use from_attributes=True

# --- Main Event Model --- 

class GoogleCalendarEvent(BaseModel):
    """Pydantic model representing a Google Calendar event resource."""
    kind: str = "calendar#event"
    id: Optional[str] = Field(None, description="Opaque identifier of the event.")
    status: Optional[str] = Field(None, description="Status of the event ('confirmed', 'tentative', 'cancelled').")
    html_link: Optional[str] = Field(None, alias='htmlLink', description="URL for the event in the Google Calendar UI.")
    created: Optional[datetime.datetime] = Field(None, description="Creation time of the event (RFC3339 format).")
    updated: Optional[datetime.datetime] = Field(None, description="Last modification time of the event (RFC3339 format).")
    summary: Optional[str] = Field(None, description="Title of the event.")
    description: Optional[str] = Field(None, description="Description of the event. Optional.")
    location: Optional[str] = Field(None, description="Geographic location of the event. Optional.")
    color_id: Optional[str] = Field(None, alias='colorId', description="Color of the event. Optional.")
    creator: Optional[EventCreator] = Field(None, description="The creator of the event. Read-only.")
    organizer: Optional[EventOrganizer] = Field(None, description="The organizer of the event.")
    start: Optional[EventDateTime] = Field(None, description="The start time of the event.")
    end: Optional[EventDateTime] = Field(None, description="The end time of the event.")
    end_time_unspecified: Optional[bool] = Field(None, alias='endTimeUnspecified', description="Whether the end time is actually unspecified.")
    recurrence: Optional[List[str]] = Field(None, description="List of RRULE, EXRULE, RDATE or EXDATE properties for recurring events.")
    recurring_event_id: Optional[str] = Field(None, alias='recurringEventId', description="For an instance of a recurring event, this is the id of the recurring event itself.")
    original_start_time: Optional[EventDateTime] = Field(None, alias='originalStartTime', description="For an instance of a recurring event, this is the original start time of the instance before modification.")
    attendees: Optional[List[EventAttendee]] = Field([], description="The attendees of the event.")
    attendees_omitted: Optional[bool] = Field(None, alias='attendeesOmitted', description="Whether attendees were omitted.")
    reminders: Optional[EventReminders] = Field(None, description="Information about the event's reminders.")
    # Add other fields as needed (e.g., attachments, conferenceData, gadget, source, etc.)

    class Config:
        populate_by_name = True
        # Consider adding validation logic, e.g., ensuring start is before end

# --- Models for API Requests/Responses --- 

class EventCreateRequest(BaseModel):
    """Model for the request body when creating a detailed event."""
    summary: str
    start: EventDateTime
    end: EventDateTime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[EmailStr]] = Field(None, description="List of attendee email addresses to invite.")
    recurrence: Optional[List[str]] = Field(None, description="List of RRULEs, EXRULEs, RDATEs or EXDATEs for recurring events.")
    reminders: Optional[EventReminders] = Field(None, description="Notification settings for the event.")
    # Add other creatable fields as needed

class QuickAddEventRequest(BaseModel):
    """Model for the request body when using the quickAdd endpoint."""
    text: str = Field(..., description="The text describing the event to be parsed by Google Calendar.")

class EventUpdateRequest(BaseModel):
    """Model for the request body when updating an event.
       Contains only the fields that can be updated.
    """
    summary: Optional[str] = None
    start: Optional[EventDateTime] = None
    end: Optional[EventDateTime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[EventAttendee]] = None # Allow updating attendee details or list
    # Add other updatable fields

class AddAttendeeRequest(BaseModel):
    """Model for adding attendees to an existing event."""
    attendee_emails: List[EmailStr] = Field(..., description="List of email addresses to add as attendees.")

# You might also want models for CalendarList entries, etc.

# Define NotificationSettings first as it's used in CalendarListEntry
class NotificationSettings(BaseModel):
    """Represents notification settings for a calendar."""
    notifications: Optional[List[Dict[str, str]]] = None # List of {'type': 'eventCreation', 'method': 'email'} etc.

    class Config:
        populate_by_name = True # Changed from allow_population_by_field_name

class CalendarListEntry(BaseModel):
    """Represents an entry in the user's calendar list."""
    kind: str = "calendar#calendarListEntry"
    etag: str
    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    timeZone: Optional[str] = None # Renamed from 'time_zone'
    summaryOverride: Optional[str] = None # Renamed from 'summary_override'
    colorId: Optional[str] = None # Renamed from 'color_id'
    backgroundColor: Optional[str] = None # Renamed from 'background_color'
    foregroundColor: Optional[str] = None # Renamed from 'foreground_color'
    hidden: Optional[bool] = None
    selected: Optional[bool] = None
    accessRole: Optional[str] = None # Renamed from 'access_role'
    defaultReminders: Optional[List[EventReminderOverride]] = None # Renamed from 'default_reminders'
    notificationSettings: Optional[NotificationSettings] = None # Renamed from 'notification_settings'
    primary: Optional[bool] = None
    deleted: Optional[bool] = None

class CalendarListResponse(BaseModel):
    """Response containing a list of calendars."""
    kind: str = "calendar#calendarList"
    items: List[CalendarListEntry] = []
    nextPageToken: Optional[str] = None
    nextSyncToken: Optional[str] = None

# Re-inserting EventsResponse definition
class EventsResponse(BaseModel):
    """Response containing a list of events."""
    kind: str = "calendar#events"
    summary: Optional[str] = None
    description: Optional[str] = None
    updated: Optional[datetime.datetime] = None
    timeZone: Optional[str] = None
    accessRole: Optional[str] = None
    defaultReminders: Optional[List[EventReminderOverride]] = []
    items: List[GoogleCalendarEvent] = []
    nextPageToken: Optional[str] = None
    nextSyncToken: Optional[str] = None

class CalendarList(BaseModel):
    """Represents the user's list of calendars."""
    kind: str = "calendar#calendarList"
    etag: str
    nextPageToken: Optional[str] = None # Renamed from 'next_page_token'
    nextSyncToken: Optional[str] = None # Renamed from 'next_sync_token'
    items: List[CalendarListEntry]

    class Config:
        populate_by_name = True # Changed from allow_population_by_field_name

# --- Models for Advanced Actions --- 

# --- Check Attendee Status ---
class CheckAttendeeStatusRequest(BaseModel):
    event_id: str
    calendar_id: str = 'primary'
    attendee_emails: Optional[List[EmailStr]] = None

class CheckAttendeeStatusResponse(BaseModel):
    status_map: Dict[EmailStr, str] = Field(..., description="Mapping of attendee email to their responseStatus ('accepted', 'declined', etc.)")

# --- Find Availability (Free/Busy) ---
class FreeBusyRequestItem(BaseModel):
    id: str # Calendar ID

class FreeBusyRequest(BaseModel):
    time_min: datetime.datetime = Field(..., alias='timeMin')
    time_max: datetime.datetime = Field(..., alias='timeMax')
    items: List[FreeBusyRequestItem]
    # Optional: timeZone, groupExpansionMax, calendarExpansionMax
    time_zone: Optional[str] = Field(None, alias='timeZone')

    class Config:
        populate_by_name = True

class TimePeriod(BaseModel):
    start: datetime.datetime
    end: datetime.datetime

class FreeBusyError(BaseModel):
    domain: str
    reason: str

class CalendarBusyInfo(BaseModel):
    errors: Optional[List[FreeBusyError]] = None
    busy: List[TimePeriod] = []

class FreeBusyResponse(BaseModel):
    kind: str = "calendar#freeBusy"
    time_min: datetime.datetime = Field(..., alias='timeMin')
    time_max: datetime.datetime = Field(..., alias='timeMax')
    calendars: Dict[str, CalendarBusyInfo] = {}
    # Optional: groups

    class Config:
        populate_by_name = True

# --- Find Mutual Availability & Schedule ---
class ScheduleMutualRequest(BaseModel):
    attendee_calendar_ids: List[str] = Field(..., description="List of calendar IDs (usually emails) for attendees whose availability should be checked.")
    time_min: datetime.datetime
    time_max: datetime.datetime
    duration_minutes: int
    event_details: EventCreateRequest # Use the existing model for core event info
    organizer_calendar_id: str = 'primary'
    working_hours_start_str: Optional[str] = Field(None, description="Optional start time for working hours constraint (HH:MM format)")
    working_hours_end_str: Optional[str] = Field(None, description="Optional end time for working hours constraint (HH:MM format)")
    send_notifications: bool = True

# Response is GoogleCalendarEvent

# --- Project Recurring Events ---
class ProjectRecurringRequest(BaseModel):
    time_min: datetime.datetime
    time_max: datetime.datetime
    calendar_id: str = 'primary'
    event_query: Optional[str] = None

# Define ProjectedEventOccurrence within models.py for consistency
class ProjectedEventOccurrenceModel(BaseModel):
    original_event_id: str
    original_summary: str
    occurrence_start: datetime.datetime
    occurrence_end: datetime.datetime

class ProjectRecurringResponse(BaseModel):
    projected_occurrences: List[ProjectedEventOccurrenceModel]

# --- Analyze Busyness ---
class AnalyzeBusynessRequest(BaseModel):
    time_min: datetime.datetime
    time_max: datetime.datetime
    calendar_id: str = 'primary'

class DailyBusynessStats(BaseModel):
    event_count: int
    total_duration_minutes: float

class AnalyzeBusynessResponse(BaseModel):
    # Use string representation for date keys in JSON
    busyness_by_date: Dict[str, DailyBusynessStats] = Field(..., description="Mapping of date string (YYYY-MM-DD) to busyness stats") 