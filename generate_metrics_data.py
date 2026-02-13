#!/usr/bin/env python3
"""
Generate metrics data for the website: Pedersen indices, HHI, cosine similarity.
Outputs site/data/metrics.json

Written by Harel Cain, 2025
"""

import json
import numpy as np
from collections import defaultdict
from pathlib import Path


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── Settlement name normalization ──
# The CEC changed settlement name formatting between elections 22→23,
# removing some spaces. Map variant names to canonical (spaced) form.
SETTLEMENT_NAME_OVERRIDES = {
    'אום אלפחם': 'אום אל פחם',
    'באקה אלגרביה': 'באקה אל גרביה',
    'בועינהנוגידאת': 'בועינה נוגידאת',
    'ביר אלמכסור': 'ביר אל מכסור',
    'בנימינהגבעת עדה': 'בנימינה גבעת עדה',
    'גדידהמכר': 'גדידה מכר',
    'גסר אזרקא': 'גסר א זרקא',
    'דאלית אלכרמל': 'דאלית אל כרמל',
    'דיר אלאסד': 'דיר אל אסד',
    'חפציבה': 'חפצי בה',
    'טובאזנגריה': 'טובא זנגריה',
    'יאנוחגת': 'יאנוח גת',
    'יהודמונוסון': 'יהוד מונוסון',
    'כאוכב אבו אלהיגא': 'כאוכב אבו אל היגא',
    'כסראסמיע': 'כסרא סמיע',
    'כעביהטבאשחגאגרה': 'כעביה טבאש חגאגרה',
    'מגד אלכרום': 'מגד אל כרום',
    'מודיעיןמכביםרעות': 'מודיעין מכבים רעות',
    'מסעודין אלעזאזמה': 'מסעודין אל עזאזמה',
    'מעלותתרשיחא': 'מעלות תרשיחא',
    'ערערהבנגב': 'ערערה בנגב',
    'פרדס חנהכרכור': 'פרדס חנה כרכור',
    'קדימהצורן': 'קדימה צורן',
    'רםאון': 'רם און',
    'שגבשלום': 'שגב שלום',
    'שריגים ליאון': 'שריגים לי און',
}


def normalize_settlement(name):
    """Normalize settlement name to canonical form."""
    return SETTLEMENT_NAME_OVERRIDES.get(name, name)


# ── Party family merge groups for Pedersen index ──
# When parties split or merge between elections, sum their proportions
# to avoid inflating volatility from organizational reshuffling.
FAMILY_MERGE_GROUPS = {
    (21, 22): [
        # Kulanu merged into Likud
        {'הליכוד', 'כולנו'},
        # Ra'am-Balad + Hadash-Taal merged into Joint List
        {'חד״ש-תע״ל', 'רע״ם-בל״ד', 'הרשימה המשותפת'},
        # Bayit Yehudi → Yamina; HaYamin HaChadash → Yamina
        {'הבית היהודי', 'הימין החדש', 'ימינה'},
    ],
    (22, 23): [
        # Meretz (Democratic Union in E22) merged into Labor-Gesher-Meretz (E23)
        {'העבודה-גשר', 'המחנה הדמוקרטי', 'עבודה-גשר-מרצ'},
    ],
    (23, 24): [
        # Blue and White (E23) split into Yesh Atid + Blue and White (E24) + New Hope
        {'כחול לבן', 'יש עתיד', 'תקווה חדשה'},
        # Labor-Gesher-Meretz (E23) split into Labor + Meretz (E24)
        {'עבודה-גשר-מרצ', 'העבודה', 'מרצ'},
        # Joint List split: Ra'am separated
        {'הרשימה המשותפת', 'רע״ם'},
        # Yamina split: Religious Zionism emerged
        {'ימינה', 'הציונות הדתית'},
    ],
    (24, 25): [
        # Blue and White + New Hope → National Unity
        {'כחול לבן', 'תקווה חדשה', 'המחנה הממלכתי'},
        # Yamina disappeared into Religious Zionism
        {'ימינה', 'הציונות הדתית'},
        # Joint List → Hadash-Taal + Balad
        {'הרשימה המשותפת', 'חד״ש-תע״ל', 'בל״ד'},
    ],
}


def merge_proportions(props, merge_groups):
    """Merge party proportions according to family groups.

    For each merge group, sum all member parties' proportions and assign
    the total to a single canonical key (the group as a frozenset label).
    """
    if not merge_groups:
        return props

    # Build party → group mapping
    party_to_group = {}
    for group in merge_groups:
        canonical = min(group)  # deterministic canonical name
        for party in group:
            party_to_group[party] = canonical

    merged = {}
    for party, val in props.items():
        key = party_to_group.get(party, party)
        merged[key] = merged.get(key, 0) + val
    return merged


