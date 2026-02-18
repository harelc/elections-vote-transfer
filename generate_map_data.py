#!/usr/bin/env python3
"""
Generate map data files from T-SNE JSON files.
Aggregates ballot data by settlement, merges with coordinates and socioeconomic clusters.
Output: site/data/map_*.json (one per election)
"""

import json
import os
from collections import defaultdict

# Paths
DATA_DIR = 'data'
SITE_DATA_DIR = 'site/data'
COORDINATES_FILE = os.path.join(SITE_DATA_DIR, 'station_coordinates.json')
SOCIOECONOMIC_FILE = os.path.join(SITE_DATA_DIR, 'socioeconomic_clusters.json')

ELECTIONS = ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26']

# CSV files and encodings per election (for counting total lists)
ELECTION_CSV = {
    '16': ('ballot16.csv', 'utf-8-sig'),
    '17': ('ballot17.csv', 'utf-8-sig'),
    '18': ('ballot18.csv', 'utf-8-sig'),
    '19': ('ballot19.csv', 'utf-8-sig'),
    '20': ('ballot20.csv', 'utf-8-sig'),
    '21': ('ballot21.csv', 'iso8859_8'),
    '22': ('ballot22.csv', 'iso8859_8'),
    '23': ('ballot23.csv', 'iso8859_8'),
    '24': ('ballot24.csv', 'iso8859_8'),
    '25': ('ballot25.csv', 'utf-8-sig'),
    '26': ('ballot26.csv', 'utf-8-sig'),
}


# Post-normalization name corrections (CEC misspellings → canonical names)
NAME_OVERRIDES = {
    'גולס': "ג'וליס",
    'גוליס': "ג'וליס",
}


def normalize_name(name):
    """Normalize settlement name for matching.

    The CEC changed formatting between elections 22→23, stripping hyphens,
    geresh/gershayim, and parentheses. This ensures consistent names across all elections.
    """
    if not name:
        return name
    # Remove dashes
    normalized = name.replace('-', ' ').replace('–', ' ')
    # Remove geresh (ASCII apostrophe and Hebrew geresh)
    normalized = normalized.replace("'", '').replace('\u05f3', '')
    # Remove gershayim (ASCII double-quote and Hebrew gershayim)
    normalized = normalized.replace('"', '').replace('\u05f4', '')
    # Remove parentheses
    normalized = normalized.replace('(', ' ').replace(')', ' ')
    # Collapse multiple spaces
    normalized = ' '.join(normalized.split())
    # Normalize double-yod to single (קריית -> קרית)
    normalized = normalized.replace('יי', 'י')
    # Apply name overrides
    normalized = NAME_OVERRIDES.get(normalized, normalized)
    return normalized


def count_lists(election_id):
    """Count total party lists from CSV header."""
    csv_info = ELECTION_CSV.get(election_id)
    if not csv_info:
        return 0
    filepath, encoding = csv_info
    if not os.path.exists(filepath):
        return 0
    with open(filepath, encoding=encoding) as f:
        header = f.readline().strip().split(',')
    try:
        idx = header.index('\u05db\u05e9\u05e8\u05d9\u05dd')  # כשרים
        return len(header) - idx - 1
    except ValueError:
        return 0


