"""Scrape K26 party logos from VoteSmart (votesmart.co.il/Lists).

The Lists page is a Base44 SPA; its public Party entity API returns
`logo_url` per list. This script fetches that API, matches parties to the
K26 roster in party_config.py by ballot letter, downloads each logo into
site/images/logos/k26_<slug>.<ext> (rasters normalised to PNG via Pillow,
SVGs kept as-is), and prints the `logo:` lines to paste / verify in
PARTY_OVERRIDES for election 26.

Usage:  source venv/bin/activate && python scrape_k26_logos.py
Source: https://votesmart.co.il/Lists (fetched 2026-10-23). Logos remain
the property of the respective lists; used here as party identifiers.
"""
import io
import json
import sys
import urllib.request

APP_ID = "69f986d223ef3b2476c4cf87"
API = f"https://votesmart.co.il/api/apps/{APP_ID}/entities/Party?limit=100"
OUT_DIR = "site/images/logos"

# K26 ballot letter -> file slug (mirrors ELECTIONS['26'] in party_config.py)
K26_BY_LETTER = {
    "דרך": "yashar",
    "מחל": "likud",
    "רק": "beyachad",
    "אמת": "democrats",
    "ל": "yisrael_beiteinu",
    "ודם": "joint_list",
    "ג": "utj",
    "שס": "shas",
    "ב": "otzma_yehudit",
    "ט": "religious_zionism",
    "עם": "raam",
    "ך": "amcha_yisrael",
    "די": "hendel_zelicha",
    "זך": "haredi_public",
    "ני": "noam",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-App-Id": APP_ID})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), r.headers.get_content_type()


def main():
    raw, _ = fetch(API)
    parties = json.loads(raw)
    by_letter = {p.get("letter"): p for p in parties if p.get("letter")}
    missing = []
    for letter, slug in K26_BY_LETTER.items():
        p = by_letter.get(letter)
        url = (p or {}).get("logo_url")
        if not url:
            missing.append((letter, slug, (p or {}).get("name")))
            continue
        try:
            data, ctype = fetch(url)
        except Exception as e:  # dead logo_url on VoteSmart — report, don't abort
            missing.append((letter, slug, f"{(p or {}).get('name')} [{e}]"))
            continue
        if "svg" in ctype or url.split("?")[0].endswith(".svg"):
            path = f"{OUT_DIR}/k26_{slug}.svg"
            open(path, "wb").write(data)
        else:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            if img.mode not in ("RGBA", "LA"):
                img = img.convert("RGBA")
            img.thumbnail((900, 900))
            path = f"{OUT_DIR}/k26_{slug}.png"
            img.save(path)
        print(f"{letter:5} {slug:20} {path}  <- {url[:90]}")
    for letter, slug, name in missing:
        print(f"MISSING {letter} {slug} ({name}): no logo_url on VoteSmart", file=sys.stderr)


if __name__ == "__main__":
    main()
