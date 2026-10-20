#!/usr/bin/env python3
"""
Ballot-level bootstrap intervals for the Sankey transfer percentages.

Each draw resamples the matched ballots and re-solves the same constrained
least-squares problem the page displays (rows sum to 1, cells in range,
forbidden cells fixed at zero). The interval is the 2.5 and 97.5 percentiles
of that cell. 25→26 is omitted from the default run. refresh_k26.py adds a
short run (small --B, no abstention) once a real count crosses a coverage
milestone; run --only 25_to_26 at full B by hand once the count is final.
"""

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import cvxpy as cvx
import numpy as np

from generate_transfer_data import VoteTransferAnalyzer

PAIRS = [
    ('16', '17'),
    ('17', '18'),
    ('18', '19'),
    ('19', '20'),
    ('20', '21'),
    ('21', '22'),
    ('22', '23'),
    ('23', '24'),
    ('24', '25'),
]
NO_ABSTENTION = {('16', '17'), ('17', '18')}
B = 200
SEED = 42


def make_solver(n, p, q, row_sum, zero_cells):
    """One compiled problem. Each draw only replaces the ballot matrices."""
    Xp = cvx.Parameter((n, p))
    Yp = cvx.Parameter((n, q))
    M = cvx.Variable((p, q))
    constraints = [M >= 0, M <= row_sum, cvx.sum(M, axis=1) == row_sum]
    for i, j in zero_cells:
        constraints.append(M[i, j] == 0)
    prob = cvx.Problem(cvx.Minimize(cvx.sum_squares(Xp @ M - Yp)), constraints)

    def solve(Xb, Yb):
        Xp.value = Xb
        Yp.value = Yb
        prob.solve(solver='CLARABEL', warm_start=True)
        if M.value is None:
            raise RuntimeError(prob.status)
        return np.array(M.value, dtype=float)

    return solve


def r_squared(X, Y, M):
    resid = Y - X @ M
    ss_res = np.sum(resid * resid)
    centered = Y - Y.mean(axis=0)
    ss_tot = np.sum(centered * centered)
    return 1 - ss_res / ss_tot


def draw_range(election_from, election_to, include_abstention, seed, start, stop):
    """Bootstrap draws start..stop-1. The first slice also solves the point estimate.

    The RNG is replayed from the seed, so splitting the draws across workers
    gives the same resamples as one serial run.
    """
    analyzer = VoteTransferAnalyzer(
        method='convex', min_flow_threshold=0, verbose=False,
        include_abstention=include_abstention,
    )
    design = analyzer.design_matrices(election_from, election_to)
    X, Y = design['X'], design['Y']
    n, p = X.shape
    q = Y.shape[1]
    solve = make_solver(n, p, q, design['row_sum'], design['zero_cells'])

    point, t_point = None, 0.0
    if start == 0:
        t0 = time.time()
        point = solve(X, Y)
        t_point = time.time() - t0

    samples = np.empty((stop - start, p, q))
    r2s = np.empty(stop - start)
    rng = np.random.RandomState(seed)
    failed = 0
    t1 = time.time()
    for b in range(stop):
        idx = rng.randint(0, n, size=n)
        if b < start:
            continue
        k = b - start
        try:
            Mb = solve(X[idx], Y[idx])
        except RuntimeError:
            failed += 1
            samples[k] = np.nan
            r2s[k] = np.nan
            continue
        samples[k] = Mb
        r2s[k] = r_squared(X[idx], Y[idx], Mb)
    return {
        'start': start,
        'samples': samples,
        'r2s': r2s,
        'failed': failed,
        'elapsed': time.time() - t1,
        'point': point,
        'point_seconds': t_point,
        'names_from': design['names_from'],
        'names_to': design['names_to'],
    }


def summarize(parts):
    parts = sorted(parts, key=lambda part: part['start'])
    first = parts[0]
    samples = np.concatenate([part['samples'] for part in parts])
    r2s = np.concatenate([part['r2s'] for part in parts])
    draws = len(r2s)
    lo = np.nanpercentile(samples, 2.5, axis=0) * 100
    hi = np.nanpercentile(samples, 97.5, axis=0) * 100
    r2_ok = r2s[np.isfinite(r2s)]
    return {
        'point': first['point'] * 100,
        'lo': lo,
        'hi': hi,
        'names_from': first['names_from'],
        'names_to': first['names_to'],
        'point_seconds': round(first['point_seconds'], 2),
        'draw_seconds': round(sum(part['elapsed'] for part in parts) / max(draws, 1), 3),
        'failed': sum(part['failed'] for part in parts),
        'r2_ci': [
            round(float(np.percentile(r2_ok, 2.5)), 3),
            round(float(np.percentile(r2_ok, 97.5)), 3),
        ],
    }


def bootstrap(election_from, election_to, include_abstention, B, seed, probe=0):
    draws = probe or B
    return summarize([draw_range(election_from, election_to, include_abstention, seed, 0, draws)])


def spec_key(election_from, election_to, include_abstention):
    key = f'{election_from}_to_{election_to}'
    return key + '_abstention' if include_abstention else key


