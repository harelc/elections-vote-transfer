#!/usr/bin/env python3
"""
Scrape ballot location names from Israeli Central Elections Committee website.
Polite scraper with delays and incremental saving.

Written by Harel Cain, 2024
"""

import json
import logging
import random
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Election website URLs
ELECTION_URLS = {
    '21': 'https://votes21.bechirot.gov.il/ballotresults',
    '22': 'https://votes22.bechirot.gov.il/ballotresults',
    '23': 'https://votes23.bechirot.gov.il/ballotresults',
    '24': 'https://votes24.bechirot.gov.il/ballotresults',
    '25': 'https://votes25.bechirot.gov.il/ballotresults',
}

# Polite request settings
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
}

# Delay settings (in seconds)
MIN_DELAY = 0.05
MAX_DELAY = 0.1


def get_delay():
    """Get a random delay to be polite."""
    return random.uniform(MIN_DELAY, MAX_DELAY)


def fetch_page(url, params=None, session=None):
    """Fetch a page with proper headers and error handling."""
    if session is None:
        session = requests.Session()

    try:
        response = session.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def extract_settlements(html):
    """Extract settlement list from the main page."""
    # The HTML has a quirky structure: <datalist id=select1 /><option>...
    # So we need to use regex to extract the options after the datalist

    # Find all OPTION tags with VALUE attribute (settlement options)
    # Pattern: <OPTION ... VALUE=number>name</OPTION>
    pattern = re.compile(r'<OPTION[^>]*VALUE=(\d+)[^>]*>([^<]+)</OPTION>', re.IGNORECASE)

    settlements = []
    for match in pattern.finditer(html):
        value = match.group(1)
        name = match.group(2).strip()
        if value and value != '0' and name:
            settlements.append({
                'id': value,
                'name': name
            })

    # Deduplicate (in case there are multiple dropdowns)
    seen = set()
    unique = []
    for s in settlements:
        if s['id'] not in seen:
            seen.add(s['id'])
            unique.append(s)

    return unique


def extract_ballots(html):
    """Extract ballot locations from a city page."""
    # Use regex to find the ballot options in select2 datalist
    # The options are after <datalist id=select2

    # Find the section with select2 (polling stations)
    select2_match = re.search(r'<datalist id=select2[^>]*>(.*?)(?=<datalist|$)', html, re.IGNORECASE | re.DOTALL)
    if not select2_match:
        # Try alternate: look for PollingStation options
        select2_match = re.search(r'id="PollingStation"[^>]*>.*?<datalist[^>]*>(.*?)(?=</datalist|<datalist|$)', html, re.IGNORECASE | re.DOTALL)

    if not select2_match:
        return []

    options_html = select2_match.group(1) if select2_match else html

    ballots = []
    # Pattern for ballot options: <OPTION VALUE=ballot_num>location קלפי מספר ballot_num מספר ברזל</OPTION>
    option_pattern = re.compile(r'<OPTION[^>]*VALUE=([^>]+)>([^<]+)</OPTION>', re.IGNORECASE)
    # Pattern to extract location from text
    location_pattern = re.compile(r'^(.+?)\s*קלפי מספר\s*([\d.]+)\s*מספר ברזל')

    for match in option_pattern.finditer(options_html):
        value = match.group(1).strip()
        text = match.group(2).strip()

        if value and value != '0':
            loc_match = location_pattern.match(text)
            if loc_match:
                location = loc_match.group(1).strip()
                ballot_num = loc_match.group(2)
                ballots.append({
                    'ballot': ballot_num,
                    'location': location
                })
            else:
                # Fallback: just use the whole text
                ballots.append({
                    'ballot': value,
                    'location': text
                })

    return ballots


def load_progress(election_id):
    """Load previously scraped data."""
    progress_file = Path(f'data/ballot_locations_{election_id}_progress.json')
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'settlements_done': [], 'data': {}}


