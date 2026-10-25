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
├── party_config.py                # Election metadata, party names/symbols/seats per election (16-26)
├── generate_transfer_data.py      # Generates vote transfer matrices (cvxpy optimization)
├── generate_tsne_data.py          # Generates T-SNE clustering data
├── generate_map_data.py           # Generates geographic map data per election (with name normalization)
├── generate_metrics_data.py       # Pedersen volatility + HHI → site/data/metrics.json
├── generate_irregularities_data.py # Unusual-ballot scores → site/data/irregularities_*.json
├── generate_suspects_data.py      # Crosswalk-paired regression residuals → site/data/suspects_26.json (k26 pane)
├── generate_settlement_sectors.py # Settlement sector taxonomy (form/population/WB/Haredi) → site/data/settlement_sectors.json
├── generate_settlement_districts.py # Adds district (מחוז) + subdistrict (נפה) per settlement to settlement_sectors.json (Population Authority locality list on data.gov.il: settlement code → נפה → fixed CBS district mapping; 100% code-matched)
├── generate_command_center_data.py # Twelve Knessets + factoids + bellwether + gated nowcast → site/data/command_center_26.json (k26 panes)
├── download_statistical_zones.py  # Loads CBS 2011 GDB, matches stations to zones via point-in-polygon
├── process_statistical_zones.py   # Joins CBS socioeconomic data to zones, creates station mapping
├── download_historical_ballots.py # Downloads K16-K20 ballot CSVs from CEC CKAN API
├── normalize_tsne_names.py        # One-shot: normalize settlement names in tsne_*.json
├── normalize_coordinates.py       # One-shot: normalize settlement names in station_coordinates.json
├── add_locations_to_tsne.py       # Adds venue names to tsne_*.json from ballot_locations
├── enrich_settlements_wikipedia.py # Fetches Wikipedia summaries for settlements
├── simulate_election_26.py        # Builds synthetic ballot26.csv from K25 + transfer matrix
├── prepare_election_26.py         # Workflow script to generate all election 26 data
├── prepare_fraud_sim.py           # Builds fraud_sim_24_25.json / fraud_sim_25_26.json
├── estimate_alpha.py              # Dirichlet α estimates per historical transition
├── generate_og_image.py           # Generates OG social preview image (Pillow)
├── geocode_with_amenities.py      # Geocodes ballot stations via Nominatim
├── fix_venues_google.py           # Precise geocoding via Google Places API
├── requirements.txt               # Python dependencies
├── venv/                          # Python virtual environment
├── wikipages/                     # Wikipedia HTML files with party info per election
├── elections-paper/               # Nested git repo (harelc/elections-paper) — not a submodule
├── site/                          # Static website (served directly)
│   ├── index.html                 # Landing page dashboard
│   ├── sankey.html                # Sankey vote flow diagram (was index.html)
│   ├── sankey.js                  # Sankey visualization logic
│   ├── sankey-explainer.html      # Click-through explainer of the transfer-matrix solver
│   ├── tsne.html                  # T-SNE ballot clustering visualization
│   ├── geomap.html                # Geographic map with ballot station markers
│   ├── scatter.html               # Party support scatter plot (X vs Y axis)
│   ├── dhondt.html                # D'Hondt/Bader-Ofer seat allocation calculator
│   ├── irregular.html             # Irregular ballot analysis
│   ├── fraud-sim.html             # Election fraud detection simulator (K24→K25, K25→K26)
│   ├── k26.html                   # K26 information center (desktop-only, full-width; embeds dhondt.html?embed=1)
│   ├── regional.html              # Regional elections simulator (Voronoi + D'Hondt)
│   ├── voronoi-explainer.html     # Click-through explainer of Voronoi districting
│   ├── settlement.html            # Settlement profile page (?name=...)
│   ├── party.html                 # Party profile page (?name=...)
│   ├── rankings.html              # Settlement volatility (Pedersen) + party HHI
│   ├── methodology.html           # Written methodology (convex solver, R², Dirichlet α)
│   ├── primer.html                # Illustrated intro to K25 election data (D3 chapters)
│   ├── animation.html             # Full-screen animated Sankey across K16→K25
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
│   ├── m/                         # Mobile-optimized pages (not every desktop page has a twin)
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
│   │   ├── rankings.html          # Mobile rankings
│   │   ├── methodology.html       # Mobile methodology
│   │   ├── discussions.html       # Mobile discussions
│   │   └── styles.css             # Shared CSS (mobile)
│   └── data/                      # JSON data for frontend (source of truth)
│       ├── transfer_*.json        # Vote transfer matrices between elections
│       ├── transfer_*_abstention.json # Same matrices with "did not vote" pseudo-party
│       ├── tsne_*.json            # T-SNE clustering data per election
│       ├── map_*.json             # Geographic/settlement data per election (16-26)
│       ├── all_transfers.json     # Combined transfer data for all election pairs
│       ├── metrics.json           # Pedersen volatility + HHI (from generate_metrics_data.py)
│       ├── irregularities_*.json  # Unusual-ballot scores per election
│       ├── fraud_sim_24_25.json / fraud_sim_25_26.json
│       ├── primer_25.json / sankey_primer.json  # Primer / explainer source data
│       ├── alpha_estimates.json   # Dirichlet α per historical transition
│       ├── settlement_wiki.json   # Wikipedia enrichment data per settlement
│       ├── settlement_names_en.json # English settlement names
│       ├── wiki_official_results.json # Official per-party vote totals per election (from Wikipedia)
│       ├── station_coordinates.json # Geocoded ballot station coordinates
│       ├── socioeconomic_clusters.json # CBS socioeconomic cluster per settlement
│       ├── statistical_zones.json     # CBS 2011 statistical area boundaries (centroids + metadata)
│       ├── statistical_zones_socioeconomic.json # Per-zone socioeconomic cluster/index
│       ├── station_zone_mapping.json  # Ballot station → statistical zone (YISHUV_STAT)
│       ├── settlement_sectors.json   # Per-settlement sector taxonomy (form/population/WB/Haredi)
│       ├── command_center_26.json    # Twelve Knessets + factoids + bellwether + nowcast (k26 panes)
│       └── station_socioeconomic.json # Per-station socioeconomic cluster + zone ID
```

## Running the Project

```bash
# Start local server
cd site && python3 -m http.server 8888
# Access at http://localhost:8888/

