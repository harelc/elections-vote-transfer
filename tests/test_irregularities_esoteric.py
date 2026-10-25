#!/usr/bin/env python3
"""Sensitivity tests for detect_unexpected_party_votes (run from repo root).

    venv/bin/python tests/test_irregularities_esoteric.py

The planted-misfeed cases simulate a column misfeed: votes moved from a
major list into an esoteric list's column in one ballot box. A useful
detector must flag a large misfeed (60 votes) AND a small one (12 votes in
a settlement where the list otherwise gets ~0), must stay quiet on the
unmodified file except for a small number of boxes, and must not flag a
list that is genuinely strong across a whole settlement (its other boxes
lift the leave-one-out prediction).

Each check prints PASS/FAIL with its evidence; exits non-zero on any FAIL.
"""
import sys

sys.path.insert(0, '.')
import generate_irregularities_data as g

results = []


def report(name, ok, evidence):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {evidence}")


def context(df, party_cols):
    tv = df[party_cols].sum()
    profile = {c: tv[c] / tv.sum() for c in party_cols}
    sv = df.groupby('שם ישוב')['כשרים'].sum().to_dict()
    sp = df.groupby('שם ישוב')[party_cols].sum().to_dict('index')
    return profile, sp, sv


def detect(df, party_cols, idx):
    profile, sp, sv = context(df, party_cols)
    return g.detect_unexpected_party_votes(df.loc[idx], party_cols, profile, '25', sp, sv)


df = g.load_ballot_data('25')
party_cols = g.get_party_columns(df, '25')
majors = set(g.ELECTIONS['25']['major_parties']['symbols'])
esoteric = [c for c in party_cols if c not in majors]

# Pick a Jerusalem box with >= 250 valid votes where some esoteric list is
# at ~0 both in the box and across the settlement (the misfeed canvas).
jer = df[(df['שם ישוב'] == 'ירושלים') & (df['כשרים'] >= 250)]
base_idx = eso_col = None
for idx, row in jer.iterrows():
    for col in esoteric:
        if row[col] == 0 and df[df['שם ישוב'] == 'ירושלים'][col].sum() <= 5:
            base_idx, eso_col = idx, col
            break
    if base_idx is not None:
        break
assert base_idx is not None, 'no suitable Jerusalem box found'

# Negative control: the unmodified box is not flagged.
n0, _ = detect(df, party_cols, base_idx)
report('unmodified box not flagged', n0 == 0, f'box {base_idx}, esoteric column {eso_col!r}')

# Plant a large misfeed: 60 votes moved from the box's biggest major list.
big = df.copy()
donor = max((c for c in party_cols if c in majors), key=lambda c: big.loc[base_idx, c])
big.loc[base_idx, eso_col] += 60
big.loc[base_idx, donor] -= 60
n1, info1 = detect(big, party_cols, base_idx)
report('planted 60-vote misfeed flagged', n1 >= 1 and any(i['party'] == eso_col for i in info1),
       f'{donor} -> {eso_col}: {info1}')

# Plant a small misfeed: only 12 votes (2-4% of a typical box, far below
# the old small_party_spike 5%-share threshold).
small = df.copy()
small.loc[base_idx, eso_col] += 12
small.loc[base_idx, donor] -= 12
n2, info2 = detect(small, party_cols, base_idx)
report('planted 12-vote misfeed flagged', n2 >= 1 and any(i['party'] == eso_col for i in info2),
       f'{donor} -> {eso_col}: {info2}')

# Genuine stronghold guard: give the same esoteric list 10% in five boxes
# of one mid-size settlement; the leave-one-out prediction must absorb it.
strong = df.copy()
settlements = (strong.groupby('שם ישוב')['כשרים'].sum())
mid = settlements[(settlements >= 1500) & (settlements <= 4000)].index
guard_ok, guard_ev = False, 'no suitable settlement'
for name in mid:
    idxs = strong[strong['שם ישוב'] == name].index[:5]
    if len(idxs) < 5:
        continue
    s2 = strong.copy()
    for i in idxs:
        s2.loc[i, eso_col] += int(s2.loc[i, 'כשרים'] * 0.10)
    n3, _ = detect(s2, party_cols, idxs[0])
    guard_ok, guard_ev = (n3 == 0), f'{name} box {idxs[0]}: 10% in 5 boxes, flagged={n3}'
    if guard_ok:
        break
report('settlement-wide stronghold not flagged', guard_ok, guard_ev)

# Flood control on the real file: well under 1% of analysed boxes.
profile, sp, sv = context(df, party_cols)
flagged = sum(
    1 for _, row in df.iterrows()
    if row.get('כשרים', 0) >= g.MIN_VOTES
    and g.detect_unexpected_party_votes(row, party_cols, profile, '25', sp, sv)[0] > 0
)
total = len(df[df['כשרים'] >= g.MIN_VOTES])
report('real K25 flags are rare', flagged < total * 0.01, f'{flagged}/{total} boxes ({100 * flagged / total:.2f}%)')

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
