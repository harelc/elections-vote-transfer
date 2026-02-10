#!/usr/bin/env python3
"""
One-shot script to normalize settlement names in tsne_*.json files.
Avoids re-running the expensive t-SNE computation.
Uses the same normalize_name() logic as generate_map_data.py.
"""

import json
import glob
import os


NAME_OVERRIDES = {
    'גולס': "ג'וליס",
    'גוליס': "ג'וליס",
}


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
    normalized = NAME_OVERRIDES.get(normalized, normalized)
    return normalized


def main():
    pattern = os.path.join('site', 'data', 'tsne_*.json')
    files = sorted(glob.glob(pattern))
    if not files:
        print("No tsne_*.json files found in site/data/")
        return

    for filepath in files:
        print(f"Processing {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        changed = 0
        for station in data.get('stations', []):
            old = station.get('n', '')
            if old:
                new = normalize_name(old)
                if new != old:
                    station['n'] = new
                    changed += 1

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

        print(f"  Updated {changed} station names")

    print("Done!")


if __name__ == '__main__':
    main()
