"""Build the national Knesset poll database from Wikipedia's poll tables.

Source: English Wikipedia "Opinion polling for the <year> Israeli legislative
election" pages, each pinned to one revision (WIKI_PAGES below), so every row
can be traced back to the exact table it came from. The raw HTML is cached in
data/polls_wiki/ (fetched by revision id when missing).

Only the main seat-projection tables are read. Scenario tables ("what if X
merged"), preferred-PM tables and percentage-only tables are skipped.
Rows dated more than KEEP_DAYS before the election are dropped.

Output: data/polls_db.json  (one record per poll row, with its source)
        data/polls_db.csv   (same rows, one column per list, for Excel)

Columns are the list names as Wikipedia writes them. Mapping them onto the
lists that actually ran is done in poll_list_map.py and used by
generate_poll_accuracy.py.

Usage: python build_polls_db.py
"""
import csv
import json
import os
import re
import sys
import urllib.request
from datetime import date, timedelta

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

RAW_DIR = os.path.join('data', 'polls_wiki')
OUT_JSON = os.path.join('data', 'polls_db.json')
OUT_CSV = os.path.join('data', 'polls_db.csv')
# polls taken from their original sources (not yet on Wikipedia) and exit polls
MANUAL = os.path.join('data', 'polls_manual.json')
KEEP_DAYS = 180
UA = 'kolot-nodedim-poll-db/1.0'

# election -> page, pinned revision, election day, indices of the main poll
# tables among the page's "wikitable"s (scenario tables are left out).
WIKI_PAGES = {
    '19': dict(page='2013', revid=1368358600, day=date(2013, 1, 22), tables=[0]),
    '20': dict(page='2015', revid=1376431859, day=date(2015, 3, 17), tables=[0]),
    '21': dict(page='April_2019', revid=1368358661, day=date(2019, 4, 9), tables=[0, 1, 2, 3]),
    '22': dict(page='September_2019', revid=1357147577, day=date(2019, 9, 17), tables=[0, 1, 2, 3, 4, 5]),
    '23': dict(page='2020', revid=1379044811, day=date(2020, 3, 2), tables=[0, 1, 2, 3, 4]),
    '24': dict(page='2021', revid=1357147509, day=date(2021, 3, 23), tables=[0, 1, 2, 3, 4, 5, 6]),
    '25': dict(page='2022', revid=1360584369, day=date(2022, 11, 1), tables=[0, 1, 2, 3, 4, 5]),
    '26': dict(page='2026', revid=1381901283, day=date(2026, 10, 27), tables=[1, 2, 3, 4, 5, 6, 7]),
}

MONTHS = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}

# Header labels that are not lists.
NON_LIST_HEADERS = {'date', 'fieldwork date', 'polling firm', 'publisher', 'poll', 'sample size',
                    'gov.', 'gov', 'opp.', 'opp', 'l', 'r', 'c', 'o', 'lead', 'others', 'oth.',
                    'opposition', 'coalition', 'bloc'}

NOT_A_POLL = re.compile(r'election results|final results|pre-election seats|current seats|'
                        r'outgoing knesset|seats at dissolution|seats in the outgoing|seats won|'
                        r'election result', re.I)


def page_url(cfg):
    return ('https://en.wikipedia.org/w/index.php?title=Opinion_polling_for_the_'
            f'{cfg["page"]}_Israeli_legislative_election&oldid={cfg["revid"]}')


def load_page(cfg):
    path = os.path.join(RAW_DIR, f'en_{cfg["page"]}.html')
    if not os.path.exists(path):
        os.makedirs(RAW_DIR, exist_ok=True)
        url = f'https://en.wikipedia.org/w/index.php?oldid={cfg["revid"]}&action=render'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req) as r, open(path, 'wb') as f:
            f.write(r.read())
    return BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')


