import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DATA_DIRS = [
  join(dirname(fileURLToPath(import.meta.url)), "mcp-data"),
  join(process.cwd(), "netlify/lib/mcp/mcp-data"),
];

const cache = new Map();

function dataDir() {
  const found = DATA_DIRS.find((dir) => existsSync(dir));
  if (!found) {
    throw new Error(`MCP data directory not found. Looked in ${DATA_DIRS.join(", ")}`);
  }
  return found;
}

function load(name) {
  if (!cache.has(name)) {
    cache.set(name, JSON.parse(readFileSync(join(dataDir(), name), "utf8")));
  }
  return cache.get(name);
}

function meta() {
  return load("meta.json");
}

export function normalize(text) {
  return String(text)
    .replace(/[-–'׳"״()]/g, "")
    .replace(/יי/g, "י")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function clampLimit(value, fallback = 12) {
  const number = value == null ? fallback : Number(value);
  if (!Number.isInteger(number)) return { error: "limit must be an integer." };
  return Math.min(20, Math.max(1, number));
}

function electionKey(election) {
  const id = Number(election);
  if (!Number.isInteger(id) || id < 16 || id > 26) {
    return { error: "Election must be an integer from 16 to 26." };
  }
  return String(id);
}

function k26Note(electionId) {
  if (electionId !== "26") return undefined;
  return meta().notes["26"];
}

function k26Status() {
  return meta().k26 || { kind: "simulated" };
}

/** Wording for election 26 that follows site/data/k26_status.json, as baked into meta.json. */
export function k26Caveat(status = k26Status()) {
  if (status.kind === "official") {
    return {
      kind: "official",
      scope: "elections 16–26",
      instruction: "Election 26 is the official Central Elections Committee count.",
      sentence: "Election 26 is the official count.",
      short: "26 is the official count.",
    };
  }
  if (status.kind === "partial") {
    const coverage = status.ballots != null && status.ballots_total
      ? `${status.ballots} of ${status.ballots_total} ballots`
      : "not all ballots";
    const when = status.as_of ? ` as of ${status.as_of}` : "";
    return {
      kind: "partial",
      scope: "elections 16–25, plus a partial count of election 26",
      instruction: `Election 26 is a partial Central Elections Committee count${when} (${coverage}). Say so whenever you cite it; totals and seats can still change.`,
      sentence: "Election 26 is a partial count and can still change.",
      short: "26 is a partial count.",
    };
  }
  return {
    kind: "simulated",
    scope: "elections 16–25, plus simulated election 26",
    instruction: "Election 26 is not a real result. Say so whenever you cite it.",
    sentence: "Election 26 is simulated.",
    short: "26 is simulated.",
  };
}

function k26Fields(...ids) {
  if (!ids.includes("26")) return { simulated: false };
  const { kind } = k26Status();
  if (kind !== "partial" && kind !== "official") return { simulated: true };
  return { simulated: false, count_status: kind, count_note: meta().notes["26"] };
}

function partiesFor(electionId) {
  return meta().parties[electionId] || [];
}

function partyFields(party) {
  return [party.name, party.symbol, party.name_en].filter(Boolean);
}

function matchOne(query, items, fieldsOf) {
  const needle = normalize(query);
  if (!needle) return { error: "A name is required." };
  const exact = [];
  const partial = [];
  for (const item of items) {
    const fields = fieldsOf(item).map(normalize).filter(Boolean);
    if (fields.some((field) => field === needle)) exact.push(item);
    else if (needle.length >= 2 && fields.some((field) => field.includes(needle))) partial.push(item);
  }
  const hits = exact.length ? exact : partial;
  if (hits.length === 1) return { match: hits[0] };
  if (hits.length === 0) return { error: "No match.", candidates: items.slice(0, 12).map(fieldsOf) };
  return {
    error: "Several matches. Ask again with one of these.",
    candidates: hits.slice(0, 8).map(fieldsOf),
  };
}

function resolveParty(electionId, query) {
  const found = matchOne(query, partiesFor(electionId), partyFields);
  if (found.error) {
    return {
      error: found.error,
      candidates: (found.candidates || []).map((fields) => ({
        name: fields[0],
        symbol: fields[1] || null,
        name_en: fields[2] || null,
      })),
    };
  }
  return { party: found.match };
}

function namesEn() {
  return load("names_en.json");
}

let englishByName;

function englishFor(hebrew) {
  if (!englishByName) {
    englishByName = new Map();
    for (const [name, english] of Object.entries(namesEn())) {
      const key = normalize(name);
      if (!englishByName.has(key)) englishByName.set(key, english);
    }
  }
  return englishByName.get(normalize(hebrew)) || null;
}

function settlements(electionId) {
  return load(`settlements_${electionId}.json`);
}

function settlementRecord(electionId, row) {
  return {
    name: row.n,
    name_en: englishFor(row.n),
    voters: row.v,
    eligible: row.e,
    turnout: row.t,
  };
}

function resolveSettlement(electionId, query) {
  const rows = settlements(electionId);
  const found = matchOne(query, rows, (row) => [row.n, englishFor(row.n)].filter(Boolean));
  if (found.error) {
    return {
      error: found.error,
      candidates: (found.candidates || []).map((fields) => fields[0]),
    };
  }
  return { settlement: found.match };
}

function sharesOf(row) {
  return Object.entries(row.p)
    .map(([name, share_pct]) => ({ name, share_pct }))
    .sort((a, b) => b.share_pct - a.share_pct);
}

export function listElections() {
  return {
    elections: meta().elections,
    k26: meta().k26,
    scope: meta().notes.scope,
  };
}

export function officialResults(election) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const rows = meta().official[electionId];
  if (!rows) return { error: `No official results stored for election ${electionId}.` };
  return {
    election: Number(electionId),
    ...k26Fields(electionId),
    note: k26Note(electionId),
    parties: rows,
  };
}

export function findSettlement(query, election = 25) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const found = resolveSettlement(electionId, query);
  if (found.error) return { election: Number(electionId), ...found };
  return {
    election: Number(electionId),
    ...settlementRecord(electionId, found.settlement),
    winning_party: found.settlement.w,
  };
}

export function settlementResults(name, election = 25) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const found = resolveSettlement(electionId, name);
  if (found.error) return { election: Number(electionId), ...found };
  const row = found.settlement;
  return {
    election: Number(electionId),
    ...k26Fields(electionId),
    note: k26Note(electionId) || meta().notes.scope,
    ...settlementRecord(electionId, row),
    winning_party: row.w,
    socioeconomic_cluster: row.c ?? null,
    parties: sharesOf(row),
  };
}

