#!/usr/bin/env python3
"""Assign every K26 ballot with coordinates to a CBS 2011 statistical area.

Geomap looks up ``settlement|ballot`` using the t-SNE name and ballot string.
K26 renumbered many boxes, so those keys were missing and the map fell back to
the municipal cluster (Jerusalem is 2) with no zone id. This fills the keys
from the same polygons used for earlier elections.
"""

import json
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent
GEOJSON = ROOT / 'data' / 'statistical_zones_2011.geojson'
TSNE = ROOT / 'site' / 'data' / 'tsne_26.json'
COORDS = ROOT / 'site' / 'data' / 'station_coordinates.json'
ZONES = ROOT / 'site' / 'data' / 'statistical_zones_socioeconomic.json'
OUT = ROOT / 'site' / 'data' / 'station_socioeconomic.json'


def load_polygons():
    geojson = json.loads(GEOJSON.read_text(encoding='utf-8'))
    geoms = []
    ids = []
    for feat in geojson['features']:
        yishuv = feat['properties'].get('YISHUV_STAT11')
        if yishuv is None:
            continue
        geom = shape(feat['geometry'])
        if geom.is_empty:
            continue
        if not geom.is_valid:
            geom = geom.buffer(0)
        geoms.append(geom)
        ids.append(str(int(yishuv)) if isinstance(yishuv, float) else str(yishuv))
    return STRtree(geoms), geoms, ids


def coord_for(stations, name, ballot):
    for key in (f'{name}|{ballot}', f'{name}|{ballot}.0'):
        entry = stations.get(key)
        if entry and entry.get('lat') is not None and entry.get('lng') is not None:
            return float(entry['lat']), float(entry['lng'])
    return None


def main():
    print('Loading polygons…')
    tree, geoms, ids = load_polygons()
    print(f'  {len(geoms)} zones')

    tsne = json.loads(TSNE.read_text(encoding='utf-8'))
    coords = json.loads(COORDS.read_text(encoding='utf-8'))['stations']
    zone_socio = json.loads(ZONES.read_text(encoding='utf-8'))['zones']
    station_se = json.loads(OUT.read_text(encoding='utf-8'))

    matched = already = no_coord = outside = no_cluster = 0
    for station in tsne['stations']:
        name, ballot = station['n'], str(station['b'])
        key = f'{name}|{ballot}'
        if key in station_se and station_se[key].get('zone') and station_se[key].get('cluster'):
            already += 1
            continue
        latlng = coord_for(coords, name, ballot)
        if latlng is None:
            no_coord += 1
            continue
        point = Point(latlng[1], latlng[0])
        yishuv = None
        for idx in tree.query(point):
            if geoms[idx].covers(point):
                yishuv = ids[idx]
                break
        if yishuv is None:
            outside += 1
            continue
        socio = zone_socio.get(yishuv) or {}
        cluster = socio.get('cluster')
        if not cluster:
            no_cluster += 1
            continue
        station_se[key] = {'zone': int(yishuv) if str(yishuv).isdigit() else yishuv, 'cluster': int(cluster)}
        matched += 1

    OUT.write_text(json.dumps(station_se, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    # The existing file is pretty-printed. Rewrite with the same indent so the
    # diff stays readable for the new keys only as far as JSON allows.
    OUT.write_text(json.dumps(station_se, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Already had a zone: {already}')
    print(f'Newly matched: {matched}')
    print(f'No coordinate: {no_coord}')
    print(f'Outside every polygon: {outside}')
    print(f'Polygon hit but no cluster: {no_cluster}')
    print(f'Station records: {len(station_se)}')


if __name__ == '__main__':
    main()
