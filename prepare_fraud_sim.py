#!/usr/bin/env python3
"""Prepare data for the K26 fraud-detection simulator.

Output: site/data/fraud_sim_25_26.json with:
  parties_25: [{name, symbol, color}]  (12)
  parties_26: [{name, symbol, color}]  (14)
  T:          12×14 transition matrix (rows = K25 source, cols = K26 dest)
  ballots:    array of {n, b, sid, v, b25, b26, pred} for common K25↔K26 ballots
              where b25/b26/pred are per-party fractions summing to ~1
"""
import json
import numpy as np

PRIMER = 'site/data/fraud_sim_25_26.json'


def load_ballot_lookup(tsne):
    return {s['n'] + '|' + s['b']: s for s in tsne['stations']}


def normalize_or_uniform(v):
    v = np.maximum(v, 0)
    s = v.sum()
    if s <= 0:
        return np.ones_like(v) / len(v)
    return v / s


def main():
    t25 = json.load(open('site/data/tsne_25.json', encoding='utf-8'))
    t26 = json.load(open('site/data/tsne_26.json', encoding='utf-8'))
    T_obj = json.load(open('site/data/transfer_25_to_26.json', encoding='utf-8'))

    parties_25 = T_obj['nodes_from']
    parties_26 = T_obj['nodes_to']
    name_to_25 = {p['name']: i for i, p in enumerate(parties_25)}
    name_to_26 = {p['name']: i for i, p in enumerate(parties_26)}
    P25, P26 = len(parties_25), len(parties_26)

    # Build T from sparse transfers list
    T = np.zeros((P25, P26))
    for edge in T_obj['transfers']:
        i, j = name_to_25[edge['source']], name_to_26[edge['target']]
        T[i, j] = edge['percentage'] / 100.0
    # Renormalize each row to sum to 1 (so a unit-mass voter spreads to 1 unit of K26 mass).
    # In the data file rows sum to ~1.075 (population growth) — we cancel that here.
    row_sums = T.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1)
    T = T / row_sums

    i25 = load_ballot_lookup(t25)
    i26 = load_ballot_lookup(t26)
    common = sorted(set(i25) & set(i26))
    print(f"common ballots: {len(common)}")

    ballots = []
    skipped = 0
    for key in common:
        s25, s26 = i25[key], i26[key]
        p25_raw = s25.get('p', {})
        p26_raw = s26.get('p', {})

        # Per-party fraction (input shares are stored as percentages; divide by 100)
        b25 = np.array([p25_raw.get(p['name'], 0.0) for p in parties_25]) / 100.0
        b26 = np.array([p26_raw.get(p['name'], 0.0) for p in parties_26]) / 100.0

        # Filter out near-zero ballots (low turnout, suspicious data quality)
        if b25.sum() < 0.5 or b26.sum() < 0.5:
            skipped += 1
            continue

        # Renormalize to make ballot a probability vector (drops the implicit
        # "minor parties" remainder so we have clean composition data)
        b25 = normalize_or_uniform(b25)
        b26 = normalize_or_uniform(b26)

        # Predict K26 from K25 via the model
        pred = b25 @ T
        pred = normalize_or_uniform(pred)

        # Quantize per-party shares to 0.001 (0.1%) precision, store as ints.
        # That's plenty for visualization and shrinks the JSON ~3x.
        ballots.append({
            'n': s25.get('n', ''),
            'b': s25.get('b', ''),
            'sid': s25.get('s'),
            'v': s26.get('v', 0),
            'b26': [int(round(x * 1000)) for x in b26],
            'pred': [int(round(x * 1000)) for x in pred],
        })

    print(f"skipped (low-turnout): {skipped}")
    print(f"kept: {len(ballots)}")

    def party_lite(p):
        return {'name': p['name'], 'symbol': p['symbol'], 'color': p.get('color', '#64748b')}

    out = {
        'parties_25': [party_lite(p) for p in parties_25],
        'parties_26': [party_lite(p) for p in parties_26],
        'T': [[round(float(v), 5) for v in row] for row in T],
        'ballots': ballots,
    }
    with open(PRIMER, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    import os
    size_kb = os.path.getsize(PRIMER) / 1024
    print(f"wrote {PRIMER} ({size_kb:.1f} KB)")


if __name__ == '__main__':
    main()
