#!/usr/bin/env python3
"""
Fix settlements that couldn't be found. Handles:
1. West Bank settlements (not listed under Israel in OSM)
2. Merged city names (מודיעיןמכביםרעות -> מודיעין-מכבים-רעות)
3. Arabic transliteration differences
"""

import json
import sys
import time
import requests
from collections import defaultdict

# Force unbuffered output
print = lambda *a, **k: (sys.stdout.write(' '.join(str(x) for x in a) + k.get('end', '\n')), sys.stdout.flush())

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

def is_place(r):
    """Check if result is a place (not a street)."""
    place_types = {'city', 'town', 'village', 'hamlet', 'locality', 'neighbourhood',
                   'suburb', 'quarter', 'isolated_dwelling', 'farm', 'allotments',
                   'residential', 'municipality'}
    if r.get('class') == 'place' and r.get('type') in place_types:
        return True
    if r.get('class') == 'boundary' and r.get('type') == 'administrative':
        return True
    return False

# Known name fixes for settlements that OSM has under different names
NAME_FIXES = {
    'מודיעיןמכביםרעות': 'מודיעין-מכבים-רעות',
    'פרדס חנהכרכור': 'פרדס חנה-כרכור',
    'יהודמונוסון': 'יהוד-מונוסון',
    'מעלותתרשיחא': 'מעלות-תרשיחא',
    'קדימהצורן': 'קדימה-צורן',
    'גדיידהמכר': 'ג\'דיידה-מכר',
    'בנימינהגבעת עדה': 'בנימינה-גבעת עדה',
    'אום אלפחם': 'אום אל-פחם',
    'באקה אלגרביה': 'באקה אל-גרביה',
    'דאלית אלכרמל': 'דאלית אל-כרמל',
    'מגד אלכרום': 'מג\'ד אל-כרום',
    'גסר אזרקא': 'ג\'סר א-זרקא',
    'אכסאל': 'אכסאל',
    'כאבול': 'כאבול',
    'כעביה טבאש חג\'אג\'רה': 'כעביה-טבאש-חג\'אג\'רה',
    'נצרת': 'נצרת',
    'שפרעם': 'שפרעם',
    'טורעאן': 'טורעאן',
    'עראבה': 'עראבה',
    'ערערה': 'ערערה',
    'מעטפות חיצוניות': None,  # Not a real place - skip
}

# West Bank settlements - search without country code
WEST_BANK = {
    'מודיעין עילית', 'ביתר עילית', 'מעלה אדומים', 'אריאל',
    'גבעת זאב', 'בית אל', 'אפרת', 'קרית ארבע',
    'אלפי מנשה', 'קרני שומרון', 'עמנואל', 'ביתאר עילית',
    'אדם (גבע בנימין)', 'גבע בנימין', 'כוכב יעקב', 'עלי',
    'שילו', 'אורנית', 'מגדלים', 'רבבה', 'יצהר',
    'נעלה', 'חשמונאים', 'בית חורון', 'דולב', 'עפרה',
    'בית אריה', 'עטרת', 'מבוא חורון', 'גבעון החדשה',
    'פסגות', 'טלמון', 'חלמיש', 'מתתיהו', 'נריה',
    'קריית נטפים', 'ברוכין', 'אלון מורה', 'איתמר',
    'נוקדים', 'תקוע', 'כרמי צור', 'סוסיא', 'שמעה',
    'מצפה יריחו', 'ורד יריחו', 'נעמי', 'מעון', 'חגי',
    'עתניאל', 'בית הגי', 'טנא', 'אשכולות', 'פני חבר',
}


def search_settlement(name, is_west_bank=False):
    """Search for a settlement, handling different naming conventions."""
    # Try the fixed name first if available
    search_name = NAME_FIXES.get(name, name)
    if search_name is None:
        return None  # Explicitly skip (e.g., מעטפות חיצוניות)

    queries_params = []

    if is_west_bank:
        # Search without country code for West Bank
        queries_params.append({
            'q': f'{search_name}',
            'format': 'json',
            'limit': 10,
        })
        queries_params.append({
            'q': f'{search_name}, Palestine',
            'format': 'json',
            'limit': 10,
        })
        queries_params.append({
            'q': f'{search_name}, West Bank',
            'format': 'json',
            'limit': 10,
        })
    else:
        # Search with Israel country code
        queries_params.append({
            'q': f'{search_name}, ישראל',
            'format': 'json',
            'limit': 10,
            'countrycodes': 'il',
        })
        queries_params.append({
            'q': f'{search_name}, Israel',
            'format': 'json',
            'limit': 10,
            'countrycodes': 'il',
        })
        # Also try without country code (for edge cases)
        queries_params.append({
            'q': f'{search_name}, ישראל',
            'format': 'json',
            'limit': 10,
        })

    for params in queries_params:
        results = nominatim_request(params)
        for r in results:
            if is_place(r):
                return r

    return None


def main():
    with open(COORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = data['stations']

    # Find not_found settlements
    not_found = defaultdict(int)
    for key, sdata in stations.items():
        if sdata.get('source') == 'not_found':
            not_found[sdata.get('settlement', '')] += 1

    nf_list = sorted(not_found.items(), key=lambda x: -x[1])
    print(f"Not-found settlements: {len(nf_list)}")
    print(f"Total stations: {sum(c for _, c in nf_list)}")
    print("-" * 80)

    fixed = 0
    fixes = {}  # settlement_name -> (lat, lng)

    for settlement, count in nf_list:
        if not settlement or settlement == 'מעטפות חיצוניות':
            print(f"\n[{count}] {settlement} - SKIPPING (not a real place)")
            continue

        is_wb = settlement in WEST_BANK
        tag = " [WB]" if is_wb else ""
        print(f"\n[{count}] {settlement}{tag}")

        result = search_settlement(settlement, is_west_bank=is_wb)
        if result:
            lat = float(result['lat'])
            lng = float(result['lon'])
            display = result.get('display_name', '')[:60]
            print(f"  ✓ Found: {lat:.5f}, {lng:.5f} - {display}")
            fixes[settlement] = (lat, lng)
            fixed += 1
        else:
            # Try without any country filter as last resort
            params = {
                'q': f'{settlement}',
                'format': 'json',
                'limit': 10,
            }
            results = nominatim_request(params)
            for r in results:
                if is_place(r):
                    lat = float(r['lat'])
                    lng = float(r['lon'])
                    display = r.get('display_name', '')[:60]
                    print(f"  ✓ Found (no filter): {lat:.5f}, {lng:.5f} - {display}")
                    fixes[settlement] = (lat, lng)
                    fixed += 1
                    break
            else:
                print(f"  ✗ Not found")

    print(f"\n{'='*80}")
    print(f"Fixed {fixed}/{len(nf_list)} settlements")

    if fixes:
        applied = 0
        for key, sdata in stations.items():
            if sdata.get('source') == 'not_found':
                settlement = sdata.get('settlement', '')
                if settlement in fixes:
                    lat, lng = fixes[settlement]
                    sdata['lat'] = lat
                    sdata['lng'] = lng
                    sdata['source'] = 'settlement'
                    applied += 1

        data['stations'] = stations
        with open(COORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Applied fixes to {applied} stations")
        print(f"Saved to {COORDS_FILE}")

if __name__ == '__main__':
    main()