def clean(text):
    text = re.sub(r'\[\s*[^\]]{1,6}\s*\]', '', text)   # footnote markers [ 12 ] [ a ]
    return re.sub(r'\s+', ' ', text).strip()


def grid(table):
    """Expand rowspan/colspan. Returns list of rows; each row is a list of
    (cell_element, first) where first is True only at the cell's own slot."""
    out, pending = [], {}
    for tr in table.find_all('tr'):
        row, col = [], 0
        cells = tr.find_all(['th', 'td'], recursive=False)
        ci = 0
        while ci < len(cells) or col in pending:
            if col in pending:
                el, left, first_row = pending[col]
                row.append((el, False))
                if left <= 1:
                    del pending[col]
                else:
                    pending[col] = (el, left - 1, False)
                col += 1
                continue
            el = cells[ci]
            ci += 1
            cs = int(re.sub(r'\D', '', el.get('colspan', '1')) or 1)
            rs = int(re.sub(r'\D', '', el.get('rowspan', '1')) or 1)
            for k in range(cs):
                row.append((el, k == 0))
                if rs > 1:
                    pending[col] = (el, rs - 1, False)
                col += 1
        out.append((tr, row))
    return out


def parse_date(text, election_day, section_year=None):
    """'6–7 Jul 22', '3–6 Oct 2019', '31 Dec – 1 Jan', '19 Oct' -> (start, end).
    section_year: the year of the table's own year-divider row above this row."""
    t = clean(text).replace('–', '-').replace('—', '-')
    t = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', t)
    parts = [p.strip() for p in t.split('-') if p.strip()]
    if not parts:
        return None, None

    def one(p, fallback_month=None, fallback_year=None):
        m = re.match(r'^(\d{1,2})(?:\s+([A-Za-z]+))?(?:\s+(\d{2,4}))?$', p)
        if not m:
            m2 = re.match(r'^([A-Za-z]+)\s+(\d{1,2})(?:,?\s+(\d{4}))?$', p)   # 'Oct 19, 2019'
            if not m2:
                return None
            d, mon, y = int(m2.group(2)), m2.group(1), m2.group(3)
        else:
            d, mon, y = int(m.group(1)), m.group(2), m.group(3)
        mon = MONTHS.get((mon or '')[:3].lower()) if mon else fallback_month
        if not mon:
            return None
        if y:
            y = int(y)
            if y < 100:
                y += 2000
        else:
            y = fallback_year
        return [d, mon, y]

    end = one(parts[-1])
    if not end:
        return None, None
    start = one(parts[0], end[1], end[2]) if len(parts) > 1 else list(end)
    if not start:
        start = list(end)
    # Year missing: the table's year-divider row, else the latest year that
    # keeps the date on/before election day.
    for x in (end, start):
        if x[2] is None and section_year:
            x[2] = section_year
        if x[2] is None:
            y = election_day.year
            if date(y, x[1], min(x[0], 28)) > election_day:
                y -= 1
            x[2] = y
    try:
        e = date(end[2], end[1], end[0])
        s = date(start[2], start[1], start[0])
    except ValueError:
        return None, None
    if s > e:   # '31 Dec - 1 Jan' with the year taken from the end
        s = date(s.year - 1, s.month, s.day)
    return s, e


