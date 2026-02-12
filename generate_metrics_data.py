#!/usr/bin/env python3
"""
Generate metrics data for the website: Pedersen indices, HHI, cosine similarity.
Outputs site/data/metrics.json

Written by Harel Cain, 2025
"""

import json
import numpy as np
from collections import defaultdict
from pathlib import Path


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def pedersen_index(props1, props2):
    """Pedersen volatility index between two elections for a settlement."""
    all_parties = set(list(props1.keys()) + list(props2.keys()))
    return sum(abs(props1.get(p, 0) - props2.get(p, 0)) for p in all_parties) / 2


def main():
    # Load all map data
    all_maps = {}
    for eid in [21, 22, 23, 24, 25]:
        all_maps[eid] = load_json(f'site/data/map_{eid}.json')

    # ============================================================
    # 1. Settlement-level Pedersen indices
    # ============================================================
    settlement_props = {}
    settlement_voters = {}
    for eid in [21, 22, 23, 24, 25]:
        for s in all_maps[eid]['settlements']:
            name = s['name']
            if name not in settlement_props:
                settlement_props[name] = {}
                settlement_voters[name] = {}
            settlement_props[name][eid] = s.get('proportions', {})
            settlement_voters[name][eid] = s.get('voters', 0)

    settlement_pedersen = {}
    transitions = [(21, 22), (22, 23), (23, 24), (24, 25)]
    for name, data in settlement_props.items():
        per_transition = {}
        for e1, e2 in transitions:
            if e1 in data and e2 in data:
                pi = pedersen_index(data[e1], data[e2])
                per_transition[f'{e1}_to_{e2}'] = round(pi, 1)
        if per_transition:
            avg = round(np.mean(list(per_transition.values())), 1)
            settlement_pedersen[name] = {
                'transitions': per_transition,
                'average': avg,
            }

    # Rank settlements by average Pedersen
    ranked = sorted(settlement_pedersen.items(), key=lambda x: -x[1]['average'])
    for rank, (name, data) in enumerate(ranked, 1):
        data['rank'] = rank
    total_settlements = len(ranked)

    # National median and percentiles
    all_avg = [d['average'] for _, d in settlement_pedersen.items()]
    national_median = round(float(np.median(all_avg)), 1)
    national_mean = round(float(np.mean(all_avg)), 1)

    # ============================================================
    # 2. Party-level metrics (HHI, cosine similarity)
    # ============================================================
    # Compute settlement-level party proportions for E25
    e25_settlements = {}
    for s in all_maps[25]['settlements']:
        name = s['name']
        e25_settlements[name] = s.get('proportions', {})

    settlement_names = sorted(e25_settlements.keys())
    parties_25 = list(all_maps[25]['parties'])
    party_names = [p['name'] for p in parties_25]

    # Build settlement-level voter counts
    e25_voter_counts = {}
    for s in all_maps[25]['settlements']:
        e25_voter_counts[s['name']] = s.get('voters', 0)

    # Build settlement-level vote vectors per party (weighted by voters)
    party_vectors = {}
    for party in party_names:
        vec = np.array([
            e25_settlements.get(s, {}).get(party, 0) / 100.0 * e25_voter_counts.get(s, 0)
            for s in settlement_names
        ])
        party_vectors[party] = vec

    # HHI per party
    party_hhi = {}
    for party in party_names:
        vec = party_vectors[party]
        total = vec.sum()
        if total > 0:
            shares = vec / total
            hhi = float(np.sum(shares ** 2))
            effective = round(1.0 / hhi) if hhi > 0 else 0
            party_hhi[party] = {
                'hhi': round(hhi, 4),
                'effective_settlements': effective,
            }

    # Cosine similarity between all party pairs
    from scipy.spatial.distance import cosine
    party_cosine = {}
    for p1 in party_names:
        sims = {}
        v1 = party_vectors[p1]
        if v1.sum() == 0:
            continue
        for p2 in party_names:
            if p1 == p2:
                continue
            v2 = party_vectors[p2]
            if v2.sum() == 0:
                continue
            sim = 1 - cosine(v1, v2)
            sims[p2] = round(sim, 3)
        if sims:
            party_cosine[p1] = sims

    # Station-level correlation between parties
    # Load tsne data for ballot-level props
    tsne_25 = load_json('site/data/tsne_25.json')
    ballot_props = {}
    for s in tsne_25['stations']:
        props = s.get('p', {})
        for party in party_names:
            if party not in ballot_props:
                ballot_props[party] = []
            ballot_props[party].append(props.get(party, 0))

    from scipy.stats import pearsonr
    party_correlations = {}
    for p1 in party_names:
        if p1 not in ballot_props:
            continue
        corrs = {}
        v1 = np.array(ballot_props[p1])
        for p2 in party_names:
            if p1 == p2 or p2 not in ballot_props:
                continue
            v2 = np.array(ballot_props[p2])
            r, _ = pearsonr(v1, v2)
            corrs[p2] = round(r, 3)
        if corrs:
            party_correlations[p1] = corrs

    # Settlement concentration (top N settlements for each party)
    party_concentration = {}
    for party in party_names:
        vec = party_vectors[party]
        total = vec.sum()
        if total == 0:
            continue
        # Sort settlements by party share
        idxs = np.argsort(-vec)
        cum = 0
        top_50_idx = None
        top_90_idx = None
        for i, idx in enumerate(idxs):
            cum += vec[idx]
            if top_50_idx is None and cum >= total * 0.5:
                top_50_idx = i + 1
            if top_90_idx is None and cum >= total * 0.9:
                top_90_idx = i + 1
                break

        # Top 5 settlements
        top5 = []
        for idx in idxs[:5]:
            top5.append({
                'name': settlement_names[idx],
                'share': round(float(vec[idx] / total * 100), 1)
            })

        party_concentration[party] = {
            'settlements_for_50pct': top_50_idx,
            'settlements_for_90pct': top_90_idx,
            'total_settlements': int(np.sum(vec > 0)),
            'top5': top5,
        }

    # ============================================================
    # 3. Assemble output
    # ============================================================
    output = {
        'settlement_pedersen': settlement_pedersen,
        'national_stats': {
            'median_pedersen': national_median,
            'mean_pedersen': national_mean,
            'total_settlements': total_settlements,
        },
        'party_hhi': party_hhi,
        'party_cosine_similarity': party_cosine,
        'party_ballot_correlations': party_correlations,
        'party_concentration': party_concentration,
    }

    outpath = Path('site/data/metrics.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {outpath}")
    print(f"  {len(settlement_pedersen)} settlements with Pedersen indices")
    print(f"  {len(party_hhi)} parties with HHI")
    print(f"  National median Pedersen: {national_median}%")
    print(f"  National mean Pedersen: {national_mean}%")


if __name__ == '__main__':
    main()
