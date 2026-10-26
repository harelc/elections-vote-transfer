#!/usr/bin/env python3
"""Election-day turnout view for k26.html -> site/data/turnout_day_26.json

Runs BEFORE any K26 results exist. The CEC *may* publish turnout at
individual-ballot resolution a few times over election day; this script
ingests one such snapshot and joins every K26 roster ballot to:

  * its crosswalked K25 twin (data/k25_k26_ballot_union.csv, decisions
    id / id_dot1 / venue / coord -- the same pairing the transfer fit uses),
    whose final K25 voting pattern is known from tsne_25.json, and
  * its settlement sector taxonomy (settlement_sectors.json) and
    per-station socioeconomic cluster (station_socioeconomic.json).

The output carries no K26 result information at all -- only how many
people have voted so far, where, and how that compares with the K25 twin
ballot. Group analyses therefore answer "who is turning out so far?"
in K25 terms: by the twin's winning party, bloc, stronghold (>=40% for a
party), sector / form / district / socioeconomic cluster, and the twin's
own K25 turnout band. `pace` everywhere is voters-so-far divided by the
twin group's final K25 voters: 0.62 means the group has already cast
62% as many ballots as it cast in all of K25 (on matched ballots).

Snapshot format (CEC shape, CSV or a {columns, rows} JSON like the
results snapshots refresh_k26.py accepts). Recognised columns, Hebrew
or English: settlement code (סמל ישוב), settlement name (שם ישוב),
ballot (קלפי / מספר קלפי), eligible (בזב), voters (מצביעים), or a
turnout percentage (אחוז הצבעה / turnout). Rows are matched to the
roster by (code, ballot), falling back to (normalised name, ballot).

Usage:
    # live snapshot(s); history accumulates across runs (same --out)
    python generate_turnout_day_data.py --snapshot cec_turnout_1200.csv --as-of 2026-10-27T12:05+02:00
    python generate_turnout_day_data.py --snapshot cec_turnout_1700.csv --as-of 2026-10-27T17:05+02:00

    # rehearsal (no CEC file yet): synthetic mid-day snapshot derived
    # from the simulated ballot26.csv final turnout, with sector lags
    python generate_turnout_day_data.py --rehearsal --target-turnout 0.38 --as-of 2026-10-27T15:00+02:00

The k26.html view is optional: it activates with ?turnout=1, or
automatically when k26_status.json reports kind="turnout" (the day
flow), and deactivates with ?turnout=0. Once results flow in
(partial/official) the regular command center takes over again.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SITE_DATA = ROOT / "site" / "data"
UNION = ROOT / "data" / "k25_k26_ballot_union.csv"
MATCHED_DECISIONS = ("id", "id_dot1", "venue", "coord")

from generate_map_data import normalize_name

# K25 blocs in party *names* (tsne_25 proportions are keyed by name).
K25_BLOCS = {
    "right": ["הליכוד", "הציונות הדתית", "ש״ס", "יהדות התורה"],
    "leftcenter": ["יש עתיד", "המחנה הממלכתי", "ישראל ביתנו", "העבודה", "מרצ", "הבית היהודי"],
    "arab": ["רע״ם", "חד״ש-תע״ל", "בל״ד"],
}
BLOC_OF = {p: b for b, ps in K25_BLOCS.items() for p in ps}
BLOC_LABELS = {
    "right": ("גוש הימין (25)", "Right bloc (K25)"),
    "leftcenter": ("גוש מרכז־שמאל (25)", "Centre-left bloc (K25)"),
    "arab": ("מפלגות ערביות (25)", "Arab parties (K25)"),
    "other": ("אחר / לא מסווג", "Other / unclassified"),
}
POP_LABELS = {
    "jewish": ("יישובים יהודיים", "Jewish localities"), "arab": ("יישובים ערביים", "Arab localities"),
    "bedouin": ("יישובים בדואיים", "Bedouin localities"), "druze": ("יישובים דרוזיים", "Druze localities"),
    "circassian": ("יישובים צ׳רקסיים", "Circassian localities"),
    "mixed": ("ערים מעורבות", "Mixed cities"), "unknown": ("לא ידוע", "Unknown"),
}
FORM_LABELS = {
    "city": ("ערים", "Cities"), "local_council": ("מועצות מקומיות", "Local councils"),
    "kibbutz": ("קיבוצים", "Kibbutzim"), "moshav": ("מושבים", "Moshavim"),
    "moshav_shitufi": ("מושבים שיתופיים", "Cooperative moshavim"), "moshava": ("מושבות", "Moshavot"),
    "community": ("יישובים קהילתיים", "Community settlements"),
    "regional": ("יישובי מועצות אזוריות", "Regional-council localities"),
    "locality": ("יישובים", "Localities"), "village": ("כפרים", "Villages"),
    "institution": ("מוסדות ומחנות", "Institutions and camps"),
    "unknown": ("לא ידוע", "Unknown"),
}
OTHER_LABEL = ("אחר / לא מסווג", "Other / unclassified")
UNKNOWN_LABEL = ("לא ידוע", "Unknown")
STRONGHOLD_MIN = 40.0  # K25 party share (%) in the twin for "stronghold"
MIN_GROUP_ELIGIBLE = 3000


def load(name, default=None):
    p = SITE_DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def norm_ballot(b):
    b = str(b or "").strip()
    return b[:-2] if b.endswith(".0") else b


# --------------------------------------------------------------- snapshots
# The daytime turnout source is expected to be a JSON payload inside
# the CEC map service (mapvotes.bechirot.gov.il), not a CSV file, so
# the aliases cover map-service style field names (GovMap / ArcGIS /
# GeoJSON) as well as the CEC CSV headers.
ALIASES = {
    "code": ("סמל ישוב", "סמל_ישוב", "settlement_code", "settlementCode", "cityID", "cityId",
             "yishuv_code", "code", "סמל יישוב", "id"),
    "name": ("שם ישוב", "שם_ישוב", "settlement", "settlementName", "cityName", "name", "שם יישוב"),
    "ballot": ("קלפי", "מספר קלפי", "ballot", "ballot_number", "BallotNumber", "ballotNumber",
               "kalpi", "stationNumber", "station_number"),
    "eligible": ("בזב", "בז\"ב", "eligible", "eligible_voters", "eligibleVoters", "numEligible",
                 "totalEligible", "electors", "בוחרים"),
    "voters": ("מצביעים", "voters", "voted", "cast", "votersCount", "numVoters", "actualVoters",
               "votedCount", "מספר מצביעים", "הצביעו"),
    "turnout": ("אחוז הצבעה", "אחוז_הצבעה", "turnout", "turnout_pct", "turnoutPct", "pct",
                "votingPercentage", "voting_percent", "percentage", "אחוז מצביעים", "שיעור הצבעה"),
}

# Dict keys under which a map-service JSON nests its record collection.
RECORD_CONTAINERS = ("features", "rows", "records", "data", "stations", "items", "results")


def json_rows(data):
    """Any plausible map-service JSON -> flat row dicts.

    Handles {columns, rows}; a bare record array; records nested under
    a RECORD_CONTAINERS key; GeoJSON/ArcGIS features (properties /
    attributes are flattened); and a GovMap-style features dict keyed
    by settlement code (the key becomes the code when the record has
    none). Field *names* are resolved later, by ALIASES.
    """
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "columns" in data and "rows" in data:
        cols = [str(c).strip() for c in data["columns"]]
        return [{c: (str(v) if v is not None else "") for c, v in zip(cols, row)} for row in data["rows"]]
    elif isinstance(data, dict):
        items = None
        for key in RECORD_CONTAINERS:
            if key in data:
                items = data[key]
                break
        if items is None:
            # A bare {code: record} map, GovMap without the wrapper.
            items = data
        if isinstance(items, dict):
            rows = []
            for key, rec in items.items():
                if isinstance(rec, dict):
                    rec = dict(rec)
                    if not any(a in rec for a in ALIASES["code"]):
                        rec["סמל ישוב"] = str(key)
                    rows.append(rec)
            return rows
        if not isinstance(items, list):
            return []
    else:
        return []
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rec = None
        for wrap in ("properties", "attributes", "fields"):
            if isinstance(item.get(wrap), dict):
                rec = dict(item[wrap])
                break
        rows.append(rec if rec is not None else dict(item))
    return rows


def read_snapshot(path):
    """CEC CSV (utf-8-sig / cp1255) or map-service JSON -> row dicts."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1255")
    if text.lstrip().startswith(("{", "[")):
        return [{str(k).strip(): (str(v) if v is not None else "") for k, v in row.items()}
                for row in json_rows(json.loads(text))]
    if text.lstrip().startswith("<"):
        # Generic XML adapter (the CEC interface is not yet known): row
        # elements are the repeated children of the root; fields come from
        # attributes and child elements. Adjust here when the real feed
        # shape is published -- this is the single parsing seam.
        import xml.etree.ElementTree as ET
        root = ET.fromstring(text)
        containers = [root] + [el for el in root if len(el)]
        rows = []
        for parent in containers:
            groups = {}
            for child in parent:
                groups.setdefault(child.tag, []).append(child)
            repeated = max(groups.values(), key=len) if groups else []
            if len(repeated) >= 2:
                for el in repeated:
                    rec = {str(k): str(v) for k, v in el.attrib.items()}
                    for sub in el:
                        if sub.text is not None:
                            rec[sub.tag] = sub.text.strip()
                    rows.append(rec)
                if rows:
                    return rows
        return rows
    return [{(k or "").strip(): (v or "") for k, v in row.items()}
            for row in csv.DictReader(io.StringIO(text))]


