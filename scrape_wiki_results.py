#!/usr/bin/env python3
"""
Scrape official election results from saved Wikipedia pages.
"""

from bs4 import BeautifulSoup
import re
import json
from pathlib import Path

# Party name normalization mapping
PARTY_NAME_MAP = {
    'הליכוד': 'הליכוד',
    'יש עתיד': 'יש עתיד',
    'הציונות הדתית': 'הציונות הדתית',
    'המחנה הממלכתי': 'המחנה הממלכתי',
    'התאחדות הספרדים שומרי תורה': 'ש״ס',
    'ש"ס': 'ש״ס',
    'שס': 'ש״ס',
    'יהדות התורה': 'יהדות התורה',
    'יהדות התורהוהשבת': 'יהדות התורה',
    'ישראל ביתנו': 'ישראל ביתנו',
    'הרשימה הערבית המאוחדת': 'רע״ם',
    'רע"ם': 'רע״ם',
    'חד"ש תע"ל': 'חד״ש-תע״ל',
    'חד"ש-תע"ל': 'חד״ש-תע״ל',
    'חדש-תעל': 'חד״ש-תע״ל',
    'מפלגת העבודה': 'העבודה',
    'העבודה': 'העבודה',
    'העבודה-גשר-מרצ': 'העבודה',
    'מרצ': 'מרצ',
    'מרצהשמאל של ישראל': 'מרצ',
    'בל"ד': 'בל״ד',
    'בל"ד- אלתג\'מוע אלווטני אלדמוקרטי': 'בל״ד',
    'הבית היהודי': 'הבית היהודי',
    'כחול לבן': 'כחול לבן',
    'ימינה': 'ימינה',
    'תקווה חדשה': 'תקווה חדשה',
    'הרשימה המשותפת': 'הרשימה המשותפת',
    'כולנו': 'כולנו',
    'הימין החדש': 'הימין החדש',
    'איחוד מפלגות הימין': 'איחוד מפלגות הימין',
    'זהות': 'זהות',
    'גשר': 'גשר',
}

def normalize_party_name(name):
    """Normalize party name for consistent matching."""
    # Clean up the name
    name = name.strip()
    # Remove common suffixes
    name = re.split(r'בהנהגת|בראשות|בראש|תנועתו של|זצ"ל', name)[0].strip()

    # Check mapping
    for key, value in PARTY_NAME_MAP.items():
        if key in name:
            return value

    return name


# Non-party rows to skip
SKIP_NAMES = [
    'סה"כ',
    'סה״כ',
    'סהכ',
    'בעלי זכות',
    'בעלי זכות הצבעה',
    'כשרים',
    'פסולים',
    'נמנעים',
    'total',
]


def is_party_row(name):
    """Check if this is an actual party row (not total/summary row)."""
    name_lower = name.lower().strip()
    for skip in SKIP_NAMES:
        if skip in name_lower or skip in name:
            return False
    return True


def extract_election_results(filepath):
    """Extract party results from a Wikipedia election page."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    tables = soup.find_all("table", class_="wikitable")

    results = []
    seen_parties = set()

    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        header_text = ' '.join(headers)

        # Look for the main results table
        if ('מנדט' in header_text or 'מושב' in header_text) and 'קולות' in header_text:
            rows = table.find_all("tr")

            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 4:
                    continue

                texts = [c.get_text(strip=True) for c in cells]

                # Try to extract party name from first cell
                first_text = texts[0]
                if len(first_text) < 2 or first_text.isdigit():
                    continue

                party_name = normalize_party_name(first_text)

                # Skip non-party rows (totals, eligible voters, etc.)
                if not is_party_row(first_text) or not is_party_row(party_name):
                    continue

                if party_name in seen_parties or len(party_name) < 2:
                    continue

                # Find seats and votes in the row
                seats = None
                votes = None

                for text in texts[1:]:
                    # Clean the text
                    clean = text.replace(',', '').replace(' ', '')

                    # Check if it's a number
                    if clean.isdigit():
                        num = int(clean)
                        # Seats are typically 0-120
                        if seats is None and 0 <= num <= 120:
                            # But could also be votes if very small party
                            if votes is None and num > 120:
                                votes = num
                            else:
                                seats = num
                        # Votes are typically > 1000
                        elif votes is None and num > 1000:
                            votes = num

                if party_name and votes and votes > 10000:
                    seen_parties.add(party_name)
                    results.append({
                        'name': party_name,
                        'seats': seats or 0,
                        'votes': votes
                    })

    # Sort by votes descending
    results.sort(key=lambda x: x['votes'], reverse=True)
    return results


def main():
    wiki_dir = Path("wikipages")
    output_dir = Path("data")

    elections = {
        '21': 'הבחירות_לכנסת_העשרים_ואחת.html',
        '22': 'הבחירות_לכנסת_העשרים_ושתיים.html',
        '23': 'הבחירות_לכנסת_העשרים_ושלוש.html',
        '24': 'הבחירות_לכנסת_העשרים_וארבע.html',
        '25': 'הבחירות לכנסת העשרים וחמש – ויקיפדיה.html',
    }

    all_results = {}

    for election_id, filename in elections.items():
        filepath = wiki_dir / filename
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        print(f"\n=== Knesset {election_id} ===")
        results = extract_election_results(filepath)
        all_results[election_id] = results

        total_votes = sum(r['votes'] for r in results)
        total_seats = sum(r['seats'] for r in results)

        print(f"Total: {total_votes:,} votes, {total_seats} seats")
        print(f"Parties that passed threshold:")
        for r in results:
            if r['seats'] > 0:
                print(f"  {r['name']}: {r['seats']} seats, {r['votes']:,} votes")

    # Save results
    output_file = output_dir / "wiki_official_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
