#!/usr/bin/env python3
"""Build the trimmed tables the Netlify MCP function queries.

Reads site/data and party_config.py. Writes compact JSON under mcp-data/.
Settlement rows keep party shares and turnout, and drop ballot boxes, coordinates,
and zero shares. Re-run after regenerating map, transfer, or metrics files.

    python netlify/lib/mcp/build_mcp_data.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import party_config  # noqa: E402

DATA = ROOT / "site" / "data"
OUT = Path(__file__).resolve().parent / "mcp-data"
UNRELIABLE_ABSTENTION = {("16", "17"), ("17", "18")}


def normalize(text):
    for ch in "-–'׳\"״()":
        text = text.replace(ch, "")
    return " ".join(text.replace("יי", "י").split()).casefold()


def english_name(symbol, election, hebrew):
    info = party_config.get_party_info(symbol, str(election)) or {}
    if normalize(info.get("name") or "") != normalize(hebrew):
        return None
    name_en = info.get("name_en")
    return name_en or None


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB")


def load_k26_status():
    path = DATA / "k26_status.json"
    status = load_json(path) if path.exists() else {}
    kind = status.get("kind")
    return {
        "kind": kind if kind in ("simulated", "partial", "official") else "simulated",
        "as_of": status.get("as_of"),
        "ballots": status.get("ballots"),
        "ballots_total": status.get("ballots_total"),
    }


def k26_note(official, k26):
    if k26["kind"] == "official":
        return "Official count from the Central Elections Committee."
    if k26["kind"] == "partial":
        counted = k26["ballots"]
        total = k26["ballots_total"]
        coverage = f"{counted} of {total} ballots" if counted is not None and total else "an incomplete set of ballots"
        when = f" as of {k26['as_of']}" if k26["as_of"] else ""
        return (
            f"Partial count from the Central Elections Committee{when}, covering {coverage}. "
            "Totals, seats, and shares will change as more ballots are counted."
        )
    return official.get("_26_note") or official.get("26_note") or "Simulated scenario"


def build_elections(k26):
    elections = []
    for election_id, meta in party_config.ELECTIONS.items():
        elections.append(
            {
                "id": int(election_id),
                "name": meta["name"],
                "name_en": meta["name_en"],
                "date": meta["date"],
                "turnout_percent": meta.get("turnout_percent"),
                "eligible_voters": meta.get("eligible_voters"),
                "simulated": election_id == "26" and k26["kind"] == "simulated",
            }
        )
    elections.sort(key=lambda row: row["id"])
    return elections


def build_parties(map_data, election_id):
    parties = []
    for party in map_data["parties"]:
        parties.append(
            {
                "name": party["name"],
                "symbol": party.get("symbol"),
                "name_en": english_name(party.get("symbol"), election_id, party["name"]),
            }
        )
    return parties


def build_settlements(map_data):
    rows = []
    for settlement in map_data["settlements"]:
        shares = {}
        for name, share in settlement.get("proportions", {}).items():
            if not share:
                continue
            shares[name] = round(float(share), 1)
        row = {
            "n": settlement["name"],
            "v": settlement["voters"],
            "e": settlement["eligible"],
            "t": settlement["turnout"],
            "w": settlement.get("winningParty"),
            "p": shares,
        }
        if settlement.get("cluster") is not None:
            row["c"] = settlement["cluster"]
        rows.append(row)
    return rows


def slim_flows(transfer, intervals):
    rows = []
    for flow in transfer["transfers"]:
        row = {
            "source": flow["source"],
            "target": flow["target"],
            "votes": flow["votes"],
            "percentage": flow["percentage"],
        }
        interval = intervals.get(f"{flow['source']}\t{flow['target']}")
        if interval:
            row["percentage_ci"] = interval
        rows.append(row)
    return rows


def ci_block(ci_file, key, stats):
    block = (ci_file.get("transitions") or {}).get(key) or {}
    if "common_precincts" in block and (
        block["common_precincts"] != stats.get("common_precincts") or block.get("r_squared") != stats.get("r_squared")
    ):
        return None, {}
    return block.get("r2_ci"), block.get("cells") or {}


def build_transfers():
    ci_path = DATA / "transfer_ci.json"
    ci_file = load_json(ci_path) if ci_path.exists() else {"transitions": {}}
    pairs = {}
    for path in sorted(DATA.glob("transfer_*_to_*.json")):
        if path.name.endswith("_abstention.json"):
            continue
        # transfer_24_to_25.json
        stem = path.stem.replace("transfer_", "")
        from_id, to_id = stem.split("_to_")
        transfer = load_json(path)
        r2_ci, cells = ci_block(ci_file, f"{from_id}_to_{to_id}", transfer["stats"])
        abstention_path = path.with_name(f"{path.stem}_abstention.json")
        entry = {
            "from": int(from_id),
            "to": int(to_id),
            "r_squared": transfer["stats"].get("r_squared"),
            "r_squared_ci": r2_ci,
            "common_precincts": transfer["stats"].get("common_precincts"),
            "flows": slim_flows(transfer, cells),
        }
        if abstention_path.exists():
            abstention = load_json(abstention_path)
            _, abstention_cells = ci_block(ci_file, f"{from_id}_to_{to_id}_abstention", abstention["stats"])
            entry["abstention_flows"] = slim_flows(abstention, abstention_cells)
            entry["abstention_unreliable"] = (from_id, to_id) in UNRELIABLE_ABSTENTION
        pairs[f"{from_id}_to_{to_id}"] = entry
    return pairs


def build_volatility():
    metrics = load_json(DATA / "metrics.json")
    return metrics["settlement_pedersen"]


def build_embeddings(tsne):
    rows = []
    for station in tsne["stations"]:
        proportions = station.get("p") or {}
        winner, share = max(proportions.items(), key=lambda item: item[1]) if proportions else (None, None)
        row = {
            "n": station["n"],
            "b": str(station["b"]),
            "x": round(float(station["x"]), 2),
            "y": round(float(station["y"]), 2),
            "ux": round(float(station["ux"]), 2),
            "uy": round(float(station["uy"]), 2),
            "v": station["v"],
            "t": station["t"],
            "w": winner,
            "ws": round(float(share), 1) if share is not None else None,
        }
        if station.get("l"):
            row["l"] = station["l"]
        rows.append(row)
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    official = load_json(DATA / "wiki_official_results.json")
    k26 = load_k26_status()
    names_en = load_json(DATA / "settlement_names_en.json")
    parties = {}
    for map_path in sorted(DATA.glob("map_*.json"), key=lambda path: int(path.stem.split("_")[1])):
        election_id = map_path.stem.split("_")[1]
        map_data = load_json(map_path)
        parties[election_id] = build_parties(map_data, election_id)
        write_json(OUT / f"settlements_{election_id}.json", build_settlements(map_data))

    write_json(
        OUT / "meta.json",
        {
            "elections": build_elections(k26),
            "k26": k26,
            "parties": parties,
            "official": official,
            "notes": {
                "26": k26_note(official, k26),
                "transfers": (
                    "Transfer figures are a national least-squares estimate, not a count of "
                    "individual voters. percentage is the share of the source party. "
                    "percentage_ci, when present, is the 95% ballot-bootstrap interval."
                ),
                "scope": (
                    "Settlement tools return settlement totals. "
                    "Ballot questions use the t-SNE and UMAP tools, which return neighbors and the winning party, "
                    "not the full party vector of every box."
                ),
                "embeddings": (
                    "t-SNE and UMAP are 2D views of each ballot's party-share vector, not geography. "
                    "t-SNE distance is meaningful only among nearby points. "
                    "UMAP keeps more of the global layout."
                ),
            },
        },
    )
    write_json(OUT / "names_en.json", names_en)
    write_json(OUT / "volatility.json", build_volatility())
    write_json(OUT / "transfers.json", build_transfers())
    for tsne_path in sorted(DATA.glob("tsne_*.json"), key=lambda path: int(path.stem.split("_")[1])):
        election_id = tsne_path.stem.split("_")[1]
        write_json(OUT / f"embeddings_{election_id}.json", build_embeddings(load_json(tsne_path)))


if __name__ == "__main__":
    main()