def pedersen_index(props1, props2):
    """Pedersen volatility index between two elections for a settlement."""
    all_parties = set(list(props1.keys()) + list(props2.keys()))
    return sum(abs(props1.get(p, 0) - props2.get(p, 0)) for p in all_parties) / 2


# ── Party families for averaged HHI ──
# Maps family id to {election_id: party_name_in_that_election}
PARTY_FAMILIES = {
    'likud': {21: 'הליכוד', 22: 'הליכוד', 23: 'הליכוד', 24: 'הליכוד', 25: 'הליכוד'},
    'yesh_atid': {21: 'כחול לבן', 22: 'כחול לבן', 23: 'כחול לבן', 24: 'יש עתיד', 25: 'יש עתיד'},
    'national_unity': {24: 'כחול לבן', 25: 'המחנה הממלכתי'},
    'shas': {21: 'ש״ס', 22: 'ש״ס', 23: 'ש״ס', 24: 'ש״ס', 25: 'ש״ס'},
    'utj': {21: 'יהדות התורה', 22: 'יהדות התורה', 23: 'יהדות התורה', 24: 'יהדות התורה', 25: 'יהדות התורה'},
    'yisrael_beiteinu': {21: 'ישראל ביתנו', 22: 'ישראל ביתנו', 23: 'ישראל ביתנו', 24: 'ישראל ביתנו', 25: 'ישראל ביתנו'},
    'labor': {21: 'העבודה', 22: 'העבודה-גשר', 23: 'עבודה-גשר-מרצ', 24: 'העבודה', 25: 'העבודה'},
    'meretz': {21: 'מרצ', 22: 'המחנה הדמוקרטי', 24: 'מרצ', 25: 'מרצ'},
    'joint_list': {21: 'חד״ש-תע״ל', 22: 'הרשימה המשותפת', 23: 'הרשימה המשותפת', 24: 'הרשימה המשותפת', 25: 'חד״ש-תע״ל'},
    'raam': {21: 'רע״ם-בל״ד', 24: 'רע״ם', 25: 'רע״ם'},
    'yamina': {21: 'הבית היהודי', 22: 'ימינה', 23: 'ימינה', 24: 'ימינה'},
    'religious_zionism': {24: 'הציונות הדתית', 25: 'הציונות הדתית'},
    'new_hope': {24: 'תקווה חדשה'},
    'kulanu': {21: 'כולנו'},
    'balad': {25: 'בל״ד'},
}


def compute_hhi_for_election(all_maps, eid):
    """Compute HHI, effective settlements, and concentration for one election.

    Returns dict: party_name → {hhi, effective_settlements, s50, s90}
    """
    settlements_data = {}
    voter_counts = {}
    for s in all_maps[eid]['settlements']:
        name = normalize_settlement(s['name'])
        # If duplicate (shouldn't happen within single election), keep last
        settlements_data[name] = s.get('proportions', {})
        voter_counts[name] = s.get('voters', 0)

    settlement_names = sorted(settlements_data.keys())
    party_names = [p['name'] for p in all_maps[eid]['parties']]

    result = {}
    for party in party_names:
        vec = np.array([
            settlements_data.get(s, {}).get(party, 0) / 100.0 * voter_counts.get(s, 0)
            for s in settlement_names
        ])
        total = vec.sum()
        if total <= 0:
            continue

        shares = vec / total
        hhi = float(np.sum(shares ** 2))
        effective = round(1.0 / hhi) if hhi > 0 else 0

        # Concentration: settlements for 50%, 75%, 90%, 98%
        idxs = np.argsort(-vec)
        cum = 0
        s50, s75, s90, s98 = None, None, None, None
        for i, idx in enumerate(idxs):
            cum += vec[idx]
            if s50 is None and cum >= total * 0.5:
                s50 = i + 1
            if s75 is None and cum >= total * 0.75:
                s75 = i + 1
            if s90 is None and cum >= total * 0.9:
                s90 = i + 1
            if s98 is None and cum >= total * 0.98:
                s98 = i + 1
                break

        result[party] = {
            'hhi': hhi,
            'effective_settlements': effective,
            'settlements_for_50pct': s50,
            'settlements_for_75pct': s75,
            'settlements_for_90pct': s90,
            'settlements_for_98pct': s98,
        }

    return result


