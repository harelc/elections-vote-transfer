#!/usr/bin/env python3
"""
Generate irregularities data for Israeli election ballot boxes.
Detects various types of suspicious voting patterns including:
1. Data entry shift errors (votes in wrong column)
2. Overly round numbers
3. Statistical outliers
4. Impossible turnout
5. Single-party extreme dominance
6. Unusual patterns in small parties
"""

import pandas as pd
import numpy as np
import json
import re
import time
import requests
from collections import defaultdict
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from party_config import ELECTIONS, get_party_info, get_party_name

# URLs for official election results
OFFICIAL_URLS = {
    '21': 'https://votes21.bechirot.gov.il/ballotresults',
    '22': 'https://votes22.bechirot.gov.il/ballotresults',
    '23': 'https://votes23.bechirot.gov.il/ballotresults',
    '24': 'https://votes24.bechirot.gov.il/ballotresults',
    '25': 'https://votes25.bechirot.gov.il/ballotresults'
}

# Minimum votes for a ballot box to be analyzed
MIN_VOTES = 50

# Maximum irregularities to report per election
MAX_IRREGULARITIES = 100

# Minimum score to be considered truly irregular (must have at least one significant anomaly)
MIN_IRREGULARITY_SCORE = 8


def load_ballot_data(election_id):
    """Load ballot data for an election."""
    election = ELECTIONS[election_id]
    encoding = election.get('encoding', 'utf-8-sig')
    df = pd.read_csv(election['file'], encoding=encoding)
    # Fill NaN with 0 for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    return df


def get_party_columns(df, election_id):
    """Get all party symbol columns (everything after the standard columns)."""
    standard_cols = ['סמל ועדה', 'ברזל', 'שם ישוב', 'סמל ישוב', 'קלפי', 'ריכוז', 'שופט', 'בזב', 'מצביעים', 'פסולים', 'כשרים']
    # Also handle alternate column names
    alt_cols = ['סמל_ועדה', 'מספר קלפי']
    exclude = set(standard_cols + alt_cols)
    return [col for col in df.columns if col not in exclude and df[col].dtype in ['int64', 'float64', 'int32', 'float32']]


def safe_int(val):
    """Convert value to int, handling NaN and inf."""
    if pd.isna(val) or np.isinf(val):
        return 0
    return int(val)


def fetch_official_ballot_data(election_id, city_id, ballot_number):
    """
    Fetch ballot data from official election website using simple HTTP request.
    Returns (dict of party_symbol -> vote_count, was_corrected) or (None, False) on error.
    """
    if election_id not in OFFICIAL_URLS:
        return None, False

    url = f"{OFFICIAL_URLS[election_id]}?cityID={city_id}&BallotNumber={ballot_number}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, False

        html = response.text

        # Check if data was corrected
        was_corrected = 'תוקנו על ידי יושב-ראש' in html

        # Parse vote data from HTML table
        # Format: <td>symbol</td> ... <div class="FloatDir">votes</div>
        votes = {}

        # Find all table rows with vote data
        # Pattern: symbol in <td> followed later by votes in FloatDir div
        row_pattern = r'<tr>\s*<td[^>]*>[^<]*</td>\s*<td>\s*([א-ת]{1,4})\s*</td>\s*<td>[^<]*</td>\s*<td[^>]*>.*?<div class="FloatDir">\s*(\d+)\s*</div>'
        matches = re.findall(row_pattern, html, re.DOTALL)

        for symbol, vote_count in matches:
            try:
                votes[symbol.strip()] = int(vote_count.strip())
            except ValueError:
                continue

        return votes if votes else None, was_corrected

    except Exception as e:
        print(f"    Error fetching official data: {e}", flush=True)
        return None, False


