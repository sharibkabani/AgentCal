/**
 * Google Meet API client that interacts with the Google Calendar API
 * to manage Google Meet meetings.
 */

import fs from "fs/promises";
import path from "path";
import { google } from "googleapis";

class GoogleMeetAPI {
  /**
   * Initialize the Google Meet API client.
   * @param {string} credentialsPath - Path to the client_secret.json file
   * @param {string} tokenPath - Path to save/load the token.json file
   */
  constructor(credentialsPath, tokenPath) {
    this.credentialsPath = credentialsPath;
    this.tokenPath = tokenPath;
    this.calendar = null;
  }

  /**
   * Initialize the API client with OAuth2 credentials.
   */
  async initialize() {
    const credentials = JSON.parse(
      await fs.readFile(this.credentialsPath, "utf8")
    );

    // Support both 'web' and 'installed' credential types
    const credData = credentials.web || credentials.installed;
    if (!credData) {
      throw new Error(
        'Invalid credentials file format. Must contain "web" or "installed" property.'
      );
    }

    const { client_id, client_secret, redirect_uris } = credData;

    const oAuth2Client = new google.auth.OAuth2(
      client_id,
      client_secret,
      redirect_uris[0]
    );

    try {
      // Check if token exists and use it
      const token = JSON.parse(await fs.readFile(this.tokenPath, "utf8"));
      oAuth2Client.setCredentials(token);

      // Check if token is expired and needs refresh
      if (token.expiry_date && token.expiry_date < Date.now()) {
        // Token is expired, refresh it
        const { credentials } = await oAuth2Client.refreshToken(
          token.refresh_token
        );
        await fs.writeFile(this.tokenPath, JSON.stringify(credentials));
        oAuth2Client.setCredentials(credentials);
      }
    } catch (error) {
      throw new Error(
        "No valid credentials. Please run the setup script first to authorize access."
      );
    }

    // Initialize the calendar API
    this.calendar = google.calendar({ version: "v3", auth: oAuth2Client });
  }

  /**
   * List upcoming Google Meet meetings.
   * @param {number} maxResults - Maximum number of results to return
   * @param {string} timeMin - Start time in ISO format
   * @param {string} timeMax - End time in ISO format
   * @returns {Promise<Array>} - List of meetings
   */
  async listMeetings(maxResults = 10, timeMin = null, timeMax = null) {
    // Default timeMin to now if not provided
    if (!timeMin) {
      timeMin = new Date().toISOString();
    }

    // Prepare parameters for the API call
    const params = {
      calendarId: "primary",
      maxResults: maxResults,
      timeMin: timeMin,
      orderBy: "startTime",
      singleEvents: true,
      conferenceDataVersion: 1,
    };

    if (timeMax) {
      params.timeMax = timeMax;
    }

    try {
      const response = await this.calendar.events.list(params);
      const events = response.data.items || [];

      // Filter for events with conferenceData (Google Meet)
      const meetings = [];
      for (const event of events) {
        if (event.conferenceData) {
          const meeting = this._formatMeetingData(event);
          if (meeting) {
            meetings.push(meeting);
          }
        }
      }

      return meetings;
    } catch (error) {
      throw new Error(`Error listing meetings: ${error.message}`);
    }
  }

  /**
   * Get details of a specific Google Meet meeting.
   * @param {string} meetingId - ID of the meeting to retrieve
   * @returns {Promise<Object>} - Meeting details
   */
  async getMeeting(meetingId) {
    try {
      const response = await this.calendar.events.get({
        calendarId: "primary",
        eventId: meetingId,
        conferenceDataVersion: 1,
      });

      const event = response.data;

      if (!event.conferenceData) {
        throw new Error(
          `Event with ID ${meetingId} does not have Google Meet conferencing data`
        );
      }

      const meeting = this._formatMeetingData(event);
      if (!meeting) {
        throw new Error(
          `Failed to format meeting data for event ID ${meetingId}`
        );
      }

      return meeting;
    } catch (error) {
      throw new Error(`Error getting meeting: ${error.message}`);
    }
  }

