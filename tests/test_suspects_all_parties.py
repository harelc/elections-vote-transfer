#!/usr/bin/env python3
"""Sensitivity tests for the all-parties suspects TVD (run from repo root).

    venv/bin/python tests/test_suspects_all_parties.py

A planted misfeed moves 40% of a matched box's votes from its biggest
major list into an esoteric list's column (צף, which receives no votes in
the simulated K26). With the old majors-only renormalised TVD this was
invisible; now the box must jump to the top of the ranking, its TVD must
rise sharply, and the esoteric list must be named as the deviating party.

Each check prints PASS/FAIL with its evidence; exits non-zero on any FAIL.
"""
import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, '.')
import generate_suspects_data as s

results = []


def report(name, ok, evidence):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {evidence}")


scored, parties, meta = s.score_all('ballot25.csv', 'ballot26.csv')
by_key = {(b['n'], b['b']): b for b in scored}
report('baseline pairs matched boxes', meta['paired_ballots'] > 5000,
       f"{meta['paired_ballots']} paired, {meta['skipped']} skipped, {len(parties)} parties")

# Choose a quiet mid-size box (baseline TVD below the median) with >= 300
# valid votes, matched by id, whose settlement code we can find in the CSV.
quiet = sorted((b for b in scored if b['v'] >= 300 and b['decision'] == 'id'),
               key=lambda b: b['tvd'])
rows = list(csv.DictReader(open('ballot26.csv', encoding='utf-8-sig')))
cols = list(rows[0].keys())
party_cols = cols[cols.index('כשרים') + 1:]
row_by_key = {(r['שם ישוב'], s.norm_ballot(r['קלפי'])): r for r in rows}
# A quiet box dominated by one major list, so a large misfeed can be
# planted out of that single column.
target = donor = None
for cand in quiet[:len(quiet) // 2]:
    r = row_by_key.get((cand['n'], cand['b']))
    if r is None:
        continue
    d = max(party_cols, key=lambda c: int(float(r[c] or 0)))
    if int(float(r[d])) >= 0.45 * int(float(r['כשרים'])):
        target, donor, row = cand, d, r
        break
assert target is not None, 'no suitable quiet box found'
planted_idx = rows.index(row)
move = min(int(int(float(row['כשרים'])) * 0.40), int(int(float(row[donor])) * 0.9))
row[donor] = str(int(float(row[donor])) - move)
row['צף'] = str(int(float(row['צף'] or 0)) + move)

tmp = Path(tempfile.mkdtemp()) / 'ballot26_planted.csv'
with tmp.open('w', encoding='utf-8-sig', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

scored2, parties2, _ = s.score_all('ballot25.csv', str(tmp))
rank = next(i for i, b in enumerate(scored2) if (b['n'], b['b']) == (target['n'], target['b']))
after = scored2[rank]
report('planted major->esoteric misfeed surfaces in the displayed top 12', rank < 12,
       f"{target['n']} {target['b']}: rank #{rank + 1} of {len(scored2)}")
report('TVD rises sharply', after['tvd'] - target['tvd'] >= 0.15,
       f"TVD {target['tvd']:.3f} -> {after['tvd']:.3f} (moved {move} votes {donor} -> צף)")
report('esoteric list named as deviating party', after['dev_symbol'] == 'צף',
       f"dev_party={after['dev_party']!r} dev_symbol={after['dev_symbol']!r} +{after['dev_pts']} pts")

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
