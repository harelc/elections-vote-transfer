# Elections Vote Transfer Project

Interactive visualizations for analyzing Israeli Knesset election data, showing vote transfers between elections, party support patterns, and ballot-level analysis.

## Project Structure

```
├── data/                    # Raw and processed data files
│   ├── ballot*.csv          # Raw election data per election (21-25)
│   ├── transfer_*.json      # Vote transfer matrices between elections
│   └── socioeconomic_clusters.json
├── site/                    # Static website (served directly)
│   ├── index.html           # Main page with Sankey diagram
│   ├── sankey.js            # Sankey visualization logic
│   ├── tsne.html            # T-SNE ballot clustering visualization
│   ├── scatter.html         # Party support scatter plot (X vs Y axis)
│   ├── dhondt.html          # D'Hondt seat allocation calculator
│   ├── irregular.html       # Irregular ballot analysis
│   └── data/                # JSON data for frontend (copy of processed data)
├── generate_transfer_data.py # Generates vote transfer matrices
└── venv/                    # Python virtual environment
```

## Running the Project

```bash
# Start local server (from site/ directory)
cd site && python3 -m http.server 8888

# Or from project root
python3 -m http.server 8888  # then access site/index.html
```

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
  "parties": [{"name": "...", "symbol": "..."}],
  "stations": [
    {"n": "settlement", "b": "ballot", "l": "location", "v": total_voters, "p": {"party": proportion}}
  ]
}
```

**transfer_*.json** (between elections):
```json
{
  "from_election": {...},
  "to_election": {...},
  "nodes_from": [...],
  "nodes_to": [...],
  "transfer_matrix": [[...]],  # Row=from party, Col=to party, values are proportions
  "stats": {"common_precincts": N, "r_squared": 0.xx}
}
```

### Generating Transfer Data

```bash
source venv/bin/activate
python generate_transfer_data.py
cp data/transfer_*.json site/data/
```

Uses convex optimization (cvxpy) to estimate vote transfers. Requires pandas, numpy, cvxpy.

## Visualization Pages

### index.html (Sankey)
- Shows vote flow between consecutive elections
- Uses `sankey.js` for rendering
- Data: `transfer_*.json`

### tsne.html
- T-SNE clustering of ballot boxes by voting patterns
- Color modes: turnout, party support, socioeconomic cluster
- Socioeconomic data from CBS (1-10 scale)
- Small settlements mapped to regional councils for coverage

### scatter.html
- Compare party X support vs party Y support across ballots
- Can compare same or different elections
- Settlement filter with autocomplete search
- Units toggle: percentages vs absolute votes

### dhondt.html
- Interactive D'Hondt seat calculator
- Adjust vote counts to see seat changes

## Common Issues

1. **Browser cache**: After regenerating data, hard refresh (Cmd+Shift+R) or use incognito
2. **Python environment**: Always use `source venv/bin/activate` for generate scripts
3. **Site files ignored by git**: Use `git add -f site/...` to stage site files

## Election IDs

- 21: April 2019
- 22: September 2019
- 23: March 2020
- 24: March 2021
- 25: November 2022
