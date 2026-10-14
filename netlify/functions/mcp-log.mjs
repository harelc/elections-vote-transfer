import { logTokenOk, recentQueries } from "../lib/mcp/traffic.mjs";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Cache-Control": "no-store",
};

export default async function handler(req) {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (!process.env.MCP_LOG_TOKEN) return new Response("Not found", { status: 404, headers: CORS });
  if (!logTokenOk(req.headers.get("authorization"))) {
    return Response.json({ error: "unauthorized" }, { status: 401, headers: CORS });
  }
  if (req.method !== "GET") return new Response("Method not allowed", { status: 405, headers: CORS });
  return Response.json(await recentQueries(), { headers: CORS });
}
