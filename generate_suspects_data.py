#!/usr/bin/env python3
"""Most-suspicious K26 ballots for the k26.html command-center pane.

A ballot is "suspicious" if its K26 result is far from what the national
25->26 transfer regression predicts for it. The prediction must start from
the K25 ballot the K26 simulation actually sourced the box from — the
official-roster crosswalk in data/k25_k26_ballot_union.csv (the same file
simulate_election_26.py uses). Pairing by settlement|ballot string alone
(the naive approach) mismatches new/renumbered boxes: e.g. Jerusalem 33.3
is a new Haredi-school box whose votes were drawn from nearby Haredi K25
boxes, so a key-matched "residual" of 72% is a pairing artifact, not noise.

For index-matched boxes only (crosswalk decisions id / id_dot1 — same
settlement, same ballot index; venue/coord pairs are different physical
boxes and are excluded):
    pred = (K25 source ballot proportions) @ T
with T the published, re-estimated transfer matrix (row-normalised), and
    score = total variation distance(actual, pred)  in [0, 1].

Output: site/data/suspects_26.json with the top TOP_N boxes.
    source venv/bin/activate && python generate_suspects_data.py
"""
import csv
import json
from pathlib import Path

from generate_map_data import normalize_name

ROOT = Path(__file__).resolve().parent
TOP_N = 60
MIN_VOTERS = 100
DECISIONS = ("id", "id_dot1")


def box_sector(name, sectors):
    entry = sectors.get(normalize_name(name), {})
    if entry.get("population") in ("arab", "bedouin", "druze", "circassian"):
        return entry["population"]
    return "haredi" if entry.get("haredi") else "other"


def rank_within_sector(scored, sectors=None):
    """Rank boxes by robust z of their TVD inside their own sector.

    A raw national TVD ranks whole sectors the national matrix fits poorly
    (on real 2021->2022 data 53% of the top 60 were Druze boxes, 1.8% of all
    boxes). Comparing each box with its own sector's median keeps the list
    about boxes, not communities. Small boxes are dropped: their shares move
    by several points on noise alone.
    """
    if sectors is None:
        sectors = json.loads((ROOT / "site/data/settlement_sectors.json").read_text(encoding="utf-8"))["settlements"]
    scored = [r for r in scored if (r.get("v") or 0) >= MIN_VOTERS]
    by_sector = {}
    for r in scored:
        r["sector"] = box_sector(r["n"], sectors)
        by_sector.setdefault(r["sector"], []).append(r["tvd"])
    stats = {}
    for name, values in by_sector.items():
        values = sorted(values)
        med = values[len(values) // 2]
        mad = sorted(abs(v - med) for v in values)[len(values) // 2]
        stats[name] = (med, max(1.4826 * mad, 0.01))
    for r in scored:
        med, scale = stats[r["sector"]]
        r["z"] = round((r["tvd"] - med) / scale, 2)
    scored.sort(key=lambda r: -r["z"])
    return scored


def shares(props, names):
    vec = [float(props.get(n, 0.0)) for n in names]
    total = sum(vec)
    return [v / total for v in vec] if total > 0 else [0.0] * len(names)


def main():
    tsne25 = json.loads((ROOT / "site/data/tsne_25.json").read_text(encoding="utf-8"))
    tsne26 = json.loads((ROOT / "site/data/tsne_26.json").read_text(encoding="utf-8"))
    transfer = json.loads((ROOT / "site/data/transfer_25_to_26.json").read_text(encoding="utf-8"))

    from_names = [p["name"] for p in transfer["nodes_from"]]
    to_parties = [{"name": p["name"], "symbol": p["symbol"], "color": p.get("color", "#666")}
                  for p in transfer["nodes_to"]]
    to_names = [p["name"] for p in to_parties]

    # Re-estimated transfer matrix, row-normalised (as in prepare_fraud_sim.py)
    idx_from = {n: i for i, n in enumerate(from_names)}
    idx_to = {n: i for i, n in enumerate(to_names)}
    matrix = [[0.0] * len(to_names) for _ in from_names]
    for edge in transfer["transfers"]:
        if edge["source"] in idx_from and edge["target"] in idx_to:
            matrix[idx_from[edge["source"]]][idx_to[edge["target"]]] = edge["percentage"] / 100.0
    for row in matrix:
        s = sum(row)
        if s > 0:
            for j in range(len(row)):
                row[j] /= s

    by_key_25 = {s["n"] + "|" + str(s["b"]): s for s in tsne25["stations"]}
    by_key_26 = {s["n"] + "|" + str(s["b"]): s for s in tsne26["stations"]}

    crosswalk = {}
    with (ROOT / "data/k25_k26_ballot_union.csv").open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["decision"] in DECISIONS:
                crosswalk[(row["k26_name"], row["k26_ballot"])] = row

    scored, skipped = [], 0
    for (name, ballot), row in crosswalk.items():
        st = by_key_26.get(name + "|" + ballot)
        sf = by_key_25.get(row["k25_name"] + "|" + row["k25_ballot"])
        if st is None or sf is None:
            skipped += 1
            continue
        src = shares(sf.get("p", {}), from_names)
        actual = shares(st.get("p", {}), to_names)
        if sum(src) <= 0 or sum(actual) <= 0:
            skipped += 1
            continue
        pred = [sum(src[i] * matrix[i][j] for i in range(len(from_names))) for j in range(len(to_names))]
        ps = sum(pred)
        pred = [v / ps for v in pred] if ps > 0 else pred
        tvd = 0.5 * sum(abs(a - p) for a, p in zip(actual, pred))
        dev_idx = max(range(len(to_names)), key=lambda j: actual[j] - pred[j])
        scored.append({
            "n": name, "b": ballot, "v": st.get("v", 0),
            "venue": row.get("k26_venue", ""),
            "src_n": row["k25_name"], "src_b": row["k25_ballot"], "decision": row["decision"],
            "tvd": round(tvd, 4),
            "dev_party": to_names[dev_idx], "dev_pts": round((actual[dev_idx] - pred[dev_idx]) * 100, 1),
            "actual": [round(a * 100, 2) for a in actual],
            "pred": [round(p * 100, 2) for p in pred],
        })

    scored = rank_within_sector(scored)
    out = {
        "meta": {
            "method": "TVD between the K26 result and the national 25->26 transfer-regression "
                      "prediction, pairing each K26 box with its index-matched K25 ballot "
                      "(data/k25_k26_ballot_union.csv, decisions id/id_dot1 only), ranked by "
                      f"how far it sits above the median TVD of its own sector (robust z), "
                      f"boxes with at least {MIN_VOTERS} voters.",
            "paired_ballots": len(scored), "skipped": skipped,
            "r_squared": transfer.get("stats", {}).get("r_squared"),
        },
        "parties": to_parties,
        "ballots": scored[:TOP_N],
    }
    path = ROOT / "site/data/suspects_26.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {path} ({len(scored)} paired ballots, top {TOP_N})")
    for r in scored[:8]:
        print(f"  {r['tvd']:.3f}  {r['n']} {r['b']}  <- K25 {r['src_n']} {r['src_b']} ({r['decision']})  dev {r['dev_party']} +{r['dev_pts']}")


if __name__ == "__main__":
    main()
