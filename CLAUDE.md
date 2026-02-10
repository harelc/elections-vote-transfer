# Elections Vote Transfer Project

Interactive visualizations for analyzing Israeli Knesset election data, showing vote transfers between elections, party support patterns, and ballot-level analysis.

Live site: https://kolot-nodedim.netlify.app/

## Project Structure

```
├── ballot*.csv                    # Raw election data per election (21-26), in project root
├── data/                          # Processed data files
│   └── ballot_locations_*.json    # Ballot venue names (scraped)
├── party_config.py                # Election metadata, party names/symbols/seats per election
├── generate_transfer_data.py      # Generates vote transfer matrices (cvxpy optimization)
├── generate_tsne_data.py          # Generates T-SNE clustering data
├── generate_map_data.py           # Generates geographic map data per election (with name normalization)
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
│   ├── discussions.html           # Giscus discussions page
│   ├── styles.css                 # Shared CSS (desktop)
│   ├── i18n.js                    # Internationalization (Hebrew/English), nav rendering
│   ├── i18n.css                   # RTL/LTR + language toggle styles
│   ├── og-image.png               # Social preview image (1200x630)
│   ├── favicon.svg                # Site favicon
│   ├── m/                         # Mobile-optimized pages
│   │   ├── index.html             # Mobile dashboard
│   │   ├── sankey.html            # Mobile Sankey
│   │   ├── tsne.html              # Mobile T-SNE
│   │   ├── geomap.html            # Mobile geographic map
│   │   ├── scatter.html           # Mobile scatter plot
│   │   ├── dhondt.html            # Mobile D'Hondt calculator
│   │   ├── regional.html          # Mobile regional simulator
│   │   ├── settlement.html        # Mobile settlement profile
│   │   ├── discussions.html       # Mobile discussions
│   │   └── styles.css             # Shared CSS (mobile)
│   └── data/                      # JSON data for frontend (source of truth)
│       ├── transfer_*.json        # Vote transfer matrices between elections
│       ├── tsne_*.json            # T-SNE clustering data per election
│       ├── map_*.json             # Geographic/settlement data per election
│       ├── all_transfers.json     # Combined transfer data for all election pairs
│       ├── settlement_wiki.json   # Wikipedia enrichment data per settlement
│       ├── station_coordinates.json # Geocoded ballot station coordinates
│       └── socioeconomic_clusters.json # CBS socioeconomic cluster per settlement
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
Every visualization has two HTML files: `site/<page>.html` (desktop) and `site/m/<page>.html` (mobile). Desktop pages detect mobile user agents and redirect to `m/<page>.html`. Mobile pages have bottom tab navigation and touch-optimized bottom sheets instead of hover tooltips.

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
- Mobile: simplified version without map or ballot table
- Party colors use merged lookup from ALL elections (not just latest)
- Cross-page links: geomap popups, tsne tooltips, scatter tooltips all link to settlement profiles

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

### Geocoding Stations

Station coordinates are in `site/data/station_coordinates.json`. Sources by priority:
- `google_venue`: Precise venue coords from Google Places API (`fix_venues_google.py`)
- `venue`: Venue coords from Nominatim (`geocode_with_amenities.py`)
- `settlement`: Fallback to settlement center coordinates
- Google API key: set `GOOGLE_MAPS_API_KEY` env var (never commit the key)

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
- Discussions link next to language toggle
- No nav bar (uses `injectLangToggle()` only)

### sankey.html (Vote Transfer Flow)
- Shows vote flow between consecutive elections as Sankey diagram
- Uses `sankey.js` for rendering
- Data: `transfer_*.json` and `all_transfers.json`

### tsne.html (Ballot Clustering)
- T-SNE clustering of ballot boxes by voting patterns
- Color modes: turnout, party support, socioeconomic cluster
- Socioeconomic data from CBS (1-10 scale)
- Small settlements mapped to regional councils for coverage

### geomap.html (Geographic Map)
- Leaflet map with clustered ballot station markers
- Color by party support or turnout
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

## Common Issues

1. **Browser cache**: After regenerating data, hard refresh (Cmd+Shift+R) or use incognito
2. **Python environment**: Always use `source venv/bin/activate` for generate scripts
3. **Data sync**: Scripts write to `data/`, web serves from `site/data/` — copy after generating
4. **Map tiles**: Using CartoDB Positron (no auth required, unlike Stadia Maps)

## Election IDs

- 21: April 2019
- 22: September 2019
- 23: March 2020
- 24: March 2021
- 25: November 2022
- 26: TBD (feature-flagged behind `?e26=1`)