def build_payload(key, result, B):
    page, page_r2, precincts = published(key)
    cells = {}
    for i, src in enumerate(result['names_from']):
        for j, dst in enumerate(result['names_to']):
            if (src, dst) not in page:
                continue
            cells[f'{src}\t{dst}'] = display_interval(
                page[(src, dst)], result['point'][i, j],
                result['lo'][i, j], result['hi'][i, j], 1,
            )
    r2_lo, r2_hi = result['r2_ci']
    return {
        'B': B,
        'failed': result['failed'],
        'r2_ci': [min(r2_lo, round(page_r2, 3)), max(r2_hi, round(page_r2, 3))],
        # The page hides these intervals once the published transfer stops matching.
        'common_precincts': precincts,
        'r_squared': page_r2,
        'cells': cells,
    }


def published(key):
    path = f'site/data/transfer_{key}.json'
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    cells = {(t['source'], t['target']): t['percentage'] for t in data['transfers']}
    return cells, data['stats']['r_squared'], data['stats']['common_precincts']


def display_interval(page, point, lo, hi, ndigits):
    """Bootstrap spread, shifted onto the percentage the page already shows.

    A second solve of the same problem can sit a few points away on a
    poorly identified row. The reported interval covers that re-solve and
    the resampling spread, and it always contains the number on the ribbon.
    """
    show_lo = min(page, point, lo + page - point)
    show_hi = max(page, point, hi + page - point)
    show_lo = min(100.0, max(0.0, show_lo))
    show_hi = min(100.0, max(0.0, show_hi))
    return [round(float(show_lo), ndigits), round(float(show_hi), ndigits)]


def probe():
    """One published transition: how far the fast solve sits from the page."""
    result = bootstrap('24', '25', False, B=8, seed=SEED, probe=8)
    page, _r2, _precincts = published('24_to_25')
    worst = 0
    worst_cell = None
    for i, src in enumerate(result['names_from']):
        for j, dst in enumerate(result['names_to']):
            if (src, dst) not in page:
                continue
            gap = abs(result['point'][i, j] - page[(src, dst)])
            if gap > worst:
                worst = gap
                worst_cell = (src, dst, round(float(result['point'][i, j]), 2), page[(src, dst)])
    print(
        f"point {result['point_seconds']}s, draw {result['draw_seconds']}s, "
        f"failed {result['failed']}, worst gap vs page {worst:.2f} at {worst_cell}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--only', default='', help='one transition key, e.g. 25_to_26; merged into the existing file')
    parser.add_argument('--B', type=int, default=B)
    parser.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 4) - 1))
    parser.add_argument('--no-abstention', action='store_true',
                        help='skip the abstention variant and drop its stale entry')
    parser.add_argument('--out', default='site/data/transfer_ci.json')
    args = parser.parse_args()
    if args.probe:
        probe()
        return

    pairs = list(PAIRS)
    if args.only:
        left, right = args.only.split('_to_')
        pairs = [(left, right)]

    specs = []
    for pair in pairs:
        specs.append((*pair, False, args.B, SEED))
        if pair not in NO_ABSTENTION and not args.no_abstention:
            specs.append((*pair, True, args.B, SEED))

    out_path = args.out
    if args.only and os.path.exists(out_path):
        with open(out_path, encoding='utf-8') as f:
            out = json.load(f)
        out.setdefault('transitions', {})
        if args.no_abstention:
            for pair in pairs:
                out['transitions'].pop(spec_key(*pair, True), None)
    else:
        out = {
            'B': args.B,
            'level': 0.95,
            'estimator': 'constrained least squares, ballot bootstrap',
            'transitions': {},
        }
    # Few transitions (e.g. --only) would leave most workers idle, so each
    # transition's draws are split into slices.
    slices = max(1, min(args.B, args.workers // len(specs)))
    bounds = np.linspace(0, args.B, slices + 1).astype(int)
    print(f'{len(specs)} transitions, B={args.B}, workers={args.workers}, '
          f'{slices} slice(s) per transition', flush=True)
    parts = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for election_from, election_to, include_abstention, B_, seed in specs:
            key = spec_key(election_from, election_to, include_abstention)
            parts[key] = []
            for start, stop in zip(bounds[:-1], bounds[1:]):
                fut = pool.submit(draw_range, election_from, election_to,
                                  include_abstention, seed, int(start), int(stop))
                futures[fut] = key
        for fut in as_completed(futures):
            key = futures[fut]
            parts[key].append(fut.result())
            if len(parts[key]) < slices:
                continue
            result = summarize(parts.pop(key))
            out['transitions'][key] = build_payload(key, result, args.B)
            print(f"{key}: point {result['point_seconds']}s, draw {result['draw_seconds']}s, "
                  f"failed {result['failed']}", flush=True)
            write_json(out_path, out)

    print(f'wrote {out_path} ({len(out["transitions"])} transitions)')


def write_json(path, data):
    """refresh_k26.py may kill this run on a timeout; never leave half a file."""
    tmp = f'{path}.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


if __name__ == '__main__':
    main()
