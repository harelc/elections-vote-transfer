"""Score Knesset polls against the official results -> site/data/poll_accuracy.json

Input:  data/polls_db.json            (build_polls_db.py, from Wikipedia)
        site/data/wiki_official_results.json  (seats; votes = official CEC totals)
        ballot<k>.csv                 (valid votes, and the votes of small lists
                                       missing from the results file)
        poll_list_map.py              (poll column -> final list, pollster and
                                       outlet names, exclusions)
        poll_list_map.py              (also NETANYAHU and ARAB_LISTS per election)

Per poll:
  mae          mean absolute seat error over the lists that matter (a list
               matters if it won seats or the poll gave it seats). Lists that
               merged or split between the poll and the vote are compared as
               one combined unit (see poll_list_map.py).
  bloc_bibi    poll seats minus real seats of the Netanyahu bloc (signed).
  bloc_arab    same for the Arab lists.
  thr_miss     number of lists called on the wrong side of the threshold.
  pct_err      mean absolute vote-share error, only where the poll gave a %.

Per pollster / outlet, per election, per time window: means of the above, a
recency-weighted mean MAE (weight halves every HALF_LIFE days before the
vote), the rank, and the number of polls. Across elections: the mean of the
per-election MAEs, every election weighted equally, and the mean "relative
MAE" = own MAE minus that election's median MAE, which corrects for some
elections being harder to poll than others.

K26 is not scored while wiki_official_results.json holds the simulated
scenario; its polls are kept for viewing.

Usage: python generate_poll_accuracy.py
"""
import json
import math
import os
import statistics
import sys
from collections import defaultdict

import pandas as pd

import party_config
from poll_list_map import (ABSORBED, ARAB_LISTS, EXCLUDE_ROWS, K26_BLOCS, K26_BLOCS_NOTE_HE, NETANYAHU, FINAL_EXTRA, LIST_MAP, LIST_NOTES_HE, MERGE_NOTES_HE,
                           TABLE_OVERRIDES, WITHDREW, classify, label_tokens)

sys.stdout.reconfigure(encoding='utf-8')

POLLS = os.path.join('data', 'polls_db.json')
RESULTS = os.path.join('site', 'data', 'wiki_official_results.json')
OUT = os.path.join('site', 'data', 'poll_accuracy.json')

