#!/usr/bin/env python3
"""
Add ballot location names to T-SNE JSON data files.
Run this after scrape_ballot_locations.py completes.

Written by Harel Cain, 2024
"""

import json
import logging
from pathlib import Path

from party_config import ELECTIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_ballot_locations(election_id):
    """Load scraped ballot locations for an election."""
    locations_file = Path(f'data/ballot_locations_{election_id}.json')
    if not locations_file.exists():
        logger.warning(f"No ballot locations file for election {election_id}")
        return None

    with open(locations_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_tsne_data(election_id):
    """Load T-SNE data for an election."""
    tsne_file = Path(f'site/data/tsne_{election_id}.json')
    if not tsne_file.exists():
        # Try alternate location
        tsne_file = Path(f'data/tsne_{election_id}.json')

    if not tsne_file.exists():
        logger.warning(f"No T-SNE file for election {election_id}")
        return None, None

    with open(tsne_file, 'r', encoding='utf-8') as f:
        return json.load(f), tsne_file


def normalize_ballot_number(ballot):
    """Normalize ballot number - remove trailing .0 if present."""
    ballot = str(ballot)
    if ballot.endswith('.0'):
        ballot = ballot[:-2]
    return ballot


def match_location(station, locations_data, election_config):
    """Try to match a station with its ballot location."""
    # Get station info (handle both compact and full formats)
    settlement_name = station.get('n') or station.get('settlement_name', '')
    ballot_number = str(station.get('b') or station.get('ballot_number', ''))
    ballot_normalized = normalize_ballot_number(ballot_number)

    if not settlement_name or not ballot_number:
        return None

    settlements = locations_data.get('settlements', {})
    b2l = locations_data.get('ballot_to_location', {})

    # Find settlement ID by name
    settlement_id = None
    for sid, sdata in settlements.items():
        # Handle both formats: {id: {name: str, ...}} and {id: str}
        sname = sdata['name'] if isinstance(sdata, dict) else sdata
        if sname == settlement_name:
            settlement_id = sid
            break

    if not settlement_id:
        return None

    # Try structured ballots list (K21-K25 format)
    sdata = settlements.get(settlement_id)
    if isinstance(sdata, dict):
        for ballot in sdata.get('ballots', []):
            if ballot['ballot'] == ballot_number or ballot['ballot'] == ballot_normalized:
                return ballot['location']

    # Try flat ballot_to_location mapping
    for bn in [ballot_number, ballot_normalized]:
        key = f"{settlement_id}:{bn}"
        location = b2l.get(key)
        if location:
            return location

    return None


def add_locations_to_tsne(election_id):
    """Add ballot locations to T-SNE data for one election."""
    logger.info(f"Processing election {election_id}...")

    # Load data
    locations_data = load_ballot_locations(election_id)
    if not locations_data:
        return False

    tsne_data, tsne_file = load_tsne_data(election_id)
    if not tsne_data:
        return False

    election_config = ELECTIONS.get(election_id, {})

    # Match locations for each station
    matched = 0
    total = len(tsne_data.get('stations', []))

    for station in tsne_data.get('stations', []):
        location = match_location(station, locations_data, election_config)
        if location:
            # Add location using compact key 'l' for location
            station['l'] = location
            matched += 1

    logger.info(f"  Matched {matched}/{total} stations ({100*matched/total:.1f}%)")

    # Save updated T-SNE data
    with open(tsne_file, 'w', encoding='utf-8') as f:
        json.dump(tsne_data, f, ensure_ascii=False)

    logger.info(f"  Saved to {tsne_file}")
    return True


def main():
    """Add locations to all T-SNE files."""
    import argparse

    parser = argparse.ArgumentParser(description='Add ballot locations to T-SNE data')
    all_elections = ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25']
    parser.add_argument('--election', '-e', choices=all_elections + ['all'],
                       default='all', help='Election to process (default: all)')
    args = parser.parse_args()

    elections = all_elections if args.election == 'all' else [args.election]

    for election_id in elections:
        try:
            add_locations_to_tsne(election_id)
        except Exception as e:
            logger.error(f"Error processing election {election_id}: {e}")

    logger.info("Done!")


if __name__ == '__main__':
    main()
