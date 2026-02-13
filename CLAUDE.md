# Elections Vote Transfer Project

Interactive visualizations for analyzing Israeli Knesset election data, showing vote transfers between elections, party support patterns, and ballot-level analysis.

Live site: https://kolot-nodedim.netlify.app/

## Project Structure

```
├── ballot*.csv                    # Raw election data per election (16-26), in project root
├── data/                          # Processed data files
│   ├── ballot_locations_*.json    # Ballot venue names (scraped)
│   ├── socio_eco21_T*.xlsx        # CBS 2021 socioeconomic data (T01, T07, T08, T12)
│   └── statisticalareas_demography2019.gdb/  # CBS 2011 statistical area boundaries (GDB)
├── party_config.py                # Election metadata, party names/symbols/seats per election (16-25)
├── generate_transfer_data.py      # Generates vote transfer matrices (cvxpy optimization)
├── generate_tsne_data.py          # Generates T-SNE clustering data
├── generate_map_data.py           # Generates geographic map data per election (with name normalization)
├── download_statistical_zones.py  # Loads CBS 2011 GDB, matches stations to zones via point-in-polygon
├── process_statistical_zones.py   # Joins CBS socioeconomic data to zones, creates station mapping
├── download_historical_ballots.py # Downloads K16-K20 ballot CSVs from CEC CKAN API
├── normalize_tsne_names.py        # One-shot: normalize settlement names in tsne_*.json
├── normalize_coordinates.py       # One-shot: normalize settlement names in station_coordinates.json
├── add_locations_to_tsne.py       # Adds venue names to tsne_*.json from ballot_locations
├── enrich_settlements_wikipedia.py # Fetches Wikipedia summaries for settlements
├── prepare_election_26.py         # Workflow script to generate all election 26 data
├── generate_og_image.py           # Generates OG social preview image (Pillow)
├── geocode_with_amenities.py      # Geocodes ballot stations via Nominatim
├── fix_venues_google.py           # Precise geocoding via Google Places API
├── requirements.txt               # Python dependencies
├── venv/                          # Python virtual environment
├── wikipages/                     # Wikipedia HTML files with party info per election
├── site/                          # Static website (served directly)
│   ├── index.html                 # Landing page dashboard
│   ├── sankey.html                # Sankey vote flow diagram (was index.html)
│   ├── sankey.js                  # Sankey visualization logic
│   ├── tsne.html                  # T-SNE ballot clustering visualization
│   ├── geomap.html                # Geographic map with ballot station markers
│   ├── scatter.html               # Party support scatter plot (X vs Y axis)
│   ├── dhondt.html                # D'Hondt/Bader-Ofer seat allocation calculator
│   ├── irregular.html             # Irregular ballot analysis
│   ├── regional.html              # Regional elections simulator (Voronoi + D'Hondt)
│   ├── settlement.html            # Settlement profile page (?name=...)
│   ├── party.html                 # Party profile page (?name=...)
│   ├── discussions.html           # Giscus discussions page
│   ├── styles.css                 # Shared CSS (desktop)
│   ├── i18n.js                    # Internationalization (Hebrew/English), nav rendering
│   ├── i18n.css                   # RTL/LTR + language toggle styles
│   ├── og-image.png               # Social preview image (1200x630)
│   ├── favicon.svg                # Site favicon
│   ├── images/                    # Archive election photos (NLI Dan Hadani collection)
│   │   ├── archive_poster_1.jpg   # Election poster
│   │   ├── archive_poster_2.jpg   # Election poster
│   │   └── archive_photo_3-12.jpg # Historical election photos (voting, rallies, results)
│   ├── m/                         # Mobile-optimized pages
│   │   ├── index.html             # Mobile dashboard
│   │   ├── sankey.html            # Mobile Sankey
│   │   ├── tsne.html              # Mobile T-SNE
│   │   ├── geomap.html            # Mobile geographic map
│   │   ├── scatter.html           # Mobile scatter plot
│   │   ├── dhondt.html            # Mobile D'Hondt calculator
│   │   ├── regional.html          # Mobile regional simulator
│   │   ├── settlement.html        # Mobile settlement profile
│   │   ├── party.html             # Mobile party profile
│   │   ├── irregular.html         # Mobile irregular ballot analysis
│   │   ├── discussions.html       # Mobile discussions
│   │   └── styles.css             # Shared CSS (mobile)
│   └── data/                      # JSON data for frontend (source of truth)
│       ├── transfer_*.json        # Vote transfer matrices between elections
│       ├── tsne_*.json            # T-SNE clustering data per election
│       ├── map_*.json             # Geographic/settlement data per election
│       ├── all_transfers.json     # Combined transfer data for all election pairs
│       ├── settlement_wiki.json   # Wikipedia enrichment data per settlement
│       ├── wiki_official_results.json # Official per-party vote totals per election (from Wikipedia)
│       ├── station_coordinates.json # Geocoded ballot station coordinates
│       ├── socioeconomic_clusters.json # CBS socioeconomic cluster per settlement
│       ├── statistical_zones.json     # CBS 2011 statistical area boundaries (centroids + metadata)
│       ├── statistical_zones_socioeconomic.json # Per-zone socioeconomic cluster/index
│       ├── station_zone_mapping.json  # Ballot station → statistical zone (YISHUV_STAT)
│       └── station_socioeconomic.json # Per-station socioeconomic cluster + zone ID
```