HALF_LIFE = 14          # days
FEW_POLLS = 3           # fewer polls than this in a window -> flagged
MAX_TOTAL_GAP = 6       # a poll row whose seats add up further than this from 120 is incomplete
MIN_ELECTIONS = 2       # ranked across elections only with at least this many
MIN_LISTS_FOR_DUP = 8   # identical rows with at least this many lists are treated as a copy error
WINDOWS = [
    ('d120', '120 הימים האחרונים', 120),
    ('d90', '90 הימים האחרונים', 90),
    ('d60', '60 הימים האחרונים', 60),
    ('d30', '30 הימים האחרונים', 30),
    ('d14', 'השבועיים האחרונים', 14),
    ('last', 'הסקר האחרון של כל גוף', 120),
    ('exit', 'מדגם ביום הבחירות (22:00)', 0),
]
# Rows checked by hand against the article Wikipedia cites (25/10/2026).
SAMPLE_CHECKS = [
    {'key': ('22', '2019-08-05', 'Midgam', 'Walla!'), 'url': 'https://elections.walla.co.il/item/3251377',
     'he': 'מדגם לוואלה, 5/8/2019: כל המנדטים זהים. בכתבה: 503 משיבים, טעות דגימה 4.4%.'},
    {'key': ('22', '2019-08-28', 'Smith', '103fm/ Maariv'), 'url': 'https://www.maariv.co.il/elections2019/polls/Article-716309',
     'he': 'סמית למעריב: המספרים שמופיעים בכתבה (כחול לבן 31, המחנה הדמוקרטי 7, העבודה-גשר 5, המשותפת 10) זהים. '
           'הכתבה פורסמה ב-30/8, ובוויקיפדיה רשום 28/8 (כנראה תאריך העבודה בשטח).'},
    {'key': ('25', '2022-10-20', 'Camil Fuchs', 'Channel 13'), 'url': 'https://elections.walla.co.il/item/3536051',
     'he': 'קמיל פוקס לחדשות 13, 20/10/2022: כל המנדטים והאחוזים מתחת לאחוז החסימה זהים. בכתבה: 801 משיבים, טעות דגימה 3.5%.'},
    {'key': ('25', '2022-11-01', 'Midgam', 'Channel 12'), 'url': 'https://www.mako.co.il/news-israel-elections/election_2022/Article-a5858c5b6243481026.htm',
     'he': 'המדגם של 2022: הכתבה מביאה את העדכונים המאוחרים של הלילה (00:30–01:30), שבהם המספרים כבר זזו. '
           'בוויקיפדיה רשומים מספרי 22:00, וכך גם כותרת הכתבה של כאן (יש עתיד 22, המחנה הממלכתי 13).'},
    {'key': ('26', '2026-10-23', 'Midgam R&C', 'HaHadashot 12'), 'url': 'https://www.mako.co.il/news-israel-elections/2026/Article-8ea5e45ec2961a1027.htm',
     'he': 'מדגם לחדשות 12, 23/10/2026: כל המנדטים והאחוזים זהים. בכתבה: 1,018 משיבים, טעות דגימה 4.4%.'},
    {'key': ('26', '2026-10-22', 'LRI+P4A', 'Maariv'), 'url': 'https://www.maariv.co.il/news/elections-2026/article-1380289',
     'he': 'מכון לזר למעריב, 23/10/2026: סכומי הגושים (48 ו-54) והאחוזים מתחת לחסימה זהים. בכתבה: 1,048 משיבים, טעות 3%.'},
]
EXIT_BOXES_HE = (
    'לא מצאתי שום פרסום של ערוצי הטלוויזיה או של מכוני הסקרים שמפרט באילו קלפיות נערך המדגם. '
    'רשימת הקלפיות היא סוד מסחרי של מכוני הסקרים, ובכתבה במאקו מ-2019 נאמר במפורש שאי אפשר לחשוף את נתוני '
    'הספירה בקלפיות המדגם. לכן אין כאן "תוצאות אמת של קלפיות המדגם", ולא בניתי רשימה כזו מניחוש. '
    'מה שכן נבדק: תחזית המדגם של כל ערוץ ב-22:00 מול התוצאה הארצית הרשמית.')
EXIT_BOXES_SOURCES = [
    'https://www.mako.co.il/news-israel-elections/elections_2019-interviews/Article-8e1cd0d1184f961006.htm',
    'https://www.timesofisrael.com/botched-tv-exit-polls-earn-vote-of-non-confidence/amp/',
]

ELECTION_LABELS = {'19': '2013 (הכנסת ה-19)', '20': '2015 (הכנסת ה-20)', '21': 'אפריל 2019 (הכנסת ה-21)',
                   '22': 'ספטמבר 2019 (הכנסת ה-22)', '23': '2020 (הכנסת ה-23)', '24': '2021 (הכנסת ה-24)',
                   '25': '2022 (הכנסת ה-25)', '26': '2026 (הכנסת ה-26)'}


def final_results(k, official):
    """{list name: {'seats', 'votes', 'pct'}} and the valid-vote total."""
    cfg = party_config.ELECTIONS[k]
    df = pd.read_csv(cfg['file'], encoding=cfg.get('encoding', 'utf-8'))
    df.columns = [c.strip() for c in df.columns]
    valid_col = 'כשרים' if 'כשרים' in df.columns else 'קולות כשרים'
    valid = float(df[valid_col].sum())
    out = {p['name']: {'seats': p['seats'], 'votes': p['votes']} for p in official[k]}
    for name, sym in FINAL_EXTRA.get(k, {}).items():
        out[name] = {'seats': 0, 'votes': int(df[sym].sum())}
    for v in out.values():
        v['pct'] = round(100 * v['votes'] / valid, 3)
    # the site's party colours, by CEC letter
    mp = cfg.get('major_parties', {})
    sym_of = dict(zip(mp.get('names', []), mp.get('symbols', [])))
    sym_of.update(FINAL_EXTRA.get(k, {}))
    for name, v in out.items():
        try:
            v['color'] = party_config.get_party_color(sym_of[name], k) if name in sym_of else '#6b7280'
        except Exception:
            v['color'] = '#6b7280'
    return out, valid


