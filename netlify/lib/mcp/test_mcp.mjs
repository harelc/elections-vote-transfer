import assert from "node:assert/strict";
import {
  ballotNeighbors,
  officialResults,
  partyNationalHistory,
  partyStrongholds,
  sankey,
  settlementEmbedding,
  settlementPartyHistory,
  settlementResults,
  transferFlows,
} from "./query.mjs";
import handler from "../../functions/mcp.mjs";

const likud = officialResults(25).parties.find((party) => party.name === "הליכוד");
assert.equal(likud.seats, 32);

const telAviv = settlementResults("Tel Aviv", 25);
assert.equal(telAviv.name, "תל אביב יפו");
assert.ok(telAviv.parties.length > 0);
assert.equal(telAviv.parties.some((party) => party.share_pct === 0), false);

const strongholds = partyStrongholds("Likud", 25, 5, 500);
assert.equal(strongholds.party, "הליכוד");
assert.equal(strongholds.settlements.length, 5);
assert.ok(strongholds.settlements.every((row) => row.voters >= 500));
assert.ok(strongholds.settlements[0].share_pct >= strongholds.settlements[1].share_pct);

const simulated = officialResults(26);
assert.equal(simulated.simulated, true);
assert.match(simulated.note, /SIMULATED/);

const diagram = sankey(24, 25);
assert.ok(diagram.r_squared > 0.5);
const likudFlow = diagram.parties.find((party) => party.source === "הליכוד");
assert.equal(likudFlow.top_destinations[0].target, "הליכוד");

const flows = transferFlows({ fromElection: 21, toElection: 22, source: "Likud", target: "ש״ס" });
assert.equal(flows.flows.length, 1);
assert.equal(flows.flows[0].percentage, 5.6);
assert.deepEqual(flows.flows[0].percentage_ci, [5.1, 5.8]);

const missing = sankey(16, 25);
assert.ok(missing.error);
assert.ok(missing.available.includes("24_to_25"));

const cloud = settlementEmbedding("תל אביב יפו", 25, "umap", 5);
assert.equal(cloud.space, "umap");
assert.equal(cloud.nearest_settlements.length, 5);
assert.ok(cloud.spread > 0);

const ballotId = "1";
const neighbors = ballotNeighbors("תל אביב יפו", ballotId, 25, "tsne", 5);
assert.equal(neighbors.ballot.ballot, ballotId);
assert.equal(neighbors.neighbors.length, 5);
assert.ok(neighbors.neighbors.every((row, index, list) => index === 0 || row.distance >= list[index - 1].distance));

const history = settlementPartyHistory("הליכוד", "ראש פינה");
assert.equal(history.strongest.election, 23);
assert.equal(history.strongest.share_pct, 27.4);
const national = partyNationalHistory("Likud");
assert.equal(national.series.find((row) => row.election === 25).seats, 32);

const tooMany = partyStrongholds("Likud", 25, 100, 500);
assert.equal(tooMany.settlements.length, 20);

process.env.MCP_TRAFFIC_MEMORY = "1";

async function rpc(method, params, id = 1) {
  const response = await handler(new Request("http://localhost/mcp", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "application/json, text/event-stream",
    },
    body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
  }));
  const body = await response.json();
  assert.equal(response.status, 200, JSON.stringify(body));
  return body;
}

const listed = await rpc("tools/list", {});
const names = listed.result.tools.map((tool) => tool.name);
for (const name of ["sankey", "ballot_neighbors", "settlement_embedding", "settlement_results"]) {
  assert.ok(names.includes(name), name);
}

const called = await rpc("tools/call", {
  name: "settlement_embedding",
  arguments: { name: "Tel Aviv", election: "25", space: "tsne", limit: 3 },
});
const payload = JSON.parse(called.result.content[0].text);
assert.equal(payload.settlement, "תל אביב יפו");
assert.equal(payload.nearest_settlements.length, 3);

const nearby = await rpc("tools/call", {
  name: "ballot_neighbors",
  arguments: { settlement: "תל אביב יפו", ballot: 1, election: 25, space: "umap", limit: 3 },
}, 2);
const nearbyPayload = JSON.parse(nearby.result.content[0].text);
assert.equal(nearbyPayload.space, "umap");
assert.equal(nearbyPayload.neighbors.length, 3);

const rejected = await handler(new Request("http://localhost/mcp", { method: "GET" }));
assert.equal(rejected.status, 405);

process.env.MCP_LOG_TOKEN = "test-token";
const { admit, resetTrafficForTests, summarizeQuery } = await import("./traffic.mjs");
const summary = summarizeQuery(JSON.stringify({
  jsonrpc: "2.0",
  id: 7,
  method: "tools/call",
  params: { name: "transfer_flows", arguments: { source: "כחול לבן", target: "יש עתיד" } },
}));
assert.equal(summary[0].tool, "transfer_flows");
assert.equal(summary[0].arguments.source, "כחול לבן");

resetTrafficForTests();
process.env.MCP_DAILY_LIMIT = "10";
process.env.MCP_IP_DAILY_LIMIT = "300";
process.env.MCP_PER_MINUTE = "20";
await rpc("tools/call", {
  name: "transfer_flows",
  arguments: { from_election: 23, to_election: 24, source: "כחול לבן", target: "יש עתיד" },
}, 9);

const logHandler = (await import("../../functions/mcp-log.mjs")).default;
const hidden = await logHandler(new Request("http://localhost/mcp-log"));
assert.equal(hidden.status, 401);
const opened = await logHandler(new Request("http://localhost/mcp-log", {
  headers: { authorization: "Bearer test-token" },
}));
assert.equal(opened.status, 200);
const logBody = await opened.json();
assert.equal(logBody.queries[0].queries[0].tool, "transfer_flows");
assert.equal(logBody.queries[0].queries[0].arguments.target, "יש עתיד");

resetTrafficForTests();
process.env.MCP_DAILY_LIMIT = "2";
assert.equal((await admit("203.0.113.5")).ok, true);
assert.equal((await admit("203.0.113.5")).ok, true);
const blocked = await admit("203.0.113.9");
assert.equal(blocked.ok, false);
assert.equal(blocked.reason, "daily");
delete process.env.MCP_DAILY_LIMIT;
resetTrafficForTests();

console.log("mcp tests ok");