def check_if_ballot_was_fixed(ballot_info, election_id):
    """
    Check if a ballot's data was corrected on the official website.
    Returns (was_fixed: bool, correction_note: str or None).
    """
    city_id = ballot_info.get('settlement_code', 0)
    ballot_number = ballot_info.get('ballot', '')

    # Clean ballot number (remove trailing .0 if any)
    if isinstance(ballot_number, str) and ballot_number.endswith('.0'):
        ballot_number = ballot_number[:-2]

    official_votes, was_corrected = fetch_official_ballot_data(election_id, city_id, ballot_number)

    if official_votes is None:
        # Couldn't fetch official data, keep the irregularity
        return False, None

    # If the official site explicitly says it was corrected, that's a fix
    if was_corrected:
        return True, "תוקן באתר הרשמי"

    csv_votes = ballot_info.get('votes', {})

    # Compare the votes - look for significant differences
    differences = []
    for symbol, csv_count in csv_votes.items():
        official_count = official_votes.get(symbol, 0)
        if csv_count > 5:  # Only check parties with meaningful votes
            diff = abs(csv_count - official_count)
            if diff >= 5:
                differences.append(f"{symbol}: CSV={csv_count}, רשמי={official_count}")

    # Also check for parties in official that aren't in CSV
    for symbol, official_count in official_votes.items():
        if symbol not in csv_votes and official_count >= 5:
            differences.append(f"{symbol}: CSV=0, רשמי={official_count}")

    if differences:
        return True, "; ".join(differences[:3])

    return False, None


def calculate_roundness_score(row, party_cols):
    """Calculate how 'round' the numbers are in this ballot."""
    votes = row[party_cols].values
    total = sum(votes)
    if total == 0:
        return 0

    round_10 = sum(1 for v in votes if v > 0 and v % 10 == 0)
    round_50 = sum(1 for v in votes if v > 0 and v % 50 == 0)
    round_100 = sum(1 for v in votes if v > 0 and v % 100 == 0)
    non_zero = sum(1 for v in votes if v > 0)

    if non_zero == 0:
        return 0

    # Weight: being divisible by 100 is more suspicious than by 10
    score = (round_10 * 1 + round_50 * 2 + round_100 * 3) / non_zero
    return score


def detect_shift_error(row, party_cols, national_profile, election_id):
    """
    Detect if votes might have been shifted to wrong column.
    Returns (score, explanation) tuple.
    """
    votes = row[party_cols].values
    total = sum(votes)
    if total < MIN_VOTES:
        return 0, None

    props = votes / total
    major_parties = ELECTIONS[election_id]['major_parties']['symbols']

    # Find unexpected zeros in major parties combined with unexpected spikes in adjacent columns
    anomalies = []

    for i, col in enumerate(party_cols):
        if col in major_parties:
            expected = national_profile.get(col, 0)
            actual = props[i] if i < len(props) else 0

            # Major party with suspiciously low votes
            if expected > 0.05 and actual < 0.01:
                # Check adjacent columns for unusual spikes
                for offset in [-1, 1]:
                    adj_idx = i + offset
                    if 0 <= adj_idx < len(party_cols):
                        adj_col = party_cols[adj_idx]
                        if adj_col not in major_parties:
                            adj_expected = national_profile.get(adj_col, 0)
                            adj_actual = props[adj_idx]
                            if adj_actual > 0.05 and adj_expected < 0.01:
                                direction = "→" if offset == 1 else "←"
                                anomalies.append({
                                    'missing': col,
                                    'unexpected': adj_col,
                                    'missing_votes': safe_int(votes[i]),
                                    'unexpected_votes': safe_int(votes[adj_idx]),
                                    'expected_missing': f"{expected*100:.1f}%",
                                    'expected_unexpected': f"{adj_expected*100:.1f}%",
                                    'missing_position': i + 1,
                                    'unexpected_position': adj_idx + 1,
                                    'direction': direction,
                                    'adjacent_symbols': f"{col} {direction} {adj_col}" if offset == 1 else f"{adj_col} {direction} {col}"
                                })

    if anomalies:
        return len(anomalies), anomalies
    return 0, None


def detect_statistical_outlier(row, party_cols, cluster_centers, scaler):
    """
    Detect if ballot is a statistical outlier compared to national clusters.
    Returns (distance_score, explanation).
    """
    votes = row[party_cols].values
    total = sum(votes)
    if total < MIN_VOTES:
        return 0, None

    props = votes / total
    props_scaled = scaler.transform([props])

    # Find minimum distance to any cluster center
    distances = [np.linalg.norm(props_scaled - center) for center in cluster_centers]
    min_distance = min(distances)

    return min_distance, None


