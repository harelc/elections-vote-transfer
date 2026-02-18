#!/usr/bin/env python3
"""
Generate T-SNE projection data for Israeli Knesset election voting stations.
Each voting station is projected based on its vote distribution across parties.

Written by Harel Cain, 2024
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
try:
    import umap
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

from party_config import ELECTIONS, get_party_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_election_data(election_id):
    """Load election data from CSV."""
    config = ELECTIONS[election_id]

    logger.info(f"Loading {config['name']} from {config['file']}")

    df = pd.read_csv(
        config['file'],
        encoding=config['encoding']
    )

    logger.info(f"Loaded {len(df)} precincts")
    return df, config


def compute_tsne_projection(df, config, perplexity=30, random_state=42):
    """
    Compute T-SNE projection for voting stations based on vote proportions.

    Args:
        df: DataFrame with voting station data
        config: Election configuration
        perplexity: T-SNE perplexity parameter
        random_state: Random seed for reproducibility

    Returns:
        DataFrame with T-SNE coordinates and station metadata
    """
    parties = config['major_parties']
    symbols = parties['symbols']
    names = parties['names']

    # Filter to existing columns
    existing_symbols = [s for s in symbols if s in df.columns]
    existing_names = [names[i] for i, s in enumerate(symbols) if s in df.columns]

    if len(existing_symbols) < len(symbols):
        missing = set(symbols) - set(existing_symbols)
        logger.warning(f"Missing party columns: {missing}")

    # Extract vote counts for major parties
    vote_data = df[existing_symbols].copy()
    vote_data.columns = existing_names

    # Calculate total votes per station for normalization
    total_votes = vote_data.sum(axis=1)

    # Filter out stations with very few votes (noise)
    min_votes = 50
    valid_mask = total_votes >= min_votes
    logger.info(f"Filtering stations with >= {min_votes} votes: {valid_mask.sum()} of {len(df)}")

    df_filtered = df[valid_mask].copy()
    vote_data_filtered = vote_data[valid_mask].copy()
    total_votes_filtered = total_votes[valid_mask]

    # Convert to vote proportions (each row sums to 1)
    vote_proportions = vote_data_filtered.div(total_votes_filtered, axis=0)
    vote_proportions = vote_proportions.fillna(0)

    # Standardize for T-SNE (helps with convergence)
    scaler = StandardScaler()
    vote_scaled = scaler.fit_transform(vote_proportions.values)

    # Compute T-SNE
    logger.info(f"Computing T-SNE with perplexity={perplexity}...")
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=random_state,
        max_iter=1000,
        learning_rate='auto',
        init='pca'
    )

    coords = tsne.fit_transform(vote_scaled)
    logger.info("T-SNE computation complete")

    # Compute UMAP
    umap_coords = None
    if HAS_UMAP:
        logger.info("Computing UMAP...")
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=30,
            min_dist=0.3,
            metric='euclidean',
            random_state=random_state,
        )
        umap_coords = reducer.fit_transform(vote_scaled)
        logger.info("UMAP computation complete")
    else:
        logger.warning("umap-learn not installed, skipping UMAP")

    # Build result data
    result = []
    ballot_field = config.get('ballot_field', 'קלפי')
    divisor = config.get('ballot_number_divisor', 1)

    for i, (idx, row) in enumerate(df_filtered.iterrows()):
        # Calculate turnout
        eligible = int(row.get('בזב', 0))
        actual_voters = int(row.get('מצביעים', 0))
        turnout = round((actual_voters / eligible * 100), 1) if eligible > 0 else 0

        # Normalize ballot number (K16-K17 use x10 numbering)
        raw_ballot = str(row.get(ballot_field, ''))
        if raw_ballot.endswith('.0'):
            raw_ballot = raw_ballot[:-2]
        if divisor > 1:
            try:
                n = int(raw_ballot)
                if n % divisor == 0:
                    raw_ballot = str(n // divisor)
            except ValueError:
                pass

        # Get station metadata
        station_data = {
            'x': float(coords[i, 0]),
            'y': float(coords[i, 1]),
            'id': int(idx),
            'settlement_name': str(row.get('שם ישוב', '')),
            'settlement_id': int(row.get('סמל ישוב', 0)),
            'ballot_number': raw_ballot,
            'total_voters': int(total_votes_filtered.iloc[i]),
            'eligible_voters': eligible,
            'turnout': turnout,
        }
        if umap_coords is not None:
            station_data['ux'] = float(umap_coords[i, 0])
            station_data['uy'] = float(umap_coords[i, 1])

        # Add committee symbol if available
        if 'סמל ועדה' in row:
            station_data['committee_id'] = str(row['סמל ועדה'])

        # Add vote counts and proportions for each party
        votes = {}
        proportions = {}
        for j, name in enumerate(existing_names):
            symbol = existing_symbols[j]
            vote_count = int(vote_data_filtered.iloc[i][name])
            proportion = float(vote_proportions.iloc[i][name])
            votes[name] = vote_count
            proportions[name] = round(proportion * 100, 1)  # As percentage

        station_data['votes'] = votes
        station_data['proportions'] = proportions

        result.append(station_data)

    return result, existing_names, existing_symbols


def generate_tsne_json(election_id, compact=True):
    """Generate T-SNE data for a single election."""
    df, config = load_election_data(election_id)

    # Filter out aggregated data (city 9999)
    df = df[df['סמל ישוב'] != 9999].copy()
    df = df.reset_index(drop=True)

    # Compute T-SNE projection
    stations, party_names, party_symbols = compute_tsne_projection(df, config)

    # Build party info for legend (always include info for tooltips)
    parties = []
    for i, name in enumerate(party_names):
        symbol = party_symbols[i]
        info = get_party_info(symbol, election_id)
        party_data = {
            'name': name,
            'symbol': symbol,
            'color': info['color'],
            'info': {
                'leader': info.get('leader', ''),
                'leader_image': info.get('leader_image', ''),
                'logo': info.get('logo', ''),
                'ideology': info.get('ideology', ''),
                'description': info.get('description', ''),
            }
        }
        parties.append(party_data)

    # For compact mode, simplify station data
    if compact:
        compact_stations = []
        for s in stations:
            cs = {
                'x': round(s['x'], 2),
                'y': round(s['y'], 2),
                'n': s['settlement_name'],  # shortened key
                'b': s['ballot_number'],     # shortened key
                'v': s['total_voters'],      # shortened key
                'e': s['eligible_voters'],   # eligible voters
                't': s['turnout'],           # turnout percentage
                'p': s['proportions'],       # keep proportions for coloring
            }
            if 'ux' in s:
                cs['ux'] = round(s['ux'], 2)
                cs['uy'] = round(s['uy'], 2)
            compact_stations.append(cs)
        stations = compact_stations

    # Create output structure
    output = {
        'election': {
            'id': election_id,
            'name': config['name'],
            'name_en': config['name_en'],
            'date': config['date'],
        },
        'parties': parties,
        'stations': stations,
        'stats': {
            'total_stations': len(stations),
            'parties_count': len(parties),
        }
    }

    return output


def main():
    """Generate T-SNE data for all elections."""
    import argparse
    parser = argparse.ArgumentParser(description='Generate T-SNE clustering data')
    parser.add_argument('--elections', nargs='+',
                        help='Only process specific elections, e.g. --elections 25 26')
    args = parser.parse_args()

    elections = args.elections or ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25']

    for election_id in elections:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing election {election_id}")
        logger.info('='*60)

        try:
            data = generate_tsne_json(election_id)

            # Save to file
            output_file = f"data/tsne_{election_id}.json"
            Path('data').mkdir(exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {output_file} ({data['stats']['total_stations']} stations)")

        except Exception as e:
            logger.error(f"Failed to process election {election_id}: {e}")
            raise

    logger.info("\nDone!")


if __name__ == '__main__':
    main()
