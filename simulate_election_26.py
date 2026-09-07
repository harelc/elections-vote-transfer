#!/usr/bin/env python3
"""
Simulate election 26 ballot data from election 25 results + a configurable transfer matrix.

Generates synthetic ballot26.csv in CEC format. Each E25 ballot's votes are redistributed
to E26 parties using the transfer matrix, with Dirichlet noise for realism.

Usage:
    python simulate_election_26.py [--alpha 80] [--seed 42]

Then run:
    python prepare_election_26.py --real-csv ballot26.csv
"""

import argparse
import numpy as np
import pandas as pd
from party_config import ELECTIONS

# ============================================================================
# CONFIGURATION — Edit these to model different scenarios
# ============================================================================

# E26 party definitions: symbol → (hebrew_name, color)
# List map follows Madad 120 (7 Sep 2026): Yashar, Likud, Beyachad, Democrats,
# YB, Joint List (Hadash–Ta'al–Balad), UTJ, Shas, Otzma, RZ+Zehut, Ra'am,
# Amcha Yisrael (Winter), Hendel–Zelicha, Gantz below threshold.
E26_PARTIES = {
    'יר':  ('ישר', '#14b8a6'),
    'מחל': ('הליכוד', '#2563eb'),
    'נב':  ('ביחד', '#f97316'),
    'דמ':  ('הדמוקרטים', '#16a34a'),
    'ל':   ('ישראל ביתנו', '#db2777'),
    'ום':  ('הרשימה המשותפת', '#0d9488'),
    'ג':   ('יהדות התורה', '#4b5563'),
    'שס':  ('ש״ס', '#1e3a8a'),
    'עי':  ('עוצמה יהודית', '#7f1d1d'),
    'ט':   ('הציונות הדתית', '#92400e'),
    'עם':  ('רע״ם', '#84cc16'),
    'וי':  ('עמך ישראל', '#4d7c0f'),
    'מי':  ('הנדל–זליכה', '#d97706'),
    'כל':  ('כחול לבן', '#8b5cf6'),
}

# Madad 120 center, 7 Sep 2026. Both threshold lists included as passing (4 each);
# 1 seat shaved from Yashar / Likud / Beyachad so the 120 still add up.
TARGET_SEATS = {
    'ישר': 22, 'הליכוד': 20, 'ביחד': 13, 'הדמוקרטים': 9,
    'ישראל ביתנו': 8, 'הרשימה המשותפת': 8, 'יהדות התורה': 8,
    'ש״ס': 7, 'עוצמה יהודית': 7, 'הציונות הדתית': 5, 'רע״ם': 5,
    'עמך ישראל': 4, 'הנדל–זליכה': 4, 'כחול לבן': 0,
}

# K25 official valid votes (wiki_official_results.json) — used by --preview
K25_NATIONAL_VOTES = {
    'הליכוד': 1115336, 'יש עתיד': 847435, 'הציונות הדתית': 516470,
    'המחנה הממלכתי': 432482, 'ש״ס': 392964, 'יהדות התורה': 280194,
    'ישראל ביתנו': 213687, 'רע״ם': 194047, 'חד״ש-תע״ל': 178735,
    'העבודה': 175992, 'מרצ': 150793, 'בל״ד': 138617,
}

