#!/usr/bin/env python3
"""End-to-end drill for the election-day turnout view (feat/k26-election-day-turnout).

PR #22's lesson: the K26 publish path crashed only when actually run, on
the shipped files, in a fresh environment. This drill therefore runs the
whole turnout-day chain the way election day will, on copies, and exits
non-zero on the first failure:

  1. three synthetic CEC snapshots of the day (12:00 CSV, 17:00
     {columns,rows} JSON, 20:00 XML), each built from the repo's own
     ballot26.csv so every code/ballot is real;
  2. generate_turnout_day_data.py on each in sequence -- history must
     accumulate, turnout must be monotonic, the roster must match;
  3. refresh_turnout_day.py gates: refuses with turnout_auto off,
     refuses on a sha mismatch (files untouched), publishes with
     --force and flips k26_status.json to kind="turnout", and refuses
     again once results are flowing (status partial);
  4. the Netlify poller (netlify/functions/k26-turnout-poll.mjs) with
     stubbed fetch/GitHub: dispatch on a new snapshot, skip on the
     same one, hold with auto off, reject an HTML error page;
  5. the published JSON's contract with k26.html (station_fields width,
     group dimensions, pace bounds).

Run it in a FRESH venv from requirements.txt alone, in a clean
worktree -- that is the point. Wrapper:

    ./tests/drill_turnout_day.sh

or by hand:

    python tests/drill_turnout_day.py            # uses this repo (copies to a temp dir)
    python tests/drill_turnout_day.py --repo /path/to/worktree
"""
import argparse
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FAILURES = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)