def detect_roundness_anomaly(row, party_cols):
    """
    Detect suspiciously round vote counts.
    """
    votes = row[party_cols].values
    total = sum(votes)
    if total < MIN_VOTES:
        return 0, None

    non_zero_votes = [(col, safe_int(v)) for col, v in zip(party_cols, votes) if v > 0]

    # Count round numbers
    round_votes = []
    for col, v in non_zero_votes:
        if v >= 100 and v % 100 == 0:
            round_votes.append((col, v, 'מאות'))
        elif v >= 50 and v % 50 == 0:
            round_votes.append((col, v, 'חמישים'))
        elif v >= 10 and v % 10 == 0:
            round_votes.append((col, v, 'עשרות'))

    # Require at least 4 round numbers AND >60% of non-zero votes to be round
    if len(round_votes) >= 4 and len(non_zero_votes) >= 5 and len(round_votes) / len(non_zero_votes) > 0.6:
        return len(round_votes), round_votes

    return 0, None


def detect_turnout_anomaly(row):
    """
    Detect impossible or suspicious turnout.
    """
    eligible = row.get('בזב', 0)
    voted = row.get('מצביעים', 0)
    valid = row.get('כשרים', 0)
    invalid = row.get('פסולים', 0)

    anomalies = []

    # More votes than eligible
    if voted > eligible and eligible > 0:
        anomalies.append(f"מצביעים ({voted}) > בעלי זכות ({eligible})")

    # Valid + invalid doesn't match total
    if valid + invalid != voted and voted > 0:
        diff = voted - (valid + invalid)
        if abs(diff) > 1:  # Allow for rounding
            anomalies.append(f"כשרים+פסולים ({valid+invalid}) ≠ מצביעים ({voted})")

    # 100% turnout is suspicious in large ballots
    if eligible > 100 and voted == eligible:
        anomalies.append(f"השתתפות 100% ({voted}/{eligible})")

    if anomalies:
        return len(anomalies), anomalies
    return 0, None


def detect_extreme_dominance(row, party_cols, election_id):
    """
    Detect extreme single-party dominance that's unusual for the area type.
    """
    votes = row[party_cols].values
    total = sum(votes)
    if total < MIN_VOTES:
        return 0, None

    props = votes / total
    max_prop = max(props)
    max_idx = np.argmax(props)
    max_party = party_cols[max_idx]
    max_votes = safe_int(votes[max_idx])

    # Ultra-orthodox areas often have 90%+ for one party, so we need high threshold
    # But if a small/unknown party has extreme dominance, that's very suspicious
    major_parties = ELECTIONS[election_id]['major_parties']['symbols']

    if max_party not in major_parties and max_prop > 0.3:
        # Small party with >30% is very suspicious
        return max_prop, {
            'party': max_party,
            'party_name': get_party_name(max_party, election_id),
            'proportion': f"{max_prop*100:.1f}%",
            'votes': max_votes,
            'type': 'small_party_dominance'
        }

    if max_prop > 0.95 and max_party in major_parties:
        # Even for major parties, 95%+ is noteworthy
        return max_prop, {
            'party': max_party,
            'party_name': get_party_name(max_party, election_id),
            'proportion': f"{max_prop*100:.1f}%",
            'votes': max_votes,
            'type': 'extreme_dominance'
        }

    return 0, None


