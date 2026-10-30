#!/usr/bin/env python3
"""Rebuild the K26 site files from one accepted CEC snapshot.

The scheduled poller calls this through GitHub Actions. With k26_control.json
auto set to false, the script exits before touching the site unless --force
is passed (a manual run).
"""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROL = ROOT / "k26_control.json"
STATUS = ROOT / "site" / "data" / "k26_status.json"
CI_FILE = ROOT / "site" / "data" / "transfer_ci.json"
CI_KEYS = ("25_to_26", "25_to_26_abstention")
# Intervals matter only near the final count; earlier polls skip them.
MILESTONES = (0.95, 1.0)
# The poller fires every 10 minutes and skips while a rebuild runs.
LIVE_CI_B = 50
LIVE_CI_TIMEOUT = 8 * 60


def auto_enabled():
    return json.loads(CONTROL.read_text(encoding="utf-8")).get("auto") is True


def run(cmd, env=None, timeout=None):
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, start_new_session=True)
    try:
        returncode = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise SystemExit(f"timed out after {timeout}s")
    if returncode != 0:
        raise SystemExit(returncode)


def drop_stale_ci():
    """Remove K26 intervals that were computed against an older transfer matrix."""
    if not CI_FILE.exists():
        return
    ci = json.loads(CI_FILE.read_text(encoding="utf-8"))
    transitions = ci.get("transitions") or {}
    dropped = []
    for key in CI_KEYS:
        block = transitions.get(key)
        if block is None:
            continue
        path = ROOT / "site" / "data" / f"transfer_{key}.json"
        stats = json.loads(path.read_text(encoding="utf-8"))["stats"] if path.exists() else {}
        if block.get("common_precincts") != stats.get("common_precincts") or block.get("r_squared") != stats.get("r_squared"):
            del transitions[key]
            dropped.append(key)
    if dropped:
        CI_FILE.write_text(json.dumps(ci, ensure_ascii=False), encoding="utf-8")
        print(f"dropped stale confidence intervals: {', '.join(dropped)}")


def refresh_irregularities(ballots):
    """Rebuild the K26 unusual-ballot list. A failure does not block the rest of the update."""
    try:
        run([sys.executable, "generate_irregularities_data.py", "--elections", "26"])
    except SystemExit as error:
        print(f"irregularities were not updated ({error})")
        return
    path = ROOT / "site" / "data" / "irregularities_26.json"
    covered = json.loads(path.read_text(encoding="utf-8"))["election"]["total_ballots"]
    if covered != ballots:
        # The irregular page hides K26 while these disagree with k26_status.json.
        print(f"irregularities_26.json covers {covered} ballots, not {ballots}")


def refresh_suspects():
    """Rebuild the command-center (k26.html) most-suspicious-ballots pane.

    Needs the refreshed tsne_26 + transfer_25_to_26 in site/data, so it runs
    after prepare_election_26. A failure does not block the rest of the update.
    """
    try:
        run([sys.executable, "generate_suspects_data.py"])
    except SystemExit as error:
        print(f"suspects pane data was not updated ({error})")


def refresh_command_center():
    """Rebuild the k26.html extras (Twelve Knessets, factoids, bellwether, gated nowcast).

    Runs after k26_live publishes, so k26_status.json and the wiki/map/tsne/
    transfer files are the fresh snapshot. The sectors taxonomy is static;
    it is regenerated only if missing. A failure does not block the update.
    """
    try:
        sectors_path = ROOT / "site" / "data" / "settlement_sectors.json"
        if not sectors_path.exists():
            run([sys.executable, "generate_settlement_sectors.py"])
        # District (מחוז) fields on the sectors are static, but a sectors
        # regeneration would drop them and with them the district slices;
        # restore them if any settlement lacks one.
        try:
            settlements = json.loads(sectors_path.read_text(encoding="utf-8")).get("settlements", {})
            if settlements and not all("district" in e for e in settlements.values()):
                run([sys.executable, "generate_settlement_districts.py"])
        except Exception as error:
            print(f"district check skipped ({error})")
        run([sys.executable, "generate_command_center_data.py"])
    except SystemExit as error:
        print(f"command-center extras were not updated ({error})")


def refresh_turnout():
    """Rebase the turnout what-if on the official count. turnout.html stays paused if this fails."""
    try:
        run([sys.executable, "generate_turnout_sim.py"], env={**os.environ, "K26_REAL": "1"})
    except SystemExit as error:
        print(f"turnout data was not updated ({error})")


# Non-party columns the K26 CEC file (see the official dummy expb.csv)
# carries between כשרים and the first list symbol: external / double-
# envelope tallies, not lists. They must never reach party consumers.
NON_PARTY_COLUMNS = ("חיצוניות", "חיצוניים", "קלפי אחרת")


