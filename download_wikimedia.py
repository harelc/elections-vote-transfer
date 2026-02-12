#!/usr/bin/env python3
"""Download party logos and leader photos from Wikimedia Commons."""

import json
import os
import subprocess
import urllib.request
import urllib.parse
import time
import sys

LOGOS_DIR = "/Users/harel/Developer/elections-vote-transfer/site/images/logos"
LEADERS_DIR = "/Users/harel/Developer/elections-vote-transfer/site/images/leaders"

API_BASE = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ElectionsVoteTransfer/1.0 (https://github.com/elections-vote-transfer; harel@example.com) Python/3"

# Each entry: (output_filename, [list of Wikimedia filenames to try], width)
LOGOS = [
    ("yesh_atid.png", ["File:YeshAtidLogo.svg", "File:Yesh Atid logo.png"], 250),
    ("shas.png", ["File:Shas logo.png"], 250),
    ("utj.png", ["File:Yahadut HaTorah logo.png"], 250),
    ("yisrael_beiteinu.png", ["File:Israel-beytenu-logo.svg"], 250),
    ("labor.png", ["File:Israeli Labor Party 2019.png"], 250),
    ("hadash_taal.png", ["File:Hadash.svg", "File:Logo Hadash Ta'al.png"], 250),
    ("raam.png", ["File:Raam logo 2021.svg"], 250),
    ("religious_zionism.png", ["File:RZ logo 2023.svg", "File:Religious Zionist party logo 2022.svg", "File:Logo Sionismo Religioso.png"], 250),
    ("national_unity.png", [u"File:\u05dc\u05d5\u05d2\u05d5 \u05e0\u05d5\u05e2\u05e8 \u05d4\u05de\u05d7\u05e0\u05d4 \u05d4\u05de\u05de\u05dc\u05db\u05ea\u05d9.jpg"], 250),
    ("otzma_yehudit.png", ["File:Otzma Yehudit 2021 logo.svg", "File:Otzma Yehudit logo 2019.png"], 250),
    ("zehut.png", ["File:ZehutParty.svg", "File:Zehut logo.png"], 250),
    ("new_right.png", ["File:Logo of HaYamin HeHadash.svg", "File:Logo of HaYamin HeHadash.png"], 250),
]

LEADERS = [
    ("ben_gvir.jpg", ["File:Itamar Ben Gvir 3 (cropped).jpg", "File:Itamar Ben Gvir.jpg"], 300),
]


def query_wikimedia_api(file_title, width):
    """Query Wikimedia Commons API for thumbnail URL."""
    params = {
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": str(width),
        "format": "json",
    }
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    pages = data.get("query", {}).get("pages", {})
    # If the key is "-1", the file doesn't exist
    if "-1" in pages:
        return None

    for page_id, page_data in pages.items():
        imageinfo = page_data.get("imageinfo", [])
        if imageinfo:
            return imageinfo[0].get("thumburl") or imageinfo[0].get("url")
    return None


def download_with_curl(url, output_path):
    """Download a file using curl (avoids urllib 403 issues with Wikimedia)."""
    result = subprocess.run(
        [
            "curl", "-L", "-s", "-o", output_path,
            "-A", USER_AGENT,
            "--max-time", "30",
            url
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"curl failed: {result.stderr}")
    if not os.path.exists(output_path):
        raise Exception("File was not created")
    size = os.path.getsize(output_path)
    if size == 0:
        os.remove(output_path)
        raise Exception("Downloaded file is empty")
    return size


def verify_image(path):
    """Verify the downloaded file is an actual image, not HTML error page."""
    result = subprocess.run(["file", path], capture_output=True, text=True)
    output = result.stdout.lower()
    # Check for image types
    if any(t in output for t in ["png", "jpeg", "jpg", "image", "bitmap", "graphic", "photo"]):
        return True, output.strip()
    # If it's HTML or text, it's an error page
    if any(t in output for t in ["html", "text", "ascii", "xml"]):
        return False, output.strip()
    # For other types, assume ok but warn
    return True, output.strip()


def process_downloads(items, output_dir, item_type="logo"):
    """Process a list of download items."""
    results = {"success": [], "failed": []}

    for output_name, filenames_to_try, width in items:
        output_path = os.path.join(output_dir, output_name)
        print(f"\n--- {output_name} ---")

        success = False
        for filename in filenames_to_try:
            print(f"  Trying: {filename}")
            try:
                thumb_url = query_wikimedia_api(filename, width)
                if thumb_url is None:
                    print(f"    -> File not found on Wikimedia Commons")
                    time.sleep(0.3)
                    continue

                print(f"    -> Found thumbnail: {thumb_url}")
                size = download_with_curl(thumb_url, output_path)
                print(f"    -> Downloaded {size} bytes")

                is_valid, file_type = verify_image(output_path)
                if is_valid:
                    print(f"    -> Verified: {file_type}")
                    results["success"].append(output_name)
                    success = True
                    break
                else:
                    print(f"    -> INVALID: {file_type}, deleting")
                    os.remove(output_path)

            except Exception as e:
                print(f"    -> Error: {e}")
                if os.path.exists(output_path):
                    os.remove(output_path)

            # Be polite to the API
            time.sleep(0.5)

        if not success:
            print(f"  FAILED: Could not download {output_name}")
            results["failed"].append(output_name)

        time.sleep(0.3)

    return results


def main():
    os.makedirs(LOGOS_DIR, exist_ok=True)
    os.makedirs(LEADERS_DIR, exist_ok=True)

    print("=" * 60)
    print("Downloading party logos...")
    print("=" * 60)
    logo_results = process_downloads(LOGOS, LOGOS_DIR, "logo")

    print("\n" + "=" * 60)
    print("Downloading leader photos...")
    print("=" * 60)
    leader_results = process_downloads(LEADERS, LEADERS_DIR, "leader")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_success = logo_results["success"] + leader_results["success"]
    all_failed = logo_results["failed"] + leader_results["failed"]

    print(f"\nLogos - Success: {len(logo_results['success'])}, Failed: {len(logo_results['failed'])}")
    for name in logo_results["success"]:
        path = os.path.join(LOGOS_DIR, name)
        size = os.path.getsize(path)
        print(f"  OK: {name} ({size} bytes)")
    if logo_results["failed"]:
        print(f"  Failed: {', '.join(logo_results['failed'])}")

    print(f"\nLeaders - Success: {len(leader_results['success'])}, Failed: {len(leader_results['failed'])}")
    for name in leader_results["success"]:
        path = os.path.join(LEADERS_DIR, name)
        size = os.path.getsize(path)
        print(f"  OK: {name} ({size} bytes)")
    if leader_results["failed"]:
        print(f"  Failed: {', '.join(leader_results['failed'])}")

    print(f"\nTotal: {len(all_success)} succeeded, {len(all_failed)} failed")
    return 0 if not all_failed else 1


if __name__ == "__main__":
    sys.exit(main())
