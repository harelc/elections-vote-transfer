#!/usr/bin/env python3
"""Command-center extras for k26.html -> site/data/command_center_26.json

Bundles four analyses that share the same inputs, so they are generated
together (and refreshed together on election night):

  twelve_knessets
                The K26 result re-allocated as if only one slice of Israel
                voted (kibbutzim, moshavim, Arab/Druze/Bedouin localities,
                West-Bank settlements, Haredi localities, mixed cities,
                socioeconomic cluster bands...). Slices come from
                settlement_sectors.json (generate_settlement_sectors.py);
                never from the votes themselves.
  factoids      Machine-mined records/extremes for the ticker. Templates
                scan map_25/map_26 + sectors; ranked by magnitude, never
                hand-picked.
  bellwether    Ballots whose party vector is closest to the national
                result, consistently across K16-K25 (plus the single most
                representative K26 ballot). t-SNE distance is NOT used;
                this is total-variation distance in vote-share space.
  nowcast       Election-night projection of the uncounted ballots, gated.
                Counted boxes are identified against the official roster
                (data/k25_k26_ballot_union.csv, all non-k25_only rows).
                Uncounted boxes are predicted from their K25 source ballot
                through the ANALYZED 25->26 transfer matrix (never the
                simulation's hidden generating matrix):
                  - live mode: the published convex matrix in
                    transfer_25_to_26.json, which on election night is
                    estimated from the counted snapshot only;
                  - rehearsal mode (simulated status): the published convex
                    design refit on a deterministic masked subset whose count
                    is deliberately skewed (the large Haredi cities almost
                    entirely uncounted), so the gate and the now-vs-mean
                    divergence can be exercised before the night.
                The gate opens into the full party-level projection as
                soon as it is semi-reliable: >=1,000 matched counted
                ballots, >=12% of roster K25 votes counted, R2>=0.75,
                composition TVD<=0.18, and every K25 source party with
                >=3% national share has >=8,000 counted origin votes.
                Source rows below the origin-vote floor are shrunk toward
                the global row (partial pooling) instead of being trusted.
                Monte-Carlo dispersion uses the empirical Dirichlet
                alpha for 24->25 (alpha_estimates.json), not the
                simulation's alpha.

    source venv/bin/activate && python generate_command_center_data.py
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SITE_DATA = ROOT / "site" / "data"

from k26_live import SURPLUS_AGREEMENTS, bader_ofer
from generate_map_data import normalize_name

BLOCS = {
    "right": ["הליכוד", "יהדות התורה", "ש״ס", "עוצמה יהודית", "הציונות הדתית", "עמך ישראל", "המילואימניקים והכלכלית"],
    "center": ["ישר", "ביחד", "הדמוקרטים", "ישראל ביתנו"],
    "arab": ["הרשימה המשותפת", "רע״ם"],
}
SIMS = 200
ALPHA_FALLBACK = 51.2


def load(name, default=None):
    p = SITE_DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def settlement_votes(settlement):
    """Party votes implied by a map settlement's percentages."""
    v = settlement.get("voters") or 0
    return {p: pct * v / 100.0 for p, pct in (settlement.get("proportions") or {}).items()}


def add_into(acc, votes):
    for k, val in votes.items():
        acc[k] = acc.get(k, 0.0) + val


# ------------------------------------------------------------- twelve knessets
def twelve_knessets(map26, sectors):
    sec = sectors.get("settlements", {})
    slices = [
        ("kibbutzim", "קיבוצים", "Kibbutzim", lambda e: e.get("form") == "kibbutz"),
        ("moshavim", "מושבים", "Moshavim", lambda e: e.get("form") in ("moshav", "moshav_shitufi")),
        # Community settlements are set-diffed against the WB settlements:
        # most WB localities are formally community settlements, but they
        # get their own tribe below and should not be counted twice.
        ("community", "יישובים קהילתיים", "Community settlements", lambda e: e.get("form") == "community" and not e.get("wb")),
        ("cities", "ערים", "Cities", lambda e: e.get("form") == "city"),
        ("wb", "התנחלויות", "West Bank settlements", lambda e: e.get("wb")),
        ("arab", "יישובים ערביים", "Arab localities", lambda e: e.get("population") == "arab"),
        ("bedouin", "יישובים בדואיים", "Bedouin localities", lambda e: e.get("population") == "bedouin"),
        ("druze", "יישובים דרוזיים", "Druze localities", lambda e: e.get("population") == "druze"),
        ("haredi", "יישובים חרדיים", "Haredi localities", lambda e: e.get("haredi")),
        ("cluster_low", "אשכולות חברתיים־כלכליים 1–3", "Socioeconomic clusters 1-3", lambda e, s: (s.get("cluster") or 0) in (1, 2, 3)),
        ("cluster_mid", "אשכולות חברתיים־כלכליים 4–7", "Socioeconomic clusters 4-7", lambda e, s: (s.get("cluster") or 0) in (4, 5, 6, 7)),
        ("cluster_high", "אשכולות חברתיים־כלכליים 8–10", "Socioeconomic clusters 8-10", lambda e, s: (s.get("cluster") or 0) in (8, 9, 10)),
        # Districts (מחוזות) from settlement_sectors.district -- the CBS
        # district of each locality, via settlement code -> subdistrict
        # (generate_settlement_districts.py). Judea and Samaria is the CBS
        # area, not formally a district, so it carries no מחוז prefix.
        ("district_jerusalem", "מחוז ירושלים", "Jerusalem District", lambda e: e.get("district") == "ירושלים"),
        ("district_north", "מחוז הצפון", "Northern District", lambda e: e.get("district") == "הצפון"),
        ("district_haifa", "מחוז חיפה", "Haifa District", lambda e: e.get("district") == "חיפה"),
        ("district_center", "מחוז המרכז", "Central District", lambda e: e.get("district") == "המרכז"),
        ("district_telaviv", "מחוז תל אביב", "Tel Aviv District", lambda e: e.get("district") == "תל אביב"),
        ("district_south", "מחוז הדרום", "Southern District", lambda e: e.get("district") == "הדרום"),
        ("district_judeasamaria", "יהודה ושומרון", "Judea and Samaria", lambda e: e.get("district") == "יהודה ושומרון"),
    ]
    # Sector slices + district slices, each re-allocated its own 120 seats.
    # ("Jewish localities" was cut for tracking the national result too
    # closely; "mixed cities" for being dominated by Jerusalem + Tel Aviv.)
    national = {}
    for s in map26["settlements"]:
        add_into(national, settlement_votes(s))
    national_total = sum(national.values()) or 1

    out = []
    for slice_id, he, en, pred in slices:
        votes, n_set = {}, 0
        for s in map26["settlements"]:
            entry = sec.get(s["name"], {})
            try:
                take = pred(entry, s)
            except TypeError:
                take = pred(entry)
            if not take:
                continue
            n_set += 1
            add_into(votes, settlement_votes(s))
        total = sum(votes.values())
        if total < 20000 or n_set < 3:
            continue
        seats = bader_ofer(votes, agreements=SURPLUS_AGREEMENTS, valid_total=total)
        top = sorted(
            ({"name": k, "seats": seats.get(k, 0), "votes": round(v), "share": round(100 * v / total, 1)}
             for k, v in votes.items()),
            key=lambda r: (-r["seats"], -r["votes"]),
        )[:4]
        out.append({
            "id": slice_id, "label_he": he, "label_en": en,
            "settlements": n_set, "voters": round(total),
            "share_national": round(100 * total / national_total, 1),
            "top": top,
            "all": sorted(
                ({"name": k, "seats": seats.get(k, 0), "votes": round(v), "share": round(100 * v / total, 1)}
                 for k, v in votes.items()),
                key=lambda r: (-r["seats"], -r["votes"])),
            "blocs": {b: sum(seats.get(p, 0) for p in ps) for b, ps in BLOCS.items()},
        })
    return out


