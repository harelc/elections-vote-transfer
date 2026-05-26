#!/usr/bin/env python3
"""
Re-geocode polling-station venues using Nominatim (OSM).

Two failure modes addressed:
  (1) source == 'settlement' — many distinct venues stuck at the city
      centre fallback. Most common for cities with >50 ballots.
  (2) name_collision — distinct venue names sharing identical (lat, lng).
      Only flagged when ≥7 ballots share the cluster AND the names
      aren't string-similar (so legitimate "Wing A"/"Wing B" pairs
      are skipped).

Validation:
  Each Nominatim result is accepted only if within a city-specific
  radius of the city centre (taken from the existing settlement-level
  fallback coordinates). Default radius 20km; Haifa uses 15km because
  its sprawling metro is well-covered by that range.

Nominatim is the public OSM endpoint — free, rate-limited to 1 req/sec.
The cache (nominatim_cache.json) is reused across runs.
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from difflib import SequenceMatcher

COORDS_FILE = 'site/data/station_coordinates.json'
CACHE_FILE = 'nominatim_venue_cache.json'
USER_AGENT = 'kolot-nodedim-venue-fix/1.0 (harel.cain@gmail.com)'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

# Bounding box for Israel-only sanity
ISRAEL_BOUNDS = {'min_lat': 29.5, 'max_lat': 33.3, 'min_lng': 34.2, 'max_lng': 35.9}

# Per-city radius override (km). Default 20km.
CITY_RADIUS_KM = {
    'חיפה':        15.0,  # Haifa metro reaches ~15km incl. Nesher, Tirat Carmel
    'תל אביב יפו': 15.0,
    'ירושלים':     20.0,
}

DEFAULT_RADIUS_KM = 20.0
CLUSTER_MIN_BALLOTS = 7      # only investigate clusters with this many ballots
NAME_SIMILARITY_SKIP = 0.75  # skip name-collisions when names are this similar


def haversine_km(p1, p2):
    lat1, lng1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lng2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def nominatim_query(query, viewbox=None, cache=None):
    """Single Nominatim text search with optional viewbox bias."""
    params = {
        'q': query,
        'format': 'json',
        'limit': 5,
        'accept-language': 'he',
        'countrycodes': 'il',
    }
    if viewbox:
        # viewbox = (lng_min, lat_max, lng_max, lat_min)
        params['viewbox'] = ','.join(f'{x:.5f}' for x in viewbox)
        params['bounded'] = '1'
    cache_key = json.dumps(params, sort_keys=True, ensure_ascii=False)
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        time.sleep(1.1)  # Nominatim rate limit
        with urllib.request.urlopen(req, timeout=20) as resp:
            results = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"    Nominatim error: {e}", file=sys.stderr)
        return []
    out = []
    for r in results:
        try:
            lat, lng = float(r['lat']), float(r['lon'])
        except (KeyError, TypeError, ValueError):
            continue
        if not (ISRAEL_BOUNDS['min_lat'] <= lat <= ISRAEL_BOUNDS['max_lat']
                and ISRAEL_BOUNDS['min_lng'] <= lng <= ISRAEL_BOUNDS['max_lng']):
            continue
        out.append({
            'lat': lat, 'lng': lng,
            'display_name': r.get('display_name', ''),
            'osm_type': r.get('osm_type', ''),
            'osm_class': r.get('class', ''),
        })
    if cache is not None:
        cache[cache_key] = out
        save_cache(cache)
    return out


def search_venue(venue, city, city_centre, radius_km, cache):
    """Try a couple of query forms; return best-quality in-radius hit."""
    # viewbox approximating ~2*radius_km
    deg = radius_km / 111.0  # rough lat-degrees per km
    vb = (city_centre[1] - deg, city_centre[0] + deg,
          city_centre[1] + deg, city_centre[0] - deg)

    forms = [
        f'{venue}, {city}, ישראל',
        f'{venue}, {city}',
        f'{venue}',
    ]
    for query in forms:
        results = nominatim_query(query, viewbox=vb, cache=cache)
        for r in results:
            d_km = haversine_km((r['lat'], r['lng']), city_centre)
            if d_km <= radius_km:
                r = dict(r)
                r['distance_km'] = round(d_km, 3)
                r['query'] = query
                return r
    return None


def name_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() >= NAME_SIMILARITY_SKIP


def main():
    print("=== Nominatim venue re-geocoding ===\n")
    cache = load_cache()
    print(f"Cache: {len(cache)} entries\n")

    with open(COORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    stations = data['stations']

    # Find city centres (use settlement-fallback ballots' coords as the
    # canonical city centre, since the geocoding pipeline put them there).
    city_centre = {}
    for s in stations.values():
        if s.get('source') == 'settlement' and s.get('lat') is not None:
            city_centre.setdefault(s.get('settlement', ''), (s['lat'], s['lng']))
    # Fall back to any in-city ballot for cities without explicit fallback.
    for s in stations.values():
        city = s.get('settlement', '')
        if city and city not in city_centre and s.get('lat') is not None:
            city_centre[city] = (s['lat'], s['lng'])
    print(f"City centres known: {len(city_centre)}\n")

    # Group stations per (city, venue_name)
    by_city_venue = defaultdict(list)
    for k, v in stations.items():
        city = v.get('settlement', '')
        venue = v.get('location')
        if not city or not venue:
            continue
        by_city_venue[(city, venue)].append(k)

    # Also build per-city coord clusters for collision detection
    coord_clusters = defaultdict(lambda: defaultdict(set))  # city → coord → set(venues)
    for (city, venue), keys in by_city_venue.items():
        c = stations[keys[0]]
        if c.get('lat') is None:
            continue
        coord_clusters[city][(round(c['lat'], 5), round(c['lng'], 5))].add(venue)

    # Build the to-fix list
    needs_fix = []   # (city, venue, [keys], reason)
    for (city, venue), keys in by_city_venue.items():
        s0 = stations[keys[0]]
        src = s0.get('source')
        lat, lng = s0.get('lat'), s0.get('lng')
        if src == 'settlement':
            needs_fix.append((city, venue, keys, 'settlement_fallback'))
            continue
        if lat is None:
            needs_fix.append((city, venue, keys, 'no_coords'))
            continue
        cluster = coord_clusters[city].get((round(lat, 5), round(lng, 5)), set())
        if len(cluster) >= 2:
            # cluster size in BALLOTS — only flag if ≥CLUSTER_MIN_BALLOTS
            total_ballots = sum(len(by_city_venue[(city, v)]) for v in cluster)
            if total_ballots < CLUSTER_MIN_BALLOTS:
                continue
            # skip if names are nearly-identical (likely same place)
            others = [v for v in cluster if v != venue]
            if any(name_similar(venue, o) for o in others):
                continue
            needs_fix.append((city, venue, keys, f'collision_in_cluster_of_{total_ballots}'))

    # Group counts
    print(f"Total venues needing fix: {len(needs_fix)}")
    from collections import Counter
    by_reason = Counter(r.split('_')[0] for *_, r in needs_fix)
    for reason, n in by_reason.most_common():
        print(f"  {reason}: {n}")
    print()

    # Sort: settlement-fallback first (larger fix impact), then collisions.
    # Within each: most-ballots first so big cities get fixed first.
    def sort_key(item):
        city, venue, keys, reason = item
        kind = 0 if 'settlement' in reason else 1
        return (kind, -len(keys))
    needs_fix.sort(key=sort_key)

    # Optional: limit to top N for a partial run
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        needs_fix = needs_fix[:int(sys.argv[2])]
        print(f"limited to top {len(needs_fix)} venues this run\n")

    fixed_venues = 0
    fixed_ballots = 0
    no_result = 0
    t0 = time.time()
    for i, (city, venue, keys, reason) in enumerate(needs_fix, 1):
        centre = city_centre.get(city)
        if centre is None:
            print(f"  [{i}/{len(needs_fix)}] ✗ {city} no city centre — skip")
            continue
        radius = CITY_RADIUS_KM.get(city, DEFAULT_RADIUS_KM)
        result = search_venue(venue, city, centre, radius, cache)
        if not result:
            no_result += 1
            elapsed = (time.time() - t0) / 60.0
            print(f"  [{i:4d}/{len(needs_fix)}] ✗ {city:18s} {venue[:38]!r:40s} "
                  f"({reason}, {len(keys)} ballots, {elapsed:.1f}m)")
            continue
        new_lat = round(result['lat'], 6)
        new_lng = round(result['lng'], 6)
        for k in keys:
            stations[k]['lat'] = new_lat
            stations[k]['lng'] = new_lng
            stations[k]['source'] = 'nominatim_venue'
            stations[k]['osm_name'] = result['display_name'].split(',')[0]
        fixed_venues += 1
        fixed_ballots += len(keys)
        elapsed = (time.time() - t0) / 60.0
        print(f"  [{i:4d}/{len(needs_fix)}] ✓ {city:18s} {venue[:38]!r:40s} "
              f"→ ({new_lat}, {new_lng}) {result['distance_km']:.1f}km "
              f"({len(keys)} ballots, {elapsed:.1f}m)")

        # Save every 20 venues
        if i % 20 == 0:
            data['stations'] = stations
            with open(COORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # Final save
    data['stations'] = stations
    with open(COORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Fixed: {fixed_venues} venues, {fixed_ballots} ballots")
    print(f"No Nominatim result: {no_result} venues")
    print(f"Total time: {(time.time() - t0)/60:.1f} min")
    print(f"Saved to {COORDS_FILE}")
    print(f"\nNext: re-run download_statistical_zones.py + process_statistical_zones.py")
    print(f"      to update zone assignments for moved ballots.")


if __name__ == '__main__':
    main()
