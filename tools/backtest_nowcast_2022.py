"""Backtest the election-night nowcast on the real K24 -> K25 (2021 -> 2022) results.

The repo's nowcast (generate_command_center_data.nowcast, live mode) is
replicated step by step: convex transfer fit on the counted matched boxes,
the published-file truncation (flows < 15,000 votes dropped, 0.1% rounding,
rows renormalised), partial pooling, one national turnout factor, double
envelopes (settlement 9999) left out. Each fix is then added on its own, and
every variant is scored against the real final K25 seats.

Run from the repo root (about 40 minutes):  python tools/backtest_nowcast_2022.py
V0 is the nowcast as it was; V5 is what the patched code does.
"""
import json
import sys
from collections import defaultdict

sys.path.insert(0, '.')
import cvxpy as cvx
import numpy as np
import pandas as pd

from generate_map_data import normalize_name
from generate_transfer_data import VoteTransferAnalyzer
from k26_live import bader_ofer
from party_config import ELECTIONS

AGREEMENTS_25 = [('הליכוד', 'הציונות הדתית'), ('ש״ס', 'יהדות התורה'),
                 ('יש עתיד', 'המחנה הממלכתי'), ('העבודה', 'מרצ')]
COALITION = ['הליכוד', 'הציונות הדתית', 'ש״ס', 'יהדות התורה']
ARAB = ['רע״ם', 'חד״ש-תע״ל', 'בל״ד']
SHRINK_K = 8000.0
MIN_FLOW = 15000


def load(e):
    c = ELECTIONS[e]
    raw = pd.read_csv(c['file'], encoding=c['encoding'])
    an = VoteTransferAnalyzer()
    df, _ = an.load_election_data(e)
    syms, names = c['major_parties']['symbols'], c['major_parties']['names']
    keep = [(s, n) for s, n in zip(syms, names) if s in df.columns]
    return raw, df, [s for s, _ in keep], [n for _, n in keep]


def match(df_from, df_to):
    """The repo's 16-25 matching: exact id, else .1 falls back to the base box."""
    from_ids = set(df_from.index)
    bases_with_zero = {i.rsplit('.', 1)[0] for i in df_to.index if i.endswith('.0')}
    pairs = []
    for t in df_to.index:
        if t in from_ids:
            pairs.append((t, t))
        elif t.endswith('.1'):
            base = t.rsplit('.', 1)[0]
            if base not in bases_with_zero and base in from_ids:
                pairs.append((base, t))
    return pairs


def fit(X, Y, row_sum):
    M = cvx.Variable((X.shape[1], Y.shape[1]))
    cons = [M >= 0, M <= row_sum, cvx.sum(M, axis=1) == row_sum]
    cvx.Problem(cvx.Minimize(cvx.sum_squares(X @ M - Y)), cons).solve(solver='CLARABEL')
    return np.clip(np.array(M.value), 0, None)


def published_view(M, nat_from):
    """What transfer_<a>_to_<b>.json keeps: >=15,000-vote flows, 0.1% rounding."""
    votes = M * nat_from[:, None]
    T = np.where(votes >= MIN_FLOW, np.round(M * 100, 1) / 100, 0.0)
    return T


def normalise_and_pool(T, origin_votes):
    rs = T.sum(axis=1, keepdims=True)
    T = np.divide(T, rs, out=np.zeros_like(T), where=rs > 0)
    g = (origin_votes @ T) / origin_votes.sum()
    for i in range(len(T)):
        w = origin_votes[i] / (origin_votes[i] + SHRINK_K) if origin_votes[i] > 0 else 0.0
        T[i] = w * T[i] + (1 - w) * g
    return T


def seats(votes_vec, names, valid_total):
    return bader_ofer(dict(zip(names, votes_vec)), agreements=AGREEMENTS_25, valid_total=valid_total)


