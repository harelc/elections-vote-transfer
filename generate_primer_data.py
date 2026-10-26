"""Generate site/data/primer_25.json for primer.html (K25 intro).

Per-ballot distributions (ballot-size / turnout histograms, medians) come
from ballot25.csv. The national headline figures do NOT: ballot25.csv is
the per-ballot file as captured during the count (its last commit is the
"seventh results update" of election night) and it never picked up the
final tally — summing it gives 4,740,556 votes cast / 69.93% turnout,
against the CEC's final official 4,794,593 / 70.63%. Most of the gap is
double envelopes counted late (411,451 valid in the file vs 458,714 in
the final CEC results-by-locality file), the rest a handful of regular
ballots and corrections that only ever appeared in the national totals.

So the national totals and the per-party votes baked into the primer are
the CEC's final official figures (https://votes25.bechirot.gov.il/
nationalresults, fetched 2026-10-26), and only the shapes of the
per-ballot distributions are taken from the ballot file — a ~1% shortfall
spread over ~12,000 ballots does not move a histogram bin or a median in
any visible way.

Run:  venv/bin/python generate_primer_data.py
"""

import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).parent

# CEC final official national results, K25 (votes25.bechirot.gov.il/
# nationalresults). Eligible/voted/valid also match party_config.py.
OFFICIAL = {
    'eligible': 6_788_804,
    'voted': 4_794_593,
    'kosher': 4_764_742,
    'invalid': 29_851,
    'turnout_pct': 70.63,
    # Valid double-envelope ("outer envelope") votes in the final CEC
    # results-by-locality file (settlement 9999 row): 9.63% of valid votes.
    'double_kosher': 458_714,
}

# CEC final official valid votes per list, by ballot symbol (same page).
OFFICIAL_PARTY_VOTES = {
    'מחל': 1115336, 'פה': 847435, 'ט': 516470, 'כן': 432482, 'שס': 392964,
    'ג': 280194, 'ל': 213687, 'עם': 194047, 'ום': 178735, 'אמת': 175992,
    'מרצ': 150793, 'ד': 138617, 'ב': 56775, 'אצ': 15801, 'קץ': 14694,
    'יז': 13920, 'צ': 8800, 'ף': 1728, 'ק': 1618, 'ת': 1524, 'ני': 1354,
    'קנ': 1292, 'נק': 1215, 'י': 1157, 'קך': 1078, 'נץ': 1020, 'ץ': 988,
    'רז': 939, 'ך': 746, 'ז': 430, 'קי': 415, 'יק': 411, 'נז': 350,
    'נר': 334, 'זץ': 292, 'יץ': 262, 'נף': 255, 'ינ': 234, 'זך': 205,
    'זנ': 153,
}

THRESHOLD_PCT = 3.25


def _num(row, col):
    return int(float(row[col] or 0))


def _histogram(values, edges):
    counts = [0] * (len(edges) - 1)
    for v in values:
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1] or (i == len(edges) - 2 and v == edges[-1]):
                counts[i] += 1
                break
    return {'edges': edges, 'counts': counts}


def _percentile(values, pct):
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)


def main():
    with open(ROOT / 'ballot25.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        party_cols = reader.fieldnames[11:]
        rows = list(reader)

    assert set(party_cols) == set(OFFICIAL_PARTY_VOTES), (
        set(party_cols) ^ set(OFFICIAL_PARTY_VOTES))
    assert sum(OFFICIAL_PARTY_VOTES.values()) == OFFICIAL['kosher']

    regular = [r for r in rows if r['סמל ישוב'] != '9999']
    double = [r for r in rows if r['סמל ישוב'] == '9999']

    # Per-ballot distributions from the ballot file (see module docstring).
    eligible_per_ballot = [_num(r, 'בזב') for r in regular]
    turnout_per_ballot = [
        _num(r, 'מצביעים') / _num(r, 'בזב') * 100
        for r in regular if _num(r, 'בזב')
    ]

    # Party names/colours match the rest of the site (map_25.json); lists
    # with no map entry (the tiny ones) fall back to their ballot symbol.
    map25 = json.loads((ROOT / 'site/data/map_25.json').read_text(encoding='utf-8'))
    party_info = {p['symbol']: p for p in map25['parties']}

    total_valid = OFFICIAL['kosher']
    threshold_votes = int(total_valid * THRESHOLD_PCT / 100)
    parties = []
    for symbol, votes in OFFICIAL_PARTY_VOTES.items():
        share = votes / total_valid
        if share >= 0.10:
            bucket = 'big'
        elif votes >= threshold_votes:
            bucket = 'medium'
        elif share >= 0.005:
            bucket = 'small_below_threshold'
        else:
            bucket = 'tiny'
        info = party_info.get(symbol, {})
        parties.append({
            'symbol': symbol,
            'votes': votes,
            'bucket': bucket,
            'name': info.get('name', symbol),
            'color': info.get('color', '#64748b'),
        })
    parties.sort(key=lambda p: -p['votes'])

    data = {
        'totals': {
            'ballots_real': len(regular),
            'double_envelope_rows': len(double),
            'eligible': OFFICIAL['eligible'],
            'voted': OFFICIAL['voted'],
            'kosher': OFFICIAL['kosher'],
            'invalid': OFFICIAL['invalid'],
            'turnout_pct': OFFICIAL['turnout_pct'],
            'double_kosher': OFFICIAL['double_kosher'],
            'settlements': len({r['סמל ישוב'] for r in regular}),
            'parties_running': len(party_cols),
            'parties_passed_threshold': sum(
                1 for p in parties if p['votes'] >= threshold_votes),
            'threshold_votes': threshold_votes,
            'threshold_pct': THRESHOLD_PCT,
        },
        'ballot_size_histogram': _histogram(
            eligible_per_ballot, list(range(0, 880, 80))),
        'turnout_histogram': _histogram(
            turnout_per_ballot, [0, 30, 40, 50, 60, 70, 80, 90, 100]),
        'parties': parties,
        'total_valid': total_valid,
        'eligible_per_ballot_median': int(statistics.median(eligible_per_ballot)),
        'eligible_per_ballot_p10': int(_percentile(eligible_per_ballot, 10)),
        'eligible_per_ballot_p90': int(_percentile(eligible_per_ballot, 90)),
        'turnout_per_ballot_median': round(statistics.median(turnout_per_ballot), 1),
        'sources': {
            'totals_and_parties': 'CEC final official national results, '
                                  'https://votes25.bechirot.gov.il/nationalresults',
            'double_kosher': 'CEC final results-by-locality file, settlement 9999 row',
            'ballot_distributions': 'ballot25.csv (per-ballot file as captured '
                                    'during the count; ~1.1% below the final '
                                    'national tally — see generate_primer_data.py)',
        },
    }

    out = ROOT / 'site/data/primer_25.json'
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n',
                   encoding='utf-8')
    print(f'Wrote {out}')
    print(f"  official: {OFFICIAL['voted']:,} voted / {OFFICIAL['eligible']:,} "
          f"eligible = {OFFICIAL['turnout_pct']}%")


if __name__ == '__main__':
    main()