# Transfer matrix: E25 party name → dict of E26 party name → fraction
# Each row must sum to 1.0. Cross-bloc cells kept tiny (Madad: <1% undecided
# between camps). K25 RZ list was Otzma+RZ+Noam together.
TRANSFER_MATRIX = {
    'הליכוד': {
        'הליכוד': 0.73, 'עוצמה יהודית': 0.08, 'עמך ישראל': 0.09,
        'הציונות הדתית': 0.05, 'ש״ס': 0.03, 'יהדות התורה': 0.02,
    },
    'יש עתיד': {
        'ביחד': 0.39, 'ישר': 0.42, 'הדמוקרטים': 0.07, 'ישראל ביתנו': 0.03,
        'הנדל–זליכה': 0.06, 'כחול לבן': 0.03,
    },
    'הציונות הדתית': {
        'עוצמה יהודית': 0.38, 'הציונות הדתית': 0.34, 'עמך ישראל': 0.18,
        'הליכוד': 0.10,
    },
    'המחנה הממלכתי': {
        'ישר': 0.62, 'ביחד': 0.12, 'הנדל–זליכה': 0.16, 'הדמוקרטים': 0.03,
        'ישראל ביתנו': 0.02, 'כחול לבן': 0.05,
    },
    'ש״ס': {
        'ש״ס': 0.88, 'הליכוד': 0.05, 'יהדות התורה': 0.05, 'עוצמה יהודית': 0.02,
    },
    'יהדות התורה': {
        'יהדות התורה': 0.94, 'ש״ס': 0.04, 'הליכוד': 0.02,
    },
    'ישראל ביתנו': {
        'ישראל ביתנו': 0.85, 'ישר': 0.06, 'ביחד': 0.03, 'הנדל–זליכה': 0.03, 'כחול לבן': 0.03,
    },
    'רע״ם': {
        'רע״ם': 0.92, 'הרשימה המשותפת': 0.08,
    },
    'חד״ש-תע״ל': {
        'הרשימה המשותפת': 0.82, 'רע״ם': 0.08, 'הדמוקרטים': 0.10,
    },
    'העבודה': {
        'הדמוקרטים': 0.68, 'ישר': 0.15, 'ביחד': 0.10, 'הנדל–זליכה': 0.04, 'כחול לבן': 0.03,
    },
    'מרצ': {
        'הדמוקרטים': 0.70, 'ישר': 0.12, 'הרשימה המשותפת': 0.04, 'ביחד': 0.12, 'כחול לבן': 0.02,
    },
    'בל״ד': {
        'הרשימה המשותפת': 0.88, 'רע״ם': 0.12,
    },
}

ROW_TURNOUT = {
    'הליכוד':        0.80,
    'יש עתיד':      1.08,
    'הציונות הדתית': 0.84,
    'המחנה הממלכתי': 1.18,
    'ש״ס':          0.62,
    'יהדות התורה':  1.02,
    'ישראל ביתנו':  1.40,
    'רע״ם':         0.90,
    'חד״ש-תע״ל':   1.00,
    'העבודה':       1.08,
    'מרצ':          1.08,
    'בל״ד':         0.98,
}
DEFAULT_ROW_TURNOUT = 1.00

# Surplus agreements used by --preview Bader-Ofer (and later dhondt.html)
SURPLUS_AGREEMENTS = [
    ('ש״ס', 'יהדות התורה'),
    ('עוצמה יהודית', 'הציונות הדתית'),
    ('ישר', 'ישראל ביתנו'),
    ('הרשימה המשותפת', 'רע״ם'),
]

# Global population growth between K25 (Nov 2022) and K26 (~Oct 2026).
# Israeli registered-voter rolls grew ~1.93%/year (2021→2022 CEC figures);
# extrapolated over ~3.9 years → ~7.5% growth in eligible voters.
POP_GROWTH = 1.075

# E25 symbol → party name mapping (major parties only)
E25_SYMBOL_TO_NAME = {
    'מחל': 'הליכוד',
    'פה':  'יש עתיד',
    'ט':   'הציונות הדתית',
    'כן':  'המחנה הממלכתי',
    'שס':  'ש״ס',
    'ג':   'יהדות התורה',
    'ל':   'ישראל ביתנו',
    'עם':  'רע״ם',
    'ום':  'חד״ש-תע״ל',
    'אמת': 'העבודה',
    'מרצ': 'מרצ',
    'ד':   'בל״ד',
}

# E26 party name → symbol (reverse of E26_PARTIES)
E26_NAME_TO_SYMBOL = {name: sym for sym, (name, _) in E26_PARTIES.items()}

# ============================================================================
# SIMULATION LOGIC
# ============================================================================

