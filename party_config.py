"""
Party configuration for Israeli Knesset elections (21st-25th).
Maps Hebrew ballot symbols to party names, colors, and metadata.
Official data from votes.bechirot.gov.il
"""

# Distinct color palette for maximum visual separation
PARTY_COLORS = {
    'likud': '#2563eb',       # Blue
    'yesh_atid': '#06b6d4',   # Cyan
    'blue_white': '#8b5cf6',  # Purple
    'shas': '#1e3a8a',        # Dark blue
    'utj': '#4b5563',         # Gray
    'labor': '#dc2626',       # Red
    'meretz': '#16a34a',      # Green
    'yisrael_beiteinu': '#db2777', # Pink/Magenta
    'joint_list': '#059669',  # Teal
    'raam': '#84cc16',        # Lime green (Islamic green)
    'hadash_taal': '#f43f5e', # Rose (communist red)
    'balad': '#065f46',       # Dark green
    'yamina': '#ea580c',      # Orange
    'religious_zionism': '#92400e', # Brown
    'new_hope': '#a855f7',    # Light purple
    'kulanu': '#eab308',      # Yellow
    'national_unity': '#7c3aed', # Violet
    'other': '#6b7280',       # Gray
}

# Complete party database with metadata
PARTIES = {
    # Likud
    'מחל': {
        'name': 'הליכוד',
        'name_en': 'Likud',
        'color': PARTY_COLORS['likud'],
        'leader': 'בנימין נתניהו',
        'leader_en': 'Benjamin Netanyahu',
        'leader_image': 'images/leaders/netanyahu.jpg',
        'logo': 'images/logos/likud.png',
        'ideology': 'ימין, לאומנות, ליברליזם כלכלי',
        'founded': 1973,
        'description': 'מפלגת הימין הגדולה בישראל, שולטת בפוליטיקה הישראלית מאז 1977'
    },

    # Yesh Atid (from 24th Knesset onwards, after Blue and White split)
    'פה': {
        'name': 'יש עתיד',
        'name_en': 'Yesh Atid',
        'color': PARTY_COLORS['yesh_atid'],
        'leader': 'יאיר לפיד',
        'leader_en': 'Yair Lapid',
        'leader_image': 'images/leaders/lapid.jpg',
        'logo': '',
        'ideology': 'מרכז, ליברליזם, חילוניות',
        'founded': 2012,
        'description': 'מפלגת מרכז ליברלית, התמקדה בנושאי מעמד הביניים והפרדת דת ומדינה'
    },

    # Shas
    'שס': {
        'name': 'ש״ס',
        'name_en': 'Shas',
        'color': PARTY_COLORS['shas'],
        'leader': 'אריה דרעי',
        'leader_en': 'Aryeh Deri',
        'leader_image': 'images/leaders/deri.jpg',
        'logo': '',
        'ideology': 'חרדית ספרדית, שמרנות חברתית, מסורתיות',
        'founded': 1984,
        'description': 'מפלגה חרדית ספרדית-מזרחית, מייצגת את הציבור החרדי הספרדי'
    },

    # United Torah Judaism
    'ג': {
        'name': 'יהדות התורה',
        'name_en': 'United Torah Judaism',
        'color': PARTY_COLORS['utj'],
        'leader': 'יצחק גולדקנופף',
        'leader_en': 'Yitzhak Goldknopf',
        'leader_image': 'images/leaders/goldknopf.jpg',
        'logo': '',
        'ideology': 'חרדית אשכנזית, שמרנות דתית',
        'founded': 1992,
        'description': 'ברית של אגודת ישראל ודגל התורה, מייצגת את הציבור החרדי האשכנזי'
    },

    # Israel Beiteinu
    'ל': {
        'name': 'ישראל ביתנו',
        'name_en': 'Yisrael Beiteinu',
        'color': PARTY_COLORS['yisrael_beiteinu'],
        'leader': 'אביגדור ליברמן',
        'leader_en': 'Avigdor Lieberman',
        'leader_image': 'images/leaders/lieberman.jpg',
        'logo': '',
        'ideology': 'ימין חילוני, לאומנות, חילוניות',
        'founded': 1999,
        'description': 'מפלגת ימין חילונית, פופולרית בקרב עולים מברית המועצות לשעבר'
    },

    # Labor
    'אמת': {
        'name': 'העבודה',
        'name_en': 'Labor',
        'color': PARTY_COLORS['labor'],
        'leader': 'מרב מיכאלי',
        'leader_en': 'Merav Michaeli',
        'leader_image': 'images/leaders/michaeli.jpg',
        'logo': '',
        'ideology': 'שמאל-מרכז, סוציאל-דמוקרטיה, ציונות',
        'founded': 1968,
        'description': 'מפלגת השמאל הציוני ההיסטורית, הקימה את המדינה והובילה אותה עד 1977'
    },

    # Meretz
    'מרצ': {
        'name': 'מרצ',
        'name_en': 'Meretz',
        'color': PARTY_COLORS['meretz'],
        'leader': 'זהבה גלאון',
        'leader_en': 'Zahava Galon',
        'leader_image': 'images/leaders/galon.jpg',
        'logo': 'images/logos/meretz.png',
        'ideology': 'שמאל, סוציאל-דמוקרטיה, ליברליזם חברתי',
        'founded': 1992,
        'description': 'מפלגת שמאל ליברלית, תומכת בשלום ובזכויות אדם'
    },

    # Joint List
    'ודעם': {
        'name': 'הרשימה המשותפת',
        'name_en': 'Joint List',
        'color': PARTY_COLORS['joint_list'],
        'leader': 'איימן עודה',
        'leader_en': 'Ayman Odeh',
        'leader_image': 'images/leaders/odeh.jpg',
        'logo': 'images/logos/joint_list.png',
        'ideology': 'שמאל ערבי, סוציאליזם, זכויות מיעוטים',
        'founded': 2015,
        'description': 'ברית מפלגות ערביות - חד״ש, תע״ל, בל״ד ורע״ם (עד 2021)'
    },

    # Ra'am-Balad in 21
    'דעם': {
        'name': 'רע״ם-בל״ד',
        'name_en': "Ra'am-Balad",
        'color': PARTY_COLORS['raam'],
        'leader': 'מנסור עבאס',
        'leader_en': 'Mansour Abbas',
        'leader_image': 'images/leaders/abbas.jpg',
        'logo': '',
        'ideology': 'ערבי-אסלאמי, שמרנות חברתית',
        'founded': 2019,
        'description': 'רשימה משותפת של רע״ם ובל״ד בבחירות 2019'
    },

    # Hadash-Ta'al
    'ום': {
        'name': 'חד״ש-תע״ל',
        'name_en': 'Hadash-Taal',
        'color': PARTY_COLORS['hadash_taal'],
        'leader': 'איימן עודה',
        'leader_en': 'Ayman Odeh',
        'leader_image': 'images/leaders/odeh.jpg',
        'logo': '',
        'ideology': 'שמאל, קומוניזם, שוויון יהודי-ערבי',
        'founded': 1977,
        'description': 'החזית הדמוקרטית לשלום ושוויון, מפלגה יהודית-ערבית משותפת'
    },

    # Ra'am
    'עם': {
        'name': 'רע״ם',
        'name_en': "Ra'am",
        'color': PARTY_COLORS['raam'],
        'leader': 'מנסור עבאס',
        'leader_en': 'Mansour Abbas',
        'leader_image': 'images/leaders/abbas.jpg',
        'logo': '',
        'ideology': 'ערבי-אסלאמי, פרגמטיזם, שמרנות חברתית',
        'founded': 1996,
        'description': 'הרשימה הערבית המאוחדת, המפלגה הערבית הראשונה להצטרף לקואליציה'
    },

    # Balad
    'ד': {
        'name': 'בל״ד',
        'name_en': 'Balad',
        'color': PARTY_COLORS['balad'],
        'leader': 'סמי אבו שחאדה',
        'leader_en': 'Sami Abu Shehadeh',
        'leader_image': '',
        'logo': 'images/logos/balad.png',
        'ideology': 'לאומנות ערבית, שמאל',
        'founded': 1995,
        'description': 'ברית לאומית דמוקרטית, מפלגה ערבית לאומית'
    },

    # Yamina / Right Union (טב)
    'טב': {
        'name': 'ימינה',
        'name_en': 'Yamina',
        'color': PARTY_COLORS['yamina'],
        'leader': 'נפתלי בנט',
        'leader_en': 'Naftali Bennett',
        'leader_image': 'images/leaders/bennett.jpg',
        'logo': 'images/logos/yamina.png',
        'ideology': 'ימין דתי-לאומי, התנחלויות',
        'founded': 2018,
        'description': 'מפלגת ימין דתית-לאומית, תומכת בהתנחלויות וריבונות'
    },

    # Yamina in 24 (ב)
    'ב': {
        'name': 'ימינה',
        'name_en': 'Yamina',
        'color': PARTY_COLORS['yamina'],
        'leader': 'נפתלי בנט',
        'leader_en': 'Naftali Bennett',
        'leader_image': 'images/leaders/bennett.jpg',
        'logo': 'images/logos/yamina.png',
        'ideology': 'ימין דתי-לאומי',
        'founded': 2018,
        'description': 'מפלגת ימין דתית-לאומית, בנט כיהן כראש ממשלה 2021-2022'
    },

    # Religious Zionism (ט)
    'ט': {
        'name': 'הציונות הדתית',
        'name_en': 'Religious Zionism',
        'color': PARTY_COLORS['religious_zionism'],
        'leader': 'בצלאל סמוטריץ׳',
        'leader_en': 'Bezalel Smotrich',
        'leader_image': 'images/leaders/smotrich.jpg',
        'logo': '',
        'ideology': 'ימין קיצוני, ציונות דתית, התנחלויות',
        'founded': 2021,
        'description': 'ברית של הציונות הדתית, עוצמה יהודית ונעם'
    },

    # Blue and White / National Unity (כן)
    'כן': {
        'name': 'המחנה הממלכתי',
        'name_en': 'National Unity',
        'color': PARTY_COLORS['national_unity'],
        'leader': 'בני גנץ',
        'leader_en': 'Benny Gantz',
        'leader_image': 'images/leaders/gantz.jpg',
        'logo': '',
        'ideology': 'מרכז-ימין, ביטחוניות, ממלכתיות',
        'founded': 2022,
        'description': 'מפלגת מרכז-ימין בהנהגת בני גנץ, התמזגה עם כחול לבן'
    },

    # Kulanu (כ)
    'כ': {
        'name': 'כולנו',
        'name_en': 'Kulanu',
        'color': PARTY_COLORS['kulanu'],
        'leader': 'משה כחלון',
        'leader_en': 'Moshe Kahlon',
        'leader_image': 'images/leaders/kahlon.jpg',
        'logo': 'images/logos/kulanu.png',
        'ideology': 'מרכז, כלכלה חברתית',
        'founded': 2014,
        'description': 'מפלגת מרכז שהתמקדה ברפורמות כלכליות, התמזגה לליכוד ב-2019'
    },

    # New Hope (ת)
    'ת': {
        'name': 'תקווה חדשה',
        'name_en': 'New Hope',
        'color': PARTY_COLORS['new_hope'],
        'leader': 'גדעון סער',
        'leader_en': "Gideon Sa'ar",
        'leader_image': 'images/leaders/saar.jpg',
        'logo': 'images/logos/new_hope.png',
        'ideology': 'ימין ליברלי, שלטון חוק',
        'founded': 2020,
        'description': 'מפלגת ימין ליברלית שהוקמה על ידי סער לאחר פרישתו מהליכוד'
    },
}