def main():
    raw24, df24, s24, n24 = load('24')
    raw25, df25, s25, n25 = load('25')
    sectors = json.load(open('site/data/settlement_sectors.json', encoding='utf-8'))['settlements']

    # Truth: the full K25 file, double envelopes included.
    true_votes = np.array([raw25[s].sum() for s in s25], float)
    true_valid = float(raw25['כשרים'].sum())
    truth = seats(true_votes, n25, true_valid)

    pairs = match(df24, df25)
    twin = {t: f for f, t in pairs}
    X24 = df24[s24].astype(float)
    Y25 = df25[s25].astype(float)
    nat_from = np.array([raw24[s].sum() for s in s24], float)
    sh24 = X24.div(X24.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    nat24 = nat_from / nat_from.sum()
    settle24 = (X24.groupby(df24['שם ישוב'].map(normalize_name)).sum())
    settle24 = settle24.div(settle24.sum(axis=1), axis=0)

    # Sector of each K25 box (the repo's own taxonomy + K24 twin Haredi rule).
    def sector(bid):
        name = normalize_name(str(df25.at[bid, 'שם ישוב']))
        ent = sectors.get(name, {})
        if ent.get('population') in ('arab', 'bedouin', 'druze', 'circassian'):
            return 'arab'
        if ent.get('haredi'):
            return 'haredi'
        f = twin.get(bid)
        if f is not None:
            p = sh24.loc[f]
            if p.get('יהדות התורה', 0) + p.get('ש״ס', 0) >= 0.5:
                return 'haredi'
        return 'other'
    sec25 = pd.Series({b: sector(b) for b in df25.index})

    # Double envelopes
    d24 = raw24[raw24['סמל ישוב'] == 9999]
    d25 = raw25[raw25['סמל ישוב'] == 9999]
    de24 = np.array([d24[s].sum() for s in s24], float)
    de25_valid = float(d25['כשרים'].sum())

    others_share_true = 1 - Y25.values.sum() / df25['כשרים'].sum()
    print(f"truth (full K25 incl. double envelopes): {[truth[n] for n in n25]}  coalition {sum(truth[n] for n in COALITION)}")
    print(f"matched pairs {len(pairs)} of {len(df25)} K25 boxes; double envelopes K25 valid {de25_valid:,.0f} "
          f"({de25_valid/true_valid:.1%})")
    print("sector box counts:", sec25.value_counts().to_dict())

    masks = {
        'random 30%': lambda rng: {b: 0.30 for b in df25.index},
        'random 60%': lambda rng: {b: 0.60 for b in df25.index},
        'Haredi late (8% vs 58%)': lambda rng: {b: (0.08 if sec25[b] == 'haredi' else 0.58) for b in df25.index},
        'Arab late (10% vs 55%)': lambda rng: {b: (0.10 if sec25[b] == 'arab' else 0.55) for b in df25.index},
        'Arab early (75% vs 35%)': lambda rng: {b: (0.75 if sec25[b] == 'arab' else 0.35) for b in df25.index},
    }
    variants = ['V0 repo as-is', 'V1 full matrix', 'V2 +double env.', 'V3 +sector turnout', 'V4 +sector matrices',
                'V5 patched code']
    results = defaultdict(list)
    detail = {}

    for mname, mk in masks.items():
        for seed in range(6):
            rng = np.random.default_rng(seed)
            prob = mk(rng)
            counted = {b for b in df25.index if rng.random() < prob[b]}
            cnt_ids = [b for b in df25.index if b in counted]
            unc_ids = [b for b in df25.index if b not in counted]
            cnt_votes = Y25.loc[cnt_ids].values.sum(axis=0)
            cnt_valid = float(df25.loc[cnt_ids, 'כשרים'].sum())
            others_share = 1 - cnt_votes.sum() / cnt_valid
            mp = [(twin[t], t) for t in cnt_ids if t in twin]
            Xc = X24.loc[[f for f, _ in mp]].values
            Yc = Y25.loc[[t for _, t in mp]].values
            row_sum = Yc.sum() / Xc.sum()
            M = fit(Xc, Yc, row_sum)
            origin = (sh24.loc[[f for f, _ in mp]].values * Yc.sum(axis=1)[:, None]).sum(axis=0)

            # Sector matrices and sector turnout
            Ms, tadj_s = {}, {}
            for sname in ('arab', 'haredi', 'other'):
                sel = [i for i, (_, t) in enumerate(mp) if sec25[t] == sname]
                if len(sel) >= 40:
                    Xs, Ys = Xc[sel], Yc[sel]
                    Ms[sname] = normalise_and_pool(fit(Xs, Ys, Ys.sum() / Xs.sum()),
                                                   (sh24.loc[[mp[i][0] for i in sel]].values * Ys.sum(axis=1)[:, None]).sum(axis=0))
            def tadj(ids):
                num = den = 0.0
                for f, t in ids:
                    if df24.at[f, 'בזב'] > 0 and df25.at[t, 'בזב'] > 0:
                        den += df24.at[f, 'מצביעים'] / df24.at[f, 'בזב']
                        num += df25.at[t, 'מצביעים'] / df25.at[t, 'בזב']
                return min(1.15, max(0.7, num / den)) if den else 1.0
            g_adj = tadj(mp)
            for sname in ('arab', 'haredi', 'other'):
                ids = [p for p in mp if sec25[p[1]] == sname]
                tadj_s[sname] = tadj(ids) if len(ids) >= 40 else g_adj

            T_pub = normalise_and_pool(published_view(M, nat_from), origin)
            T_full = normalise_and_pool(M.copy(), origin)

            def project(T, sector_turnout=False, sector_T=False):
                tot = np.zeros(len(n25))
                for b in unc_ids:
                    f = twin.get(b)
                    if f is not None:
                        shares = sh24.loc[f].values
                        base = df24.at[f, 'מצביעים'] / df24.at[f, 'בזב'] if df24.at[f, 'בזב'] > 0 else None
                    else:
                        nm = normalize_name(str(df25.at[b, 'שם ישוב']))
                        shares = settle24.loc[nm].values if nm in settle24.index else nat24
                        base = None
                    if base is None:
                        base = cnt_valid / max(1.0, float(df25.loc[cnt_ids, 'בזב'].sum()))
                    adj = tadj_s[sec25[b]] if sector_turnout else g_adj
                    Tb = Ms.get(sec25[b], T) if sector_T else T
                    tot += shares @ Tb * float(df25.at[b, 'בזב']) * min(0.97, base * adj)
                return tot

            proj = {
                variants[0]: project(T_pub),
                variants[1]: project(T_full),
            }
            de_proj = (de24 / de24.sum()) @ T_full * de24.sum() * row_sum
            proj[variants[2]] = proj[variants[1]] + de_proj
            proj[variants[3]] = project(T_full, sector_turnout=True) + de_proj
            proj[variants[4]] = project(T_full, sector_turnout=True, sector_T=True) + de_proj
            # What the patched generate_command_center_data.py does: full
            # matrix, per-sector matrices and turnout, no double envelopes.
            proj[variants[5]] = project(T_full, sector_turnout=True, sector_T=True)
            for v, unc in proj.items():
                final = cnt_votes + unc
                valid = final.sum() / (1 - others_share)
                st = seats(final, n25, valid)
                err = sum(abs(st[n] - truth[n]) for n in n25)
                coal = sum(st[n] for n in COALITION) - sum(truth[n] for n in COALITION)
                arab = sum(st[n] for n in ARAB) - sum(truth[n] for n in ARAB)
                vote_err = np.abs(final / final.sum() - true_votes / true_votes.sum()).max() * 100
                results[(mname, v)].append((err, coal, arab, vote_err))
                if seed == 0:
                    detail[(mname, v)] = {n: st[n] - truth[n] for n in n25 if st[n] != truth[n]}

    print("\nmask | variant | mean total seat error | mean coalition error | mean Arab-lists error | mean max vote-share error (pts)")
    for (mname, v), rs in results.items():
        a = np.array(rs, float)
        print(f"{mname:26s} | {v:20s} | {a[:,0].mean():5.1f} | {a[:,1].mean():+5.1f} | {a[:,2].mean():+5.1f} | {a[:,3].mean():4.2f}")
    print("\nper-party seat errors, seed 0:")
    for k, d in detail.items():
        print(' ', k[0], '|', k[1], '|', d)


if __name__ == '__main__':
    main()