export function partyStrongholds(party, election = 25, limit = 10, minVoters = 500) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const capped = clampLimit(limit, 10);
  if (capped.error) return capped;
  const resolved = resolveParty(electionId, party);
  if (resolved.error) return { election: Number(electionId), ...resolved };
  const name = resolved.party.name;
  const floor = minVoters == null ? 500 : Number(minVoters);
  if (!Number.isFinite(floor) || floor < 0) return { error: "min_voters must be a non-negative number." };
  const rows = settlements(electionId)
    .filter((row) => row.v >= floor && row.p[name] != null)
    .map((row) => ({
      ...settlementRecord(electionId, row),
      share_pct: row.p[name],
      socioeconomic_cluster: row.c ?? null,
    }))
    .sort((a, b) => b.share_pct - a.share_pct || b.voters - a.voters)
    .slice(0, capped);
  return {
    election: Number(electionId),
    ...k26Fields(electionId),
    note: k26Note(electionId),
    party: name,
    party_en: resolved.party.name_en,
    min_voters: floor,
    settlements: rows,
  };
}

export function filterSettlements({
  election = 25,
  party,
  minSupport,
  maxSupport,
  minVoters = 0,
  sort = "voters",
  limit = 12,
} = {}) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const capped = clampLimit(limit, 12);
  if (capped.error) return capped;
  const needsParty = party || minSupport != null || maxSupport != null || sort === "support";
  let partyName = null;
  let partyEn = null;
  if (needsParty) {
    if (!party) return { error: "A party is required when filtering or sorting by support." };
    const resolved = resolveParty(electionId, party);
    if (resolved.error) return { election: Number(electionId), ...resolved };
    partyName = resolved.party.name;
    partyEn = resolved.party.name_en;
  }
  const floor = minVoters == null ? 0 : Number(minVoters);
  if (!Number.isFinite(floor) || floor < 0) return { error: "min_voters must be a non-negative number." };
  let rows = settlements(electionId).filter((row) => row.v >= floor);
  if (partyName) {
    rows = rows.filter((row) => {
      const share = row.p[partyName] || 0;
      if (minSupport != null && share < minSupport) return false;
      if (maxSupport != null && share > maxSupport) return false;
      return minSupport != null || maxSupport != null ? true : row.p[partyName] != null;
    });
  }
  const shaped = rows.map((row) => ({
    ...settlementRecord(electionId, row),
    winning_party: row.w,
    share_pct: partyName ? row.p[partyName] || 0 : undefined,
  }));
  const sorters = {
    voters: (a, b) => b.voters - a.voters,
    turnout: (a, b) => b.turnout - a.turnout,
    support: (a, b) => b.share_pct - a.share_pct || b.voters - a.voters,
  };
  if (!sorters[sort]) return { error: "sort must be voters, turnout, or support." };
  shaped.sort(sorters[sort]);
  return {
    election: Number(electionId),
    ...k26Fields(electionId),
    note: k26Note(electionId) || meta().notes.scope,
    party: partyName,
    party_en: partyEn,
    sort,
    returned: Math.min(capped, shaped.length),
    matched: shaped.length,
    settlements: shaped.slice(0, capped),
  };
}