def parse_value(text):
    """Seat cell -> dict(seats, pct, raw) or None when the list was not polled."""
    raw = clean(text)
    t = raw.replace('−', '-')
    if t in ('', '–', '-', '—', '— N/a', 'N/a', '?', '…', 'x'):
        return None
    m = re.match(r'^\(?\s*(\d+(?:\.\d+)?)\s*%\s*\)?$', t)
    if m:
        return {'seats': 0, 'pct': float(m.group(1)), 'raw': raw}
    m = re.match(r'^(\d{1,2})$', t)
    if m:
        return {'seats': int(m.group(1)), 'pct': None, 'raw': raw}
    m = re.match(r'^(\d{1,2})\s*\(?\s*(\d+(?:\.\d+)?)\s*%\s*\)?$', t)    # '4 (3.4%)'
    if m:
        return {'seats': int(m.group(1)), 'pct': float(m.group(2)), 'raw': raw}
    if re.match(r'^\(\d{1,2}\)$', t):                    # '(3)': seat-equivalent of a list below the threshold
        return {'seats': 0, 'pct': None, 'raw': raw}
    if re.match(r'^\(?\s*<\s*\d+(?:\.\d+)?\s*%\s*\)?$', t):              # '(<1%)': below threshold
        return {'seats': 0, 'pct': None, 'raw': raw}
    m = re.match(r'^\(?\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*%\s*\)?$', t)   # '(1.7-2.1%)'
    if m:
        return {'seats': 0, 'pct': None, 'raw': raw}
    m = re.match(r'^(\d+(?:\.\d+)?)\s*%\s+\D', t)        # 'Others' cell: '2.4% New Economic at 1.5% ...'
    if m:
        return {'seats': 0, 'pct': float(m.group(1)), 'raw': raw}
    m = re.match(r'^(\d{1,2}\.\d)$', t)                  # averaged seat figure, e.g. '16.5'
    if m:
        return {'seats': float(m.group(1)), 'pct': None, 'raw': raw}
    return {'seats': None, 'pct': None, 'raw': raw, 'unparsed': True}


def references(soup):
    """cite_note id -> list of external URLs."""
    refs = {}
    for li in soup.select('li[id^=cite_note]'):
        urls = [a['href'] for a in li.find_all('a', href=True)
                if a['href'].startswith('http') and 'wikipedia.org' not in a['href']
                and 'archive.org' not in a['href'] and 'doi.org' not in a['href']]
        archived = [a['href'] for a in li.find_all('a', href=True) if 'archive.org' in a['href']]
        refs[li['id']] = urls[:1] + archived[:1]
    return refs


def row_refs(tr, refs):
    out = []
    for a in tr.select('sup.reference a[href^="#cite_note"]'):
        for u in refs.get(a['href'][1:], []):
            if u not in out:
                out.append(u)
    return out


def header_labels(rows):
    """Header rows are the leading rows made only of <th>. Returns
    (labels per column, number of header rows)."""
    n = 0
    for tr, row in rows:
        if row and all(el.name == 'th' for el, _ in row):
            n += 1
        else:
            break
    width = max(len(r) for _, r in rows[:max(n, 1)])
    labels = []
    for c in range(width):
        stack = []
        for tr, row in rows[:n]:
            if c < len(row):
                t = clean(row[c][0].get_text(' ', strip=True))
                if t and (not stack or stack[-1] != t):
                    stack.append(t)
        labels.append(stack)
    return labels, n


def is_exit_row(end, election_day):
    # Israeli law bars publishing polls on election day before the polls close,
    # so a row dated election day is an exit poll.
    return end == election_day


