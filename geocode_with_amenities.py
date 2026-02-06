#!/usr/bin/env python3
"""
Geocode ballot station venues using OSM Nominatim with structured amenity queries.

Uses amenity=school, amenity=community_centre, etc. for better results.
Rate limited to 1 request/second per Nominatim policy.
"""

import json
import os
import time
import re
import urllib.request
import urllib.parse
from collections import defaultdict
from difflib import SequenceMatcher

SITE_DATA_DIR = 'site/data'
OUTPUT_FILE = os.path.join(SITE_DATA_DIR, 'station_coordinates.json')
CACHE_FILE = 'nominatim_cache.json'
ELECTIONS = ['21', '22', '23', '24', '25']

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'ElectionsVoteTransfer/1.0 (https://github.com/harelc/elections-vote-transfer)'

ISRAEL_BOUNDS = {'min_lat': 29.5, 'max_lat': 33.3, 'min_lng': 34.2, 'max_lng': 35.9}

# Map our venue types to OSM amenity tags
VENUE_TO_AMENITY = {
    'school': 'school',
    'community_center': 'community_centre',
    'kindergarten': 'kindergarten',
    'synagogue': 'place_of_worship',
    'club': None,  # No direct amenity, use q search
    'hall': None,
}


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def is_in_israel(lat, lng):
    return (ISRAEL_BOUNDS['min_lat'] <= lat <= ISRAEL_BOUNDS['max_lat'] and
            ISRAEL_BOUNDS['min_lng'] <= lng <= ISRAEL_BOUNDS['max_lng'])


def nominatim_request(params, cache):
    """Make a Nominatim request with caching."""
    cache_key = json.dumps(params, sort_keys=True)

    if cache_key in cache:
        return cache[cache_key]

    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        time.sleep(1.1)

        with urllib.request.urlopen(req, timeout=15) as response:
            results = json.loads(response.read().decode('utf-8'))

        # Filter and simplify results
        valid = []
        for r in results:
            lat, lng = float(r['lat']), float(r['lon'])
            if is_in_israel(lat, lng):
                valid.append({
                    'lat': lat,
                    'lng': lng,
                    'name': r.get('display_name', '').split(',')[0],
                    'full_name': r.get('display_name', ''),
                    'type': r.get('type', ''),
                    'class': r.get('class', '')
                })

        cache[cache_key] = valid
        save_cache(cache)
        return valid

    except Exception as e:
        print(f"    Error: {e}")
        return []


def search_settlement(settlement, cache):
    """Get settlement coordinates - only accept actual places, not streets."""
    params = {
        'q': f'{settlement}, ישראל',
        'format': 'json',
        'limit': 10,
        'countrycodes': 'il',
    }
    results = nominatim_request(params, cache)

    # Valid place types (NOT streets/highways)
    place_types = {'city', 'town', 'village', 'hamlet', 'locality', 'neighbourhood',
                   'suburb', 'quarter', 'isolated_dwelling', 'farm', 'allotments'}

    # ONLY accept results that are actual places
    for r in results:
        # Must be class='place' with a valid place type
        if r.get('class') == 'place' and r.get('type') in place_types:
            return r
        # Also accept boundary/administrative results (regional councils etc)
        if r.get('class') == 'boundary' and r.get('type') == 'administrative':
            return r

    # If no place found, return None - do NOT fall back to streets
    return None


def search_amenities_viewbox(lat, lng, amenity_query, cache, radius_deg=0.05, limit=50):
    """Search for amenities in a viewbox around coordinates.

    Args:
        lat, lng: Center coordinates
        amenity_query: Search term like 'school', 'community center'
        radius_deg: Viewbox radius in degrees (~5km for 0.05)
    """
    # viewbox format: left,top,right,bottom (lng_min, lat_max, lng_max, lat_min)
    viewbox = f'{lng-radius_deg},{lat+radius_deg},{lng+radius_deg},{lat-radius_deg}'

    params = {
        'q': amenity_query,
        'format': 'json',
        'limit': limit,
        'countrycodes': 'il',
        'viewbox': viewbox,
        'bounded': 1,
    }
    return nominatim_request(params, cache)


def search_amenities(settlement, amenity, cache, limit=50):
    """Search for amenities in a settlement using structured query (fallback)."""
    params = {
        'city': settlement,
        'country': 'Israel',
        'format': 'json',
        'limit': limit,
        'amenity': amenity,
    }
    return nominatim_request(params, cache)


def search_query(query, cache, limit=30):
    """Fallback q-based search."""
    params = {
        'q': query,
        'format': 'json',
        'limit': limit,
        'countrycodes': 'il',
    }
    return nominatim_request(params, cache)


