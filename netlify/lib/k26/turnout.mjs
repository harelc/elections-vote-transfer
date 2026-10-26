/** Election-day turnout polling: gate, feed inspection, dispatch decision.
 *
 * The CEC turnout interface is NOT yet known (unknown URL, unknown
 * shape). The seams are deliberately narrow:
 *   - URL: env K26_TURNOUT_URL only (never user input; the fetch target
 *     is operator-configured, which is the SSRF control here -- CWE-918).
 *   - Shape: inspectTurnout() below is the single adapter. Today it
 *     accepts CSV / {columns,rows} JSON / generic XML and extracts only
 *     a row count + timestamp; extend it when the real feed is known,
 *     together with ALIASES in generate_turnout_day_data.py.
 *   - Decision: turnout snapshots replace each other (they are not a
 *     growing ballot count), so any new hash dispatches, the same hash
 *     skips, and unreadable/HTML payloads reject.
 */

/** Local minute in the polling timezone, YYYY-MM-DDTHH:mm. */
function localStamp(now, timeZone) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(now);
  const get = (type) => parts.find((part) => part.type === type).value;
  const hour = get("hour") === "24" ? "00" : get("hour");
  return `${get("year")}-${get("month")}-${get("day")}T${hour}:${get("minute")}`;
}

/** Turnout has its own daytime window (turnout_* fields), separate from
 * the results window that opens at 21:00. K26_TURNOUT_POLL=0 stops early. */
export function turnoutGate(env, file, now) {
  const override = env && env.K26_TURNOUT_POLL;
  if (override === "0" || override === "false") return { open: false, reason: "turnout polling stopped" };
  if (file && file.turnout_poll === false && override !== "1" && override !== "true") {
    return { open: false, reason: "turnout polling stopped" };
  }
  const start = file && file.turnout_poll_start, end = file && file.turnout_poll_end;
  if (start && end) {
    const tz = file.timezone || "Asia/Jerusalem";
    const stamp = localStamp(now, tz);
    if (stamp < start.slice(0, 16) || stamp > end.slice(0, 16)) {
      return { open: false, reason: "outside the turnout polling window" };
    }
  }
  return { open: true };
}

/** Whether a new snapshot may dispatch a rebuild. Env overrides the file. */
export function turnoutAutoEnabled(env, file) {
  const override = env && env.K26_TURNOUT_AUTO;
  if (override === "0" || override === "false") return false;
  if (override === "1" || override === "true") return true;
  return Boolean(file && file.turnout_auto === true);
}

export function decideTurnout({ acceptedSha256, next, auto }) {
  if (!next || !next.sha256) return { action: "reject", reason: "unreadable file" };
  if (!auto) return { action: "hold", reason: "turnout auto off" };
  if (acceptedSha256 && acceptedSha256 === next.sha256) return { action: "skip", reason: "same file" };
  return { action: "dispatch", reason: acceptedSha256 ? "new turnout snapshot" : "first turnout snapshot" };
}

// The CEC published K21-K24 in ISO-8859-8; windows-1255 decodes that Hebrew too.
function decodeText(bytes) {
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return new TextDecoder("windows-1255").decode(bytes);
  }
}

/** Shallow feed inspection: { rowCount, asOf } or null.
 * rowCount counts data rows for CSV/JSON feeds; XML feeds report the
 * number of repeated row elements. This intentionally does NOT parse
 * turnout values -- the CI-side generator is the real parser. */
export function inspectTurnout(bytes, headers = new Headers()) {
  const text = decodeText(bytes).replace(/^\uFEFF/, "");
  const trimmed = text.trim();
  if (!trimmed) return null;
  if (/^<!doctype html|^<html[\s>]/i.test(trimmed)) return null;
  if (trimmed.startsWith("{")) {
    let data;
    try { data = JSON.parse(trimmed); } catch { return null; }
    if (Array.isArray(data.rows) && Array.isArray(data.columns)) {
      return { rowCount: data.rows.length, asOf: typeof data.as_of === "string" ? data.as_of : null };
    }
    if (Array.isArray(data)) return { rowCount: data.length, asOf: null };
    return null;
  }
  if (trimmed.startsWith("<")) {
    // XML: count the most-repeated child element of the root.
    const tags = [...trimmed.matchAll(/<([A-Za-z_][\w.-]*)[\s>]/g)].map((m) => m[1]);
    if (tags.length < 3) return null;
    const counts = {};
    for (const t of tags.slice(1)) counts[t] = (counts[t] || 0) + 1;
    const rowCount = Math.max(0, ...Object.values(counts));
    return rowCount >= 2 ? { rowCount, asOf: null } : null;
  }
  const lines = text.split(/\r?\n/).filter((line) => line.trim() !== "");
  if (lines.length < 2) return null;
  // A turnout feed must carry a ballot column or a turnout/voters column;
  // anything else is not the feed we are looking for.
  const header = lines[0];
  if (!/(קלפי|ballot|אחוז|turnout|מצביעים|voters)/i.test(header)) return null;
  return { rowCount: lines.length - 1, asOf: headers.get("last-modified") };
}