def k26_is_simulated(official):
    return 'simul' in str(official.get('26_note', '')).lower() or 'simul' in str(official.get('_26_note', '')).lower()


def label_lists(k, table, label):
    """-> (set of final lists, withdrawn?, unknown tokens)"""
    ov = TABLE_OVERRIDES.get((k, table), {})
    if label in ov:
        return set(ov[label]), False, []
    if label in LIST_MAP[k]:
        return set(LIST_MAP[k][label]), False, []
    lists, unknown, withdrawn = set(), [], 0
    toks = label_tokens(label)
    for t in toks:
        if t in ov:
            lists |= set(ov[t])
        elif t in LIST_MAP[k]:
            lists |= set(LIST_MAP[k][t])
        elif t in WITHDREW[k]:
            withdrawn += 1
        else:
            unknown.append(t)
    return lists, (withdrawn == len(toks)), unknown


def score_poll(p, final, k):
    """Compare one poll with the result. Returns a dict (or with 'unscorable')."""
    labels, withdrawn, unknown = {}, [], []
    for label, v in p['values'].items():
        if label == 'Others':
            continue
        lists, wd, unk = label_lists(k, p['wiki']['table'], label)
        if unk:
            unknown += unk
            continue
        if wd:
            withdrawn.append(label)
            continue
        missing = [l for l in lists if l not in final]
        if missing:
            unknown += missing
            continue
        labels[label] = (lists, v)
    if unknown:
        return {'unscorable': 'עמודה שלא מופתה: ' + ', '.join(sorted(set(unknown)))}
    if any(v['seats'] is None for _, v in labels.values()):
        return {'unscorable': 'ערך מנדטים שלא ניתן לקרוא'}

    # connected components of lists linked through poll columns
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for lists, _ in labels.values():
        ls = sorted(lists)
        for a in ls[1:]:
            parent[find(a)] = find(ls[0])
    comps = defaultdict(lambda: {'lists': set(), 'labels': [], 'poll': 0.0, 'pct': None})
    for label, (lists, v) in labels.items():
        c = comps[find(next(iter(lists)))]
        c['lists'] |= lists
        c['labels'].append(label)
        c['poll'] += v['seats']
        # a vote % only counts when the column is the list itself, alone
        c['pcts'] = c.get('pcts', []) + [v.get('pct') if (len(lists) == 1 and label not in ABSORBED.get(k, ())) else None]
    covered = set().union(*[c['lists'] for c in comps.values()]) if comps else set()
    others_lists = {l for l in final if l not in covered}
    others_poll = (p['values'].get('Others') or {}).get('seats') or 0
    groups = []
    for c in comps.values():
        if len(c['labels']) == 1 and c.get('pcts') and c['pcts'][0] is not None:
            c['pct'] = c['pcts'][0]
        else:
            c['pct'] = None
        groups.append({'lists': sorted(c['lists']), 'labels': c['labels'], 'poll': c['poll'],
                       'real': sum(final[l]['seats'] for l in c['lists']), 'pct': c['pct']})
    if others_lists or others_poll:
        groups.append({'lists': sorted(others_lists), 'labels': ['Others'], 'poll': others_poll,
                       'real': sum(final[l]['seats'] for l in others_lists), 'pct': None, 'others': True})
    poll_total = sum(g['poll'] for g in groups) + sum((p['values'][l]['seats'] or 0) for l in withdrawn)
    if abs(poll_total - 120) > MAX_TOTAL_GAP:
        return {'unscorable': f'בטבלת המקור יש לסקר {poll_total:g} מנדטים ולא 120 (חסרות רשימות)'}
    relevant = [g for g in groups if g['poll'] > 0 or g['real'] > 0]
    errs = [abs(g['poll'] - g['real']) for g in relevant]
    res = {
        'mae': round(sum(errs) / len(errs), 3) if errs else None,
        'abs_total': round(sum(errs), 2),
        'n_units': len(relevant),
        'poll_total': round(poll_total, 1),
        'withdrawn': withdrawn,
        'groups': groups,
    }
    for key, bloc in (('bloc_bibi', NETANYAHU.get(k)), ('bloc_arab', ARAB_LISTS.get(k))):
        if not bloc:
            res[key] = None
            continue
        bloc = set(bloc)
        ok, ps = True, 0.0
        for g in groups:
            inside = set(g['lists']) & bloc
            if inside and inside != set(g['lists']):
                ok = False
            if inside == set(g['lists']) and g['lists']:
                ps += g['poll']
        res[key] = round(ps - sum(final[l]['seats'] for l in bloc), 2) if ok else None
    misses, pct_errs, signed = [], [], {}
    for g in groups:
        if len(g['lists']) != 1 or g.get('others'):
            continue
        name = g['lists'][0]
        signed[name] = round(g['poll'] - g['real'], 2)
        if (g['poll'] > 0) != (g['real'] > 0):
            misses.append({'list': name, 'poll_in': g['poll'] > 0})
        if g['pct'] is not None:
            pct_errs.append(abs(g['pct'] - final[name]['pct']))
    res['thr_miss'] = len(misses)
    res['thr_detail'] = misses
    res['pct_err'] = round(sum(pct_errs) / len(pct_errs), 3) if pct_errs else None
    res['pct_n'] = len(pct_errs)
    res['signed'] = signed
    return res