def search_venue_in_city(venue_name, city, cache, limit=10):
    """Search for a venue and filter results to those in the city."""
    # Extract core name (remove prefixes like בי"ס, בית ספר, etc.)
    core_name = extract_core_name(venue_name)
    # Search with core name + city
    query = f"{core_name}, {city}" if core_name else f"{venue_name}, {city}"
    params = {
        'q': query,
        'format': 'json',
        'limit': limit,
        'countrycodes': 'il',
    }
    results = nominatim_request(params, cache)

    # Filter: city name should appear as a separate part in the address
    # (not just as a street name prefix)
    city_clean = city.replace('-', ' ').replace('(', '').replace(')', '').strip()
    city_words = set(city_clean.split())

    valid_results = []
    for r in results:
        display = r.get('full_name', '')
        parts = [p.strip() for p in display.split(',')]

        # Check if city appears as its own part (not first part which is venue)
        for part in parts[1:]:
            part_clean = part.replace('-', ' ').strip()
            # Exact match or significant word overlap
            if part_clean == city_clean or part_clean == city:
                valid_results.append(r)
                break
            # For multi-word cities, check word overlap
            if len(city_words) > 1:
                part_words = set(part_clean.split())
                if len(city_words & part_words) >= len(city_words) - 1:
                    valid_results.append(r)
                    break

    # If no filtered results, return all (trust the search query)
    return valid_results if valid_results else results


def extract_core_name(name):
    """Extract core venue name, removing type prefixes."""
    prefixes = [
        r'בי"ס\s*', r'ביה"ס\s*', r'בית הספר\s*', r'בית ספר\s*',
        r'ממלכתי\s*', r'ממ"ד\s*', r'ממ"י\s*',
        r'יסודי\s*', r'תיכון\s*', r'חטיבת ביניים\s*',
        r'על יסודי\s*', r'תורני\s*', r'דתי\s*',
        r'מתנ"ס\s*', r'מתנס\s*', r'מרכז קהילתי\s*',
        r'מועדון\s*', r'בית העם\s*', r'אולם\s*',
        r'גן ילדים\s*', r'גן\s*',
    ]
    result = name
    for prefix in prefixes:
        result = re.sub(prefix, '', result, flags=re.IGNORECASE)
    return result.strip()


def match_score(our_name, osm_name):
    """Calculate match score between venue names."""
    our_core = extract_core_name(our_name)
    osm_core = extract_core_name(osm_name)

    if not our_core or not osm_core:
        return 0

    sim = SequenceMatcher(None, our_core.lower(), osm_core.lower()).ratio()

    # Bonus for substring match
    if our_core.lower() in osm_core.lower() or osm_core.lower() in our_core.lower():
        sim += 0.3

    return min(sim, 1.0)


def find_best_match(venue_name, osm_results, threshold=0.6):
    """Find best matching OSM result."""
    best = None
    best_score = 0

    for r in osm_results:
        score = match_score(venue_name, r['name'])
        if score > best_score:
            best_score = score
            best = r

    return best if best_score >= threshold else None


def get_venue_type(location):
    """Determine venue type from location string."""
    if not location:
        return None

    # Schools (most common)
    if 'בית ספר' in location or 'בי"ס' in location or 'ביה"ס' in location:
        return 'school'
    if 'תלמוד תורה' in location:
        return 'school'

    # Community centers
    if 'מתנ"ס' in location or 'מתנס' in location or 'מרכז קהילתי' in location:
        return 'community_center'

    # Kindergartens
    if 'גן ילדים' in location or location.startswith('גן '):
        return 'kindergarten'

    # Religious venues
    if 'בית כנסת' in location or 'ביכ"נ' in location:
        return 'synagogue'
    if 'ישיבה' in location or 'ישיבת' in location:
        return 'yeshiva'
    if 'כולל' in location:
        return 'yeshiva'

    # Clubs
    if 'מועדון' in location:
        return 'club'

    # Halls
    if 'אולם' in location or 'בית העם' in location:
        return 'hall'

    # Libraries
    if 'ספריה' in location or 'ספרייה' in location:
        return 'library'

    # Cultural centers
    if 'בית תרבות' in location:
        return 'community_center'

    return None


def extract_stations():
    """Extract all stations from tsne files."""
    stations = {}

    for eid in ELECTIONS:
        path = os.path.join(SITE_DATA_DIR, f'tsne_{eid}.json')
        if not os.path.exists(path):
            continue

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for s in data.get('stations', []):
            settlement = s.get('n') or s.get('settlement_name', '')
            ballot = s.get('b') or s.get('ballot_number', '')
            location = s.get('l') or ''

            key = f"{settlement}|{ballot}"
            if key not in stations:
                stations[key] = {
                    'settlement': settlement,
                    'ballot': ballot,
                    'location': location,
                }

    return stations


