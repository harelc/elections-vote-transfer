#!/usr/bin/env python3
"""
Ballot data for site/turnout.html: what if turnout rises on the simulated K26?

The page computes everything live from per-ballot eligible voters, voters and
list votes. This script exports those and prints reference numbers from the
same model so the page can be checked against it.

The model. A ballot's non-voters are assumed to lean like its voters. Bloc j
has a relative motivation w_j: its non-voters turn out at rate q * w_j, with q
solved so national turnout hits the target. Ballot b gains

  q * (non-voters in b) * sum over lists of (list's share of b's votes * w)

capped so no ballot passes CAP turnout, split between lists in the same
proportions. With all w equal, each ballot closes the same share of its gap to
100% (low-turnout ballots catch up fastest) until it hits the ceiling. Below
the forecast, voters stay home at rate |q| / w_j.

The forecast is the K25 ballot turnout times one national factor
(see simulate_election_26.simulate). With K26_REAL=1 the starting point is
the official count in ballot26.csv instead.

Usage:
    python generate_turnout_sim.py
    K26_REAL=1 python generate_turnout_sim.py
"""

import json
import os

import numpy as np
import pandas as pd

from simulate_election_26 import E26_PARTIES, SURPLUS_AGREEMENTS, bader_ofer

CSV = 'ballot26.csv'
OUT = 'site/data/turnout_ballots_26.json'
CAP = 0.90
K25_TURNOUT = round(4794593 / 6788804, 5)

BLOCS = {
    'right':      ['מחל', 'שס', 'ג', 'ט', 'ב', 'ך', 'די', 'זך', 'ני'],
    'leftcenter': ['רק', 'ל', 'אמת', 'דרך'],
    'arab':       ['ודם', 'עם'],
}


def load():
    df = pd.read_csv(CSV, encoding='utf-8-sig')
    df = df[df['בזב'] > 0]
    in_bloc = {s for syms in BLOCS.values() for s in syms}
    symbols = [s for s in E26_PARTIES if s in df.columns and s in in_bloc]
    lists = [c for c in df.columns[df.columns.get_loc('כשרים') + 1:] if c not in ('חיצוניות', 'חיצוניים', 'קלפי אחרת')]
    E = df['בזב'].to_numpy(float)
    V = df['מצביעים'].to_numpy(float)
    P = df[symbols].to_numpy(float)
    rest = [c for c in lists if c not in symbols]
    others = float(df[rest].to_numpy(float).sum()) if rest else 0.0
    valid = P.sum() + others
    for c in rest:
        if df[c].sum() >= 0.0325 * valid:
            print(f'warning: {c} passes the threshold but is not in E26_PARTIES and BLOCS; it counts as "others"')
    return symbols, E, V, P, others


def mobilize(P, E, V, w, q):
    """Ballot × list votes and ballot voters when turnout propensity moves by q."""
    valid = P.sum(axis=1)
    if q >= 0:
        share = np.divide(P, valid[:, None], out=np.zeros_like(P), where=valid[:, None] > 0)
        gain = q * (E - V)[:, None] * share * w[None, :]
        want = gain.sum(axis=1)
        room = np.maximum(0, CAP * E - V)
        scale = np.divide(np.minimum(want, room), want, out=np.zeros_like(want), where=want > 0)
        gain *= scale[:, None]
    else:
        gain = q * P / w[None, :]
    added = gain.sum(axis=1) * np.divide(V, valid, out=np.ones_like(V), where=valid > 0)
    return P + gain, V + added


def solve(P, E, V, w, target):
    lo, hi = -1.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if mobilize(P, E, V, w, mid)[1].sum() / E.sum() < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    symbols, E, V, P, others = load()
    names = {sym: E26_PARTIES[sym][0] for sym in symbols}
    sym_of = {n: s for s, n in names.items()}
    out = {
        'election': 26,
        'simulated': os.environ.get('K26_REAL') != '1',
        'others': int(others),
        'cap': CAP,
        'k25_turnout': K25_TURNOUT,
        'baseline_turnout': round(float(V.sum() / E.sum()), 5),
        'parties': [{'symbol': s, 'name': names[s], 'color': E26_PARTIES[s][1]} for s in symbols],
        'agreements': [[sym_of[a], sym_of[b]] for a, b in SURPLUS_AGREEMENTS if a in sym_of and b in sym_of],
        'blocs': {b: [s for s in syms if s in symbols] for b, syms in BLOCS.items()},
        'E': [int(x) for x in E],
        'V': [int(x) for x in V],
        'P': [[int(x) for x in P[:, k]] for k in range(len(symbols))],
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'Wrote {OUT}: {len(E):,} ballots, forecast turnout {V.sum() / E.sum():.2%}')

    bloc_idx = {b: np.array([s in syms for s in symbols]) for b, syms in BLOCS.items()}
    presets = {
        'everyone': {},
        'right ×2': {'right': 2},
        'leftcenter ×2': {'leftcenter': 2},
        'arab ×2': {'arab': 2},
        'leftcenter+arab ×2': {'leftcenter': 2, 'arab': 2},
    }
    for label, motivation in presets.items():
        w = np.ones(len(symbols))
        for b, m in motivation.items():
            w[bloc_idx[b]] = m
        cells = []
        for t in (0.70, 0.743, 0.80, 0.85):
            ballots, _ = mobilize(P, E, V, w, solve(P, E, V, w, t))
            vm = {names[s]: v for s, v in zip(symbols, ballots.sum(axis=0))}
            seats, _, _ = bader_ofer(vm, agreements=SURPLUS_AGREEMENTS)
            b = {k: sum(seats[names[s]] for s in syms) for k, syms in BLOCS.items()}
            cells.append(f'{t:.1%}: R{b["right"]:>3} LC{b["leftcenter"]:>3} A{b["arab"]:>3}')
        print(f'{label:20} ' + '   '.join(cells))


if __name__ == '__main__':
    main()
