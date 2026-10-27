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

The vectors run over ALL parties, not just the majors. (An earlier version
renormalised each box over the transfer matrix's major parties only, which
made votes mistakenly fed into an esoteric list's column invisible: the
esoteric votes sat outside both vectors, and the donor major's loss was
diluted across the renormalised majors.) Major destinations are predicted
from the transfer matrix as before; each esoteric destination is predicted
from the source box's total non-major share, allocated across esoteric
lists by their counted national share of the non-major vote (falling back
to same-symbol persistence when no esoteric votes have been counted yet).

Box vote counts come from the raw ballot25.csv / ballot26.csv columns —
tsne_*.json only carries the major parties — matched by settlement code
and ballot number from the crosswalk.

Output: site/data/suspects_26.json with the top TOP_N boxes.
    source venv/bin/activate && python generate_suspects_data.py
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOP_N = 60
DECISIONS = ("id", "id_dot1")
MAJOR26 = None  # filled from party_config in score_all


def norm_ballot(value):
    b = str(value).strip()
    if b.endswith(".0") and b[:-2].isdigit():
        b = b[:-2]
    return b


def norm_code(value):
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()


def load_box_votes(path, encoding):
    """{(settlement_code, ballot): ({symbol: votes}, valid)} + national totals."""
    boxes, national = {}, {}
    with Path(path).open(encoding=encoding) as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        party_cols = [c for c in cols[cols.index("כשרים") + 1:] if c not in ("חיצוניות", "חיצוניים", "קלפי אחרת")]
        for row in reader:
            votes = {}
            for col in party_cols:
                try:
                    v = int(float(row.get(col) or 0))
                except ValueError:
                    v = 0
                if v:
                    votes[col] = v
                    national[col] = national.get(col, 0) + v
            valid = int(float(row.get("כשרים") or 0))
            boxes[(norm_code(row.get("סמל ישוב")), norm_ballot(row.get("קלפי")))] = (votes, valid)
    return boxes, national


