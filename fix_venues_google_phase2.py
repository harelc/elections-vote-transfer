#!/usr/bin/env python3
"""
Phase 2: Fix remaining venue locations using Google Places API.
Targets cities with < 100 missing stations (not covered by phase 1).
Also re-applies Ramla fix for stations misplaced in Modi'in.
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

ISRAEL_BOUNDS = {'min_lat': 29.5, 'max_lat': 33.3, 'min_lng': 34.2, 'max_lng': 35.9}

# Process cities with 20+ missing stations (phase 1 covered 100+)
MIN_MISSING = 20


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
        params['radius'] = 10000

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        time.sleep(0.1)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data.get('status') not in ('OK', 'ZERO_RESULTS'):
            print(f"    API error: {data.get('status')} - {data.get('error_message', '')}", flush=True)
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
        print(f"    Error: {e}", flush=True)
        return []


def search_venue(venue_name, settlement, settlement_coords, cache):
    query = f"{venue_name}, {settlement}, ישראל"
    results = google_text_search(query, location_bias=settlement_coords, cache=cache)

    if results:
        settlement_clean = settlement.replace('-', ' ').replace('  ', ' ').strip()
        for r in results:
            addr = r.get('address', '')
            if settlement_clean in addr or settlement in addr:
                return r
        return results[0]

    return None


def fix_ramla_modiin(stations):
    """Fix Ramla stations that were misplaced in Modi'in."""
    fixes = {
        'בי"ס יסודי קשת': (31.914183, 34.872099, 'בי"ס יסודי קשת'),
        'בי"ס אריאל - ב': (31.935089, 34.861995, 'בי"ס אריאל'),
    }
    fixed = 0
    for key, s in stations.items():
        if s.get('settlement') == 'רמלה' and s.get('lng', 0) > 34.95:
            loc = s.get('location', '')
            if loc in fixes:
                lat, lng, name = fixes[loc]
                s['lat'] = lat
                s['lng'] = lng
                s['source'] = 'google_venue'
                s['google_name'] = name
                fixed += 1
    print(f"Ramla/Modi'in fix: {fixed} stations corrected", flush=True)
    return fixed


def main():
    print("=== Fix Venues Phase 2 (Google Places API) ===\n", flush=True)

    cache = load_cache()
    print(f"Cache: {len(cache)} entries", flush=True)

    with open(COORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = data['stations']

    # First, re-apply Ramla fix
    fix_ramla_modiin(stations)

    # Find settlement-level stations grouped by city
    by_city = defaultdict(list)
    for key, s in stations.items():
        if s.get('source') == 'settlement':
            settlement = s.get('settlement', '')
            location = s.get('location', '')
            if location and settlement:
                by_city[settlement].append((key, location))

    # Filter to mid-size cities (phase 1 already did >= 100)
    target_cities = {city: venues for city, venues in by_city.items()
                     if len(venues) >= MIN_MISSING}
    print(f"Target cities (>={MIN_MISSING} missing): {len(target_cities)}", flush=True)

    # Get settlement coordinates for location bias
    settlement_coords = {}
    for key, s in stations.items():
        city = s.get('settlement', '')
        if city in target_cities and s.get('lat') and s.get('source') in ('settlement', 'venue', 'google_venue'):
            if city not in settlement_coords:
                settlement_coords[city] = (s['lat'], s['lng'])

    total_fixed = 0
    total_queries = 0
    total_cached = 0

    for city in sorted(target_cities, key=lambda c: -len(target_cities[c])):
        venues = target_cities[city]
        coords = settlement_coords.get(city)

        unique_venues = {}
        for key, location in venues:
            if location not in unique_venues:
                unique_venues[location] = []
            unique_venues[location].append(key)

        cached = sum(1 for v in unique_venues if f"google:{v}, {city}, ישראל" in cache)
        uncached = len(unique_venues) - cached

        if uncached == 0:
            # All cached, still apply results
            pass
        else:
            print(f"\n{city}: {len(venues)} stations, {len(unique_venues)} unique venues "
                  f"({cached} cached, {uncached} to query)", flush=True)

        city_fixed = 0
        for venue_name, station_keys in unique_venues.items():
            was_cached = f"google:{venue_name}, {city}, ישראל" in cache
            result = search_venue(venue_name, city, coords, cache)

            if not was_cached:
                total_queries += 1
            else:
                total_cached += 1

            if result:
                lat = round(result['lat'], 6)
                lng = round(result['lng'], 6)
                for key in station_keys:
                    stations[key]['lat'] = lat
                    stations[key]['lng'] = lng
                    stations[key]['source'] = 'google_venue'
                    stations[key]['google_name'] = result['name']
                city_fixed += len(station_keys)

        total_fixed += city_fixed
        if uncached > 0:
            print(f"  -> Fixed {city_fixed}/{len(venues)} stations", flush=True)

        # Save incrementally
        data['stations'] = stations
        with open(COORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}", flush=True)
    print(f"Total fixed: {total_fixed} stations", flush=True)
    print(f"New API queries: {total_queries}", flush=True)
    print(f"From cache: {total_cached}", flush=True)
    print(f"Estimated cost: ${total_queries * 0.032:.2f}", flush=True)
    print(f"Total cache entries: {len(cache)}", flush=True)
    print(f"Cumulative est. cost: ${len(cache) * 0.032:.2f} / $200 free tier", flush=True)
    print(f"Saved to {COORDS_FILE}", flush=True)


if __name__ == '__main__':
    main()