export function transferFlows({
  fromElection,
  toElection,
  source,
  target,
  includeAbstention = false,
  limit = 15,
} = {}) {
  const fromId = electionKey(fromElection);
  if (fromId.error) return fromId;
  const toId = electionKey(toElection);
  if (toId.error) return toId;
  const capped = clampLimit(limit, 15);
  if (capped.error) return capped;
  const found = transition(fromId, toId);
  if (found.error) return found;
  const table = found.table;
  const flowKey = includeAbstention ? "abstention_flows" : "flows";
  const allFlows = table[flowKey] || [];
  let sourceName = null;
  let targetName = null;
  if (source) {
    const resolved = resolveFlowParty(fromId, source, allFlows);
    if (resolved.error) return { ...resolved, side: "source" };
    sourceName = resolved.party.name;
  }
  if (target) {
    const resolved = resolveFlowParty(toId, target, allFlows);
    if (resolved.error) return { ...resolved, side: "target" };
    targetName = resolved.party.name;
  }
  let flows = allFlows;
  if (sourceName) flows = flows.filter((flow) => flow.source === sourceName);
  if (targetName) flows = flows.filter((flow) => flow.target === targetName);
  flows = [...flows].sort((a, b) => b.votes - a.votes).slice(0, capped);
  return {
    from: Number(fromId),
    to: Number(toId),
    ...k26Fields(fromId, toId),
    note: meta().notes.transfers,
    abstention_unreliable: includeAbstention ? Boolean(table.abstention_unreliable) : undefined,
    r_squared: table.r_squared,
    r_squared_ci: table.r_squared_ci || null,
    common_precincts: table.common_precincts,
    source: sourceName,
    target: targetName,
    flows,
  };
}

function transition(fromId, toId) {
  const key = `${fromId}_to_${toId}`;
  const table = load("transfers.json")[key];
  if (!table) {
    return {
      error: `No published Sankey for ${fromId} → ${toId}. Only consecutive elections exist; do not chain them.`,
      available: Object.keys(load("transfers.json")),
    };
  }
  return { key, table };
}

function resolveFlowParty(electionId, query, flows) {
  if (normalize(query) === normalize("לא הצביעו") || ["abstain", "did not vote"].includes(normalize(query))) {
    return { party: { name: "לא הצביעו", name_en: "Did not vote" } };
  }
  const resolved = resolveParty(electionId, query);
  if (!resolved.error) return resolved;
  const names = [...new Set(flows.flatMap((flow) => [flow.source, flow.target]))];
  const found = matchOne(query, names.map((name) => ({ name })), (item) => [item.name]);
  if (found.match) return { party: { name: found.match.name, name_en: null } };
  return resolved;
}

export function sankey(fromElection, toElection, includeAbstention = false) {
  const fromId = electionKey(fromElection);
  if (fromId.error) return fromId;
  const toId = electionKey(toElection);
  if (toId.error) return toId;
  const found = transition(fromId, toId);
  if (found.error) return found;
  const flows = found.table[includeAbstention ? "abstention_flows" : "flows"] || [];
  const bySource = new Map();
  for (const flow of flows) {
    if (!bySource.has(flow.source)) bySource.set(flow.source, []);
    bySource.get(flow.source).push(flow);
  }
  const parties = [...bySource.entries()].map(([source, outgoing]) => {
    const top = [...outgoing].sort((a, b) => b.votes - a.votes).slice(0, 3);
    return {
      source,
      top_destinations: top.map((flow) => ({
        target: flow.target,
        votes: flow.votes,
        percentage: flow.percentage,
        percentage_ci: flow.percentage_ci || null,
      })),
    };
  });
  return {
    from: Number(fromId),
    to: Number(toId),
    ...k26Fields(fromId, toId),
    note: meta().notes.transfers,
    abstention_unreliable: includeAbstention ? Boolean(found.table.abstention_unreliable) : undefined,
    r_squared: found.table.r_squared,
    r_squared_ci: found.table.r_squared_ci || null,
    common_precincts: found.table.common_precincts,
    parties,
  };
}