# Desktop pages served at root, mobile at /m/
# Pages with an m/ twin auto-redirect to /m/ on mobile devices
```

## Architecture

### Desktop vs Mobile
Most visualizations have two HTML files: `site/<page>.html` (desktop) and `site/m/<page>.html` (mobile). Desktop pages detect mobile user agents and redirect to `m/<page>.html`. Mobile pages have:
- **Top bar**: Fixed header with 🏠 home link, page title (flex:1 to push buttons left), ℹ info toggle, language toggle
- **Bottom tab bar**: Horizontally scrollable pill-style nav (48px height, no home item since it's in top-bar)
- **BMC banner**: Floating dismissible Buy Me a Coffee banner above tab bar (3s delay, sessionStorage persistence)
- Touch-optimized bottom sheets instead of hover tooltips

**Desktop-only** (no `m/` twin; some are linked from the mobile dashboard to the desktop URL): `primer.html`, `animation.html`, `fraud-sim.html`, `sankey-explainer.html`, `voronoi-explainer.html`. Exception: `k26.html` redirects phone user agents to `m/index.html` and is not linked from the mobile dashboard.

### Internationalization (i18n.js)
Central bilingual system (Hebrew/English). Key concepts:
- **Translation dict**: All UI strings keyed by ID, with `he` and `en` values
- **`data-i18n` attributes**: HTML elements get auto-translated via `applyTranslations()`
- **`renderNav(activePageId)`**: Generates the view-switcher nav bar on every page. The dashboard (`index.html`) uses `injectLangToggle()` instead (no nav bar)
- **`navViews` array**: Main nav row. Order: home → geomap → tsne → sankey → scatter → dhondt → regional → irregular → fraud-sim
- **`extraLinks` row** (`.nav-extras` below the main nav): settlement → party → rankings → methodology → discussions + language toggle
- **Helper functions**: `i18n.partyName()`, `i18n.settlementName()`, `i18n.settlementMatches()`, `i18n.fmtNum()`
- **Language toggle**: Persisted in localStorage, fires `langchange` event

### Election 26 Feature Flag
Election 26 is **on by default** (`i18n.SHOW_E26`); `?e26=0` is the explicit opt-out (persisted in localStorage). URLs are clean — no `e26=1` argument is needed or propagated:
- Each page conditionally adds election 26 buttons/options to its UI **and makes K26 the default selected election/transition** (sankey/dhondt/geomap/tsne/regional)
- `renderNav()` propagates only the opt-out (`?e26=0`) to nav links via `addE26()` helper
- Data files (`tsne_26.json`, `map_26.json`, `transfer_25_to_26.json`) must be generated first via `prepare_election_26.py`

#### Simulated K26 scenario
K26 is a **simulated scenario** — `ballot26.csv` is generated by `simulate_election_26.py` from `ballot25.csv`. Seat map is calibrated to [Madad 120](https://madad120.geva.workers.dev/) (7 Sep 2026). CEC letter-symbols are still provisional until the official list harvest; remap after https://www.gov.il/he/pages/candidates-lists-26?chapterIndex=5 fills in.

##### Harvesting the official K26 list (including tiny parties)
CEC publishes the full submitted lists (every list, not just majors) on **7–8 Sep 2026**:
https://www.gov.il/he/pages/candidates-lists-26?chapterIndex=5
(`chapterIndex=5` = "רשימות המועמדים לכנסת"). As of 7 Sep the chapter is still a placeholder.

Sibling chapters on the same page (useful on harvest day):
- taken vs available letter-symbols
- approved ballot slips (פתקי הצבעה)
- surplus agreements (הסכמי עודפים)
- disqualification requests

Harvest into:
1. `party_config.py` `PARTIES` (and `PARTY_OVERRIDES` for `(26, symbol)` as needed) — **all** symbols, including below-threshold lists. Historical tiny parties live in the same dict, grouped by election in comments.
2. `party_config.py` `ELECTIONS['26']['major_parties']` — threshold-relevant lists only (symbols, names, seats).
3. `simulate_election_26.py` `E26_PARTIES` — currently the Madad 120 majors; after harvest, add every letter-symbol as a CSV column. Tiny K25 votes are today collapsed into `_small` and dumped onto the ballot's dominant party; K26 tiny lists should exist as columns even if the transfer matrix sends them ~0.
4. `PARTY_FAMILIES` in `party.html` / `m/party.html` if new families appear.
5. `prepare_fraud_sim.py` `BLOC_DEFINITIONS['26']` and Sankey `INFO_OVERRIDES` in `sankey.js`.

`generate_map_data.py` `count_lists()` counts CSV columns after `כשרים`, so a full-column `ballot26.csv` is what makes the dashboard "lists" stat correct.

##### Calibrating seats from polling (Madad 120)
The **hidden** generating process is `TRANSFER_MATRIX` + `ROW_TURNOUT` in `simulate_election_26.py`. After simulation we *re-estimate* a transfer matrix from matched ballots (`generate_transfer_data.py`) for the Sankey — so the hidden matrix and the published matrix are not the same object.

Treat [Madad 120](https://madad120.geva.workers.dev/) as the target seat map (weighted-poll forecast, updated ~daily). Calibration loop:

1. Lock `E26_PARTIES` to letter-symbols / names (provisional until CEC harvest).
2. Read Madad 120 `#parties` center forecast (and `#polls` table). Optionally `#vote-share` for raw % before Bader-Ofer.
3. Tune `TRANSFER_MATRIX` (who goes where) and `ROW_TURNOUT` (mobilization) so simulated national totals, after Bader-Ofer, match that center. Cross-bloc leakage should stay small: Madad 120 currently has &lt;1% undecided *between* blocs; most residual is threshold / turnout.
4. `python simulate_election_26.py` → `prepare_election_26.py --real-csv ballot26.csv` → copy transfer/tsne/map; sync hardcoded totals (dhondt, wiki_official_results, party_config).

