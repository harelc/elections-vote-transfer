#!/bin/sh
# Partial-count drill for election night: builds CEC-dummy-shaped
# snapshots (cp1255, full roster, external tally columns) from the
# simulated ballot26.csv and runs the poller -> normalize -> publish
# seams on copies. Nothing in the repo is written.
#
#   ./tests/drill_partial_count.sh
set -eu
REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
python3 tests/drill_partial_count.py
node --test netlify/lib/k26/decide.test.mjs netlify/lib/k26/turnout.test.mjs
echo
echo "drill passed."