# ------------------------------------------------------------------- factoids
def factoids(map25, map26, sectors, wiki26, names_en, party_en):
    sec = sectors.get("settlements", {})
    by25 = {s["name"]: s for s in map25["settlements"]}
    facts = []

    def en_s(name):
        return names_en.get(name, name)

    # Winner flips in sizeable settlements
    flips = []
    for s in map26["settlements"]:
        o = by25.get(s["name"])
        if not o or (s.get("voters") or 0) < 1500:
            continue
        if o.get("winningParty") and s.get("winningParty") and o["winningParty"] != s["winningParty"]:
            flips.append(s)
    flips.sort(key=lambda s: -(s.get("voters") or 0))
    for s in flips[:3]:
        o = by25[s["name"]]
        facts.append({
            "kind": "flip",
            "he": f"מהפך ב{s['name']}: ב־25 ניצחה {o['winningParty']}, ב־26 מנצחת {s['winningParty']}",
            "en": f"Flip in {en_s(s['name'])}: {party_en.get(o['winningParty'], o['winningParty'])} (K25) → {party_en.get(s['winningParty'], s['winningParty'])} (K26)",
            "source_he": "השוואת המפלגה המנצחת ביישוב, מפות 25 ו־26",
            "source_en": "Winning party per settlement, maps 25 vs 26",
        })

    # Largest party gain / loss in a sizeable settlement
    best_gain, best_loss = None, None
    for s in map26["settlements"]:
        o = by25.get(s["name"])
        if not o or (s.get("voters") or 0) < 3000:
            continue
        for party, pct in (s.get("proportions") or {}).items():
            d = pct - (o.get("proportions") or {}).get(party, 0.0)
            if best_gain is None or d > best_gain[0]:
                best_gain = (d, party, s["name"])
            if best_loss is None or d < best_loss[0]:
                best_loss = (d, party, s["name"])
    if best_gain:
        d, party, name = best_gain
        facts.append({
            "kind": "gain",
            "he": f"הזינוק הגדול ביותר: {party} ב{name} עלתה ב־{d:.1f} נקודות לעומת 2022",
            "en": f"Biggest surge: {party_en.get(party, party)} in {en_s(name)} is up {d:.1f} points vs 2022",
            "source_he": "הפרש אחוזי תמיכה ביישובים עם 3,000+ מצביעים",
            "source_en": "Support change in settlements with 3,000+ voters",
        })
    if best_loss:
        d, party, name = best_loss
        facts.append({
            "kind": "loss",
            "he": f"הנפילה הגדולה ביותר: {party} ב{name} ירדה ב־{abs(d):.1f} נקודות לעומת 2022",
            "en": f"Biggest collapse: {party_en.get(party, party)} in {en_s(name)} is down {abs(d):.1f} points vs 2022",
            "source_he": "הפרש אחוזי תמיכה ביישובים עם 3,000+ מצביעים",
            "source_en": "Support change in settlements with 3,000+ voters",
        })

    # Turnout extremes (sizeable settlements)
    sized = [s for s in map26["settlements"] if (s.get("eligible") or 0) >= 800]
    if sized:
        hi = max(sized, key=lambda s: s.get("turnout") or 0)
        lo = min(sized, key=lambda s: s.get("turnout") or 0)
        facts.append({
            "kind": "turnout_hi",
            "he": f"שיא ההצבעה: ב{hi['name']} הצביעו {hi['turnout']:.1f}% מבעלי זכות הבחירה",
            "en": f"Turnout record: {en_s(hi['name'])} voted at {hi['turnout']:.1f}%",
            "source_he": "יישובים עם 800+ בעלי זכות בחירה",
            "source_en": "Settlements with 800+ eligible voters",
        })
        facts.append({
            "kind": "turnout_lo",
            "he": f"ובצד השני: ב{lo['name']} הצביעו רק {lo['turnout']:.1f}%",
            "en": f"At the other end: only {lo['turnout']:.1f}% voted in {en_s(lo['name'])}",
            "source_he": "יישובים עם 800+ בעלי זכות בחירה",
            "source_en": "Settlements with 800+ eligible voters",
        })

    # Each major party's strongest settlement
    for p in sorted(wiki26, key=lambda x: -x["votes"])[:6]:
        party = p["name"]
        cand = [s for s in map26["settlements"] if (s.get("voters") or 0) >= 400]
        if not cand:
            continue
        top_s = max(cand, key=lambda s: (s.get("proportions") or {}).get(party, 0.0))
        share = (top_s.get("proportions") or {}).get(party, 0.0)
        if share <= 0:
            continue
        facts.append({
            "kind": "stronghold",
            "he": f"המעוז של {party}: {top_s['name']} עם {share:.1f}%",
            "en": f"{party_en.get(party, party)}'s stronghold: {en_s(top_s['name'])} at {share:.1f}%",
            "source_he": "יישובים עם 400+ מצביעים",
            "source_en": "Settlements with 400+ voters",
        })

    # Sector winners (kibbutzim vs moshavim vs Arab localities vs WB)
    for slice_id, he_name, en_name, pred in (
        ("kibbutzim", "הקיבוצים", "the kibbutzim", lambda e: e.get("form") == "kibbutz"),
        ("moshavim", "המושבים", "the moshavim", lambda e: e.get("form") in ("moshav", "moshav_shitufi")),
        ("wb", "ההתנחלויות", "West Bank settlements", lambda e: e.get("wb")),
        ("arab", "היישובים הערביים", "Arab localities", lambda e: e.get("population") == "arab"),
    ):
        agg = {}
        for s in map26["settlements"]:
            if pred(sec.get(s["name"], {})):
                add_into(agg, settlement_votes(s))
        if sum(agg.values()) < 20000:
            continue
        winner, wv = max(agg.items(), key=lambda kv: kv[1])
        share = 100 * wv / sum(agg.values())
        facts.append({
            "kind": f"sector_{slice_id}",
            "he": f"ב{he_name} מנצחת {winner} עם {share:.1f}%",
            "en": f"In {en_name}, {party_en.get(winner, winner)} leads with {share:.1f}%",
            "source_he": "סיווג יישובים: settlement_sectors.json",
            "source_en": "Settlement classification: settlement_sectors.json",
        })

    # Threshold distance for the closest below-threshold list
    total_valid = sum(p["votes"] for p in wiki26) or 1
    thr_votes = total_valid * 3.25 / 100
    below = [p for p in wiki26 if not p["seats"]]
    if below:
        closest = max(below, key=lambda p: p["votes"])
        gap = round(thr_votes - closest["votes"])
        if gap > 0:
            facts.append({
                "kind": "threshold",
                "he": f"{closest['name']} רחוקה {gap:,} קולות מאחוז החסימה",
                "en": f"{party_en.get(closest['name'], closest['name'])} is {gap:,} votes short of the threshold",
                "source_he": "אחוז חסימה 3.25% מסך הקולות הכשרים",
                "source_en": "3.25% threshold of total valid votes",
            })
    return facts


