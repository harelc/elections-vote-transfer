/** Local minute in the polling timezone, YYYY-MM-DDTHH:mm. */
export function localStamp(now, timeZone) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(now);
  const get = (type) => parts.find((part) => part.type === type).value;
  const hour = get("hour") === "24" ? "00" : get("hour");
  return `${get("year")}-${get("month")}-${get("day")}T${hour}:${get("minute")}`;
}

/** Inclusive window. Stamps in the control file are local times, not UTC. */
export function withinPollWindow(now, file) {
  const timeZone = (file && file.timezone) || "Asia/Jerusalem";
  const start = file && file.poll_start;
  const end = file && file.poll_end;
  if (!start || !end) return true;
  const stamp = localStamp(now, timeZone);
  return stamp >= start.slice(0, 16) && stamp <= end.slice(0, 16);
}

/**
 * Polling runs only inside the window. K26_POLL=0 or poll:false stops it early.
 * K26_POLL=1 does not extend past the window.
 */
export function pollGate(env, file, now) {
  const override = env && env.K26_POLL;
  if (override === "0" || override === "false") return { open: false, reason: "polling stopped" };
  if (file && file.poll === false && override !== "1" && override !== "true") {
    return { open: false, reason: "polling stopped" };
  }
  if (!withinPollWindow(now, file)) return { open: false, reason: "outside the polling window" };
  return { open: true };
}

/** Whether the poller may dispatch a rebuild. Env overrides the committed file. */
export function autoEnabled(env, file) {
  const override = env && env.K26_AUTO;
  if (override === "0" || override === "false") return false;
  if (override === "1" || override === "true") return true;
  return Boolean(file && file.auto === true);
}

export function publishKind(ballotCount, roster, finalFlag) {
  void ballotCount;
  void roster;
  if (finalFlag) return "official";
  return "partial";
}

const FLIGHT_MS = 45 * 60 * 1000;

/**
 * previous: last accepted snapshot, plus an optional in-flight dispatch.
 * next: the file just fetched.
 * Returns action dispatch | hold | skip | reject.
 */
export function decide({ previous, next, now, auto, allowShrink }) {
  if (!auto) return { action: "hold", reason: "auto off" };
  if (!next || !next.sha256 || !Number.isFinite(next.ballotCount)) {
    return { action: "reject", reason: "unreadable file" };
  }
  const accepted = previous && previous.accepted;
  if (accepted && accepted.sha256 === next.sha256) {
    return { action: "skip", reason: "same file" };
  }
  if (accepted && next.ballotCount < accepted.ballotCount && !allowShrink) {
    return { action: "reject", reason: "fewer ballots" };
  }

  const pending = previous && previous.pending;
  const pendingAge = pending ? now - Date.parse(pending.dispatchedAt) : Infinity;
  if (pending && Number.isFinite(pendingAge) && pendingAge < FLIGHT_MS) {
    if (next.ballotCount > pending.ballotCount) {
      return { action: "dispatch", reason: "more ballots than the rebuild in flight" };
    }
    return { action: "skip", reason: "rebuild in progress" };
  }

  if (!accepted) return { action: "dispatch", reason: "first file" };
  if (next.ballotCount > accepted.ballotCount) {
    return { action: "dispatch", reason: "more ballots" };
  }
  return { action: "dispatch", reason: "newer file" };
}