def mapped_values(p, k):
    """The poll's columns with Hebrew final-list names, in table order."""
    out = []
    for label, v in p['values'].items():
        if label == 'Others':
            out.append({'he': 'אחרות', 'raw': v['raw'][:12]})
            continue
        lists, wd, unk = label_lists(k, p['wiki']['table'], label)
        if wd:
            he = label + ' (פרשה)'
        elif unk:
            he = label
        else:
            he = ' + '.join(sorted(lists))
        out.append({'he': he, 'raw': v['raw']})
    return out


def seat_values(p, k):
    """{final list (or 'A + B' when measured together): seats} for the
    columns that map cleanly; used to show what the polls say before there is
    a result to score them against."""
    out = {}
    for label, v in p['values'].items():
        if label == 'Others' or v.get('seats') is None:
            continue
        lists, wd, unk = label_lists(k, p['wiki']['table'], label)
        if wd or unk or not lists:
            continue
        key = ' + '.join(sorted(lists))
        out[key] = out.get(key, 0) + v['seats']
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def aggregate(polls, entity_of):
    """polls already filtered to one election + window. -> {entity: stats}"""
    by = defaultdict(list)
    for p in polls:
        for ent in entity_of(p):
            by[ent].append(p)
    out = {}
    for ent, ps in by.items():
        w = [0.5 ** (p['days_before'] / HALF_LIFE) for p in ps]
        maes = [p['score']['mae'] for p in ps]
        signed = defaultdict(list)
        for p in ps:
            for l, v in p['score']['signed'].items():
                signed[l].append(v)
        out[ent] = {
            'n': len(ps),
            'mae': mean(maes),
            'mae_w': round(sum(a * b for a, b in zip(w, maes)) / sum(w), 3),
            'bibi_abs': mean([abs(p['score']['bloc_bibi']) if p['score']['bloc_bibi'] is not None else None for p in ps]),
            'bibi_signed': mean([p['score']['bloc_bibi'] for p in ps]),
            'arab_abs': mean([abs(p['score']['bloc_arab']) if p['score']['bloc_arab'] is not None else None for p in ps]),
            'arab_signed': mean([p['score']['bloc_arab'] for p in ps]),
            'thr_miss': mean([p['score']['thr_miss'] for p in ps]),
            'pct_err': mean([p['score']['pct_err'] for p in ps]),
            'pct_n': sum(p['score']['pct_n'] for p in ps),
            'signed': {l: mean(v) for l, v in signed.items()},
            'polls': [p['id'] for p in ps],
            'first': min(p['date'] for p in ps), 'last': max(p['date'] for p in ps),
        }
    ranked = sorted(out, key=lambda e: (out[e]['mae'], out[e]['mae_w']))
    for i, e in enumerate(ranked):
        out[e]['rank'] = i + 1
    return out


def window_polls(polls, wkey, days, entity_of):
    if wkey == 'exit':
        return [p for p in polls if p['exit_poll']]
    pre = [p for p in polls if not p['exit_poll'] and 1 <= p['days_before'] <= days]
    if wkey != 'last':
        return pre
    # each entity's latest poll date; every poll it published that day
    latest = {}
    for p in pre:
        for ent in entity_of(p):
            latest[ent] = max(latest.get(ent, ''), p['date'])
    return [dict(p, _only=[e for e in entity_of(p) if latest[e] == p['date']])
            for p in pre if any(latest[e] == p['date'] for e in entity_of(p))]