def snapshot_records(path):
    """Normalise a snapshot to per-ballot + per-settlement indexes.

    Returns (by_code, by_name, settle_by_code, settle_by_name). A row
    with a ballot number lands in the per-ballot indexes; a row without
    one (a map service may publish settlement aggregates only) lands in
    the settlement indexes as a turnout *rate*, which main() applies
    to each roster ballot of that settlement by its eligible count.
    """
    by_code, by_name, settle_by_code, settle_by_name = {}, {}, {}, {}
    unmatched_cols = None
    for row in read_snapshot(path):
        get = {}
        for field, aliases in ALIASES.items():
            for a in aliases:
                if a in row and str(row[a]).strip() != "":
                    get[field] = str(row[a]).strip()
                    break
        if "code" not in get and "name" not in get:
            unmatched_cols = list(row.keys())
            continue
        elig = float(get["eligible"]) if get.get("eligible") else None
        if get.get("voters"):
            voters = float(get["voters"])
        elif get.get("turnout") and elig:
            voters = round(elig * float(get["turnout"].replace("%", "")) / 100.0)
        else:
            voters = None
        code = str(get["code"]).strip() if get.get("code") else None
        name = normalize_name(get["name"]) if get.get("name") else None
        if "ballot" in get:
            if voters is None:
                continue
            ballot = norm_ballot(get["ballot"])
            rec = {"eligible": elig, "voters": voters}
            if code:
                by_code[(code, ballot)] = rec
            if name:
                by_name[(name, ballot)] = rec
        else:
            rate = (voters / elig) if (voters is not None and elig) else \
                (float(get["turnout"].replace("%", "")) / 100.0 if get.get("turnout") else None)
            if rate is None:
                continue
            rec = {"eligible": elig, "voters": voters, "rate": rate}
            if code:
                settle_by_code[code] = rec
            if name:
                settle_by_name[name] = rec
    if unmatched_cols and not by_code and not by_name and not settle_by_code and not settle_by_name:
        raise SystemExit(f"snapshot has no recognisable ballot/code columns; saw {unmatched_cols}")
    return by_code, by_name, settle_by_code, settle_by_name