# ----------------------------------------------------------------- bellwether
def national_shares(map_e):
    agg = {}
    for s in map_e["settlements"]:
        add_into(agg, settlement_votes(s))
    total = sum(agg.values()) or 1
    return {k: v / total for k, v in agg.items()}


def bellwether(names_en):
    per_key = {}  # key -> list of (election, tvd)
    venue_of = {}  # key -> venue name at its latest appearance
    elections = [str(e) for e in range(16, 26)]
    for eid in elections:
        map_e = load(f"map_{eid}.json")
        tsne_e = load(f"tsne_{eid}.json")
        if not map_e or not tsne_e:
            continue
        nat = national_shares(map_e)
        parties = [p["name"] for p in tsne_e["parties"]]
        nat_vec = np.array([nat.get(p, 0.0) for p in parties])
        for st in tsne_e["stations"]:
            props = st.get("p") or {}
            tot = sum(props.values()) or 1
            vec = np.array([props.get(p, 0.0) / tot for p in parties])
            tvd = 0.5 * float(np.abs(vec - nat_vec).sum())
            key = f"{st['n']}|{st['b']}"
            per_key.setdefault(key, []).append((eid, tvd))
            if st.get("l"):
                venue_of[key] = st["l"]  # latest election's venue wins
    rows = []
    for key, vals in per_key.items():
        if len(vals) < 6:
            continue
        name, ballot = key.rsplit("|", 1)
        rows.append({
            "n": name, "n_en": names_en.get(name, name), "b": ballot,
            "elections": len(vals),
            "mean_tvd": round(float(np.mean([v for _, v in vals])), 4),
        })
    rows.sort(key=lambda r: r["mean_tvd"])
    # Most representative single K26 ballot
    k26_best = None
    map26, tsne26 = load("map_26.json"), load("tsne_26.json")
    if map26 and tsne26:
        nat = national_shares(map26)
        parties = [p["name"] for p in tsne26["parties"]]
        nat_vec = np.array([nat.get(p, 0.0) for p in parties])
        best = None
        for st in tsne26["stations"]:
            props = st.get("p") or {}
            tot = sum(props.values()) or 1
            vec = np.array([props.get(p, 0.0) / tot for p in parties])
            tvd = 0.5 * float(np.abs(vec - nat_vec).sum())
            if best is None or tvd < best[0]:
                best = (tvd, st)
        if best:
            tvd, st = best
            k26_best = {"n": st["n"], "n_en": names_en.get(st["n"], st["n"]), "b": st["b"], "tvd": round(tvd, 4), "v": st.get("v", 0)}
        # Each leaderboard ballot's own K26 result (once that box exists in
        # the K26 data — on election night, once it has been counted).
        # Ballot numbers are renumbered between elections, so the lookup
        # goes through the official crosswalk: the K26 successor of the
        # K25 box (same number, else same venue, else nearest).
        st26_by_key = {f"{s['n']}|{s['b']}": s for s in tsne26["stations"]}
        parties26 = [p["name"] for p in tsne26["parties"]]
        nat26_vec = np.array([nat.get(p, 0.0) for p in parties26])
        from generate_map_data import normalize_name
        successor = {}
        union_path = ROOT / "data/k25_k26_ballot_union.csv"
        if union_path.exists():
            rank = {"id": 0, "id_dot1": 1, "venue": 2, "coord": 3}
            with union_path.open(encoding="utf-8-sig") as fh:
                urows = [row for row in csv.DictReader(fh) if row["decision"] in rank]
            for row in sorted(urows, key=lambda x: rank[x["decision"]]):
                successor.setdefault(f"{normalize_name(row['k25_name'])}|{row['k25_ballot']}",
                                     (f"{normalize_name(row['k26_name'])}|{row['k26_ballot']}", row["decision"]))
        venue26 = {}
        for s in tsne26["stations"]:
            if s.get("l"):
                venue26.setdefault((s["n"], s["l"]), s)
        for r in rows[:10]:
            succ_key, via = successor.get(f"{r['n']}|{r['b']}", (f"{r['n']}|{r['b']}", "same number"))
            st = st26_by_key.get(succ_key)
            if st is None and venue_of.get(f"{r['n']}|{r['b']}"):
                st = venue26.get((r["n"], venue_of[f"{r['n']}|{r['b']}"]))
                if st is not None:
                    via = "venue_name"
            if st is None:
                r["k26"] = None
                continue
            props = st.get("p") or {}
            tot = sum(props.values()) or 1
            vec = np.array([props.get(p, 0.0) / tot for p in parties26])
            top = sorted(props.items(), key=lambda kv: -kv[1])[:5]
            r["k26"] = {
                "v": st.get("v", 0), "e": st.get("e", 0), "t": st.get("t", 0),
                "winner": top[0][0] if top else None,
                "tvd": round(0.5 * float(np.abs(vec - nat26_vec).sum()), 4),
                "top": [{"name": k, "pct": round(v, 1)} for k, v in top],
                "n": st["n"], "b": st["b"], "via": via,
            }
    return {"leaderboard": rows[:10], "unrepresentative": rows[-5:][::-1], "k26_most_representative": k26_best}


