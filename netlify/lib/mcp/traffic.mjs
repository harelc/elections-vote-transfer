import { createHash, randomBytes, timingSafeEqual } from "node:crypto";

export const MAX_QUERY_BODY = 16_000;
const LOG_KEEP = 150;

const memory = {
  counts: new Map(),
  log: [],
  bursts: new Map(),
};

let storePromise = null;

export function limits() {
  return {
    daily: positiveInt(process.env.MCP_DAILY_LIMIT, 1500),
    ipDaily: positiveInt(process.env.MCP_IP_DAILY_LIMIT, 300),
    perMinute: positiveInt(process.env.MCP_PER_MINUTE, 20),
  };
}

function positiveInt(value, fallback) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : fallback;
}

export function jerusalemDay(now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jerusalem",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

export function clientIp(req) {
  const netlifyIp = req.headers.get("x-nf-client-connection-ip");
  if (netlifyIp) return netlifyIp.trim();
  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0].trim();
  return "unknown";
}

function ipKey(ip) {
  return createHash("sha256").update(String(ip)).digest("hex").slice(0, 16);
}

function slimParams(params) {
  if (!params || typeof params !== "object") return null;
  const copy = { ...params };
  delete copy._meta;
  const text = JSON.stringify(copy);
  if (text.length <= 800) return copy;
  return { truncated: text.slice(0, 800) };
}

export function summarizeQuery(raw) {
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [{ method: "unparsed", arguments: String(raw).slice(0, 500) }];
  }
  const messages = Array.isArray(parsed) ? parsed : [parsed];
  return messages.slice(0, 8).map((msg) => {
    const params = msg && typeof msg.params === "object" && msg.params ? msg.params : {};
    const args = params.arguments && typeof params.arguments === "object" ? params.arguments : null;
    return {
      method: typeof msg?.method === "string" ? msg.method : null,
      tool: typeof params.name === "string" ? params.name : null,
      arguments: args || slimParams(params),
    };
  });
}

function blobStore() {
  if (process.env.MCP_TRAFFIC_MEMORY === "1") return Promise.resolve(null);
  if (!storePromise) {
    storePromise = import("@netlify/blobs")
      .then(({ getStore }) => getStore("mcp-traffic"))
      .catch(() => null);
  }
  return storePromise;
}

async function usingStore(fn) {
  const store = await blobStore();
  if (!store) return fn(null);
  try {
    return await fn(store);
  } catch (error) {
    console.log(`mcp-traffic store unavailable: ${error.message}`);
    storePromise = Promise.resolve(null);
    return fn(null);
  }
}

async function readCount(store, key) {
  if (!store) return memory.counts.get(key) || 0;
  return Number(await store.get(key)) || 0;
}

async function writeCount(store, key, value) {
  if (!store) {
    memory.counts.set(key, value);
    return;
  }
  await store.set(key, String(value));
}

function burstLimited(ip, perMinute) {
  const now = Date.now();
  const recent = (memory.bursts.get(ip) || []).filter((time) => now - time < 60_000);
  if (recent.length >= perMinute) {
    memory.bursts.set(ip, recent);
    return true;
  }
  recent.push(now);
  memory.bursts.set(ip, recent);
  return false;
}

export async function admit(ip) {
  const cap = limits();
  const day = jerusalemDay();
  return usingStore(async (store) => {
    const siteKey = `day:${day}`;
    const ipCountKey = `ip:${day}:${ipKey(ip)}`;
    const siteCount = await readCount(store, siteKey);
    const ipCount = await readCount(store, ipCountKey);
    if (siteCount >= cap.daily) {
      return { ok: false, reason: "daily", day, siteCount, ipCount, limits: cap };
    }
    if (ipCount >= cap.ipDaily) {
      return { ok: false, reason: "ip", day, siteCount, ipCount, limits: cap };
    }
    if (burstLimited(ip, cap.perMinute)) {
      return { ok: false, reason: "minute", day, siteCount, ipCount, limits: cap };
    }
    await writeCount(store, siteKey, siteCount + 1);
    await writeCount(store, ipCountKey, ipCount + 1);
    return { ok: true, day, siteCount: siteCount + 1, ipCount: ipCount + 1, limits: cap };
  });
}

export async function remember(entry) {
  const row = {
    t: new Date().toISOString(),
    ip: entry.ip,
    status: entry.status,
    reason: entry.reason || null,
    queries: entry.queries,
  };
  console.log(`mcp-query ${JSON.stringify(row)}`);
  await usingStore(async (store) => {
    if (!store) {
      memory.log.unshift(row);
      memory.log.length = Math.min(memory.log.length, LOG_KEEP);
      return;
    }
    const key = `q/${Date.now()}-${randomBytes(3).toString("hex")}`;
    await store.set(key, JSON.stringify(row));
  });
}

export async function recentQueries() {
  const cap = limits();
  const day = jerusalemDay();
  return usingStore(async (store) => {
    const count = await readCount(store, `day:${day}`);
    let queries;
    if (!store) {
      queries = memory.log.slice(0, LOG_KEEP);
    } else {
      const listed = await store.list({ prefix: "q/" });
      const blobs = (Array.isArray(listed) ? listed : listed.blobs || [])
        .slice()
        .sort((a, b) => (a.key < b.key ? 1 : -1));
      queries = [];
      for (const blob of blobs.slice(0, LOG_KEEP)) {
        const raw = await store.get(blob.key);
        if (!raw) continue;
        try {
          queries.push(JSON.parse(raw));
        } catch {
          // Skip a damaged row rather than hiding the rest of the log.
        }
      }
      await Promise.all(blobs.slice(LOG_KEEP).map((blob) => store.delete(blob.key)));
    }
    return {
      day,
      count,
      daily_limit: cap.daily,
      ip_daily_limit: cap.ipDaily,
      per_minute: cap.perMinute,
      queries,
    };
  });
}

export function logTokenOk(header) {
  const expected = process.env.MCP_LOG_TOKEN || "";
  if (!expected) return false;
  const token = String(header || "").replace(/^Bearer\s+/i, "");
  const presented = Buffer.from(token);
  const required = Buffer.from(expected);
  if (presented.length !== required.length || presented.length === 0) return false;
  return timingSafeEqual(presented, required);
}

export function resetTrafficForTests() {
  memory.counts.clear();
  memory.log.length = 0;
  memory.bursts.clear();
  storePromise = null;
}

export function limitMessage(reason) {
  if (reason === "daily") return "This site has hit its daily query limit. Try again tomorrow.";
  if (reason === "ip") return "Too many queries from this network today. Try again tomorrow.";
  return "Too many queries this minute. Wait a minute and try again.";
}