def rehearsal_records(target_turnout, seed=42):
    """Synthetic mid-day snapshot from the simulated ballot26.csv.

    Each ballot's final simulated turnout is scaled by a national
    progress factor plus a sector lag (Haredi and Arab/Bedouin ballots
    report slower in this scenario) and deterministic hash noise. This
    is a rehearsal of the plumbing, not a forecast of election day.
    """
    df_rows = read_snapshot(ROOT / "ballot26.csv")
    sectors = (load("settlement_sectors.json", {"settlements": {}}) or {}).get("settlements", {})
    finals = []
    for row in df_rows:
        elig = float(row.get("בזב") or 0)
        voters = float(row.get("מצביעים") or 0)
        if elig <= 0:
            continue
        finals.append((row, elig, voters))
    final_turnout = sum(v for _, _, v in finals) / max(1, sum(e for _, e, _ in finals))
    base_progress = min(1.0, target_turnout / final_turnout) if final_turnout else 0.0
    by_code = {}
    for row, elig, voters in finals:
        code = str(row.get("סמל ישוב") or "").strip()
        ballot = norm_ballot(row.get("קלפי"))
        noise = 0.92 + 0.16 * (int(hashlib.sha256(f"{code}|{ballot}".encode()).hexdigest()[:6], 16) % 1000) / 1000
        sec = sectors.get(normalize_name(row.get("שם ישוב") or ""), {})
        lag = 0.82 if sec.get("haredi") else 0.78 if sec.get("population") in ("arab", "bedouin") else 0.9 if sec.get("population") == "druze" else 1.0
        cast = int(round(voters * min(1.0, base_progress * noise * lag)))
        by_code[(code, ballot)] = {"eligible": elig, "voters": float(cast)}
    return by_code, {}, {}, {}


