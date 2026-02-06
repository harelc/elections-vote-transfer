# Israeli Elections Vote Transfer Analysis

Interactive visualizations for analyzing voting patterns and vote transfers between Israeli Knesset elections (2019-2022).

**[View Live Demo](https://harelc.github.io/elections-vote-transfer/)** (if hosted)

## Overview

This project provides a suite of interactive tools to explore Israeli election data at the ballot-box level (~10,000-12,000 polling stations per election). It answers questions like:

- Where did votes for party X go in the next election?
- How do voting patterns cluster geographically and demographically?
- Which polling stations show unusual voting patterns?
- How would seat allocation change with different vote counts?

## Features

### 1. Vote Transfer Sankey Diagram (Main Page)

Visualizes the flow of votes between consecutive elections using a Sankey diagram.

- **What it shows**: Estimated proportion of voters who switched from one party to another
- **How to read it**: Left side shows parties from the earlier election, right side shows parties from the later election. The width of each flow represents the estimated number of voters who made that transition.
- **Elections covered**: 21→22, 22→23, 23→24, 24→25

The transfer matrix is computed using convex optimization to find the best-fit stochastic matrix M where `Votes_before × M ≈ Votes_after`.

### 2. T-SNE Ballot Clustering

A 2D visualization of all polling stations, positioned by similarity of voting patterns.

- **Clustering**: Stations with similar voting patterns appear close together
- **Color modes**:
  - **Turnout**: Color by voter turnout percentage
  - **Party support**: Color by support level for any selected party
  - **Socioeconomic cluster**: Color by CBS socioeconomic index (1-10 scale)
- **Interactions**: Hover for details, zoom and pan, search for specific settlements

### 3. Party Support Scatter Plot

Compare support for two parties (or the same party across elections) at the ballot-box level.

- **Axes**: Select any party for X and Y axes, from any election
- **Cross-election comparison**: When comparing different elections, only matching ballot boxes are shown
- **Filters**: Filter by settlement name to focus on specific areas
- **Units**: Toggle between percentage and absolute vote counts

### 4. D'Hondt Seat Calculator

Interactive calculator showing how Knesset seats are allocated using the D'Hondt method.

- **Adjust votes**: Modify party vote counts to see how seat allocation changes
- **Threshold visualization**: See which parties pass/fail the electoral threshold
- **Surplus agreements**: View the effect of surplus vote agreements between parties

### 5. Irregular Ballot Analysis

Identifies polling stations with unusual voting patterns compared to their surroundings.

- **Detection method**: Compares each station to nearby stations in the same settlement
- **Metrics**: Highlights stations with statistically unusual party support levels

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
  - Ballot-level results (expb.csv files) for Knesset elections 21-25
- **Socioeconomic data**: [Central Bureau of Statistics (CBS)](https://www.cbs.gov.il/)
  - Settlement socioeconomic cluster ratings (1-10 scale)
  - Regional council assignments for small localities

## Elections Covered

| Election | Knesset | Date | Turnout |
|----------|---------|------|---------|
| 21 | 21st Knesset | April 2019 | 68.5% |
| 22 | 22nd Knesset | September 2019 | 69.8% |
| 23 | 23rd Knesset | March 2020 | 71.5% |
| 24 | 24th Knesset | March 2021 | 67.4% |
| 25 | 25th Knesset | November 2022 | 70.6% |

## Local Development

### Prerequisites

- Python 3.8+
- Node.js (optional, for alternative dev server)

### Setup

```bash
# Clone the repository
git clone https://github.com/harelc/elections-vote-transfer.git
cd elections-vote-transfer

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pandas numpy cvxpy

# Start local server
cd site
python3 -m http.server 8888
```

Then open http://localhost:8888 in your browser.

### Regenerating Transfer Data

If you modify the transfer calculation logic:

```bash
source venv/bin/activate
python generate_transfer_data.py
cp data/transfer_*.json site/data/
```

## Project Structure

```
├── site/                    # Static website files
│   ├── index.html           # Sankey diagram (main page)
│   ├── sankey.js            # Sankey visualization logic
│   ├── tsne.html            # T-SNE clustering view
│   ├── scatter.html         # Party scatter plot
│   ├── dhondt.html          # Seat calculator
│   ├── irregular.html       # Irregular ballot analysis
│   └── data/                # JSON data files for frontend
├── data/                    # Source and processed data
│   ├── ballot*.csv          # Raw election results
│   └── transfer_*.json      # Computed transfer matrices
├── generate_transfer_data.py # Transfer matrix computation
└── CLAUDE.md                # Technical notes for AI assistants
```

## Credits

- **Concept and original implementation**: Harel Cain (September 2019)
- **Inspiration**: [Itamar Mushkin's analysis](https://www.themarker.com/techblogs/ormigoldstein/BLOG-1.6567019)
- **Libraries**: D3.js, CVXPY, scikit-learn (t-SNE)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

Areas for potential improvement:
- Adding more elections as they occur
- Improving the irregular ballot detection algorithm
- Mobile responsiveness improvements
- Additional visualization types
