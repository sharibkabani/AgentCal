#!/usr/bin/env node

/**
 * Google Meet MCP Server
 * This implements the Model Context Protocol server for Google Meet
 * functionality via the Google Calendar API.
 */

import "dotenv/config";
import path from "path";
import { fileURLToPath } from "url";
import process from "process";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

import GoogleMeetAPI from "./GoogleMeetAPI.js";

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class GoogleMeetMcpServer {
  /**
   * Initialize the Google Meet MCP server
   */
  constructor() {
    this.server = new Server(
      {
        name: "google-meet-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Setup Google Meet API client
    const credentialsPath = process.env.GOOGLE_MEET_CREDENTIALS_PATH;
    const tokenPath = process.env.GOOGLE_MEET_TOKEN_PATH;

    if (!credentialsPath || !tokenPath) {
      console.error("Error: Missing required environment variables.");
      console.error(
        "Please set GOOGLE_MEET_CREDENTIALS_PATH and GOOGLE_MEET_TOKEN_PATH"
      );
      process.exit(1);
    }

    this.googleMeet = new GoogleMeetAPI(credentialsPath, tokenPath);

    // Setup request handlers
    this.setupToolHandlers();

    // Error handling
    this.server.onerror = (error) => console.error(`[MCP Error] ${error}`);

    process.on("SIGINT", async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  /**
   * Set up the tool request handlers
   */
  setupToolHandlers() {
    this.server.setRequestHandler(
      ListToolsRequestSchema,
      this.handleListTools.bind(this)
    );
    this.server.setRequestHandler(
      CallToolRequestSchema,
      this.handleCallTool.bind(this)
    );
  }

  /**
   * Handle requests to list available tools
   */
  async handleListTools() {
    return {
      tools: [
        {
          name: "list_meetings",
          description: "List upcoming Google Meet meetings",
          inputSchema: {
            type: "object",
            properties: {
              max_results: {
                type: "number",
                description:
                  "Maximum number of results to return (default: 10)",
              },
              time_min: {
                type: "string",
                description: "Start time in ISO format (default: now)",
              },
              time_max: {
                type: "string",
                description: "End time in ISO format (optional)",
              },
            },
            required: [],
          },
        },
        {
          name: "get_meeting",
          description: "Get details of a specific Google Meet meeting",
          inputSchema: {
            type: "object",
            properties: {
              meeting_id: {
                type: "string",
                description: "ID of the meeting to retrieve",
              },
            },
            required: ["meeting_id"],
          },
        },
        {
          name: "create_meeting",
          description: "Create a new Google Meet meeting",
          inputSchema: {
            type: "object",
            properties: {
              summary: {
                type: "string",
                description: "Title of the meeting",
              },
              description: {
                type: "string",
                description: "Description for the meeting (optional)",
              },
              start_time: {
                type: "string",
                description: "Start time in ISO format",
              },
              end_time: {
                type: "string",
                description: "End time in ISO format",
              },
              attendees: {
                type: "array",
                description: "List of email addresses for attendees (optional)",
                items: {
                  type: "string",
                },
              },
              time_zone: {
                type: "string",
                description: "IANA timezone (e.g., 'America/New_York', 'America/Los_Angeles'). Defaults to UTC if not specified.",
              },
            },
            required: ["summary", "start_time", "end_time"],
          },
        },
        {
          name: "update_meeting",
          description: "Update an existing Google Meet meeting",
          inputSchema: {
            type: "object",
            properties: {
              meeting_id: {
                type: "string",
                description: "ID of the meeting to update",
              },
              summary: {
                type: "string",
                description: "Updated title of the meeting (optional)",
              },
              description: {
                type: "string",
                description: "Updated description for the meeting (optional)",
              },
              start_time: {
                type: "string",
                description: "Updated start time in ISO format (optional)",
              },
              end_time: {
                type: "string",
                description: "Updated end time in ISO format (optional)",
              },
              attendees: {
                type: "array",
                description:
                  "Updated list of email addresses for attendees (optional)",
                items: {
                  type: "string",
                },
              },
            },
            required: ["meeting_id"],
          },
        },
        {
          name: "delete_meeting",
          description: "Delete a Google Meet meeting",
          inputSchema: {
            type: "object",
            properties: {
              meeting_id: {
                type: "string",
                description: "ID of the meeting to delete",
              },
            },
            required: ["meeting_id"],
          },
        },
      ],
    };
  }

  /**
   * Handle tool calls
   */
  async handleCallTool(request) {
    // Initialize the API if not already initialized
    if (!this.googleMeet.calendar) {
      try {
        await this.googleMeet.initialize();
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error initializing Google Meet API: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    }

    const toolName = request.params.name;
    const args = request.params.arguments || {};

    try {
      if (toolName === "list_meetings") {
        const maxResults = args.max_results || 10;
        const timeMin = args.time_min || null;
        const timeMax = args.time_max || null;

        const meetings = await this.googleMeet.listMeetings(
          maxResults,
          timeMin,
          timeMax
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(meetings, null, 2),
            },
          ],
        };
      } else if (toolName === "get_meeting") {
        const meetingId = args.meeting_id;
        if (!meetingId) {
          throw new McpError(ErrorCode.InvalidParams, "meeting_id is required");
        }

        const meeting = await this.googleMeet.getMeeting(meetingId);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(meeting, null, 2),
            },
          ],
        };
      } else if (toolName === "create_meeting") {
        const {
          summary,
          description = "",
          start_time,
          end_time,
          attendees = [],
          time_zone = "UTC",
        } = args;

        // Validate required parameters
        if (!summary || !start_time || !end_time) {
          const missing = [];
          if (!summary) missing.push("summary");
          if (!start_time) missing.push("start_time");
          if (!end_time) missing.push("end_time");

          throw new McpError(
            ErrorCode.InvalidParams,
            `Missing required parameters: ${missing.join(", ")}`
          );
        }

        const meeting = await this.googleMeet.createMeeting(
          summary,
          start_time,
          end_time,
          description,
          attendees,
          time_zone
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(meeting, null, 2),
            },
          ],
        };
      } else if (toolName === "update_meeting") {
        const {
          meeting_id,
          summary,
          description,
          start_time,
          end_time,
          attendees,
        } = args;

        if (!meeting_id) {
          throw new McpError(ErrorCode.InvalidParams, "meeting_id is required");
        }

        // Extract optional parameters
        const updateData = {};
        if (summary !== undefined) updateData.summary = summary;
        if (description !== undefined) updateData.description = description;
        if (start_time !== undefined) updateData.startTime = start_time;
        if (end_time !== undefined) updateData.endTime = end_time;
        if (attendees !== undefined) updateData.attendees = attendees;

        if (Object.keys(updateData).length === 0) {
          throw new McpError(
            ErrorCode.InvalidParams,
            "At least one field to update must be provided"
          );
        }

        const meeting = await this.googleMeet.updateMeeting(
          meeting_id,
          updateData
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(meeting, null, 2),
            },
          ],
        };
      } else if (toolName === "delete_meeting") {
        const { meeting_id } = args;

        if (!meeting_id) {
          throw new McpError(ErrorCode.InvalidParams, "meeting_id is required");
        }

        await this.googleMeet.deleteMeeting(meeting_id);

        return {
          content: [
            {
              type: "text",
              text: "Meeting successfully deleted",
            },
          ],
        };
      } else {
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${toolName}`
        );
      }
    } catch (error) {
      // Handle any errors from Google API or MCP errors
      if (error instanceof McpError) {
        throw error;
      }

      return {
        content: [
          {
            type: "text",
            text: `Error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  /**
   * Run the server
   */
  async run() {
    const transport = new StdioServerTransport();
    console.error("Google Meet MCP server starting on stdio...");
    await this.server.connect(transport);
    console.error("Google Meet MCP server connected");
  }
}

// Create and run the server
const server = new GoogleMeetMcpServer();
server.run().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