const EMBEDDING_NOTE = {
  tsne: "t-SNE places ballots with similar party mixes near each other. Distance matters locally, not between far-apart clusters, and it is not geographic.",
  umap: "UMAP places ballots with similar party mixes near each other and keeps more of the global layout than t-SNE. It is not a geographic map.",
};

function embeddingSpace(space) {
  const name = space || "tsne";
  if (name !== "tsne" && name !== "umap") return { error: "space must be tsne or umap." };
  return name;
}

function embeddings(electionId) {
  return load(`embeddings_${electionId}.json`);
}

function point(row, space) {
  return space === "umap" ? [row.ux, row.uy] : [row.x, row.y];
}

function distance(a, b) {
  const dx = a[0] - b[0];
  const dy = a[1] - b[1];
  return Math.sqrt(dx * dx + dy * dy);
}

const centroidCache = new Map();

function centroids(electionId, space) {
  const key = `${electionId}:${space}`;
  if (centroidCache.has(key)) return centroidCache.get(key);
  const groups = new Map();
  for (const row of embeddings(electionId)) {
    const [x, y] = point(row, space);
    let group = groups.get(row.n);
    if (!group) {
      group = { name: row.n, sx: 0, sy: 0, weight: 0, ballots: 0, voters: 0 };
      groups.set(row.n, group);
    }
    const weight = row.v || 1;
    group.sx += x * weight;
    group.sy += y * weight;
    group.weight += weight;
    group.ballots += 1;
    group.voters += row.v || 0;
  }
  const list = [...groups.values()].map((group) => ({
    name: group.name,
    name_en: englishFor(group.name),
    x: group.sx / group.weight,
    y: group.sy / group.weight,
    ballots: group.ballots,
    voters: group.voters,
  }));
  centroidCache.set(key, list);
  return list;
}

function ballotView(row) {
  return {
    settlement: row.n,
    name_en: englishFor(row.n),
    ballot: row.b,
    voters: row.v,
    turnout: row.t,
    winning_party: row.w,
    winning_share_pct: row.ws,
    location: row.l || null,
  };
}

export function settlementEmbedding(name, election = 25, space = "tsne", limit = 8) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const which = embeddingSpace(space);
  if (which.error) return which;
  const capped = clampLimit(limit, 8);
  if (capped.error) return capped;
  const found = resolveSettlement(electionId, name);
  if (found.error) return { election: Number(electionId), ...found };
  const center = centroids(electionId, which).find((row) => row.name === found.settlement.n);
  const ballots = embeddings(electionId).filter((row) => row.n === found.settlement.n);
  let spread = 0;
  const weight = ballots.reduce((sum, row) => sum + (row.v || 1), 0);
  if (weight) {
    const mean = [center.x, center.y];
    const variance = ballots.reduce((sum, row) => {
      const d = distance(point(row, which), mean);
      return sum + (row.v || 1) * d * d;
    }, 0);
    spread = Math.sqrt(variance / weight);
  }
  const neighbors = centroids(electionId, which)
    .filter((row) => row.name !== center.name)
    .map((row) => ({
      name: row.name,
      name_en: row.name_en,
      voters: row.voters,
      ballots: row.ballots,
      distance: Math.round(distance([center.x, center.y], [row.x, row.y]) * 100) / 100,
    }))
    .sort((a, b) => a.distance - b.distance)
    .slice(0, capped);
  return {
    election: Number(electionId),
    ...k26Fields(electionId),
    space: which,
    note: EMBEDDING_NOTE[which],
    settlement: center.name,
    name_en: center.name_en,
    ballots: center.ballots,
    voters: center.voters,
    spread: Math.round(spread * 100) / 100,
    nearest_settlements: neighbors,
  };
}

export function ballotNeighbors(settlement, ballot, election = 25, space = "tsne", limit = 8, excludeSameSettlement = false) {
  const electionId = electionKey(election);
  if (electionId.error) return electionId;
  const which = embeddingSpace(space);
  if (which.error) return which;
  const capped = clampLimit(limit, 8);
  if (capped.error) return capped;
  const found = resolveSettlement(electionId, settlement);
  if (found.error) return { election: Number(electionId), ...found };
  const boxes = embeddings(electionId);
  const here = boxes.filter((row) => row.n === found.settlement.n);
  const wanted = String(ballot);
  const self = here.find((row) => row.b === wanted);
  if (!self) {
    return {
      error: `No ballot ${wanted} in ${found.settlement.n}.`,
      ballots: here.map((row) => row.b).slice(0, 20),
    };
  }
  const origin = point(self, which);
  const neighbors = boxes
    .filter((row) => row !== self && (!excludeSameSettlement || row.n !== self.n))
    .map((row) => ({
      ...ballotView(row),
      same_settlement: row.n === self.n,
      distance: distance(origin, point(row, which)),
    }))
    .sort((a, b) => a.distance - b.distance)
    .slice(0, capped)
    .map((row) => ({ ...row, distance: Math.round(row.distance * 100) / 100 }));
  return {
    election: Number(electionId),
    ...k26Fields(electionId),
    space: which,
    note: EMBEDDING_NOTE[which],
    ballot: ballotView(self),
    neighbors,
  };
}

