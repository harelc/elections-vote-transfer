# Israeli Elections Vote Transfer Analysis

Interactive visualizations for analyzing voting patterns and vote transfers between Israeli Knesset elections (2003-2022, Knesset 16-25).

**[קולות נודדים - Visit the Website](https://kolot-nodedim.netlify.app/)**

## Overview

This project provides a suite of interactive tools to explore Israeli election data at the ballot-box level (~10,000-12,000 polling stations per election). It answers questions like:

- Where did votes for party X go in the next election?
- How do voting patterns cluster geographically and demographically?
- Which polling stations show unusual voting patterns?
- How would seat allocation change with different vote counts?
- What are the voting trends in a specific settlement across elections?

All pages are fully bilingual (Hebrew/English) and have both desktop and mobile-optimized versions.

## Features

### 1. Dashboard (Landing Page)

A central hub with key stats and card navigation to all visualizations. Shows live visitor count.

### 2. Vote Transfer Sankey Diagram

Visualizes the flow of votes between consecutive elections using a Sankey diagram.

- **What it shows**: Estimated proportion of voters who switched from one party to another
- **How to read it**: Left side shows parties from the earlier election, right side shows parties from the later election. The width of each flow represents the estimated number of voters who made that transition.
- **Elections covered**: 16→17, 17→18, 18→19, 19→20, 20→21, 21→22, 22→23, 23→24, 24→25
- **Abstention toggle**: Optionally shows a "Did not vote" pseudo-party to visualize turnout changes

The transfer matrix is computed using convex optimization to find the best-fit stochastic matrix M where `Votes_before × M ≈ Votes_after`.

### 3. T-SNE Ballot Clustering

A 2D visualization of all polling stations, positioned by similarity of voting patterns.

- **Clustering**: Stations with similar voting patterns appear close together
- **Color modes**:
  - **Turnout**: Color by voter turnout percentage
  - **Party support**: Color by support level for any selected party
  - **Socioeconomic cluster**: Color by CBS 2021 socioeconomic index (1-10 scale), per statistical area within cities
- **Interactions**: Hover for details, zoom and pan, search for specific settlements

### 4. Geographic Map

Interactive Leaflet map showing all ballot stations across Israel.

- **Clustered markers**: Zoom in to see individual stations, zoom out to see aggregated clusters
- **Color modes**: Color by party support, turnout, or socioeconomic cluster
- **Settlement search**: Find and zoom to specific settlements
- **Station popups**: Click for detailed voting breakdown with link to settlement profile

### 5. Party Support Scatter Plot

Compare support for two parties (or the same party across elections) at the ballot-box level.

- **Axes**: Select any party for X and Y axes, from any election
- **Cross-election comparison**: When comparing different elections, only matching ballot boxes are shown
- **Filters**: Filter by settlement name to focus on specific areas
- **Units**: Toggle between percentage and absolute vote counts

### 6. Bader-Ofer Seat Calculator

Interactive calculator showing how Knesset seats are allocated using the Bader-Ofer (modified D'Hondt) method.

- **Adjust votes**: Modify party vote counts to see how seat allocation changes
- **Threshold visualization**: See which parties pass/fail the electoral threshold
- **Surplus agreements**: View the effect of surplus vote agreements between parties

### 7. Irregular Ballot Analysis

Identifies polling stations with unusual voting patterns compared to their surroundings.

- **Detection method**: Compares each station to nearby stations in the same settlement
- **Metrics**: Highlights stations with statistically unusual party support levels

### 8. Regional Elections Simulator

Simulates a hypothetical regional election system for Israel using Voronoi district mapping and D'Hondt seat allocation.

### 9. Party Profile

Deep-dive page for party families showing their evolution across elections:

- **Leader photo and party color**: Hero section with the party's identifying visuals
- **Election history table**: Seats, votes, percentage, and leader per election
- **Voting trends chart**: Support trajectory across all elections
- **Strongholds**: Top settlements by party support with mini-map
- **Vote migration**: Incoming/outgoing vote flows from Sankey transfer data

Accessible via `party.html?name=<party_family_name>`.

### 10. Settlement Profile

Deep-dive page for individual settlements showing:

- **Wikipedia info**: Thumbnail image, description, and extract from Hebrew Wikipedia
- **Voting trends**: Chart showing top party support across all 10 elections
- **Latest election breakdown**: Party table with percentages and votes
- **Mini map**: Leaflet map zoomed to the settlement's ballot stations
- **Ballot table**: Sortable list of individual ballot boxes with turnout and winner
- **Navigation**: Autocomplete search to jump between settlements

Accessible via `settlement.html?name=<settlement_name>` or by clicking settlement links in the map, T-SNE, and scatter views.

## Methodology

### Vote Transfer Estimation

The vote transfer matrix is estimated by solving a constrained optimization problem:

```
minimize ||V_from × M - V_to||²
subject to:
  - M[i,j] ≥ 0 for all i,j (non-negative transfers)
  - Σⱼ M[i,j] = 1 for all i (rows sum to 1, i.e., stochastic matrix)
```

This assumes voters transfer between parties in a consistent pattern across all polling stations—a simplification, but one that produces interpretable results.

**Solver**: CVXPY with SCS backend

### Ballot Box Matching

When comparing elections, ballot boxes are matched by settlement name and ballot number. Israeli ballot boxes sometimes get subdivided between elections (e.g., box 14 becomes 14.1, 14.2, 14.3). The matching logic:

- Exact matches are preferred (14.1 ↔ 14.1)
- If no exact match exists, 14.1 can match against 14 (the original undivided box)
- Subdivisions .2, .3, etc. only match exactly (no fallback)

### T-SNE Dimensionality Reduction

Polling stations are embedded in 2D using t-SNE on the vector of party vote proportions. Stations with similar voting profiles cluster together, often revealing geographic and demographic patterns.

## Data Sources

- **Election results**: [Central Elections Committee](https://votes.bechirot.gov.il/)
  - Ballot-level results for Knesset elections 16-25 (K16-K20 from CKAN API, K21-K25 from expb.csv files)
- **Socioeconomic data**: [Central Bureau of Statistics (CBS)](https://www.cbs.gov.il/)
  - CBS 2021 socioeconomic index (publication 1955) per statistical area
  - CBS 2011 Census statistical area boundaries (geodatabase)
  - Settlement and regional council level fallbacks for small localities
- **Settlement info**: [Hebrew Wikipedia](https://he.wikipedia.org/) REST API
  - Descriptions, thumbnails, and extracts for ~1,100 settlements
- **Geocoding**: OpenStreetMap Nominatim + Google Places API for ballot station coordinates

## Elections Covered

| Election | Knesset | Date | Turnout |
|----------|---------|------|---------|
| 16 | 16th Knesset | January 2003 | 67.8% |
| 17 | 17th Knesset | March 2006 | 63.6% |
| 18 | 18th Knesset | February 2009 | 64.7% |
| 19 | 19th Knesset | January 2013 | 67.8% |
| 20 | 20th Knesset | March 2015 | 72.3% |
| 21 | 21st Knesset | April 2019 | 68.5% |
| 22 | 22nd Knesset | September 2019 | 69.8% |
| 23 | 23rd Knesset | March 2020 | 71.5% |
| 24 | 24th Knesset | March 2021 | 67.4% |
| 25 | 25th Knesset | November 2022 | 70.6% |

## Local Development

### Prerequisites

- Python 3.8+

### Setup

```bash
# Clone the repository
git clone https://github.com/harelc/elections-vote-transfer.git
cd elections-vote-transfer

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start local server
cd site
python3 -m http.server 8888
```

Then open http://localhost:8888 in your browser.

### Regenerating Data

```bash
source venv/bin/activate

# Vote transfer matrices
python generate_transfer_data.py
cp data/transfer_*.json site/data/

# T-SNE clustering
python generate_tsne_data.py
python add_locations_to_tsne.py
cp data/tsne_*.json site/data/

# Geographic map data (writes directly to site/data/)
python generate_map_data.py

# Wikipedia enrichment for settlement profiles (writes to site/data/)
python enrich_settlements_wikipedia.py
```

## Project Structure

```
├── site/                          # Static website files
│   ├── index.html                 # Dashboard landing page
│   ├── sankey.html                # Sankey vote transfer diagram
│   ├── tsne.html                  # T-SNE ballot clustering
│   ├── geomap.html                # Geographic map
│   ├── scatter.html               # Party scatter plot
│   ├── dhondt.html                # Bader-Ofer seat calculator
│   ├── irregular.html             # Irregular ballot analysis
│   ├── regional.html              # Regional elections simulator
│   ├── settlement.html            # Settlement profile page
│   ├── discussions.html           # Community discussions (Giscus)
│   ├── i18n.js                    # Internationalization & navigation
│   ├── og-image.png               # Social preview image
│   ├── m/                         # Mobile-optimized versions of all pages
│   └── data/                      # JSON data files for frontend
├── data/                          # Source and intermediate data
├── party_config.py                # Election metadata & party config (K16-K25)
├── generate_transfer_data.py      # Transfer matrix computation
├── generate_tsne_data.py          # T-SNE embedding computation
├── generate_map_data.py           # Geographic data generation
├── download_statistical_zones.py  # CBS 2011 zone matching pipeline
├── process_statistical_zones.py   # CBS socioeconomic data processing
├── download_historical_ballots.py # K16-K20 ballot data from CEC CKAN API
├── enrich_settlements_wikipedia.py # Wikipedia data enrichment
├── prepare_election_26.py         # Election 26 data workflow
└── ballot*.csv                    # Raw election results per election (16-25)
```

## Credits

- **Concept and original implementation**: Harel Cain (September 2019)
- **Inspiration**: [Itamar Mushkin's analysis](https://www.themarker.com/techblogs/ormigoldstein/BLOG-1.6567019)
- **Libraries**: D3.js, Chart.js, Leaflet, CVXPY, scikit-learn (t-SNE)

## License

This project is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International).

You are free to share and adapt this work for non-commercial purposes, with attribution.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