def validate_config():
    """Validate that transfer matrix rows sum to ~1.0 and all target parties exist."""
    e26_names = {name for _, (name, _) in E26_PARTIES.items()}
    for src, row in TRANSFER_MATRIX.items():
        total = sum(row.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Transfer row '{src}' sums to {total:.4f}, expected 1.0")
        for dst in row:
            if dst not in e26_names:
                raise ValueError(f"Transfer target '{dst}' not in E26_PARTIES")


def largest_remainder_round(values, total):
    """Round floats to integers preserving their sum using largest-remainder method."""
    floors = np.floor(values).astype(int)
    remainders = values - floors
    deficit = total - floors.sum()
    if deficit > 0:
        indices = np.argsort(-remainders)
        for i in range(int(deficit)):
            floors[indices[i]] += 1
    return floors


def get_dominant_party(votes_by_e25_name):
    """Return the E25 party name with the most votes in a ballot."""
    if not votes_by_e25_name:
        return None
    return max(votes_by_e25_name, key=votes_by_e25_name.get)


def simulate_ballot(votes_by_e25_name, e26_party_list, rng, alpha):
    """
    Simulate E26 votes for a single ballot from E25 votes.

    Args:
        votes_by_e25_name: dict of E25 party name → vote count
        e26_party_list: ordered list of E26 party names
        rng: numpy random generator
        alpha: Dirichlet concentration parameter (higher = less noise)

    Returns:
        dict of E26 party name → simulated vote count
    """
    n_parties = len(e26_party_list)
    party_idx = {name: i for i, name in enumerate(e26_party_list)}

    # Accumulate expected E26 votes from each E25 party, scaled by turnout
    expected = np.zeros(n_parties)
    effective_total = 0

    for e25_name, votes in votes_by_e25_name.items():
        if votes <= 0:
            continue

        # Scale by per-source turnout factor and global population growth
        turnout = ROW_TURNOUT.get(e25_name, DEFAULT_ROW_TURNOUT)
        effective_votes = votes * turnout * POP_GROWTH
        effective_total += effective_votes

        # Get transfer row; if no row, distribute proportionally to all parties
        row = TRANSFER_MATRIX.get(e25_name)
        if row is None:
            row = {'הליכוד': 0.25, 'ביחד': 0.20, 'ישר': 0.22, 'הדמוקרטים': 0.10,
                   'ישראל ביתנו': 0.05, 'הרשימה המשותפת': 0.05,
                   'הנדל–זליכה': 0.08, 'עמך ישראל': 0.05}

        for dst_name, fraction in row.items():
            if dst_name in party_idx:
                expected[party_idx[dst_name]] += effective_votes * fraction

    if effective_total <= 0:
        return {name: 0 for name in e26_party_list}

    # Round effective total to integer (this ballot's new valid vote count)
    total_votes = max(1, round(effective_total))

    # Normalize to proportions
    proportions = expected / expected.sum() if expected.sum() > 0 else np.ones(n_parties) / n_parties

    # Add Dirichlet noise
    # Clamp minimum to small positive to avoid zeros in Dirichlet
    dir_alpha = np.maximum(alpha * proportions, 0.01)
    noisy_proportions = rng.dirichlet(dir_alpha)

    # Scale to total votes and round
    raw_votes = noisy_proportions * total_votes
    int_votes = largest_remainder_round(raw_votes, int(total_votes))

    return {name: int(int_votes[i]) for i, name in enumerate(e26_party_list)}


def bader_ofer(votes, threshold_pct=3.25, total_seats=120, agreements=None):
    """Israeli Bader-Ofer (D'Hondt) with optional surplus-vote pairs."""
    total = sum(votes.values())
    thresh = total * threshold_pct / 100.0
    passed = {k: v for k, v in votes.items() if v >= thresh}

    partner = {}
    for a, b in (agreements or []):
        if a in passed and b in passed:
            partner[a] = b
            partner[b] = a

    groups = []
    seen = set()
    for name in passed:
        if name in seen:
            continue
        if name in partner:
            other = partner[name]
            groups.append(([name, other], passed[name] + passed[other]))
            seen.update((name, other))
        else:
            groups.append(([name], passed[name]))
            seen.add(name)

    seats_g = [0] * len(groups)
    for _ in range(total_seats):
        i = max(range(len(groups)), key=lambda j: groups[j][1] / (seats_g[j] + 1))
        seats_g[i] += 1

    result = {k: 0 for k in votes}
    for (members, _), n in zip(groups, seats_g):
        if len(members) == 1:
            result[members[0]] = n
            continue
        inner = [0] * len(members)
        for _ in range(n):
            i = max(range(len(members)), key=lambda j: passed[members[j]] / (inner[j] + 1))
            inner[i] += 1
        for m, s in zip(members, inner):
            result[m] = s
    return result, passed, thresh


def expected_national_votes():
    """Noise-free national E26 totals from K25 official votes × matrix."""
    totals = {name: 0.0 for _, (name, _) in E26_PARTIES.items()}
    for src, v in K25_NATIONAL_VOTES.items():
        ev = v * ROW_TURNOUT.get(src, DEFAULT_ROW_TURNOUT) * POP_GROWTH
        for dst, frac in TRANSFER_MATRIX[src].items():
            totals[dst] += ev * frac
    return {k: int(round(x)) for k, x in totals.items()}


def preview_national():
    """Print expected votes / Bader-Ofer seats vs Madad 120 targets."""
    validate_config()
    votes = expected_national_votes()
    total = sum(votes.values())
    seats, passed, thresh = bader_ofer(votes, agreements=SURPLUS_AGREEMENTS)
    print(f"National preview (no Dirichlet noise), valid={total:,}  threshold={thresh:,.0f}")
    print(f"{'Party':<22} {'Votes':>10} {'%':>6} {'Seats':>5} {'Target':>6} {'Δ':>4}")
    print("-" * 58)
    for name in TARGET_SEATS:
        v = votes.get(name, 0)
        s = seats.get(name, 0)
        t = TARGET_SEATS[name]
        print(f"{name:<22} {v:>10,} {100*v/total:5.1f}% {s:>5} {t:>6} {s-t:>+4}")
    print("-" * 58)
    print(f"{'TOTAL':<22} {total:>10,} {'':>6} {sum(seats.values()):>5} {sum(TARGET_SEATS.values()):>6}")
    missed = [n for n, t in TARGET_SEATS.items() if t > 0 and n not in passed]
    extra = [n for n in passed if TARGET_SEATS.get(n, 0) == 0]
    if missed:
        print("Below threshold (wanted seats):", ", ".join(missed))
    if extra:
        print("Passed but target 0:", ", ".join(extra))


def simulate(alpha=55, seed=42):
    """Generate simulated ballot26.csv from ballot25.csv."""
    validate_config()

    rng = np.random.default_rng(seed)

    # Read E25 data
    e25_config = ELECTIONS['25']
    df = pd.read_csv(e25_config['file'], encoding=e25_config['encoding'])

    # Identify metadata columns (up to and including כשרים)
    cols = list(df.columns)
    try:
        kosher_idx = cols.index('כשרים')
    except ValueError:
        raise ValueError("Cannot find 'כשרים' column in ballot25.csv")

    meta_cols = cols[:kosher_idx + 1]
    e25_party_cols = cols[kosher_idx + 1:]

    # E26 party list (ordered)
    e26_party_list = [name for _, (name, _) in E26_PARTIES.items()]
    e26_symbol_list = list(E26_PARTIES.keys())

    print(f"E25 parties: {len(e25_party_cols)} columns")
    print(f"E26 parties: {len(e26_party_list)} parties")
    print(f"Ballots: {len(df)}")
    print(f"Alpha (noise): {alpha}, Seed: {seed}")

    # Build output dataframe with same metadata columns
    out_df = df[meta_cols].copy()

    # Initialize E26 party columns
    for sym in e26_symbol_list:
        out_df[sym] = 0

    total_e25_votes = 0
    total_e26_votes = 0

    for idx, row in df.iterrows():
        # Gather E25 votes by party name
        votes_by_name = {}
        for sym in e25_party_cols:
            name = E25_SYMBOL_TO_NAME.get(sym)
            v = int(row.get(sym, 0) or 0)
            if name:
                votes_by_name[name] = votes_by_name.get(name, 0) + v
            else:
                # Small party: add to a generic bucket
                votes_by_name.setdefault('_small', 0)
                votes_by_name['_small'] = votes_by_name.get('_small', 0) + v

        # Handle small party votes: distribute through default transfer
        small_votes = votes_by_name.pop('_small', 0)
        if small_votes > 0:
            # Find the dominant party and add small votes to it
            dominant = get_dominant_party(votes_by_name)
            if dominant:
                votes_by_name[dominant] = votes_by_name.get(dominant, 0) + small_votes
            else:
                votes_by_name['הליכוד'] = small_votes

        # Simulate E26 votes (turnout adjustment is built into simulate_ballot
        # via ROW_TURNOUT per source party)
        total_e25 = sum(votes_by_name.values())
        e26_votes = simulate_ballot(votes_by_name, e26_party_list, rng, alpha)

        # Update metadata to reflect adjusted totals
        e26_total = sum(e26_votes.values())
        out_df.at[idx, 'כשרים'] = e26_total
        # Scale invalid ballots by population growth too, then recompute voters
        invalid_e26 = int(round(int(row.get('פסולים', 0) or 0) * POP_GROWTH))
        out_df.at[idx, 'פסולים'] = invalid_e26
        out_df.at[idx, 'מצביעים'] = e26_total + invalid_e26
        # Scale eligible voters by population growth so turnout ratio stays consistent
        if 'בזב' in out_df.columns:
            out_df.at[idx, 'בזב'] = int(round(int(row.get('בזב', 0) or 0) * POP_GROWTH))

        # Write E26 votes by symbol
        for sym, (name, _) in E26_PARTIES.items():
            out_df.at[idx, sym] = e26_votes[name]

        total_e25_votes += total_e25
        total_e26_votes += e26_total

    # Save
    output_path = 'ballot26.csv'
    out_df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"\nOutput: {output_path}")
    print(f"Total E25 valid votes: {total_e25_votes:,.0f}")
    print(f"Total E26 valid votes: {total_e26_votes:,}")
    print(f"Rows: {len(out_df)}")

    # Print per-party totals
    print(f"\nE26 Party Totals:")
    print(f"{'Symbol':<6} {'Party':<20} {'Votes':>12} {'%':>7}")
    print("-" * 48)
    for sym, (name, _) in E26_PARTIES.items():
        votes = out_df[sym].sum()
        pct = votes / total_e26_votes * 100 if total_e26_votes > 0 else 0
        print(f"{sym:<6} {name:<20} {votes:>12,} {pct:>6.1f}%")

    # Bader-Ofer on noisy national totals
    vote_map = {name: int(out_df[sym].sum()) for sym, (name, _) in E26_PARTIES.items()}
    seats, passed, thresh = bader_ofer(vote_map, agreements=SURPLUS_AGREEMENTS)
    print(f"\nBader-Ofer (threshold {thresh:,.0f}):")
    for name, t in TARGET_SEATS.items():
        s = seats.get(name, 0)
        print(f"  {name:<22} {s:>3} seats  (target {t}{'' if s == t else f', Δ{s-t:+d}'})")


def main():
    parser = argparse.ArgumentParser(description='Simulate election 26 from election 25 data')
    parser.add_argument('--alpha', type=float, default=55,
                        help='Dirichlet concentration (higher = less noise, default: 55, '
                             'roughly matches the empirically-estimated K24→K25 pooled α=51.2 '
                             'from estimate_alpha.py; see site/data/alpha_estimates.json)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--preview', action='store_true',
                        help='Print national Bader-Ofer seats from the matrix (no ballot CSV)')
    args = parser.parse_args()

    if args.preview:
        preview_national()
        return

    simulate(alpha=args.alpha, seed=args.seed)


if __name__ == '__main__':
    main()
