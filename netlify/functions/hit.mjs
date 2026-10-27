import { createHash } from "node:crypto";
import { getStore } from "@netlify/blobs";

// First-party traffic counter (no cookies, no third party).
// A 1-line beacon in i18n.js POSTs {p: location.pathname} here on
// page load. We store, per Asia/Jerusalem hour, in Netlify Blobs:
//   { pv, pages: {path: {pv, ips: [hash...]}}, ips: [hash...] }
// so a report can give pageviews and UNIQUE IPs. Raw IPs are never
// stored: only sha256(ip | day | HIT_SALT), truncated — the day in
// the hash means yesterday's identifiers cannot be linked to
// today's. Counts are approximate (read-modify-write per hour can
// lose an increment under heavy concurrency) — a gauge, not billing.
//
// Report: GET with header x-hit-token: <HIT_READ_TOKEN> returns the
// stored hour buckets, newest first. Without the token: 403.

const BOT_UA = /bot|crawler|spider|headless|preview|monitor/i;

function jerusalemParts(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jerusalem", year: "numeric", month: "2-digit",
    day: "2-digit", hour: "2-digit", hourCycle: "h23",
  }).formatToParts(now);
  const get = (t) => parts.find((p) => p.type === t).value;
  const hour = get("hour") === "24" ? "00" : get("hour");
  return { day: `${get("year")}-${get("month")}-${get("day")}`, hour };
}

function clientIp(request) {
  const nf = request.headers.get("x-nf-client-connection-ip");
  if (nf) return nf.trim();
  const fwd = request.headers.get("x-forwarded-for");
  return fwd ? fwd.split(",")[0].trim() : "";
}

export default async function handler(request) {
  const store = getStore("site-traffic");

  if (request.method === "GET") {
    const token = process.env.HIT_READ_TOKEN;
    if (!token || request.headers.get("x-hit-token") !== token) {
      return new Response("forbidden", { status: 403 });
    }
    const { keys } = await store.list({ prefix: "h:" });
    const hours = [];
    for (const { key } of keys.sort().reverse()) {
      const data = await store.get(key, { type: "json" }).catch(() => null);
      if (!data) continue;
      hours.push({
        hour: key.slice(2),
        pageviews: data.pv || 0,
        unique_ips: (data.ips || []).length,
        pages: Object.entries(data.pages || {})
          .map(([path, p]) => ({ path, pageviews: p.pv || 0, unique_ips: (p.ips || []).length }))
          .sort((a, b) => b.pageviews - a.pageviews),
      });
    }
    return Response.json({ generated: new Date().toISOString(), hours });
  }

  if (request.method !== "POST") return new Response("method not allowed", { status: 405 });

  const ua = request.headers.get("user-agent") || "";
  if (!ua || BOT_UA.test(ua)) return new Response(null, { status: 204 });

  let page = "/";
  try {
    const body = await request.json();
    if (typeof body.p === "string" && body.p.startsWith("/")) page = body.p.slice(0, 80);
  } catch { /* beacon without a body still counts as a hit on / */ }
  page = page.split(/[?#]/)[0] || "/";

  const ip = clientIp(request);
  const { day, hour } = jerusalemParts();
  const salt = process.env.HIT_SALT || "kolot-nodedim";
  const ipHash = ip ? createHash("sha256").update(`${ip}|${day}|${salt}`).digest("hex").slice(0, 16) : null;

  const key = `h:${day}T${hour}`;
  const data = (await store.get(key, { type: "json" }).catch(() => null)) || { pv: 0, pages: {}, ips: [] };
  data.pv += 1;
  const pg = data.pages[page] || (data.pages[page] = { pv: 0, ips: [] });
  pg.pv += 1;
  if (ipHash) {
    if (!data.ips.includes(ipHash)) data.ips.push(ipHash);
    if (!pg.ips.includes(ipHash)) pg.ips.push(ipHash);
  }
  await store.setJSON(key, data);
  return new Response(null, { status: 204 });
}
