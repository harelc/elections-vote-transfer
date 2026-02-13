#!/usr/bin/env python3
"""
Download historical Knesset ballot data (K16-K20) from data.gov.il CKAN API.
Normalizes column names to match the existing ballot CSV format.
"""

import csv
import json
import sys
import time
import urllib.request

RESOURCES = {
    '16': {
        'resource_id': '498b48e9-5af6-474d-b7a4-5ac1e21d3a08',
        'total': 7886,
        'ballot_field': 'סמל קלפי',
        'eligible_field': 'בוחרים',
        'settlement_code_field': 'סמל ישוב',
        'needs_settlement_name_first': False,
    },
    '17': {
        'resource_id': '70f8bc93-8d98-4c20-ad7c-768af713f1c5',
        'total': 8426,
        'ballot_field': 'מספר קלפי',  # encodes settlement in first digits
        'eligible_field': None,  # missing!
        'settlement_code_field': None,  # missing! need to derive from ballot#
        'needs_settlement_name_first': False,
    },
    '18': {
        'resource_id': '840edb33-90ac-4176-8ad9-4cdcb8e5caa5',
        'total': 9264,
        'ballot_field': 'סמל קלפי',
        'eligible_field': "בז''ב",
        'settlement_code_field': 'סמל ישוב',
        'needs_settlement_name_first': False,
    },
    '19': {
        'resource_id': '432d3185-545a-41d9-8c72-d10ee515919c',
        'total': 10109,
        'ballot_field': 'מספר קלפי',
        'eligible_field': 'בזב',
        'settlement_code_field': 'סמל ישוב',
        'needs_settlement_name_first': True,
    },
    '20': {
        'resource_id': 'c3db5581-f48d-45fc-b221-e7635e940c41',
        'total': 10414,
        'ballot_field': 'מספר קלפי',
        'eligible_field': 'בזב',
        'settlement_code_field': 'סמל ישוב',
        'needs_settlement_name_first': True,
    },
}

# Standard output column order
STD_FIELDS = ['שם ישוב', 'סמל ישוב', 'מספר קלפי', 'בזב', 'מצביעים', 'פסולים', 'כשרים']

# Fields to exclude from party columns
EXCLUDE_FIELDS = {'_id', 'שם ישוב', 'סמל ישוב', 'מספר קלפי', 'סמל קלפי',
                  'בזב', "בז''ב", 'בוחרים', 'מצביעים', 'פסולים', 'כשרים',
                  'כתובת', 'ת. עדכון', 'ריכוז', 'שופט', 'סמל ועדה', 'ברזל'}


def fetch_all_records(resource_id, total):
    """Fetch all records from a CKAN datastore resource."""
    records = []
    limit = 500
    offset = 0

    while offset < total:
        url = f'https://data.gov.il/api/3/action/datastore_search?resource_id={resource_id}&limit={limit}&offset={offset}'
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    data = json.loads(resp.read())
                batch = data['result']['records']
                records.extend(batch)
                break
            except Exception as e:
                if attempt == 2:
                    print(f'  FAILED at offset {offset}: {e}')
                    raise
                time.sleep(2)

        offset += limit
        sys.stdout.write(f'\r  Fetched {len(records)}/{total} records')
        sys.stdout.flush()
        time.sleep(0.1)  # be polite to API

    print()
    return records


def normalize_record(rec, config, fields):
    """Normalize a record to the standard column format."""
    out = {}

    # Settlement name
    out['שם ישוב'] = str(rec.get('שם ישוב', '')).strip()

    # Settlement code
    code_field = config['settlement_code_field']
    if code_field:
        val = rec.get(code_field, '')
        # Handle float codes like "967.0"
        try:
            out['סמל ישוב'] = str(int(float(val)))
        except (ValueError, TypeError):
            out['סמל ישוב'] = str(val)
    else:
        out['סמל ישוב'] = ''

    # Ballot number
    ballot_field = config['ballot_field']
    val = rec.get(ballot_field, '')
    try:
        # Remove .0 from float values
        out['מספר קלפי'] = str(int(float(val)))
    except (ValueError, TypeError):
        out['מספר קלפי'] = str(val)

    # Eligible voters
    eligible_field = config['eligible_field']
    if eligible_field:
        out['בזב'] = rec.get(eligible_field, 0) or 0
    else:
        out['בזב'] = 0

    # Voters, invalid, valid
    out['מצביעים'] = rec.get('מצביעים', 0) or 0
    out['פסולים'] = rec.get('פסולים', 0) or 0
    out['כשרים'] = rec.get('כשרים', 0) or 0

    # Party columns
    for f in fields:
        if f not in EXCLUDE_FIELDS:
            out[f] = rec.get(f, 0) or 0

    return out


def download_election(kid):
    """Download and save ballot data for one election."""
    config = RESOURCES[kid]
    print(f'\n=== Downloading Knesset {kid} ===')

    records = fetch_all_records(config['resource_id'], config['total'])
    if not records:
        print(f'  No records fetched!')
        return

    # Get all field names from the data
    all_fields = list(records[0].keys())
    party_fields = [f for f in all_fields if f not in EXCLUDE_FIELDS]

    print(f'  Party columns ({len(party_fields)}): {party_fields}')

    # Normalize all records
    rows = []
    for rec in records:
        row = normalize_record(rec, config, all_fields)
        rows.append(row)

    # Filter out special rows (settlement code 0 = double envelopes etc.)
    rows = [r for r in rows if r['סמל ישוב'] not in ('0', '', '0.0')]

    # Output columns: standard fields + party symbols
    out_columns = STD_FIELDS + party_fields

    outfile = f'ballot{kid}.csv'
    with open(outfile, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f'  Saved {len(rows)} rows to {outfile}')
    print(f'  Columns: {out_columns}')


def main():
    elections = sys.argv[1:] if len(sys.argv) > 1 else ['16', '17', '18', '19', '20']
    for kid in elections:
        if kid in RESOURCES:
            download_election(kid)
        else:
            print(f'Unknown election: {kid}')


if __name__ == '__main__':
    main()
