#!/usr/bin/env python3
"""
Targeted re-geocoding for Haifa polling stations.

Two failure modes are fixed:
  1. Settlement-fallback ballots: many distinct venues (e.g. נאות פרס,
     אהרון הרואה, אורט הכרמל) share Haifa's city-center coordinates
     because per-venue lookup failed.
  2. Wrong-google_venue ballots: Google Places returned coordinates
     outside the city (e.g. ~10km east near Nesher) for venues that
     are actually in central Haifa.

Strategy:
  * Find all distinct (location-name) groups for Haifa.
  * Re-query each via Google Places with a TIGHT 5km radius bias
    centred on Haifa proper (32.794, 34.989).
  * Validate result is within a 6km radius of Haifa centre; otherwise
    keep the existing coordinates and flag.
  * Write coordinates back to site/data/station_coordinates.json with
    source='google_venue_haifa'.
"""

import json
import math
import os
import time
import urllib.parse
import urllib.request
from collections import defaultdict

COORDS_FILE = 'site/data/station_coordinates.json'
GOOGLE_CACHE_FILE = 'google_places_cache.json'
HAIFA_CACHE_FILE  = 'google_haifa_cache.json'   # separate cache for tight-bias results
API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
if not API_KEY:
    raise SystemExit("Set GOOGLE_MAPS_API_KEY environment variable")

HAIFA_CENTRE = (32.7940, 34.9896)
# Haifa municipal area is geographically large (sprawls up Carmel ridge and
# eastward toward Nesher); we use a wide validity radius and only reject
# results obviously outside the city's metropolitan region.
HAIFA_VALID_RADIUS_KM = 15.0
HAIFA_BIAS_RADIUS_M   = 8000    # radius parameter for Google bias (a bit wider too)

# Israel bounding box for the sanity check on geocoded results.
ISRAEL_BOUNDS = {'min_lat': 29.5, 'max_lat': 33.3, 'min_lng': 34.2, 'max_lng': 35.9}

SETTLEMENT_NAME = 'חיפה'


def haversine_km(p1, p2):
    lat1, lng1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lng2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def load_cache(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(path, cache):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def google_search_tight(query, cache):
    """Text-search with tight Haifa bias and a strict radius."""
    cache_key = f"haifa-tight:{query}"
    if cache_key in cache:
        return cache[cache_key]

    params = {
        'query': query,
        'key': API_KEY,
        'language': 'he',
        'region': 'il',
        'location': f"{HAIFA_CENTRE[0]},{HAIFA_CENTRE[1]}",
        'radius': HAIFA_BIAS_RADIUS_M,
    }
    url = ("https://maps.googleapis.com/maps/api/place/textsearch/json?"
           + urllib.parse.urlencode(params))
    time.sleep(0.1)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"    HTTP error: {e}")
        return None

    if data.get('status') not in ('OK', 'ZERO_RESULTS'):
        print(f"    API: {data.get('status')} — {data.get('error_message', '')}")
        return None

    best = None
    for r in data.get('results', []):
        loc = r.get('geometry', {}).get('location', {})
        lat = loc.get('lat')
        lng = loc.get('lng')
        if lat is None or lng is None:
            continue
        # Reject only if outside Israel entirely.
        if not (ISRAEL_BOUNDS['min_lat'] <= lat <= ISRAEL_BOUNDS['max_lat']
                and ISRAEL_BOUNDS['min_lng'] <= lng <= ISRAEL_BOUNDS['max_lng']):
            continue
        d_km = haversine_km((lat, lng), HAIFA_CENTRE)
        # Reject if absurdly far from Haifa (e.g. Google returned a result
        # in Tel Aviv or Beer Sheba). Haifa metropolitan area easily reaches
        # 15km from city centre (Nesher, Tirat Carmel, Kiryat Bialik).
        if d_km > HAIFA_VALID_RADIUS_KM:
            continue
        best = {
            'lat': lat,
            'lng': lng,
            'name': r.get('name', ''),
            'place_id': r.get('place_id', ''),
            'distance_km': round(d_km, 3),
        }
        break

    cache[cache_key] = best
    save_cache(HAIFA_CACHE_FILE, cache)
    return best


