// Token-gated proxy for the CEC election-day turnout feed.
//
// Why this exists: the CEC map service (mapvotes.bechirot.gov.il)
// refuses requests from GitHub Actions runner IPs (403 for every
// client), while Netlify's function IPs pass. The turnout refresh
// workflow therefore downloads the feed through this function
// instead of from the CEC directly. The poller (k26-turnout-poll)
// keeps fetching the CEC itself for dedupe/dispatch decisions.
//
// Gate: requests must carry the K26_FEED_TOKEN env value in the
// x-feed-token header. The token lives only in Netlify env and in a
// GitHub Actions secret — never in the repo. Without the env var
// the proxy is closed (503).
export default async function handler(request) {
  const token = process.env.K26_FEED_TOKEN;
  if (!token) return new Response("feed proxy not configured", { status: 503 });
  if ((request.headers.get("x-feed-token") || "") !== token) {
    return new Response("forbidden", { status: 403 });
  }
  const url = process.env.K26_TURNOUT_URL;
  if (!url) return new Response("K26_TURNOUT_URL unset", { status: 503 });

  const headers = {};
  if (process.env.K26_TURNOUT_AUTH) {
    headers.Authorization = `Basic ${Buffer.from(process.env.K26_TURNOUT_AUTH).toString("base64")}`;
  }
  const fetchUrl = `${url}${url.includes("?") ? "&" : "?"}v=${Date.now()}`;
  let response;
  try {
    response = await fetch(fetchUrl, { redirect: "follow", headers });
  } catch (error) {
    return new Response(`upstream fetch failed: ${String(error)}`, { status: 502 });
  }
  if (!response.ok) {
    return new Response(`upstream returned ${response.status}`, { status: 502 });
  }
  const bytes = await response.arrayBuffer();
  return new Response(bytes, {
    status: 200,
    headers: {
      "Content-Type": response.headers.get("content-type") || "application/json",
      "Cache-Control": "no-store",
    },
  });
}
