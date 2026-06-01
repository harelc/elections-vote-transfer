#!/usr/bin/env python3
"""Prepare data for the fraud-detection simulator.

Supports any K(N-1) → K(N) transition for which we have tsne_<N-1>.json,
tsne_<N>.json, and transfer_<N-1>_to_<N>.json. Defaults to both 24→25
and 25→26.

Output (per transition): site/data/fraud_sim_<from>_<to>.json with:
  meta:        {from, to, is_simulated, scenarios, blocs}
  parties_from / parties_to: [{name, symbol, color}]
  T:           transition matrix, rows = sources, cols = destinations
  ballots:     [{n, b, sid, v, b26, pred}] for common ballots
               (key 'b26' is the destination-year vote-share vector;
                kept as the name regardless of year for compactness)
"""
import argparse
import json
import os
import numpy as np

# Bloc definitions, lifted from fraud-detection/fraud_detection_e26.py.
# Symbols here are the *destination-year* symbols (in our scoring the
# attack direction lives in the destination party space).
BLOC_DEFINITIONS = {
    '25': {
        'right':      ['מחל', 'ט', 'שס', 'ג'],
        'leftcenter': ['פה', 'כן', 'ל', 'אמת', 'מרצ'],
        'arab':       ['עם', 'ום', 'ד'],
    },
    '26': {
        'right':      ['מחל', 'שס', 'ג', 'ט', 'עי', 'מי'],
        'leftcenter': ['נב', 'ל', 'דמ', 'יר', 'כל'],
        'arab':       ['ום', 'עם', 'ד'],
    },
}

# Per-target scenario catalog. Some scenarios are bloc-to-bloc;
# others are pair (single party → single party). Symbols are the
# destination-year symbols.
SCENARIOS_BY_YEAR = {
    '25': [
        {'id': 'right_to_left',  'kind': 'bloc', 'src': 'right',      'dst': 'leftcenter', 'label': 'גוש הימין ← גוש שמאל-מרכז'},
        {'id': 'left_to_right',  'kind': 'bloc', 'src': 'leftcenter', 'dst': 'right',      'label': 'גוש שמאל-מרכז ← גוש הימין'},
        {'id': 'jewish_to_arab', 'kind': 'bloc', 'src': 'right',      'dst': 'arab',       'label': 'הימין ← המפלגות הערביות'},
        {'id': 'intra_right',    'kind': 'pair', 'src': 'מחל',         'dst': 'ט',          'label': 'בתוך הימין: ליכוד ← הציונות הדתית'},
        {'id': 'intra_arab',     'kind': 'pair', 'src': 'עם',          'dst': 'ום',         'label': 'בתוך הערביות: רע״ם ← חד״ש-תע״ל'},
        {'id': 'lapid_likud',    'kind': 'pair', 'src': 'פה',          'dst': 'מחל',        'label': 'יש עתיד ← ליכוד'},
        {'id': 'custom',         'kind': 'pair', 'src': None,         'dst': None,         'label': 'התאמה אישית (זוג מפלגות)'},
    ],
    '26': [
        {'id': 'right_to_left',  'kind': 'bloc', 'src': 'right',      'dst': 'leftcenter', 'label': 'גוש הימין ← גוש שמאל-מרכז'},
        {'id': 'left_to_right',  'kind': 'bloc', 'src': 'leftcenter', 'dst': 'right',      'label': 'גוש שמאל-מרכז ← גוש הימין'},
        {'id': 'jewish_to_arab', 'kind': 'bloc', 'src': 'right',      'dst': 'arab',       'label': 'הימין ← המפלגות הערביות'},
        {'id': 'intra_right',    'kind': 'pair', 'src': 'מחל',         'dst': 'ט',          'label': 'בתוך הימין: ליכוד ← הציונות הדתית'},
        {'id': 'intra_arab',     'kind': 'pair', 'src': 'עם',          'dst': 'ום',         'label': 'בתוך הערביות: רע״ם ← חד״ש-תע״ל'},
        {'id': 'lapid_likud',    'kind': 'pair', 'src': 'נב',          'dst': 'מחל',        'label': 'ביחד ← ליכוד'},
        {'id': 'custom',         'kind': 'pair', 'src': None,         'dst': None,         'label': 'התאמה אישית (זוג מפלגות)'},
    ],
}

