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
import csv
import json
import math
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from pyproj import Transformer
from party_config import ELECTIONS

# ============================================================================
# CONFIGURATION — Edit these to model different scenarios
# ============================================================================

# E26 party definitions: symbol → (hebrew_name, color)
# List map follows Madad 120 (7 Sep 2026): Yashar, Likud, Beyachad, Democrats,
# YB, Joint List (Hadash–Ta'al–Balad), UTJ, Shas, Otzma, RZ+Zehut, Ra'am,
# Amcha Yisrael (Winter), Hendel–Zelicha, Gantz below threshold.
# Official CEC letter-symbols (candidates-lists-26, finalized).
E26_PARTIES = {
    'דרך': ('ישר', '#14b8a6'),
    'מחל': ('הליכוד', '#2563eb'),
    'רק':  ('ביחד', '#f97316'),
    'אמת': ('הדמוקרטים', '#16a34a'),
    'ל':   ('ישראל ביתנו', '#db2777'),
    'ודם': ('הרשימה המשותפת', '#0d9488'),
    'ג':   ('יהדות התורה', '#4b5563'),
    'שס':  ('ש״ס', '#1e3a8a'),
    'ב':   ('עוצמה יהודית', '#7f1d1d'),
    'ט':   ('הציונות הדתית', '#92400e'),
    'עם':  ('רע״ם', '#84cc16'),
    'ך':   ('עמך ישראל', '#4d7c0f'),
    'די':  ('הנדל–זליכה', '#d97706'),
    'כן':  ('כחול לבן', '#8b5cf6'),
    # Below the threshold, but large enough to show beside the other lists.
    # הציבור החרדי draws from Shas and UTJ; Noam draws from the K25
    # Religious Zionism list (Otzma + RZ + Noam ran together in 2022).
    'זך':  ('הציבור החרדי', '#a16207'),
    'ני':  ('נעם', '#be123c'),
}

# Below-threshold lists. Columns exist so the dashboard list-count is right.
# They stay at 0; the Dirichlet draw covers the majors only.
E26_TINY = [
    ('בד', 'ביחד נצליח'), ('בי', 'צומת בית ישראל'), ('בקר', 'אורות השחר'),
    ('ד', 'השותפות לכולם'), ('ה', 'גן עדן'),     ('ז', 'בטח'),
    ('זץ', 'ברית עולם'), ('י', 'ישראל תחילה'),
    ('יק', 'גה״ת'), ('נף', 'שמע'), ('נץ', 'ביטחון אישי'),
    ('נקי', 'התיקון'), ('נר', 'צבע שחור'), ('פה', 'אני ואתה'),
    ('צבי', 'תנועת אחי'), ('צדק', 'שרשר'), ('צף', 'הפיראטים'),
    ('ק', 'תקומה'), ('קה', 'קול הנשים'), ('קך', 'סדר חדש'),
    ('קץ', 'משפט צדק'), ('רץ', 'הקהל'),
]

