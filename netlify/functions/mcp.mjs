import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";
import {
  ballotNeighbors,
  filterSettlements,
  findSettlement,
  listElections,
  officialResults,
  partyNationalHistory,
  partyStrongholds,
  sankey,
  settlementEmbedding,
  settlementPartyHistory,
  settlementResults,
  settlementVolatility,
  transferFlows,
} from "../lib/mcp/query.mjs";
import {
  MAX_QUERY_BODY,
  admit,
  clientIp,
  limitMessage,
  remember,
  summarizeQuery,
} from "../lib/mcp/traffic.mjs";

const READ_ONLY = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
};

const election = z.coerce.number().int().min(16).max(26).describe("Knesset election number, 16 through 26. 26 is simulated.");

function text(data) {
  return { content: [{ type: "text", text: JSON.stringify(data) }] };
}

function buildServer() {
  const server = new McpServer(
    { name: "kolot-nodedim", version: "0.1.0" },
    {
      instructions: [
        "Read-only Israeli Knesset election data (elections 16–25, plus simulated election 26).",
        "Election 26 is not a real result. Say so whenever you cite it.",
        "Sankey figures are a national estimate, not a count of people. Quote the R² returned with them.",
        "t-SNE and UMAP are not maps of Israel. t-SNE distance matters only among nearby ballots.",
        "Seat allocation and regional-district scenarios are not available from these tools.",
        "For one party across many elections, use settlement_party_history or party_national_history instead of calling settlement_results once per year.",
        "If a tool returns an error or candidates, use that. Do not invent numbers.",
      ].join(" "),
    },
  );

  server.registerTool("list_elections", {
    description: "List elections 16–26 with date, turnout, and whether the election is simulated.",
    annotations: READ_ONLY,
  }, async () => text(listElections()));

  server.registerTool("official_results", {
    description: "National seats and votes for one election. Election 26 is simulated.",
    inputSchema: { election },
    annotations: READ_ONLY,
  }, async ({ election: id }) => text(officialResults(id)));

  server.registerTool("find_settlement", {
    description: "Find a settlement by Hebrew or English name. Returns identity and size, not the party table.",
    inputSchema: {
      query: z.string().describe("Hebrew or English settlement name, or part of one."),
      election: election.optional().describe("Election to search. Defaults to 25."),
    },
    annotations: READ_ONLY,
  }, async ({ query, election: id }) => text(findSettlement(query, id ?? 25)));

  server.registerTool("settlement_results", {
    description: "Party shares, turnout, and winner for one settlement in one election. Settlement totals, not ballot boxes.",
    inputSchema: {
      name: z.string().describe("Hebrew or English settlement name."),
      election: election.optional(),
    },
    annotations: READ_ONLY,
  }, async ({ name, election: id }) => text(settlementResults(name, id ?? 25)));

  server.registerTool("party_strongholds", {
    description: "Settlements where a party’s share was highest. Defaults to places with at least 500 voters.",
    inputSchema: {
      party: z.string().describe("Hebrew name, English name, or ballot symbol."),
      election: election.optional(),
      limit: z.number().int().min(1).max(20).optional(),
      min_voters: z.number().min(0).optional().describe("Ignore smaller settlements. Default 500."),
    },
    annotations: READ_ONLY,
  }, async ({ party, election: id, limit, min_voters: minVoters }) => text(partyStrongholds(party, id ?? 25, limit, minVoters)));

  server.registerTool("filter_settlements", {
    description: "Rank or filter settlements by party share, turnout, or number of voters.",
    inputSchema: {
      election: election.optional(),
      party: z.string().optional().describe("Required when sorting or filtering by support."),
      min_support: z.number().min(0).max(100).optional().describe("Minimum party share, in percent."),
      max_support: z.number().min(0).max(100).optional(),
      min_voters: z.number().min(0).optional(),
      sort: z.enum(["voters", "turnout", "support"]).optional(),
      limit: z.number().int().min(1).max(20).optional(),
    },
    annotations: READ_ONLY,
  }, async (args) => text(filterSettlements({
    election: args.election ?? 25,
    party: args.party,
    minSupport: args.min_support,
    maxSupport: args.max_support,
    minVoters: args.min_voters,
    sort: args.sort,
    limit: args.limit,
  })));

  server.registerTool("sankey", {
    description: "Overview of the Sankey between two consecutive elections: each party’s top destinations, plus R². Estimates, not individuals.",
    inputSchema: {
      from_election: election.describe("Earlier election."),
      to_election: election.describe("The next election. Only consecutive pairs exist."),
      include_abstention: z.boolean().optional().describe("Add the did-not-vote pseudo-party. Unreliable for 16→17 and 17→18."),
    },
    annotations: READ_ONLY,
  }, async ({ from_election: fromElection, to_election: toElection, include_abstention: includeAbstention }) => text(sankey(fromElection, toElection, includeAbstention)));

  server.registerTool("transfer_flows", {
    description: "Drill into the Sankey. Filter by source party, destination party, or both. percentage is the share of the source party. percentage_ci is the 95% ballot-bootstrap interval when one was published.",
    inputSchema: {
      from_election: election,
      to_election: election,
      source: z.string().optional().describe("Party in the earlier election."),
      target: z.string().optional().describe("Party in the later election."),
      include_abstention: z.boolean().optional(),
      limit: z.number().int().min(1).max(20).optional(),
    },
    annotations: READ_ONLY,
  }, async (args) => text(transferFlows({
    fromElection: args.from_election,
    toElection: args.to_election,
    source: args.source,
    target: args.target,
    includeAbstention: args.include_abstention,
    limit: args.limit,
  })));

  server.registerTool("settlement_embedding", {
    description: "Where a settlement sits in the t-SNE or UMAP ballot plot, and which settlements are nearest in that plot. Not geography.",
    inputSchema: {
      name: z.string().describe("Hebrew or English settlement name."),
      election: election.optional(),
      space: z.enum(["tsne", "umap"]).optional().describe("Defaults to tsne."),
      limit: z.number().int().min(1).max(20).optional(),
    },
    annotations: READ_ONLY,
  }, async ({ name, election: id, space, limit }) => text(settlementEmbedding(name, id ?? 25, space, limit)));

  server.registerTool("ballot_neighbors", {
    description: "Ballots closest to one ballot in t-SNE or UMAP space. Use for “what votes like this box”, not for map distance.",
    inputSchema: {
      settlement: z.string().describe("Hebrew or English settlement name."),
      ballot: z.coerce.string().describe("Ballot number within the settlement, as published (for example 1 or 14.1)."),
      election: election.optional(),
      space: z.enum(["tsne", "umap"]).optional(),
      limit: z.number().int().min(1).max(20).optional(),
      outside_settlement: z.boolean().optional().describe("Skip other ballots in the same settlement."),
    },
    annotations: READ_ONLY,
  }, async ({ settlement, ballot, election: id, space, limit, outside_settlement: outsideSettlement }) => text(ballotNeighbors(settlement, ballot, id ?? 25, space, limit, outsideSettlement)));

  server.registerTool("settlement_volatility", {
    description: "How much a settlement’s party mix changed across elections (Pedersen-style index). Higher means more change.",
    inputSchema: { name: z.string().describe("Hebrew or English settlement name.") },
    annotations: READ_ONLY,
  }, async ({ name }) => text(settlementVolatility(name)));

  server.registerTool("settlement_party_history", {
    description: "One party’s share in one settlement across elections 16–26, and which election was its high. One call, not one per election. A joint list such as הליכוד ישראל ביתנו does not match הליכוד.",
    inputSchema: {
      party: z.string().describe("Hebrew name, English name, or ballot symbol."),
      settlement: z.string().describe("Hebrew or English settlement name."),
    },
    annotations: READ_ONLY,
  }, async ({ party, settlement }) => text(settlementPartyHistory(party, settlement)));

  server.registerTool("party_national_history", {
    description: "National seats and votes for one party across elections 16–26, and which election was its high. Election 26 is simulated.",
    inputSchema: {
      party: z.string().describe("Hebrew name, English name, or ballot symbol."),
    },
    annotations: READ_ONLY,
  }, async ({ party }) => text(partyNationalHistory(party)));

  return server;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, Mcp-Session-Id, Mcp-Protocol-Version",
};