def main():
    # Load all map data
    all_maps = {}
    for eid in [21, 22, 23, 24, 25]:
        all_maps[eid] = load_json(f'site/data/map_{eid}.json')

    # ============================================================
    # 1. Settlement-level Pedersen indices (with family merging)
    # ============================================================
    settlement_props = {}
    settlement_voters = {}
    for eid in [21, 22, 23, 24, 25]:
        for s in all_maps[eid]['settlements']:
            name = normalize_settlement(s['name'])
            if name not in settlement_props:
                settlement_props[name] = {}
                settlement_voters[name] = {}
            settlement_props[name][eid] = s.get('proportions', {})
            settlement_voters[name][eid] = s.get('voters', 0)

    settlement_pedersen = {}
    transitions = [(21, 22), (22, 23), (23, 24), (24, 25)]
    for name, data in settlement_props.items():
        # Skip settlements with 0 voters in latest election
        latest_voters = settlement_voters[name].get(25, 0)
        if latest_voters == 0:
            continue
        per_transition = {}
        for e1, e2 in transitions:
            if e1 in data and e2 in data:
                merge_groups = FAMILY_MERGE_GROUPS.get((e1, e2), [])
                p1 = merge_proportions(data[e1], merge_groups)
                p2 = merge_proportions(data[e2], merge_groups)
                pi = pedersen_index(p1, p2)
                per_transition[f'{e1}_to_{e2}'] = round(pi, 1)
        # Only include settlements with all 4 transitions
        if len(per_transition) == 4:
            avg = round(np.mean(list(per_transition.values())), 1)
            settlement_pedersen[name] = {
                'transitions': per_transition,
                'average': avg,
                'voters': latest_voters,
            }

    # Rank settlements by average Pedersen
    ranked = sorted(settlement_pedersen.items(), key=lambda x: -x[1]['average'])
    for rank, (name, data) in enumerate(ranked, 1):
        data['rank'] = rank
    total_settlements = len(ranked)

    # National median and percentiles
    all_avg = [d['average'] for _, d in settlement_pedersen.items()]
    national_median = round(float(np.median(all_avg)), 1)
    national_mean = round(float(np.mean(all_avg)), 1)

    # ============================================================
    # 2. Party-level metrics (averaged HHI, cosine similarity)
    # ============================================================
    # Compute HHI per election
    hhi_per_election = {}
    for eid in [21, 22, 23, 24, 25]:
        hhi_per_election[eid] = compute_hhi_for_election(all_maps, eid)

    # Average HHI across elections per party family
    party_hhi = {}
    for family_id, elections_map in PARTY_FAMILIES.items():
        hhis = []
        effectives = []
        s50s = []
        s75s = []
        s90s = []
        s98s = []
        latest_party_name = None

        for eid in sorted(elections_map.keys()):
            party_name = elections_map[eid]
            latest_party_name = party_name
            election_hhi = hhi_per_election.get(eid, {}).get(party_name)
            if election_hhi:
                hhis.append(election_hhi['hhi'])
                effectives.append(election_hhi['effective_settlements'])
                if election_hhi['settlements_for_50pct'] is not None:
                    s50s.append(election_hhi['settlements_for_50pct'])
                if election_hhi.get('settlements_for_75pct') is not None:
                    s75s.append(election_hhi['settlements_for_75pct'])
                if election_hhi['settlements_for_90pct'] is not None:
                    s90s.append(election_hhi['settlements_for_90pct'])
                if election_hhi.get('settlements_for_98pct') is not None:
                    s98s.append(election_hhi['settlements_for_98pct'])

        if hhis and latest_party_name:
            avg_hhi = float(np.mean(hhis))
            avg_effective = round(1.0 / avg_hhi) if avg_hhi > 0 else 0
            party_hhi[latest_party_name] = {
                'hhi': round(avg_hhi, 4),
                'effective_settlements': avg_effective,
            }

    # E25 data for cosine similarity and correlations
    e25_settlements = {}
    for s in all_maps[25]['settlements']:
        name = s['name']
        e25_settlements[name] = s.get('proportions', {})

    settlement_names_25 = sorted(e25_settlements.keys())
    parties_25 = list(all_maps[25]['parties'])
    party_names_25 = [p['name'] for p in parties_25]

    e25_voter_counts = {}
    for s in all_maps[25]['settlements']:
        e25_voter_counts[s['name']] = s.get('voters', 0)

    party_vectors = {}
    for party in party_names_25:
        vec = np.array([
            e25_settlements.get(s, {}).get(party, 0) / 100.0 * e25_voter_counts.get(s, 0)
            for s in settlement_names_25
        ])
        party_vectors[party] = vec

    # Cosine similarity between all party pairs (E25 only)
    from scipy.spatial.distance import cosine
    party_cosine = {}
    for p1 in party_names_25:
        sims = {}
        v1 = party_vectors[p1]
        if v1.sum() == 0:
            continue
        for p2 in party_names_25:
            if p1 == p2:
                continue
            v2 = party_vectors[p2]
            if v2.sum() == 0:
                continue
            sim = 1 - cosine(v1, v2)
            sims[p2] = round(sim, 3)
        if sims:
            party_cosine[p1] = sims

    # Station-level correlation between parties (E25)
    tsne_25 = load_json('site/data/tsne_25.json')
    ballot_props = {}
    for s in tsne_25['stations']:
        props = s.get('p', {})
        for party in party_names_25:
            if party not in ballot_props:
                ballot_props[party] = []
            ballot_props[party].append(props.get(party, 0))

    from scipy.stats import pearsonr
    party_correlations = {}
    for p1 in party_names_25:
        if p1 not in ballot_props:
            continue
        corrs = {}
        v1 = np.array(ballot_props[p1])
        for p2 in party_names_25:
            if p1 == p2 or p2 not in ballot_props:
                continue
            v2 = np.array(ballot_props[p2])
            r, _ = pearsonr(v1, v2)
            corrs[p2] = round(r, 3)
        if corrs:
            party_correlations[p1] = corrs

    # Settlement concentration (top N settlements — averaged across elections per family)
    party_concentration = {}
    for family_id, elections_map in PARTY_FAMILIES.items():
        latest_party_name = None
        s50s = []
        s75s = []
        s90s = []
        s98s = []
        total_sett_counts = []

        for eid in sorted(elections_map.keys()):
            party_name = elections_map[eid]
            latest_party_name = party_name
            election_hhi = hhi_per_election.get(eid, {}).get(party_name)
            if election_hhi:
                if election_hhi['settlements_for_50pct'] is not None:
                    s50s.append(election_hhi['settlements_for_50pct'])
                if election_hhi.get('settlements_for_75pct') is not None:
                    s75s.append(election_hhi['settlements_for_75pct'])
                if election_hhi['settlements_for_90pct'] is not None:
                    s90s.append(election_hhi['settlements_for_90pct'])
                if election_hhi.get('settlements_for_98pct') is not None:
                    s98s.append(election_hhi['settlements_for_98pct'])

        if not latest_party_name:
            continue

        # Top 5 from latest election
        top5 = []
        latest_eid = max(elections_map.keys())
        latest_name = elections_map[latest_eid]
        # Use E25 vectors if available, otherwise compute from latest election
        if latest_name in party_vectors:
            vec = party_vectors[latest_name]
            total = vec.sum()
            if total > 0:
                idxs = np.argsort(-vec)
                for idx in idxs[:5]:
                    top5.append({
                        'name': settlement_names_25[idx],
                        'share': round(float(vec[idx] / total * 100), 1)
                    })
                total_sett_count = int(np.sum(vec > 0))
            else:
                total_sett_count = 0
        else:
            # Compute from the latest election data
            sett_data = {}
            voter_data = {}
            for s in all_maps[latest_eid]['settlements']:
                sn = normalize_settlement(s['name'])
                sett_data[sn] = s.get('proportions', {})
                voter_data[sn] = s.get('voters', 0)
            snames = sorted(sett_data.keys())
            vec = np.array([
                sett_data.get(s, {}).get(latest_name, 0) / 100.0 * voter_data.get(s, 0)
                for s in snames
            ])
            total = vec.sum()
            if total > 0:
                idxs = np.argsort(-vec)
                for idx in idxs[:5]:
                    top5.append({
                        'name': snames[idx],
                        'share': round(float(vec[idx] / total * 100), 1)
                    })
                total_sett_count = int(np.sum(vec > 0))
            else:
                total_sett_count = 0

        party_concentration[latest_party_name] = {
            'settlements_for_50pct': round(np.mean(s50s)) if s50s else None,
            'settlements_for_75pct': round(np.mean(s75s)) if s75s else None,
            'settlements_for_90pct': round(np.mean(s90s)) if s90s else None,
            'settlements_for_98pct': round(np.mean(s98s)) if s98s else None,
            'total_settlements': total_sett_count,
            'top5': top5,
        }

    # ============================================================
    # 3. Assemble output
    # ============================================================
    output = {
        'settlement_pedersen': settlement_pedersen,
        'national_stats': {
            'median_pedersen': national_median,
            'mean_pedersen': national_mean,
            'total_settlements': total_settlements,
        },
        'party_hhi': party_hhi,
        'party_cosine_similarity': party_cosine,
        'party_ballot_correlations': party_correlations,
        'party_concentration': party_concentration,
    }

    outpath = Path('site/data/metrics.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {outpath}")
    print(f"  {len(settlement_pedersen)} settlements with Pedersen indices")
    print(f"  {len(party_hhi)} parties with HHI (averaged across elections)")
    print(f"  National median Pedersen: {national_median}%")
    print(f"  National mean Pedersen: {national_mean}%")

    # Show some before/after comparisons
    print(f"\nSettlement name dedup: {len(SETTLEMENT_NAME_OVERRIDES)} variants normalized")
    sample_names = ['אום אל פחם', 'ירושלים', 'תל אביב יפו']
    for name in sample_names:
        p = settlement_pedersen.get(name)
        if p:
            print(f"  {name}: avg={p['average']}%, transitions={p['transitions']}")


if __name__ == '__main__':
    main()
