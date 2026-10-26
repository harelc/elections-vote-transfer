#!/usr/bin/env python3
"""Publish one accepted election-day turnout snapshot to the site.

Election-day counterpart of refresh_k26.py, for the hours BEFORE any
results exist. The scheduled Netlify poller (k26-turnout-poll) dispatches
.github/workflows/k26-turnout-refresh.yml, which downloads the CEC
turnout feed and calls this script; it can also be run by hand:

    python refresh_turnout_day.py --snapshot cec_turnout.csv \
        --sha256 <hex> --as-of 2026-10-27T12:05:00+02:00 --force

Gates and hand-off:
  * k26_control.json "turnout_auto" must be true unless --force.
  * Once k26_status.json is partial/official (results flowing) this
    script refuses: the turnout view's day is over and the regular
    command center owns the page.
  * On success it flips k26_status.json to kind="turnout", which makes
    k26.html auto-activate the turnout view (geomap turnout layers +
    K25-twin/sector/stronghold analyses) with no URL parameter.
    refresh_k26.py overwrites the status again when results arrive.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROL = ROOT / "k26_control.json"
STATUS = ROOT / "site" / "data" / "k26_status.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--as-of", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    control = json.loads(CONTROL.read_text(encoding="utf-8"))
    if control.get("turnout_auto") is not True and not args.force:
        print("k26_control.json turnout_auto is not true; not publishing. Pass --force for a manual update.")
        return

    status = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    if status.get("kind") in ("partial", "official"):
        print(f"k26_status.json is already {status['kind']} (results flowing); turnout day is over, not publishing.")
        return

    blob = Path(args.snapshot).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != args.sha256:
        raise SystemExit(f"sha256 mismatch: file {digest} dispatch {args.sha256}")

    subprocess.run([sys.executable, "generate_turnout_day_data.py",
                    "--snapshot", args.snapshot, "--as-of", args.as_of,
                    "--sha256", digest], cwd=ROOT, check=True)

    out = {
        "kind": "turnout",
        "as_of": args.as_of or None,
        "ballots": None,
        "ballots_total": None,
        "sha256": digest,
        "source_he": "אחוזי הצבעה, ועדת הבחירות המרכזית",
        "source_en": "Turnout, Central Elections Committee",
    }
    STATUS.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"published turnout snapshot as_of={args.as_of} sha256={digest[:12]}")


if __name__ == "__main__":
    main()