# -------------------------------------------------------------------- nowcast
def shares_of(props, names):
    vec = np.array([float(props.get(n, 0.0)) for n in names], dtype=float)
    s = vec.sum()
    return vec / s if s > 0 else vec


def nowcast(status, sectors, target_share=None, force=False):
    sec = sectors.get("settlements", {})
    tsne25, tsne26 = load("tsne_25.json"), load("tsne_26.json")
    transfer = load("transfer_25_to_26.json")
    map25 = load("map_25.json")
    mode = "live" if status.get("kind") in ("partial", "official") else "rehearsal"

    from_names = [p["name"] for p in transfer["nodes_from"]]
    to_names = [p["name"] for p in transfer["nodes_to"]]
    st25 = {f"{s['n']}|{s['b']}": s for s in tsne25["stations"]}
    st26 = {f"{s['n']}|{s['b']}": s for s in tsne26["stations"]}
    nat25 = np.array([transfer["nodes_from"][i].get("votes", 0) for i in range(len(from_names))], dtype=float)
    nat25 = nat25 / nat25.sum() if nat25.sum() else nat25

    # Official roster: every union row that has a K26 box.
    roster = []
    with (ROOT / "data/k25_k26_ballot_union.csv").open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["decision"] == "k25_only" or not row["k26_name"]:
                continue
            roster.append(row)

    def is_haredi_box(row):
        # Haredi boxes: curated Haredi localities, plus any ballot whose
        # K25 twin voted majority UTJ+Shas (Haredi neighbourhoods inside
        # mixed cities, above all Jerusalem). The mask is a counting-
        # order scenario, so identifying late-counted boxes by their
        # known K25 composition is the honest way to build it.
        entry = sec.get(normalize_name(row["k26_name"] or ""), {})
        if entry.get("haredi"):
            return True
        if row["k25_name"]:
            src = (st25.get(f"{row['k25_name']}|{row['k25_ballot']}")
                   or st25.get(f"{normalize_name(row['k25_name'])}|{row['k25_ballot']}"))
            if src:
                pp = src.get("p") or {}
                return (pp.get("יהדות התורה", 0) + pp.get("ש״ס", 0)) >= 50
        return False

    # Rehearsal mask cutoffs (percent of the deterministic per-ballot hash):
    # Haredi boxes count at ~14% of the rate of other boxes (8% vs 58% in
    # the default late-night mask). With --target-share, both cutoffs are
    # rescaled so the counted set is that share of the roster while keeping
    # the same skew — an earlier moment of the same night, not a new night.
    SKEW_RATIO = 8 / 58
    cuts = (8.0, 58.0)
    if mode == "rehearsal" and target_share:
        n_h = n_o = 0
        for row in roster:
            key = f"{row['k26_name']}|{row['k26_ballot']}"
            if key not in st26 or str(row["k26_code"]) == "9999":
                continue
            if is_haredi_box(row):
                n_h += 1
            else:
                n_o += 1
        # Aim at target_share of the full roster (as the page displays it:
        # counted_ballots / roster_ballots), including never-counted 9999s.
        o_cut = 100 * target_share * len(roster) / max(1, n_o + SKEW_RATIO * n_h)
        cuts = (SKEW_RATIO * o_cut, o_cut)
        print(f"  rehearsal target {target_share:.0%}: cutoffs haredi {cuts[0]:.1f}% / other {cuts[1]:.1f}% "
              f"(haredi boxes {n_h}, other {n_o})")

    def counted_key(row):
        key = f"{row['k26_name']}|{row['k26_ballot']}"
        if key not in st26:
            return None
        if mode == "rehearsal":
            # Deliberately skewed fake count: double envelopes (9999) never
            # counted; Haredi boxes almost entirely still uncounted. This
            # is the nasty election-night case: the counted-only ("now")
            # seats must visibly understate UTJ/Shas, and the projection
            # has to pull them back toward the truth.
            if str(row["k26_code"]) == "9999":
                return None
            h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 10000 / 100
            if h >= (cuts[0] if is_haredi_box(row) else cuts[1]):
                return None
        return key

    counted_rows, uncounted_rows = [], []
    for row in roster:
        (counted_rows if counted_key(row) else uncounted_rows).append(row)

    # Uncounted ballot locations, for the geomap's faint gray dots during a
    # partial count (compact [name, ballot, lat, lng] rows).
    geo_uncounted = []
    geo_counted = []
    try:
        stations_coord = (load("station_coordinates.json", {}) or {}).get("stations", {})
        map26_for_coords = load("map_26.json", {}) or {}
        settle_coords = {normalize_name(s["name"]): (s["lat"], s["lng"])
                         for s in map26_for_coords.get("settlements", [])
                         if s.get("lat") is not None}
        for row in uncounted_rows:
            b = str(row["k26_ballot"])
            if b.endswith(".0"):
                b = b[:-2]
            cd = (stations_coord.get(f"{normalize_name(row['k26_name'])}|{b}")
                  or stations_coord.get(f"{row['k26_name']}|{b}"))
            if cd and cd.get("lat") is not None:
                lat, lng = cd["lat"], cd["lng"]
            elif normalize_name(row["k26_name"]) in settle_coords:
                lat, lng = settle_coords[normalize_name(row["k26_name"])]
            else:
                continue
            geo_uncounted.append([normalize_name(row["k26_name"]), b, round(lat, 5), round(lng, 5)])
        # Counted ballot locations + winning party, for the mobile map
        # (compact [name, ballot, lat, lng, winner, winner_pct] rows).
        for row in counted_rows:
            b = str(row["k26_ballot"])
            if b.endswith(".0"):
                b = b[:-2]
            st = st26.get(f"{row['k26_name']}|{row['k26_ballot']}")
            if st is None:
                continue
            props = st.get("p") or {}
            if not props:
                continue
            winner = max(props, key=props.get)
            cd = (stations_coord.get(f"{normalize_name(row['k26_name'])}|{b}")
                  or stations_coord.get(f"{row['k26_name']}|{b}"))
            if cd and cd.get("lat") is not None:
                lat, lng = cd["lat"], cd["lng"]
            elif normalize_name(row["k26_name"]) in settle_coords:
                lat, lng = settle_coords[normalize_name(row["k26_name"])]
            else:
                continue
            geo_counted.append([normalize_name(row["k26_name"]), b, round(lat, 5), round(lng, 5),
                                winner, round(float(props[winner]), 1)])
    except Exception as error:
        print(f"geo_uncounted skipped ({error})")

    # Matched counted pairs: ALL crosswalk decisions (id, id_dot1, venue,
    # coord) — the same pairing the published transfer fit uses in
    # generate_transfer_data.design_matrices. (generate_suspects_data
    # restricts to id/id_dot1 because a fraud residual needs the same
    # physical box; a national transfer estimate wants every pair.)
    matched = []
    for row in counted_rows:
        if row["decision"] not in ("id", "id_dot1", "venue", "coord"):
            continue
        s26 = st26.get(f"{row['k26_name']}|{row['k26_ballot']}")
        s25 = st25.get(f"{row['k25_name']}|{row['k25_ballot']}")
        if s26 is not None and s25 is not None:
            matched.append((row, s25, s26))

    origin_votes = np.zeros(len(from_names))
    counted_k25_votes = 0.0
    for _, s25, s26 in matched:
        origin_votes += shares_of(s25.get("p") or {}, from_names) * (s26.get("v") or 0)
        counted_k25_votes += s25.get("v") or 0
    roster_k25_votes = sum(float(r["k25_valid"] or 0) for r in roster if r["decision"] in ("id", "id_dot1", "venue", "coord")) or 1
    counted_share = counted_k25_votes / roster_k25_votes

    # Composition distance: K25 party mix of counted boxes vs the full roster
    counted_dist = origin_votes / origin_votes.sum() if origin_votes.sum() else origin_votes
    comp_tvd = 0.5 * float(np.abs(counted_dist - nat25).sum()) if origin_votes.sum() else 1.0

    # Transfer matrix for the projection: in BOTH modes refit the solved
    # convex design on the counted boxes. Never rebuild T from
    # transfer_25_to_26.json's `transfers` list: that is a drawing subset
    # (flows >= 15,000 votes only, rounded to 0.1%), and renormalising it
    # redistributes the dropped flows onto the large ones.
    # Reuse the published fit's exact design (official crosswalk,
    # FORBIDDEN_CELLS zero-constraints, matched-valid-votes row sum),
    # subset to the counted boxes. Fitting shares with an
    # unconstrained solver was tried and misallocates collinear rows
    # (e.g. Likud +2pts on the uncounted aggregate).
    from generate_transfer_data import VoteTransferAnalyzer, load_k26_crosswalk
    analyzer = VoteTransferAnalyzer(method="convex")
    design = analyzer.design_matrices("25", "26")
    df_from, _ = analyzer.load_election_data("25")
    df_to, _ = analyzer.load_election_data("26")
    pairs = [(f, t) for f, t in load_k26_crosswalk()
             if f in set(df_from.index) and t in set(df_to.index)]
    counted_ids = set()
    for row in counted_rows:
        b = str(row["k26_ballot"])
        if b.endswith(".0"):
            b = b[:-2]
        counted_ids.add(f"{row['k26_code']}__{b}")
    row_mask = np.array([t in counted_ids for _, t in pairs])
    X, Y = design["X"][row_mask], design["Y"][row_mask]
    row_sum = float(Y.sum() / X.sum()) if X.sum() else 1.0
    Td = analyzer.solve_transfer_matrix_convex(X, Y, row_sum=row_sum, zero_cells=design["zero_cells"])
    Td = np.clip(np.array(Td, dtype=float), 0, None)
    # Reindex from the design's party order to the transfer file's order
    T = np.zeros((len(from_names), len(to_names)))
    for i, fn in enumerate(design["names_from"]):
        for j, tn in enumerate(design["names_to"]):
            if fn in from_names and tn in to_names:
                T[from_names.index(fn), to_names.index(tn)] = Td[i, j]
    pred = X @ Td
    ss_res = float(((Y - pred) ** 2).sum())
    ss_tot = float(((Y - Y.mean(axis=0)) ** 2).sum()) or 1.0
    r2 = 1 - ss_res / ss_tot
    estimator = f"published convex design refit on the counted subset ({mode})"

    row_sums = T.sum(axis=1, keepdims=True)
    T = np.divide(T, row_sums, out=np.zeros_like(T), where=row_sums > 0)
    # Partial pooling: rows with little counted origin data shrink to the
    # vote-weighted global row instead of being trusted at face value.
    global_row = (origin_votes @ T) / origin_votes.sum() if origin_votes.sum() else T.mean(axis=0)
    shrink_k = 8000.0
    for i in range(len(from_names)):
        wgt = origin_votes[i] / (origin_votes[i] + shrink_k) if origin_votes[i] > 0 else 0.0
        T[i] = wgt * T[i] + (1 - wgt) * global_row

    # Sector coverage (by K25 valid votes on the roster)
    sector_cov = {}
    for row in roster:
        pop = (sec.get(row["k26_name"]) or {}).get("population") or "unknown"
        bucket = sector_cov.setdefault(pop, {"counted": 0.0, "roster": 0.0})
        v = float(row["k25_valid"] or 0)
        bucket["roster"] += v
        if counted_key(row):
            bucket["counted"] += v
    sector_rows = [
        {"sector": k, "counted_share": round(v["counted"] / v["roster"], 3) if v["roster"] else 0.0, "roster_votes": round(v["roster"])}
        for k, v in sorted(sector_cov.items(), key=lambda kv: -kv[1]["roster"]) if v["roster"] > 5000
    ]

    checks = [
        {"id": "matched", "ok": len(matched) >= 1000, "value": len(matched), "threshold": 1000,
         "he": "קלפיות מוצלבות שנספרו", "en": "Matched counted ballots"},
        {"id": "share", "ok": counted_share >= 0.12, "value": round(counted_share, 3), "threshold": 0.12,
         "he": "איזה חלק מקולות 25 כבר יש לו קלפי תאומה שנספרה", "en": "Share of K25 votes that already have a counted twin ballot"},
        {"id": "r2", "ok": r2 >= 0.75, "value": round(float(r2), 3), "threshold": 0.75,
         "he": "מדד התאמה של מעברי הקולות המשוערים לתוצאות שנספרו (R² — מדד יחסי בלבד: גם התאמה מצוינת נמוכה מ־1.00, כי בכל קלפי יש גם רעש אקראי)",
         "en": "Fit of the estimated vote transfers to the counted results (R² — a relative index only: even an excellent fit is below 1.00, because every ballot box also contains random noise)"},
        {"id": "tvd", "ok": comp_tvd <= 0.18, "value": round(comp_tvd, 3), "threshold": 0.18,
         "he": "כמה תמהיל ההצבעה של 25 בקלפיות שנספרו שונה מהתמהיל הארצי (קטן = מייצג את הארץ)",
         "en": "How different the counted ballots' K25 vote mix is from the national mix (smaller = more representative)"},
    ]
    weak_sources = []
    for i, n in enumerate(from_names):
        if nat25[i] >= 0.03 and origin_votes[i] < 8000:
            weak_sources.append(n)
    checks.append({"id": "sources", "ok": not weak_sources, "value": weak_sources, "threshold": 8000,
                   "he": "מפלגות־מקור עם מספיק קולות מוצלבים (≥8,000)", "en": "Source parties with enough matched origin votes (≥8,000)"})
    ready = all(c["ok"] for c in checks)

    projection = None
    if (ready or force) and uncounted_rows:
        alpha_data = load("alpha_estimates.json", {}) or {}
        alpha = float((alpha_data.get("24_to_25") or {}).get("alpha_pooled") or ALPHA_FALLBACK)
        # Counted votes (actual) per K26 party
        counted_votes = np.zeros(len(to_names))
        counted_keys = set()
        for row in counted_rows:
            key = f"{row['k26_name']}|{row['k26_ballot']}"
            st = st26.get(key)
            if st is None:
                continue
            counted_keys.add(key)
            counted_votes += shares_of(st.get("p") or {}, to_names) * (st.get("v") or 0)
        # Expected valid votes per uncounted box: its K25 turnout, adjusted by
        # how counted boxes' turnout moved vs their own K25 turnout.
        num = den = 0.0
        for row, s25, s26 in matched:
            if (s25.get("e") or 0) > 0 and (s26.get("e") or 0) > 0:
                den += (s25.get("v") or 0) / s25["e"]
                num += (s26.get("v") or 0) / s26["e"]
        turnout_adj = min(1.15, max(0.7, num / den)) if den else 1.0
        counted_turnout = (sum((st26[k].get("v") or 0) for k in counted_keys) /
                           max(1, sum((st26[k].get("e") or 0) for k in counted_keys)))
        map25_by_name = {s["name"]: s for s in map25["settlements"]} if map25 else {}

        def source_shares(row):
            src = st25.get(f"{row['k25_name']}|{row['k25_ballot']}") if row["k25_name"] else None
            if src is not None:
                return shares_of(src.get("p") or {}, from_names), src
            if row["k26_name"] in map25_by_name:
                return shares_of(map25_by_name[row["k26_name"]].get("proportions") or {}, from_names), None
            return nat25, None

        pred_boxes, pred_weights, pred_src = [], [], []
        for row in uncounted_rows:
            shares, src = source_shares(row)
            if src is not None:
                base_turnout = (src.get("v") or 0) / src["e"] if (src.get("e") or 0) > 0 else counted_turnout
            elif row["k26_name"] in map25_by_name:
                base_turnout = (map25_by_name[row["k26_name"]].get("turnout") or 0) / 100.0 or counted_turnout
            else:
                base_turnout = counted_turnout
            elig = float(row["k26_eligible"] or 0) or (src.get("e") if src else 0) or 600
            expected = elig * min(0.97, base_turnout * turnout_adj)
            pred_boxes.append(shares @ T)
            pred_weights.append(expected)
            pred_src.append(shares)
        P = np.array(pred_boxes)          # boxes x parties, shares
        W = np.array(pred_weights)        # expected valid votes per box
        rng = np.random.default_rng(42)
        seat_samples = {n: [] for n in to_names}
        chunk = 40
        for start in range(0, SIMS, chunk):
            k = min(chunk, SIMS - start)
            gamma = rng.gamma(shape=np.maximum(P * alpha, 1e-6), scale=1.0,
                              size=(k, P.shape[0], P.shape[1]))
            sampled = gamma / gamma.sum(axis=2, keepdims=True)
            unc = (sampled * W[None, :, None]).sum(axis=1)  # k x parties
            # Estimator jitter: per-ballot Dirichlet noise alone gives
            # seat bands of +-0-1, which the rehearsal shows is overconfident
            # (the matrix itself is estimated from a partial, non-random
            # count). Re-draw the uncounted aggregate shares from a
            # Dirichlet with a concentration that grows with the counted
            # share, calibrated so the rehearsal bands cover the known
            # full-count result: honest wide bands early, narrow late.
            ALPHA_AGG = max(250.0, 700.0 * counted_share / max(0.02, 1 - counted_share))
            unc_tot = unc.sum(axis=1, keepdims=True)
            g2 = rng.gamma(shape=np.maximum(unc / np.maximum(unc_tot, 1) * ALPHA_AGG, 1e-6), scale=1.0)
            unc = g2 / g2.sum(axis=1, keepdims=True) * unc_tot
            totals = counted_votes[None, :] + unc
            for row_votes in totals:
                votes = {to_names[j]: float(row_votes[j]) for j in range(len(to_names))}
                seats = bader_ofer(votes, agreements=SURPLUS_AGREEMENTS, valid_total=float(row_votes.sum()))
                for n in to_names:
                    seat_samples[n].append(seats[n])
        counted_seats = bader_ofer({to_names[j]: float(counted_votes[j]) for j in range(len(to_names))},
                                   agreements=SURPLUS_AGREEMENTS, valid_total=float(counted_votes.sum()))
        # The headline forecast integer is NOT an average of seat counts:
        # it is a single Bader-Ofer allocation of the projected final
        # votes (counted actuals + expected uncounted). That guarantees a
        # coherent map summing to 120 and threshold-legal values only
        # (a list is at 0 or >=4, never at an impossible 3).
        proj_totals_arr = counted_votes + (P * W[:, None]).sum(axis=0) if len(pred_src) else counted_votes
        proj_seats_map = bader_ofer({to_names[j]: float(proj_totals_arr[j]) for j in range(len(to_names))},
                                    agreements=SURPLUS_AGREEMENTS, valid_total=float(proj_totals_arr.sum()))
        parties_out = []
        for j, n in enumerate(to_names):
            arr = np.array(seat_samples[n])
            parties_out.append({
                "name": n, "seats_now": counted_seats[n], "proj_seats": proj_seats_map[n],
                "counted_votes": int(round(float(counted_votes[j]))),
                "proj_votes": int(round(float(proj_totals_arr[j]))),
                "median": int(np.median(arr)), "p10": int(np.percentile(arr, 10)), "p90": int(np.percentile(arr, 90)),
                "mean": round(float(np.mean(arr)), 2), "median_dec": round(float(np.median(arr)), 2),
                # Full seat distribution over the completions, for the
                # colour-coded density plot in the nowcast (seat -> count).
                "hist": {str(int(s)): int(c) for s, c in zip(*np.unique(arr, return_counts=True))},
                # Most likely exact outcome (mode) -- the headline integer.
                # A rounded mean can land on impossible values (e.g. mean
                # 3.4 for a list that either fails the threshold with 0 or
                # passes with >=4); the mode never does. p_pass is the share
                # of completions in which the list passes the threshold.
                "mode": int(np.bincount(arr).argmax()),
                "p_pass": round(float((arr > 0).mean()), 2),
            })
        parties_out.sort(key=lambda r: -r["median"])
        # Projected final vote transfers: the same T applied to the whole
        # roster. Each K25 source party flows by its OWN row of T
        # (F = diag(origin totals) @ T). Building flows per box as
        # outer(source shares, the box's average destination) instead
        # smears every source in a mixed box across every destination --
        # Haredi voters in a mixed Jerusalem box "flow" to secular lists
        # at the box-average rate -- which looks noisy and unreal.
        # Columns are then scaled so the right-hand nodes equal the
        # projected final totals exactly (counted actuals + predicted
        # uncounted); scaling preserves T's zero cells.
        origin_totals = np.zeros(len(from_names))
        for row in counted_rows:
            st = st26.get(f"{row['k26_name']}|{row['k26_ballot']}")
            if st is None:
                continue
            sh, _ = source_shares(row)
            origin_totals += (st.get("v") or 0) * sh
        if len(pred_src):
            origin_totals += (np.array(pred_src) * W[:, None]).sum(axis=0)
        F = origin_totals[:, None] * T
        proj_totals = proj_totals_arr
        col = F.sum(axis=0)
        F = F * np.divide(proj_totals, col, out=np.zeros_like(col), where=col > 0)[None, :]
        seats_median = {p["name"]: p["proj_seats"] for p in parties_out}
        projected_sankey = {
            "nodes_from": [{"name": n["name"], "symbol": n.get("symbol", ""), "votes": n.get("votes", 0), "color": n.get("color", "#666")} for n in transfer["nodes_from"]],
            "nodes_to": [{"name": n["name"], "symbol": n.get("symbol", ""), "votes": round(float(proj_totals[to_names.index(n["name"])])), "seats": seats_median.get(n["name"], 0), "color": n.get("color", "#666")} for n in transfer["nodes_to"]],
            "transfers": [{"source": from_names[i], "target": to_names[j], "votes": round(float(F[i, j]))}
                          for i in range(len(from_names)) for j in range(len(to_names)) if F[i, j] >= 15000],
            "r_squared": round(float(r2), 4),
        }
        projection = {
            "sims": SIMS, "alpha": alpha, "turnout_adj": round(turnout_adj, 3),
            "uncounted_ballots": len(uncounted_rows),
            "expected_uncounted_votes": round(float(W.sum())),
            "parties": parties_out,
            "blocs": {b: {"proj_seats": sum(proj_seats_map.get(p, 0) for p in ps),
                          "median": int(np.median(_bloc_arr := [sum(seat_samples[p][i] for p in ps if p in seat_samples)
                                                    for i in range(SIMS)])),
                          "mean": round(float(np.mean(_bloc_arr)), 2),
                          "median_dec": round(float(np.median(_bloc_arr)), 2),
                          "p10": int(np.percentile(_bloc_arr, 10)),
                          "p90": int(np.percentile(_bloc_arr, 90))}
                      for b, ps in BLOCS.items()},
            "projected_sankey": projected_sankey,
        }

    return {
        "mode": mode, "estimator": estimator,
        "rehearsal_target": target_share,
        "counted_ballots": len(counted_rows), "roster_ballots": len(roster),
        "geo_uncounted": geo_uncounted, "geo_counted": geo_counted,
        "matched_ballots": len(matched), "r_squared": round(float(r2), 4),
        "counted_k25_share": round(counted_share, 3), "composition_tvd": round(comp_tvd, 3),
        "sector_coverage": sector_rows,
        "checks": checks, "ready": ready,
        "source_origin_votes": {from_names[i]: round(float(origin_votes[i])) for i in range(len(from_names))},
        "projection": projection,
    }


