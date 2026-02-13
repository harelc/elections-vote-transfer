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
        'logo': 'images/logos/yesh_atid.png',
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
        'logo': 'images/logos/shas.png',
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
        'logo': 'images/logos/utj.png',
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
        'logo': 'images/logos/yisrael_beiteinu.png',
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
        'logo': 'images/logos/labor.png',
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
        'logo': 'images/logos/raam.png',
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
        'logo': 'images/logos/hadash_taal.png',
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
        'logo': 'images/logos/raam.png',
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
        'leader_image': 'images/leaders/abu_shehadeh.jpg',
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
        'logo': 'images/logos/religious_zionism.png',
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
        'logo': 'images/logos/national_unity.png',
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

    # Small parties (below threshold) - Election 25
    'ז': {
        'name': 'שחר כוח חברתי',
        'name_en': 'Shachar Social Power',
        'color': '#ffde15',
        'leader': "וג'די טאהר",
        'ideology': 'חברתי',
        'description': 'מפלגה ששמה לה למטרה שינוי התרבות הפוליטית בישראל'
    },
    'זך': {
        'name': 'קמ"ה - קידום מעמד הפרט',
        'name_en': 'KAMA',
        'color': '#aeda91',
        'leader': 'דורית בירן',
        'ideology': 'זכויות אדם',
        'description': 'מפלגה המתמקדת בזכויות האדם והפרט מן הזווית הדתית'
    },
    'זנ': {
        'name': 'כח להשפיע',
        'name_en': 'Power to Influence',
        'color': '#6b7280',
        'leader': 'בני אלבז',
        'ideology': 'ספורט וחברה',
        'description': 'מפלגה לקידום הספורט בישראל ותמיכה במתמודדים בחדלות פרעון'
    },
    'זץ': {
        'name': 'צומת',
        'name_en': 'Tzomet',
        'color': '#262558',
        'leader': 'משה גרין',
        'ideology': 'ימין לאומי',
        'description': 'מפלגה ציונית לאומית, מתמקדת במעמד החקלאים'
    },
    'יז': {
        'name': 'הכלכלית החדשה',
        'name_en': 'New Economic Party',
        'color': '#fcaf12',
        'leader': 'ירון זליכה',
        'ideology': 'כלכלי',
        'description': 'מפלגה המתמקדת בנושאים כלכליים, הוקמה ע"י החשב הכללי לשעבר'
    },
    'י': {
        'name': 'ישראל חופשית דמוקרטית',
        'name_en': 'Free Democratic Israel',
        'color': '#70b9b8',
        'leader': 'אלי אבידר',
        'ideology': 'חילוניות',
        'description': 'מפלגה חילונית הדוגלת בגיוס בני ישיבות ומאבק בשחיתות'
    },
    'ינ': {
        'name': 'איחוד בני הברית',
        'name_en': 'Union of Allies',
        'color': '#8948fa',
        'leader': 'בשארה שליאן',
        'ideology': 'נוצרי',
        'description': 'מפלגת ימאים נוצרים'
    },
    'יץ': {
        'name': 'צו השעה',
        'name_en': 'Order of the Hour',
        'color': '#6b7280',
        'leader': 'אורי דויד חי',
        'ideology': 'גמלאים ונכים',
        'description': 'מפלגה לקידום גמלאים, בעלי מוגבלויות ונהגי מוניות'
    },
    'יק': {
        'name': 'הגוש התנ"כי',
        'name_en': 'Biblical Bloc',
        'color': '#1163bf',
        'leader': 'דניס ליפקין',
        'ideology': 'נוצרי-יהודי',
        'description': 'מפלגה נוצרית-יהודית לייצוג הולם של נוצרים בישראל'
    },
    'ך': {
        'name': 'אני ואתה',
        'name_en': 'Ani VeAta',
        'color': '#101b68',
        'leader': 'אלון גלעדי',
        'ideology': 'סוציאליזם',
        'description': 'מפלגה סוציאליסטית המבקשת להילחם בתופעת הון-שלטון'
    },
    'נז': {
        'name': 'כבוד האדם',
        'name_en': 'Human Dignity',
        'color': '#6b7280',
        'leader': 'ארקדי פוגץ',
        'ideology': 'עולים',
        'description': 'מפלגה המייצגת עולי ברית המועצות לשעבר'
    },
    'ני': {
        'name': 'נתיב',
        'name_en': 'Nativ',
        'color': '#2764a7',
        'leader': 'איל כהן',
        'ideology': 'נכים',
        'description': 'מפלגה לקידום זכויות בעלי מוגבלויות'
    },
    'נף': {
        'name': 'שמע',
        'name_en': 'Shema',
        'color': '#6fa4e8',
        'leader': 'נפתלי גולדמן',
        'ideology': 'שמרני דתי',
        'description': 'מפלגה שמרנית הדוגלת בערכים דתיים מסורתיים'
    },
    'נץ': {
        'name': 'העצמאים החדשים',
        'name_en': 'New Independents',
        'color': '#4ea9ff',
        'leader': 'יורם מועלמי',
        'ideology': 'עסקים קטנים',
        'description': 'מפלגה לשיפור מצב העסקים הקטנים והבינוניים'
    },
    'נק': {
        'name': 'יש כיוון',
        'name_en': 'Yesh Kivun',
        'color': '#66ad2d',
        'leader': 'עמוס דב סילבר',
        'ideology': 'ליברטריאנית',
        'description': 'מפלגה להעצמת חירות הפרט, הוקמה ע"י מייסד טלגראס'
    },
    'נר': {
        'name': 'אנחנו',
        'name_en': 'Anachnu',
        'color': '#056fab',
        'leader': "מוש חוג'ה",
        'ideology': 'רפורמה פוליטית',
        'description': 'מפלגה המבקשת לשנות את שיטת הבחירות בישראל'
    },
    'ף': {
        'name': 'הפיראטים',
        'name_en': 'Pirates',
        'color': '#000000',
        'leader': 'נועם כוזר',
        'ideology': 'חופש מידע',
        'description': 'דוגלת בדמוקרטיה דינמית, רפורמה בזכויות יוצרים ושקיפות'
    },
    'צ': {
        'name': 'צעירים בוערים',
        'name_en': 'Burning Youth',
        'color': '#f72222',
        'leader': 'הדר מוכתר',
        'ideology': 'צעירים',
        'description': 'מפלגה לייצוג צעירים וטיפול במשבר הדיור ויוקר המחיה'
    },
    'ץ': {
        'name': 'מנהיגות חברתית',
        'name_en': 'Social Leadership',
        'color': '#6b7280',
        'leader': 'אילן משיחא יר-זנבר',
        'ideology': 'חברתי',
        'description': 'מפלגה המתמודדת לכנסת מאז הכנסת ה-19'
    },
    'ק': {
        'name': 'קול הסביבה והחי',
        'name_en': 'Voice of Environment',
        'color': '#6cb334',
        'leader': 'דרור בן-עמי',
        'ideology': 'סביבה',
        'description': 'מפלגה לקידום איכות הסביבה, החיים והבריאות'
    },
    'קי': {
        'name': 'הלב היהודי',
        'name_en': 'Jewish Heart',
        'color': '#0002fd',
        'leader': 'אלי יוסף',
        'ideology': 'שלום',
        'description': 'מפלגה למניעת מכירת נשק למדינות המבצעות פשעי מלחמה'
    },
    'קך': {
        'name': 'סדר חדש',
        'name_en': 'New Order',
        'color': '#215191',
        'leader': 'אופק אביטל',
        'ideology': 'גיל שלישי',
        'description': 'מפלגה לקידום רמת חיי האזרחים הוותיקים'
    },
    'קנ': {
        'name': 'קול',
        'name_en': 'Kol',
        'color': '#6b7280',
        'leader': 'נועם קולמן',
        'ideology': 'עצמאים',
        'description': 'מפלגה לעצמאיים, פרילנסרים, פנסיונרים ובני הגיל השלישי'
    },
    'קץ': {
        'name': 'באומץ בשבילך',
        'name_en': 'Boldly for You',
        'color': '#8fb73d',
        'leader': 'צביקה גרנות',
        'ideology': 'חירות',
        'description': 'מפלגה לקידום חירות הפרט, התנגדה למדיניות הקורונה'
    },
    'נ': {
        'name': 'הימין החדש',
        'name_en': 'New Right',
        'color': '#1e40af',
        'leader': 'נפתלי בנט ואיילת שקד',
        'logo': 'images/logos/new_right.png',
        'ideology': 'ימין, ליברלי-לאומי',
        'description': 'מפלגת ימין בראשות נפתלי בנט ואיילת שקד, לא עברה את אחוז החסימה בבחירות לכנסת ה-21'
    },
    'ר': {
        'name': 'הרשימה הערבית',
        'name_en': 'Arab List',
        'color': '#2d8a4e',
        'leader': 'מוחמד כנעאן',
        'ideology': 'ערבי',
        'description': 'הרשימה הערבית בראשות מוחמד כנעאן'
    },
    'רז': {
        'name': 'כבוד ומסורת',
        'name_en': 'Honor and Tradition',
        'color': '#b10277',
        'leader': 'סטלה ויינשטיין',
        'ideology': 'ימין חברתי',
        'description': 'מפלגה למאבק בבירוקרטיה ועידוד שוק חופשי'
    },
    'ת': {
        'name': 'עלה ירוק',
        'name_en': 'Green Leaf',
        'color': '#658932',
        'leader': 'דקל עוזר',
        'ideology': 'ליברלית',
        'description': 'מפלגה ליברלית התומכת בלגליזציה של הקנאביס'
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
    '16': {
        'name': 'הכנסת ה-16',
        'name_en': '16th Knesset',
        'date': '2003-01-28',
        'file': 'ballot16.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'מספר קלפי',
        'ballot_number_divisor': 10,  # K16 uses x10 ballot numbering (10,20,30...)
        'eligible_voters': 4720075,
        'votes_cast': 3200773,
        'valid_votes': 3148364,
        'turnout_percent': 67.81,
        'major_parties': {
            'symbols': ['מחל', 'אמת', 'יש', 'שס', 'ל', 'מרצ', 'ב', 'ג', 'ו', 'ם', 'ד', 'כן', 'עם'],
            'names': ['הליכוד', 'העבודה', 'שינוי', 'ש״ס', 'האיחוד הלאומי', 'מרצ',
                     'המפד״ל', 'יהדות התורה', 'חד״ש', 'עם אחד', 'בל״ד', 'ישראל בעלייה', 'הרשימה הערבית המאוחדת'],
            'seats': [38, 19, 15, 11, 7, 6, 6, 5, 3, 3, 3, 2, 2]
        }
    },
    '17': {
        'name': 'הכנסת ה-17',
        'name_en': '17th Knesset',
        'date': '2006-03-28',
        'file': 'ballot17.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'מספר קלפי',
        'ballot_number_divisor': 10,  # K17 uses x10 ballot numbering (10,20,30...)
        'eligible_voters': 5014622,
        'votes_cast': 3186739,
        'valid_votes': 3137064,
        'turnout_percent': 63.55,
        'major_parties': {
            'symbols': ['כן', 'אמת', 'שס', 'מחל', 'ל', 'טב', 'זך', 'ג', 'מרצ', 'עם', 'ו', 'ד'],
            'names': ['קדימה', 'העבודה-מימד', 'ש״ס', 'הליכוד', 'ישראל ביתנו',
                     'האיחוד הלאומי-מפד״ל', 'גיל', 'יהדות התורה', 'מרצ',
                     'הרשימה הערבית המאוחדת-התחדשות ערבית', 'חד״ש', 'בל״ד'],
            'seats': [29, 19, 12, 12, 11, 9, 7, 6, 5, 4, 3, 3]
        }
    },
    '18': {
        'name': 'הכנסת ה-18',
        'name_en': '18th Knesset',
        'date': '2009-02-10',
        'file': 'ballot18.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'מספר קלפי',
        'eligible_voters': 5278985,
        'votes_cast': 3416587,
        'valid_votes': 3373490,
        'turnout_percent': 64.72,
        'major_parties': {
            'symbols': ['כן', 'מחל', 'ל', 'אמת', 'שס', 'ג', 'עם', 'ט', 'ו', 'מרצ', 'ב', 'ד'],
            'names': ['קדימה', 'הליכוד', 'ישראל ביתנו', 'העבודה', 'ש״ס',
                     'יהדות התורה', 'רע״ם-תע״ל', 'האיחוד הלאומי', 'חד״ש', 'מרצ', 'הבית היהודי', 'בל״ד'],
            'seats': [28, 27, 15, 13, 11, 5, 4, 4, 4, 3, 3, 3]
        }
    },
    '19': {
        'name': 'הכנסת ה-19',
        'name_en': '19th Knesset',
        'date': '2013-01-22',
        'file': 'ballot19.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'מספר קלפי',
        'eligible_voters': 5656705,
        'votes_cast': 3834136,
        'valid_votes': 3792742,
        'turnout_percent': 67.78,
        'major_parties': {
            'symbols': ['מחל', 'פה', 'אמת', 'טב', 'שס', 'ג', 'צפ', 'מרץ', 'עם', 'ו', 'ד', 'כן'],
            'names': ['הליכוד ישראל ביתנו', 'יש עתיד', 'העבודה', 'הבית היהודי', 'ש״ס',
                     'יהדות התורה', 'התנועה', 'מרצ', 'רע״ם-תע״ל', 'חד״ש', 'בל״ד', 'קדימה'],
            'seats': [31, 19, 15, 12, 11, 7, 6, 6, 4, 4, 3, 2]
        }
    },
    '20': {
        'name': 'הכנסת ה-20',
        'name_en': '20th Knesset',
        'date': '2015-03-17',
        'file': 'ballot20.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'מספר קלפי',
        'eligible_voters': 5881696,
        'votes_cast': 4254738,
        'valid_votes': 4210884,
        'turnout_percent': 72.34,
        'major_parties': {
            'symbols': ['מחל', 'אמת', 'ודעם', 'פה', 'כ', 'טב', 'שס', 'ל', 'ג', 'מרצ'],
            'names': ['הליכוד', 'המחנה הציוני', 'הרשימה המשותפת', 'יש עתיד', 'כולנו',
                     'הבית היהודי', 'ש״ס', 'ישראל ביתנו', 'יהדות התורה', 'מרצ'],
            'seats': [30, 24, 13, 11, 10, 8, 7, 6, 6, 5]
        }
    },
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
            'symbols': ['מחל', 'פה', 'שס', 'ג', 'ום', 'אמת', 'ל', 'טב', 'מרצ', 'כ', 'דעם', 'ז', 'נ'],
            'names': ['הליכוד', 'כחול לבן', 'ש״ס', 'יהדות התורה', 'חד״ש-תע״ל',
                     'העבודה', 'ישראל ביתנו', 'הבית היהודי', 'מרצ', 'כולנו', 'רע״ם-בל״ד', 'זהות', 'הימין החדש'],
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
        'file': 'ballot23.csv',
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
        'file': 'ballot24.csv',
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
    },
    '26': {
        'name': 'הכנסת ה-26',
        'name_en': '26th Knesset',
        'date': '2026-??-??',
        'file': 'ballot26.csv',
        'encoding': 'utf-8-sig',
        'ballot_field': 'קלפי',
        # TBD - placeholder values until official data available
        'eligible_voters': 0,
        'votes_cast': 0,
        'valid_votes': 0,
        'turnout_percent': 0,
        'major_parties': {
            'symbols': [],
            'names': [],
            'seats': []
        }
    }
}

