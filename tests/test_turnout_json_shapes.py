"""Map-service JSON shapes for the election-day turnout snapshot.

    python tests/test_turnout_json_shapes.py

The daytime turnout source is expected to be JSON inside the CEC map
service (mapvotes.bechirot.gov.il), not a single CSV. Each plausible
shape -- GovMap features dict, GeoJSON/ArcGIS features, a bare record
array, {columns, rows} -- must land in the right index of
generate_turnout_day_data.snapshot_records(): per-ballot rows in the
ballot indexes, settlement aggregates in the settlement indexes as a
turnout rate.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import generate_turnout_day_data as g

results = []


def report(name, ok, evidence=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({evidence})" if evidence and not ok else ""))


tmp = Path(tempfile.mkdtemp())


def snap(name, payload):
    p = tmp / name
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return g.snapshot_records(str(p))


# 1. GovMap-style: features dict keyed by settlement code, Hebrew fields
by_code, _, settle, _ = snap("govmap.json", {
    "version": 2, "generated": "2026-10-27T10:00:00Z",
    "features": {
        "3000": {"שם ישוב": "ירושלים", "בזב": 1000, "מצביעים": 400},
        "5000": {"שם ישוב": "תל אביב יפו", "בזב": 900, "מצביעים": 270},
    }})
report("govmap features dict -> settlement rates",
       not by_code and abs(settle["3000"]["rate"] - 0.4) < 1e-9 and abs(settle["5000"]["rate"] - 0.3) < 1e-9,
       str(settle))

# 2. GeoJSON features with Hebrew per-ballot properties
by_code, _, settle, _ = snap("geojson.json", {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"סמל ישוב": 3000, "קלפי": "12.1", "בזב": 600, "מצביעים": 222}},
        {"type": "Feature", "properties": {"סמל ישוב": 3000, "קלפי": "12.2", "בזב": 610, "מצביעים": 200}},
    ]})
report("geojson features -> per-ballot index",
       by_code.get(("3000", "12.1"), {}).get("voters") == 222.0 and not settle, str(by_code))

# 3. ArcGIS features, English fields, turnout percentage only
by_code, _, _, _ = snap("arcgis.json", {
    "features": [
        {"attributes": {"cityID": 5000, "BallotNumber": "3", "eligibleVoters": 800, "votingPercentage": 35}},
    ]})
report("arcgis attributes + pct -> voters derived",
       by_code.get(("5000", "3"), {}).get("voters") == 280.0, str(by_code))

# 4. Bare record array, English per-ballot fields
by_code, by_name, _, _ = snap("array.json", [
    {"settlement_code": "3000", "settlementName": "ירושלים", "ballot": "1", "eligible": 500, "voters": 125},
])
report("record array -> per-ballot by code and name",
       by_code.get(("3000", "1"), {}).get("voters") == 125.0 and ("ירושלים", "1") in by_name,
       f"{by_code} {by_name}")

# 5. {columns, rows} regression
by_code, _, _, _ = snap("colsrows.json", {
    "columns": ["סמל ישוב", "קלפי", "בזב", "מצביעים"],
    "rows": [[3000, "7", 700, 350]],
})
report("{columns,rows} still works", by_code.get(("3000", "7"), {}).get("voters") == 350.0, str(by_code))

# 6. Settlement aggregate by name, percentage only
_, _, _, settle_by_name = snap("settle.json", [
    {"settlementName": "ירושלים", "turnoutPct": 41.5},
])
report("settlement pct-only -> rate by name",
       abs(settle_by_name.get("ירושלים", {}).get("rate", 0) - 0.415) < 1e-9, str(settle_by_name))

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
