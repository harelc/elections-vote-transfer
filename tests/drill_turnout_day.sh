#!/bin/sh
# End-to-end drill for the election-day turnout view, the PR #22 way:
# a clean git worktree of HEAD plus a FRESH venv built from
# requirements.txt alone, so missing dependencies, publish-path crashes
# and format surprises surface here and not on election day.
#
#   ./tests/drill_turnout_day.sh
#
# Runs tests/drill_turnout_day.py in the worktree, then the Netlify
# poller unit tests, and leaves the worktree + venv paths printed for a
# manual browser pass:
#   cd <worktree>/site && python3 -m http.server 8899
#   open http://localhost:8899/k26.html?turnout=1
set -eu
REPO=$(git rev-parse --show-toplevel)
TMP=$(mktemp -d /tmp/turnout-drill-env.XXXXXX)
echo "drill env: $TMP"
git -C "$REPO" worktree add --force "$TMP/repo" HEAD >/dev/null
python3 -m venv "$TMP/venv"
"$TMP/venv/bin/pip" install --quiet --upgrade pip
"$TMP/venv/bin/pip" install --quiet -r "$TMP/repo/requirements.txt"
cp "$REPO/tests/drill_turnout_day.py" "$TMP/repo/tests/drill_turnout_day.py"
"$TMP/venv/bin/python" "$TMP/repo/tests/drill_turnout_day.py" --repo "$TMP/repo"
node --test "$TMP/repo/netlify/lib/k26/turnout.test.mjs" "$TMP/repo/netlify/lib/k26/decide.test.mjs"
echo
echo "drill passed. Browser pass:"
echo "  cd $TMP/repo/site && python3 -m http.server 8899   # then open http://localhost:8899/k26.html?turnout=1"
echo "cleanup when done:"
echo "  git -C $REPO worktree remove --force $TMP/repo && rm -rf $TMP"