# ------------------------------------------------------------------ groups
def agg():
    return {"ballots": 0, "eligible": 0.0, "voters": 0.0, "k25_voters": 0.0, "k25_eligible": 0.0}


def add(a, elig, voters, k25_voters, k25_eligible):
    a["ballots"] += 1
    a["eligible"] += elig
    a["voters"] += voters
    a["k25_voters"] += k25_voters
    a["k25_eligible"] += k25_eligible


def finish(a):
    elig, k25e = a["eligible"], a["k25_eligible"]
    return {
        "ballots": a["ballots"], "eligible": round(a["eligible"]), "voters": round(a["voters"]),
        "turnout": round(100 * a["voters"] / elig, 1) if elig else 0.0,
        "k25_turnout": round(100 * a["k25_voters"] / k25e, 1) if k25e else None,
        # pace: share of the group's final K25 voters already cast today
        "pace": round(a["voters"] / a["k25_voters"], 3) if a["k25_voters"] else None,
    }


def group_rows(groups, labels, total_voters):
    rows = []
    for gid, a in groups.items():
        if a["eligible"] < MIN_GROUP_ELIGIBLE:
            continue
        r = finish(a)
        he, en_ = labels(gid) if callable(labels) else labels.get(gid, (str(gid), str(gid)))
        r.update({"id": str(gid), "label_he": he, "label_en": en_,
                  "share_of_voters": round(100 * a["voters"] / total_voters, 1) if total_voters else 0.0})
        rows.append(r)
    return sorted(rows, key=lambda r: -r["turnout"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snapshot", action="append", default=[],
                    help="CEC turnout snapshot (CSV or {columns,rows} JSON); repeatable, last one is current")
    ap.add_argument("--as-of", default=None, help="ISO timestamp of the current snapshot")
    ap.add_argument("--sha256", default=None, help="sha256 of the source snapshot file (recorded for poller dedupe)")
    ap.add_argument("--rehearsal", action="store_true", help="build a synthetic snapshot from ballot26.csv")
    ap.add_argument("--target-turnout", type=float, default=0.38, help="rehearsal national turnout so far")
    ap.add_argument("--out", default="turnout_day_26.json")
    args = ap.parse_args()
    if not args.snapshot and not args.rehearsal:
        raise SystemExit("pass --snapshot FILE (live CEC turnout) or --rehearsal")

    tsne25 = load("tsne_25.json")
    map25 = load("map_25.json", {"settlements": []})
    sectors = (load("settlement_sectors.json", {"settlements": {}}) or {}).get("settlements", {})
    socio = load("station_socioeconomic.json", {}) or {}
    coords = (load("station_coordinates.json", {}) or {}).get("stations", {})
    st25 = {f"{s['n']}|{norm_ballot(s['b'])}": s for s in tsne25["stations"]}
    parties25 = [p["name"] for p in tsne25["parties"]]
    color25 = {p["name"]: p.get("color", "#666") for p in tsne25["parties"]}
    by_settle25 = {s["name"]: s for s in map25["settlements"]}

    # --- roster (K26 boxes) + crosswalk to K25 twins
    roster = []
    with UNION.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["decision"] == "k25_only" or not row["k26_name"]:
                continue
            roster.append(row)

    # --- snapshot lookup
    kind = "rehearsal" if args.rehearsal else "live"
    if args.rehearsal:
        by_code, by_name, settle_by_code, settle_by_name = rehearsal_records(args.target_turnout)
    else:
        by_code, by_name, settle_by_code, settle_by_name = snapshot_records(args.snapshot[-1])

    stations, unmatched, settlement_level = [], 0, 0
    match_counts = defaultdict(int)
    groups = {k: defaultdict(agg) for k in
              ("k25_winner", "k25_bloc", "stronghold", "population", "form", "district", "socio", "k25_turnout_band")}
    total = agg()
    settle_agg = defaultdict(agg)
    settle_meta = {}

    for row in roster:
        name = normalize_name(row["k26_name"] or "")
        ballot = norm_ballot(row["k26_ballot"])
        rec = by_code.get((str(row["k26_code"]).strip(), ballot)) or by_name.get((name, ballot))
        if rec is None:
            # Settlement-aggregate snapshot (map service with no ballot
            # resolution): apply the settlement turnout rate to this
            # ballot's roster eligible count.
            srec = settle_by_code.get(str(row["k26_code"]).strip()) or settle_by_name.get(name)
            roster_elig = float(row["k26_eligible"] or 0)
            if srec is not None and srec.get("rate") is not None and roster_elig:
                rec = {"eligible": roster_elig, "voters": roster_elig * srec["rate"],
                       "settlement_level": True}
        if rec is None:
            unmatched += 1
            continue
        elig = rec["eligible"] or float(row["k26_eligible"] or 0)
        if not elig:
            unmatched += 1
            continue
        voters = float(rec["voters"])
        if rec.get("settlement_level"):
            settlement_level += 1

        # K25 twin pattern: crosswalked ballot, else settlement aggregate.
        # The match *kind* is part of the output (match field): how this
        # box was paired says how much the K25 comparison can be trusted.
        #   id        same settlement code + ballot number
        #   id_dot1   K26 x.1 paired to the K25 base ballot x
        #   venue     same distinctive venue name in the settlement,
        #             ballots paired in ballot-number order
        #   coord     mutual nearest venue-grade pins within 150 m
        #   settlement no paired ballot; the settlement's K25 aggregate,
        #             apportioned by this box's eligible count
        #   none      no K25 baseline at all
        twin = None
        if row["decision"] in MATCHED_DECISIONS and row["k25_name"]:
            twin = st25.get(f"{row['k25_name']}|{norm_ballot(row['k25_ballot'])}") \
                or st25.get(f"{normalize_name(row['k25_name'])}|{norm_ballot(row['k25_ballot'])}")
        props, k25_voters, k25_elig = {}, 0.0, 0.0
        if twin is not None:
            match_kind = row["decision"]
            props = twin.get("p") or {}
            k25_voters, k25_elig = float(twin.get("v") or 0), float(twin.get("e") or 0)
        elif name in by_settle25:
            match_kind = "settlement"
            s = by_settle25[name]
            props = s.get("proportions") or {}
            # settlement-level K25 baseline, apportioned by this box's size
            share = elig / (s.get("eligible") or elig or 1)
            k25_voters, k25_elig = (s.get("voters") or 0) * share, (s.get("eligible") or 0) * share
        else:
            match_kind = "none"
        match_counts[match_kind] += 1
        winner = max(props.items(), key=lambda kv: kv[1])[0] if props else None
        k25_turnout = (100 * k25_voters / k25_elig) if k25_elig else None

        try:
            lat = float(row["k26_lat"]) if row.get("k26_lat") else None
            lng = float(row["k26_lng"]) if row.get("k26_lng") else None
        except ValueError:
            lat = lng = None
        if lat is None:
            cd = coords.get(f"{name}|{ballot}") or {}
            lat, lng = cd.get("lat"), cd.get("lng")
        sec = sectors.get(name, {})
        soc = (socio.get(f"{name}|{ballot}") or socio.get(f"{name}|{ballot}.0") or {}).get("cluster")
        if soc is None and name in by_settle25:
            soc = by_settle25[name].get("cluster")

        add(total, elig, voters, k25_voters, k25_elig)
        dims = {
            "k25_winner": winner or "other",
            "k25_bloc": BLOC_OF.get(winner or "", "other"),
            "population": sec.get("population") or "unknown",
            "form": sec.get("form") or "unknown",
            "district": sec.get("district") or "unknown",
            "socio": f"cluster_{soc}" if soc else "unknown",
            "k25_turnout_band": ("<40" if k25_turnout is not None and k25_turnout < 40 else
                                 "40-55" if k25_turnout is not None and k25_turnout < 55 else
                                 "55-65" if k25_turnout is not None and k25_turnout < 65 else
                                 "65-75" if k25_turnout is not None and k25_turnout < 75 else
                                 "75+" if k25_turnout is not None else "unknown"),
        }
        for dim, gid in dims.items():
            add(groups[dim][gid], elig, voters, k25_voters, k25_elig)
        for party, pct in props.items():
            if pct >= STRONGHOLD_MIN:
                add(groups["stronghold"][party], elig, voters, k25_voters, k25_elig)
        add(settle_agg[name], elig, voters, k25_voters, k25_elig)
        settle_meta[name] = {"district": sec.get("district"), "population": sec.get("population")}

        # fields: see meta.station_fields in the output document
        try:
            match_m = round(float(row["distance_m"]), 1) if twin is not None and row.get("distance_m") else None
        except ValueError:
            match_m = None
        stations.append([name, ballot, round(lat, 5) if lat else None, round(lng, 5) if lng else None,
                         round(elig), round(voters), round(100 * voters / elig, 1),
                         round(k25_turnout, 1) if k25_turnout is not None else None,
                         round(voters / k25_voters, 3) if k25_voters else None,
                         winner, dims["k25_bloc"], dims["population"], dims["district"], soc,
                         1 if twin is not None else 0,
                         match_kind,
                         row["k25_name"] if twin is not None else None,
                         norm_ballot(row["k25_ballot"]) if twin is not None else None,
                         match_m])

    total_voters = total["voters"] or 1
    nat = finish(total)
    nat.update({
        "delta_vs_k25_final_pp": round(nat["turnout"] - nat["k25_turnout"], 1) if nat["k25_turnout"] is not None else None,
        "remaining_voters": round(total["eligible"] - total["voters"]),
        "matched_ballots": sum(1 for s in stations if s[14]),
        "settlement_level_ballots": settlement_level,
        "match_kinds": dict(match_counts),
        "reported_ballots": len(stations), "roster_ballots": len(roster), "unmatched_rows": unmatched,
        "eligible_coverage": round(total["eligible"] / sum(float(r["k26_eligible"] or 0) for r in roster), 3)
        if roster else 0.0,
    })

    def settle_rows(key, reverse, limit=12, min_eligible=800):
        rows = []
        for name, a in settle_agg.items():
            if a["eligible"] < min_eligible:
                continue
            r = finish(a)
            r.update({"name": name, **settle_meta.get(name, {}),
                      "remaining": round(a["eligible"] - a["voters"])})
            rows.append(r)
        rows.sort(key=key, reverse=reverse)
        return rows[:limit]

    out_path = SITE_DATA / args.out
    history = []
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
            history = [h for h in prev.get("history", []) if h.get("as_of") != args.as_of]
            # prev.history normally already ends with prev's own entry;
            # append it only if it somehow is not there (no duplicates --
            # a duplicate inflates the count and breaks the delta display).
            seen = {h.get("as_of") for h in history}
            if prev.get("meta", {}).get("as_of") and prev["meta"]["as_of"] not in seen and prev["meta"]["as_of"] != args.as_of:
                history.append({"as_of": prev["meta"]["as_of"], "national": prev.get("national")})
        except Exception:
            history = []
    history = (history + [{"as_of": args.as_of, "national": nat}])[-12:]

    out = {
        "meta": {"kind": kind, "as_of": args.as_of, "source_sha256": args.sha256,
                 "note_he": "אחוזי הצבעה ביום הבחירות — לפני תוצאות. ההשוואות הן לקלפי התאומה בבחירות 25, לא לתוצאת 26."
                 if kind == "live" else "חזרה (סימולציה): אחוזי הצבעה מדומים ליום הבחירות, לפני תוצאות.",
                 "note_en": "Election-day turnout — before any results. Comparisons are to the matched K25 twin ballot, not to a K26 result."
                 if kind == "live" else "Rehearsal (simulated): synthetic election-day turnout, before any results.",
                 "station_fields": ["name", "ballot", "lat", "lng", "eligible", "voters", "turnout",
                                    "k25_turnout", "pace", "k25_winner", "bloc", "population", "district", "socio", "matched",
                                    "match", "k25_name", "k25_ballot", "match_m"]},
        "national": nat,
        "history": history,
        "groups": {
            "k25_winner": group_rows(groups["k25_winner"], lambda g: OTHER_LABEL if g == "other" else (g, g), total_voters),
            "k25_bloc": group_rows(groups["k25_bloc"], lambda g: BLOC_LABELS.get(g, (g, g)), total_voters),
            "stronghold": group_rows(groups["stronghold"], lambda g: (g, g), total_voters),
            "population": group_rows(groups["population"], lambda g: POP_LABELS.get(g, (g, g)), total_voters),
            "form": group_rows(groups["form"], lambda g: FORM_LABELS.get(g, (g, g)), total_voters),
            "district": group_rows(groups["district"], lambda g: UNKNOWN_LABEL if g == "unknown" else (g, g), total_voters),
            "socio": group_rows(groups["socio"], lambda g: ({"cluster_1": ("אשכול 1", "Cluster 1"), "unknown": UNKNOWN_LABEL}.get(g) or
                                                             ((f"אשכול {g.split('_')[-1]}", f"Cluster {g.split('_')[-1]}") if g.startswith("cluster_") else (g, g))), total_voters),
            "k25_turnout_band": group_rows(groups["k25_turnout_band"], lambda g: ("שיעור הצבעה ב־25: לא ידוע", "K25 turnout rate: unknown") if g == "unknown" else (f"שיעור הצבעה ב־25: {g}%", f"K25 turnout rate: {g}%"), total_voters),
        },
        "party_colors_25": color25,
        "settlements": {
            "highest_turnout": settle_rows(lambda r: r["turnout"], True),
            "lowest_turnout": settle_rows(lambda r: r["turnout"], False),
            "fastest_pace": settle_rows(lambda r: (r["pace"] is not None, r["pace"] or 0), True),
            "most_remaining": settle_rows(lambda r: r["remaining"], True),
        },
        "stations": stations,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path}: kind={kind} as_of={args.as_of} stations={len(stations)}/{len(roster)} "
          f"turnout={nat['turnout']}% pace_vs_k25={nat['pace']} matched={nat['matched_ballots']}")


if __name__ == "__main__":
    main()
