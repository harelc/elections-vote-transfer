#!/usr/bin/env python3
"""
Estimate the Dirichlet concentration parameter alpha for each historical
election transition using a method-of-moments approach.

Model:
    For each ballot b with K-prev vote vector X_b and recovered transfer
    matrix M, the K-curr proportions y_b are drawn from
    Dirichlet(alpha * p̂_b) where p̂_b = (X_b @ M) / sum.

    Under this model: Var(y_{bi}) = p̂_{bi}(1 - p̂_{bi}) / (alpha + 1).

    Method-of-moments estimator (pooled across cells):
        alpha + 1 = sum_b sum_i p̂_{bi}(1 - p̂_{bi})
                  / sum_b sum_i (y_{bi} - p̂_{bi})^2

A separate per-row estimate is also reported (alpha varies by source party
because some parties shed voters more chaotically than others).
"""

import json
import numpy as np
from generate_transfer_data import VoteTransferAnalyzer


TRANSITIONS = [
    ('16', '17'), ('17', '18'), ('18', '19'), ('19', '20'),
    ('20', '21'), ('21', '22'), ('22', '23'), ('23', '24'), ('24', '25'),
]


def estimate_alpha(election_from, election_to):
    """Estimate alpha for a single transition. Returns dict of stats."""
    analyzer = VoteTransferAnalyzer(method='convex', verbose=False)

    df_from, config_from = analyzer.load_election_data(election_from)
    df_to, config_to = analyzer.load_election_data(election_to)

    parties_from = config_from['major_parties']
    parties_to = config_to['major_parties']
    votes_from, _, _ = analyzer.extract_party_votes(
        df_from, parties_from['symbols'], parties_from['names']
    )
    votes_to, _, _ = analyzer.extract_party_votes(
        df_to, parties_to['symbols'], parties_to['names']
    )

    # Match precincts
    common_ids = [bid for bid in df_to.index if bid in df_from.index]
    X = votes_from.loc[common_ids].values.astype(float)
    Y = votes_to.loc[common_ids].values.astype(float)

    # Recover transfer matrix
    M = analyzer.solve_transfer_matrix_convex(X, Y)
    if M is None:
        return None

    # Convert to per-ballot proportions
    X_totals = X.sum(axis=1, keepdims=True)
    Y_totals = Y.sum(axis=1, keepdims=True)
    valid = (X_totals.flatten() > 0) & (Y_totals.flatten() > 0)
    X = X[valid]
    Y = Y[valid]
    X_totals = X_totals[valid]
    Y_totals = Y_totals[valid]

    # Predicted K-curr proportions per ballot: (X @ M) row-normalized
    pred = X @ M                                  # (B, K_to)
    pred_props = pred / pred.sum(axis=1, keepdims=True).clip(min=1e-9)
    actual_props = Y / Y_totals

    # Pooled method-of-moments estimator
    numer = float((pred_props * (1 - pred_props)).sum())
    denom = float(((actual_props - pred_props) ** 2).sum())
    alpha_pooled = numer / denom - 1 if denom > 0 else float('inf')

    # Per-destination-party alpha: column-wise residual variance
    # Estimates "how tightly does party j cluster around its matrix prediction"
    n_dst = Y.shape[1]
    per_dst = {}
    dst_names = list(parties_to['names'])
    for j in range(n_dst):
        n = float((pred_props[:, j] * (1 - pred_props[:, j])).sum())
        d = float(((actual_props[:, j] - pred_props[:, j]) ** 2).sum())
        if d > 0 and n > 0:
            per_dst[dst_names[j]] = (n / d - 1, int(pred_props[:, j].mean() * 1000) / 10)

    avg_ballot_size = float(Y_totals.mean())

    return {
        'alpha_pooled': alpha_pooled,
        'avg_ballot_size': avg_ballot_size,
        'n_ballots': int(valid.sum()),
        'per_dst': per_dst,
    }


def main():
    print(f"{'Transition':<12} {'alpha':>8}  {'avg N':>7}  {'over-disp':>10}")
    print('-' * 50)
    results = {}
    for src, dst in TRANSITIONS:
        try:
            r = estimate_alpha(src, dst)
        except Exception as e:
            print(f'{src}→{dst:<8}  FAILED: {e}')
            continue
        if r is None:
            continue
        results[(src, dst)] = r
        # Over-dispersion ratio: ballot size / alpha. >1 means more variance
        # than independent multinomial sampling would predict.
        overdisp = r['avg_ballot_size'] / r['alpha_pooled'] if r['alpha_pooled'] > 0 else float('inf')
        print(f"{src}→{dst:<8}  {r['alpha_pooled']:>8.1f}  {r['avg_ballot_size']:>7.0f}  {overdisp:>9.1f}×")

    print('\nPer-destination-party alpha (sorted by alpha desc — high = tight cluster, low = volatile):')
    for (src, dst), r in results.items():
        if not r['per_dst']:
            continue
        print(f'\n  K{src}→K{dst}:')
        top = sorted(r['per_dst'].items(), key=lambda kv: -kv[1][0])
        for party, (a, mean_share) in top:
            print(f'    {party:<22}  alpha={a:>7.1f}  (mean share={mean_share:.1f}%)')

    # Serialize to JSON for downstream use (website + paper)
    out = {}
    for (src, dst), r in results.items():
        out[f'{src}_to_{dst}'] = {
            'alpha_pooled': round(r['alpha_pooled'], 2),
            'avg_ballot_size': round(r['avg_ballot_size'], 1),
            'n_ballots': r['n_ballots'],
            'overdispersion': round(r['avg_ballot_size'] / r['alpha_pooled'], 2)
                if r['alpha_pooled'] > 0 else None,
            'per_destination': {
                party: {'alpha': round(a, 2), 'mean_share_pct': round(mean_share, 2)}
                for party, (a, mean_share) in r['per_dst'].items()
            },
        }
    out_path = 'site/data/alpha_estimates.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
