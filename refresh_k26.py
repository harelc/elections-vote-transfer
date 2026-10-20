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
MILESTONES = (0.25, 0.5, 0.8, 1.0)
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


def normalize(source, dest):
    """Copy a CEC CSV, or a {columns, rows} JSON file, to ballot26.csv."""
    raw = Path(source).read_bytes()
    text = raw.decode("utf-8-sig")
    if text.lstrip().startswith("{"):
        import csv
        import io

        data = json.loads(text)
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(data["columns"])
        writer.writerows(data["rows"])
        dest.write_text(buffer.getvalue(), encoding="utf-8-sig")
        return len(data["rows"])
    if "קלפי" not in text.splitlines()[0] and "מספר קלפי" not in text.splitlines()[0]:
        raise SystemExit("snapshot is neither a CEC CSV nor a columns/rows JSON file")
    dest.write_bytes(raw if raw.startswith(b"\xef\xbb\xbf") else b"\xef\xbb\xbf" + text.encode("utf-8"))
    return max(0, sum(1 for line in text.splitlines() if line.strip()) - 1)


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

    from k26_live import ROSTER, STATUS as status_path, publish_kind, summarize

    summary = summarize(ballot_path)
    kind = publish_kind(summary["ballots"], args.final)
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
    run([sys.executable, "netlify/lib/mcp/build_mcp_data.py"])
    print(f"rebuilt {kind} from {summary['ballots']} ballots")


if __name__ == "__main__":
    main()