def run(cmd, cwd, expect=0):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if expect is not None and proc.returncode != expect:
        print(proc.stdout[-2000:])
        print(proc.stderr[-2000:])
    return proc


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- fixtures
def build_fixtures(repo, tmp):
    """Three snapshots of the same day from the repo's ballot26.csv."""
    rows = list(csv.DictReader(open(repo / "ballot26.csv", encoding="utf-8-sig")))
    base = []
    for r in rows:
        elig = int(float(r["בזב"] or 0))
        final = int(float(r["מצביעים"] or 0))
        if elig <= 0:
            continue
        base.append((r["סמל ישוב"], r["שם ישוב"], r["קלפי"], elig, final))
    snaps = []
    # 12:00 - CEC-style CSV, ~40% of the final simulated turnout
    p1 = tmp / "turnout_1200.csv"
    with open(p1, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["סמל ישוב", "שם ישוב", "קלפי", "בזב", "מצביעים"])
        for code, name, ballot, elig, final in base:
            w.writerow([code, name, ballot, elig, int(final * 0.40)])
    snaps.append((p1, "2026-10-27T12:00:00+02:00"))
    # 17:00 - {columns, rows} JSON, ~65%
    p2 = tmp / "turnout_1700.json"
    p2.write_text(json.dumps({
        "as_of": "2026-10-27T17:00:00+02:00",
        "columns": ["סמל ישוב", "קלפי", "בזב", "מצביעים"],
        "rows": [[c, b, e, int(f * 0.65)] for c, _, b, e, f in base],
    }, ensure_ascii=False), encoding="utf-8")
    snaps.append((p2, "2026-10-27T17:00:00+02:00"))
    # 20:00 - generic XML, ~85%
    p3 = tmp / "turnout_2000.xml"
    with open(p3, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?><feed>')
        for code, _, ballot, elig, final in base:
            fh.write(f'<row code="{code}" ballot="{ballot}" eligible="{elig}" voters="{int(final * 0.85)}"/>')
        fh.write("</feed>")
    snaps.append((p3, "2026-10-27T20:00:00+02:00"))
    return snaps


def copy_repo(repo, dst):
    """Copy only what the turnout chain reads, preserving layout."""
    for rel in ("generate_turnout_day_data.py", "refresh_turnout_day.py",
                "generate_map_data.py", "party_config.py", "k26_control.json",
                "ballot26.csv", "ballot25.csv"):
        src = repo / rel
        if src.exists():
            shutil.copy2(src, dst / rel)
    (dst / "data").mkdir(exist_ok=True)
    shutil.copy2(repo / "data/k25_k26_ballot_union.csv", dst / "data/k25_k26_ballot_union.csv")
    (dst / "site/data").mkdir(parents=True, exist_ok=True)
    for name in ("tsne_25.json", "map_25.json", "settlement_sectors.json",
                 "station_socioeconomic.json", "station_coordinates.json", "k26_status.json"):
        shutil.copy2(repo / f"site/data/{name}", dst / f"site/data/{name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="turnout-drill-"))
    work = tmp / "repo"
    work.mkdir()
    copy_repo(repo, work)
    py = sys.executable
    print(f"drill repo copy: {work}\npython: {py}\n")

    # Fresh-environment import check (the PR22 requirements lesson):
    # everything the publish path imports must come from requirements.txt.
    proc = run([py, "-c", "import generate_turnout_day_data, refresh_turnout_day"], work)
    check("fresh-env imports (generate + refresh)", proc.returncode == 0)

    snaps = build_fixtures(repo, tmp)
    status_path = work / "site/data/k26_status.json"
    out_path = work / "site/data/turnout_day_26.json"
    original_status = status_path.read_bytes()

    # -- stage 1+2: generator over the three snapshots, in order
    turnouts = []
    for i, (snap, as_of) in enumerate(snaps):
        proc = run([py, "generate_turnout_day_data.py", "--snapshot", str(snap),
                    "--as-of", as_of, "--sha256", sha256(snap)], work)
        check(f"generator accepts snapshot {i + 1} ({snap.suffix})", proc.returncode == 0)
        if proc.returncode != 0:
            break
        data = json.loads(out_path.read_text(encoding="utf-8"))
        nat = data["national"]
        turnouts.append(nat["turnout"])
        check(f"snapshot {i + 1}: roster fully reported",
              nat["reported_ballots"] == nat["roster_ballots"] and nat["unmatched_rows"] == 0,
              f"{nat['reported_ballots']}/{nat['roster_ballots']} unmatched={nat['unmatched_rows']}")
        check(f"snapshot {i + 1}: history accumulates", len(data["history"]) == i + 1)
        check(f"snapshot {i + 1}: source sha recorded", data["meta"]["source_sha256"] == sha256(snap))
    check("turnout monotonic over the day", turnouts == sorted(turnouts) and len(set(turnouts)) == 3,
          str(turnouts))

    data = json.loads(out_path.read_text(encoding="utf-8"))
    fields = data["meta"]["station_fields"]
    check("station rows match station_fields width",
          all(len(s) == len(fields) for s in data["stations"]))
    check("all group dimensions present and non-empty",
          all(data["groups"].get(k) for k in
              ("k25_winner", "k25_bloc", "stronghold", "population", "form", "district", "socio", "k25_turnout_band")))
    # Pace can legitimately exceed 1 late in the day (a group that has
    # already cast more ballots than in all of K25); it must stay sane.
    max_pace = max((r["pace"] or 0) for rows in data["groups"].values() for r in rows)
    check("pace positive and sane everywhere (max reported)",
          all(r["pace"] is None or 0 < r["pace"] <= 1.5
              for rows in data["groups"].values() for r in rows)
          and 0 < data["national"]["pace"] <= 1.5, f"max pace {max_pace}")
    mk = data["national"].get("match_kinds", {})
    check("unmatched ballots fall back to <400m neighbours before settlement",
          mk.get("neighbor", 0) > mk.get("settlement", 0), str(mk))
    check("matched twins are the large majority",
          data["national"]["matched_ballots"] > 0.75 * data["national"]["reported_ballots"],
          f"{data['national']['matched_ballots']}/{data['national']['reported_ballots']}")

    # -- stage 3: refresh gates
    snap3, asof3 = snaps[-1]
    before = out_path.read_bytes()
    proc = run([py, "refresh_turnout_day.py", "--snapshot", str(snap3),
                "--sha256", sha256(snap3), "--as-of", asof3], work, expect=None)
    check("refresh refuses while turnout_auto is off (exit 0, no publish)",
          proc.returncode == 0 and status_path.read_bytes() == original_status and out_path.read_bytes() == before)

    proc = run([py, "refresh_turnout_day.py", "--snapshot", str(snap3), "--sha256", "0" * 64,
                "--as-of", asof3, "--force"], work, expect=None)
    check("refresh refuses a sha mismatch without touching files",
          proc.returncode != 0 and status_path.read_bytes() == original_status and out_path.read_bytes() == before)

    proc = run([py, "refresh_turnout_day.py", "--snapshot", str(snaps[1][0]),
                "--sha256", sha256(snaps[1][0]), "--as-of", snaps[1][1], "--force"], work)
    status = json.loads(status_path.read_text(encoding="utf-8"))
    check("refresh --force publishes and flips status to turnout",
          proc.returncode == 0 and status.get("kind") == "turnout" and status.get("sha256") == sha256(snaps[1][0]))

    published = out_path.read_bytes()
    status["kind"] = "partial"
    status_path.write_text(json.dumps(status), encoding="utf-8")
    proc = run([py, "refresh_turnout_day.py", "--snapshot", str(snap3),
                "--sha256", sha256(snap3), "--as-of", asof3, "--force"], work, expect=None)
    check("refresh refuses once results are flowing",
          proc.returncode == 0 and out_path.read_bytes() == published)

    # -- stage 4: Netlify poller with stubbed fetch + GitHub
    node_script = tmp / "poller_drill.mjs"
    node_script.write_text(f"""
import assert from "node:assert/strict";
import {{ readFileSync }} from "node:fs";
import {{ pollTurnout }} from "{(repo / 'netlify/functions/k26-turnout-poll.mjs').as_posix()}";

const snapBytes = readFileSync("{snaps[1][0].as_posix()}");
const publishedSha = "{sha256(snaps[1][0])}";
const b64 = (obj) => Buffer.from(JSON.stringify(obj)).toString("base64");
let dispatched = null;
function stub(acceptedSha, statusKind) {{
  return async (url, opts) => {{
    const u = String(url);
    if (u.includes("example.invalid")) return new Response(snapBytes, {{ status: 200 }});
    if (u.includes("turnout_day_26.json")) return Response.json({{ content: b64({{ meta: {{ source_sha256: acceptedSha }} }}) }});
    if (u.includes("k26_status.json")) return Response.json({{ content: b64({{ kind: statusKind }}) }});
    if (u.includes("runs?")) return Response.json({{ total_count: 0 }});
    if (u.includes("dispatches")) {{ dispatched = JSON.parse(opts.body); return new Response(null, {{ status: 204 }}); }}
    throw new Error("unexpected fetch " + u);
  }};
}}
const env = {{ K26_TURNOUT_URL: "https://example.invalid/turnout", GITHUB_DISPATCH_TOKEN: "x" }};
const noon = new Date("2026-10-27T10:00:00Z"); // 12:00 IST, inside the turnout window

let r = await pollTurnout({{ ...env, K26_TURNOUT_AUTO: "1" }}, noon, stub("a-different-sha", "turnout"));
assert.equal(r.action, "dispatch"); assert.equal(dispatched.inputs.sha256, "{sha256(snaps[1][0])}");
assert.ok(dispatched.ref); console.log("PASS  poller dispatches a new snapshot with its sha");

dispatched = null;
r = await pollTurnout({{ ...env, K26_TURNOUT_AUTO: "1" }}, noon, stub(publishedSha, "turnout"));
assert.equal(r.action, "skip"); assert.equal(dispatched, null);
console.log("PASS  poller skips the already-published snapshot");

r = await pollTurnout({{ ...env }}, noon, stub("other", "turnout")); // turnout_auto false in the committed control file
assert.equal(r.action, "hold"); console.log("PASS  poller holds while turnout_auto is off");

r = await pollTurnout({{ ...env, K26_TURNOUT_AUTO: "1" }}, noon, stub("other", "partial"));
assert.equal(r.action, "skip"); assert.equal(r.reason, "results already flowing");
console.log("PASS  poller stands down once results are flowing");

r = await pollTurnout({{ ...env, K26_TURNOUT_AUTO: "1" }}, noon, async (url) =>
  String(url).includes("example.invalid") ? new Response("<html>error</html>", {{ status: 200 }}) : stub("o", "turnout")(url));
assert.equal(r.action, "reject"); console.log("PASS  poller rejects an HTML error page");
""", encoding="utf-8")
    proc = run(["node", str(node_script)], work, expect=None)
    sys.stdout.write(proc.stdout)
    check("Netlify poller end-to-end (stubbed GitHub)", proc.returncode == 0)
    if proc.returncode != 0:
        print(proc.stderr[-2000:])

    print(f"\n{len(FAILURES)} failure(s)" if FAILURES else "\nALL CHECKS PASSED")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
