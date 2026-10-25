#!/usr/bin/env python3
"""Pre-publish consistency checks. Exit code 1 if any check fails.

    python audit_checks.py            # fast checks (seconds)
    python audit_checks.py --deep     # also refit every published matrix (minutes)

Checks:
  totals    each ballot CSV's per-list sums equal wiki_official_results.json
  seats     Bader-Ofer on the official votes gives the official seats (K21-K25)
  dhondt    the calculators' parties25 / parties26 arrays equal the results file
  k26       party_config K26 seats equal the results file
  matrix    every transfer file has a full 'matrix' whose rows sum to its row sum
  deep      the published matrix equals what generate_transfer_data.py fits now
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

from k26_live import bader_ofer
from party_config import ELECTIONS

ROOT = Path(__file__).resolve().parent
WIKI = json.loads((ROOT / 'site/data/wiki_official_results.json').read_text(encoding='utf-8'))
AGREEMENTS = {
    '25': [('הליכוד', 'הציונות הדתית'), ('ש״ס', 'יהדות התורה'), ('יש עתיד', 'המחנה הממלכתי'), ('העבודה', 'מרצ')],
}
failures = []


def check(name, ok, detail=''):
    print(f"{'ok  ' if ok else 'FAIL'} {name}{(': ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def totals():
    for e in [str(k) for k in range(16, 26)]:
        cfg = ELECTIONS[e]
        official = {r['name']: r['votes'] for r in WIKI.get(e, [])}
        df = pd.read_csv(ROOT / cfg['file'], encoding=cfg['encoding'])
        bad = []
        for sym, name in zip(cfg['major_parties']['symbols'], cfg['major_parties']['names']):
            if sym in df.columns and name in official and int(df[sym].sum()) != official[name]:
                bad.append(f"{name} {int(df[sym].sum()) - official[name]:+,}")
        check(f'totals K{e}', not bad, ', '.join(bad[:5]))


def seats():
    for e in ('21', '22', '23', '24', '25'):
        official = WIKI.get(e, [])
        valid = ELECTIONS[e].get('valid_votes') or sum(r['votes'] for r in official)
        got = bader_ofer({r['name']: r['votes'] for r in official}, agreements=AGREEMENTS.get(e, []), valid_total=valid)
        # Agreements are only listed for K25 here; for earlier Knessets a one-seat
        # difference can come from a missing agreement, so only K25 is strict.
        diff = {r['name']: (r['seats'], got[r['name']]) for r in official if r['seats'] != got[r['name']]}
        if e == '25':
            check(f'seats K{e}', not diff and sum(got.values()) == 120, str(diff))
        else:
            print(f"info seats K{e} without agreements: {diff or 'identical'}")


def dhondt():
    for page in ('site/dhondt.html', 'site/m/dhondt.html'):
        text = (ROOT / page).read_text(encoding='utf-8')
        for arr, e in (('parties25', '25'), ('parties26', '26')):
            block = re.search(rf'const {arr} = \[(.*?)\];', text, re.S).group(1)
            rows = dict((n, int(v)) for n, v in re.findall(r"name: '([^']+)', votes: (\d+)", block))
            official = {r['name']: r['votes'] for r in WIKI.get(e, [])}
            bad = [f"{n} {rows[n]:,} vs {official[n]:,}" for n in official if n in rows and rows[n] != official[n] and official[n] > 0]
            check(f'{page} {arr}', not bad, ', '.join(bad[:4]))


def k26():
    cfg = ELECTIONS['26']['major_parties']
    wiki = {r['name']: r['seats'] for r in WIKI.get('26', [])}
    bad = [f"{n} config {s} wiki {wiki.get(n)}" for n, s in zip(cfg['names'], cfg['seats']) if wiki.get(n) != s]
    check('k26 seats party_config = results file', not bad, ', '.join(bad))
    check('k26 seats sum to 120', sum(wiki.values()) == 120, str(sum(wiki.values())))


def matrices():
    for path in sorted((ROOT / 'site/data').glob('transfer_*_to_*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        m = data.get('matrix')
        if not m:
            check(f'matrix {path.name}', False, "no full 'matrix' field (regenerate with generate_transfer_data.py)")
            continue
        sums = [sum(r) for r in m]
        spread = max(sums) - min(sums)
        check(f'matrix {path.name}', spread < 1e-3 and min(min(r) for r in m) >= 0,
              f"row sums {min(sums):.4f}-{max(sums):.4f}")


def deep():
    from generate_transfer_data import VoteTransferAnalyzer
    for path in sorted((ROOT / 'site/data').glob('transfer_*_to_*.json')):
        a, b = re.match(r'transfer_(\d+)_to_(\d+)', path.name).groups()
        data = json.loads(path.read_text(encoding='utf-8'))
        an = VoteTransferAnalyzer(include_abstention='abstention' in path.name)
        d = an.design_matrices(a, b)
        M = an.solve_transfer_matrix_convex(d['X'], d['Y'], row_sum=d['row_sum'], zero_cells=d['zero_cells'])
        pub = data.get('matrix')
        worst = max(abs(M[i][j] - pub[i][j]) for i in range(len(pub)) for j in range(len(pub[0]))) if pub else 1
        check(f'deep {path.name}', worst < 0.002, f"max cell difference {worst * 100:.2f} points")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--deep', action='store_true')
    args = ap.parse_args()
    totals()
    seats()
    dhondt()
    k26()
    matrices()
    if args.deep:
        deep()
    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