def detect_small_party_anomaly(row, party_cols, national_profile, election_id):
    """
    Detect unexpected votes in small/fringe parties.
    """
    votes = row[party_cols].values
    total = sum(votes)
    if total < MIN_VOTES:
        return 0, None

    props = votes / total
    major_parties = ELECTIONS[election_id]['major_parties']['symbols']

    anomalies = []
    for i, col in enumerate(party_cols):
        if col not in major_parties:
            expected = national_profile.get(col, 0)
            actual = props[i]
            actual_votes = safe_int(votes[i])

            # Small party with much higher than expected proportion
            if expected < 0.005 and actual > 0.05 and actual_votes >= 5:
                ratio = actual / max(expected, 0.001)
                if ratio > 20 and not np.isnan(ratio) and not np.isinf(ratio):  # 20x higher than national average
                    anomalies.append({
                        'party': col,
                        'party_name': get_party_name(col, election_id),
                        'votes': safe_int(actual_votes),
                        'proportion': f"{actual*100:.2f}%",
                        'national_avg': f"{expected*100:.3f}%",
                        'ratio': f"{ratio:.0f}x"
                    })

    if anomalies:
        return len(anomalies), anomalies
    return 0, None


def generate_irregularities(election_id):
    """Generate irregularities data for a single election."""
    print(f"Processing election {election_id}...", flush=True)

    df = load_ballot_data(election_id)
    party_cols = get_party_columns(df, election_id)

    print(f"  Found {len(df)} ballot boxes, {len(party_cols)} party columns", flush=True)

    # Calculate national profile (average proportions)
    total_votes = df[party_cols].sum()
    national_total = total_votes.sum()
    national_profile = {col: total_votes[col] / national_total for col in party_cols}

    # Build clusters for outlier detection
    valid_rows = df[df['כשרים'] >= MIN_VOTES].copy()
    props_matrix = valid_rows[party_cols].div(valid_rows['כשרים'], axis=0).fillna(0).values

    scaler = StandardScaler()
    props_scaled = scaler.fit_transform(props_matrix)

    # Use K-means to find demographic clusters
    n_clusters = min(10, len(valid_rows) // 100)
    if n_clusters >= 2:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(props_scaled)
        cluster_centers = scaler.transform(kmeans.cluster_centers_)
    else:
        cluster_centers = [props_scaled.mean(axis=0)]

    # Analyze each ballot box
    irregularities = []

    for idx, row in df.iterrows():
        if row.get('כשרים', 0) < MIN_VOTES:
            continue

        # Handle different ballot column names across elections
        ballot_num = row.get('קלפי', row.get('מספר קלפי', ''))
        ballot_id = f"{row.get('שם ישוב', '')}_{ballot_num}"
        ballot_info = {
            'id': ballot_id,
            'settlement': row.get('שם ישוב', ''),
            'settlement_code': safe_int(row.get('סמל ישוב', 0)),
            'ballot': str(ballot_num),
            'eligible': safe_int(row.get('בזב', 0)),
            'voted': safe_int(row.get('מצביעים', 0)),
            'valid': safe_int(row.get('כשרים', 0)),
            'invalid': safe_int(row.get('פסולים', 0)),
            'votes': {col: safe_int(row[col]) for col in party_cols if row[col] > 0},
            'anomalies': [],
            'score': 0
        }

        # Check for various anomalies

        # 1. Shift error
        shift_score, shift_info = detect_shift_error(row, party_cols, national_profile, election_id)
        if shift_score > 0:
            ballot_info['anomalies'].append({
                'type': 'shift_error',
                'severity': 'high',
                'description': 'חשד להזנת קולות בעמודה הלא נכונה',
                'details': shift_info
            })
            ballot_info['score'] += shift_score * 10

        # 2. Roundness
        round_score, round_info = detect_roundness_anomaly(row, party_cols)
        if round_score > 0:
            ballot_info['anomalies'].append({
                'type': 'round_numbers',
                'severity': 'medium',
                'description': 'מספרים עגולים באופן חשוד',
                'details': round_info
            })
            ballot_info['score'] += round_score * 2

        # 3. Turnout
        turnout_score, turnout_info = detect_turnout_anomaly(row)
        if turnout_score > 0:
            ballot_info['anomalies'].append({
                'type': 'turnout_anomaly',
                'severity': 'high',
                'description': 'אנומליה באחוזי ההשתתפות',
                'details': turnout_info
            })
            ballot_info['score'] += turnout_score * 15

        # 4. Statistical outlier - only flag extreme cases
        outlier_score, _ = detect_statistical_outlier(row, party_cols, cluster_centers, scaler)
        if outlier_score > 15:  # Very high distance from all clusters
            ballot_info['anomalies'].append({
                'type': 'statistical_outlier',
                'severity': 'medium',
                'description': 'דפוס הצבעה חריג שלא מתאים לאף אשכול דמוגרפי',
                'details': {'distance_score': f"{outlier_score:.2f}"}
            })
            ballot_info['score'] += outlier_score * 0.5  # Reduce weight

        # 5. Extreme dominance
        dom_score, dom_info = detect_extreme_dominance(row, party_cols, election_id)
        if dom_score > 0:
            ballot_info['anomalies'].append({
                'type': 'extreme_dominance',
                'severity': 'low' if dom_info.get('type') == 'extreme_dominance' else 'high',
                'description': 'שליטה קיצונית של מפלגה אחת',
                'details': dom_info
            })
            ballot_info['score'] += dom_score * 5 if dom_info.get('type') == 'small_party_dominance' else dom_score

        # 6. Small party anomaly
        small_score, small_info = detect_small_party_anomaly(row, party_cols, national_profile, election_id)
        if small_score > 0:
            ballot_info['anomalies'].append({
                'type': 'small_party_spike',
                'severity': 'high',
                'description': 'תוצאות גבוהות באופן חריג למפלגות קטנות',
                'details': small_info
            })
            ballot_info['score'] += small_score * 8

        # Only include if score is significant AND has at least one high-severity anomaly
        has_high_severity = any(a['severity'] == 'high' for a in ballot_info['anomalies'])
        if ballot_info['anomalies'] and ballot_info['score'] >= MIN_IRREGULARITY_SCORE and has_high_severity:
            irregularities.append(ballot_info)

    # Sort by score and take top N
    irregularities.sort(key=lambda x: x['score'], reverse=True)

    # Check against official data and filter out fixed irregularities
    print(f"  Found {len(irregularities)} potential irregularities, checking against official data...", flush=True)
    verified_irregularities = []
    checked = 0
    fixed_count = 0

    for ballot in irregularities:
        checked += 1
        if checked % 10 == 0:
            print(f"    Checked {checked} ballots...", flush=True)

        was_fixed, fix_note = check_if_ballot_was_fixed(ballot, election_id)
        if was_fixed:
            fixed_count += 1
            ballot['status'] = 'fixed'
            ballot['fix_note'] = fix_note
            print(f"    Ballot {ballot['settlement']} #{ballot['ballot']} - FIXED: {fix_note}", flush=True)
        else:
            ballot['status'] = 'verified'
            verified_irregularities.append(ballot)

        # Be nice to the server
        time.sleep(0.2)

    top_irregularities = verified_irregularities

    print(f"  {fixed_count} irregularities were fixed, reporting {len(top_irregularities)} remaining", flush=True)

    # Build output
    election_info = ELECTIONS[election_id]
    output = {
        'election': {
            'id': election_id,
            'name': election_info['name'],
            'name_en': election_info['name_en'],
            'date': election_info['date'],
            'total_ballots': len(df),
            'analyzed_ballots': len(valid_rows),
            'irregular_found': len(irregularities)
        },
        'parties': [],
        'irregularities': top_irregularities
    }

    # Add party info
    for symbol in party_cols:
        info = get_party_info(symbol, election_id)
        total = safe_int(total_votes[symbol])
        if total > 0:
            output['parties'].append({
                'symbol': symbol,
                'name': info['name'],
                'color': info['color'],
                'votes': total,
                'proportion': f"{national_profile[symbol]*100:.2f}%",
                'description': info.get('description', ''),
                'ideology': info.get('ideology', ''),
                'leader': info.get('leader', '')
            })

    # Sort parties by votes
    output['parties'].sort(key=lambda x: x['votes'], reverse=True)

    return output


def main():
    """Generate irregularities data for all elections."""
    for election_id in ['21', '22', '23', '24', '25']:
        try:
            data = generate_irregularities(election_id)

            output_file = f"data/irregularities_{election_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  Saved to {output_file}", flush=True)
        except Exception as e:
            print(f"  Error processing election {election_id}: {e}", flush=True)
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
