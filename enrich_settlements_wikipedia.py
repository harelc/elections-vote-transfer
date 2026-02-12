#!/usr/bin/env python3
"""
Enrich settlement data with Wikipedia summaries and Wikidata info.

Reads settlement names from map_25.json and queries:
- Hebrew Wikipedia REST API for description + thumbnail
- Wikidata SPARQL for population, district, settlement type

Output: site/data/settlement_wiki.json
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
RATE_LIMIT = 0.15  # seconds between requests
USER_AGENT = 'KolotNodedim/1.0 (https://kolot-nodedim.netlify.app/; elections research)'


def fetch_json(url):
    """Fetch JSON from URL with proper headers."""
    req = urllib.request.Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None


def get_wiki_summary(name):
    """Get Wikipedia summary for a settlement."""
    encoded = urllib.parse.quote(name.replace(' ', '_'))
    data = fetch_json(WIKI_API + encoded)
    if not data or data.get('type') == 'not_found':
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

    # Enrich each settlement
    results = dict(existing)
    new_count = 0
    for i, name in enumerate(names):
        if name in results:
            continue

        print(f'  [{i+1}/{len(names)}] {name}...', end=' ', flush=True)
        wiki = get_wiki_summary(name)
        if wiki:
            results[name] = wiki
            print(f'OK ({(wiki.get("description") or "")[:40]})')
        else:
            results[name] = None
            print('not found')

        new_count += 1
        time.sleep(RATE_LIMIT)

        # Save periodically
        if new_count % 50 == 0:
            with open(OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=1)
            print(f'  Saved {len(results)} entries')

    # Final save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)

    found = sum(1 for v in results.values() if v is not None)
    print(f'\nDone! {found}/{len(results)} settlements enriched.')
    print(f'Output: {OUTPUT}')


if __name__ == '__main__':
    main()
