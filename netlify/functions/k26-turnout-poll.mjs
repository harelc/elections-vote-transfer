import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { decideTurnout, inspectTurnout, turnoutAutoEnabled, turnoutGate } from "../lib/k26/turnout.mjs";

const require = createRequire(import.meta.url);
const controlFile = require("../../k26_control.json");

// Scheduled election-day turnout poller (see netlify.toml). Mirrors
// k26-poll.mjs (results) but for the pre-results hours: fetch the CEC
// turnout feed from the operator-configured K26_TURNOUT_URL, dedupe
// against the source hash committed in turnout_day_26.json, and
// dispatch k26-turnout-refresh.yml to rebuild + publish. The feed's
// real interface is unknown; inspectTurnout in lib/k26/turnout.mjs is
// the adapter seam.
export default async function handler() {
  const result = await pollTurnout();
  return Response.json(result);
}

export async function pollTurnout(env = process.env, now = new Date(), fetchImpl = fetch) {
  const gate = turnoutGate(env, controlFile, now);
  if (!gate.open) return { ok: true, action: "skip", reason: gate.reason };

  const url = env.K26_TURNOUT_URL;
  if (!url) return { ok: true, action: "skip", reason: "K26_TURNOUT_URL unset" };

  let response;
  try {
    response = await fetchImpl(url, { redirect: "follow" });
  } catch (error) {
    return { ok: false, action: "reject", reason: "fetch failed", detail: String(error) };
  }
  if (!response.ok) {
    return { ok: false, action: "reject", reason: `source returned ${response.status}` };
  }

  const bytes = new Uint8Array(await response.arrayBuffer());
  const inspected = inspectTurnout(bytes, response.headers);
  if (!inspected) {
    return { ok: false, action: "reject", reason: "unrecognized turnout feed" };
  }
  const next = {
    sha256: sha256(bytes),
    rowCount: inspected.rowCount,
    asOf: inspected.asOf || response.headers.get("last-modified") || new Date().toISOString(),
  };

  const github = await githubState(env, fetchImpl);
  // Results already flowing: the turnout view's day is over.
  if (github.statusKind === "partial" || github.statusKind === "official") {
    return { ok: true, action: "skip", reason: "results already flowing" };
  }
  const decision = decideTurnout({
    acceptedSha256: github.acceptedSha256,
    next,
    auto: turnoutAutoEnabled(env, controlFile),
  });
  const result = { ...decision, rows: next.rowCount, sha256: next.sha256 };
  if (decision.action !== "dispatch") {
    return { ok: decision.action !== "reject", ...result };
  }
  if (github.runs > 0) {
    return { ok: true, action: "skip", reason: "turnout rebuild in progress", ...result };
  }
  const dispatched = await dispatch(env, next, fetchImpl);
  if (!dispatched.ok) {
    return { ok: false, action: "hold", reason: dispatched.reason, rows: next.rowCount, sha256: next.sha256 };
  }
  return { ok: true, action: "dispatch", reason: decision.reason, rows: next.rowCount, sha256: next.sha256 };
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function githubHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "User-Agent": "k26-turnout-poll",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

async function githubFile(env, fetchImpl, path) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) return null;
  const repo = env.K26_GITHUB_REPO || "harelc/elections-vote-transfer";
  const ref = env.K26_GIT_REF || "master";
  const res = await fetchImpl(`https://api.github.com/repos/${repo}/contents/${path}?ref=${encodeURIComponent(ref)}`, { headers: githubHeaders(token) });
  if (!res.ok) return null;
  const body = await res.json();
  const encoded = String(body.content || "").replace(/\n/g, "");
  try {
    return JSON.parse(Buffer.from(encoded, "base64").toString("utf8"));
  } catch {
    return null;
  }
}

async function githubState(env, fetchImpl) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) return { acceptedSha256: null, statusKind: null, runs: 0 };
  const [status, turnout] = await Promise.all([
    githubFile(env, fetchImpl, "site/data/k26_status.json"),
    githubFile(env, fetchImpl, "site/data/turnout_day_26.json"),
  ]);
  const repo = env.K26_GITHUB_REPO || "harelc/elections-vote-transfer";
  let runs = 0;
  for (const runStatus of ["queued", "in_progress"]) {
    const runRes = await fetchImpl(`https://api.github.com/repos/${repo}/actions/workflows/k26-turnout-refresh.yml/runs?status=${runStatus}&per_page=1`, { headers: githubHeaders(token) });
    if (!runRes.ok) continue;
    const body = await runRes.json();
    runs += body.total_count || 0;
  }
  return {
    acceptedSha256: (turnout && turnout.meta && turnout.meta.source_sha256) || null,
    statusKind: status && status.kind,
    runs,
  };
}

async function dispatch(env, next, fetchImpl) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) return { ok: false, reason: "GITHUB_DISPATCH_TOKEN unset" };
  const repo = env.K26_GITHUB_REPO || "harelc/elections-vote-transfer";
  const response = await fetchImpl(`https://api.github.com/repos/${repo}/actions/workflows/k26-turnout-refresh.yml/dispatches`, {
    method: "POST",
    headers: githubHeaders(token),
    body: JSON.stringify({
      ref: env.K26_GIT_REF || "master",
      inputs: {
        sha256: next.sha256,
        rows: String(next.rowCount),
        as_of: next.asOf || "",
        force: "false",
      },
    }),
  });
  if (response.status !== 204) {
    return { ok: false, reason: `github dispatch ${response.status}` };
  }
  return { ok: true };
}