function withCors(response) {
  const headers = new Headers(response.headers);
  for (const [key, value] of Object.entries(CORS)) headers.set(key, value);
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

function rpcError(status, id, message) {
  return new Response(JSON.stringify({
    jsonrpc: "2.0",
    id: id ?? null,
    error: { code: -32000, message },
  }), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Retry-After": status === 429 ? "60" : "0",
      ...CORS,
    },
  });
}

function requestId(raw) {
  try {
    const parsed = JSON.parse(raw);
    const message = Array.isArray(parsed) ? parsed[0] : parsed;
    return message && Object.prototype.hasOwnProperty.call(message, "id") ? message.id : null;
  } catch {
    return null;
  }
}

export default async function handler(req) {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405, headers: CORS });

  const raw = await req.text();
  const ip = clientIp(req);
  const queries = summarizeQuery(raw);
  if (raw.length > MAX_QUERY_BODY) {
    await remember({ ip, status: 413, reason: "body", queries }).catch(() => {});
    return rpcError(413, requestId(raw), "Request body is too large.");
  }

  const gate = await admit(ip);
  if (!gate.ok) {
    await remember({ ip, status: 429, reason: gate.reason, queries }).catch(() => {});
    return rpcError(429, requestId(raw), limitMessage(gate.reason));
  }

  const replay = new Request(req.url, { method: "POST", headers: req.headers, body: raw });
  const server = buildServer();
  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  await server.connect(transport);
  const response = withCors(await transport.handleRequest(replay));
  await remember({ ip, status: response.status, queries }).catch(() => {});
  return response;
}

export const config = {
  includedFiles: ["netlify/lib/mcp/mcp-data/**"],
  rateLimit: {
    windowSize: 60,
    windowLimit: 20,
    aggregateBy: ["ip"],
  },
};
