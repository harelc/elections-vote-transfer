#!/usr/bin/env python3
"""
Enrich settlement data with Wikipedia summaries and Wikidata info.

Reads settlement names from map_25.json and queries:
- Hebrew Wikipedia REST API for description + thumbnail
- Wikidata SPARQL for population, district, settlement type

Output: site/data/settlement_wiki.json

Usage:
  python enrich_settlements_wikipedia.py         # Enrich new settlements only
  python enrich_settlements_wikipedia.py --fix    # Re-process bad entries (disambiguation, wrong topic, null)
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

OUTPUT = os.path.join('site', 'data', 'settlement_wiki.json')
MAP_FILE = os.path.join('site', 'data', 'map_25.json')
WIKI_API = 'https://he.wikipedia.org/api/rest_v1/page/summary/'
WIKI_SEARCH_API = 'https://he.wikipedia.org/w/api.php'
RATE_LIMIT = 0.15  # seconds between requests
USER_AGENT = 'KolotNodedim/1.0 (https://kolot-nodedim.netlify.app/; elections research)'

# Manual Wikipedia title overrides for normalized names that can't be auto-resolved
# (mostly compound hyphenated names where CEC removed the hyphen)
WIKI_TITLE_OVERRIDES = {
    'בועינהנוגידאת': 'בועיינה-נוג\'ידאת',
    'בנימינהגבעת עדה': 'בנימינה-גבעת עדה',
    'גדידהמכר': 'ג\'דיידה-מכר',
    'גסר אזרקא': 'ג\'סר א-זרקא',
    'טובאזנגריה': 'טובא-זנגריה',
    'יאנוחגת': 'ינוח-ג\'ת',
    'יהודמונוסון': 'יהוד-מונוסון',
    'כאוכב אבו אלהיגא': 'כאוכב אבו אל-היג\'א',
    'כסראסמיע': 'כסרא-סמיע',
    'כעביהטבאשחגאגרה': 'כעביה-טבאש-חג\'אג\'רה',
    'מודיעיןמכביםרעות': 'מודיעין-מכבים-רעות',
    'מעלותתרשיחא': 'מעלות-תרשיחא',
    'סאגור': 'סאג\'ור',
    'ערערהבנגב': 'ערערה בנגב',
    'פרדס חנהכרכור': 'פרדס חנה-כרכור',
    'קדימהצורן': 'קדימה-צורן',
    'שגבשלום': 'שגב-שלום',
    'מגד אלכרום': 'מג\'ד אל-כרום',
    'מסעודין אלעזאזמה': 'מסעודין אל-עזאזמה',
    'גש גוש חלב': 'גוש חלב',
    'רםאון': 'רם-און',
    'אורות': 'אורות (מושב)',
    'צרעה': 'צרעה (קיבוץ)',
    'חולדה': 'חולדה (קיבוץ)',
    'ציפורי': 'ציפורי (מושב)',
}

# Keywords that indicate the article is about an Israeli settlement/locality
SETTLEMENT_KEYWORDS = [
    'בישראל', 'מושב', 'קיבוץ', 'מושבה', 'עיר', 'כפר', 'יישוב',
    'התנחלות', 'קהילה', 'מועצה', 'נפה', 'שכונה', 'עיירה',
    'עיירת פיתוח', 'מועצה מקומית', 'מועצה אזורית',
]


def fetch_json(url):
    """Fetch JSON from URL with proper headers."""
    req = urllib.request.Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'type': 'not_found'}
        return None
    except Exception as e:
        return None


def is_settlement_article(data):
    """Check if Wikipedia API response is about an Israeli settlement."""
    if not data:
        return False
    if data.get('type') == 'not_found':
        return False
    if data.get('type') == 'disambiguation':
        return False
    desc = (data.get('description') or '').lower()
    extract = (data.get('extract') or '').lower()
    text = desc + ' ' + extract
    return any(kw in text for kw in SETTLEMENT_KEYWORDS)


def extract_result(data):
    """Extract settlement wiki info from a Wikipedia API response."""
    if not data or data.get('type') in ('not_found', 'disambiguation'):
        return None
    result = {
        'title': data.get('title'),
        'description': data.get('description'),
        'extract': data.get('extract', '')[:500],
        'wiki_url': data.get('content_urls', {}).get('desktop', {}).get('page'),
        'thumbnail': None,
    }
    thumb = data.get('thumbnail')
    if thumb:
        result['thumbnail'] = thumb.get('source')
    return result


def get_wiki_summary(name):
    """Get Wikipedia summary for a settlement with fallback chain."""
    # 0. Check manual overrides first
    if name in WIKI_TITLE_OVERRIDES:
        override_name = WIKI_TITLE_OVERRIDES[name]
        override_encoded = urllib.parse.quote(override_name.replace(' ', '_'))
        data = fetch_json(WIKI_API + override_encoded)
        if data and data.get('type') not in ('not_found', 'disambiguation'):
            result = extract_result(data)
            if result:
                return result
        time.sleep(RATE_LIMIT)

    encoded = urllib.parse.quote(name.replace(' ', '_'))

    # 1. Try bare name
    data = fetch_json(WIKI_API + encoded)
    if data and is_settlement_article(data):
        return extract_result(data)

    time.sleep(RATE_LIMIT)

    # 2. Try "{name} (יישוב)" — Wikipedia often redirects to specific article
    suffix_encoded = urllib.parse.quote(f'{name} (יישוב)'.replace(' ', '_'))
    data = fetch_json(WIKI_API + suffix_encoded)
    if data and is_settlement_article(data):
        return extract_result(data)

    time.sleep(RATE_LIMIT)

    # 3. Try search API (with and without quotes, also try hyphenated variant)
    search_queries = [f'"{name}" יישוב ישראל']
    # For compound names, also try with hyphens between space-separated parts
    parts = name.split()
    if len(parts) > 1:
        search_queries.append(f'"{"-".join(parts)}" יישוב ישראל')
    # Also try unquoted search
    search_queries.append(f'{name} יישוב ישראל')

    for sq in search_queries:
        search_params = urllib.parse.urlencode({
            'action': 'query',
            'list': 'search',
            'srsearch': sq,
            'srnamespace': '0',
            'srlimit': '5',
            'format': 'json',
        })
        search_data = fetch_json(f'{WIKI_SEARCH_API}?{search_params}')
        if search_data:
            results = search_data.get('query', {}).get('search', [])
            for sr in results:
                title = sr.get('title', '')
                title_encoded = urllib.parse.quote(title.replace(' ', '_'))
                candidate = fetch_json(WIKI_API + title_encoded)
                if candidate and is_settlement_article(candidate):
                    return extract_result(candidate)
                time.sleep(RATE_LIMIT)

    return None


def is_bad_entry(entry):
    """Check if an existing entry is bad and should be re-fetched."""
    if entry is None:
        return True
    if not isinstance(entry, dict):
        return True
    desc = entry.get('description') or ''
    extract = entry.get('extract') or ''
    title = entry.get('title') or ''
    # Check if it's a disambiguation page
    if 'פירושונים' in desc or 'פירושונים' in extract or 'פירושונים' in title:
        return True
    # Check if description/extract suggest it's NOT about a settlement
    text = desc + ' ' + extract
    if not any(kw in text for kw in SETTLEMENT_KEYWORDS):
        return True
    return False


def get_wikidata_info(wiki_title):
    """Try to get structured data from Wikidata via Wikipedia."""
    if not wiki_title:
        return {}

    # Use Wikidata SPARQL to get population, district, etc.
    # This is a best-effort approach
    encoded = urllib.parse.quote(wiki_title.replace(' ', '_'))
    url = f'https://he.wikipedia.org/w/api.php?action=query&titles={encoded}&prop=pageprops&format=json'
    data = fetch_json(url)
    if not data:
        return {}

    pages = data.get('query', {}).get('pages', {})
    for page_id, page_data in pages.items():
        wikibase_item = page_data.get('pageprops', {}).get('wikibase_item')
        if wikibase_item:
            return {'wikidata_id': wikibase_item}
    return {}


def main():
    fix_mode = '--fix' in sys.argv

    # Load settlement names
    print(f'Loading settlements from {MAP_FILE}...')
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        map_data = json.load(f)

    settlements = map_data.get('settlements', [])
    names = sorted(set(s['name'] for s in settlements if s.get('name')))
    print(f'Found {len(names)} unique settlement names')

    # Load existing data to resume
    existing = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f'Loaded {len(existing)} existing entries')

    # In fix mode, identify bad entries + entries with manual overrides
    if fix_mode:
        bad_names = [name for name in names if name in existing and (
            is_bad_entry(existing.get(name)) or name in WIKI_TITLE_OVERRIDES
        )]
        print(f'Fix mode: found {len(bad_names)} bad entries to re-process')
        to_process = bad_names
    else:
        to_process = [name for name in names if name not in existing]
        print(f'New entries to process: {len(to_process)}')

    if not to_process:
        print('Nothing to do!')
        return

    # Enrich each settlement
    results = dict(existing)
    processed = 0
    fixed = 0
    for i, name in enumerate(to_process):
        old_entry = results.get(name)
        old_desc = (old_entry.get('description', '') if isinstance(old_entry, dict) else '') or ''

        print(f'  [{i+1}/{len(to_process)}] {name}...', end=' ', flush=True)
        if fix_mode:
            print(f'(was: {old_desc[:40]})', end=' ', flush=True)

        wiki = get_wiki_summary(name)
        if wiki:
            results[name] = wiki
            new_desc = (wiki.get('description') or '')[:40]
            if fix_mode and old_entry is not None:
                print(f'FIXED → {new_desc}')
                fixed += 1
            else:
                print(f'OK ({new_desc})')
        else:
            results[name] = None
            print('not found')

        processed += 1
        time.sleep(RATE_LIMIT)

        # Save periodically
        if processed % 50 == 0:
            with open(OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=1)
            print(f'  Saved {len(results)} entries')

    # Final save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)

    found = sum(1 for v in results.values() if v is not None)
    print(f'\nDone! {found}/{len(results)} settlements enriched.')
    if fix_mode:
        print(f'Fixed: {fixed} entries')
    print(f'Output: {OUTPUT}')


if __name__ == '__main__':
    main()