# Default party info for unknown symbols
DEFAULT_PARTY = {
    'name': 'רשימה אחרת',
    'name_en': 'Other List',
    'color': PARTY_COLORS['other'],
    'leader': '',
    'leader_en': '',
    'leader_image': '',
    'logo': '',
    'ideology': '',
    'founded': None,
    'description': 'רשימה קטנה'
}

# Election configurations with OFFICIAL data from votes.bechirot.gov.il
# Voter statistics from Central Elections Committee official results
ELECTIONS = {
    '21': {
        'name': 'הכנסת ה-21',
        'name_en': '21st Knesset',
        'date': '2019-04-09',
        'file': 'ballot21.csv',
        'encoding': 'iso8859_8',
        'ballot_field': 'מספר קלפי',
        # Official voter statistics
        'eligible_voters': 6339279,
        'votes_cast': 4340253,
        'valid_votes': 4268929,
        'turnout_percent': 68.46,
        'major_parties': {
            'symbols': ['מחל', 'פה', 'שס', 'ג', 'ום', 'אמת', 'ל', 'טב', 'מרצ', 'כ', 'דעם'],
            'names': ['הליכוד', 'כחול לבן', 'ש״ס', 'יהדות התורה', 'חד״ש-תע״ל',
                     'העבודה', 'ישראל ביתנו', 'איחוד מפלגות הימין', 'מרצ', 'כולנו', 'רע״ם-בל״ד'],
            'seats': [35, 35, 8, 8, 6, 6, 5, 5, 4, 4, 4]
        }
    },
    '22': {
        'name': 'הכנסת ה-22',
        'name_en': '22nd Knesset',
        'date': '2019-09-17',
        'file': 'ballot22.csv',
        'encoding': 'iso8859_8',
        'ballot_field': 'קלפי',
        # Official voter statistics
        'eligible_voters': 6394030,
        'votes_cast': 4465168,
        'valid_votes': 4421448,
        'turnout_percent': 69.83,
        'major_parties': {
            'symbols': ['פה', 'מחל', 'ודעם', 'שס', 'ל', 'ג', 'טב', 'אמת', 'מרצ'],
            'names': ['כחול לבן', 'הליכוד', 'הרשימה המשותפת', 'ש״ס',
                     'ישראל ביתנו', 'יהדות התורה', 'ימינה', 'העבודה-גשר', 'המחנה הדמוקרטי'],
            'seats': [33, 32, 13, 9, 8, 7, 7, 6, 5]
        }
    },
    '23': {
        'name': 'הכנסת ה-23',
        'name_en': '23rd Knesset',
        'date': '2020-03-02',
        'file': 'ballot23final.csv',
        'encoding': 'iso8859_8',
        'ballot_field': 'קלפי',
        # Official voter statistics
        'eligible_voters': 6453255,
        'votes_cast': 4615135,
        'valid_votes': 4553225,
        'turnout_percent': 71.52,
        'major_parties': {
            'symbols': ['מחל', 'פה', 'ודעם', 'שס', 'ג', 'אמת', 'ל', 'טב'],
            'names': ['הליכוד', 'כחול לבן', 'הרשימה המשותפת', 'ש״ס',
                     'יהדות התורה', 'עבודה-גשר-מרצ', 'ישראל ביתנו', 'ימינה'],
            'seats': [36, 33, 15, 9, 7, 7, 7, 6]
        }
    },
    '24': {
        'name': 'הכנסת ה-24',
        'name_en': '24th Knesset',
        'date': '2021-03-23',
        'file': 'ballot24final.csv',
        'encoding': 'iso8859_8',
        'ballot_field': 'קלפי',
        # Official voter statistics
        'eligible_voters': 6578084,
        'votes_cast': 4436365,
        'valid_votes': 4381020,
        'turnout_percent': 67.44,
        'major_parties': {
            'symbols': ['מחל', 'פה', 'שס', 'כן', 'ב', 'אמת', 'ג', 'ל', 'ט', 'ודעם', 'ת', 'מרצ', 'עם'],
            'names': ['הליכוד', 'יש עתיד', 'ש״ס', 'כחול לבן', 'ימינה', 'העבודה',
                     'יהדות התורה', 'ישראל ביתנו', 'הציונות הדתית', 'הרשימה המשותפת',
                     'תקווה חדשה', 'מרצ', 'רע״ם'],
            'seats': [30, 17, 9, 8, 7, 7, 7, 7, 6, 6, 6, 6, 4]
        }
    },
    '25': {
        'name': 'הכנסת ה-25',
        'name_en': '25th Knesset',
        'date': '2022-11-01',
        'file': 'ballot25.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'קלפי',
        # Official voter statistics
        'eligible_voters': 6788804,
        'votes_cast': 4794593,
        'valid_votes': 4764742,
        'turnout_percent': 70.63,
        'major_parties': {
            'symbols': ['מחל', 'פה', 'ט', 'כן', 'שס', 'ג', 'ל', 'עם', 'ום', 'אמת', 'מרצ', 'ד'],
            'names': ['הליכוד', 'יש עתיד', 'הציונות הדתית', 'המחנה הממלכתי', 'ש״ס',
                     'יהדות התורה', 'ישראל ביתנו', 'רע״ם', 'חד״ש-תע״ל', 'העבודה', 'מרצ', 'בל״ד'],
            'seats': [32, 24, 14, 12, 11, 7, 6, 5, 5, 4, 0, 0]
        }
    }
}

