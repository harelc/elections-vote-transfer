#!/usr/bin/env python3
"""
Process CBS 2011 statistical zones and match to ballot stations.

Uses the CBS geodatabase "statisticalareas_demography2019.gdb" which contains
2011 statistical area boundaries (matching the socio_eco19 T12 data exactly).

Steps:
1. Load polygons from CBS 2011 GDB (EPSG:2039 → WGS84)
2. Save compact zones JSON and full GeoJSON
3. Match ballot stations to statistical zones via point-in-polygon
"""

import json
import sys
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform as shapely_transform
from shapely.prepared import prep
import fiona

GDB_PATH = Path("data/statisticalareas_demography2019.gdb")
SITE_DATA = Path("site/data")
DATA_DIR = Path("data")

# Coordinate transformer: Israel TM Grid (EPSG:2039) → WGS84 (EPSG:4326)
transformer_to_wgs84 = Transformer.from_crs("EPSG:2039", "EPSG:4326", always_xy=True)


def load_gdb_features():
    """Load features from CBS 2011 geodatabase, converting to WGS84."""
    if not GDB_PATH.exists():
        print(f"ERROR: GDB not found at {GDB_PATH}")
        print("Download from: https://www.cbs.gov.il/he/Pages/geo-layers.aspx")
        sys.exit(1)

    print(f"  Loading from {GDB_PATH}...")
    features = []

    with fiona.open(GDB_PATH) as src:
        print(f"  CRS: {src.crs}, Features: {len(src)}")
        for rec in src:
            props = rec["properties"]
            geom_2039 = shape(rec["geometry"])

            # Transform geometry to WGS84
            geom_4326 = shapely_transform(transformer_to_wgs84.transform, geom_2039)

            features.append({
                "type": "Feature",
                "properties": {
                    "SEMEL_YISHUV": props.get("SEMEL_YISHUV"),
                    "SHEM_YISHUV": (props.get("SHEM_YISHUV") or "").strip(),
                    "SHEM_YISHUV_ENGLISH": (props.get("SHEM_YISHUV_ENGLISH") or "").strip(),
                    "STAT11": props.get("STAT11"),
                    "YISHUV_STAT11": props.get("YISHUV_STAT11"),
                    "Pop_Total": props.get("Pop_Total"),
                },
                "geometry": mapping(geom_4326),
            })

    print(f"  Loaded {len(features)} features (converted to WGS84)")
    return {"type": "FeatureCollection", "features": features}


def create_compact_zones(geojson):
    """Create compact zone data with centroids and properties."""
    zones = {}
    for feat in geojson["features"]:
        props = feat["properties"]
        yishuv_stat = props.get("YISHUV_STAT11")
        if yishuv_stat is None:
            continue

        try:
            geom = shape(feat["geometry"])
            centroid = geom.centroid
            lat, lng = round(centroid.y, 5), round(centroid.x, 5)
        except Exception:
            lat, lng = None, None

        zones[str(yishuv_stat)] = {
            "settlement_code": props.get("SEMEL_YISHUV"),
            "settlement": props.get("SHEM_YISHUV", ""),
            "settlement_en": props.get("SHEM_YISHUV_ENGLISH", ""),
            "stat_area": props.get("STAT11"),
            "pop_total": props.get("Pop_Total"),
            "lat": lat,
            "lng": lng,
        }

    return zones


def match_stations_to_zones(geojson, stations_path):
    """Match ballot stations to statistical zones via point-in-polygon."""
    print("\n--- Matching ballot stations to statistical zones ---")

    with open(stations_path, 'r', encoding='utf-8') as f:
        coord_data = json.load(f)

    stations = coord_data.get("stations", {})

    # Build spatial index
    print("  Building spatial index from zone polygons...")
    zone_polys = []
    for feat in geojson["features"]:
        props = feat["properties"]
        try:
            geom = shape(feat["geometry"])
            if not geom.is_valid:
                geom = geom.buffer(0)
            zone_polys.append((prep(geom), geom, props))
        except Exception:
            continue
    print(f"  Built index with {len(zone_polys)} zone polygons")

    # Match stations
    matched = 0
    unmatched_with_coords = 0
    no_coords = 0
    station_zones = {}

    total = len(stations)
    for i, (key, sdata) in enumerate(stations.items()):
        if i % 5000 == 0:
            print(f"  Processing station {i}/{total}...")

        lat = sdata.get("lat")
        lng = sdata.get("lng")

        if lat is None or lng is None:
            no_coords += 1
            continue

        point = Point(lng, lat)
        found = False

        for pg, geom, props in zone_polys:
            if pg.contains(point):
                yishuv_stat = props.get("YISHUV_STAT11")
                station_zones[key] = yishuv_stat
                matched += 1
                found = True
                break

        if not found:
            unmatched_with_coords += 1

    print(f"\n  Results:")
    print(f"    Matched to zone: {matched}")
    print(f"    Had coords but no zone match: {unmatched_with_coords}")
    print(f"    No coordinates: {no_coords}")
    print(f"    Total stations: {total}")

    return station_zones


def main():
    # Step 1: Load features from CBS 2011 GDB
    print("=== Step 1: Loading CBS 2011 statistical zones ===")
    geojson_path = DATA_DIR / "statistical_zones_2011.geojson"

    if geojson_path.exists():
        print(f"  Loading cached GeoJSON from {geojson_path}...")
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
        print(f"  Loaded {len(geojson['features'])} features")
    else:
        geojson = load_gdb_features()
        # Save for caching
        with open(geojson_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False)
        size_mb = geojson_path.stat().st_size / (1024 * 1024)
        print(f"  Saved GeoJSON: {geojson_path} ({size_mb:.1f} MB)")

    # Step 2: Create compact zones file
    print("\n=== Step 2: Creating compact zones data ===")
    zones = create_compact_zones(geojson)

    compact_path = SITE_DATA / "statistical_zones.json"
    with open(compact_path, 'w', encoding='utf-8') as f:
        json.dump({"zones": zones}, f, ensure_ascii=False)
    size_kb = compact_path.stat().st_size / 1024
    print(f"  Saved compact zones: {compact_path} ({size_kb:.0f} KB, {len(zones)} zones)")

    settlements = set(z["settlement"] for z in zones.values())
    print(f"  Unique settlements: {len(settlements)}")

    # Step 3: Match ballot stations to zones
    print("\n=== Step 3: Matching ballot stations to statistical zones ===")
    stations_path = SITE_DATA / "station_coordinates.json"
    station_zones = match_stations_to_zones(geojson, stations_path)

    mapping_path = SITE_DATA / "station_zone_mapping.json"
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(station_zones, f, ensure_ascii=False)
    size_kb = mapping_path.stat().st_size / 1024
    print(f"  Saved station-zone mapping: {mapping_path} ({size_kb:.0f} KB, {len(station_zones)} stations)")

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
