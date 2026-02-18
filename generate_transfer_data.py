#!/usr/bin/env python3
"""
Generate vote transfer data for Israeli Knesset elections.
Computes transfer matrices using constrained convex optimization
and exports data as JSON for web visualization.

Written by Harel Cain, 2019-2024
"""

import json
import logging
import time
from pathlib import Path

import cvxpy as cvx
import numpy as np
import pandas as pd
from scipy.optimize import nnls

from party_config import ELECTIONS, get_party_info, get_party_color

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

pd.options.mode.chained_assignment = None


class VoteTransferAnalyzer:
    """Analyzes vote transfers between consecutive elections."""

    def __init__(self, method='convex', min_flow_threshold=5000, verbose=False, include_abstention=False):
        """
        Initialize the analyzer.

        Args:
            method: Optimization method ('convex', 'nnls', or 'closed_form')
            min_flow_threshold: Minimum vote flow to include in output
            verbose: Whether to print detailed output
            include_abstention: Whether to include "did not vote" pseudo-party
        """
        self.method = method
        self.min_flow_threshold = min_flow_threshold
        self.verbose = verbose
        self.include_abstention = include_abstention

    def load_election_data(self, election_id):
        """Load and prepare election data from CSV."""
        config = ELECTIONS[election_id]

        logger.info(f"Loading {config['name']} from {config['file']}")

        df = pd.read_csv(
            config['file'],
            encoding=config['encoding']
        )

        logger.info(f"Loaded {len(df)} precincts")

        # Create unique ballot ID
        ballot_field = config.get('ballot_field', 'קלפי')
        divisor = config.get('ballot_number_divisor', 1)
        def normalize_ballot(b):
            b = str(b)
            if b.endswith('.0'):
                b = b[:-2]
            if divisor > 1:
                try:
                    n = int(b)
                    if n % divisor == 0:
                        b = str(n // divisor)
                except ValueError:
                    pass
            return b
        df['ballot_id'] = df['סמל ישוב'].astype(str) + '__' + df[ballot_field].apply(normalize_ballot)

        # Filter out city 9999 (aggregated/invalid data)
        df = df[df['סמל ישוב'] != 9999]
        df = df.set_index('ballot_id')

        # Remove duplicate ballot IDs (can happen with historical data from CKAN API)
        dupes = df.index.duplicated(keep='first')
        if dupes.any():
            logger.warning(f"Removing {dupes.sum()} duplicate ballot IDs")
            df = df[~dupes]

        logger.info(f"{len(df)} precincts after filtering")

        return df, config

    def extract_party_votes(self, df, symbols, names):
        """Extract vote columns for specified parties."""
        # Filter to only existing columns
        existing_symbols = [s for s in symbols if s in df.columns]
        existing_names = [names[i] for i, s in enumerate(symbols) if s in df.columns]

        if len(existing_symbols) < len(symbols):
            missing = set(symbols) - set(existing_symbols)
            logger.warning(f"Missing party columns: {missing}")

        party_df = df[existing_symbols].copy()
        party_df.columns = existing_names

        return party_df, existing_symbols, existing_names

    def solve_transfer_matrix_convex(self, X, Y):
        """
        Solve for transfer matrix using convex optimization.

        Minimizes ||XM - Y||_F subject to:
        - 0 <= M <= 1 (probabilities)
        - sum(M, axis=1) == 1 (each row sums to 1)

        Args:
            X: Previous election votes (n_precincts, n_parties_prev)
            Y: Current election votes (n_precincts, n_parties_curr)

        Returns:
            Transfer matrix M (n_parties_prev, n_parties_curr)
        """
        M = cvx.Variable((X.shape[1], Y.shape[1]))
        constraints = [
            M >= 0,
            M <= 1,
            cvx.sum(M, axis=1) == 1
        ]
        objective = cvx.Minimize(cvx.norm(X @ M - Y, 'fro'))

        prob = cvx.Problem(objective, constraints)
        prob.solve(solver='SCS', verbose=self.verbose, max_iters=20000)

        if prob.status != 'optimal':
            logger.warning(f"Solver status: {prob.status}")

        return M.value

    def solve_transfer_matrix_nnls(self, X, Y):
        """Solve using non-negative least squares (per destination party)."""
        M = np.zeros((X.shape[1], Y.shape[1]))

        for i in range(Y.shape[1]):
            sol, _ = nnls(X, Y[:, i])
            M[:, i] = sol

        # Normalize rows to sum to 1
        row_sums = M.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        M = M / row_sums

        return M

    def solve_transfer_matrix_closed(self, X, Y):
        """Solve using closed-form least squares (may have negative values)."""
        return X.T @ Y @ np.linalg.pinv(Y.T @ Y)

    def _compute_dnv(self, df, config):
        """Compute 'did not vote' per ballot, handling missing בזב data."""
        bzv = df['בזב']
        voters = df['מצביעים']
        if bzv.sum() > 0:
            return (bzv - voters).clip(lower=0)
        # בזב column is empty (e.g. K17) — estimate from national eligible_voters
        national_eligible = config.get('eligible_voters', 0)
        if national_eligible > 0:
            total_voters = voters.sum()
            # Distribute eligible voters proportionally to voter count per ballot
            estimated_bzv = (voters / total_voters * national_eligible).round().astype(int)
            logger.warning(f"בזב column empty, estimating from national eligible={national_eligible:,}")
            return (estimated_bzv - voters).clip(lower=0)
        logger.warning("No eligible voter data available, abstention will be 0")
        return pd.Series(0, index=df.index)

    def compute_transfer(self, election_from, election_to):
        """
        Compute vote transfer between two elections.

        Returns:
            dict with transfer data suitable for JSON export
        """
        # Load data
        df_from, config_from = self.load_election_data(election_from)
        df_to, config_to = self.load_election_data(election_to)

        # Get party configurations
        parties_from = config_from['major_parties']
        parties_to = config_to['major_parties']

        # Extract party votes
        votes_from, symbols_from, names_from = self.extract_party_votes(
            df_from, parties_from['symbols'], parties_from['names']
        )
        votes_to, symbols_to, names_to = self.extract_party_votes(
            df_to, parties_to['symbols'], parties_to['names']
        )

        # Find common precincts with fallback matching
        # Matching logic:
        # - Exact match first (including .0 which normalizes to base)
        # - Only .1 can fall back to base, and only if no .0 sibling exists in "to" data

        def get_base_ballot_id(ballot_id):
            parts = ballot_id.split('__')
            if len(parts) == 2 and '.' in parts[1]:
                return parts[0] + '__' + parts[1].split('.')[0]
            return ballot_id

        def is_dot_one(ballot_id):
            parts = ballot_id.split('__')
            return len(parts) == 2 and parts[1].endswith('.1')

        # Track which base IDs have a .0 variant in "to" data
        to_bases_with_zero = set()
        for to_id in votes_to.index:
            parts = to_id.split('__')
            if len(parts) == 2 and parts[1].endswith('.0'):
                # This is a .0 ballot, record its base
                base = parts[0] + '__' + parts[1][:-2]
                to_bases_with_zero.add(base)

        # Build mapping: for each "to" ballot, find matching "from" ballot
        from_ids = set(votes_from.index)
        matched_pairs = []  # (from_id, to_id)

        for to_id in votes_to.index:
            if to_id in from_ids:
                # Exact match
                matched_pairs.append((to_id, to_id))
            elif is_dot_one(to_id):
                # Only .1 can fall back (not .2, .3, etc.)
                base_id = get_base_ballot_id(to_id)
                if base_id not in to_bases_with_zero and base_id in from_ids:
                    matched_pairs.append((base_id, to_id))

        logger.info(f"Found {len(matched_pairs)} matched precincts (with fallback)")

        if not matched_pairs:
            raise ValueError("No matching precincts found")

        from_matched_ids = [p[0] for p in matched_pairs]
        to_matched_ids = [p[1] for p in matched_pairs]
        common_idx = None  # Not used anymore

        X = votes_from.loc[from_matched_ids].values.astype(float)
        Y = votes_to.loc[to_matched_ids].values.astype(float)

        # Optionally add "did not vote" pseudo-party column
        if self.include_abstention:
            dnv_from = self._compute_dnv(df_from, config_from)
            dnv_to = self._compute_dnv(df_to, config_to)

            dnv_from_matched = dnv_from.loc[from_matched_ids].values.astype(float).reshape(-1, 1)
            dnv_to_matched = dnv_to.loc[to_matched_ids].values.astype(float).reshape(-1, 1)

            X = np.hstack([X, dnv_from_matched])
            Y = np.hstack([Y, dnv_to_matched])

            abstention_name = 'לא הצביעו'
            names_from = list(names_from) + [abstention_name]
            names_to = list(names_to) + [abstention_name]
            symbols_from = list(symbols_from) + ['abstain']
            symbols_to = list(symbols_to) + ['abstain']

        # Compute transfer matrix
        logger.info(f"Computing transfer matrix using {self.method} method...")

        if self.method == 'convex':
            M = self.solve_transfer_matrix_convex(X, Y)
        elif self.method == 'nnls':
            M = self.solve_transfer_matrix_nnls(X, Y)
        else:
            M = self.solve_transfer_matrix_closed(X, Y)

        # Compute R² score
        Y_pred = X @ M
        ss_res = ((Y - Y_pred) ** 2).sum()
        ss_tot = ((Y - Y.mean(axis=0)) ** 2).sum()
        r_squared = 1 - ss_res / ss_tot
        logger.info(f"R² = {r_squared:.4f}")

        # Compute vote movements
        # Use national totals (all precincts, not just matched)
        total_votes_from = votes_from.sum().values
        if self.include_abstention:
            national_dnv_from = self._compute_dnv(df_from, config_from).sum()
            total_votes_from = np.append(total_votes_from, national_dnv_from)
        vote_movements = M * total_votes_from[:, np.newaxis]

        # Build transfer data for JSON
        transfers = []
        for i, source_name in enumerate(names_from):
            source_symbol = symbols_from[i]
            for j, target_name in enumerate(names_to):
                target_symbol = symbols_to[j]
                votes = float(vote_movements[i, j])
                percentage = float(M[i, j] * 100)

                if votes >= self.min_flow_threshold:
                    transfers.append({
                        'source': source_name,
                        'source_symbol': source_symbol,
                        'target': target_name,
                        'target_symbol': target_symbol,
                        'votes': int(votes),
                        'percentage': round(percentage, 1)
                    })

        # Build node data
        seats_from = parties_from.get('seats', [None] * len(names_from))
        abstention_info = {
            'name': 'לא הצביעו',
            'name_en': 'Did not vote',
            'color': '#9ca3af'
        }
        nodes_from = []
        for i, name in enumerate(names_from):
            symbol = symbols_from[i]
            if symbol == 'abstain':
                nodes_from.append({
                    'name': name,
                    'symbol': symbol,
                    'votes': int(total_votes_from[i]),
                    'seats': None,
                    'color': '#9ca3af',
                    'info': abstention_info
                })
            else:
                info = get_party_info(symbol, election_from)
                nodes_from.append({
                    'name': name,
                    'symbol': symbol,
                    'votes': int(total_votes_from[i]),
                    'seats': seats_from[i] if i < len(seats_from) else None,
                    'color': info['color'],
                    'info': info
                })

        total_votes_to = votes_to.sum().values
        if self.include_abstention:
            national_dnv_to = self._compute_dnv(df_to, config_to).sum()
            total_votes_to = np.append(total_votes_to, national_dnv_to)
        seats_to = parties_to.get('seats', [None] * len(names_to))
        nodes_to = []
        for i, name in enumerate(names_to):
            symbol = symbols_to[i]
            if symbol == 'abstain':
                nodes_to.append({
                    'name': name,
                    'symbol': symbol,
                    'votes': int(total_votes_to[i]),
                    'seats': None,
                    'color': '#9ca3af',
                    'info': abstention_info
                })
            else:
                info = get_party_info(symbol, election_to)
                nodes_to.append({
                    'name': name,
                    'symbol': symbol,
                    'votes': int(total_votes_to[i]),
                    'seats': seats_to[i] if i < len(seats_to) else None,
                    'color': info['color'],
                    'info': info
                })

        return {
            'from_election': {
                'id': election_from,
                'name': config_from['name'],
                'name_en': config_from['name_en'],
                'date': config_from['date'],
                'eligible_voters': config_from.get('eligible_voters'),
                'votes_cast': config_from.get('votes_cast'),
                'valid_votes': config_from.get('valid_votes'),
                'turnout_percent': config_from.get('turnout_percent')
            },
            'to_election': {
                'id': election_to,
                'name': config_to['name'],
                'name_en': config_to['name_en'],
                'date': config_to['date'],
                'eligible_voters': config_to.get('eligible_voters'),
                'votes_cast': config_to.get('votes_cast'),
                'valid_votes': config_to.get('valid_votes'),
                'turnout_percent': config_to.get('turnout_percent')
            },
            'nodes_from': nodes_from,
            'nodes_to': nodes_to,
            'transfers': transfers,
            'stats': {
                'common_precincts': len(matched_pairs),
                'r_squared': round(r_squared, 4),
                'total_votes_from': int(total_votes_from.sum()),
                'total_votes_to': int(total_votes_to.sum()),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }


def run_analysis(include_abstention=False, only_transitions=None):
    """Run transfer analysis for all election pairs.

    Args:
        include_abstention: Whether to include "did not vote" pseudo-party
        only_transitions: Optional list of "X_to_Y" strings to filter pairs
    """
    suffix = '_abstention' if include_abstention else ''
    label = ' (with abstention)' if include_abstention else ''

    analyzer = VoteTransferAnalyzer(
        method='convex',
        min_flow_threshold=5000,
        verbose=False,
        include_abstention=include_abstention
    )

    # Election pairs to analyze
    pairs = [
        ('16', '17'),
        ('17', '18'),
        ('18', '19'),
        ('19', '20'),
        ('20', '21'),
        ('21', '22'),
        ('22', '23'),
        ('23', '24'),
        ('24', '25'),
        ('25', '26'),
    ]

    if only_transitions:
        requested = set(only_transitions)
        pairs = [(f, t) for f, t in pairs if f"{f}_to_{t}" in requested]
        if not pairs:
            logger.warning(f"No matching transitions found for: {only_transitions}")
            return

    all_data = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'transitions': {}
    }

    for from_id, to_id in pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing {from_id} → {to_id}{label}")
        logger.info('='*60)

        try:
            data = analyzer.compute_transfer(from_id, to_id)
            key = f"{from_id}_to_{to_id}"
            all_data['transitions'][key] = data

            # Save individual file
            output_file = f"data/transfer_{from_id}_to_{to_id}{suffix}.json"
            Path('data').mkdir(exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {output_file}")

        except Exception as e:
            logger.error(f"Failed to analyze {from_id} → {to_id}{label}: {e}")
            raise

    # Save combined file — merge into existing if running subset
    combined_file = f'data/all_transfers{suffix}.json'
    if only_transitions and Path(combined_file).exists():
        with open(combined_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        existing['transitions'].update(all_data['transitions'])
        existing['generated_at'] = all_data['generated_at']
        all_data = existing
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved {combined_file}")


def main():
    """Generate transfer data for all consecutive election pairs."""
    import argparse
    parser = argparse.ArgumentParser(description='Generate vote transfer matrices')
    parser.add_argument('--transitions', nargs='+',
                        help='Only compute specific transitions, e.g. --transitions 25_to_26 24_to_25')
    args = parser.parse_args()

    only = args.transitions

    # Regular analysis
    logger.info("=== Regular transfer analysis ===")
    run_analysis(include_abstention=False, only_transitions=only)

    # Abstention analysis
    logger.info("\n=== Abstention transfer analysis ===")
    run_analysis(include_abstention=True, only_transitions=only)

    logger.info("\nDone!")


if __name__ == '__main__':
    main()
