#!/usr/bin/env python3
"""
Fix missing venue locations by querying Nominatim for specific venues.
Targets venues that only have settlement-level coordinates.
"""

import json
import time
import requests
from collections import defaultdict

COORDS_FILE = 'site/data/station_coordinates.json'

def nominatim_request(params):
    """Make a Nominatim API request with rate limiting."""
    url = 'https://nominatim.openstreetmap.org/search'
    headers = {'User-Agent': 'ElectionsVoteTransfer/1.0'}
    time.sleep(1.1)
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  Error: {e}")
    return []

def search_venue(venue_name, settlement):
    """Search for a venue in a settlement."""
    clean_name = venue_name
    for prefix in ['בי"ס', "בי״ס", 'ביה"ס', "ביה״ס", 'בית ספר', 'ביס']:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):].strip()

    # Remove common suffixes and clarifiers
    for suffix in ['- כניסה צפונית', '- כניסה דרומית', '- מבנה חדש', '- מבנה ישן']:
        clean_name = clean_name.replace(suffix, '').strip()

    parts = clean_name.split(' - ')
    short_name = parts[0].strip() if parts else clean_name

    # Also extract core name (remove ע"ש, ממ"ד etc.)
    core_name = clean_name
    for prefix in ["ע\"ש ", "ע״ש ", "ממ\"ד ", "ממ״ד ", "ממלכתי ", "תיכון ", "יסודי "]:
        core_name = core_name.replace(prefix, '')
    core_name = core_name.strip()

    queries = [
        f'{venue_name}, {settlement}, ישראל',
        f'{clean_name}, {settlement}, ישראל',
        f'{short_name}, {settlement}, ישראל',
        f'{core_name}, {settlement}, ישראל',
    ]

    for query in queries:
        params = {
            'q': query,
            'format': 'json',
            'limit': 5,
            'countrycodes': 'il',
        }
        results = nominatim_request(params)

        for r in results:
            rclass = r.get('class', '')
            rtype = r.get('type', '')
            if rclass == 'amenity' and rtype in ['school', 'community_centre', 'kindergarten',
                                                    'college', 'university', 'place_of_worship',
                                                    'social_facility', 'library', 'theatre',
                                                    'townhall', 'arts_centre']:
                return r
            if rclass == 'building' and rtype in ['school', 'civic', 'public', 'yes',
                                                    'synagogue', 'church', 'mosque']:
                return r
            if rclass == 'leisure' and rtype in ['sports_centre', 'sports_hall', 'stadium']:
                return r

        # Accept any amenity/building in second pass
        for r in results:
            rclass = r.get('class', '')
            if rclass in ['amenity', 'building', 'leisure']:
                return r

    return None

def main():
    with open(COORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = data['stations']

    # Find venues with only settlement-level coords
    missing = defaultdict(lambda: defaultdict(int))
    for key, sdata in stations.items():
        if sdata.get('source') == 'settlement':
            settlement = sdata.get('settlement', '')
            location = sdata.get('location', '')
            if location and settlement:
                missing[settlement][location] += 1

    all_venues = []
    for settlement, venues in missing.items():
        for venue, count in venues.items():
            all_venues.append((settlement, venue, count))
    all_venues.sort(key=lambda x: -x[2])

    print(f"Venues with settlement-only coords: {len(all_venues)}")
    print(f"Total stations affected: {sum(v[2] for v in all_venues)}")
    print(f"\nProcessing top 150 venues by station count:")
    print("-" * 80)

    fixed = 0
    fixes = {}

    for settlement, venue, count in all_venues[:150]:
        print(f"\n[{count}] {settlement} | {venue}")

        result = search_venue(venue, settlement)
        if result:
            lat = float(result['lat'])
            lng = float(result['lon'])
            osm_name = result.get('display_name', '').split(',')[0]
            print(f"  ✓ Found: {lat:.5f}, {lng:.5f} - {osm_name}")
            fixes[(settlement, venue)] = (lat, lng, osm_name)
            fixed += 1
        else:
            print(f"  ✗ Not found")

    print(f"\n{'='*80}")
    print(f"Fixed {fixed}/{min(150, len(all_venues))} venues")

    if fixes:
        applied = 0
        for key, sdata in stations.items():
            settlement = sdata.get('settlement', '')
            location = sdata.get('location', '')
            if (settlement, location) in fixes:
                lat, lng, osm_name = fixes[(settlement, location)]
                sdata['lat'] = lat
                sdata['lng'] = lng
                sdata['source'] = 'venue'
                sdata['osm_name'] = osm_name
                applied += 1

        data['stations'] = stations
        with open(COORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Applied fixes to {applied} stations")
        print(f"Saved to {COORDS_FILE}")

if __name__ == '__main__':
    main()