## Running the Project

```bash
# Start local server
cd site && python3 -m http.server 8888
# Access at http://localhost:8888/

# Desktop pages served at root, mobile at /m/
# Each desktop page auto-redirects to /m/ on mobile devices
```

## Architecture

### Desktop vs Mobile
Every visualization has two HTML files: `site/<page>.html` (desktop) and `site/m/<page>.html` (mobile). Desktop pages detect mobile user agents and redirect to `m/<page>.html`. Mobile pages have:
- **Top bar**: Fixed header with 🏠 home link, page title (flex:1 to push buttons left), ℹ info toggle, language toggle
- **Bottom tab bar**: Horizontally scrollable pill-style nav (48px height, no home item since it's in top-bar)
- **BMC banner**: Floating dismissible Buy Me a Coffee banner above tab bar (3s delay, sessionStorage persistence)
- Touch-optimized bottom sheets instead of hover tooltips

### Internationalization (i18n.js)
Central bilingual system (Hebrew/English). Key concepts:
- **Translation dict**: All UI strings keyed by ID, with `he` and `en` values
- **`data-i18n` attributes**: HTML elements get auto-translated via `applyTranslations()`
- **`renderNav(activePageId)`**: Generates the view-switcher nav bar on every page. The dashboard (`index.html`) uses `injectLangToggle()` instead (no nav bar)
- **`navViews` array**: Defines page order and hrefs for navigation. Order: home → geomap → tsne → sankey → scatter → dhondt → regional → irregular
- **Helper functions**: `i18n.partyName()`, `i18n.settlementName()`, `i18n.settlementMatches()`, `i18n.fmtNum()`
- **Language toggle**: Persisted in localStorage, fires `langchange` event

### Election 26 Feature Flag
Election 26 support is behind a URL feature flag: `?e26=1`. When active:
- `i18n.SHOW_E26` is `true` (exposed in public API)
- Each page conditionally adds election 26 buttons/options to its UI
- `renderNav()` propagates `?e26=1` to all nav links via `addE26()` helper
- Data files (`tsne_26.json`, `map_26.json`, `transfer_25_to_26.json`) must be generated first via `prepare_election_26.py`

### Settlement Profile Pages
URL pattern: `settlement.html?name=<settlement_name>` (URL-encoded Hebrew, normalized name)
- Loads all 5 map files (`map_21.json` through `map_25.json`) to show voting trends
- Loads `settlement_wiki.json` for Wikipedia data (thumbnail, description, extract)
- Loads `socioeconomic_clusters.json` and `station_coordinates.json`
- Desktop: search box, hero section, voting trends chart (Chart.js), party table + Leaflet mini-map (dots colored by winning party), sortable ballot table
- Mobile: has top-bar, trends chart, party table, and sortable ballot table (no map)
- Party colors use merged lookup from ALL elections (not just latest)
- Cross-page links: geomap popups, tsne tooltips, scatter tooltips all link to settlement profiles

### Party Profile Pages
URL pattern: `party.html?name=<canonical_hebrew_name>` (URL-encoded)
- 15 party families with per-election incarnations, merges, notes, and gaps
- PARTY_FAMILIES config duplicated in desktop `party.html` and mobile `m/party.html`
- Loads `wiki_official_results.json` for official per-party vote totals
- Leader photos from `map_*.json` party info `leader_image` field (e.g. `images/leaders/netanyahu.jpg`)
- Desktop: hero with leader photo + color bar, election history table (seats, votes, %, leader), trends chart, strongholds + mini-map, vote migration (from all_transfers.json)
- Mobile: hero with leader photo, election history table, trends chart, top 10 strongholds

### Social Preview (OG Tags)
All HTML files have `og:type`, `og:title`, `og:description`, `og:image`, and `twitter:card` meta tags. The OG image is at `site/og-image.png` (1200x630, generated by `generate_og_image.py`). The `og:image` URL must be absolute (`https://kolot-nodedim.netlify.app/og-image.png`).

### Visitor Counter
The dashboard pages (`index.html`, `m/index.html`) use counterapi.dev for visitor counting. Uses `sessionStorage` to avoid double-counting within a session. **URLs must have trailing slashes** or the API returns 301 which fails with CORS.

### Settlement Name Normalization
The CEC changed settlement name formatting between elections 22→23 (stripped hyphens, geresh, gershayim, parentheses). `generate_map_data.py` has `normalize_name()` that ensures consistent names across all elections. Key rules:
- Remove: `-`, `–`, `'`, `׳`, `"`, `״`, `(`, `)`
- Collapse multiple spaces, normalize `יי` → `י`
- `NAME_OVERRIDES` dict for special cases (e.g. `גולס` → `ג'וליס`)
- After regenerating tsne data, run `normalize_tsne_names.py` to apply same normalization
- After changing coordinates, run `normalize_coordinates.py`
- `settlement_wiki.json` keys must also be normalized

## Key Technical Details

### Ballot Matching Logic

When comparing elections, ballots are matched by `settlement_name|ballot_number`. Subdivided ballots (e.g., 14.1, 14.2) follow this logic:

- **Exact match first**: 14.1 matches 14.1
- **Fallback for .1 only**: 14.1 can match 14 if 14.1 doesn't exist in the other election
- **.2, .3, etc. do NOT fallback**: 14.2 only matches 14.2, never 14

This is implemented in:
- `site/scatter.html`: `getBaseKey()` function
- `generate_transfer_data.py`: `get_base_ballot_id()` function

### Data Formats

**tsne_*.json** (per election):
```json
{
  "parties": [{"name": "...", "symbol": "...", "color": "#..."}],
  "stations": [
    {"n": "settlement", "b": "ballot", "l": "location", "v": total_voters, "e": eligible, "t": turnout, "p": {"party": proportion}}
  ]
}
```

**map_*.json** (per election):
```json
{
  "election": {...},
  "parties": [...],
  "settlements": [
    {
      "name": "...", "lat": N, "lng": N, "voters": N, "eligible": N,
      "turnout": N, "ballotCount": N, "proportions": {...},
      "winningParty": "...", "cluster": N,
      "ballots": [
        {"b": "ballot_num", "v": voters, "e": eligible, "t": turnout, "l": "location", "p": {"party": pct}}
      ]
    }
  ],
  "stats": {"totalSettlements": N, "totalBallots": N, "totalVoters": N, "totalEligible": N, "totalLists": N, ...}
}
```

**transfer_*.json** (between elections):
```json
{
  "from_election": {...},
  "to_election": {...},
  "nodes_from": [...],
  "nodes_to": [...],
  "transfer_matrix": [[...]],
  "stats": {"common_precincts": N, "r_squared": 0.xx}
}
```

**settlement_wiki.json** (settlement → Wikipedia data):
```json
{
  "תל אביב יפו": {
    "title": "...", "description": "...", "extract": "...(max 500 chars)",
    "wiki_url": "https://he.wikipedia.org/wiki/...", "thumbnail": "https://..."
  }
}
```

**wiki_official_results.json** (per-party official vote totals):
```json
{
  "21": [
    {"name": "הליכוד", "seats": 35, "votes": 1140370},
    {"name": "כחול לבן", "seats": 35, "votes": 1125881}
  ]
}
```

### Generating Data

```bash
source venv/bin/activate

# Vote transfer matrices
python generate_transfer_data.py
cp data/transfer_*.json site/data/

# T-SNE clustering
python generate_tsne_data.py
python add_locations_to_tsne.py   # Adds venue names from ballot_locations_*.json
python normalize_tsne_names.py    # Normalize settlement names

# Geographic map data (reads tsne, applies normalization, counts lists from CSV)
python generate_map_data.py

# Wikipedia enrichment (rate-limited, ~3 min for 1100 settlements, resumes from cache)
python enrich_settlements_wikipedia.py

# Election 26 (all-in-one workflow)
python prepare_election_26.py          # Uses ballot25.csv as placeholder
python prepare_election_26.py --real-csv ballot26.csv  # With actual data
```

**IMPORTANT**: Scripts write to `data/`, but the web server reads from `site/data/`. Always copy generated files:
```bash
cp data/transfer_*.json site/data/
cp data/tsne_*.json site/data/
```
(Some scripts like `generate_map_data.py` and `enrich_settlements_wikipedia.py` write directly to `site/data/`)

The `l` (location/venue name) field in `tsne_*.json` is NOT generated by `generate_tsne_data.py`. It must be added separately by `add_locations_to_tsne.py`, which reads from `data/ballot_locations_*.json`.

### Statistical Zones & Socioeconomic Data

CBS 2011 Census statistical areas provide intra-city socioeconomic resolution. The pipeline:

```bash
source venv/bin/activate
python download_statistical_zones.py   # Load CBS 2011 GDB → match stations to zones
python process_statistical_zones.py    # Join CBS 2021 socioeconomic data → per-station mapping
```

**Key concepts:**
- **YISHUV_STAT**: Zone ID format = `settlement_code * 10000 + stat_area` (e.g. `30001335` = Jerusalem area 1335)
- **CBS 2011 boundaries**: From `statisticalareas_demography2019.gdb` (EPSG:2039 → WGS84 conversion)
- **CBS 2021 socioeconomic index**: Publication 1955, tables T12 (stat areas), T01 (local authorities), T07/T08 (regional localities)
- **Matching priority**: T12 exact stat area → T01 settlement-level fallback → T07/T08 regional fallback
- **Point-in-polygon**: Station coordinates matched to zone polygons via Shapely
- **Coverage**: ~31,550/31,590 stations get a cluster (99.87%)

**CRITICAL**: Must use CBS 2011 boundaries (not 2022 ArcGIS). The 2021 socioeconomic data is keyed to 2011 Census stat areas. Using 2022 boundaries only matches 67.6% of T12 zones; 2011 boundaries match 100%.

**Output files** (all write directly to `site/data/`):
- `statistical_zones.json` — compact zone data with centroids
- `statistical_zones_socioeconomic.json` — per-zone cluster/index/rank
- `station_zone_mapping.json` — station key → YISHUV_STAT
- `station_socioeconomic.json` — station key → `{zone, cluster}`

### Historical Elections (K16-K20)

Elections 16-20 (2003-2015) are downloaded via `download_historical_ballots.py` from the CEC CKAN API. Key differences from K21-K25:
- **Encoding**: UTF-8-BOM (not ISO-8859-8)
- **Ballot field**: `מספר קלפי` (not `קלפי`)
- **K16-K17 ballot numbering**: Uses x10 numbering (10, 20, 30...) — `ballot_number_divisor: 10` in party_config normalizes to 1, 2, 3...
- **K17 eligible voters**: `בזב` column is empty — abstention estimated from national totals
- **Abstention toggle disabled**: For transitions 16→17 and 17→18 (unreliable per-ballot eligible data)

### Geocoding Stations

Station coordinates are in `site/data/station_coordinates.json`. Sources by priority:
- `manual`: Hand-corrected coordinates (when automated sources were wrong)
- `google_venue`: Precise venue coords from Google Places API (`fix_venues_google.py`)
- `venue`: Venue coords from Nominatim (`geocode_with_amenities.py`)
- `settlement`: Fallback to settlement center coordinates
- Google API key: set `GOOGLE_MAPS_API_KEY` env var (never commit the key)
- **After fixing coordinates**: Re-run `download_statistical_zones.py` + `process_statistical_zones.py` to update zone assignments

### Party Configuration

`party_config.py` contains the `ELECTIONS` dict with metadata for each election (21-26):
- Election name (Hebrew + English), date, file path, encoding
- Eligible voters, votes cast, turnout percentage
- Major parties: symbols, names, seats
- Reference: `wikipages/` folder has Wikipedia HTML with correct party info per election

## Visualization Pages

### index.html (Dashboard)
- Landing page with animated hero stats and card grid linking to all visualizations
- Stats: elections (25), lists, settlements, ballots, eligible voters, voted, visitors — all with rolling number animation
- Stats loaded from all 5 map_*.json files (max ballots across elections, latest for rest)
- Visitor counter integrated as regular stat (counterapi.dev)
- Archive photos: 12 historical NLI images in `site/images/`, 2 randomly chosen per page load, flanking the 9 view cards
- Credit: Dan Hadani Archive, Pritzker Family National Photography Collection, National Library of Israel
- Photos hidden on screens < 1200px
- Discussions link next to language toggle
- No nav bar (uses `injectLangToggle()` only)

### sankey.html (Vote Transfer Flow)
- Shows vote flow between consecutive elections as Sankey diagram (K16→K17 through K24→K25)
- Uses `sankey.js` for rendering
- Data: `transfer_*.json` and `all_transfers.json`
- **Abstention toggle**: Shows "did not vote" pseudo-party (לא הצביעו) using `*_abstention.json` files
- Abstention disabled for K16→K17 and K17→K18 (unreliable per-ballot eligible voter data)

### tsne.html (Ballot Clustering)
- T-SNE clustering of ballot boxes by voting patterns
- Color modes: turnout, party support, socioeconomic cluster
- Socioeconomic data from CBS 2021 index (1-10 scale), per statistical area within cities
- `getStationCluster(station)` returns `{cluster, statArea}` — per-station lookup first, settlement-level fallback
- Tooltips show cluster + full YISHUV_STAT zone ID (e.g. "30001335")

### geomap.html (Geographic Map)
- Leaflet map with clustered ballot station markers
- Color by party support, turnout, or socioeconomic cluster
- Per-station socioeconomic coloring (different ballots in same city show different clusters)
- `getStationCluster(station)` same pattern as tsne — per-station first, settlement fallback
- Settlement search with autocomplete
- Uses CartoDB Positron tiles with CSS `brightness(0.7)` for dark theme

### scatter.html (Party Comparison)
- Compare party X support vs party Y support across ballots
- Can compare same or different elections
- Settlement filter with autocomplete search
- Units toggle: percentages vs absolute votes

### dhondt.html (Seat Calculator)
- Interactive Bader-Ofer (modified D'Hondt) seat calculator
- Adjust vote counts to see seat changes

### irregular.html (Anomaly Detection)
- Identifies statistically unusual ballot boxes

### regional.html (Regional Elections Simulator)
- Voronoi-based regional election simulation with D'Hondt allocation

### settlement.html (Settlement Profile)
- Per-settlement deep dive with Wikipedia info, voting trends, party breakdown
- URL parameter: `?name=<settlement_name>`

## Paper

The `paper/` directory is a **separate git repo** (`harelc/elections-paper`) embedded in this repo. It has its own remote, branch (`main`), and commit history. Commit and push it independently:

```bash
# Compile the paper (uses tectonic, NOT pdflatex/latexmk)
cd paper && tectonic paper.tex

# Commit paper changes (separate repo!)
cd paper && git add -A && git commit -m "..." && git push
# Then update the submodule ref in the parent:
cd .. && git add paper && git commit -m "Update paper submodule"

# Key files:
# paper/paper.tex         — Main paper source
# paper/references.bib    — Bibliography
# paper/figures/           — Generated figures (PDF)
# paper/generate_figures.py — Script to regenerate figures
# paper/bootstrap_analysis.py — Bootstrap confidence interval analysis
```

## Common Issues

1. **Browser cache**: After regenerating data, hard refresh (Cmd+Shift+R) or use incognito
2. **Python environment**: Always use `source venv/bin/activate` for generate scripts
3. **Data sync**: Scripts write to `data/`, web serves from `site/data/` — copy after generating
4. **Map tiles**: Using CartoDB Positron (no auth required, unlike Stadia Maps)

## Election IDs

- 16: January 2003
- 17: March 2006
- 18: February 2009
- 19: January 2013
- 20: March 2015
- 21: April 2019
- 22: September 2019
- 23: March 2020
- 24: March 2021
- 25: November 2022
- 26: TBD (feature-flagged behind `?e26=1`)