def geo_all():
    """Every K26 ballot box with what the mobile map/sheet needs:
    [name, ballot, lat, lng, winner_idx, winner_pct, voters, eligible,
     turnout, venue, socio_cluster, tsne_x, tsne_y, [[party_idx, pct]...top7]]
    Party indices refer to the returned parties list. Built from tsne_26
    (in a real partial count: counted boxes only) + station coordinates."""
    tsne26 = load("tsne_26.json", {}) or {}
    parties = [{"name": p["name"], "color": p.get("color", "#666")}
               for p in tsne26.get("parties", [])]
    pidx = {p["name"]: i for i, p in enumerate(parties)}
    coords = (load("station_coordinates.json", {}) or {}).get("stations", {})
    socio = load("station_socioeconomic.json", {}) or {}
    map26 = load("map_26.json", {}) or {}
    settle_coords = {normalize_name(s["name"]): (s["lat"], s["lng"])
                     for s in map26.get("settlements", []) if s.get("lat") is not None}
    rows = []
    for s in tsne26.get("stations", []):
        n, b = s["n"], str(s["b"])
        keys = [f"{n}|{b}"] + ([f"{n}|{b}.0"] if "." not in b else [])
        cd = next((coords[k] for k in keys if k in coords), None)
        if cd and cd.get("lat") is not None:
            lat, lng = cd["lat"], cd["lng"]
        elif normalize_name(n) in settle_coords:
            lat, lng = settle_coords[normalize_name(n)]
        else:
            continue
        props = sorted((s.get("p") or {}).items(), key=lambda kv: -kv[1])
        top = [[pidx[name], round(float(pct), 1)] for name, pct in props[:7]
               if name in pidx and pct > 0]
        if not top:
            continue
        se = next((socio[k] for k in keys if k in socio), None)
        rows.append([n, b, round(lat, 5), round(lng, 5), top[0][0], top[0][1],
                     s.get("v", 0), s.get("e", 0), s.get("t", 0), s.get("l", ""),
                     (se or {}).get("cluster"), round(s.get("x", 0), 2),
                     round(s.get("y", 0), 2), top])
    return {"parties": parties, "rows": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target-share", type=float, default=None,
                    help="rehearsal only: rescale the skewed mask so this share of roster ballots is counted")
    ap.add_argument("--out", default="command_center_26.json",
                    help="output filename inside site/data/")
    args = ap.parse_args()
    map25, map26 = load("map_25.json"), load("map_26.json")
    sectors = load("settlement_sectors.json", {"settlements": {}})
    wiki = load("wiki_official_results.json", {})
    status = load("k26_status.json", {"kind": "simulated"})
    names_en = load("settlement_names_en.json", {})
    transfer = load("transfer_25_to_26.json", {"nodes_to": []})
    party_en = {}
    for n in transfer.get("nodes_to", []):
        if n.get("info"):
            party_en[n["name"]] = n["info"].get("name_en") or n["name"]

    out = {
        "meta": {
            "simulated": status.get("kind") == "simulated",
            "status_kind": status.get("kind"),
            "note_he": "כנסת 26 היא תרחיש מדומה — לא תוצאות אמת" if status.get("kind") == "simulated" else "",
        },
        "twelve_knessets": twelve_knessets(map26, sectors),
        "factoids": factoids(map25, map26, sectors, wiki.get("26", []), names_en, party_en),
        "bellwether": bellwether(names_en),
        "nowcast": nowcast(status, sectors, args.target_share),
        "geo_all": geo_all(),
    }
    path = SITE_DATA / args.out
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    nc = out["nowcast"]
    print(f"wrote {path}")
    print(f"  twelve_knessets: {len(out['twelve_knessets'])} slices; factoids: {len(out['factoids'])}; "
          f"bellwether top: {out['bellwether']['leaderboard'][0]['n'] if out['bellwether']['leaderboard'] else '-'}")
    print(f"  nowcast[{nc['mode']}]: counted {nc['counted_ballots']}/{nc['roster_ballots']}, matched {nc['matched_ballots']}, "
          f"R2={nc['r_squared']}, share={nc['counted_k25_share']}, tvd={nc['composition_tvd']}, ready={nc['ready']}")
    for c in nc["checks"]:
        print(f"    [{'OK ' if c['ok'] else 'FAIL'}] {c['id']}: {c['value']} (threshold {c['threshold']})")
    if nc["projection"]:
        print("  projection medians:", {p["name"]: p["median"] for p in nc["projection"]["parties"] if p["median"]})


if __name__ == "__main__":
    main()