  /**
   * Create a new Google Meet meeting.
   * @param {string} summary - Title of the meeting
   * @param {string} startTime - Start time in ISO format
   * @param {string} endTime - End time in ISO format
   * @param {string} description - Description for the meeting
   * @param {Array<string>} attendees - List of email addresses for attendees
   * @param {string} timeZone - IANA timezone (e.g., "America/New_York", defaults to "UTC")
   * @returns {Promise<Object>} - Created meeting details
   */
  async createMeeting(
    summary,
    startTime,
    endTime,
    description = "",
    attendees = [],
    timeZone = "UTC"
  ) {
    // Prepare attendees list in the format required by the API
    const formattedAttendees = attendees.map((email) => ({ email }));

    // Create the event with Google Meet conferencing
    const event = {
      summary: summary,
      description: description,
      start: {
        dateTime: startTime,
        timeZone: timeZone,
      },
      end: {
        dateTime: endTime,
        timeZone: timeZone,
      },
      attendees: formattedAttendees,
      conferenceData: {
        createRequest: {
          requestId: `meet-${Date.now()}`,
        },
      },
    };

    try {
      const response = await this.calendar.events.insert({
        calendarId: "primary",
        conferenceDataVersion: 1,
        resource: event,
      });

      const createdEvent = response.data;

      if (!createdEvent.conferenceData) {
        throw new Error("Failed to create Google Meet conferencing data");
      }

      const meeting = this._formatMeetingData(createdEvent);
      if (!meeting) {
        throw new Error(
          "Failed to format meeting data for newly created event"
        );
      }

      return meeting;
    } catch (error) {
      throw new Error(`Error creating meeting: ${error.message}`);
    }
  }

  /**
   * Update an existing Google Meet meeting.
   * @param {string} meetingId - ID of the meeting to update
   * @param {Object} updateData - Fields to update
   * @returns {Promise<Object>} - Updated meeting details
   */
  async updateMeeting(
    meetingId,
    { summary, description, startTime, endTime, attendees } = {}
  ) {
    try {
      // First, get the existing event
      const response = await this.calendar.events.get({
        calendarId: "primary",
        eventId: meetingId,
      });

      const event = response.data;

      // Update the fields that were provided
      if (summary !== undefined) {
        event.summary = summary;
      }

      if (description !== undefined) {
        event.description = description;
      }

      if (startTime !== undefined) {
        event.start.dateTime = startTime;
      }

      if (endTime !== undefined) {
        event.end.dateTime = endTime;
      }

      if (attendees !== undefined) {
        event.attendees = attendees.map((email) => ({ email }));
      }

      // Make the API call to update the event
      const updateResponse = await this.calendar.events.update({
        calendarId: "primary",
        eventId: meetingId,
        conferenceDataVersion: 1,
        resource: event,
      });

      const updatedEvent = updateResponse.data;

      if (!updatedEvent.conferenceData) {
        throw new Error(
          "Updated event does not have Google Meet conferencing data"
        );
      }

      const meeting = this._formatMeetingData(updatedEvent);
      if (!meeting) {
        throw new Error("Failed to format meeting data for updated event");
      }

      return meeting;
    } catch (error) {
      throw new Error(`Error updating meeting: ${error.message}`);
    }
  }

  /**
   * Delete a Google Meet meeting.
   * @param {string} meetingId - ID of the meeting to delete
   * @returns {Promise<boolean>} - True if deleted successfully
   */
  async deleteMeeting(meetingId) {
    try {
      await this.calendar.events.delete({
        calendarId: "primary",
        eventId: meetingId,
      });

      return true;
    } catch (error) {
      throw new Error(`Error deleting meeting: ${error.message}`);
    }
  }

  /**
   * Format event data to meeting format.
   * @param {Object} event - Event data from Google Calendar API
   * @returns {Object|null} - Formatted meeting data or null
   */
  _formatMeetingData(event) {
    if (!event.conferenceData) {
      return null;
    }

    // Extract the Google Meet link
    let meetLink = null;
    for (const entryPoint of event.conferenceData.entryPoints || []) {
      if (entryPoint.entryPointType === "video") {
        meetLink = entryPoint.uri;
        break;
      }
    }

    if (!meetLink) {
      return null;
    }

    // Format attendees
    const attendees = (event.attendees || []).map((attendee) => ({
      email: attendee.email,
      response_status: attendee.responseStatus,
    }));

    // Build the formatted meeting data
    const meeting = {
      id: event.id,
      summary: event.summary || "",
      description: event.description || "",
      meet_link: meetLink,
      start_time: event.start?.dateTime || event.start?.date,
      end_time: event.end?.dateTime || event.end?.date,
      attendees: attendees,
      creator: event.creator?.email,
      organizer: event.organizer?.email,
      created: event.created,
      updated: event.updated,
    };

    return meeting;
  }
}

export default GoogleMeetAPI;
