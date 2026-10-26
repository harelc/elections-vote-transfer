import assert from "node:assert/strict";
import test from "node:test";
import { autoEnabled, decide, pollGate, publishKind } from "./decide.mjs";
import { inspect, poll } from "../../functions/k26-poll.mjs";

const fileOff = { auto: false, roster: 12018 };
const fileOn = { auto: true, roster: 12018 };

test("the committed switch defaults to off", () => {
  assert.equal(autoEnabled({}, fileOff), false);
  assert.equal(autoEnabled({}, fileOn), true);
});

test("K26_AUTO overrides the file without a deploy", () => {
  assert.equal(autoEnabled({ K26_AUTO: "0" }, fileOn), false);
  assert.equal(autoEnabled({ K26_AUTO: "false" }, fileOn), false);
  assert.equal(autoEnabled({ K26_AUTO: "1" }, fileOff), true);
  assert.equal(autoEnabled({ K26_AUTO: "true" }, fileOff), true);
});

test("auto off holds a larger file", () => {
  const result = decide({
    previous: { accepted: { sha256: "a", ballotCount: 100 } },
    next: { sha256: "b", ballotCount: 200 },
    now: 0,
    auto: false,
    allowShrink: false,
  });
  assert.deepEqual(result, { action: "hold", reason: "auto off" });
});

test("a larger file dispatches", () => {
  const result = decide({
    previous: { accepted: { sha256: "a", ballotCount: 100 } },
    next: { sha256: "b", ballotCount: 200 },
    now: 0,
    auto: true,
    allowShrink: false,
  });
  assert.equal(result.action, "dispatch");
  assert.equal(result.reason, "more ballots");
});

test("the same bytes do not rebuild", () => {
  const result = decide({
    previous: { accepted: { sha256: "a", ballotCount: 100 } },
    next: { sha256: "a", ballotCount: 100 },
    now: 0,
    auto: true,
    allowShrink: false,
  });
  assert.equal(result.action, "skip");
});

test("a correction with the same count dispatches", () => {
  const result = decide({
    previous: { accepted: { sha256: "a", ballotCount: 100 } },
    next: { sha256: "b", ballotCount: 100 },
    now: 0,
    auto: true,
    allowShrink: false,
  });
  assert.equal(result.reason, "newer file");
});

test("a smaller file is rejected unless shrink is allowed", () => {
  const previous = { accepted: { sha256: "a", ballotCount: 100 } };
  const next = { sha256: "b", ballotCount: 90 };
  assert.equal(decide({ previous, next, now: 0, auto: true, allowShrink: false }).action, "reject");
  assert.equal(decide({ previous, next, now: 0, auto: true, allowShrink: true }).action, "dispatch");
});

test("an in-flight rebuild waits, unless a larger file arrives", () => {
  const now = Date.parse("2026-10-27T22:00:00Z");
  const previous = {
    accepted: { sha256: "a", ballotCount: 100 },
    pending: { sha256: "b", ballotCount: 150, dispatchedAt: new Date(now - 60_000).toISOString() },
  };
  assert.equal(
    decide({ previous, next: { sha256: "b", ballotCount: 150 }, now, auto: true, allowShrink: false }).action,
    "skip",
  );
  assert.equal(
    decide({ previous, next: { sha256: "c", ballotCount: 400 }, now, auto: true, allowShrink: false }).reason,
    "more ballots than the rebuild in flight",
  );
});

test("official only at the roster or an explicit final flag", () => {
  assert.equal(publishKind(4820, 12018, false), "partial");
  assert.equal(publishKind(12018, 12018, false), "official");
  assert.equal(publishKind(4820, 12018, true), "official");
});

test("a CEC csv counts ballot rows", () => {
  const body = new TextEncoder().encode("\uFEFFסמל ועדה,קלפי,כשרים,מחל\n1,1,10,6\n1,2,8,3\n");
  const found = inspect(body);
  assert.equal(found.ballotCount, 2);
  assert.equal(found.final, false);
});

test("a windows-1255 CEC csv counts ballot rows", () => {
  const ascii = (s) => [...s].map((c) => c.charCodeAt(0));
  const kalpi = [0xf7, 0xec, 0xf4, 0xe9];
  const body = Uint8Array.from([...kalpi, ...ascii(",x\n1,2\n3,4\n5,6\n")]);
  assert.equal(inspect(body).ballotCount, 3);
});

test("columns and rows json is accepted", () => {
  const body = new TextEncoder().encode(JSON.stringify({
    as_of: "2026-10-27T22:00:00+03:00",
    final: false,
    columns: ["קלפי", "כשרים", "מחל"],
    rows: [["1", 10, 4], ["2", 8, 1]],
  }));
  const found = inspect(body);
  assert.equal(found.ballotCount, 2);
  assert.equal(found.asOf, "2026-10-27T22:00:00+03:00");
});

test("an html page is not a count", () => {
  assert.equal(inspect(new TextEncoder().encode("<html></html>")), null);
});

const windowFile = {
  poll: true,
  poll_start: "2026-10-27T21:00",
  poll_end: "2026-10-31T23:59",
  timezone: "Asia/Jerusalem",
};

test("polling is closed before 21:00 on 27 Oct 2026 Israel time", () => {
  const gate = pollGate({}, windowFile, new Date("2026-10-27T18:59:00Z"));
  assert.equal(gate.open, false);
  assert.equal(gate.reason, "outside the polling window");
});

test("polling is open from 21:00 on 27 Oct through 23:59 on 31 Oct", () => {
  assert.equal(pollGate({}, windowFile, new Date("2026-10-27T19:00:00Z")).open, true);
  assert.equal(pollGate({}, windowFile, new Date("2026-10-31T21:59:00Z")).open, true);
  assert.equal(pollGate({}, windowFile, new Date("2026-10-31T22:00:00Z")).open, false);
});

test("K26_POLL=0 stops fetching inside the window", () => {
  const gate = pollGate({ K26_POLL: "0" }, windowFile, new Date("2026-10-27T19:00:00Z"));
  assert.equal(gate.reason, "polling stopped");
});

test("a roster-prefilled file with nothing counted does not dispatch", async () => {
  const body = "\uFEFFסמל ועדה,קלפי,בזב,מצביעים,כשרים,מחל\n1,1,500,0,0,0\n1,2,500,0,0,0\n";
  const stub = async () => new Response(body, { status: 200 });
  const result = await poll({}, new Date("2026-10-27T19:00:00Z"), stub);
  assert.equal(result.action, "reject");
  assert.equal(result.reason, "no counted ballots yet");
});

test("uncounted roster rows do not inflate the ballot count", () => {
  const body = new TextEncoder().encode(
    "\uFEFFסמל ועדה,קלפי,בזב,מצביעים,כשרים,מחל\n1,1,500,120,118,40\n1,2,500,0,0,0\n1,3,500,90,88,30\n");
  assert.equal(inspect(body).ballotCount, 2);
});

test("today does not fetch the results URL", async () => {
  const result = await poll({ K26_RESULTS_URL: "https://example.invalid/count" });
  assert.equal(result.reason, "outside the polling window");
});