def _num(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def normalize(source, dest):
    """Write a CEC snapshot to ballot26.csv in the historical shape.

    Accepts a CEC CSV (utf-8-sig or cp1255, as the K26 dummy is) or a
    {columns, rows} JSON file. Two K26 shape fixes happen here, at the
    single seam: the חיצוניות/חיצוניים tally columns are dropped (they
    are not party lists), and roster rows with no voters and no valid
    votes yet are dropped -- the dummy ships all 12,018 boxes, and a
    roster-prefilled live file must rebuild from counted boxes only.
    Returns the number of counted ballots written.
    """
    import csv
    import io

    raw = Path(source).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # The CEC published K21–K24 in ISO-8859-8; cp1255 decodes that Hebrew too.
        text = raw.decode("cp1255")
    if text.lstrip().startswith("{"):
        data = json.loads(text)
        columns = [str(c) for c in data["columns"]]
        rows = [dict(zip(columns, row)) for row in data["rows"]]
    else:
        reader = csv.DictReader(io.StringIO(text))
        columns = list(reader.fieldnames or [])
        rows = list(reader)
    if not any(c in columns for c in ("קלפי", "מספר קלפי")):
        raise SystemExit("snapshot is neither a CEC CSV nor a columns/rows JSON file")
    keep = [c for c in columns if c not in NON_PARTY_COLUMNS]
    counted = [r for r in rows if _num(r.get("מצביעים")) > 0 or _num(r.get("כשרים")) > 0]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=keep, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(counted)
    dest.write_text(buffer.getvalue(), encoding="utf-8-sig")
    return len(counted)


def ci_milestone(ballots, roster, final, previous):
    coverage = 1.0 if final or ballots >= roster else ballots / roster
    reached = max((mark for mark in MILESTONES if coverage + 1e-9 >= mark), default=0)
    if reached > (previous or 0):
        return reached
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--ballots", type=int, required=True)
    parser.add_argument("--as-of", default="")
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--ci-b", type=int, default=LIVE_CI_B)
    parser.add_argument("--ci-abstention", action="store_true")
    parser.add_argument("--ci-timeout", type=int, default=LIVE_CI_TIMEOUT)
    args = parser.parse_args()

    if not auto_enabled() and not args.force:
        print("k26_control.json auto is false; not rebuilding. Pass --force for a manual update.")
        return

    blob = Path(args.csv).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != args.sha256:
        raise SystemExit(f"sha256 mismatch: file {digest} dispatch {args.sha256}")

    ballot_path = ROOT / "ballot26.csv"
    counted = normalize(args.csv, ballot_path)
    if counted != args.ballots:
        raise SystemExit(f"ballot count mismatch: file {counted} dispatch {args.ballots}")

    run([sys.executable, "prepare_election_26.py", "--real-csv", str(ballot_path)])
    run([sys.executable, "prepare_fraud_sim.py", "--transitions", "25_26"], env={**os.environ, "K26_REAL": "1"})
    refresh_suspects()
    refresh_irregularities(counted)

    from k26_live import ROSTER, STATUS as status_path, publish_kind, summarize

    summary = summarize(ballot_path)
    kind = publish_kind(
        summary["ballots"],
        args.final,
        regular_ballots=summary["ballots"] - summary["external_envelopes_counted"],
        external_pending=summary["external_envelopes_pending"],
    )
    if kind == "official":
        refresh_turnout()
    previous_ci = 0
    if status_path.exists():
        previous_ci = json.loads(status_path.read_text(encoding="utf-8")).get("ci_coverage") or 0
    milestone = ci_milestone(summary["ballots"], ROSTER, args.final, previous_ci) if args.ci else None
    ci_coverage = previous_ci
    if milestone:
        cmd = [sys.executable, "generate_transfer_ci.py", "--only", "25_to_26", "--B", str(args.ci_b)]
        if not args.ci_abstention:
            cmd.append("--no-abstention")
        try:
            run(cmd, timeout=args.ci_timeout or None)
            ci_coverage = milestone
        except SystemExit as error:
            print(f"confidence intervals were not updated ({error})")
    drop_stale_ci()

    run([
        sys.executable, "k26_live.py",
        "--csv", str(ballot_path),
        "--publish",
        "--kind", kind,
        "--as-of", args.as_of,
        "--sha256", digest,
        "--ci-coverage", str(ci_coverage),
    ])
    refresh_command_center()
    run([sys.executable, "netlify/lib/mcp/build_mcp_data.py"])
    print(f"rebuilt {kind} from {summary['ballots']} ballots")


if __name__ == "__main__":
    main()
