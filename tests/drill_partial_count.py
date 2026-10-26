#!/usr/bin/env python3
"""Partial-count drill for election night, on the CEC's official dummy shape.

The CEC K26 guide (Oct 2026) fixes the live ballot file at
https://media26.bechirot.gov.il/files/expb.csv and attaches a dummy
file "identical in structure" to the real one. That dummy is the
ground truth this drill is built on:

  * cp1255 encoding (not utf-8), CRLF rows;
  * header: meta columns, then כשרים, then two external-ballot tally
    columns (חיצוניות/חיצוניים, -1 placeholders in the dummy), then
    the 38 list symbols;
  * all 12,018 roster boxes, real בזב per box, placeholder votes.

So the live file may be roster-prefilled, and "counted" cannot mean
"row present". This drill rebuilds that shape from the repo's
simulated ballot26.csv (realistic per-box votes), marks ~45% of the
electorate counted, and runs the election-night seams on copies:

  1. the Netlify poller inspect(): a full-roster file and a
     counted-only file report the same counted ballot count, and an
     all-uncounted file reports 0 (the poller then refuses to dispatch);
  2. refresh_k26.normalize(): cp1255 CEC shape -> utf-8 ballot26.csv,
     external tally columns dropped, uncounted roster rows dropped;
  3. k26_live.summarize() on both the raw CEC file and the normalised
     one: 120 seats, external columns never treated as lists;
  4. k26_live.apply() on copies: k26_status.json flips to partial with
     the counted ballot count.

    python tests/drill_partial_count.py
"""
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

FAILURES = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)


# The official dummy expb.csv header, in order.
META = ["סמל ועדה", "ברזל", "שם ישוב", "סמל ישוב", "קלפי", "ריכוז", "שופט",
        "בזב", "מצביעים", "פסולים", "כשרים"]
EXTERNAL = ["חיצוניות", "חיצוניים"]
PARTIES = ["אמת", "ב", "בד", "בי", "בקר", "ג", "ד", "די", "דרך", "ה", "ודם",
           "ז", "זך", "זץ", "ט", "י", "יק", "ך", "כן", "ל", "מחל", "ני",
           "נף", "נץ", "נקי", "נר", "עם", "פה", "צבי", "צדק", "צף", "ק",
           "קה", "קך", "קץ", "רץ", "רק", "שס"]
HEADER = META + EXTERNAL + PARTIES


def build_fixtures(tmp):
    """CEC-shaped snapshots from the simulated ballot26.csv."""
    rows = list(csv.DictReader(open(REPO / "ballot26.csv", encoding="utf-8-sig")))
    total_voters = sum(int(float(r["מצביעים"] or 0)) for r in rows)
    # Deterministic pseudo-random count order (hash of code|ballot), so
    # the counted subset is spread over the country, not a prefix.
    ordered = sorted(rows, key=lambda r: hashlib.sha256(
        f"{r['סמל ישוב']}|{r['קלפי']}".encode()).hexdigest())
    counted_keys, cast = set(), 0
    for r in ordered:
        if cast >= 0.45 * total_voters:
            break
        counted_keys.add((r["סמל ישוב"], r["קלפי"]))
        cast += int(float(r["מצביעים"] or 0))

    def cec_row(r, counted):
        out = {}
        for c in META:
            out[c] = r.get(c, "0") if counted or c in ("סמל ועדה", "ברזל", "שם ישוב",
                                                       "סמל ישוב", "קלפי", "ריכוז", "שופט", "בזב") else "0"
        out["חיצוניות"], out["חיצוניים"] = ("0", "0") if counted else ("-1", "-1")
        for c in PARTIES:
            out[c] = r.get(c, "0") if counted else "0"
        return out

    full, only = [], []
    for r in rows:
        counted = (r["סמל ישוב"], r["קלפי"]) in counted_keys
        full.append(cec_row(r, counted))
        if counted:
            only.append(cec_row(r, True))
    paths = {}
    for name, data in (("full_roster", full), ("counted_only", only)):
        p = tmp / f"{name}.csv"
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\r\n")
        w.writeheader()
        w.writerows(data)
        p.write_bytes(buf.getvalue().encode("cp1255"))
        paths[name] = p
    zero = tmp / "nothing_counted.csv"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\r\n")
    w.writeheader()
    w.writerows([cec_row(r, False) for r in rows])
    zero.write_bytes(buf.getvalue().encode("cp1255"))
    return paths, zero, len(only), cast / total_voters


