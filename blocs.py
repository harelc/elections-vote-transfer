"""One place for bloc, family and sector definitions.

Pages show these definitions as they are written here (command_center_26.json
carries them), so what the site says and what it computes cannot drift.

NETANYAHU  per election: the lists that recommended Benjamin Netanyahu to the
           President after that election (K21 without Yisrael Beiteinu, which
           recommended him in April 2019 but then refused to join). For K26,
           before any recommendation exists, K26_BLOCS below is a stated
           assumption from the lists' public positions, shown on the page as
           an assumption.
FAMILIES   per election: ideological families of the major lists.
Sectors    settlement level, from site/data/settlement_sectors.json.
"""

# Major-list names per election (party_config names).
NETANYAHU = {
    '19': ['הליכוד ישראל ביתנו', 'הבית היהודי', 'ש״ס', 'יהדות התורה'],
    '20': ['הליכוד', 'הבית היהודי', 'כולנו', 'ש״ס', 'יהדות התורה'],
    '21': ['הליכוד', 'הבית היהודי', 'כולנו', 'ש״ס', 'יהדות התורה'],
    '22': ['הליכוד', 'ימינה', 'ש״ס', 'יהדות התורה'],
    '23': ['הליכוד', 'ימינה', 'ש״ס', 'יהדות התורה'],
    '24': ['הליכוד', 'הציונות הדתית', 'ש״ס', 'יהדות התורה'],
    '25': ['הליכוד', 'הציונות הדתית', 'ש״ס', 'יהדות התורה'],
}
ARAB_LISTS = {
    '19': ['רע״ם-תע״ל', 'חד״ש', 'בל״ד'],
    '20': ['הרשימה המשותפת'],
    '21': ['חד״ש-תע״ל', 'רע״ם-בל״ד'],
    '22': ['הרשימה המשותפת'],
    '23': ['הרשימה המשותפת'],
    '24': ['הרשימה המשותפת', 'רע״ם'],
    '25': ['רע״ם', 'חד״ש-תע״ל', 'בל״ד'],
    '26': ['הרשימה המשותפת', 'רע״ם'],
}

# K26: an assumption until recommendations are made after the election.
K26_BLOCS = {
    'right': ['הליכוד', 'יהדות התורה', 'ש״ס', 'עוצמה יהודית', 'הציונות הדתית', 'עמך ישראל',
              'המילואימניקים והכלכלית'],
    'center': ['ישר', 'ביחד', 'הדמוקרטים', 'ישראל ביתנו'],
    'arab': ['הרשימה המשותפת', 'רע״ם'],
}
K26_BLOCS_NOTE_HE = ('הנחה עד שהרשימות ימליצו על מועמד אחרי הבחירות. המילואימניקים והכלכלית '
                     'משויכת לגוש הימין וישראל ביתנו לגוש המרכז, לפי הצהרות לפני הבחירות.')

BLOC_LABELS_HE = {'right': 'גוש הימין והחרדים', 'center': 'גוש המרכז', 'arab': 'הרשימות הערביות'}

# A box's political lean, from its result in the previous election.
LEAN_BUCKETS = [
    ('arab_majority', 'רוב לרשימות הערביות', 'Arab lists majority'),
    ('bibi_65', 'גוש נתניהו 65% ומעלה', 'Netanyahu bloc 65%+'),
    ('bibi_50', 'גוש נתניהו 50%–65%', 'Netanyahu bloc 50–65%'),
    ('mixed', 'מאוזן 35%–50%', 'Balanced 35–50%'),
    ('bibi_low', 'גוש נתניהו מתחת ל-35%', 'Netanyahu bloc under 35%'),
    ('unknown', 'קלפי חדשה, ללא נתון מ-2022', 'New box, no 2022 result'),
]


def lean_bucket(bibi_share, arab_share):
    """bibi_share and arab_share as fractions of valid votes, or None."""
    if bibi_share is None:
        return 'unknown'
    if arab_share is not None and arab_share >= 0.5:
        return 'arab_majority'
    if bibi_share >= 0.65:
        return 'bibi_65'
    if bibi_share >= 0.5:
        return 'bibi_50'
    if bibi_share >= 0.35:
        return 'mixed'
    return 'bibi_low'


SECTOR_LABELS = [
    ('arab', 'יישובים ערביים', 'Arab localities', 'יישוב שהלמ"ס או ויקיפדיה מגדירים כערבי'),
    ('bedouin', 'יישובים בדואיים', 'Bedouin localities', 'לפי תיאור היישוב בוויקיפדיה'),
    ('druze', 'יישובים דרוזיים', 'Druze localities', 'רשימה ידנית של יישובים דרוזיים'),
    ('mixed_city', 'ערים מעורבות', 'Mixed cities', 'הלמ"ס: יישוב מעורב (יהודים וערבים)'),
    ('haredi', 'יישובים חרדיים', 'Haredi localities',
     '7 יישובים בלבד: בני ברק, ביתר עילית, מודיעין עילית, אלעד, רכסים, עמנואל, קרית יערים. '
     'חרדים בירושלים, בבית שמש ובערים אחרות לא נכללים כאן'),
    ('west_bank', 'יהודה ושומרון', 'West Bank settlements', 'יישוב שתיאורו בוויקיפדיה הוא התנחלות'),
    ('other_jewish', 'שאר היישובים היהודיים', 'Other Jewish localities', 'כל יישוב יהודי אחר'),
    ('unclassified', 'לא מסווג', 'Unclassified', 'יישוב שלא נמצא לו סיווג'),
]


def sector_of(entry):
    """entry: a settlement_sectors.json record (or {})."""
    p = entry.get('population')
    if p in ('arab', 'circassian'):
        return 'arab'
    if p in ('bedouin', 'druze'):
        return p
    if p == 'mixed':
        return 'mixed_city'
    if entry.get('haredi'):
        return 'haredi'
    if entry.get('wb'):
        return 'west_bank'
    if p == 'jewish':
        return 'other_jewish'
    return 'unclassified'


def definitions():
    """The definitions as the page shows them."""
    return {
        'sectors': [{'key': k, 'he': he, 'en': en, 'rule_he': rule} for k, he, en, rule in SECTOR_LABELS],
        'lean': [{'key': k, 'he': he, 'en': en} for k, he, en in LEAN_BUCKETS],
        'lean_rule_he': ('נטיית הקלפי נקבעת לפי התוצאה שלה (או של הקלפי המקבילה לה) בבחירות 2022. '
                         'גוש נתניהו ב-2022: ' + ', '.join(NETANYAHU['25']) + '. '
                         'הרשימות הערביות ב-2022: ' + ', '.join(ARAB_LISTS['25']) + '.'),
        'netanyahu_by_election': NETANYAHU,
        'netanyahu_rule_he': 'הרשימות שהמליצו לנשיא על נתניהו אחרי אותן בחירות.',
        'arab_lists_by_election': ARAB_LISTS,
        'k26_blocs': {k: {'he': BLOC_LABELS_HE[k], 'lists': v} for k, v in K26_BLOCS.items()},
        'k26_blocs_note_he': K26_BLOCS_NOTE_HE,
        'turnout_note_he': ('אחוז ההצבעה בקלפי לא כולל את מי שהצביע במעטפה כפולה (חיילים ועוד), '
                            'ולכן הוא נמוך מהאמת בכמה נקודות, בכל המגזרים.'),
    }
