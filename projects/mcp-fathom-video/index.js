import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_BASE = "https://api.fathom.ai/external/v1";
const API_KEY = process.env.FATHOM_API_KEY;

if (!API_KEY) {
  console.error("FATHOM_API_KEY environment variable is required");
  process.exit(1);
}

async function fathomRequest(path, params = {}) {
  const url = new URL(`${API_BASE}${path}`);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v));
      } else {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const res = await fetch(url.toString(), {
    headers: {
      "X-Api-Key": API_KEY,
      Accept: "application/json",
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Fathom API ${res.status}: ${body}`);
  }

  return res.json();
}

const server = new McpServer({
  name: "fathom-video",
  version: "1.0.0",
});

// List meetings
server.tool(
  "list_meetings",
  "List Fathom.video meetings with optional filters for date, domain, team, and recorder. Can optionally include summaries, transcripts, and action items inline.",
  {
    created_after: z
      .string()
      .optional()
      .describe("ISO 8601 timestamp — only meetings created after this date"),
    created_before: z
      .string()
      .optional()
      .describe("ISO 8601 timestamp — only meetings created before this date"),
    teams: z
      .array(z.string())
      .optional()
      .describe("Filter by team names"),
    recorded_by: z
      .array(z.string())
      .optional()
      .describe("Filter by recorder email addresses"),
    calendar_invitees_domains: z
      .array(z.string())
      .optional()
      .describe("Filter by invitee company domains"),
    include_summary: z
      .boolean()
      .optional()
      .describe("Include AI summary in response"),
    include_transcript: z
      .boolean()
      .optional()
      .describe("Include transcript in response"),
    include_action_items: z
      .boolean()
      .optional()
      .describe("Include action items in response"),
    cursor: z.string().optional().describe("Pagination cursor"),
  },
  async (params) => {
    try {
      const queryParams = {};
      if (params.created_after) queryParams.created_after = params.created_after;
      if (params.created_before) queryParams.created_before = params.created_before;
      if (params.teams) queryParams["teams[]"] = params.teams;
      if (params.recorded_by) queryParams["recorded_by[]"] = params.recorded_by;
      if (params.calendar_invitees_domains)
        queryParams["calendar_invitees_domains[]"] = params.calendar_invitees_domains;
      if (params.include_summary) queryParams.include_summary = "true";
      if (params.include_transcript) queryParams.include_transcript = "true";
      if (params.include_action_items) queryParams.include_action_items = "true";
      if (params.cursor) queryParams.cursor = params.cursor;

      const data = await fathomRequest("/meetings", queryParams);
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// Get recording summary
server.tool(
  "get_summary",
  "Get the AI-generated summary for a specific Fathom.video recording by its recording ID.",
  {
    recording_id: z
      .number()
      .describe("The ID of the meeting recording to fetch the summary for"),
  },
  async (params) => {
    try {
      const data = await fathomRequest(
        `/recordings/${params.recording_id}/summary`
      );
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// Get recording transcript
server.tool(
  "get_transcript",
  "Get the full transcript for a specific Fathom.video recording by its recording ID. Returns speaker names, text, and timestamps.",
  {
    recording_id: z
      .number()
      .describe("The ID of the meeting recording to fetch the transcript for"),
  },
  async (params) => {
    try {
      const data = await fathomRequest(
        `/recordings/${params.recording_id}/transcript`
      );
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// Search meetings (by listing with filters — Fathom API doesn't have a dedicated search endpoint)
server.tool(
  "search_meetings",
  "Search for Fathom.video meetings by date range. Use created_after/created_before to narrow results. Returns meetings with basic metadata.",
  {
    created_after: z
      .string()
      .optional()
      .describe("ISO 8601 timestamp — only meetings after this date"),
    created_before: z
      .string()
      .optional()
      .describe("ISO 8601 timestamp — only meetings before this date"),
    include_summary: z
      .boolean()
      .optional()
      .describe("Include AI summary in results"),
  },
  async (params) => {
    try {
      const queryParams = {};
      if (params.created_after) queryParams.created_after = params.created_after;
      if (params.created_before) queryParams.created_before = params.created_before;
      if (params.include_summary) queryParams.include_summary = "true";

      const data = await fathomRequest("/meetings", queryParams);
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

// List teams
server.tool(
  "list_teams",
  "List all teams in your Fathom.video workspace.",
  {},
  async () => {
    try {
      const data = await fathomRequest("/teams");
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