# Madad 120 center, 7 Sep 2026. Both threshold lists included as passing (4 each);
# 1 seat shaved from Yashar / Likud / Beyachad so the 120 still add up.
TARGET_SEATS = {
    'ישר': 22, 'הליכוד': 20, 'ביחד': 13, 'הדמוקרטים': 9,
    'ישראל ביתנו': 8, 'הרשימה המשותפת': 8, 'יהדות התורה': 8,
    'ש״ס': 7, 'עוצמה יהודית': 7, 'הציונות הדתית': 5, 'רע״ם': 5,
    'עמך ישראל': 4, 'הנדל–זליכה': 4, 'כחול לבן': 0,
    'הציבור החרדי': 0, 'נעם': 0,
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
# Yashar has to outpoll Likud. Ballot size follows the K25 turnout map, so a
# 73% Likud retention beat Yashar. The center (Yesh Atid, National Unity)
# leans to Yashar, and 2pp of Likud moves to Amcha.
TRANSFER_MATRIX = {
    'הליכוד': {
        'הליכוד': 0.71, 'עוצמה יהודית': 0.08, 'עמך ישראל': 0.11,
        'הציונות הדתית': 0.05, 'ש״ס': 0.03, 'יהדות התורה': 0.02,
    },
    'יש עתיד': {
        'ביחד': 0.36, 'ישר': 0.46, 'הדמוקרטים': 0.07, 'ישראל ביתנו': 0.03,
        'הנדל–זליכה': 0.06, 'כחול לבן': 0.02,
    },
    'הציונות הדתית': {
        'עוצמה יהודית': 0.365, 'הציונות הדתית': 0.325, 'עמך ישראל': 0.18,
        'הליכוד': 0.10, 'נעם': 0.030,
    },
    'המחנה הממלכתי': {
        'ישר': 0.66, 'ביחד': 0.10, 'הנדל–זליכה': 0.16, 'הדמוקרטים': 0.03,
        'ישראל ביתנו': 0.02, 'כחול לבן': 0.03,
    },
    'ש״ס': {
        'ש״ס': 0.856, 'הליכוד': 0.05, 'יהדות התורה': 0.05, 'עוצמה יהודית': 0.02,
        'הציבור החרדי': 0.024,
    },
    'יהדות התורה': {
        'יהדות התורה': 0.916, 'ש״ס': 0.04, 'הליכוד': 0.02,
        'הציבור החרדי': 0.024,
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

# National K26 turnout (voters / eligible), applied on top of the K25
# geographic pattern so high-turnout and low-turnout boxes stay apart.
TARGET_TURNOUT = 0.743

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


def _norm_ballot(value):
    text = str(value).strip()
    if text.endswith('.0'):
        text = text[:-2]
    return text


def _votes_by_name(row, party_cols):
    votes = {}
    for sym in party_cols:
        name = E25_SYMBOL_TO_NAME.get(sym)
        count = int(row.get(sym, 0) or 0)
        if name:
            votes[name] = votes.get(name, 0) + count
        elif count:
            votes['_small'] = votes.get('_small', 0) + count
    small = votes.pop('_small', 0)
    if small:
        dominant = get_dominant_party(votes)
        votes[dominant or 'הליכוד'] = votes.get(dominant or 'הליכוד', 0) + small
    return votes


def _load_k25_coords():
    raw = json.loads(Path('site/data/station_coordinates.json').read_text(encoding='utf-8'))
    lookup = {}
    for key, val in raw.get('stations', {}).items():
        if '|' not in key or val.get('lat') is None:
            continue
        name, ballot = key.rsplit('|', 1)
        lookup[(name, _norm_ballot(ballot))] = (float(val['lat']), float(val['lng']))
    return lookup


def _load_k25_ballots():
    config = ELECTIONS['25']
    frame = pd.read_csv(config['file'], encoding=config['encoding'])
    frame = frame[frame['סמל ישוב'] != 9999]
    kosher = list(frame.columns).index('כשרים')
    party_cols = list(frame.columns)[kosher + 1:]
    coords = _load_k25_coords()
    by_id = {}
    by_settlement = {}
    points = {}
    for _, row in frame.iterrows():
        code = int(row['סמל ישוב'])
        ballot = _norm_ballot(row['קלפי'])
        bid = f"{code}__{ballot}"
        latlng = coords.get((str(row['שם ישוב']).strip(), ballot))
        record = {
            'eligible': int(row['בזב'] or 0),
            'valid': int(row['כשרים'] or 0),
            'invalid': int(row['פסולים'] or 0),
            'votes': _votes_by_name(row, party_cols),
            'lat': latlng[0] if latlng else None,
            'lng': latlng[1] if latlng else None,
            'code': code,
        }
        by_id[bid] = record
        bucket = by_settlement.setdefault(code, {'eligible': 0, 'valid': 0, 'invalid': 0, 'votes': {}})
        bucket['eligible'] += record['eligible']
        bucket['valid'] += record['valid']
        bucket['invalid'] += record['invalid']
        for name, count in record['votes'].items():
            bucket['votes'][name] = bucket['votes'].get(name, 0) + count
        if latlng:
            points.setdefault(code, []).append(record)
    return by_id, by_settlement, points


def _load_crosswalk():
    path = Path('data/k25_k26_ballot_union.csv')
    pairs = {}
    with path.open(encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            if row['decision'] not in ('id', 'id_dot1', 'venue', 'coord'):
                continue
            k26 = f"{int(float(row['k26_code']))}__{row['k26_ballot']}"
            k25 = f"{int(float(row['k25_code']))}__{row['k25_ballot']}"
            pairs[k26] = k25
    return pairs


def _load_cluster_xy():
    """Official cluster points. X=0,Y=0 is a blank cell, not a place."""
    to_wgs = Transformer.from_crs('EPSG:2039', 'EPSG:4326', always_xy=True)
    book = openpyxl.load_workbook(Path('data/k26_cec/clusters.xlsx'), read_only=True, data_only=True)
    rows = list(book.active.iter_rows(values_only=True))
    book.close()
    header = {name: i for i, name in enumerate(rows[0])}
    points = {}
    for row in rows[1:]:
        if row[header['סמל ישוב בחירות']] is None or not row[header['X']] or not row[header['Y']]:
            continue
        lng, lat = to_wgs.transform(float(row[header['X']]), float(row[header['Y']]))
        if not (29.4 < lat < 33.45 and 34.2 < lng < 35.95):
            continue
        points[(int(row[header['סמל ישוב בחירות']]), row[header['סמל רכוז']])] = (lat, lng)
    return points


def _load_k26_stations():
    path = Path('data/k26_cec/stations.xlsx')
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(book.active.iter_rows(values_only=True))
    book.close()
    header = {name: i for i, name in enumerate(rows[0])}
    clusters = _load_cluster_xy()
    stations = []
    for row in rows[1:]:
        if row[header['סמל ישוב בחירות']] is None or row[header['סמל קלפי']] is None:
            continue
        code = int(row[header['סמל ישוב בחירות']])
        cluster = row[header['סמל רכוז']]
        latlng = clusters.get((code, cluster))
        stations.append({
            'committee': int(row[header['סמל ועדה']] or 0),
            'serial': int(row[header["מס' ברזל"]] or 0),
            'name': str(row[header['שם ישוב בחירות']] or '').strip(),
            'code': code,
            'ballot': _norm_ballot(row[header['סמל קלפי']]),
            'cluster': int(cluster or 0),
            'eligible': int(row[header['בוחרי כנסת']] or 0),
            'lat': latlng[0] if latlng else None,
            'lng': latlng[1] if latlng else None,
        })
    return stations


def _hav(a, b):
    radius = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(min(1.0, x)))


def _pool(records):
    pooled = {'eligible': 0, 'valid': 0, 'invalid': 0, 'votes': {}}
    for record in records:
        pooled['eligible'] += record['eligible']
        pooled['valid'] += record['valid']
        pooled['invalid'] += record['invalid']
        for name, count in record['votes'].items():
            pooled['votes'][name] = pooled['votes'].get(name, 0) + count
    return pooled


def _nearby_k25(station, points_by_code):
    """Vote mix for an unmatched K26 box: nearby K25 boxes, simulation only.

    Prefer every K25 box within 250 m in the same settlement. Otherwise the
    eight nearest boxes there. The settlement-wide mix is the last resort.
    """
    local = points_by_code.get(station['code'], [])
    if station['lat'] is not None and local:
        here = (station['lat'], station['lng'])
        ranked = sorted(((_hav(here, (p['lat'], p['lng'])), p) for p in local), key=lambda item: item[0])
        close = [p for dist, p in ranked if dist <= 250]
        if close:
            return _pool(close), 'within_250m', len(close)
        return _pool([p for _, p in ranked[:8]]), 'nearest_8', 8
    return None, 'settlement', 0


def _source_rates(record):
    eligible = record['eligible']
    voters = record['valid'] + record['invalid']
    if eligible <= 0 or voters <= 0:
        return None, 0.008
    return voters / eligible, record['invalid'] / voters


def _rescale(votes, target):
    if target <= 0 or sum(votes.values()) <= 0:
        return {name: 0 for name in votes}
    raw = np.array([votes[name] for name in votes], dtype=float)
    raw = raw / raw.sum() * target
    rounded = largest_remainder_round(raw, int(target))
    return {name: int(rounded[i]) for i, name in enumerate(votes)}


def simulate(alpha=55, seed=42):
    """Generate ballot26.csv on the official roster, at TARGET_TURNOUT."""
    validate_config()
    rng = np.random.default_rng(seed)
    k25_by_id, k25_by_settlement, k25_points = _load_k25_ballots()
    crosswalk = _load_crosswalk()
    stations = _load_k26_stations()
    e26_names = [name for _, (name, _) in E26_PARTIES.items()]

    sources = []
    neighbor_modes = {}
    for station in stations:
        bid = f"{station['code']}__{station['ballot']}"
        record = k25_by_id.get(crosswalk.get(bid))
        mode = 'paired'
        if record is None:
            record, mode, _ = _nearby_k25(station, k25_points)
            if record is None:
                record = k25_by_settlement.get(station['code'])
                mode = 'settlement'
        if record is None or not record['votes']:
            record = {'eligible': 0, 'valid': 0, 'invalid': 0, 'votes': {'הליכוד': 1}}
            mode = 'national'
        neighbor_modes[mode] = neighbor_modes.get(mode, 0) + 1
        rate, invalid_share = _source_rates(record)
        sources.append((station, record, rate if rate is not None else 0.67, invalid_share))

    weighted = sum(station['eligible'] * rate for station, _, rate, _ in sources)
    eligible_total = sum(station['eligible'] for station, _, _, _ in sources) or 1
    scale = TARGET_TURNOUT / (weighted / eligible_total)

    print(f"Official boxes: {len(stations):,}  eligible: {eligible_total:,}")
    print(f"Turnout target {TARGET_TURNOUT:.1%}, K25-pattern scale {scale:.3f}")
    paired = sum(1 for station, _, _, _ in sources if f"{station['code']}__{station['ballot']}" in crosswalk)
    print(f"Crosswalk hits: {paired:,}")
    print("Unmatched source: " + ", ".join(f"{k} {v}" for k, v in sorted(neighbor_modes.items())))

    out_rows = []
    for station, record, rate, invalid_share in sources:
        turnout = min(0.97, max(0.05, rate * scale))
        voters = int(round(station['eligible'] * turnout))
        invalid = min(voters, int(round(voters * invalid_share)))
        valid_target = voters - invalid
        drawn = simulate_ballot(record['votes'], e26_names, rng, alpha)
        drawn = _rescale(drawn, valid_target)
        out_rows.append((station, voters, invalid, valid_target, drawn))

    # The cap at 97% can leave the national rate a little short. Spread the
    # missing voters across boxes that still have room.
    voters_now = sum(voters for _, voters, _, _, _ in out_rows)
    target_voters = int(round(eligible_total * TARGET_TURNOUT))
    gap = target_voters - voters_now
    if gap > 0:
        room = []
        for i, (station, voters, _, _, _) in enumerate(out_rows):
            space = int(station['eligible'] * 0.97) - voters
            if space > 0:
                room.append((space, i))
        room.sort(reverse=True)
        for space, i in room:
            if gap <= 0:
                break
            add = min(space, gap)
            station, voters, invalid, valid_target, drawn = out_rows[i]
            invalid_share = invalid / voters if voters else 0.008
            voters += add
            invalid = min(voters, int(round(voters * invalid_share)))
            valid_target = voters - invalid
            drawn = _rescale(drawn, valid_target)
            out_rows[i] = (station, voters, invalid, valid_target, drawn)
            gap -= add

    columns = ['סמל ועדה', 'ברזל', 'שם ישוב', 'סמל ישוב', 'קלפי', 'ריכוז', 'שופט',
               'בזב', 'מצביעים', 'פסולים', 'כשרים']
    columns += [sym for sym, _ in E26_PARTIES.items()]
    columns += [sym for sym, _ in E26_TINY]
    records = []
    for station, voters, invalid, valid_target, drawn in out_rows:
        row = {
            'סמל ועדה': station['committee'],
            'ברזל': station['serial'],
            'שם ישוב': station['name'],
            'סמל ישוב': station['code'],
            'קלפי': station['ballot'],
            'ריכוז': station['cluster'],
            'שופט': 0,
            'בזב': station['eligible'],
            'מצביעים': voters,
            'פסולים': invalid,
            'כשרים': valid_target,
        }
        for sym, (name, _) in E26_PARTIES.items():
            row[sym] = drawn.get(name, 0)
        for sym, _ in E26_TINY:
            row[sym] = 0
        records.append(row)
    out_df = pd.DataFrame.from_records(records, columns=columns)
    out_df.to_csv('ballot26.csv', index=False, encoding='utf-8-sig')

    eligible_total = int(out_df['בזב'].sum())
    voter_total = int(out_df['מצביעים'].sum())
    valid_total = int(out_df['כשרים'].sum())
    print(f"\nOutput: ballot26.csv")
    print(f"Rows: {len(out_df):,}")
    print(f"Eligible: {eligible_total:,}")
    print(f"Voters: {voter_total:,}  turnout {voter_total / eligible_total:.1%}")
    print(f"Valid: {valid_total:,}")

    print(f"\nE26 Party Totals:")
    print(f"{'Symbol':<6} {'Party':<20} {'Votes':>12} {'%':>7}")
    print("-" * 48)
    for sym, (name, _) in E26_PARTIES.items():
        votes = int(out_df[sym].sum())
        pct = votes / valid_total * 100 if valid_total else 0
        print(f"{sym:<6} {name:<20} {votes:>12,} {pct:>6.1f}%")

    vote_map = {name: int(out_df[sym].sum()) for sym, (name, _) in E26_PARTIES.items()}
    seats, passed, thresh = bader_ofer(vote_map, agreements=SURPLUS_AGREEMENTS)
    print(f"\nBader-Ofer (threshold {thresh:,.0f}):")
    for name, target in TARGET_SEATS.items():
        got = seats.get(name, 0)
        print(f"  {name:<22} {got:>3} seats  (target {target}{'' if got == target else f', Δ{got - target:+d}'})")


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