def score_all(ballot25_path, ballot26_path):
    """Score every crosswalk-matched box; returns (scored, parties, meta)."""
    from party_config import ELECTIONS, get_party_name

    transfer = json.loads((ROOT / "site/data/transfer_25_to_26.json").read_text(encoding="utf-8"))
    boxes25, nat25 = load_box_votes(ballot25_path, ELECTIONS["25"].get("encoding", "utf-8-sig"))
    boxes26, nat26 = load_box_votes(ballot26_path, ELECTIONS["26"].get("encoding", "utf-8-sig"))

    major_src = ELECTIONS["25"]["major_parties"]["symbols"]   # K25 symbols
    major_dst = ELECTIONS["26"]["major_parties"]["symbols"]   # K26 symbols

    # Destination parties: the majors (colour/name from the transfer file),
    # then every esoteric K26 list that has actually received votes.
    info_by_symbol = {p["symbol"]: p for p in transfer["nodes_to"]}
    parties = []
    for symbol in major_dst:
        p = info_by_symbol.get(symbol, {})
        parties.append({"name": p.get("name") or get_party_name(symbol, "26"),
                        "symbol": symbol, "color": p.get("color", "#666")})
    esoteric_dst = [s for s in sorted(nat26, key=lambda s: -nat26[s])
                    if s not in major_dst and nat26[s] > 0]
    for symbol in esoteric_dst:
        name = get_party_name(symbol, "26")
        parties.append({"name": name if name != symbol else f"רשימה {symbol}",
                        "symbol": symbol, "color": "#9ca3af"})
    dst_symbols = [p["symbol"] for p in parties]
    dst_index = {s: j for j, s in enumerate(dst_symbols)}

    # Transfer matrix between the major symbols (edges carry symbols),
    # row-normalised as before.
    matrix = {s: {d: 0.0 for d in major_dst} for s in major_src}
    for edge in transfer["transfers"]:
        if edge["source_symbol"] in matrix and edge["target_symbol"] in matrix[edge["source_symbol"]]:
            matrix[edge["source_symbol"]][edge["target_symbol"]] = edge["percentage"] / 100.0
    for row in matrix.values():
        s = sum(row.values())
        if s > 0:
            for d in row:
                row[d] /= s

    nat26_other = sum(v for s, v in nat26.items() if s not in major_dst)

    crosswalk = []
    with (ROOT / "data/k25_k26_ballot_union.csv").open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["decision"] in DECISIONS:
                crosswalk.append(row)

    scored, skipped = [], 0
    for row in crosswalk:
        src_box = boxes25.get((norm_code(row["k25_code"]), norm_ballot(row["k25_ballot"])))
        dst_box = boxes26.get((norm_code(row["k26_code"]), norm_ballot(row["k26_ballot"])))
        if src_box is None or dst_box is None:
            skipped += 1
            continue
        src_votes, _ = src_box
        dst_votes, dst_valid = dst_box
        src_total = sum(src_votes.values())
        dst_total = sum(dst_votes.values())
        if src_total <= 0 or dst_total <= 0:
            skipped += 1
            continue

        src_share = {s: v / src_total for s, v in src_votes.items()}
        src_other = sum(v for s, v in src_share.items() if s not in major_src)

        pred = [0.0] * len(dst_symbols)
        for s in major_src:
            share = src_share.get(s, 0.0)
            if share:
                for d, frac in matrix[s].items():
                    pred[dst_index[d]] += share * frac
        for s in esoteric_dst:
            j = dst_index[s]
            if nat26_other > 0:
                pred[j] = src_other * nat26[s] / nat26_other
            else:
                pred[j] = src_share.get(s, 0.0)  # same-symbol persistence
        ps = sum(pred)
        pred = [v / ps for v in pred] if ps > 0 else pred

        actual = [dst_votes.get(s, 0) / dst_total for s in dst_symbols]
        # Any K26 votes for lists outside the destination set (zero-vote
        # columns nationally) still count toward the distance.
        covered = sum(dst_votes.get(s, 0) for s in dst_symbols)
        tvd = 0.5 * (sum(abs(a - p) for a, p in zip(actual, pred))
                     + (dst_total - covered) / dst_total)
        dev_idx = max(range(len(dst_symbols)), key=lambda j: actual[j] - pred[j])
        scored.append({
            "n": row["k26_name"], "b": norm_ballot(row["k26_ballot"]), "v": dst_valid,
            "venue": row.get("k26_venue", ""),
            "src_n": row["k25_name"], "src_b": norm_ballot(row["k25_ballot"]),
            "decision": row["decision"],
            "tvd": round(tvd, 4),
            "dev_party": parties[dev_idx]["name"],
            "dev_symbol": dst_symbols[dev_idx],
            "dev_pts": round((actual[dev_idx] - pred[dev_idx]) * 100, 1),
            "actual": [round(a * 100, 2) for a in actual],
            "pred": [round(p * 100, 2) for p in pred],
        })

    scored.sort(key=lambda r: -r["tvd"])
    meta = {
        "paired_ballots": len(scored), "skipped": skipped,
        "r_squared": transfer.get("stats", {}).get("r_squared"),
    }
    return scored, parties, meta


def main():
    from party_config import ELECTIONS

    parser = argparse.ArgumentParser()
    parser.add_argument("--ballot25", default=str(ROOT / ELECTIONS["25"]["file"]))
    parser.add_argument("--ballot26", default=str(ROOT / ELECTIONS["26"]["file"]))
    parser.add_argument("--out", default=str(ROOT / "site/data/suspects_26.json"))
    args = parser.parse_args()

    scored, parties, meta = score_all(args.ballot25, args.ballot26)
    meta["method"] = (
        "TVD between the K26 result and the national 25->26 transfer-regression "
        "prediction over ALL parties (majors from the transfer matrix; esoteric "
        "lists from the source box's non-major share allocated by their counted "
        "national share), pairing each K26 box with its index-matched K25 ballot "
        "(data/k25_k26_ballot_union.csv, decisions id/id_dot1 only)."
    )
    out = {"meta": meta, "parties": parties, "ballots": scored[:TOP_N]}
    path = Path(args.out)
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {path} ({meta['paired_ballots']} paired ballots, top {TOP_N}, "
          f"{len(parties)} parties incl. {len(parties) - len(ELECTIONS['26']['major_parties']['symbols'])} esoteric)")
    for r in scored[:8]:
        print(f"  {r['tvd']:.3f}  {r['n']} {r['b']}  <- K25 {r['src_n']} {r['src_b']} ({r['decision']})  "
              f"dev {r['dev_party']} +{r['dev_pts']}")


if __name__ == "__main__":
    main()
