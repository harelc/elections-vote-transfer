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
E26_PARTIES = {
    'מחל': ('הליכוד', '#2563eb'),
    'נב':  ('בנט 26', '#f97316'),
    'פה':  ('יש עתיד', '#06b6d4'),
    'ל':   ('ישראל ביתנו', '#db2777'),
    'דמ':  ('הדמוקרטים', '#16a34a'),
    'שס':  ('ש״ס', '#1e3a8a'),
    'ג':   ('יהדות התורה', '#4b5563'),
    'עם':  ('הרשימה המשותפת', '#84cc16'),
    'ט':   ('הציונות הדתית', '#92400e'),
    'עי':  ('עוצמה יהודית', '#7f1d1d'),
    'יר':  ('ישר', '#7c3aed'),
}

# Transfer matrix: E25 party name → dict of E26 party name → fraction
# Each row must sum to 1.0
TRANSFER_MATRIX = {
    'הליכוד':        {'הליכוד': 0.53, 'בנט 26': 0.22, 'הציונות הדתית': 0.02, 'עוצמה יהודית': 0.09, 'ישר': 0.05, 'יש עתיד': 0.04, 'ש״ס': 0.03, 'יהדות התורה': 0.02},
    'יש עתיד':      {'יש עתיד': 0.28, 'בנט 26': 0.22, 'ישר': 0.18, 'הדמוקרטים': 0.12, 'ישראל ביתנו': 0.15, 'הליכוד': 0.05},
    'הציונות הדתית': {'הציונות הדתית': 0.26, 'עוצמה יהודית': 0.40, 'בנט 26': 0.15, 'הליכוד': 0.10, 'ש״ס': 0.05, 'ישר': 0.04},
    'המחנה הממלכתי': {'בנט 26': 0.50, 'ישר': 0.15, 'יש עתיד': 0.10, 'הדמוקרטים': 0.05, 'ישראל ביתנו': 0.15, 'הליכוד': 0.05},
    'ש״ס':          {'ש״ס': 0.87, 'הליכוד': 0.03, 'עוצמה יהודית': 0.10},
    'יהדות התורה':  {'יהדות התורה': 0.87, 'ש״ס': 0.05, 'הליכוד': 0.02, 'עוצמה יהודית': 0.06},
    'ישראל ביתנו':  {'ישראל ביתנו': 0.50, 'בנט 26': 0.20, 'ישר': 0.15, 'הליכוד': 0.10, 'יש עתיד': 0.05},
    'רע״ם':         {'הרשימה המשותפת': 0.97, 'הדמוקרטים': 0.03},
    'חד״ש-תע״ל':   {'הרשימה המשותפת': 0.85, 'הדמוקרטים': 0.15},
    'העבודה':       {'הדמוקרטים': 0.60, 'בנט 26': 0.10, 'ישר': 0.15, 'יש עתיד': 0.10, 'ישראל ביתנו': 0.05},
    'מרצ':          {'הדמוקרטים': 0.70, 'בנט 26': 0.05, 'יש עתיד': 0.10, 'ישר': 0.12, 'הרשימה המשותפת': 0.03},
    'בל״ד':         {'הרשימה המשותפת': 0.95, 'הדמוקרטים': 0.05},
}

# Per-source-party turnout factor: what fraction of E25 voters show up in E26.
# <1.0 = demobilized (stay home), >1.0 = mobilized (new/returning voters join).
# The transfer matrix rows still sum to 1.0 (distribution among E26 parties),
# but the effective contribution is scaled by this factor.
ROW_TURNOUT = {
    'הליכוד':        0.85,   # Likud base demobilized
    'יש עתיד':      1.05,   # Centrist voters energized
    'הציונות הדתית': 0.97,   # Some stay home after split
    'המחנה הממלכתי': 1.05,   # National Unity base mobilized
    'ש״ס':          1.00,   # Shas machine keeps turnout high
    'יהדות התורה':  1.00,   # UTJ same
    'ישראל ביתנו':  1.00,   # Stable
    'רע״ם':         0.90,   # Arab turnout lower
    'חד״ש-תע״ל':   0.90,   # Arab turnout lower
    'העבודה':       1.10,   # Mobilized for Democrats
    'מרצ':          1.15,   # Highly mobilized for Democrats
    'בל״ד':         0.90,   # Arab turnout lower
}
DEFAULT_ROW_TURNOUT = 1.00

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

        # Scale by per-source turnout factor
        turnout = ROW_TURNOUT.get(e25_name, DEFAULT_ROW_TURNOUT)
        effective_votes = votes * turnout
        effective_total += effective_votes

        # Get transfer row; if no row, distribute proportionally to all parties
        row = TRANSFER_MATRIX.get(e25_name)
        if row is None:
            row = {'הליכוד': 0.3, 'יש עתיד': 0.2, 'ישר': 0.15, 'הדמוקרטים': 0.15,
                   'בנט 26': 0.1, 'ישראל ביתנו': 0.05, 'הרשימה המשותפת': 0.05}

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
        out_df.at[idx, 'מצביעים'] = e26_total + int(row.get('פסולים', 0) or 0)

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


def main():
    parser = argparse.ArgumentParser(description='Simulate election 26 from election 25 data')
    parser.add_argument('--alpha', type=float, default=55,
                        help='Dirichlet concentration (higher = less noise, default: 55)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')
    args = parser.parse_args()

    simulate(alpha=args.alpha, seed=args.seed)


if __name__ == '__main__':
    main()