def parse_election(k, cfg):
    soup = load_page(cfg)
    refs = references(soup)
    tables = soup.find_all('table', class_='wikitable')
    polls, results_rows, unparsed, variants = [], [], [], []
    for ti in cfg['tables']:
        rows = grid(tables[ti])
        labels, nh = header_labels(rows)
        flat = [' / '.join(s) for s in labels]
        low = [s[-1].lower() if s else '' for s in labels]
        def col(*names):
            for i, l in enumerate(low):
                if l in names:
                    return i
            return None
        c_date = col('date', 'fieldwork date')
        c_firm = col('polling firm', 'poll')
        c_pub = col('publisher')
        c_n = col('sample size')
        list_cols = [i for i, l in enumerate(low)
                     if l and l not in NON_LIST_HEADERS and i not in (c_date, c_firm, c_pub, c_n)]
        others_col = col('others', 'oth.', 'other')

        def row_values(ri, row, texts):
            values, seen, dashes = {}, set(), []
            for i in list_cols + ([others_col] if others_col is not None else []):
                if i >= len(row):
                    continue
                el, _ = row[i]
                if id(el) in seen:
                    continue
                # a cell spanning several list columns is one joint figure
                span = [j for j in list_cols if j < len(row) and row[j][0] is el]
                seen.add(id(el))
                label = ' + '.join(dict.fromkeys(flat[j] for j in span)) if span else 'Others'
                v = parse_value(texts[i])
                if v is None:
                    if texts[i] in ('–', '-', '—'):
                        dashes.append(label)
                    continue
                if v.get('unparsed'):
                    unparsed.append(('value', ti, ri, label, v['raw']))
                values[label] = v
            # A bare dash means "not polled" in some tables and "below the
            # threshold" in others. When the row already adds up to 120 without
            # those lists, the dash can only mean 0 seats.
            total = sum(v['seats'] for v in values.values() if isinstance(v.get('seats'), (int, float)))
            if dashes and abs(total - 120) < 0.5:
                for label in dashes:
                    values[label] = {'seats': 0, 'pct': None, 'raw': '–', 'dash_as_zero': True}
            return values

        section_year = None
        for ri, (tr, row) in enumerate(rows[nh:], start=nh):
            texts = [clean(el.get_text(' ', strip=True)) for el, _ in row]
            # year-divider row ('2013', '2012') spanning the table
            if len({id(el) for el, _ in row}) == 1 and re.fullmatch(r'(19|20)\d\d', texts[0] if texts else ''):
                section_year = int(texts[0])
                continue
            if len(row) < 4:
                continue
            joined = ' '.join(texts)
            firm_t = texts[c_firm] if c_firm is not None and c_firm < len(texts) else ''
            if NOT_A_POLL.search(joined[:200]):
                if re.search(r'election results|final results|election result', joined, re.I):
                    results_rows.append({'table': ti, 'row': ri, 'label': joined[:60],
                                         'values': row_values(ri, row, texts)})
                continue
            # event rows span (almost) the whole width with one cell
            distinct = len({id(el) for el, _ in row})
            if distinct <= 3:
                continue
            # A row whose date and firm cells continue from the row above (rowspan)
            # is a "what if" variant of the same poll (e.g. with two lists merged),
            # not another poll. Only the first row is the published poll.
            if (c_date is not None and c_date < len(row) and not row[c_date][1]
                    and c_firm is not None and c_firm < len(row) and not row[c_firm][1]):
                variants.append((ti, ri))
                continue
            start, end = parse_date(texts[c_date] if c_date is not None else '', cfg['day'], section_year)
            if end is None:
                unparsed.append(('date', ti, ri, texts[:4]))
                continue
            if (cfg['day'] - end).days > KEEP_DAYS or end > cfg['day']:
                continue
            firm, pub = firm_t, (texts[c_pub] if c_pub is not None and c_pub < len(texts) else '')
            values = row_values(ri, row, texts)
            n = None
            if c_n is not None and c_n < len(texts):
                m = re.match(r'^([\d,]+)', texts[c_n])
                n = int(m.group(1).replace(',', '')) if m else None
            polls.append({
                'election': k,
                'date': end.isoformat(),
                'field_start': start.isoformat(),
                'days_before': (cfg['day'] - end).days,
                'firm_raw': firm,
                'publisher_raw': pub,
                'sample_size': n,
                'margin_of_error': None,
                'exit_poll': is_exit_row(end, cfg['day']),
                'values': values,
                'source_urls': row_refs(tr, refs),
                'wiki': {'url': page_url(cfg), 'table': ti, 'row': ri},
            })
    return polls, results_rows, unparsed, variants