function historyPeak(series, field) {
  const present = series.filter((row) => row[field] != null);
  if (!present.length) return null;
  return present.reduce((best, row) => (row[field] > best[field] ? row : best));
}

export function settlementPartyHistory(party, name) {
  if (!party || !name) return { error: "A party and a settlement are required." };
  let canonical = null;
  const series = [];
  for (let id = 16; id <= 26; id += 1) {
    const electionId = String(id);
    const rows = settlements(electionId);
    const settlement = canonical
      ? rows.find((row) => normalize(row.n) === normalize(canonical))
      : null;
    const found = settlement ? { settlement } : resolveSettlement(electionId, name);
    if (found.error) {
      series.push({
        election: id,
        ...k26Fields(electionId),
        share_pct: null,
        note: "This settlement name is not in this election.",
      });
      continue;
    }
    canonical = found.settlement.n;
    const resolved = resolveParty(electionId, party);
    if (resolved.error) {
      series.push({
        election: id,
        ...k26Fields(electionId),
        settlement: canonical,
        share_pct: null,
        note: "No list with this name. A joint list keeps its own name.",
      });
      continue;
    }
    const share = found.settlement.p[resolved.party.name];
    series.push({
      election: id,
      ...k26Fields(electionId),
      settlement: canonical,
      name_en: englishFor(canonical),
      party: resolved.party.name,
      party_en: resolved.party.name_en,
      share_pct: share == null ? 0 : share,
      voters: found.settlement.v,
      winning_party: found.settlement.w,
    });
  }
  const strongest = historyPeak(series, "share_pct");
  if (!canonical || !strongest) return { error: "No matching settlement.", series };
  return {
    settlement: canonical,
    name_en: englishFor(canonical),
    party: party,
    strongest: {
      election: strongest.election,
      share_pct: strongest.share_pct,
      simulated: strongest.simulated,
      party: strongest.party,
    },
    series,
  };
}

export function partyNationalHistory(party) {
  if (!party) return { error: "A party is required." };
  const series = [];
  for (let id = 16; id <= 26; id += 1) {
    const electionId = String(id);
    const rows = meta().official[electionId] || [];
    const resolved = resolveParty(electionId, party);
    let official = null;
    if (!resolved.error) {
      official = rows.find((row) => normalize(row.name) === normalize(resolved.party.name)) || null;
    }
    if (!official) {
      const found = matchOne(party, rows, (row) => [row.name]);
      if (found.match) official = found.match;
    }
    if (!official) {
      series.push({
        election: id,
        ...k26Fields(electionId),
        seats: null,
        votes: null,
        note: "No list with this name.",
      });
      continue;
    }
    series.push({
      election: id,
      ...k26Fields(electionId),
      party: official.name,
      party_en: resolved.party ? resolved.party.name_en : null,
      seats: official.seats,
      votes: official.votes,
    });
  }
  const strongest = historyPeak(series, "seats");
  if (!strongest) return { error: "No matching party.", series };
  return {
    party: strongest.party,
    note: `${k26Caveat().sentence} Seats are the published totals for that election, not a new calculation.`,
    strongest: {
      election: strongest.election,
      seats: strongest.seats,
      votes: strongest.votes,
      simulated: strongest.simulated,
    },
    series,
  };
}

export function settlementVolatility(name) {
  const found = resolveSettlement("25", name);
  const row = found.settlement
    || (() => {
      const metrics = load("volatility.json");
      const needle = normalize(name);
      const key = Object.keys(metrics).find((candidate) => normalize(candidate) === needle);
      return key ? { n: key } : null;
    })();
  if (!row) return found.error ? found : { error: "No match." };
  const metrics = load("volatility.json")[row.n];
  if (!metrics) return { error: `No volatility row for ${row.n}.`, name: row.n };
  return {
    name: row.n,
    name_en: englishFor(row.n),
    average: metrics.average,
    voters: metrics.voters,
    rank: metrics.rank,
    transitions: metrics.transitions,
    note: "Pedersen-style index of how much the settlement's party mix changed between elections. Higher means more change.",
  };
}
