import { createRequire } from "node:module";
import { autoEnabled, withinPollWindow } from "../lib/k26/decide.mjs";

const require = createRequire(import.meta.url);
const controlFile = require("../../k26_control.json");

// Reliable trigger for the K26 count refresh. GitHub's own cron
// (schedule: */5 in k26-refresh.yml) can lag badly on first
// registration and drops runs under load, so this Netlify schedule
// simply dispatches the workflow every 5 minutes and lets the
// runner do all the work (Chrome download, inspect, rebuild).
// It never fetches the CEC itself — media26's bot challenge blocks
// plain fetches from here. Dispatches are harmless when nothing
// changed: the workflow inspects the snapshot sha and skips, and
// its concurrency group serializes overlapping runs.
export default async function handler() {
  const result = await dispatch();
  return Response.json(result);
}

export async function dispatch(env = process.env, now = new Date()) {
  if (env.K26_DISPATCH === "0") return { ok: true, action: "skip", reason: "K26_DISPATCH=0" };
  if (!autoEnabled(env, controlFile)) return { ok: true, action: "skip", reason: "auto is off" };
  if (!withinPollWindow(now, controlFile)) return { ok: true, action: "skip", reason: "outside the polling window" };
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) return { ok: false, action: "hold", reason: "GITHUB_DISPATCH_TOKEN unset" };
  const repo = env.K26_GITHUB_REPO || "harelc/elections-vote-transfer";
  const response = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/k26-refresh.yml/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "k26-dispatch",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({ ref: env.K26_GIT_REF || "master" }),
  });
  if (response.status !== 204) {
    return { ok: false, action: "hold", reason: `github dispatch ${response.status}` };
  }
  return { ok: true, action: "dispatch" };
}