def main():
    import sys

    print("=== Geocoding with OSM Amenities ===\n", flush=True)

    cache = load_cache()
    print(f"Cache: {len(cache)} entries", flush=True)

    stations = extract_stations()
    print(f"Stations: {len(stations)}", flush=True)

    # Group by settlement
    by_settlement = defaultdict(list)
    for key, info in stations.items():
        by_settlement[info['settlement']].append((key, info))

    print(f"Settlements: {len(by_settlement)}", flush=True)

    # Process all settlements (א-ת)
    FILTER_LETTERS = 'אבגדהוזחטיכלמנסעפצקרשת'
    filtered_settlements = {k: v for k, v in by_settlement.items()
                           if k and k[0] in FILTER_LETTERS}
    print(f"Filtered to letters {FILTER_LETTERS}: {len(filtered_settlements)} settlements", flush=True)

    # Load existing results to skip already-processed settlements
    existing_results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_results = existing_data.get('stations', {})
        print(f"Existing results: {len(existing_results)} stations", flush=True)

    results = dict(existing_results)  # Start with existing
    stats = {'venue_match': 0, 'settlement_only': 0, 'not_found': 0}

    total = len(filtered_settlements)
    skipped = 0

    for i, (settlement, station_list) in enumerate(sorted(filtered_settlements.items())):
        # Skip if all stations already have venue-level coordinates
        all_have_venue = all(
            key in existing_results and existing_results[key].get('source') == 'venue'
            for key, _ in station_list
        )
        if all_have_venue:
            skipped += 1
            continue

        print(f"\n[{i+1}/{total}] {settlement} ({len(station_list)} stations)", flush=True)

        # 1. Get settlement coordinates
        settlement_coords = search_settlement(settlement, cache)

        if settlement_coords:
            print(f"  Settlement: {settlement_coords['lat']:.4f}, {settlement_coords['lng']:.4f}", flush=True)
        else:
            print(f"  Settlement NOT FOUND", flush=True)

        # Skip venue search for small settlements (15 or fewer stations)
        if len(station_list) <= 15:
            for key, info in station_list:
                if settlement_coords:
                    results[key] = {
                        'settlement': settlement,
                        'ballot': info['ballot'],
                        'location': info['location'],
                        'lat': round(settlement_coords['lat'], 6),
                        'lng': round(settlement_coords['lng'], 6),
                        'source': 'settlement'
                    }
                    stats['settlement_only'] += 1
                else:
                    results[key] = {
                        'settlement': settlement,
                        'ballot': info['ballot'],
                        'location': info['location'],
                        'lat': None,
                        'lng': None,
                        'source': 'not_found'
                    }
                    stats['not_found'] += 1
            continue

        # 2. Search for each unique venue directly by name + settlement
        venue_cache = {}  # Cache results for duplicate venue names in same settlement

        for key, info in station_list:
            venue_name = info['location']

            # Skip if no venue name
            if not venue_name:
                if settlement_coords:
                    results[key] = {
                        'settlement': settlement,
                        'ballot': info['ballot'],
                        'location': venue_name,
                        'lat': round(settlement_coords['lat'], 6),
                        'lng': round(settlement_coords['lng'], 6),
                        'source': 'settlement'
                    }
                    stats['settlement_only'] += 1
                else:
                    results[key] = {
                        'settlement': settlement,
                        'ballot': info['ballot'],
                        'location': venue_name,
                        'lat': None,
                        'lng': None,
                        'source': 'not_found'
                    }
                    stats['not_found'] += 1
                continue

            # Check venue cache first
            if venue_name in venue_cache:
                matched = venue_cache[venue_name]
            else:
                # Search for venue in city using structured query
                osm_results = search_venue_in_city(venue_name, settlement, cache, limit=5)

                # Find best match (require result to be in the right city)
                matched = find_best_match(venue_name, osm_results, threshold=0.4) if osm_results else None
                venue_cache[venue_name] = matched

            if matched:
                results[key] = {
                    'settlement': settlement,
                    'ballot': info['ballot'],
                    'location': venue_name,
                    'lat': round(matched['lat'], 6),
                    'lng': round(matched['lng'], 6),
                    'source': 'venue',
                    'osm_name': matched['name']
                }
                stats['venue_match'] += 1
            elif settlement_coords:
                results[key] = {
                    'settlement': settlement,
                    'ballot': info['ballot'],
                    'location': venue_name,
                    'lat': round(settlement_coords['lat'], 6),
                    'lng': round(settlement_coords['lng'], 6),
                    'source': 'settlement'
                }
                stats['settlement_only'] += 1
            else:
                results[key] = {
                    'settlement': settlement,
                    'ballot': info['ballot'],
                    'location': venue_name,
                    'lat': None,
                    'lng': None,
                    'source': 'not_found'
                }
                stats['not_found'] += 1

        # Print progress for this settlement
        venue_in_settlement = sum(1 for k, _ in station_list if results.get(k, {}).get('source') == 'venue')
        print(f"  -> {venue_in_settlement}/{len(station_list)} venues matched", flush=True)

        # Save after each settlement (incremental)
        output = {'stations': results, 'stats': stats}
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    # Final save
    output = {'stations': results, 'stats': stats}
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Results ===", flush=True)
    print(f"Skipped (already processed): {skipped} settlements", flush=True)
    print(f"Total: {len(results)}", flush=True)
    print(f"Venue matches: {stats['venue_match']} ({100*stats['venue_match']/len(results):.1f}%)", flush=True)
    print(f"Settlement only: {stats['settlement_only']} ({100*stats['settlement_only']/len(results):.1f}%)", flush=True)
    print(f"Not found: {stats['not_found']}", flush=True)
    print(f"\nOutput: {OUTPUT_FILE}", flush=True)
    print(f"Cache: {CACHE_FILE}", flush=True)


if __name__ == '__main__':
    main()