# Which transitions yield simulated destination data
SIMULATED_TARGETS = {'26'}


def load_ballot_lookup(tsne):
    return {s['n'] + '|' + s['b']: s for s in tsne['stations']}


def normalize_or_uniform(v):
    v = np.maximum(v, 0)
    s = v.sum()
    if s <= 0:
        return np.ones_like(v) / len(v)
    return v / s


def prepare_transition(from_year, to_year):
    t_from = json.load(open(f'site/data/tsne_{from_year}.json', encoding='utf-8'))
    t_to = json.load(open(f'site/data/tsne_{to_year}.json', encoding='utf-8'))
    T_obj = json.load(open(f'site/data/transfer_{from_year}_to_{to_year}.json', encoding='utf-8'))

    parties_from = T_obj['nodes_from']
    parties_to = T_obj['nodes_to']
    name_to_from = {p['name']: i for i, p in enumerate(parties_from)}
    name_to_to = {p['name']: i for i, p in enumerate(parties_to)}
    Pf, Pt = len(parties_from), len(parties_to)

    T = np.zeros((Pf, Pt))
    for edge in T_obj['transfers']:
        if edge['source'] in name_to_from and edge['target'] in name_to_to:
            i, j = name_to_from[edge['source']], name_to_to[edge['target']]
            T[i, j] = edge['percentage'] / 100.0
    row_sums = T.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1)
    T = T / row_sums

    i_from = load_ballot_lookup(t_from)
    i_to = load_ballot_lookup(t_to)
    common = sorted(set(i_from) & set(i_to))
    print(f"[{from_year}→{to_year}] common ballots: {len(common)}")

    ballots = []
    skipped = 0
    for key in common:
        sf, st = i_from[key], i_to[key]
        pf_raw = sf.get('p', {})
        pt_raw = st.get('p', {})
        bf = np.array([pf_raw.get(p['name'], 0.0) for p in parties_from]) / 100.0
        bt = np.array([pt_raw.get(p['name'], 0.0) for p in parties_to]) / 100.0
        if bf.sum() < 0.5 or bt.sum() < 0.5:
            skipped += 1
            continue
        bf = normalize_or_uniform(bf)
        bt = normalize_or_uniform(bt)
        pred = normalize_or_uniform(bf @ T)
        ballots.append({
            'n': sf.get('n', ''),
            'b': sf.get('b', ''),
            'sid': sf.get('s'),
            'v': st.get('v', 0),
            'b26': [int(round(x * 1000)) for x in bt],     # kept name 'b26' for compactness across both files
            'pred': [int(round(x * 1000)) for x in pred],
        })
    print(f"[{from_year}→{to_year}] kept: {len(ballots)} (skipped {skipped})")

    def party_lite(p):
        return {'name': p['name'], 'symbol': p['symbol'], 'color': p.get('color', '#64748b')}

    out = {
        'meta': {
            'from_year': from_year,
            'to_year': to_year,
            'is_simulated': to_year in SIMULATED_TARGETS,
            'blocs': BLOC_DEFINITIONS[to_year],
            'scenarios': SCENARIOS_BY_YEAR[to_year],
        },
        'parties_25': [party_lite(p) for p in parties_from],   # kept name for backward compat
        'parties_26': [party_lite(p) for p in parties_to],
        'T': [[round(float(v), 5) for v in row] for row in T],
        'ballots': ballots,
    }
    path = f'site/data/fraud_sim_{from_year}_{to_year}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    size_kb = os.path.getsize(path) / 1024
    print(f"[{from_year}→{to_year}] wrote {path} ({size_kb:.1f} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--transitions', nargs='+', default=['24_25', '25_26'])
    args = ap.parse_args()
    for t in args.transitions:
        fy, ty = t.split('_')
        prepare_transition(fy, ty)


if __name__ == '__main__':
    main()