def main():
    tmp = Path(tempfile.mkdtemp(prefix="partial-drill-"))
    paths, zero, counted, share = build_fixtures(tmp)
    print(f"fixtures: {counted} counted ballots, {share:.0%} of simulated voters\n")

    # -- 1. poller inspect() on all three shapes
    node_script = tmp / "inspect_drill.mjs"
    poll_url = (REPO / "netlify/functions/k26-poll.mjs").as_uri()
    node_script.write_text(f"""
import assert from "node:assert/strict";
import {{ readFileSync }} from "node:fs";
import {{ inspect }} from "{poll_url}";
const counted = {counted};
for (const name of ["full_roster", "counted_only"]) {{
  const found = inspect(readFileSync("{tmp}/" + name + ".csv"));
  assert.equal(found.ballotCount, counted, name);
  console.log("PASS  poller inspect counts only counted ballots in " + name);
}}
assert.equal(inspect(readFileSync("{zero}")).ballotCount, 0);
console.log("PASS  poller inspect reports 0 when nothing is counted yet");
""", encoding="utf-8")
    proc = subprocess.run(["node", str(node_script)], capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    check("poller inspect end-to-end", proc.returncode == 0, proc.stderr[-500:])

    # -- 2. refresh_k26.normalize on the full-roster CEC file
    import refresh_k26
    normalised = tmp / "ballot26.csv"
    n = refresh_k26.normalize(str(paths["full_roster"]), normalised)
    check("normalize returns the counted ballot count", n == counted, f"{n} != {counted}")
    text = normalised.read_text(encoding="utf-8-sig")
    header = text.splitlines()[0].split(",")
    check("normalize drops the external tally columns",
          not any(c in header for c in EXTERNAL))
    check("normalize writes counted rows only",
          len(text.strip().splitlines()) - 1 == counted)

    # -- 3. k26_live.summarize on raw CEC shape and on normalised
    import k26_live
    raw = k26_live.summarize(str(paths["full_roster"]))
    check("summarize reads the cp1255 CEC file directly, 120 seats",
          sum(raw["seats"]) == 120, str(raw["seats"]))
    check("external tallies are not lists in summarize",
          not any(c in raw["unknown"] for c in EXTERNAL), str(raw["unknown"]))
    norm = k26_live.summarize(str(normalised))
    check("summarize(normalised): ballots == counted, 120 seats",
          norm["ballots"] == counted and sum(norm["seats"]) == 120,
          f"ballots={norm['ballots']} seats={sum(norm['seats'])}")
    check("raw and normalised summaries agree on votes and seats",
          raw["votes_by_name"] == norm["votes_by_name"] and raw["seats"] == norm["seats"])

    # -- 4. apply() on copies flips the status to partial
    work = tmp / "site_copy"
    rels = ["party_config.py", "site/data/wiki_official_results.json", "site/dhondt.html",
            "site/m/dhondt.html", "site/party.html", "site/m/party.html", "site/data/k26_status.json"]
    for rel in rels:
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, work / rel)
    k26_live.PARTY_CONFIG = work / "party_config.py"
    k26_live.WIKI = work / "site/data/wiki_official_results.json"
    k26_live.DHONDT_PAGES = [work / "site/dhondt.html", work / "site/m/dhondt.html"]
    k26_live.PARTY_PAGES = [work / "site/party.html", work / "site/m/party.html"]
    k26_live.STATUS = work / "site/data/k26_status.json"
    digest = hashlib.sha256(paths["full_roster"].read_bytes()).hexdigest()
    k26_live.apply(norm, "partial", "2026-10-27T23:05:00+02:00", digest, 0)
    status = json.loads((work / "site/data/k26_status.json").read_text(encoding="utf-8"))
    check("apply publishes a partial status with the counted count",
          status["kind"] == "partial" and status["ballots"] == counted, json.dumps(status))
    wiki = json.loads((work / "site/data/wiki_official_results.json").read_text(encoding="utf-8"))
    check("published wiki seats sum to 120 on a partial count",
          sum(e["seats"] for e in wiki["26"]) == 120)

    print(f"\n{len(FAILURES)} failure(s)" if FAILURES else "\nALL CHECKS PASSED")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
