#!/usr/bin/env python3
"""Settlement sector taxonomy -> site/data/settlement_sectors.json

Multi-axis classification (a settlement can be kibbutz + jewish + wb=False
at once; the axes are independent):

  form       Locality form from the Wikidata short description stored in
             settlement_wiki.json ("קיבוץ בישראל", "מושב בישראל", ...):
             kibbutz / moshav_shitufi / moshav / moshava / community /
             local_council / city / village / institution.
  population Main population group. Priority:
             1. curated Druze list (the DRUZE_NAMES set in fraud-sim.html,
                which includes Druze-majority and significant-minority towns)
             2. wiki description keywords: druze / bedouin / arab
             3. CBS 2011 GDB `Religion_yishuv_Txt` per SEMEL_YISHUV
                (יהודי / לא יהודי / מעורב) — the field exists in
                statisticalareas_demography2019.gdb; download_statistical_zones.py
                discarded it, so it is re-extracted here.
             CBS alone cannot split non-Jewish into Arab/Druze/Bedouin,
             which is why the wiki/Druze layers run first. A CBS
             "לא יהודי" with no finer signal stays "non_jewish".
  wb         West-Bank settlement: wiki description mentions התנחלות.
  haredi     Curated whitelist of Haredi-majority localities ONLY.
             Religiosity is never inferred from Shas/UTJ vote share —
             that would define a sector by its vote and then "discover"
             how it votes.

Consumers: the Ten-Knessets pane and the nowcast readiness gate in
k26.html (via generate_command_center_data.py), factoid mining.
Names are the normalized CEC names used as keys in map_*.json.

    source venv/bin/activate && python generate_settlement_sectors.py
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_DATA = ROOT / "site" / "data"
GDB_PATH = ROOT / "data" / "statisticalareas_demography2019.gdb"

from generate_map_data import normalize_name

# Haredi-majority localities (manual, conservative: unambiguously
# Haredi-majority municipalities/localities only; mixed cities excluded).
HAREDI_LOCALITIES = {
    "בני ברק", "ביתר עילית", "מודיעין עילית", "אלעד",
    "רכסים", "עמנואל", "קרית יערים",
}


def load_druze_names():
    """Parse the DRUZE_NAMES set literal out of site/fraud-sim.html."""
    text = (ROOT / "site" / "fraud-sim.html").read_text(encoding="utf-8")
    m = re.search(r"DRUZE_NAMES = new Set\(\[(.*?)\]\);", text, re.S)
    if not m:
        return set()
    return {normalize_name(n) for n in re.findall(r'"([^"]+)"', m.group(1))}


def cbs_religion_by_name():
    """SEMEL_YISHUV -> Religion_yishuv_Txt, re-keyed by normalized name."""
    if not GDB_PATH.exists():
        return {}, "gdb missing"
    try:
        import fiona
    except ImportError:
        return {}, "fiona missing"
    by_name = {}
    with fiona.open(GDB_PATH) as src:
        for rec in src:
            p = rec["properties"]
            name = p.get("SHEM_YISHUV")
            rel = p.get("Religion_yishuv_Txt")
            if name and rel and normalize_name(name) not in by_name:
                by_name[normalize_name(name)] = rel
    return by_name, "cbs gdb 2011"


CIRCASSIAN_LOCALITIES = {"כפר כמא", "ריחאניה"}


def classify_form(desc, name=""):
    if name.startswith("מחנה"):
        return "institution"
    d = desc or ""
    if "קיבוץ" in d:
        return "kibbutz"
    if "מושב שיתופי" in d:
        return "moshav_shitufi"
    if "מושב" in d:
        return "moshav"
    if "מושבה" in d:
        return "moshava"
    if "יישוב קהילתי" in d:
        return "community"
    if "מועצה מקומית" in d:
        return "local_council"
    if d.startswith("עיר") or " עיר " in d or "עיר ב" in d:
        return "city"
    if "כפר" in d:
        return "village"
    if "מוסדי" in d:
        return "institution"
    if "יישוב" in d:
        return "locality"
    return None


def classify_population(name, desc, cbs_rel, druze_names):
    d = desc or ""
    if name in druze_names:
        return "druze", "curated druze list"
    if name in CIRCASSIAN_LOCALITIES:
        return "circassian", "manual"
    if "שבט" in name:
        return "bedouin", "name_tribe"
    if "דרוזי" in d:
        return "druze", "wiki"
    if "בדואי" in d or "בדווי" in d:
        return "bedouin", "wiki"
    if "ערבי" in d or "ערבית" in d or "מוסלמי" in d:
        return "arab", "wiki"
    if cbs_rel == "יהודי":
        return "jewish", "cbs"
    if cbs_rel == "מעורב":
        return "mixed", "cbs"
    if cbs_rel == "לא יהודי":
        # CBS does not split non-Jewish further; with Druze/Bedouin/Circassian
        # already removed above, the remaining non-Jewish localities are
        # Arab (Muslim/Christian) localities.
        return "arab", "cbs_non_jewish"
    return None, None


def main():
    names = set()
    for eid in ("25", "26"):
        path = SITE_DATA / f"map_{eid}.json"
        if path.exists():
            m = json.loads(path.read_text(encoding="utf-8"))
            names |= {s["name"] for s in m["settlements"]}
    wiki = json.loads((SITE_DATA / "settlement_wiki.json").read_text(encoding="utf-8"))
    druze_names = load_druze_names()
    cbs_rel, cbs_src = cbs_religion_by_name()

    out = {}
    stats = Counter()
    for name in sorted(names):
        w = wiki.get(name) or {}
        desc = w.get("description") or ""
        form = classify_form(desc, name)
        pop, pop_src = classify_population(name, desc, cbs_rel.get(name), druze_names)
        entry = {
            "form": form,
            "population": pop,
            "wb": "התנחלות" in desc,
            "haredi": name in HAREDI_LOCALITIES,
        }
        srcs = []
        if form:
            srcs.append("wiki_form")
        if pop_src:
            srcs.append(pop_src)
        if entry["wb"]:
            srcs.append("wiki_wb")
        if entry["haredi"]:
            srcs.append("manual_haredi")
        entry["sources"] = srcs
        out[name] = entry
        stats[f"form:{form}"] += 1
        stats[f"pop:{pop}"] += 1
        if entry["wb"]:
            stats["wb"] += 1
        if entry["haredi"]:
            stats["haredi"] += 1

    payload = {
        "meta": {
            "method": "form from Wikidata descriptions in settlement_wiki.json; "
                      "population from curated Druze list + wiki keywords + CBS 2011 "
                      "GDB Religion_yishuv_Txt; wb from wiki התנחלות tag; haredi from a "
                      "curated whitelist (never inferred from votes).",
            "cbs_source": cbs_src,
            "settlements": len(out),
            "counts": dict(stats),
        },
        "settlements": out,
    }
    path = SITE_DATA / "settlement_sectors.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {path} ({len(out)} settlements)")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    unclassified = [n for n, e in out.items() if not e["form"] and not e["population"]]
    print(f"  fully unclassified: {len(unclassified)} {unclassified[:15]}")


if __name__ == "__main__":
    main()