Madad 120 center forecast as of **7 Sep 2026** (50 days out; lists close 8 Sep 22:00). Blocs: coalition **50** (45–55), opposition **55** (50–59), Joint List **8**, Ra'am **5**. Per-list center vs current sim:

| List | Madad center | Range | Sim seats |
|---|---|---|---|
| ישר (Eisenkot) | 23 | 20–26 | 22 |
| הליכוד | 21 | 19–23 | 20 |
| ביחד (Bennett) | 14 | 12–16 | 13 |
| הדמוקרטים | 9 | 8–11 | 9 |
| ישראל ביתנו | 8 | 7–9 | 8 |
| המשותפת (Hadash–Ta'al–Balad) | 8 | 7–9 | 8 |
| יהדות התורה | 8 | 7–8 | 8 |
| ש״ס | 7 | 6–8 | 7 |
| עוצמה יהודית | 7 | 6–8 | 7 |
| הציונות הדתית + זהות | 5 | 4–6 | 5 |
| רע״ם | 5 | 4–6 | 5 |
| עמך ישראל (Winter) | 0 / 4–5 | ~48% pass | 4 |
| המילואימניקים והכלכלית | 0 / 4–5 | ~52% pass | 4 |
Both threshold lists are included as passing (4 each); 1 seat shaved from Yashar / Likud / Beyachad so the 120 still add up. Turnout intent on Madad: opposition 82% / coalition 77% / Arab 75%.

Provisional majors in `simulate_election_26.py` (`E26_PARTIES`):
ישר, הליכוד, ביחד, הדמוקרטים, ישראל ביתנו, הרשימה המשותפת, יהדות התורה, ש״ס, עוצמה יהודית, הציונות הדתית, רע״ם, עמך ישראל, המילואימניקים והכלכלית (plus sub-threshold הציבור החרדי, נעם)

כחול לבן (Gantz) is **not running** in K26: no column in `ballot26.csv`, no `(26, 'כן')` override, not in any K26 bloc or seat list. Its former matrix cells were split between ישר and המילואימניקים והכלכלית.

Simulation knobs:
- `TRANSFER_MATRIX`: per K25 source party → K26 destination distribution (rows must sum to 1.0)
- `ROW_TURNOUT`: per-source mobilization factor (<1 demobilized, >1 mobilized)
- `POP_GROWTH = 1.075`: global multiplier modeling ~7.5% growth in eligible voters (Nov 2022 → Oct 2026)
- Per-ballot Dirichlet noise with `alpha=55` (concentration). `alpha = α₀ = effective sample size`; var = p(1−p)/(α+1)
- Random seed 42 for reproducibility

The convex solver in `generate_transfer_data.py` recognizes the 25→26 transition (`POP_GROWTH_PER_TRANSITION` dict) and uses `row_sum = 1.075` instead of 1.0 in the constraint — otherwise the matrix can't fit the population-grown K26 totals.

Hardcoded K26 totals appear in 3 places that must stay in sync when re-tuning:
1. `site/dhondt.html` parties26 array (+ `site/m/dhondt.html`)
2. `site/data/wiki_official_results.json` `"26"` entry (used by sankey side bar legend; has `_26_note` sibling key flagging simulation)
3. `party_config.py` ELECTIONS['26'] major_parties seats list

Current synced map (Oct 2026 recalibration): Yashar 23 / Likud 18 / Beyachad 15 / Democrats 8 / YB 8 / Joint List 8 / UTJ 8 / Shas 9 / Otzma 7 / RZ 6 / Ra'am 6 / Amcha 0 (below threshold, ~2.2%) / HaMiluimnikim & HaKalkalit 4. Yashar's colour is `#eab308` (golden yellow; the old teal clashed with the Joint List). Invalid ballots are a flat 0.2% of voters per box (`INVALID_SHARE` in `simulate_election_26.py`). Official K26 surplus agreements: Yisrael Beytenu+Beyachad, Ra'am+Joint List, RZ+Likud, UTJ+Shas, Democrats+Yashar (Otzma has none). Defined in `simulate_election_26.py` / `k26_live.py` `SURPLUS_AGREEMENTS`, `agreements26` in both dhondt pages, and `site/data/turnout_ballots_26.json` (regenerate via `generate_turnout_sim.py`).

Set `min_flow_threshold=15000` in `generate_transfer_data.py` to hide solver multicollinearity noise (~1% spurious cells) from sankey. `sankey.js` also drops nodes with zero remaining flows.

### Settlement Profile Pages
URL pattern: `settlement.html?name=<settlement_name>` (URL-encoded Hebrew, normalized name)
- Loads all 10 map files (`map_16.json` through `map_25.json`) to show voting trends
- Loads `settlement_wiki.json` for Wikipedia data (thumbnail, description, extract)
- Loads `socioeconomic_clusters.json` and `station_coordinates.json`
- Desktop: search box, hero section, voting trends chart (Chart.js), party table + Leaflet mini-map (dots colored by winning party), sortable ballot table
- Mobile: has top-bar, trends chart, party table, and sortable ballot table (no map)
- Party colors use merged lookup from ALL elections (not just latest)
- Cross-page links: geomap popups, tsne tooltips, scatter tooltips all link to settlement profiles

### Party Profile Pages
URL pattern: `party.html?name=<canonical_hebrew_name>` (URL-encoded)
- ~23 party families with per-election incarnations, merges, notes, and gaps (including historical: Kadima, Shinui, Gil, Kulanu, Yisrael BaAliyah; K26: Beyachad / ישר)
- PARTY_FAMILIES config duplicated in desktop `party.html` and mobile `m/party.html`
- Loads `wiki_official_results.json` for official per-party vote totals
- Leader photos from `map_*.json` party info `leader_image` field (e.g. `images/leaders/netanyahu.jpg`)
- Desktop: hero with leader photo + color bar, election history table (seats, votes, %, leader), trends chart, strongholds + mini-map, vote migration (from all_transfers.json)
- Mobile: hero with leader photo, election history table, trends chart, top 10 strongholds

### Social Preview (OG Tags)
All HTML files have `og:type`, `og:title`, `og:description`, `og:image`, and `twitter:card` meta tags. The OG image is at `site/og-image.png` (1200x630, generated by `generate_og_image.py`). The `og:image` URL must be absolute (`https://kolot-nodedim.netlify.app/og-image.png`).

#### Settlement Name Normalization
The CEC changed settlement name formatting between elections 22→23 (stripped hyphens, geresh, gershayim, parentheses). `generate_map_data.py` has `normalize_name()` that ensures consistent names across all elections. Key rules:
- Remove: `-`, `–`, `'`, `׳`, `"`, `״`, `(`, `)`
- Collapse multiple spaces, normalize `יי` → `י`
- `NAME_OVERRIDES` dict for special cases (e.g. `גולס` → `ג'וליס`)
- `MERGED_NAMES` (part of `NAME_OVERRIDES`): 41 settlements the CEC spells without a separator in K23–K25 (`אום אלפחם`, `בית יצחקשער חפר`, …) → spaced form used in K16–K22 and K26. `normalize_tsne_names.py`, `normalize_coordinates.py` and `generate_metrics_data.py` import it; check new elections for spacing-only splits across `map_*.json`
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
- `site/geomap.html` & `site/m/geomap.html`: `getComparePct()` function (party comparison mode)
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
python generate_map_data.py # all elections
python generate_map_data.py --elections 26 # just these

# Wikipedia enrichment (rate-limited, ~3 min for 1100 settlements, resumes from cache)
python enrich_settlements_wikipedia.py

# Rankings metrics (Pedersen + HHI)
python generate_metrics_data.py

# Irregular-ballot scores
python generate_irregularities_data.py

# Fraud-sim payloads (after tsne + transfer exist for those years)
python prepare_fraud_sim.py

# Election 26 (simulated scenario workflow)
python simulate_election_26.py                          # generate ballot26.csv (alpha=55, seed=42)
python prepare_election_26.py --real-csv ballot26.csv   # run tsne/transfer/map for K26
python prepare_fraud_sim.py                             # refresh fraud_sim_25_26.json
# After re-tuning the matrix, also refresh hardcoded K26 totals in:
#   site/dhondt.html, site/m/dhondt.html, site/data/wiki_official_results.json, party_config.py
```

**IMPORTANT**: Scripts write to `data/`, but the web server reads from `site/data/`. Always copy generated files:
```bash
cp data/transfer_*.json site/data/
cp data/tsne_*.json site/data/
```
(Some scripts like `generate_map_data.py` and `enrich_settlements_wikipedia.py` write directly to `site/data/`)

**CRITICAL**: The `l` (location/venue name) field in `tsne_*.json` is NOT generated by `generate_tsne_data.py`. It must be added separately by `add_locations_to_tsne.py`, which reads from `data/ballot_locations_*.json`. If you regenerate tsne data without re-running `add_locations_to_tsne.py`, station search by venue name will break (the `l` field will be missing).

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

`party_config.py` contains the `ELECTIONS` dict with metadata for each election (16-26):
- Election name (Hebrew + English), date, file path, encoding
- Eligible voters, votes cast, turnout percentage
- Major parties: symbols, names, seats
- Reference: `wikipages/` folder has Wikipedia HTML with correct party info per election

## Visualization Pages

### index.html (Dashboard)
- Landing page with animated hero stats and card grid linking to all visualizations
- Stats: elections, lists, settlements, ballots, eligible voters, voted — all with rolling number animation
- Stats loaded from map_*.json (16–26; latest map for the totals)
- Dashboard cards (13): primer, geomap, tsne, sankey, animation, scatter, settlement, party, dhondt, regional, irregular, fraud-sim, rankings
- Header extras: methodology + discussions next to language toggle
- Footer: CC BY-NC-SA 4.0, GitHub, Buy Me a Coffee
- Archive photos: 12 historical NLI images in `site/images/`, 2 randomly chosen per page load, flanking the view cards
- Credit: Dan Hadani Archive, Pritzker Family National Photography Collection, National Library of Israel
- Photos hidden on screens < 1200px
- No nav bar (uses `injectLangToggle()` only)

### primer.html (Illustrated Intro)
- Click-through D3 chapters on K25 public data (desktop-only; mobile dashboard links to the desktop page)
- Chapters: turnout totals → ballot geography → ballot size → turnout distribution → settlement 9999 double envelopes → lists running vs threshold → threshold cliff → party-size buckets → Bader-Ofer / surplus agreements
- Last "next" lands on the home page
- Data: `primer_25.json`

### animation.html (Multi-election Sankey Film)
- Full-screen autoplay Sankey across K16→K25 (9 transitions), using `all_transfers.json` + `wiki_official_results.json`
- Keyboard / swipe / play-pause; also an `animation.mp4` recording for OG/Twitter player tags
- Desktop-only (mobile dashboard links to it)

### sankey.html (Vote Transfer Flow)
- Shows vote flow between consecutive elections as Sankey diagram (K16→K17 through K24→K25; K25→K26 by default)
- Uses `sankey.js` for rendering; nodes with zero remaining flows are dropped
- Data: `transfer_*.json` and `all_transfers.json`
- **Abstention toggle**: Shows "did not vote" pseudo-party (לא הצביעו) using `*_abstention.json` files
- Abstention disabled for K16→K17 and K17→K18 (unreliable per-ballot eligible voter data)
- Link to `sankey-explainer.html` (click-through visual of T, row-sum constraint, least squares, R²)

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
- **Party support comparison mode**: When a party is selected, a row of election pills appears below the legend. Clicking one loads the comparison election's tsne data and shows a diverging bichromatic scale (orange = lost support, teal = gained support, clamped ±20%). Party matching across elections uses the party **symbol** (not name). Ballot matching uses `settlement|ballot` key with `.1` suffix fallback. State: `compareElection`, `compareData`, `compareLookup`, `compareCache` (cached fetches). Tooltips/popups show diff with both election percentages. Clusters show weighted average diff.

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
- Data: `irregularities_*.json` from `generate_irregularities_data.py`

### fraud-sim.html (Election Fraud Detection Simulator)
- Interactive fraud detector sandbox for K24→K25 (real data) and K25→K26 (simulated scenario)
- **Fraud injection**: Parametric controls inject synthetic ballot-level fraud — select target settlement, number of ballots, intervention strength (% of ballot votes to reassign)
- **Attack scenarios**: Predefined templates for party-to-party fraud (e.g., Likud→Shas redirections, bloc-to-bloc shifts)
- **Multiple detectors**: Geo (geographic isolation), manifold (t-SNE neighbor distance), matched-filter (1D variance detection)
- **Portfolio fusion**: Combines detector scores via weighted combination; optimizable threshold shown on dynamic ROC curve with AUC
- **Output**: Ranked ballot list with before/after vote distributions, seat-equivalent impact, per-detector anomaly scores
- **Druze exclusion**: 14 specified Druze settlements excluded by default (settlement-level checkbox to re-include)
- **Visualization modes**: ROC plot (dual curves for current vs population level), side-by-side tampered ballot comparison
- **First-time intro modal**: Explains concepts (detector types, fraud scenarios, ROC interpretation)
- **Default state**: K24→K25 transition, top-100 ballots, 400-ballot injection, 17% intervention strength

### k26.html (K26 Information Center)
- Full-width desktop "Gemara" layout: votes+hemicycle and surplus agreements in the start margin, turnout-in-strongholds + most-suspicious-ballots in the end margin, and a central stage switching between Sankey 25→26, geomap and the seat calculator (the ballot-distribution/t-SNE stage pill is hidden — panel and `renderTsne()` kept in the code, remove `hidden` from its tab button to restore)
- The calculator stage embeds the original `dhondt.html?embed=1` (embed mode hides its header/footer/election selector; the pane has its own reset button; the frame auto-fits its content height)
- Election-night count banner: driven by `site/data/k26_status.json` — when `kind` is `partial`/`official` it shows ballots counted out of the roster, percentage, remaining and update time; seats from `wiki_official_results.json`, MK names from `data/k26_mks.json` (CEC lists, gov.il)
- Desktop-only: phone user agents are redirected to `m/index.html`, and the mobile dashboard does not link here
- Extras (from `site/data/command_center_26.json`, built by `generate_command_center_data.py`): rotating factoid ticker under the count banner; "על הקצה" bubble list in the votes pane (per-list last-in/first-out candidates + votes-to-flip, same marginal math as the dhondt seat-block histogram, allocator ported into the page); gated nowcast of the uncounted ballots in the start margin — moving to the central stage as the auto-activated tab while the count is partial, and the Sankey stage carries the same gate (closed: gate status instead of a diagram; open: a pointer to the nowcast, inside which מעברי הקולות החזויים — predicted vote transfers, never called a Sankey — are drawn together with the seat nowcast from the nowcast matrix applied to the full roster as diag(origin totals) @ T, flows <15,000 hidden as in the published diagram; per-box outer(source shares, box-average destination) was tried and smeared every source across every destination) (gate checks matched ballots / counted K25 share / R² / composition TVD / per-source origin votes — no Level-1 bloc stage; uncounted boxes predicted from their K25 crosswalk source through the **analyzed** transfer matrix, never the simulation's hidden matrix; Monte-Carlo seat distributions (full per-party seat histogram in the JSON) use the empirical 24→25 Dirichlet α plus an aggregate estimator jitter that shrinks as the counted share grows, and are drawn in the nowcast as colour-fade density strips (party-colour intensity = share of completions at that seat count); in simulated mode it runs as a labelled rehearsal on a deliberately skewed mask — Haredi ballots (Haredi localities + ballots whose K25 twin voted majority UTJ/Shas) almost entirely uncounted, ~58% counted elsewhere — with the convex design refit on the counted subset); "A Knesset for every tribe and district" pane (formerly Twelve Knessets) in the centre column under the geomap, with clickable slice cards + per-slice hemicycle (19 slices: 12 sector slices — kibbutzim, moshavim, community settlements, cities, WB settlements, Arab/Bedouin/Druze localities, Haredi localities, socioeconomic clusters 1–3, 4–7 and 8–10 — plus the 7 CBS districts/area from `settlement_sectors.json` district field — each re-allocated with seats inside the slice; slices from `settlement_sectors.json`, never inferred from votes); bellwether-ballot pane in the end margin (vote-space TVD to the national result, K16–K25 consistency; clicking a row shows that ballot's K26 successor result via the crosswalk/venue, or "not counted yet"); twins mode (geomap/t-SNE ballot click → cosine-similarity twins/anti-twins, no separate page). The geomap pane carries geomap.html's colour modes (winner pies / turnout / socioeconomic cluster / voting-pattern embed / party support with party picker and dynamic p98 scale, same colour scales and legend; socioeconomic data fetched lazily on first use, per-station with settlement fallback; clusters get one representative colour per mode except winner, which keeps the pie). During a partial count the modes colour counted ballots only, over the gray uncounted dots
- Settlement sectors: `generate_settlement_sectors.py` → `site/data/settlement_sectors.json` (form from Wikidata descriptions, population from curated Druze list + wiki keywords + CBS 2011 GDB `Religion_yishuv_Txt` re-extracted by settlement code, WB from the wiki התנחלות tag, Haredi from a curated whitelist only — never from Shas/UTJ vote share). Static; regenerated only when missing during refresh.
- Election-night previews (presentational only, simulated data): `?preview=partial` shows the page mid-count (~45% of ballots, the default skewed rehearsal mask); `?preview=partial17` / `?preview=partial12` show the same night at ~17% / ~12% counted, loading `site/data/command_center_26_p17.json` / `command_center_26_p12.json` instead (build: `python generate_command_center_data.py --target-share 0.17 --out command_center_26_p17.json` — rescales both mask cutoffs, Haredi boxes still counting at ~14% of the rate of others). The nowcast gate opens at ≥1,000 matched ballots and ≥12% of roster K25 votes counted (plus R²≥0.75, composition TVD≤0.18, ≥8,000 origin votes per major source; thresholds chosen from a forced-projection sweep against the known simulated truth — mean seat error <1 and full p10–p90 coverage from ~12%, worst-party error 5–6 seats and threshold coin-flips below ~8%). The 12% preview is tuned to just clear it (1,498 counted, share 12.5%, matched 1,237; `--target-share 0.125`). During any partial count the geomap colours counted ballots only; uncounted boxes are faint gray dots (`nowcast.geo_uncounted`), and the "על הקצה" bubble list uses counted votes only, never the projection.
- Election-night flow: the Netlify poller dispatches `.github/workflows/k26-refresh.yml`, which runs `refresh_k26.py` (prepare → fraud-sim → `generate_suspects_data.py` → irregularities → turnout when official → `k26_live.py --publish` → command-center extras → MCP build) and commits the outputs. Every file `k26.html` fetches (status, wiki results, map/tsne/transfer 26, `suspects_26.json`, `command_center_26.json`, dhondt parties26) is in that commit list; `k26_mks.json`, `settlement_sectors.json` and `station_coordinates.json` are static. `k26_control.json` `auto:false` gates the whole flow.

### regional.html (Regional Elections Simulator)
- Voronoi-based regional election simulation with D'Hondt allocation
- Link to `voronoi-explainer.html` (animated explanation of districting)

### rankings.html (Volatility + Concentration)
- Two tabs: settlements (Pedersen-style vote volatility across elections) and parties (HHI / effective-settlement concentration)
- Size filters for settlements; sortable tables; Chart.js histogram + HHI bar chart
- Data: `site/data/metrics.json` from `generate_metrics_data.py`
- Desktop + mobile (`m/rankings.html`); `?tab=parties` URL support

### methodology.html (Written Methods)
- Bilingual prose (`.prose-he` / `.prose-en`) with KaTeX: convex transfer model, R², Dirichlet residual dispersion, empirical α, per-destination heatmap, limitations
- Desktop + mobile; linked from dashboard header and nav extras

### settlement.html (Settlement Profile)
- Per-settlement deep dive with Wikipedia info, voting trends, party breakdown
- URL parameter: `?name=<settlement_name>`
- Trends use K16–K25 map files

## Paper

The paper lives in `elections-paper/` — a **nested git repo** (`harelc/elections-paper`), gitignored in the parent (the old `paper/` submodule ref was removed because it broke GitHub Pages). It has its own remote, branch (`main`), and commit history. Commit and push it independently.

```bash
# Compile the paper (uses tectonic, NOT pdflatex/latexmk)
cd elections-paper && tectonic paper.tex

# Commit paper changes (separate repo!)
cd elections-paper && git add -A && git commit -m "..." && git push

# Key files:
# elections-paper/paper.tex              — Main paper source
# elections-paper/references.bib         — Bibliography
# elections-paper/figures/               — Generated figures (PDF)
# elections-paper/generate_figures.py    — Script to regenerate figures
# elections-paper/bootstrap_analysis.py  — Bootstrap confidence interval analysis
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
- 26: 27 October 2026 (estimated) — simulated scenario (on by default; `?e26=0` opts out)
