"""Election-night publishing checks for k26_live.py and the k26.html bubble pane.

    python tests/test_k26_publish.py      (from the repo root; node for the last check)

Each check prints PASS/FAIL with its evidence and the script exits non-zero on
any FAIL. Nothing in the repo is written: publishing runs on copies in a
temporary folder.
"""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, '.')
import k26_live as k
from party_config import ELECTIONS

results = []


def report(name, ok, evidence):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {evidence}")


tmp = Path(tempfile.mkdtemp())
major = ELECTIONS['26']['major_parties']
rows = list(csv.DictReader(open('ballot26.csv', encoding='utf-8-sig')))
cols = list(rows[0].keys())


def write_csv(path, data):
    with path.open('w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(data)


# 1. update_wiki works on the minified file that ships in the repo
text = Path('site/data/wiki_official_results.json').read_text(encoding='utf-8')
s = k.summarize('ballot26.csv')
try:
    out = json.loads(k.update_wiki(text, s, 'partial'))
    ok = out['26_note'] == 'Partial CEC count' and len(out['26']) == len(major['names']) and out['25'] == json.loads(text)['25']
    report('update_wiki on the shipped minified file', ok,
           f"26_note={out['26_note']!r}, entries={len(out['26'])}, 26_valid={out['26_valid']:,}, other K-entries untouched={out['25'] == json.loads(text)['25']}")
except SystemExit as e:
    report('update_wiki on the shipped minified file', False, f'SystemExit: {e}')

# 2. a list missing from major_parties that passes the threshold stops publishing
surprise = [dict(r) for r in rows]
for r in surprise:
    v = int(float(r['כשרים'] or 0))
    r['צף'] = str(int(v * 0.05))
    r['כשרים'] = str(v + int(v * 0.05))
p = tmp / 'surprise.csv'
write_csv(p, surprise)
try:
    k.summarize(p)
    report('unknown list above the threshold blocks publishing', False, 'summarize accepted the file')
except SystemExit as e:
    report('unknown list above the threshold blocks publishing', True, str(e))

# 3. an unknown list below the threshold still counts in the threshold base, and seats stay 120
small = [dict(r) for r in rows]
for r in small:
    v = int(float(r['כשרים'] or 0))
    r['צף'] = '5'
    r['כשרים'] = str(v + 5)
p = tmp / 'small.csv'
write_csv(p, small)
s2 = k.summarize(p)
report('small unknown list: 120 seats, others in the base', sum(s2['seats']) == 120 and s2['other_votes'] >= 5 * len(rows),
       f"seats={sum(s2['seats'])}, other_votes={s2['other_votes']:,}, valid_total={s2['valid_total']:,}")

# 4. apply() is all-or-nothing: a failing page leaves every file untouched
work = tmp / 'site_copy'
for rel in ['party_config.py', 'site/data/wiki_official_results.json', 'site/dhondt.html', 'site/m/dhondt.html',
            'site/party.html', 'site/m/party.html', 'site/data/k26_status.json']:
    (work / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(rel, work / rel)
orig = {rel: (work / rel).read_text(encoding='utf-8') for rel in ['party_config.py', 'site/data/wiki_official_results.json']}
(work / 'site/m/dhondt.html').write_text('broken page without parties26', encoding='utf-8')
k.PARTY_CONFIG = work / 'party_config.py'
k.WIKI = work / 'site/data/wiki_official_results.json'
k.DHONDT_PAGES = [work / 'site/dhondt.html', work / 'site/m/dhondt.html']
k.PARTY_PAGES = [work / 'site/party.html', work / 'site/m/party.html']
k.STATUS = work / 'site/data/k26_status.json'
try:
    k.apply(s, 'partial', None, None, 0)
    report('apply() all-or-nothing', False, 'apply did not fail on a broken page')
except SystemExit as e:
    untouched = all((work / rel).read_text(encoding='utf-8') == t for rel, t in orig.items())
    report('apply() all-or-nothing', untouched, f'failed with "{e}"; party_config and wiki untouched: {untouched}')

# 5. a full apply() on good copies, then the bubble allocator in k26.html against Python
shutil.copy('site/m/dhondt.html', work / 'site/m/dhondt.html')
night = [dict(r) for r in rows]
amcha = dict(zip(major['names'], major['symbols']))['עמך ישראל']
minor = next(c for c in cols[cols.index('כשרים') + 1:] if c not in major['symbols'])
amcha_now = sum(int(float(r[amcha] or 0)) for r in night)
for r in night:
    a = int(float(r[amcha] or 0))
    na = round(a * 179500 / amcha_now)
    r[amcha] = str(na)
    r[minor] = '5'
    r['כשרים'] = str(int(float(r['כשרים'])) + (na - a) + 5)
p = tmp / 'night.csv'
write_csv(p, night)
s3 = k.summarize(p)
k.apply(s3, 'partial', None, None, 0)
wiki = json.loads((work / 'site/data/wiki_official_results.json').read_text(encoding='utf-8'))
js = Path('site/k26.html').read_text(encoding='utf-8')
agr = js[js.index('const AGREEMENTS = ') + len('const AGREEMENTS = '):]
agr = agr[:agr.index(';')]
code = js[js.index('const TOTAL_SEATS'):js.index('function renderBubble')]
runner = tmp / 'bubble.js'
runner.write_text(
    f"const DATA = {{ wiki: {json.dumps(wiki, ensure_ascii=False)} }};\nlet AGREEMENTS = {agr};\n{code}\n"
    "const votes = {}; DATA.wiki['26'].forEach(p => votes[p.name] = p.votes);\n"
    "console.log(JSON.stringify(allocateSeats(votes).seats));\n", encoding='utf-8')
import shutil
if not shutil.which('node'):
    print('SKIP  bubble pane check (node not installed)')
    sys.exit(0 if all(results) else 1)
js_seats = json.loads(subprocess.run(['node', str(runner)], capture_output=True, text=True, encoding='utf-8').stdout)
py_seats = dict(zip(s3['names'], s3['seats']))
diff = {n: (py_seats[n], js_seats.get(n)) for n in py_seats if py_seats[n] != js_seats.get(n)}
report('k26 bubble pane agrees with the published seats when other lists have votes', not diff,
       f"Amcha {s3['votes_by_name']['עמך ישראל']:,} votes, other lists {s3['other_votes']:,}; python {py_seats['עמך ישראל']} vs bubble {js_seats.get('עמך ישראל')}; mismatches {diff}")

print(f"\n{sum(results)}/{len(results)} passed")
