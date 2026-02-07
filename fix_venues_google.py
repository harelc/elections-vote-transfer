#!/usr/bin/env python3
"""
Fix missing venue locations using Google Places API (Text Search).
Targets venues in big cities that only have settlement-level coordinates.
"""

import json
import os
import time
import urllib.request
import urllib.parse
from collections import defaultdict

COORDS_FILE = 'site/data/station_coordinates.json'
GOOGLE_CACHE_FILE = 'google_places_cache.json'
API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
if not API_KEY:
    raise SystemExit("Set GOOGLE_MAPS_API_KEY environment variable")

# Israel bounding box
ISRAEL_BOUNDS = {'min_lat': 29.5, 'max_lat': 33.3, 'min_lng': 34.2, 'max_lng': 35.9}

# Minimum missing stations to process a city
MIN_MISSING = 100


def load_cache():
    if os.path.exists(GOOGLE_CACHE_FILE):
        with open(GOOGLE_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(GOOGLE_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def is_in_israel(lat, lng):
    return (ISRAEL_BOUNDS['min_lat'] <= lat <= ISRAEL_BOUNDS['max_lat'] and
            ISRAEL_BOUNDS['min_lng'] <= lng <= ISRAEL_BOUNDS['max_lng'])


def google_text_search(query, location_bias=None, cache=None):
    """Search Google Places API (legacy text search)."""
    cache_key = f"google:{query}"
    if cache and cache_key in cache:
        return cache[cache_key]

    params = {
        'query': query,
        'key': API_KEY,
        'language': 'he',
        'region': 'il',
    }
    if location_bias:
        params['location'] = f"{location_bias[0]},{location_bias[1]}"
        params['radius'] = 10000  # 10km

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        time.sleep(0.1)  # Google allows more QPS than Nominatim

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data.get('status') not in ('OK', 'ZERO_RESULTS'):
            print(f"    API error: {data.get('status')} - {data.get('error_message', '')}")
            return []

        results = []
        for r in data.get('results', []):
            loc = r.get('geometry', {}).get('location', {})
            lat, lng = loc.get('lat', 0), loc.get('lng', 0)
            if is_in_israel(lat, lng):
                results.append({
                    'lat': lat,
                    'lng': lng,
                    'name': r.get('name', ''),
                    'address': r.get('formatted_address', ''),
                    'types': r.get('types', []),
                })

        if cache is not None:
            cache[cache_key] = results
            save_cache(cache)

        return results

    except Exception as e:
        print(f"    Error: {e}")
        return []


def search_venue(venue_name, settlement, settlement_coords, cache):
    """Search for a venue in a settlement using Google Places."""
    # Try full name first
    query = f"{venue_name}, {settlement}, ישראל"
    results = google_text_search(query, location_bias=settlement_coords, cache=cache)

    if results:
        # Prefer results that are in the right city (check address contains settlement)
        settlement_clean = settlement.replace('-', ' ').replace('  ', ' ').strip()
        for r in results:
            addr = r.get('address', '')
            if settlement_clean in addr or settlement in addr:
                return r
        # If none match by address, return first result (trust the location bias)
        return results[0]

    return None


def main():
    print("=== Fix Venues with Google Places API ===\n")

    cache = load_cache()
    print(f"Cache: {len(cache)} entries")

    with open(COORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = data['stations']

    # Find settlement-level stations grouped by city
    by_city = defaultdict(list)
    for key, s in stations.items():
        if s.get('source') == 'settlement':
            settlement = s.get('settlement', '')
            location = s.get('location', '')
            if location and settlement:
                by_city[settlement].append((key, location))

    # Filter to big cities
    big_cities = {city: venues for city, venues in by_city.items() if len(venues) >= MIN_MISSING}
    print(f"Big cities (>={MIN_MISSING} missing): {len(big_cities)}")

    # Get settlement coordinates for location bias
    settlement_coords = {}
    for key, s in stations.items():
        city = s.get('settlement', '')
        if city in big_cities and s.get('lat') and s.get('source') in ('settlement', 'venue'):
            if city not in settlement_coords:
                settlement_coords[city] = (s['lat'], s['lng'])

    total_fixed = 0
    total_queries = 0
    total_already_cached = 0

    for city in sorted(big_cities, key=lambda c: -len(big_cities[c])):
        venues = big_cities[city]
        coords = settlement_coords.get(city)

        # Deduplicate venue names
        unique_venues = {}
        for key, location in venues:
            if location not in unique_venues:
                unique_venues[location] = []
            unique_venues[location].append(key)

        # Check how many are already cached
        cached = sum(1 for v in unique_venues if f"google:{v}, {city}, ישראל" in cache)
        uncached = len(unique_venues) - cached

        print(f"\n{city}: {len(venues)} stations, {len(unique_venues)} unique venues "
              f"({cached} cached, {uncached} to query)")

        city_fixed = 0

        for venue_name, station_keys in unique_venues.items():
            was_cached = f"google:{venue_name}, {city}, ישראל" in cache
            result = search_venue(venue_name, city, coords, cache)

            if not was_cached:
                total_queries += 1
            else:
                total_already_cached += 1

            if result:
                lat = round(result['lat'], 6)
                lng = round(result['lng'], 6)
                for key in station_keys:
                    stations[key]['lat'] = lat
                    stations[key]['lng'] = lng
                    stations[key]['source'] = 'google_venue'
                    stations[key]['google_name'] = result['name']
                city_fixed += len(station_keys)
            # else: leave as settlement-level

        total_fixed += city_fixed
        print(f"  -> Fixed {city_fixed}/{len(venues)} stations")

        # Save incrementally
        data['stations'] = stations
        with open(COORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Total fixed: {total_fixed} stations")
    print(f"New API queries: {total_queries}")
    print(f"From cache: {total_already_cached}")
    print(f"Estimated cost: ${total_queries * 0.032:.2f}")
    print(f"Saved to {COORDS_FILE}")


if __name__ == '__main__':
    main()
