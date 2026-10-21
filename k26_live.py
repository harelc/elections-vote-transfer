#!/usr/bin/env python3
"""Publish K26 national totals from a ballot CSV into the pages that hardcode them.

Reads ballot26.csv (or another CEC-shaped file), sums each letter-symbol, runs
Bader-Ofer, and writes party_config seats, the wiki totals, both D'Hondt pages,
and the K26 rows of both party-profile pages. The orange card is updated only
when --publish is set.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROSTER = json.loads((ROOT / "k26_control.json").read_text(encoding="utf-8")).get("roster", 12018)
WIKI = ROOT / "site" / "data" / "wiki_official_results.json"
STATUS = ROOT / "site" / "data" / "k26_status.json"
PARTY_CONFIG = ROOT / "party_config.py"
DHONDT_PAGES = [ROOT / "site" / "dhondt.html", ROOT / "site" / "m" / "dhondt.html"]
PARTY_PAGES = [ROOT / "site" / "party.html", ROOT / "site" / "m" / "party.html"]

SURPLUS_AGREEMENTS = [
    ("ש״ס", "יהדות התורה"),
    ("עוצמה יהודית", "הציונות הדתית"),
    ("ישר", "ישראל ביתנו"),
    ("הרשימה המשותפת", "רע״ם"),
]


def bader_ofer(votes, threshold_pct=3.25, total_seats=120, agreements=None, valid_total=None):
    """Same allocation as simulate_election_26.bader_ofer.

    The threshold is a share of all valid votes, including lists not in `votes`.
    """
    total = max(valid_total or 0, sum(votes.values()))
    thresh = total * threshold_pct / 100.0
    passed = {k: v for k, v in votes.items() if v >= thresh}
    partner = {}
    for a, b in (agreements or []):
        if a in passed and b in passed:
            partner[a] = b
            partner[b] = a
    groups = []
    seen = set()
    for name in passed:
        if name in seen:
            continue
        if name in partner:
            other = partner[name]
            groups.append(([name, other], passed[name] + passed[other]))
            seen.update((name, other))
        else:
            groups.append(([name], passed[name]))
            seen.add(name)
    seats_g = [0] * len(groups)
    for _ in range(total_seats):
        i = max(range(len(groups)), key=lambda j: groups[j][1] / (seats_g[j] + 1))
        seats_g[i] += 1
    result = {k: 0 for k in votes}
    for (members, _), n in zip(groups, seats_g):
        if len(members) == 1:
            result[members[0]] = n
            continue
        inner = [0] * len(members)
        for _ in range(n):
            i = max(range(len(members)), key=lambda j: passed[members[j]] / (inner[j] + 1))
            inner[i] += 1
        for m, s in zip(members, inner):
            result[m] = s
    return result


def load_rows(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        data = json.loads(stripped)
        columns = data["columns"]
        rows = [dict(zip(columns, row)) for row in data["rows"]]
        return columns, rows
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        raise SystemExit(f"{path} has no ballot rows")
    return list(rows[0].keys()), rows


def ballot_column(columns):
    for name in ("קלפי", "מספר קלפי"):
        if name in columns:
            return name
    raise SystemExit("ballot file has no קלפי column")


def integer(value):
    if value is None or value == "":
        return 0
    return int(float(value))


def summarize(path):
    from party_config import ELECTIONS

    columns, rows = load_rows(path)
    ballot_column(columns)
    meta_columns = set(columns[: columns.index("כשרים") + 1])
    symbols = [column for column in columns if column not in meta_columns]
    votes_by_symbol = {symbol: 0 for symbol in symbols}
    eligible = voters = valid = 0
    for row in rows:
        eligible += integer(row.get("בזב"))
        voters += integer(row.get("מצביעים"))
        valid += integer(row.get("כשרים"))
        for symbol in symbols:
            votes_by_symbol[symbol] += integer(row.get(symbol))
    major = ELECTIONS["26"]["major_parties"]
    names = dict(zip(major["symbols"], major["names"]))
    unknown = sorted(symbol for symbol, votes in votes_by_symbol.items() if symbol not in names and votes > 0)
    votes_by_name = {names[symbol]: votes_by_symbol.get(symbol, 0) for symbol in major["symbols"]}
    valid_total = max(valid, sum(votes_by_symbol.values()))
    seats_by_name = bader_ofer(votes_by_name, agreements=SURPLUS_AGREEMENTS, valid_total=valid_total)
    seats = [seats_by_name[name] for name in major["names"]]
    turnout = round(100 * voters / eligible, 1) if eligible else 0
    return {
        "ballots": len(rows),
        "eligible": eligible,
        "voters": voters,
        "valid": valid,
        "turnout": turnout,
        "symbols": major["symbols"],
        "names": major["names"],
        "votes_by_name": votes_by_name,
        "other_votes": valid_total - sum(votes_by_name.values()),
        "seats": seats,
        "unknown": unknown,
    }


def publish_kind(ballots, final):
    if final or ballots >= ROSTER:
        return "official"
    return "partial"


def status_document(summary, kind, as_of, sha256, ci_coverage):
    partial = kind == "partial"
    return {
        "kind": kind,
        "as_of": as_of,
        "ballots": summary["ballots"],
        "ballots_total": ROSTER,
        "source_he": "ספירה חלקית, ועדת הבחירות המרכזית" if partial else "ועדת הבחירות המרכזית",
        "source_en": "Partial count, Central Elections Committee" if partial else "Central Elections Committee",
        "sha256": sha256,
        "ci_coverage": ci_coverage,
    }


def update_election_block(text, summary):
    start = text.index("    '26': {")
    end = text.index("# Election-specific", start)
    block = text[start:end]
    for key, value in (
        ("eligible_voters", summary["eligible"]),
        ("votes_cast", summary["voters"]),
        ("valid_votes", summary["valid"]),
        ("turnout_percent", summary["turnout"]),
    ):
        pattern = re.compile(rf"('{key}': )[0-9.]+")
        block, count = pattern.subn(rf"\g<1>{value}", block, count=1)
        if count != 1:
            raise SystemExit(f"could not update party_config {key}")
    seats = ", ".join(str(seat) for seat in summary["seats"])
    block, count = re.subn(r"('seats': )\[[^\]]+\]", rf"\g<1>[{seats}]", block, count=1)
    if count != 1:
        raise SystemExit("could not update party_config seats")
    return text[:start] + block + text[end:]


def update_parties26(text, summary):
    match = re.search(r"const parties26 = \[(.*?)\];", text, re.S)
    if not match:
        raise SystemExit("parties26 array not found")
    block = match.group(1)
    missing = []
    for name, votes in summary["votes_by_name"].items():
        pattern = re.compile(r"(\{ name: '" + re.escape(name) + r"', votes: )\d+")
        block, count = pattern.subn(rf"\g<1>{votes}", block, count=1)
        if count != 1:
            missing.append(name)
    text = text[: match.start(1)] + block + text[match.end(1) :]
    text, count = re.subn(
        r"('26': \{ parties: parties26, agreements: agreements26, eligible: )\d+(, voters: )\d+(, others: )\d+",
        rf"\g<1>{summary['eligible']}\g<2>{summary['voters']}\g<3>{summary['other_votes']}",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("could not update the K26 eligible/voters preset")
    return text, missing


def update_party_seats(text, summary):
    missing = []
    for symbol, seats in zip(summary["symbols"], summary["seats"]):
        pattern = re.compile(
            r"('26': \{ partyName: '[^']*', symbol: '" + re.escape(symbol) + r"', seats: )\d+"
        )
        text, count = pattern.subn(rf"\g<1>{seats}", text, count=1)
        if count != 1:
            missing.append(symbol)
    return text, missing


def wiki_notes(kind):
    if kind == "official":
        return (
            "Official count from the Central Elections Committee.",
            "Official CEC count",
        )
    return (
        "Partial count from the Central Elections Committee. Totals cover the ballots received so far, not the full roster.",
        "Partial CEC count",
    )


def update_wiki(text, summary, kind):
    entries = [
        {"name": name, "seats": seats, "votes": summary["votes_by_name"][name]}
        for name, seats in zip(summary["names"], summary["seats"])
    ]
    entries.sort(key=lambda entry: entry["votes"], reverse=True)
    body = json.dumps(entries, ensure_ascii=False, indent=4)
    body = "\n".join(("  " + line) if line else line for line in body.splitlines())
    text, count = re.subn(
        r'"26": \[[\s\S]*?\](?=,?\s*"26_note")',
        '"26": ' + body,
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("could not update wiki_official_results 26")
    long_note, short_note = wiki_notes(kind)
    text, count = re.subn(
        r'"_26_note": "[^"]*"',
        '"_26_note": ' + json.dumps(long_note, ensure_ascii=False),
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("could not update _26_note")
    text, count = re.subn(
        r'"26_note": "[^"]*"',
        '"26_note": ' + json.dumps(short_note, ensure_ascii=False),
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("could not update 26_note")
    return text


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def apply(summary, kind, as_of, sha256, ci_coverage):
    write_text(PARTY_CONFIG, update_election_block(PARTY_CONFIG.read_text(encoding="utf-8"), summary))
    write_text(WIKI, update_wiki(WIKI.read_text(encoding="utf-8"), summary, kind))
    for path in DHONDT_PAGES:
        text, missing = update_parties26(path.read_text(encoding="utf-8"), summary)
        if missing:
            print(f"  {path.name}: no D'Hondt row for {', '.join(missing)}")
        text = text.replace("Knesset 26 - Simulated", "Knesset 26", 1)
        write_text(path, text)
    for path in PARTY_PAGES:
        text, missing = update_party_seats(path.read_text(encoding="utf-8"), summary)
        if missing:
            print(f"  {path.name}: no K26 family row for {', '.join(missing)}")
        write_text(path, text)
    STATUS.write_text(
        json.dumps(status_document(summary, kind, as_of, sha256, ci_coverage), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def check(path):
    summary = summarize(path)
    wiki = json.loads(WIKI.read_text(encoding="utf-8"))
    published = {entry["name"]: entry for entry in wiki["26"]}
    mismatches = []
    for name, votes in summary["votes_by_name"].items():
        seats = summary["seats"][summary["names"].index(name)]
        entry = published.get(name)
        if not entry or entry["votes"] != votes or entry["seats"] != seats:
            got = None if not entry else (entry["votes"], entry["seats"])
            mismatches.append(f"{name}: file {votes} votes / {seats} seats, wiki {got}")
    print(
        f"{summary['ballots']} ballots, eligible {summary['eligible']}, "
        f"voters {summary['voters']}, valid {summary['valid']}"
    )
    if summary["unknown"]:
        print("symbols not in major_parties:", ", ".join(summary["unknown"]))
    for path in DHONDT_PAGES:
        original = path.read_text(encoding="utf-8")
        updated, missing = update_parties26(original, summary)
        if missing:
            mismatches.append(f"{path.name}: missing {', '.join(missing)}")
        elif updated != original:
            mismatches.append(f"{path.name}: published numbers differ from this file")
    for path in PARTY_PAGES:
        original = path.read_text(encoding="utf-8")
        updated, missing = update_party_seats(original, summary)
        if missing:
            print(f"{path.name}: no K26 family row for {', '.join(missing)}")
        if updated != original:
            mismatches.append(f"{path.name}: published seats differ from this file")
    config = PARTY_CONFIG.read_text(encoding="utf-8")
    if update_election_block(config, summary) != config:
        mismatches.append("party_config.py totals differ from this file")
    if mismatches:
        print("\n".join(mismatches))
        return 1
    print("wiki totals match this file")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="ballot26.csv")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--kind", choices=("partial", "official"))
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--sha256", default=None)
    parser.add_argument("--ci-coverage", type=float, default=0)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        sys.exit(check(args.csv))
    if not args.publish:
        raise SystemExit("refusing to write totals without --publish")
    summary = summarize(args.csv)
    kind = args.kind or publish_kind(summary["ballots"], args.final)
    previous = {}
    if STATUS.exists():
        previous = json.loads(STATUS.read_text(encoding="utf-8"))
    ci_coverage = args.ci_coverage or previous.get("ci_coverage") or 0
    apply(summary, kind, args.as_of, args.sha256, ci_coverage)
    print(f"published {kind}: {summary['ballots']} ballots, seats {summary['seats']}")
    if summary["unknown"]:
        print("symbols not in major_parties:", ", ".join(summary["unknown"]))


if __name__ == "__main__":
    main()
