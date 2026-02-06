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

    def __init__(self, method='convex', min_flow_threshold=5000, verbose=False):
        """
        Initialize the analyzer.

        Args:
            method: Optimization method ('convex', 'nnls', or 'closed_form')
            min_flow_threshold: Minimum vote flow to include in output
            verbose: Whether to print detailed output
        """
        self.method = method
        self.min_flow_threshold = min_flow_threshold
        self.verbose = verbose

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
        def normalize_ballot(b):
            b = str(b)
            if b.endswith('.0'):
                b = b[:-2]
            return b
        df['ballot_id'] = df['סמל ישוב'].astype(str) + '__' + df[ballot_field].apply(normalize_ballot)

        # Filter out city 9999 (aggregated/invalid data)
        df = df[df['סמל ישוב'] != 9999]
        df = df.set_index('ballot_id')
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
        # Try exact match first, then fall back to base ballot (14.1 -> 14)
        def get_base_ballot_id(ballot_id):
            # Only .1 subdivisions fall back to base, not .2, .3, etc.
            parts = ballot_id.split('__')
            if len(parts) == 2 and parts[1].endswith('.1'):
                return parts[0] + '__' + parts[1][:-2]
            return ballot_id

        # Build mapping: for each "to" ballot, find matching "from" ballot
        from_ids = set(votes_from.index)
        matched_pairs = []  # (from_id, to_id)

        for to_id in votes_to.index:
            if to_id in from_ids:
                # Exact match
                matched_pairs.append((to_id, to_id))
            else:
                # Try base ballot fallback
                base_id = get_base_ballot_id(to_id)
                if base_id != to_id and base_id in from_ids:
                    matched_pairs.append((base_id, to_id))

        logger.info(f"Found {len(matched_pairs)} matched precincts (with fallback)")

        if not matched_pairs:
            raise ValueError("No matching precincts found")

        from_matched_ids = [p[0] for p in matched_pairs]
        to_matched_ids = [p[1] for p in matched_pairs]
        common_idx = None  # Not used anymore

        X = votes_from.loc[from_matched_ids].values.astype(float)
        Y = votes_to.loc[to_matched_ids].values.astype(float)

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
        total_votes_from = votes_from.sum().values
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
        nodes_from = []
        for i, name in enumerate(names_from):
            symbol = symbols_from[i]
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
        seats_to = parties_to.get('seats', [None] * len(names_to))
        nodes_to = []
        for i, name in enumerate(names_to):
            symbol = symbols_to[i]
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


def main():
    """Generate transfer data for all consecutive election pairs."""
    analyzer = VoteTransferAnalyzer(
        method='convex',
        min_flow_threshold=5000,
        verbose=False
    )

    # Election pairs to analyze
    pairs = [
        ('21', '22'),
        ('22', '23'),
        ('23', '24'),
        ('24', '25'),
    ]

    all_data = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'transitions': {}
    }

    for from_id, to_id in pairs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing {from_id} → {to_id}")
        logger.info('='*60)

        try:
            data = analyzer.compute_transfer(from_id, to_id)
            key = f"{from_id}_to_{to_id}"
            all_data['transitions'][key] = data

            # Save individual file
            output_file = f"data/transfer_{from_id}_to_{to_id}.json"
            Path('data').mkdir(exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {output_file}")

        except Exception as e:
            logger.error(f"Failed to analyze {from_id} → {to_id}: {e}")
            raise

    # Save combined file
    with open('data/all_transfers.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    logger.info("\nSaved data/all_transfers.json")

    logger.info("\nDone!")


if __name__ == '__main__':
    main()
