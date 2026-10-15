import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { autoEnabled, decide, pollGate } from "../lib/k26/decide.mjs";

const require = createRequire(import.meta.url);
const controlFile = require("../../k26_control.json");

export default async function handler() {
  const result = await poll();
  return Response.json(result);
}

export async function poll(env = process.env, now = new Date()) {
  const gate = pollGate(env, controlFile, now);
  if (!gate.open) return { ok: true, action: "skip", reason: gate.reason };

  const url = env.K26_RESULTS_URL;
  if (!url) return { ok: true, action: "skip", reason: "K26_RESULTS_URL unset" };

  let response;
  try {
    response = await fetch(url, { redirect: "follow" });
  } catch (error) {
    return { ok: false, action: "reject", reason: "fetch failed", detail: String(error) };
  }
  if (!response.ok) {
    return { ok: false, action: "reject", reason: `source returned ${response.status}` };
  }

  const bytes = new Uint8Array(await response.arrayBuffer());
  const inspected = inspect(bytes, response.headers);
  if (!inspected) {
    return { ok: false, action: "reject", reason: "unrecognized file" };
  }

  const roster = Number(controlFile.roster) || 12018;
  const next = {
    sha256: sha256(bytes),
    ballotCount: inspected.ballotCount,
    asOf: inspected.asOf || response.headers.get("last-modified") || new Date().toISOString(),
    final: inspected.final || inspected.ballotCount >= roster,
  };
  const github = await githubState(env);
  const decision = decide({
    previous: { accepted: github.accepted },
    next,
    now: Date.now(),
    auto: autoEnabled(env, controlFile),
    allowShrink: env.K26_ALLOW_SHRINK === "1",
  });
  const result = { ...decision, ballots: next.ballotCount, sha256: next.sha256 };
  if (decision.action !== "dispatch") {
    return { ok: decision.action !== "reject", ...result };
  }
  if (github.runs > 0) {
    return { ok: true, action: "skip", reason: "rebuild in progress", ...result };
  }
  const dispatched = await dispatch(env, next);
  if (!dispatched.ok) {
    return { ok: false, action: "hold", reason: dispatched.reason, ballots: next.ballotCount, sha256: next.sha256 };
  }
  return { ok: true, action: "dispatch", reason: decision.reason, ballots: next.ballotCount, sha256: next.sha256 };
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function githubHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "User-Agent": "k26-poll",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

async function githubState(env) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) return { accepted: null, runs: 0 };
  const repo = env.K26_GITHUB_REPO || "harelc/elections-vote-transfer";
  const headers = githubHeaders(token);
  const ref = env.K26_GIT_REF || "master";
  const statusRes = await fetch(`https://api.github.com/repos/${repo}/contents/site/data/k26_status.json?ref=${encodeURIComponent(ref)}`, { headers });
  let accepted = null;
  if (statusRes.ok) {
    const body = await statusRes.json();
    const encoded = String(body.content || "").replace(/\n/g, "");
    const json = JSON.parse(Buffer.from(encoded, "base64").toString("utf8"));
    if (json.sha256 && json.ballots != null) {
      accepted = { sha256: json.sha256, ballotCount: Number(json.ballots), asOf: json.as_of || null };
    }
  }
  let runs = 0;
  for (const status of ["queued", "in_progress"]) {
    const runRes = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/k26-refresh.yml/runs?status=${status}&per_page=1`, { headers });
    if (!runRes.ok) continue;
    const body = await runRes.json();
    runs += body.total_count || 0;
  }
  return { accepted, runs };
}

export function inspect(bytes, headers = new Headers()) {
  const text = new TextDecoder("utf-8").decode(bytes).replace(/^\uFEFF/, "");
  const trimmed = text.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith("{")) {
    let data;
    try { data = JSON.parse(trimmed); } catch { return null; }
    const rows = Array.isArray(data.rows) ? data.rows : null;
    if (!rows || !Array.isArray(data.columns)) return null;
    return {
      ballotCount: rows.length,
      asOf: typeof data.as_of === "string" ? data.as_of : null,
      final: data.final === true || headers.get("x-k26-final") === "true",
    };
  }
  const lines = text.split(/\r?\n/).filter((line) => line.trim() !== "");
  if (lines.length < 2) return null;
  const header = lines[0].replace(/^\uFEFF/, "");
  if (!header.includes("קלפי") && !header.includes("מספר קלפי")) return null;
  return {
    ballotCount: lines.length - 1,
    asOf: null,
    final: headers.get("x-k26-final") === "true",
  };
}

async function dispatch(env, next) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) return { ok: false, reason: "GITHUB_DISPATCH_TOKEN unset" };
  const repo = env.K26_GITHUB_REPO || "harelc/elections-vote-transfer";
  const response = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/k26-refresh.yml/dispatches`, {
    method: "POST",
    headers: githubHeaders(token),
    body: JSON.stringify({
      ref: env.K26_GIT_REF || "master",
      inputs: {
        sha256: next.sha256,
        ballot_count: String(next.ballotCount),
        as_of: next.asOf || "",
        final: next.final ? "true" : "false",
        force: "false",
      },
    }),
  });
  if (response.status !== 204) {
    return { ok: false, reason: `github dispatch ${response.status}` };
  }
  return { ok: true };
}