def manual_polls(db):
    """Polls from data/polls_manual.json, each with its sources. Skipped when
    Wikipedia already lists the same poll (same election, firm and outlet,
    dates within a day)."""
    if not os.path.exists(MANUAL):
        return []
    out = []
    for m in json.load(open(MANUAL, encoding='utf-8'))['polls']:
        cfg = WIKI_PAGES[m['election']]
        end = date.fromisoformat(m['date'])
        dup = [p for p in db if p['election'] == m['election'] and p['firm_raw'] == m['firm_raw']
               and p['publisher_raw'] == m['publisher_raw'] and abs((date.fromisoformat(p['date']) - end).days) <= 1]
        if dup:
            print(f'  manual poll {m["firm_raw"]} / {m["publisher_raw"]} {m["date"]}: now on Wikipedia ({dup[0]["date"]}), skipped')
            continue
        values = {}
        for label, raw in m['values'].items():
            v = parse_value(raw)
            if v is not None:
                values[label] = v
        out.append({
            'election': m['election'], 'date': m['date'], 'field_start': m.get('field_start', m['date']),
            'days_before': (cfg['day'] - end).days, 'firm_raw': m['firm_raw'], 'publisher_raw': m['publisher_raw'],
            'sample_size': m.get('sample_size'), 'margin_of_error': m.get('margin_of_error'),
            'exit_poll': is_exit_row(end, cfg['day']), 'values': values, 'source_urls': m['source_urls'],
            'wiki': {'url': None, 'table': None, 'row': None}, 'manual': True,
            'verification_he': m.get('verification_he'),
        })
        print(f'  manual poll added: {m["firm_raw"]} / {m["publisher_raw"]} {m["date"]} (total {sum(v["seats"] for v in values.values() if v["seats"] is not None)})')
    return out


def main():
    db, report = [], {}
    for k, cfg in WIKI_PAGES.items():
        polls, res, bad, variants = parse_election(k, cfg)
        report[k] = {'polls': len(polls), 'exit': sum(p['exit_poll'] for p in polls),
                     'results_rows': res, 'unparsed': bad, 'variants_skipped': len(variants)}
        db.extend(polls)
        print(f'K{k}: {len(polls)} polls ({report[k]["exit"]} exit), {len(variants)} variant rows skipped, unparsed {len(bad)}')
        for b in bad[:8]:
            print('   ', b)
    db.extend(manual_polls(db))
    for i, p in enumerate(db):
        p['id'] = f'K{p["election"]}-{i:04d}'
    meta = {
        'source': 'English Wikipedia, "Opinion polling for the <year> Israeli legislative election", '
                  'main seat-projection tables, one pinned revision per page',
        'pages': {k: {'url': page_url(c), 'revid': c['revid'], 'election_day': c['day'].isoformat()}
                  for k, c in WIKI_PAGES.items()},
        'keep_days': KEEP_DAYS,
        'date_note': 'date = the end of the date range Wikipedia lists (fieldwork end, or the '
                     'publication date where only that is given)',
        'margin_of_error_note': 'Wikipedia does not list the margin of error; left empty',
        'sample_size_note': 'listed by Wikipedia only for the K26 campaign',
        'variant_rows_skipped': {k: r['variants_skipped'] for k, r in report.items()},
        'variant_rule': 'rows whose date and firm cells continue from the row above are what-if variants of one poll; only the first row is kept',
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'results_rows': {k: r['results_rows'] for k, r in report.items()},
                   'polls': db}, f, ensure_ascii=False, indent=1)
    labels = []
    for p in db:
        for l in p['values']:
            if l not in labels:
                labels.append(l)
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        base = ['id', 'election', 'date', 'field_start', 'days_before', 'firm_raw', 'publisher_raw',
                'sample_size', 'exit_poll']
        w.writerow(base + labels + ['source_urls', 'wiki_url'])
        for p in db:
            w.writerow([p[c] for c in base] +
                       [(p['values'][l]['raw'] if l in p['values'] else '') for l in labels] +
                       [' '.join(p['source_urls']), p['wiki']['url']])
    print(f'{len(db)} polls -> {OUT_JSON}, {OUT_CSV}')


if __name__ == '__main__':
    main()