# Election-specific party overrides (for parties that changed over time)
# Key: (election_number, symbol) -> overrides
PARTY_OVERRIDES = {
    # ===== ELECTION 21 (April 2019) =====
    # Blue and White (Kahol Lavan) led by Benny Gantz
    ('21', 'פה'): {
        'name': 'כחול לבן',
        'name_en': 'Blue and White',
        'color': PARTY_COLORS['blue_white'],
        'leader': 'בני גנץ',
        'leader_en': 'Benny Gantz',
        'leader_image': 'images/leaders/gantz.jpg',
        'ideology': 'מרכז, ביטחוניות, ממלכתיות',
        'founded': 2019,
        'description': 'ברית בין יש עתיד, חוסן לישראל ותלם בהנהגת בני גנץ'
    },
    # Union of Right-Wing Parties led by Rafi Peretz
    ('21', 'טב'): {
        'name': 'איחוד מפלגות הימין',
        'name_en': 'Union of Right-Wing Parties',
        'leader': 'רפי פרץ',
        'leader_en': 'Rafi Peretz',
        'leader_image': 'images/leaders/peretz_rafi.jpg',
        'ideology': 'ימין דתי-לאומי, התנחלויות',
        'founded': 2019,
        'description': 'ברית הבית היהודי, האיחוד הלאומי ועוצמה יהודית'
    },
    # Labor led by Avi Gabbay
    ('21', 'אמת'): {
        'leader': 'אבי גבאי',
        'leader_en': 'Avi Gabbay',
        'leader_image': 'images/leaders/gabbay.jpg',
        'description': 'מפלגת העבודה בהנהגת אבי גבאי'
    },
    # Meretz led by Tamar Zandberg
    ('21', 'מרצ'): {
        'leader': 'תמר זנדברג',
        'leader_en': 'Tamar Zandberg',
        'leader_image': 'images/leaders/zandberg.jpg',
        'description': 'מפלגת מרצ בהנהגת תמר זנדברג'
    },
    # UTJ led by Yaakov Litzman
    ('21', 'ג'): {
        'leader': 'יעקב ליצמן',
        'leader_en': 'Yaakov Litzman',
        'leader_image': 'images/leaders/litzman.jpg',
        'description': 'יהדות התורה בהנהגת יעקב ליצמן'
    },

    # ===== ELECTION 22 (September 2019) =====
    # Blue and White led by Benny Gantz
    ('22', 'פה'): {
        'name': 'כחול לבן',
        'name_en': 'Blue and White',
        'color': PARTY_COLORS['blue_white'],
        'leader': 'בני גנץ',
        'leader_en': 'Benny Gantz',
        'leader_image': 'images/leaders/gantz.jpg',
        'ideology': 'מרכז, ביטחוניות, ממלכתיות',
        'founded': 2019,
        'description': 'ברית בין יש עתיד, חוסן לישראל ותלם בהנהגת בני גנץ'
    },
    # Yamina led by Ayelet Shaked (merger of New Right, Jewish Home, National Union)
    ('22', 'טב'): {
        'name': 'ימינה',
        'name_en': 'Yamina',
        'leader': 'איילת שקד',
        'leader_en': 'Ayelet Shaked',
        'leader_image': 'images/leaders/shaked.jpg',
        'ideology': 'ימין דתי-לאומי, התנחלויות',
        'founded': 2019,
        'description': 'ברית הימין החדש, הבית היהודי והאיחוד הלאומי בהנהגת איילת שקד'
    },
    # Labor-Gesher led by Amir Peretz
    ('22', 'אמת'): {
        'name': 'העבודה-גשר',
        'name_en': 'Labor-Gesher',
        'leader': 'עמיר פרץ',
        'leader_en': 'Amir Peretz',
        'leader_image': 'images/leaders/peretz_amir.jpg',
        'description': 'ברית העבודה וגשר בהנהגת עמיר פרץ'
    },
    # UTJ led by Moshe Gafni (took over from Litzman in 2019)
    ('22', 'ג'): {
        'leader': 'משה גפני',
        'leader_en': 'Moshe Gafni',
        'leader_image': 'images/leaders/gafni.jpg',
        'description': 'יהדות התורה בהנהגת משה גפני'
    },
    # Democratic Union (Meretz + Israel Democratic Party + Greens) led by Nitzan Horowitz
    ('22', 'מרצ'): {
        'name': 'המחנה הדמוקרטי',
        'name_en': 'Democratic Union',
        'color': PARTY_COLORS['meretz'],
        'leader': 'ניצן הורוביץ',
        'leader_en': 'Nitzan Horowitz',
        'leader_image': 'images/leaders/horowitz.jpg',
        'ideology': 'שמאל, סוציאל-דמוקרטיה, ליברליזם חברתי',
        'founded': 2019,
        'description': 'ברית מרצ, ישראל דמוקרטית (אהוד ברק) והירוקים בהנהגת ניצן הורוביץ'
    },

    # ===== ELECTION 23 (March 2020) =====
    # Blue and White led by Benny Gantz
    ('23', 'פה'): {
        'name': 'כחול לבן',
        'name_en': 'Blue and White',
        'color': PARTY_COLORS['blue_white'],
        'leader': 'בני גנץ',
        'leader_en': 'Benny Gantz',
        'leader_image': 'images/leaders/gantz.jpg',
        'ideology': 'מרכז, ביטחוניות, ממלכתיות',
        'founded': 2019,
        'description': 'ברית בין יש עתיד, חוסן לישראל ותלם בהנהגת בני גנץ'
    },
    # Yamina led by Naftali Bennett
    ('23', 'טב'): {
        'name': 'ימינה',
        'name_en': 'Yamina',
        'leader': 'נפתלי בנט',
        'leader_en': 'Naftali Bennett',
        'leader_image': 'images/leaders/bennett.jpg',
        'ideology': 'ימין דתי-לאומי, התנחלויות',
        'founded': 2019,
        'description': 'ברית מפלגות הימין הדתי-לאומי בהנהגת נפתלי בנט'
    },
    # Labor-Gesher-Meretz led by Amir Peretz
    ('23', 'אמת'): {
        'name': 'עבודה-גשר-מרצ',
        'name_en': 'Labor-Gesher-Meretz',
        'leader': 'עמיר פרץ',
        'leader_en': 'Amir Peretz',
        'leader_image': 'images/leaders/peretz_amir.jpg',
        'ideology': 'שמאל-מרכז, סוציאל-דמוקרטיה',
        'description': 'ברית העבודה, גשר ומרצ בהנהגת עמיר פרץ'
    },
    # UTJ led by Moshe Gafni
    ('23', 'ג'): {
        'leader': 'משה גפני',
        'leader_en': 'Moshe Gafni',
        'leader_image': 'images/leaders/gafni.jpg',
        'description': 'יהדות התורה בהנהגת משה גפני'
    },

    # ===== ELECTION 24 (March 2021) =====
    # Blue and White (post-split, just Gantz's faction)
    ('24', 'כן'): {
        'name': 'כחול לבן',
        'name_en': 'Blue and White',
        'color': PARTY_COLORS['blue_white'],
        'leader': 'בני גנץ',
        'leader_en': 'Benny Gantz',
        'leader_image': 'images/leaders/gantz.jpg',
        'ideology': 'מרכז, ביטחוניות, ממלכתיות',
        'founded': 2019,
        'description': 'כחול לבן לאחר הפיצול מיש עתיד, בהנהגת בני גנץ'
    },
    # Meretz led by Nitzan Horowitz
    ('24', 'מרצ'): {
        'leader': 'ניצן הורוביץ',
        'leader_en': 'Nitzan Horowitz',
        'leader_image': 'images/leaders/horowitz.jpg',
        'description': 'מפלגת מרצ בהנהגת ניצן הורוביץ'
    },
    # UTJ led by Moshe Gafni
    ('24', 'ג'): {
        'leader': 'משה גפני',
        'leader_en': 'Moshe Gafni',
        'leader_image': 'images/leaders/gafni.jpg',
        'description': 'יהדות התורה בהנהגת משה גפני'
    },

    # ===== ELECTION 25 (November 2022) =====
    # National Unity (Gantz + Saar merger) - default config is correct
    # Meretz led by Zahava Galon (returned to lead party)
    ('25', 'מרצ'): {
        'leader': 'זהבה גלאון',
        'leader_en': 'Zahava Galon',
        'leader_image': 'images/leaders/galon.jpg',
        'description': 'מפלגת מרצ בהנהגת זהבה גלאון, לא עברה את אחוז החסימה'
    },
}


def get_party_info(symbol, election=None):
    """Get party information by ballot symbol, optionally for a specific election."""
    # Check for election-specific override first
    if election and (election, symbol) in PARTY_OVERRIDES:
        base = PARTIES.get(symbol, {**DEFAULT_PARTY, 'name': symbol})
        return {**base, **PARTY_OVERRIDES[(election, symbol)]}
    return PARTIES.get(symbol, {**DEFAULT_PARTY, 'name': symbol})

def get_party_color(symbol, election=None):
    """Get party color by ballot symbol."""
    return get_party_info(symbol, election)['color']

def get_party_name(symbol, election=None):
    """Get party name by ballot symbol."""
    return get_party_info(symbol, election)['name']