# Election-specific party overrides (for parties that changed over time)
# Key: (election_number, symbol) -> overrides
PARTY_OVERRIDES = {
    # ===== ELECTION 16 (January 2003) =====
    ('16', 'מחל'): {
        'leader': 'אריאל שרון',
        'leader_en': 'Ariel Sharon',
        'leader_image': 'images/leaders/sharon.jpg',
    },
    ('16', 'יש'): {
        'name': 'שינוי',
        'name_en': 'Shinui',
        'color': '#f59e0b',
        'leader': 'טומי לפיד',
        'leader_en': 'Tommy Lapid',
        'leader_image': 'images/leaders/tommy_lapid.jpg',
    },
    ('16', 'שס'): {
        'leader': 'אלי ישי',
        'leader_en': 'Eli Yishai',
        'leader_image': 'images/leaders/yishai.jpg',
    },
    ('16', 'ל'): {
        'name': 'האיחוד הלאומי',
        'name_en': 'National Union',
        'color': '#ea580c',
        'leader': 'אביגדור ליברמן',
        'leader_en': 'Avigdor Lieberman',
        'leader_image': 'images/leaders/lieberman.jpg',
    },
    ('16', 'ב'): {
        'name': 'המפד״ל',
        'name_en': 'NRP (Mafdal)',
        'color': '#92400e',
        'leader': 'אפי איתם',
        'leader_en': 'Effi Eitam',
        'leader_image': 'images/leaders/eitam.jpg',
    },
    ('16', 'ג'): {
        'leader': 'אברהם רביץ',
        'leader_en': 'Avraham Ravitz',
        'leader_image': 'images/leaders/ravitz.jpg',
    },
    ('16', 'ו'): {
        'name': 'חד״ש',
        'name_en': 'Hadash',
        'color': '#dc2626',
        'leader': 'מוחמד ברכה',
        'leader_en': 'Muhammad Barakeh',
        'leader_image': 'images/leaders/barakeh.jpg',
    },
    ('16', 'ם'): {
        'name': 'עם אחד',
        'name_en': 'Am Ehad',
        'color': '#f97316',
        'leader': 'עמיר פרץ',
        'leader_en': 'Amir Peretz',
        'leader_image': 'images/leaders/peretz_amir.jpg',
    },
    ('16', 'ד'): {
        'name': 'בל״ד',
        'name_en': 'Balad',
        'color': '#065f46',
        'leader': 'עזמי בשארה',
        'leader_en': 'Azmi Bishara',
        'leader_image': 'images/leaders/bishara.jpg',
    },
    ('16', 'כן'): {
        'name': 'ישראל בעלייה',
        'name_en': 'Yisrael BaAliyah',
        'color': '#3b82f6',
        'leader': 'נתן שרנסקי',
        'leader_en': 'Natan Sharansky',
        'leader_image': 'images/leaders/sharansky.jpg',
    },
    ('16', 'עם'): {
        'name': 'הרשימה הערבית המאוחדת',
        'name_en': 'United Arab List',
        'color': '#84cc16',
        'leader': 'עבד אלמאלכ דהאמשה',
        'leader_en': 'Abdulmalik Dehamshe',
        'leader_image': 'images/leaders/dehamshe.jpg',
    },
    ('16', 'אמת'): {
        'leader': 'עמרם מצנע',
        'leader_en': 'Amram Mitzna',
        'leader_image': 'images/leaders/mitzna.jpg',
    },
    ('16', 'מרצ'): {
        'leader': 'יוסי שריד',
        'leader_en': 'Yossi Sarid',
        'leader_image': 'images/leaders/sarid.jpg',
    },

    # ===== ELECTION 17 (March 2006) =====
    ('17', 'כן'): {
        'name': 'קדימה',
        'name_en': 'Kadima',
        'color': '#f59e0b',
        'leader': 'אהוד אולמרט',
        'leader_en': 'Ehud Olmert',
        'leader_image': 'images/leaders/olmert.jpg',
    },
    ('17', 'אמת'): {
        'name': 'העבודה-מימד',
        'name_en': 'Labor-Meimad',
        'leader': 'עמיר פרץ',
        'leader_en': 'Amir Peretz',
        'leader_image': 'images/leaders/peretz_amir.jpg',
    },
    ('17', 'שס'): {
        'leader': 'אלי ישי',
        'leader_en': 'Eli Yishai',
        'leader_image': 'images/leaders/yishai.jpg',
    },
    ('17', 'ל'): {
        'name': 'ישראל ביתנו',
        'name_en': 'Yisrael Beiteinu',
        'color': PARTY_COLORS['yisrael_beiteinu'],
        'leader': 'אביגדור ליברמן',
        'leader_en': 'Avigdor Lieberman',
        'leader_image': 'images/leaders/lieberman.jpg',
    },
    ('17', 'טב'): {
        'name': 'האיחוד הלאומי-מפד״ל',
        'name_en': 'National Union-NRP',
        'color': '#ea580c',
        'leader': 'בני אלון',
        'leader_en': 'Benny Elon',
        'leader_image': 'images/leaders/elon.jpg',
    },
    ('17', 'זך'): {
        'name': 'גיל',
        'name_en': 'Gil (Pensioners)',
        'color': '#a3a3a3',
        'leader': 'רפי איתן',
        'leader_en': 'Rafi Eitan',
        'leader_image': 'images/leaders/rafi_eitan.jpg',
    },
    ('17', 'ג'): {
        'leader': 'יעקב ליצמן',
        'leader_en': 'Yaakov Litzman',
        'leader_image': 'images/leaders/litzman.jpg',
    },
    ('17', 'עם'): {
        'name': 'הרשימה הערבית המאוחדת-התחדשות ערבית',
        'name_en': 'UAL-Arab Renewal',
        'color': '#84cc16',
        'leader': 'איברהים צרצור',
        'leader_en': 'Ibrahim Sarsur',
        'leader_image': 'images/leaders/sarsur.jpg',
    },
    ('17', 'ו'): {
        'name': 'חד״ש',
        'name_en': 'Hadash',
        'color': '#dc2626',
        'leader': 'מוחמד ברכה',
        'leader_en': 'Muhammad Barakeh',
        'leader_image': 'images/leaders/barakeh.jpg',
    },
    ('17', 'ד'): {
        'name': 'בל״ד',
        'name_en': 'Balad',
        'color': '#065f46',
        'leader': 'עזמי בשארה',
        'leader_en': 'Azmi Bishara',
        'leader_image': 'images/leaders/bishara.jpg',
    },
    ('17', 'מרצ'): {
        'leader': 'יוסי ביילין',
        'leader_en': 'Yossi Beilin',
        'leader_image': 'images/leaders/beilin.jpg',
    },

    # ===== ELECTION 18 (February 2009) =====
    ('18', 'כן'): {
        'name': 'קדימה',
        'name_en': 'Kadima',
        'color': '#f59e0b',
        'leader': 'ציפי לבני',
        'leader_en': 'Tzipi Livni',
        'leader_image': 'images/leaders/livni.jpg',
    },
    ('18', 'אמת'): {
        'leader': 'אהוד ברק',
        'leader_en': 'Ehud Barak',
        'leader_image': 'images/leaders/barak.jpg',
    },
    ('18', 'שס'): {
        'leader': 'אלי ישי',
        'leader_en': 'Eli Yishai',
        'leader_image': 'images/leaders/yishai.jpg',
    },
    ('18', 'ל'): {
        'name': 'ישראל ביתנו',
        'name_en': 'Yisrael Beiteinu',
        'color': PARTY_COLORS['yisrael_beiteinu'],
        'leader': 'אביגדור ליברמן',
        'leader_en': 'Avigdor Lieberman',
        'leader_image': 'images/leaders/lieberman.jpg',
    },
    ('18', 'ג'): {
        'leader': 'יעקב ליצמן',
        'leader_en': 'Yaakov Litzman',
        'leader_image': 'images/leaders/litzman.jpg',
    },
    ('18', 'עם'): {
        'name': 'רע״ם-תע״ל',
        'name_en': 'Ra\'am-Ta\'al',
        'color': '#84cc16',
        'leader': 'איברהים צרצור',
        'leader_en': 'Ibrahim Sarsur',
        'leader_image': 'images/leaders/sarsur.jpg',
    },
    ('18', 'ט'): {
        'name': 'האיחוד הלאומי',
        'name_en': 'National Union',
        'color': '#ea580c',
        'leader': 'יעקב כץ',
        'leader_en': "Ya'akov Katz",
        'leader_image': '',
    },
    ('18', 'ו'): {
        'name': 'חד״ש',
        'name_en': 'Hadash',
        'color': '#dc2626',
        'leader': 'מוחמד ברכה',
        'leader_en': 'Muhammad Barakeh',
        'leader_image': 'images/leaders/barakeh.jpg',
    },
    ('18', 'מרצ'): {
        'leader': 'חיים אורון',
        'leader_en': 'Haim Oron',
        'leader_image': 'images/leaders/oron.jpg',
    },
    ('18', 'ב'): {
        'name': 'הבית היהודי',
        'name_en': 'The Jewish Home',
        'color': '#92400e',
        'leader': 'דניאל הרשקוביץ',
        'leader_en': 'Daniel Hershkowitz',
        'leader_image': 'images/leaders/hershkowitz.jpg',
    },
    ('18', 'ד'): {
        'name': 'בל״ד',
        'name_en': 'Balad',
        'color': '#065f46',
        'leader': "ג'מאל זחאלקה",
        'leader_en': 'Jamal Zahalka',
        'leader_image': 'images/leaders/zahalka.jpg',
    },

    # ===== ELECTION 19 (January 2013) =====
    ('19', 'מחל'): {
        'name': 'הליכוד ישראל ביתנו',
        'name_en': 'Likud Yisrael Beiteinu',
        'leader_image': 'images/leaders/netanyahu.jpg',
    },
    ('19', 'שס'): {
        'leader': 'אריה דרעי',
        'leader_en': 'Aryeh Deri',
        'leader_image': 'images/leaders/deri.jpg',
    },
    ('19', 'ג'): {
        'leader': 'יעקב ליצמן',
        'leader_en': 'Yaakov Litzman',
        'leader_image': 'images/leaders/litzman.jpg',
    },
    ('19', 'צפ'): {
        'name': 'התנועה',
        'name_en': 'Hatnuah',
        'color': '#a855f7',
        'leader': 'ציפי לבני',
        'leader_en': 'Tzipi Livni',
        'leader_image': 'images/leaders/livni.jpg',
    },
    ('19', 'מרץ'): {
        'name': 'מרצ',
        'name_en': 'Meretz',
        'color': PARTY_COLORS['meretz'],
        'leader': 'זהבה גלאון',
        'leader_en': 'Zahava Galon',
        'leader_image': 'images/leaders/galon.jpg',
    },
    ('19', 'עם'): {
        'name': 'רע״ם-תע״ל',
        'name_en': 'Ra\'am-Ta\'al',
        'color': '#84cc16',
        'leader': 'איברהים צרצור',
        'leader_en': 'Ibrahim Sarsur',
        'leader_image': 'images/leaders/sarsur.jpg',
    },
    ('19', 'ו'): {
        'name': 'חד״ש',
        'name_en': 'Hadash',
        'color': '#dc2626',
        'leader': 'מוחמד ברכה',
        'leader_en': 'Muhammad Barakeh',
        'leader_image': 'images/leaders/barakeh.jpg',
    },
    ('19', 'ד'): {
        'name': 'בל״ד',
        'name_en': 'Balad',
        'color': '#065f46',
        'leader': "ג'מאל זחאלקה",
        'leader_en': 'Jamal Zahalka',
        'leader_image': 'images/leaders/zahalka.jpg',
    },
    ('19', 'כן'): {
        'name': 'קדימה',
        'name_en': 'Kadima',
        'color': '#f59e0b',
        'leader': 'שאול מופז',
        'leader_en': 'Shaul Mofaz',
        'leader_image': 'images/leaders/mofaz.jpg',
    },
    ('19', 'אמת'): {
        'leader': 'שלי יחימוביץ',
        'leader_en': 'Shelly Yachimovich',
        'leader_image': 'images/leaders/yachimovich.jpg',
    },
    ('19', 'פה'): {
        'name': 'יש עתיד',
        'name_en': 'Yesh Atid',
        'color': PARTY_COLORS['yesh_atid'],
        'leader': 'יאיר לפיד',
        'leader_en': 'Yair Lapid',
        'leader_image': 'images/leaders/lapid.jpg',
    },
    ('19', 'טב'): {
        'leader': 'נפתלי בנט',
        'leader_en': 'Naftali Bennett',
        'leader_image': 'images/leaders/bennett.jpg',
    },

    # ===== ELECTION 20 (March 2015) =====
    ('20', 'אמת'): {
        'name': 'המחנה הציוני',
        'name_en': 'Zionist Union',
        'color': '#dc2626',
        'leader': 'יצחק הרצוג',
        'leader_en': 'Isaac Herzog',
        'leader_image': 'images/leaders/herzog.jpg',
    },
    ('20', 'ודעם'): {
        'name': 'הרשימה המשותפת',
        'name_en': 'Joint List',
        'color': '#059669',
        'leader': 'איימן עודה',
        'leader_en': 'Ayman Odeh',
        'leader_image': 'images/leaders/odeh.jpg',
    },
    ('20', 'פה'): {
        'name': 'יש עתיד',
        'name_en': 'Yesh Atid',
        'color': PARTY_COLORS['yesh_atid'],
        'leader': 'יאיר לפיד',
        'leader_en': 'Yair Lapid',
        'leader_image': 'images/leaders/lapid.jpg',
    },
    ('20', 'כ'): {
        'name': 'כולנו',
        'name_en': 'Kulanu',
        'color': PARTY_COLORS['kulanu'],
        'leader': 'משה כחלון',
        'leader_en': 'Moshe Kahlon',
        'leader_image': 'images/leaders/kahlon.jpg',
    },
    ('20', 'שס'): {
        'leader': 'אריה דרעי',
        'leader_en': 'Aryeh Deri',
        'leader_image': 'images/leaders/deri.jpg',
    },
    ('20', 'ג'): {
        'leader': 'יעקב ליצמן',
        'leader_en': 'Yaakov Litzman',
        'leader_image': 'images/leaders/litzman.jpg',
    },
    ('20', 'טב'): {
        'leader': 'נפתלי בנט',
        'leader_en': 'Naftali Bennett',
        'leader_image': 'images/leaders/bennett.jpg',
    },
    ('20', 'ל'): {
        'name': 'ישראל ביתנו',
        'name_en': 'Yisrael Beiteinu',
        'color': PARTY_COLORS['yisrael_beiteinu'],
        'leader': 'אביגדור ליברמן',
        'leader_en': 'Avigdor Lieberman',
        'leader_image': 'images/leaders/lieberman.jpg',
    },
    ('20', 'מרצ'): {
        'leader': 'זהבה גלאון',
        'leader_en': 'Zahava Galon',
        'leader_image': 'images/leaders/galon.jpg',
    },

    # ===== ELECTION 21 (April 2019) =====
    # Blue and White (Kahol Lavan) led by Benny Gantz
    ('21', 'פה'): {
        'name': 'כחול לבן',
        'name_en': 'Blue and White',
        'color': PARTY_COLORS['blue_white'],
        'leader': 'בני גנץ',
        'leader_en': 'Benny Gantz',
        'leader_image': 'images/leaders/gantz.jpg',
        'logo': 'images/logos/blue_white.png',
        'ideology': 'מרכז, ביטחוניות, ממלכתיות',
        'founded': 2019,
        'description': 'ברית בין יש עתיד, חוסן לישראל ותלם בהנהגת בני גנץ'
    },
    # HaBayit HaYehudi (Jewish Home) led by Rafi Peretz - ran as Union of Right-Wing Parties
    ('21', 'טב'): {
        'name': 'הבית היהודי',
        'name_en': 'The Jewish Home',
        'leader': 'רפי פרץ',
        'leader_en': 'Rafi Peretz',
        'leader_image': 'images/leaders/peretz_rafi.jpg',
        'ideology': 'ימין דתי-לאומי, התנחלויות',
        'founded': 2008,
        'description': 'איחוד מפלגות הימין - ברית הבית היהודי, האיחוד הלאומי ועוצמה יהודית'
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
        'logo': 'images/logos/blue_white.png',
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
        'logo': 'images/logos/blue_white.png',
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
        'logo': 'images/logos/blue_white.png',
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

    # New Hope led by Gideon Saar
    ('24', 'ת'): {
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

    # ===== ELECTION 25 (November 2022) =====
    # National Unity (Gantz + Saar merger) - default config is correct
    # Meretz led by Zahava Galon (returned to lead party)
    ('25', 'מרצ'): {
        'leader': 'זהבה גלאון',
        'leader_en': 'Zahava Galon',
        'leader_image': 'images/leaders/galon.jpg',
        'description': 'מפלגת מרצ בהנהגת זהבה גלאון, לא עברה את אחוז החסימה'
    },

    # ===== SMALL PARTY OVERRIDES (symbols reused across elections) =====

    # Party נ - different meaning per election
    ('21', 'נ'): {
        'name': 'הימין החדש',
        'name_en': 'New Right',
        'leader': 'נפתלי בנט ואיילת שקד',
        'leader_image': 'images/leaders/bennett.jpg',
        'logo': 'images/logos/new_right.png',
        'description': 'הימין החדש בראשות שקד ובנט, לא עברה את אחוז החסימה'
    },
    ('22', 'נ'): {
        'name': 'מתקדמת',
        'name_en': 'Progressive',
        'leader': '',
        'description': 'מתקדמת'
    },
    ('23', 'נ'): {
        'name': 'קול הנשים',
        'name_en': "Women's Voice",
        'leader': '',
        'description': 'קול הנשים'
    },

    # Party נץ - different meaning per election
    ('21', 'נץ'): {
        'name': 'מגן',
        'name_en': 'Magen',
        'leader': 'גל הירש',
        'description': 'מגן בראשות גל הירש'
    },
    ('22', 'נץ'): {
        'name': 'כל ישראל אחים',
        'name_en': 'All Israel Brothers',
        'leader': '',
        'description': 'כל ישראל אחים לשוויון חברתי'
    },
    ('23', 'נץ'): {
        'name': 'עוצמה יהודית',
        'name_en': 'Jewish Power',
        'leader': 'איתמר בן גביר',
        'leader_image': 'images/leaders/ben_gvir.jpg',
        'logo': 'images/logos/otzma_yehudit.png',
        'ideology': 'ימין קיצוני, לאומנות',
        'description': 'עוצמה יהודית בראשות איתמר בן גביר'
    },

    # Party כ - different meaning per election
    ('21', 'כ'): {
        'name': 'כולנו',
        'name_en': 'Kulanu',
        'leader': 'משה כחלון',
        'description': 'כולנו הימין השפוי בראשות משה כחלון'
    },
    ('22', 'כ'): {
        'name': 'נעם',
        'name_en': 'Noam',
        'leader': '',
        'description': 'נעם - עם נורמלי בארצנו'
    },
    ('23', 'כ'): {
        'name': 'הלב היהודי',
        'name_en': 'Jewish Heart',
        'leader': 'אלי יוסף',
        'description': 'הלב היהודי בראשות אלי יוסף'
    },
    ('24', 'כ'): {
        'name': 'הלב היהודי',
        'name_en': 'Jewish Heart',
        'leader': 'אלי יוסף',
        'description': 'הלב היהודי בראשות אלי יוסף'
    },

    # Party ז - different meaning per election
    ('21', 'ז'): {
        'name': 'זהות',
        'name_en': 'Zehut',
        'leader': 'משה פייגלין',
        'leader_image': 'images/leaders/feiglin.jpg',
        'logo': 'images/logos/zehut.png',
        'description': 'זהות - תנועה ישראלית יהודית בהנהגת משה פייגלין'
    },
    ('22', 'ז'): {
        'name': 'עוצמה כלכלית',
        'name_en': 'Economic Power',
        'leader': '',
        'description': 'עוצמה כלכלית קולם של העסקים בישראל'
    },
    ('23', 'ז'): {
        'name': 'עוצמה ליברלית',
        'name_en': 'Liberal Power',
        'leader': 'גלעד אלפר',
        'description': 'עוצמה ליברלית – כלכלית בראשות גלעד אלפר'
    },
    ('24', 'ז'): {
        'name': 'הישראלים',
        'name_en': 'The Israelis',
        'leader': '',
        'description': 'הישראלים'
    },

    # Party זן - Zehut in election 22
    ('22', 'זן'): {
        'name': 'זהות',
        'name_en': 'Zehut',
        'leader': 'משה פייגלין',
        'leader_image': 'images/leaders/feiglin.jpg',
        'logo': 'images/logos/zehut.png',
        'description': 'זהות - תנועה ישראלית יהודית בהנהגת משה פייגלין'
    },

    # Party ק - different meaning per election
    ('21', 'ק'): {
        'name': 'צדק לכל',
        'name_en': 'Justice for All',
        'leader': '',
        'description': 'צדק לכל כי הגיעה העת למען החי, האדם והאדמה'
    },
    ('22', 'ק'): {
        'name': 'זכויותינו בקולנו',
        'name_en': 'Our Rights in Our Voice',
        'leader': '',
        'description': 'זכויותינו בקולנו - לחיים בכבוד'
    },
    ('23', 'ק'): {
        'name': 'ישראליסט',
        'name_en': 'Israellist',
        'leader': '',
        'description': 'ישראליסט זכויותינו בקולנו לחיות טוב יותר'
    },
    ('24', 'ק'): {
        'name': 'נועם קולמן',
        'name_en': 'Noam Kolman',
        'leader': 'נועם קולמן',
        'description': 'נועם קולמן, לירון עופרי וסולי וולף - הבלתי אפשרי, אפשרי'
    },

    # Party כף - Otzma Yehudit in election 22
    ('22', 'כף'): {
        'name': 'עוצמה יהודית',
        'name_en': 'Jewish Power',
        'leader': 'איתמר בן גביר',
        'leader_image': 'images/leaders/ben_gvir.jpg',
        'logo': 'images/logos/otzma_yehudit.png',
        'ideology': 'ימין קיצוני, לאומנות',
        'description': 'עוצמה יהודית בראשות איתמר בן גביר'
    },

    # Party ר - Arab List in election 21
    ('21', 'ר'): {
        'name': 'הרשימה הערבית',
        'name_en': 'Arab List',
        'leader': 'מוחמד כנעאן',
        'description': 'הרשימה הערבית בראשות מוחמד כנעאן'
    },
    ('24', 'ר'): {
        'name': 'רפא',
        'name_en': 'Rafa',
        'leader': 'אריה אבני',
        'description': 'רפא – רק בריאות בראשות דוקטור אריה אבני'
    },

    # Party י - different meaning per election
    ('21', 'י'): {
        'name': 'ישר',
        'name_en': 'Yashar',
        'leader': '',
        'description': 'ישר - דמוקרטיה אמיתית'
    },
    ('22', 'י'): {
        'name': 'מנהיגות חברתית',
        'name_en': 'Social Leadership',
        'leader': '',
        'description': 'מנהיגות חברתית'
    },
    ('23', 'י'): {
        'name': 'החזון',
        'name_en': 'The Vision',
        'leader': 'ציון אלון',
        'description': 'החזון בראשות ציון אלון'
    },
    ('24', 'י'): {
        'name': 'המפץ החברתי',
        'name_en': 'Social Bang',
        'leader': '',
        'description': 'המפץ החברתי - גימלאים'
    },

    # Party ץ - different meaning per election
    ('21', 'ץ'): {
        'name': 'כלכלה ירוקה',
        'name_en': 'Green Economy',
        'leader': '',
        'description': 'כלכלה ירוקה - מדינה אחת'
    },
    ('22', 'ץ'): {
        'name': 'דעם',
        'name_en': 'Daam',
        'leader': '',
        'description': 'דעם - כלכלה ירוקה מדינה אחת'
    },
    ('23', 'ץ'): {
        'name': 'דעם',
        'name_en': 'Daam',
        'leader': '',
        'description': 'דעם כלכלה ירוקה מדינה אחת'
    },
    ('24', 'ץ'): {
        'name': 'דעם',
        'name_en': 'Daam',
        'leader': '',
        'description': 'דעם - כלכלה ירוקה מדינה אחת'
    },

    # Party ףז - Pirates
    ('21', 'ףז'): {
        'name': 'הפיראטים',
        'name_en': 'Pirates',
        'leader': '',
        'description': 'הפיראטים בראשות האינטרנט פתק לשלשול'
    },
    ('22', 'ףז'): {
        'name': 'הפיראטים',
        'name_en': 'Pirates',
        'leader': '',
        'description': 'הפיראטים - כי כולנו באותה סירה והכל אותו שייט'
    },
    ('23', 'ףז'): {
        'name': 'הפיראטים',
        'name_en': 'Pirates',
        'leader': '',
        'description': 'הפיראטים לדמוקרטיה לחצו כאן'
    },
    ('24', 'ףז'): {
        'name': 'הפיראטים',
        'name_en': 'Pirates',
        'leader': '',
        'description': 'הפיראטים'
    },

    # Party נז - different meaning per election
    ('21', 'נז'): {
        'name': 'זכויותינו בקולנו',
        'name_en': 'Our Rights in Our Voice',
        'leader': '',
        'description': 'זכויותינו בקולנו'
    },
    ('23', 'נז'): {
        'name': 'הכח להשפיע',
        'name_en': 'Power to Influence',
        'leader': '',
        'description': 'הכח להשפיע למען הציבור לחיות בכבוד'
    },

    # Party יז - different meaning per election
    ('22', 'יז'): {
        'name': 'אדום לבן',
        'name_en': 'Red White',
        'leader': '',
        'description': 'אדום לבן - לגליזציה לקנביס, שוויון לאתיופים, ערבים ומקופחים'
    },
    ('23', 'יז'): {
        'name': 'אדום לבן',
        'name_en': 'Red White',
        'leader': 'עמי פינשטיין',
        'description': 'אדום לבן – חירבת דוראן בראשות עמי פינשטיין'
    },
    ('24', 'יז'): {
        'name': 'הכלכלית החדשה',
        'name_en': 'New Economic',
        'description': 'הכלכלית החדשה בראשות פרופסור ירון זליכה'
    },
    ('25', 'יז'): {
        'name': 'הכלכלית החדשה',
        'name_en': 'New Economic',
        'description': 'הכלכלית החדשה בראשות פרופסור ירון זליכה'
    },

    # ===== ADDITIONAL SMALL PARTIES FROM OFFICIAL DATA =====

    # Election 21 small parties
    ('21', 'זי'): {
        'name': 'מפלגת האזרחים הוותיקים',
        'description': 'מפלגת האזרחים הוותיקים'
    },
    ('21', 'זך'): {
        'name': 'ברית עולם',
        'description': 'ברית עולם'
    },
    ('21', 'זנ'): {
        'name': 'יחד',
        'description': 'יחד בראשות אלי ישי'
    },
    ('21', 'ין'): {
        'name': 'איחוד בני הברית',
        'description': 'איחוד בני הברית בראשות רב חובל בשארה שליאן'
    },
    ('21', 'יץ'): {
        'name': 'אחריות למייסדים',
        'description': 'אחריות למייסדים בראשות חיים דיין'
    },
    ('21', 'ךק'): {
        'name': 'התקווה לשינוי',
        'description': 'התקווה לשינוי'
    },
    ('21', 'ןך'): {
        'name': 'כבוד האדם',
        'description': 'כבוד האדם'
    },
    ('21', 'ןנ'): {
        'name': 'מנהיגות חברתית',
        'description': 'מנהיגות חברתית'
    },
    ('21', 'נך'): {
        'name': 'מפלגת הרפורמה',
        'description': 'מפלגת הרפורמה'
    },
    ('21', 'נר'): {
        'name': 'גשר',
        'description': 'גשר בראשות אורלי לוי אבקסיס'
    },
    ('21', 'ףי'): {
        'name': 'פשוט אהבה',
        'description': 'פשוט אהבה - כי כולן/ם בני אדם'
    },
    ('21', 'ףך'): {
        'name': 'חינוך',
        'description': 'חינוך'
    },
    ('21', 'ףנ'): {
        'name': 'שווים',
        'description': 'שווים'
    },
    ('21', 'ףץ'): {
        'name': 'נ נח',
        'description': 'נ נח - הרשימה הממלכתית - תרימו את הראש'
    },
    ('21', 'ץז'): {
        'name': 'אופק חדש בכבוד',
        'description': 'אופק חדש בכבוד'
    },
    ('21', 'ץי'): {
        'name': 'אני ואתה',
        'description': "אני ואתה-מפלגת העם הישראלית בהובלת דר' אלון גלעדי"
    },
    ('21', 'צק'): {
        'name': 'צדק חברתי',
        'description': 'צדק חברתי'
    },
    ('21', 'קי'): {
        'name': 'ארץ ישראל שלנו',
        'description': 'ארץ ישראל שלנו'
    },
    ('21', 'קן'): {
        'name': 'מהתחלה',
        'description': 'מהתחלה'
    },
    ('21', 'קף'): {
        'name': 'כל ישראל אחים ופעולה לישראל',
        'description': 'כל ישראל אחים ופעולה לישראל'
    },

    # Election 22 small parties
    ('22', 'זכ'): {
        'name': 'מפלגת הדמוקראטורה',
        'description': 'מפלגת הדמוקראטורה'
    },
    ('22', 'זץ'): {
        'name': 'צומת',
        'description': 'צומת - התיישבות וחקלאות'
    },
    ('22', 'ינ'): {
        'name': 'התנועה הנוצרית הליבראלית',
        'description': 'התנועה הנוצרית הליבראלית'
    },
    ('22', 'יף'): {
        'name': 'כבוד האדם',
        'description': 'כבוד האדם'
    },
    ('22', 'כי'): {
        'name': 'האחדות העממית',
        'description': "האחדות העממית - אלוחדה אלשעביה בראשות פרופ' אסעד גאנם"
    },
    ('22', 'נך'): {
        'name': 'כבוד ושוויון',
        'description': 'כבוד ושוויון'
    },
    ('22', 'צ'): {
        'name': 'צדק',
        'description': 'צדק בראשות אבי ילאו'
    },
    ('22', 'צן'): {
        'name': 'צפון',
        'description': 'צפון'
    },
    ('22', 'קך'): {
        'name': 'סדר חדש',
        'description': 'סדר חדש - לשינוי שיטת הבחירות'
    },
    ('22', 'רק'): {
        'name': 'רון קובי',
        'description': 'רון קובי - הימין החילוני נלחמים בכפיה החרדית'
    },

    # Election 23 small parties
    ('23', 'זך'): {
        'name': 'פעולה לישראל',
        'description': 'פעולה לישראל'
    },
    ('23', 'זץ'): {
        'name': 'צומת',
        'description': 'צומת התנועה לציונות מתחדשת'
    },
    ('23', 'ינ'): {
        'name': 'איחוד הברית והשותפות',
        'description': 'איחוד הברית והשותפות'
    },
    ('23', 'יר'): {
        'name': 'מנהיגות חברתית',
        'description': 'מנהיגות חברתית'
    },
    ('23', 'כן'): {
        'name': 'אני ואתה',
        'description': 'אני ואתה – מפלגת העם הישראלית'
    },
    ('23', 'נק'): {
        'name': 'מתקדמת',
        'description': 'מתקדמת (בשיתוף עם תנועת הדרור העברי)'
    },
    ('23', 'קי'): {
        'name': 'שמע',
        'description': 'שמע בראשות נפתלי גולדמן'
    },

    # Election 24 small parties
    ('24', 'זץ'): {
        'name': 'צומת',
        'description': 'צומת – עצמאים, חקלאים, כפרים'
    },
    ('24', 'ינ'): {
        'name': 'ברית השותפות',
        'description': 'ברית השותפות לאיחוד לאומי בהנהגת רב חובל ב. שליאן'
    },
    ('24', 'יר'): {
        'name': 'מנהיגות חברתית',
        'description': 'מנהיגות חברתית'
    },
    ('24', 'כך'): {
        'name': 'אני ואתה',
        'description': 'אני ואתה – מפלגת העם הישראלית'
    },
    ('24', 'ני'): {
        'name': 'עולם חדש',
        'description': 'עולם חדש בראשות יורם אדרי'
    },
    ('24', 'צי'): {
        'name': 'עצמנו',
        'description': 'עצמנו עצמאים וליברלים'
    },
    ('24', 'צכ'): {
        'name': 'מען',
        'description': 'מען (יחד) לעידן חדש'
    },
    ('24', 'צף'): {
        'name': 'חץ',
        'description': 'חץ'
    },
    ('24', 'קי'): {
        'name': 'מפלגת שמע',
        'description': 'מפלגת שמע בראשות נפתלי גולדמן'
    },
    ('24', 'קץ'): {
        'name': 'משפט צדק',
        'description': 'משפט צדק, לרפורמה במערכת המשפט'
    },
    ('24', 'רנ'): {
        'name': 'התקווה לשינוי',
        'description': 'התקווה לשינוי'
    },
    ('24', 'רף'): {
        'name': 'עם שלם',
        'description': 'מפלגת עם שלם – בראשות הרב חיים אמסלם'
    },
    ('24', 'רק'): {
        'name': 'דמוקרטית',
        'description': 'דמוקרטית – חירות, שיוויון וערבות הדדית'
    },

    # Election 25 small parties
    ('25', 'אצ'): {
        'name': 'חופש כלכלי',
        'description': 'חופש כלכלי בראשות אביר קארה'
    },
    ('25', 'ז'): {
        'name': 'שחר כוח חברתי',
        'description': "שחר כוח חברתי בראשות וג'די טאהר"
    },
    ('25', 'זנ'): {
        'name': 'כח להשפיע',
        'description': 'כח להשפיע בראשות בני אלבז'
    },
    ('25', 'זץ'): {
        'name': 'צומת',
        'description': 'צומת בראשות משה גרין דרכו של רפול'
    },
    ('25', 'י'): {
        'name': 'ישראל חופשית דמוקרטית',
        'description': 'ישראל חופשית דמוקרטית בראשות אלי אבידר'
    },
    ('25', 'ינ'): {
        'name': 'איחוד בני הברית',
        'description': 'איחוד בני הברית -בראשות רב חובל בשארה שליאן'
    },
    ('25', 'יץ'): {
        'name': 'צו השעה',
        'description': 'צו השעה'
    },
    ('25', 'ך'): {
        'name': 'אני ואתה',
        'description': 'אני ואתה'
    },
    ('25', 'ני'): {
        'name': 'נתיב',
        'description': 'נתיב - נחיה תמיד יחד בכבוד'
    },
    ('25', 'נף'): {
        'name': 'מפלגת שמע',
        'description': 'מפלגת שמע בראשות נפתלי גולדמן'
    },
    ('25', 'נץ'): {
        'name': 'העצמאים החדשים',
        'description': 'העצמאים החדשים בראשות יורם מועלמי'
    },
    ('25', 'נק'): {
        'name': 'יש כיוון',
        'description': 'יש כיוון בראשות עמוס דב סילבר'
    },
    ('25', 'ף'): {
        'name': 'הפיראטים',
        'description': 'הפיראטים- הכי טוב לדעתי אני רוצה להיות שם'
    },
    ('25', 'ץ'): {
        'name': 'מנהיגות חברתית',
        'description': 'מנהיגות חברתית'
    },
    ('25', 'צ'): {
        'name': 'צעירים בוערים',
        'description': 'צעירים בוערים בהנהגת הדר מוכתר'
    },
    ('25', 'ק'): {
        'name': 'קול הסביבה והחי',
        'description': 'קול הסביבה והחי'
    },
    ('25', 'קי'): {
        'name': 'הלב היהודי',
        'description': 'הלב היהודי בראשות אלי יוסף'
    },
    ('25', 'קך'): {
        'name': 'סדר חדש',
        'description': 'סדר חדש- למען האזרחים הותיקים בישראל'
    },
    ('25', 'קנ'): {
        'name': 'כל קול קובע',
        'description': 'כל קול קובע נועם קולמן ולירון עופרי לראשות הממשלה'
    },
    ('25', 'קץ'): {
        'name': 'באומץ בשבילך',
        'description': 'באומץ בשבילך'
    },
    ('25', 'רז'): {
        'name': 'רשימת שלושים/ארבעים',
        'description': 'רשימת שלושים/ארבעים בראשות סטלה ויינשטיין'
    },
    ('25', 'ת'): {
        'name': 'דעת טוב ורע',
        'description': 'דעת טוב ורע וברית שבט אברהם-עלה ירוק ואוסרת אל איס'
    },

    # Additional missing parties not in national results
    ('21', 'ן'): {
        'name': 'ן',
        'description': 'רשימה שלא עברה את אחוז החסימה'
    },
    ('23', 'יף'): {
        'name': 'כבוד האדם',
        'description': 'כבוד האדם'
    },
    ('24', 'יף'): {
        'name': 'כבוד האדם',
        'description': 'כבוד האדם'
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