def load_coordinates():
    """Load settlement coordinates from station_coordinates.json.

    The file has station-level data keyed by 'settlement|ballot'.
    We extract unique settlement coordinates (using first station per settlement).
    """
    if not os.path.exists(COORDINATES_FILE):
        print(f"Warning: Coordinates file not found: {COORDINATES_FILE}")
        return {}, []

    with open(COORDINATES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = data.get('stations', {})

    # Extract unique settlement coordinates from station-level data
    lookup = {}
    not_found = []
    for key, station in stations.items():
        settlement = station.get('settlement', '')
        lat = station.get('lat')
        lng = station.get('lng')
        source = station.get('source', '')

        if not settlement or source == 'not_found' or lat is None or lng is None:
            continue

        if settlement not in lookup:
            lookup[settlement] = {'lat': lat, 'lng': lng}
            normalized = normalize_name(settlement)
            if normalized != settlement:
                lookup[normalized] = {'lat': lat, 'lng': lng}

    return lookup, not_found


def load_socioeconomic():
    """Load socioeconomic cluster data."""
    if not os.path.exists(SOCIOECONOMIC_FILE):
        print(f"Warning: Socioeconomic file not found: {SOCIOECONOMIC_FILE}")
        return {}

    with open(SOCIOECONOMIC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Build lookup with both original and normalized names
    lookup = {}
    for item in data:
        name = item['name']
        cluster = item['cluster']
        lookup[name] = cluster
        normalized = normalize_name(name)
        if normalized != name:
            lookup[normalized] = cluster

    return lookup


def load_tsne_data(election_id):
    """Load T-SNE data for an election."""
    tsne_file = os.path.join(SITE_DATA_DIR, f'tsne_{election_id}.json')
    if not os.path.exists(tsne_file):
        print(f"Warning: T-SNE file not found: {tsne_file}")
        return None

    with open(tsne_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def aggregate_by_settlement(tsne_data, coordinates, socioeconomic):
    """Aggregate ballot data by settlement."""
    settlements = defaultdict(lambda: {
        'voters': 0,
        'eligible': 0,
        'ballotCount': 0,
        'partyVotes': defaultdict(float),  # Total percentage points (will average later)
        'ballots': []  # Store individual ballot data for expansion
    })

    for station in tsne_data.get('stations', []):
        name = station.get('n') or station.get('settlement_name')
        if not name:
            continue
        name = normalize_name(name)

        ballot_num = station.get('b') or station.get('ballot_number')
        voters = station.get('v') or station.get('total_voters', 0)
        eligible = station.get('e') or station.get('eligible_voters', 0)
        proportions = station.get('p') or station.get('proportions', {})
        turnout = station.get('t') or station.get('turnout', 0)
        location = station.get('l') or ''

        settlements[name]['voters'] += voters
        settlements[name]['eligible'] += eligible
        settlements[name]['ballotCount'] += 1

        # Accumulate party votes weighted by voter count
        for party, pct in proportions.items():
            settlements[name]['partyVotes'][party] += pct * voters

        # Store individual ballot for expansion view
        settlements[name]['ballots'].append({
            'b': ballot_num,
            'v': voters,
            'e': eligible,
            't': turnout,
            'l': location,
            'p': proportions
        })

    # Convert to final format
    result = []
    missing_coords = []

    for name, data in settlements.items():
        # Get coordinates
        coords = coordinates.get(name) or coordinates.get(normalize_name(name))

        if not coords:
            missing_coords.append(name)
            continue

        # Calculate weighted average proportions
        total_voters = data['voters']
        proportions = {}
        if total_voters > 0:
            for party, weighted_sum in data['partyVotes'].items():
                proportions[party] = round(weighted_sum / total_voters, 1)

        # Find winning party
        winning_party = max(proportions, key=proportions.get) if proportions else None

        # Get socioeconomic cluster
        cluster = socioeconomic.get(name) or socioeconomic.get(normalize_name(name))

        # Calculate overall turnout
        turnout = round(100 * data['voters'] / data['eligible'], 1) if data['eligible'] > 0 else 0

        settlement_data = {
            'name': name,
            'lat': coords.get('lat'),
            'lng': coords.get('lng'),
            'voters': data['voters'],
            'eligible': data['eligible'],
            'turnout': turnout,
            'ballotCount': data['ballotCount'],
            'proportions': proportions,
            'winningParty': winning_party
        }

        if cluster:
            settlement_data['cluster'] = cluster

        # Include individual ballots for click-to-expand
        settlement_data['ballots'] = data['ballots']

        result.append(settlement_data)

    return result, missing_coords


def generate_map_data():
    """Generate map data files for all elections."""
    print("Loading coordinates...")
    coordinates, coord_unmatched = load_coordinates()
    print(f"  Loaded {len(coordinates)} settlement coordinates")
    if coord_unmatched:
        print(f"  {len(coord_unmatched)} settlements without coordinates")

    print("Loading socioeconomic data...")
    socioeconomic = load_socioeconomic()
    print(f"  Loaded {len(socioeconomic)} socioeconomic entries")

    all_missing = set()

    for election_id in ELECTIONS:
        print(f"\nProcessing election {election_id}...")

        tsne_data = load_tsne_data(election_id)
        if not tsne_data:
            continue

        settlements, missing = aggregate_by_settlement(tsne_data, coordinates, socioeconomic)
        all_missing.update(missing)

        # Build output structure
        output = {
            'election': tsne_data.get('election', {}),
            'parties': tsne_data.get('parties', []),
            'settlements': settlements,
            'stats': {
                'totalSettlements': len(settlements),
                'totalBallots': sum(s['ballotCount'] for s in settlements),
                'totalVoters': sum(s['voters'] for s in settlements),
                'totalEligible': sum(s['eligible'] for s in settlements),
                'totalLists': count_lists(election_id),
                'missingCoordinates': len(missing)
            }
        }

        # Write output
        output_file = os.path.join(SITE_DATA_DIR, f'map_{election_id}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"  Written: {output_file}")
        print(f"  Settlements: {len(settlements)}, Ballots: {output['stats']['totalBallots']}")
        if missing:
            print(f"  Missing coordinates for {len(missing)} settlements")

    if all_missing:
        print(f"\n=== Settlements missing coordinates across all elections ===")
        for name in sorted(all_missing):
            print(f"  - {name}")

    print("\nDone!")


if __name__ == '__main__':
    generate_map_data()