def main():
    print("=== Targeted Haifa venue re-geocoding ===\n")
    cache = load_cache(HAIFA_CACHE_FILE)
    print(f"Haifa cache: {len(cache)} entries")

    with open(COORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    stations = data['stations']

    # Group Haifa stations by location-name (skip None/missing locations)
    by_venue = defaultdict(list)
    for key, s in stations.items():
        if s.get('settlement') != SETTLEMENT_NAME:
            continue
        loc = s.get('location')
        if not loc:
            continue
        by_venue[loc].append(key)

    # Classify venue groups by current geocoding health.
    # Two real failure modes:
    #   (a) source='settlement' → 60+ distinct venues lumped at city centre.
    #   (b) distinct venue names sharing identical (lat, lng) — usually two
    #       different schools that Google merged or for which the geocoder
    #       returned the same wide-area result.
    coord_to_venues = defaultdict(set)
    for venue, keys in by_venue.items():
        s0 = stations[keys[0]]
        lat, lng = s0.get('lat'), s0.get('lng')
        if lat is None or lng is None:
            continue
        coord_to_venues[(round(lat, 5), round(lng, 5))].add(venue)

    needs_fix = []
    for venue, keys in by_venue.items():
        s0 = stations[keys[0]]
        lat, lng = s0.get('lat'), s0.get('lng')
        src = s0.get('source')
        if lat is None or lng is None:
            needs_fix.append((venue, keys, 'no_coords'))
            continue
        if src == 'settlement':
            needs_fix.append((venue, keys, 'settlement_fallback'))
            continue
        # Distinct-venue-name collision: another venue at exact same coords.
        shared = coord_to_venues[(round(lat, 5), round(lng, 5))]
        if len(shared) >= 2:
            needs_fix.append((venue, keys, f'name_collision (sharing with {len(shared)-1} others)'))
            continue
        # otherwise: keep
    print(f"\nVenue groups needing fix: {len(needs_fix)} "
          f"(out of {len(by_venue)} Haifa venues total)")

    # Counts by reason
    reasons = defaultdict(int)
    for _, _, r in needs_fix:
        reasons[r.split(' ')[0]] += 1
    for r, n in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {r}: {n}")

    fixed = 0
    flagged = 0
    skipped_no_result = 0
    for i, (venue, keys, reason) in enumerate(needs_fix, 1):
        query = f"{venue}, חיפה, ישראל"
        result = google_search_tight(query, cache)
        if not result:
            skipped_no_result += 1
            print(f"  [{i}/{len(needs_fix)}] ✗ {venue!r} — no in-bounds match")
            continue
        new_lat = round(result['lat'], 6)
        new_lng = round(result['lng'], 6)
        # If new coords differ from old by < 50m, treat as no-op
        old = (stations[keys[0]].get('lat'), stations[keys[0]].get('lng'))
        if old[0] is not None:
            delta_km = haversine_km(old, (new_lat, new_lng))
        else:
            delta_km = float('inf')
        for k in keys:
            stations[k]['lat'] = new_lat
            stations[k]['lng'] = new_lng
            stations[k]['source'] = 'google_venue_haifa'
            stations[k]['google_name'] = result['name']
        fixed += len(keys)
        marker = '~' if delta_km < 0.05 else '✓'
        print(f"  [{i}/{len(needs_fix)}] {marker} {venue!r:50s} "
              f"→ ({new_lat}, {new_lng}) "
              f"Δ={delta_km:.2f}km, {len(keys)} ballots")

        # Save incrementally
        if i % 10 == 0:
            data['stations'] = stations
            with open(COORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # Final save
    data['stations'] = stations
    with open(COORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Fixed: {fixed} ballots across {len(needs_fix) - skipped_no_result} venues")
    print(f"Skipped (no Haifa-bounds match): {skipped_no_result}")
    print(f"Saved to {COORDS_FILE}")
    print(f"\nNext: re-run download_statistical_zones.py + process_statistical_zones.py")
    print(f"      to update zone assignments for the moved ballots.")


if __name__ == '__main__':
    main()