def main():
    db = json.load(open(POLLS, encoding='utf-8'))
    official = json.load(open(RESULTS, encoding='utf-8'))
    elections = sorted({p['election'] for p in db['polls']}, key=int)
    scored_elections = [k for k in elections if k != '26' or not k26_is_simulated(official)]

    finals, polls_out, checks = {}, [], []
    names = {'pollster': {}, 'outlet': {}}
    for k in elections:
        final, valid = final_results(k, official)
        finals[k] = {'lists': final, 'valid_votes': valid,
                     'simulated': k == '26' and k26_is_simulated(official),
                     'bibi_real': sum(final[l]['seats'] for l in NETANYAHU.get(k, []) if l in final),
                     'arab_real': sum(final[l]['seats'] for l in ARAB_LISTS.get(k, []) if l in final)}
        # Wikipedia's own result row against the official seats. Tables also
        # carry the previous election's results, so keep the closest row.
        best = None
        for r in db['results_rows'].get(k, []) if k != '26' else []:
            fake = {'values': {l: v for l, v in r['values'].items() if v}, 'wiki': {'table': r['table']}}
            s = score_poll(fake, final, k)
            if 'unscorable' not in s and (best is None or s['abs_total'] < best['abs_total']):
                best = {'election': k, 'table': r['table'], 'row_label': r['label'],
                        'abs_total': s['abs_total']}
        if best:
            checks.append(best)

    # Two rows with the very same numbers for every list are almost always a
    # copy error in the Wikipedia table, and there is no telling which row is
    # right, so neither is scored.
    same = defaultdict(list)
    for p in db['polls']:
        if len(p['values']) >= MIN_LISTS_FOR_DUP:
            same[(p['election'], json.dumps({l: v['raw'] for l, v in p['values'].items()}, sort_keys=True))].append(p['id'])
    twin_of = {i: [j for j in ids if j != i] for ids in same.values() if len(ids) > 1 for i in ids}

    for p in db['polls']:
        k = p['election']
        pk, phe, outlets, excluded = classify(p['firm_raw'], p['publisher_raw'])
        excluded = EXCLUDE_ROWS.get((k, p['date'], p['firm_raw'], p['publisher_raw']), excluded)
        if pk:
            names['pollster'][pk] = phe
        for ok, ohe in outlets:
            names['outlet'][ok] = ohe
        rec = {
            'id': p['id'], 'election': k, 'date': p['date'], 'field_start': p['field_start'],
            'days_before': p['days_before'], 'exit_poll': p['exit_poll'],
            'pollster': pk, 'outlets': [o[0] for o in outlets],
            'firm_raw': p['firm_raw'], 'publisher_raw': p['publisher_raw'],
            'sample_size': p['sample_size'], 'excluded': excluded,
            'source_urls': p['source_urls'], 'wiki': p['wiki'],
            'manual': p.get('manual', False), 'verification_he': p.get('verification_he'),
            'raw': {l: v['raw'] for l, v in p['values'].items()},
            'mapped': mapped_values(p, k),
            'seats': seat_values(p, k),
        }
        if p['id'] in twin_of and not excluded:
            rec['unscorable'] = ('המספרים זהים לגמרי לשורה אחרת בטבלת ויקיפדיה (' + ', '.join(twin_of[p['id']]) +
                                 '). כנראה טעות העתקה, ולא ידוע איזו שורה נכונה')
        elif k in scored_elections and not excluded:
            s = score_poll(p, finals[k]['lists'], k)
            if 'unscorable' in s:
                rec['unscorable'] = s['unscorable']
            else:
                rec['score'] = s
        polls_out.append(rec)

    scored = [p for p in polls_out if 'score' in p and p['days_before'] <= 120]
    dims = {
        'pollster': lambda p: p.get('_only') or ([p['pollster']] if p['pollster'] else []),
        'outlet': lambda p: p.get('_only') or p['outlets'],
    }
    agg = {}
    for wkey, _, days in WINDOWS:
        agg[wkey] = {}
        for dim, ent_of in dims.items():
            per_el = {}
            for k in scored_elections:
                base = [p for p in scored if p['election'] == k]
                base_dim = [p for p in base if ent_of(p)]
                wp = window_polls(base_dim, wkey, days, dims[dim])
                if wkey == 'last':
                    ent_fn = lambda p: p['_only']
                else:
                    ent_fn = dims[dim]
                per_el[k] = aggregate(wp, ent_fn)
            # across elections: equal weight per election
            cum = defaultdict(lambda: {'elections': {}, 'rel': {}})
            for k, ents in per_el.items():
                if not ents:
                    continue
                med = statistics.median(e['mae'] for e in ents.values())
                for ent, st in ents.items():
                    cum[ent]['elections'][k] = st['mae']
                    cum[ent]['rel'][k] = round(st['mae'] - med, 3)
            cum_out = {}
            for ent, c in cum.items():
                cum_out[ent] = {
                    'n_elections': len(c['elections']),
                    'mae': mean(list(c['elections'].values())),
                    'rel': mean(list(c['rel'].values())),
                    'by_election': c['elections'], 'rel_by_election': c['rel'],
                    'n_polls': sum(per_el[k][ent]['n'] for k in c['elections']),
                }
            ranked = sorted(cum_out, key=lambda e: (cum_out[e]['n_elections'] < MIN_ELECTIONS,
                                                    cum_out[e]['rel'], cum_out[e]['mae']))
            for i, e in enumerate(ranked):
                cum_out[e]['rank'] = i + 1 if cum_out[e]['n_elections'] >= MIN_ELECTIONS else None
            agg[wkey][dim] = {'by_election': per_el, 'cumulative': cum_out}

    key_to_id = {(p['election'], p['date'], p['firm_raw'], p['publisher_raw']): p['id'] for p in polls_out}
    missing = [c['key'] for c in SAMPLE_CHECKS if c['key'] not in key_to_id]
    assert not missing, f'sample-check rows not found: {missing}'

    # drop the per-poll work fields the page does not need
    for p in polls_out:
        p.pop('_only', None)

    out = {
        'meta': {
            'source': db['meta'],
            'windows': [{'key': w, 'he': he, 'days': d} for w, he, d in WINDOWS],
            'elections': {k: {'he': ELECTION_LABELS[k], 'date': db['meta']['pages'][k]['election_day'],
                              'scored': k in scored_elections} for k in elections},
            'half_life_days': HALF_LIFE, 'few_polls': FEW_POLLS, 'max_total_gap': MAX_TOTAL_GAP,
            'min_elections': MIN_ELECTIONS,
            'names': names,
            'netanyahu': NETANYAHU, 'arab_lists': ARAB_LISTS,
            'k26_blocs': K26_BLOCS, 'k26_blocs_note_he': K26_BLOCS_NOTE_HE,
            'list_notes_he': LIST_NOTES_HE, 'merge_notes_he': MERGE_NOTES_HE,
            'withdrew': WITHDREW,
            'wiki_result_rows_check': checks,
            'sample_checks': [dict({k: v for k, v in c.items() if k != 'key'}, id=key_to_id.get(c['key'], 'לא נמצא'))
                              for c in SAMPLE_CHECKS],
            'exit_boxes_he': EXIT_BOXES_HE, 'exit_boxes_sources': EXIT_BOXES_SOURCES,
        },
        'finals': finals,
        'polls': polls_out,
        'agg': agg,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

    # console summary
    n_sc = sum('score' in p for p in polls_out)
    print(f'{len(polls_out)} polls, {n_sc} scored, '
          f'{sum(1 for p in polls_out if p["excluded"])} excluded, '
          f'{sum(1 for p in polls_out if "unscorable" in p)} unscorable -> {OUT}')
    for p in polls_out:
        if 'unscorable' in p and p['days_before'] <= 120:
            print('  unscorable', p['id'], p['date'], p['unscorable'])
    for c in checks:
        print(f'  wiki result row K{c["election"]} table {c["table"]}: |wiki-official| seats = {c["abs_total"]}')
    for wkey in ('d30', 'last', 'exit'):
        for k in scored_elections:
            ents = agg[wkey]['pollster']['by_election'][k]
            top = sorted(ents.items(), key=lambda x: x[1]['rank'])[:3]
            print(wkey, k, [(names['pollster'][e], s['n'], s['mae']) for e, s in top])


if __name__ == '__main__':
    main()
