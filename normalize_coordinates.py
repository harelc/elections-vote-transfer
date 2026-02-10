#!/usr/bin/env python3
"""
One-shot script to normalize settlement names in station_coordinates.json.
Keys are 'settlement|ballot' — normalize the settlement part.
When keys collapse, keep the entry with coordinates (prefer google_venue > venue > settlement source).
"""

import json


SOURCE_PRIORITY = {'google_venue': 3, 'venue': 2, 'settlement': 1, 'not_found': 0}


def normalize_name(name):
    """Normalize settlement name — must match generate_map_data.py."""
    if not name:
        return name
    normalized = name.replace('-', ' ').replace('–', ' ')
    normalized = normalized.replace("'", '').replace('\u05f3', '')
    normalized = normalized.replace('"', '').replace('\u05f4', '')
    normalized = normalized.replace('(', ' ').replace(')', ' ')
    normalized = ' '.join(normalized.split())
    normalized = normalized.replace('יי', 'י')
    return normalized


def main():
    filepath = 'site/data/station_coordinates.json'
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = data.get('stations', {})
    new_stations = {}
    changed = 0
    merged = 0

    for key, info in stations.items():
        parts = key.split('|', 1)
        settlement = parts[0]
        ballot = parts[1] if len(parts) > 1 else ''

        new_settlement = normalize_name(settlement)
        new_key = new_settlement + '|' + ballot

        if new_settlement != settlement:
            changed += 1
            info['settlement'] = new_settlement

        if new_key in new_stations:
            # Merge: keep the one with better coordinates
            existing = new_stations[new_key]
            existing_priority = SOURCE_PRIORITY.get(existing.get('source', ''), 0)
            new_priority = SOURCE_PRIORITY.get(info.get('source', ''), 0)
            if new_priority > existing_priority:
                new_stations[new_key] = info
            merged += 1
        else:
            new_stations[new_key] = info

    data['stations'] = new_stations
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Normalized {changed} station keys")
    print(f"Merged {merged} duplicate keys")
    print(f"Total stations: {len(stations)} → {len(new_stations)}")


if __name__ == '__main__':
    main()
