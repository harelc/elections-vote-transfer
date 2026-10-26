#!/usr/bin/env python3
"""Find the CEC turnout map's data file once the map is public.

Per the CEC K26 guide, the daytime turnout map at
https://mapvotes.bechirot.gov.il opens at 00:00 the night before
election day; until then it sits behind a Basic-auth login, which is
removed at midnight. After that the map and the data files it loads
are public, but the guide publishes no direct data URL.

This script does the DevTools -> Network step mechanically:

  1. fetch the map page (exit early while it still answers 401);
  2. collect candidate data URLs from the page and its JS bundles
     (anything ending .json/.csv, or paths mentioning votes/turnout/
     data/api), resolving relative URLs against the map origin;
  3. probe each candidate and classify it the way the turnout poller
     does: a usable feed is a non-HTML CSV whose header carries a
     ballot/turnout column, or a JSON/{columns,rows} payload;
  4. print the usable candidates -- set the right one as
     K26_TURNOUT_URL (Netlify env + the GitHub secret of the same
     name) and the existing poller + workflow take it from there.

    python discover_turnout_feed.py            # after midnight
    python discover_turnout_feed.py --base https://mapvotes.bechirot.gov.il/

Read-only: it never sends credentials and writes nothing.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

UA = {"User-Agent": "k26-turnout-discovery"}
INTERESTING = re.compile(r"(votes?|turnout|kalpi|ballot|data|api|json|csv)", re.I)
URL_IN_TEXT = re.compile(r"""["'(]\s*((?:https?:)?//[^"'\s]+|/[^"'\s]+)""")


def fetch(url, limit=4_000_000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.status, res.headers.get_content_type(), res.read(limit)


def decode(raw):
    for enc in ("utf-8-sig", "cp1255"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def classify(url, status, ctype, raw):
    """Mirror inspectTurnout(): usable / data-but-unknown-shape / no."""
    if status != 200:
        return None
    text = decode(raw).strip()
    if not text or re.match(r"<!doctype html|^<html[\s>]", text, re.I):
        return None
    if text.startswith("{") or text.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return "json (unparseable)"
        # Summarise the record collection in any map-service shape and
        # show a sample record's field names, so the ALIASES mapping in
        # generate_turnout_day_data.py can be confirmed at a glance.
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and isinstance(data.get("rows"), list) and isinstance(data.get("columns"), list):
            return f"{{columns,rows}} JSON, {len(data['rows'])} rows -- poller-ready"
        elif isinstance(data, dict):
            for key in ("features", "rows", "records", "data", "stations", "items", "results"):
                if key in data:
                    items = data[key]
                    records = list(items.values()) if isinstance(items, dict) else items
                    break
            else:
                records = [v for v in data.values() if isinstance(v, dict)]
        sample = next((r for r in records if isinstance(r, dict)), {})
        for wrap in ("properties", "attributes", "fields"):
            if isinstance(sample.get(wrap), dict):
                sample = sample[wrap]
                break
        fields = ", ".join(list(sample)[:10])
        return (f"JSON, {len(records)} records, sample fields: {fields} "
                f"-- poller-ready if fields match generate_turnout_day_data ALIASES")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 2 and re.search(r"קלפי|ballot|אחוז|turnout|מצביעים|voters", lines[0], re.I):
        return f"CSV, {len(lines) - 1} rows, header: {lines[0][:110]} -- poller-ready"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="https://mapvotes.bechirot.gov.il/")
    args = ap.parse_args()

    try:
        status, _, raw = fetch(args.base)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("map still answers 401 (Basic-auth). It opens at 00:00 the "
                  "night before election day -- rerun after midnight.")
            return 2
        print(f"map returned HTTP {e.code}")
        return 1
    except Exception as e:
        print(f"could not fetch the map: {e}")
        return 1
    page = decode(raw)
    print(f"map is public (HTTP {status}, {len(raw):,} bytes). Scanning assets...")

    candidates = set()
    assets = []
    for m in re.finditer(r"""(?:src|href)=["']([^"']+)["']""", page):
        u = urljoin(args.base, m.group(1))
        assets.append(u)
        if INTERESTING.search(u) and re.search(r"\.(json|csv)(\?|$)", u):
            candidates.add(u)
    for asset in assets:
        if not re.search(r"\.m?js(\?|$)", asset):
            continue
        try:
            _, _, js_raw = fetch(asset)
        except Exception:
            continue
        js = decode(js_raw)
        for m in URL_IN_TEXT.finditer(js):
            u = urljoin(asset, m.group(1).replace("\\/", "/"))
            if urlparse(u).netloc != urlparse(args.base).netloc:
                continue
            if re.search(r"\.(json|csv)(\?|$)", u) or (INTERESTING.search(u) and "/api" in u):
                candidates.add(u)

    if not candidates:
        print("no data-file candidates found in the page or its JS bundles. "
              "Fall back to the manual DevTools -> Network pass from the guide.")
        return 1
    print(f"{len(candidates)} candidate(s):")
    usable = []
    for url in sorted(candidates):
        try:
            status, ctype, raw = fetch(url)
            verdict = classify(url, status, ctype, raw)
        except Exception as e:
            verdict = None
            print(f"  ? {url}  (fetch failed: {e})")
            continue
        if verdict:
            usable.append(url)
            print(f"  * {url}\n      {verdict}  [{ctype}, {len(raw):,} bytes]")
        else:
            print(f"  - {url}  (not a usable feed)")
    if usable:
        print("\nNext: set the poller-ready URL as K26_TURNOUT_URL in the Netlify "
              "env and the GitHub secret, then set turnout_auto when ready.")
        return 0
    print("\nNo poller-ready feed yet; inspect the candidates above manually.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
