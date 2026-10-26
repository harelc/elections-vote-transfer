import assert from "node:assert/strict";
import test from "node:test";
import { decideTurnout, inspectTurnout, turnoutAutoEnabled, turnoutGate } from "./turnout.mjs";
import { pollTurnout } from "../../functions/k26-turnout-poll.mjs";

const dayFile = {
  turnout_poll: true,
  turnout_auto: false,
  turnout_poll_start: "2026-10-27T07:00",
  turnout_poll_end: "2026-10-27T22:00",
  timezone: "Asia/Jerusalem",
};

test("turnout window is election daytime in Israel", () => {
  assert.equal(turnoutGate({}, dayFile, new Date("2026-10-27T04:59:00Z")).open, false); // 06:59 IST
  assert.equal(turnoutGate({}, dayFile, new Date("2026-10-27T05:00:00Z")).open, true); // 07:00 IST
  assert.equal(turnoutGate({}, dayFile, new Date("2026-10-27T19:59:00Z")).open, true); // 21:59 IST
  assert.equal(turnoutGate({}, dayFile, new Date("2026-10-27T20:01:00Z")).open, false); // 22:01 IST
  assert.equal(turnoutGate({ K26_TURNOUT_POLL: "0" }, dayFile, new Date("2026-10-27T10:00:00Z")).reason, "turnout polling stopped");
});

test("turnout chicken bit and env override", () => {
  assert.equal(turnoutAutoEnabled({}, dayFile), false);
  assert.equal(turnoutAutoEnabled({ K26_TURNOUT_AUTO: "1" }, dayFile), true);
  assert.equal(turnoutAutoEnabled({ K26_TURNOUT_AUTO: "0" }, { ...dayFile, turnout_auto: true }), false);
});

test("new hash dispatches, same hash skips, auto off holds", () => {
  assert.equal(decideTurnout({ acceptedSha256: "a", next: { sha256: "b" }, auto: true }).action, "dispatch");
  assert.equal(decideTurnout({ acceptedSha256: "a", next: { sha256: "a" }, auto: true }).action, "skip");
  assert.equal(decideTurnout({ acceptedSha256: null, next: { sha256: "b" }, auto: false }).action, "hold");
  assert.equal(decideTurnout({ acceptedSha256: null, next: null, auto: true }).action, "reject");
});

test("a CEC-style turnout csv is recognised", () => {
  const body = new TextEncoder().encode("\uFEFFסמל ישוב,קלפי,בזב,מצביעים\n3000,1,600,210\n3000,2,610,240\n");
  const found = inspectTurnout(body);
  assert.equal(found.rowCount, 2);
});

test("columns/rows json and generic xml are recognised", () => {
  const json = new TextEncoder().encode(JSON.stringify({ as_of: "2026-10-27T12:00:00+02:00", columns: ["קלפי", "מצביעים"], rows: [["1", 5], ["2", 7]] }));
  assert.equal(inspectTurnout(json).rowCount, 2);
  const xml = new TextEncoder().encode(`<?xml version="1.0"?><feed><row ballot="1" voters="5"/><row ballot="2" voters="7"/><row ballot="3" voters="9"/></feed>`);
  assert.equal(inspectTurnout(xml).rowCount, 3);
});

test("an html page or unrelated csv is not a turnout feed", () => {
  assert.equal(inspectTurnout(new TextEncoder().encode("<html><body>soon</body></html>")), null);
  assert.equal(inspectTurnout(new TextEncoder().encode("a,b\n1,2\n")), null);
});

test("a missing turnout URL does not dispatch", async () => {
  const result = await pollTurnout({}, new Date("2026-10-27T10:00:00Z"));
  assert.equal(result.action, "skip");
  assert.equal(result.reason, "K26_TURNOUT_URL unset");
});

test("outside the turnout window nothing is fetched", async () => {
  let fetched = false;
  const result = await pollTurnout(
    { K26_TURNOUT_URL: "https://example.invalid/turnout" },
    new Date("2026-10-26T10:00:00Z"),
    async () => { fetched = true; throw new Error("must not fetch"); },
  );
  assert.equal(result.reason, "outside the turnout polling window");
  assert.equal(fetched, false);
});
