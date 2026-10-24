#!/usr/bin/env python3
"""
Add district (מחוז) + subdistrict (נפה) to every settlement in
site/data/settlement_sectors.json.

Source: Population and Immigration Authority locality list on data.gov.il
("רשימת ישובים בישראל - מתעדכן", resource 5c78e9fa-c2e2-4771-93ff-7f400a12f7ba),
which gives, per settlement code (סמל ישוב): name + subdistrict code/name.
Every CBS subdistrict belongs to exactly one district, so the district is a
fixed mapping from the subdistrict (NAFA_TO_DISTRICT below; West Bank
subdistricts 71-77 -> "יהודה ושומרון", the CBS Judea and Samaria area).

Our settlement names -> settlement codes come from the CEC ballot CSVs
themselves (שם ישוב / סמל ישוב in ballot25.csv + ballot26.csv), with the
CBS 2011 statistical-zones file (settlement_code per settlement) as backup.
Names are normalised with generate_map_data.normalize_name, the same
normalisation the map/tsne files use.

Fallbacks for settlements with no code match, in order:
  1. normalised-name match against the Authority list itself;
  2. nearest already-classified settlement by map coordinates (< 25 km),
     marked source="nearest" -- districts are large, so a near neighbour is
     decisive except exactly on a border; these are worth a manual glance.

Output: district/subdistrict fields merged into settlement_sectors.json
(fields: district, district_code?, subdistrict, district_source) plus a
coverage report on stdout. Static data -- rerun only when the locality
list changes.
"""
import csv
import io
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from generate_map_data import normalize_name  # noqa: E402

DATASTORE_URL = (
    "https://data.gov.il/api/3/action/datastore_search"
    "?resource_id=5c78e9fa-c2e2-4771-93ff-7f400a12f7ba&limit=5000"
)

# CBS subdistrict (נפה) -> district (מחוז). Fixed administrative geography.
NAFA_TO_DISTRICT = {
    "ירושלים": "ירושלים",
    "צפת": "הצפון", "כנרת": "הצפון", "עפולה": "הצפון",
    "עכו": "הצפון", "נצרת": "הצפון", "גולן": "הצפון",
    "חיפה": "חיפה", "חדרה": "חיפה",
    "השרון": "המרכז", "פתח תקווה": "המרכז", "רמלה": "המרכז", "רחובות": "המרכז",
    "תל אביב": "תל אביב", "רמת גן": "תל אביב", "חולון": "תל אביב",
    "אשקלון": "הדרום", "באר שבע": "הדרום",
    # West Bank subdistricts (Population Authority codes 71-77)
    "ג'נין": "יהודה ושומרון", "שכם": "יהודה ושומרון", "טול כרם": "יהודה ושומרון",
    "ראמאללה": "יהודה ושומרון", "ירדן )יריחו(": "יהודה ושומרון",
    "בית לחם": "יהודה ושומרון", "חברון": "יהודה ושומרון",
}
DISTRICT_EN = {
    "ירושלים": "Jerusalem", "הצפון": "North", "חיפה": "Haifa",
    "המרכז": "Center", "תל אביב": "Tel Aviv", "הדרום": "South",
    "יהודה ושומרון": "Judea and Samaria",
}


def load_authority_records():
    with urllib.request.urlopen(DATASTORE_URL, timeout=60) as resp:
        data = json.load(resp)
    return data["result"]["records"]


def name_to_code_from_ballots():
    """normalised settlement name -> CEC/CBS settlement code, from the
    ballot CSVs (they carry both שם ישוב and סמל ישוב per ballot row)."""
    out = {}
    for fname in ("ballot25.csv", "ballot26.csv"):
        path = ROOT / fname
        if not path.exists():
            continue
        raw = path.read_bytes()
        enc = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "iso-8859-8"
        with io.StringIO(raw.decode(enc)) as fh:
            for row in csv.DictReader(fh):
                name, code = row.get("שם ישוב"), row.get("סמל ישוב")
                if name and code:
                    out.setdefault(normalize_name(name.strip()), str(code).strip())
    return out


def name_to_code_from_zones():
    out = {}
    zones = json.loads((ROOT / "site/data/statistical_zones.json").read_text())
    for z in zones.get("zones", {}).values():
        if z.get("settlement") and z.get("settlement_code"):
            out.setdefault(normalize_name(z["settlement"]), str(z["settlement_code"]))
    return out


def haversine_km(lat1, lng1, lat2, lng2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lng2 - lng1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def main():
    records = load_authority_records()
    by_code, by_name = {}, {}
    for r in records:
        code = str(r["סמל_ישוב"]).strip()
        nafa = (r["שם_נפה"] or "").strip()
        district = NAFA_TO_DISTRICT.get(nafa)
        if not district:
            print(f"WARNING: unmapped subdistrict {nafa!r} (code {r['סמל_נפה']})")
            continue
        entry = {"district": district, "district_en": DISTRICT_EN[district],
                 "subdistrict": nafa}
        by_code[code] = entry
        by_name.setdefault(normalize_name((r["שם_ישוב"] or "").strip()), entry)
    print(f"authority list: {len(records)} localities, {len(by_code)} mapped")

    code_of = name_to_code_from_ballots()
    for name, code in name_to_code_from_zones().items():
        code_of.setdefault(name, code)

    sectors_path = ROOT / "site/data/settlement_sectors.json"
    sectors = json.loads(sectors_path.read_text())
    settlements = sectors["settlements"]

    map26 = json.loads((ROOT / "site/data/map_26.json").read_text())
    coords = {s["name"]: (s["lat"], s["lng"]) for s in map26["settlements"]
              if s.get("lat") is not None}

    stats = {"code": 0, "name": 0, "nearest": 0, "missing": 0}
    classified = {}  # name -> (entry, lat, lng)
    missing = []
    for name, entry in settlements.items():
        hit, source = None, None
        code = code_of.get(name)
        if code and code in by_code:
            hit, source = by_code[code], "code"
        elif name in by_name:
            hit, source = by_name[name], "name"
        if hit:
            entry.update(hit, district_source=source)
            stats[source] += 1
            if name in coords:
                classified[name] = (hit, *coords[name])
        else:
            missing.append(name)

    for name in missing:
        entry = settlements[name]
        if name not in coords:
            stats["missing"] += 1
            continue
        lat, lng = coords[name]
        best, best_d = None, 1e9
        for other, (hit, olat, olng) in classified.items():
            d = haversine_km(lat, lng, olat, olng)
            if d < best_d:
                best, best_d = hit, d
        if best and best_d <= 25:
            entry.update(best, district_source=f"nearest:{best_d:.1f}km")
            stats["nearest"] += 1
        else:
            stats["missing"] += 1

    sectors_path.write_text(json.dumps(sectors, ensure_ascii=False, indent=1))
    from collections import Counter
    dist_counts = Counter(e["district"] for e in settlements.values() if e.get("district"))
    print(f"settlements: {len(settlements)}  by source: {stats}")
    print("by district:", dict(dist_counts.most_common()))
    uncl = [n for n, e in settlements.items() if not e.get("district")]
    if uncl:
        print("unclassified:", uncl[:20])


if __name__ == "__main__":
    main()
