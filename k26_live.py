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
_CTRL = json.loads((ROOT / "k26_control.json").read_text(encoding="utf-8"))
ROSTER = _CTRL.get("roster", 12018)
# K25 ended with 750 double-envelope (settlement 9999) boxes; the bulk drop
# on K26 night arrives after the regular polling-station roster is complete.
EXTERNAL_ENVELOPE_EXPECTED = int(_CTRL.get("external_envelopes_expected", 750))
EXTERNAL_SETTLEMENT_CODE = "9999"
WIKI = ROOT / "site" / "data" / "wiki_official_results.json"
STATUS = ROOT / "site" / "data" / "k26_status.json"
PARTY_CONFIG = ROOT / "party_config.py"
DHONDT_PAGES = [ROOT / "site" / "dhondt.html", ROOT / "site" / "m" / "dhondt.html"]
PARTY_PAGES = [ROOT / "site" / "party.html", ROOT / "site" / "m" / "party.html"]

SURPLUS_AGREEMENTS = [
    ("ישראל ביתנו", "ביחד"),
    ("רע״ם", "הרשימה המשותפת"),
    ("הציונות הדתית", "הליכוד"),
    ("יהדות התורה", "ש״ס"),
    ("הדמוקרטים", "ישר"),
]


def bader_ofer(votes, threshold_pct=3.25, total_seats=120, agreements=None, valid_total=None):
    """Same allocation as simulate_election_26.bader_ofer.

    The threshold is a share of all valid votes, including lists not in `votes`.
    """
    total = max(valid_total or 0, sum(votes.values()))
    thresh = total * threshold_pct / 100.0
    passed = {k: v for k, v in votes.items() if v >= thresh}
    if not passed:
        # No list over the threshold yet (e.g. the CEC dummy's uniform
        # placeholder votes): every list gets zero seats, never a crash.
        return {k: 0 for k in votes}
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
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # The official K26 dummy expb.csv is cp1255 (as K21-K24 were);
        # a direct --csv on the raw CEC file must not crash on it.
        text = raw.decode("cp1255")
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
    # חיצוניות/חיצוניים sit after כשרים in the K26 CEC file but are
    # external-ballot tallies, not lists (refresh_k26 strips them too).
    symbols = [column for column in columns
               if column not in meta_columns and column not in ("חיצוניות", "חיצוניים", "קלפי אחרת")]
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
    # Allocate over every list in the file, not only the majors: a list that
    # is missing from major_parties but passes the threshold must take its
    # seats from the 120, so publishing stops until it is added there.
    all_votes = dict(votes_by_name)
    all_votes.update({symbol: votes_by_symbol[symbol] for symbol in unknown})
    seats_all = bader_ofer(all_votes, agreements=SURPLUS_AGREEMENTS, valid_total=valid_total)
    passed_unknown = [symbol for symbol in unknown if seats_all[symbol] > 0]
    if passed_unknown:
        raise SystemExit(
            "lists not in ELECTIONS['26']['major_parties'] passed the threshold: "
            + ", ".join(f"{symbol} ({votes_by_symbol[symbol]:,} votes, {seats_all[symbol]} seats)" for symbol in passed_unknown)
            + ". Add them to party_config.py before publishing."
        )
    seats = [seats_all[name] for name in major["names"]]
    turnout = round(100 * voters / eligible, 1) if eligible else 0
    envelope = external_envelope_status(rows)
    return {
        "ballots": len(rows),
        "eligible": eligible,
        "voters": voters,
        "valid": valid,
        "valid_total": valid_total,
        "turnout": turnout,
        "symbols": major["symbols"],
        "names": major["names"],
        "votes_by_name": votes_by_name,
        "other_votes": valid_total - sum(votes_by_name.values()),
        "seats": seats,
        "unknown": unknown,
        **envelope,
    }


def external_envelope_status(rows):
    counted = sum(
        1 for row in rows
        if str(row.get("סמל ישוב", "")).strip() == EXTERNAL_SETTLEMENT_CODE
    )
    expected = EXTERNAL_ENVELOPE_EXPECTED
    return {
        "external_envelopes_expected": expected,
        "external_envelopes_counted": counted,
        "external_envelopes_pending": counted < expected,
    }


def publish_kind(ballots, final):
    """Official is only set when the refresh workflow passes --final (CEC certified).

    Reaching the 12,018-box roster (or more, once 9999 rows land) is not
    enough: double-envelope ballots drop later and totals stay provisional.
    """
    del ballots  # roster size alone must not flip the site to official
    if final:
        return "official"
    return "partial"


def status_document(summary, kind, as_of, sha256, ci_coverage):
    partial = kind == "partial"
    return {
        "kind": kind,
        "as_of": as_of,
        "ballots": summary["ballots"],
        "ballots_total": ROSTER,
        "roster_complete": summary["ballots"] >= ROSTER,
        "external_envelopes_expected": summary["external_envelopes_expected"],
        "external_envelopes_counted": summary["external_envelopes_counted"],
        "external_envelopes_pending": summary["external_envelopes_pending"],
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
            "Final certified results from the Central Elections Committee.",
            "Certified CEC results",
        )
    return (
        "Provisional count from the Central Elections Committee — not the certified final result. Totals change as ballots arrive, including double-envelope (9999) boxes.",
        "Provisional CEC count",
    )


def update_wiki(text, summary, kind):
    """Rewrite the K26 entries as JSON, whatever the file's whitespace.

    `26_valid` and `26_other` carry all valid votes and the votes of lists
    outside `26`, so pages can put the threshold against the legal base.
    """
    data = json.loads(text)
    entries = [
        {"name": name, "seats": seats, "votes": summary["votes_by_name"][name]}
        for name, seats in zip(summary["names"], summary["seats"])
    ]
    entries.sort(key=lambda entry: entry["votes"], reverse=True)
    long_note, short_note = wiki_notes(kind)
    data["26"] = entries
    data["_26_note"] = long_note
    data["26_note"] = short_note
    data["26_valid"] = summary["valid_total"]
    data["26_other"] = summary["other_votes"]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def apply(summary, kind, as_of, sha256, ci_coverage):
    # Build every file first; write only when all of them succeeded, so a
    # failure never leaves the site half on the new count and half on the old.
    outputs = [
        (PARTY_CONFIG, update_election_block(PARTY_CONFIG.read_text(encoding="utf-8"), summary)),
        (WIKI, update_wiki(WIKI.read_text(encoding="utf-8"), summary, kind)),
    ]
    for path in DHONDT_PAGES:
        text, missing = update_parties26(path.read_text(encoding="utf-8"), summary)
        if missing:
            raise SystemExit(f"{path.name}: no D'Hondt row for {', '.join(missing)}")
        outputs.append((path, text.replace("Knesset 26 - Simulated", "Knesset 26", 1)))
    for path in PARTY_PAGES:
        text, missing = update_party_seats(path.read_text(encoding="utf-8"), summary)
        if missing:
            print(f"  {path.name}: no K26 family row for {', '.join(missing)}")
        outputs.append((path, text))
    outputs.append((STATUS, json.dumps(status_document(summary, kind, as_of, sha256, ci_coverage),
                                       ensure_ascii=False, indent=2) + "\n"))
    for path, text in outputs:
        write_text(path, text)


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