def save_progress(election_id, progress):
    """Save progress incrementally."""
    progress_file = Path(f'data/ballot_locations_{election_id}_progress.json')
    Path('data').mkdir(exist_ok=True)
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def save_final(election_id, data):
    """Save final ballot locations data."""
    output_file = Path(f'data/ballot_locations_{election_id}.json')
    Path('data').mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved final data to {output_file}")


def scrape_election(election_id, resume=True):
    """Scrape ballot locations for one election."""
    base_url = ELECTION_URLS.get(election_id)
    if not base_url:
        logger.error(f"Unknown election ID: {election_id}")
        return None

    logger.info(f"Scraping election {election_id} from {base_url}")

    # Load progress if resuming
    progress = load_progress(election_id) if resume else {'settlements_done': [], 'data': {}}

    # Create session for connection reuse
    session = requests.Session()

    # First, get the main page to extract settlement list
    logger.info("Fetching settlement list...")
    html = fetch_page(base_url, session=session)
    if not html:
        return None

    settlements = extract_settlements(html)
    logger.info(f"Found {len(settlements)} settlements")

    # Filter out already done settlements
    todo = [s for s in settlements if s['id'] not in progress['settlements_done']]
    logger.info(f"Remaining: {len(todo)} settlements to scrape")

    # Scrape each settlement
    for i, settlement in enumerate(todo):
        settlement_id = settlement['id']
        settlement_name = settlement['name']

        logger.info(f"[{i+1}/{len(todo)}] Scraping {settlement_name} (ID: {settlement_id})...")

        # Polite delay
        time.sleep(get_delay())

        # Fetch the city page
        html = fetch_page(base_url, params={'cityID': settlement_id}, session=session)
        if not html:
            logger.warning(f"Failed to fetch {settlement_name}, skipping...")
            continue

        # Extract ballots
        ballots = extract_ballots(html)

        if ballots:
            progress['data'][settlement_id] = {
                'name': settlement_name,
                'ballots': ballots
            }
            logger.info(f"  Found {len(ballots)} ballots")
        else:
            logger.warning(f"  No ballots found for {settlement_name}")

        # Mark as done and save progress
        progress['settlements_done'].append(settlement_id)

        # Save progress every 10 settlements
        if (i + 1) % 10 == 0:
            save_progress(election_id, progress)
            logger.info(f"  Progress saved ({len(progress['settlements_done'])} settlements done)")

    # Save final progress
    save_progress(election_id, progress)

    # Build final output: flatten to ballot_number -> location mapping
    final_data = {
        'election': election_id,
        'settlements': progress['data'],
        'ballot_to_location': {}
    }

    # Create a flat mapping of (settlement_id, ballot) -> location
    for settlement_id, sdata in progress['data'].items():
        settlement_name = sdata['name']
        for ballot in sdata['ballots']:
            # Key format: "settlement_id:ballot_number"
            key = f"{settlement_id}:{ballot['ballot']}"
            final_data['ballot_to_location'][key] = ballot['location']

    save_final(election_id, final_data)

    return final_data


def main():
    """Scrape ballot locations for all elections."""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape ballot locations from elections website')
    parser.add_argument('--election', '-e', choices=['21', '22', '23', '24', '25', 'all'],
                       default='all', help='Election to scrape (default: all)')
    parser.add_argument('--no-resume', action='store_true',
                       help='Start fresh instead of resuming')
    args = parser.parse_args()

    elections = ['21', '22', '23', '24', '25'] if args.election == 'all' else [args.election]

    for election_id in elections:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing election {election_id}")
        logger.info('='*60)

        try:
            scrape_election(election_id, resume=not args.no_resume)
        except KeyboardInterrupt:
            logger.info("\nInterrupted by user. Progress has been saved.")
            break
        except Exception as e:
            logger.error(f"Error processing election {election_id}: {e}")
            continue

    logger.info("\nDone!")


if __name__ == '__main__':
    main()
