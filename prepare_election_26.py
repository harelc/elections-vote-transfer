#!/usr/bin/env python3
"""
Prepare election 26 data for the site.

Workflow:
1. Copy ballot25.csv → ballot26.csv (with optional party column remapping)
2. Generate T-SNE data for election 26
3. Generate transfer data for 25→26
4. Generate map data for election 26
5. Copy all outputs to site/data/

Usage:
    python prepare_election_26.py [--real-csv path/to/ballot26.csv]

Without --real-csv, creates a dry-run copy from election 25 data.
With --real-csv, uses the provided CSV as the real ballot26.csv.
"""

import argparse
import shutil
import subprocess
import sys
import os

# Optional: remap party column names from election 25 to election 26
# Add entries here when party names/symbols change
# Format: {'old_column_name': 'new_column_name'}
PARTY_REMAP_26 = {
    # Example: 'פה': 'כן'  # if Blue and White symbol changes
}


def copy_ballot_csv(real_csv=None):
    """Copy or create ballot26.csv from ballot25.csv."""
    dest = 'ballot26.csv'
    if real_csv:
        print(f"Using real CSV: {real_csv} → {dest}")
        if os.path.abspath(real_csv) != os.path.abspath(dest):
            shutil.copy2(real_csv, dest)
        else:
            print(f"  (source and dest are the same file, skipping copy)")
        return

    src = 'ballot25.csv'
    if not os.path.exists(src):
        print(f"ERROR: {src} not found. Cannot create dry-run data.")
        sys.exit(1)

    if PARTY_REMAP_26:
        import pandas as pd
        from party_config import ELECTIONS
        enc = ELECTIONS['25'].get('encoding', 'utf-8-sig')
        df = pd.read_csv(src, encoding=enc)
        df.rename(columns=PARTY_REMAP_26, inplace=True)
        df.to_csv(dest, index=False, encoding='utf-8-sig')
        print(f"Created {dest} from {src} with column remapping: {PARTY_REMAP_26}")
    else:
        shutil.copy2(src, dest)
        print(f"Copied {src} → {dest} (no column remapping)")


def run_script(cmd, desc):
    """Run a Python script and check for errors."""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"ERROR: {desc} failed with exit code {result.returncode}")
        sys.exit(1)
    print(f"  ✓ {desc} completed successfully")


def copy_outputs():
    """Copy generated data files to site/data/."""
    os.makedirs('site/data', exist_ok=True)
    copies = [
        ('data/transfer_25_to_26.json', 'site/data/transfer_25_to_26.json'),
        ('data/transfer_25_to_26_abstention.json', 'site/data/transfer_25_to_26_abstention.json'),
        ('data/tsne_26.json', 'site/data/tsne_26.json'),
    ]
    for src, dest in copies:
        if os.path.exists(src):
            shutil.copy2(src, dest)
            print(f"  Copied {src} → {dest}")
        else:
            print(f"  WARNING: {src} not found, skipping")

    # Also update combined all_transfers files if generated
    for name in ('all_transfers.json', 'all_transfers_abstention.json'):
        src = f'data/{name}'
        if os.path.exists(src):
            shutil.copy2(src, f'site/data/{name}')
            print(f"  Copied {src} → site/data/{name}")


def main():
    parser = argparse.ArgumentParser(description='Prepare election 26 data')
    parser.add_argument('--real-csv', help='Path to real ballot26.csv file')
    args = parser.parse_args()

    print("Election 26 Data Preparation")
    print("=" * 60)

    # Step 1: Create/copy ballot26.csv
    copy_ballot_csv(args.real_csv)

    # Step 2: Generate T-SNE data for election 26
    run_script(
        [sys.executable, 'generate_tsne_data.py', '--elections', '26'],
        'Generating T-SNE data for election 26'
    )

    # Step 2.5: Copy fresh tsne to site/data/ BEFORE running map_data,
    # because generate_map_data.py reads tsne from site/data/, not data/.
    # Without this hop the map JSON would lag one prepare-run behind on any
    # party_config change (e.g., a new leader override).
    if os.path.exists('data/tsne_26.json'):
        os.makedirs('site/data', exist_ok=True)
        shutil.copy2('data/tsne_26.json', 'site/data/tsne_26.json')
        print('  Pre-copied data/tsne_26.json → site/data/ for map_data step')

    # Step 3: Generate transfer data for 25→26
    run_script(
        [sys.executable, 'generate_transfer_data.py', '--transitions', '25_to_26'],
        'Generating transfer data for 25→26'
    )

    # Step 4: Generate map data for election 26 (reads from site/data/tsne_26.json)
    run_script(
        [sys.executable, 'generate_map_data.py', '--elections', '26'],
        'Generating map data for election 26'
    )

    # Step 5: Copy outputs to site/data/
    print(f"\n{'='*60}")
    print("  Copying outputs to site/data/")
    print(f"{'='*60}")
    copy_outputs()

    print(f"\n{'='*60}")
    print("  All done! Open pages with ?e26=1 to see election 26 data.")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
