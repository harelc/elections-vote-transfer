"""How poll columns and poll credits map onto what actually ran.

Used by generate_poll_accuracy.py. Everything a reader needs to check the
fairness of the comparison is here, in one place:

LIST_MAP        per election: Wikipedia column label -> the final list(s) it
                became. One label -> several lists means the poll measured
                them together (e.g. the Joint List before it split), and the
                comparison is then made on their combined seats.
WITHDREW        labels for lists that did not run in the end. Their poll seats
                are left out of the list comparison (the poll could not have
                known), and the poll is flagged.
TABLE_OVERRIDES the same label meant a different line-up in an earlier table
                (e.g. "Joint List" with Ra'am inside it, before Ra'am left).
FINAL_EXTRA     lists that ran and are missing from wiki_official_results.json
                (small lists), with their CEC letter so the votes come from
                the official ballot file.
POLLSTERS /     spelling variants -> one Hebrew name. Merges beyond spelling
OUTLETS         are listed in MERGE_NOTES_HE.
"""
import re

# A token inside a column label: the most specific header (after ' / ') of
# each part joined with ' + '.
def label_tokens(label):
    return [part.split(' / ')[-1].strip() for part in label.split(' + ')]


LIST_MAP = {
    '19': {
        'Likud': ['הליכוד ישראל ביתנו'], 'Yisrael Beiteinu': ['הליכוד ישראל ביתנו'],
        'Likud + Yisrael Beiteinu': ['הליכוד ישראל ביתנו'],
        'Yesh Atid': ['יש עתיד'], 'Labor': ['העבודה'], 'Shas': ['ש״ס'], 'UTJ': ['יהדות התורה'],
        'Jewish Home': ['הבית היהודי'], 'National Union': ['הבית היהודי'],
        'Hatnuah': ['התנועה'], 'Meretz': ['מרצ'], "UAL - Ta'al": ['רע״ם-תע״ל'], 'Hadash': ['חד״ש'],
        'Balad': ['בל״ד'], 'Kadima': ['קדימה'], 'Otzma': ['עוצמה לישראל'], 'Am Shalem': ['עם שלם'],
    },
    '20': {
        'Likud': ['הליכוד'], 'Yisrael Beiteinu': ['ישראל ביתנו'], 'Yesh Atid': ['יש עתיד'],
        'Labor': ['המחנה הציוני'], 'Hatnuah': ['המחנה הציוני'],
        'Jewish Home': ['הבית היהודי'], 'Shas': ['ש״ס'], 'UTJ': ['יהדות התורה'], 'Meretz': ['מרצ'],
        'Hadash': ['הרשימה המשותפת'], "UAL - Ta'al": ['הרשימה המשותפת'], 'Balad': ['הרשימה המשותפת'],
        'Kulanu': ['כולנו'], 'Yachad': ['יחד'], 'Otzma': ['יחד'],
    },
    '21': {
        'Likud': ['הליכוד'], 'Labor': ['העבודה'], 'Zionist Union': ['העבודה'],
        'Blue & White': ['כחול לבן'], 'Yesh Atid': ['כחול לבן'], 'Hosen': ['כחול לבן'],
        'Hosen - Telem': ['כחול לבן'],
        'Kulanu': ['כולנו'], "Ra'am – Balad": ['רע״ם-בל״ד'], "Hadash – Ta'al": ['חד״ש-תע״ל'],
        "Ta'al": ['חד״ש-תע״ל'], 'Joint List': ['חד״ש-תע״ל', 'רע״ם-בל״ד'],
        'Shas': ['ש״ס'], 'UTJ': ['יהדות התורה'], 'URWP': ['הבית היהודי'], 'Jewish Home': ['הבית היהודי'],
        'Yisrael Beiteinu': ['ישראל ביתנו'], 'Meretz': ['מרצ'], 'New Right': ['הימין החדש'],
        'Gesher': ['גשר'], 'Zehut': ['זהות'],
    },
    '22': {
        'Likud': ['הליכוד'], 'Likud – Kulanu': ['הליכוד'], 'Kulanu': ['הליכוד'],
        'Blue & White': ['כחול לבן'], 'Joint List': ['הרשימה המשותפת'],
        "Hadash – Ta'al": ['הרשימה המשותפת'], "Ra'am – Balad": ['הרשימה המשותפת'],
        'Shas': ['ש״ס'], 'UTJ': ['יהדות התורה'], 'Yamina': ['ימינה'], 'URWP': ['ימינה'],
        'New Right': ['ימינה'], 'Labor- Gesher': ['העבודה-גשר'], 'Labor': ['העבודה-גשר'],
        'Gesher': ['העבודה-גשר'], 'Yisrael Beiteinu': ['ישראל ביתנו'],
        'Dem. Union': ['המחנה הדמוקרטי'], 'Meretz': ['המחנה הדמוקרטי'], 'IDP': ['המחנה הדמוקרטי'],
        'Otzma Yehudit': ['עוצמה יהודית'],
    },
    '23': {
        'Blue & White': ['כחול לבן'], 'Likud': ['הליכוד'], 'Joint List': ['הרשימה המשותפת'],
        'Shas': ['ש״ס'], 'Yisrael Beiteinu': ['ישראל ביתנו'], 'UTJ': ['יהדות התורה'],
        'Emet': ['עבודה-גשר-מרצ'], 'Labor- Gesher': ['עבודה-גשר-מרצ'], 'Dem. Union': ['עבודה-גשר-מרצ'],
        'Yamina': ['ימינה'], 'New Right': ['ימינה'], 'NU': ['ימינה'], 'JH': ['ימינה'], 'JH – NU': ['ימינה'],
        'UJH': ['ימינה', 'עוצמה יהודית'],
        'Otzma': ['עוצמה יהודית'], 'Otzma Yehudit': ['עוצמה יהודית'],
    },
    '24': {
        'Likud': ['הליכוד'], 'Gesher': ['הליכוד'],
        'Yesh Atid': ['יש עתיד'], 'Yesh Atid -Telem': ['יש עתיד'],
        'Blue & White': ['כחול לבן'], 'B&W': ['כחול לבן'],
        'Joint List': ['הרשימה המשותפת'], "Ta'al": ['הרשימה המשותפת'], "Ra'am": ['רע״ם'],
        'Shas': ['ש״ס'], 'UTJ': ['יהדות התורה'], 'Yisrael Beiteinu': ['ישראל ביתנו'], 'YB': ['ישראל ביתנו'],
        'Meretz': ['מרצ'], 'Yamina': ['ימינה'], 'New Hope': ['תקווה חדשה'], 'Derekh Eretz': ['תקווה חדשה'],
        'Labor': ['העבודה'],
        'Religious Zionist': ['הציונות הדתית'], 'RZ': ['הציונות הדתית'], 'OY': ['הציונות הדתית'],
        'Otzma Yehudit': ['הציונות הדתית'], 'Otzma Yehudit - Noam': ['הציונות הדתית'],
        'New Economic': ['הכלכלית החדשה'], 'NEP': ['הכלכלית החדשה'],
    },
    '25': {
        'Likud': ['הליכוד'], 'Yesh Atid': ['יש עתיד'],
        'National Unity': ['המחנה הממלכתי'], 'NUP / B&W – NH': ['המחנה הממלכתי'],
        'B&W – NH': ['המחנה הממלכתי'], 'Blue & White': ['המחנה הממלכתי'], 'New Hope': ['המחנה הממלכתי'],
        'Shas': ['ש״ס'], 'Jewish Home': ['הבית היהודי'], 'JH / Yamina': ['הבית היהודי'],
        'Yamina': ['הבית היהודי'], 'Zionist Spirit': ['הבית היהודי'], 'Zionist Spirit/ Yamina': ['הבית היהודי'],
        'Labor': ['העבודה'], 'UTJ': ['יהדות התורה'], 'Yisrael Beiteinu': ['ישראל ביתנו'],
        'RZP - OY': ['הציונות הדתית'], 'Religious Zionist': ['הציונות הדתית'],
        'Otzma Yehudit': ['הציונות הדתית'],
        "Hadash –Ta'al": ['חד״ש-תע״ל'], 'Meretz': ['מרצ'], "Ra'am": ['רע״ם'], 'Balad': ['בל״ד'],
        'Joint List': ['חד״ש-תע״ל', 'בל״ד'],
    },
    # K26: names as in wiki_official_results.json "26", so the scoring works
    # unchanged once the real results replace the simulated ones.
    '26': {
        'Likud': ['הליכוד'], 'Together': ['ביחד'], 'Yesh Atid': ['ביחד'], 'Bennett 2026': ['ביחד'],
        'RZP - Zehut': ['הציונות הדתית'], 'RZP': ['הציונות הדתית'], 'Zehut': ['הציונות הדתית'],
        'Otzma': ['עוצמה יהודית'], 'Shas': ['ש״ס'], 'UTJ': ['יהדות התורה'],
        'Yisrael Beiteinu': ['ישראל ביתנו'], "Ra'am": ['רע״ם'],
        'Joint List': ['הרשימה המשותפת'], "Hadash –Ta'al": ['הרשימה המשותפת'], 'Balad': ['הרשימה המשותפת'],
        'Dems': ['הדמוקרטים'], 'Yashar': ['ישר'],
        'Reserv. - NEP': ['המילואימניקים והכלכלית'], 'Reserv.': ['המילואימניקים והכלכלית'],
        'Amcha Yisrael': ['עמך ישראל'], 'Haredi Public': ['הציבור החרדי'],
        # Ofer Winter's party before it was named Amcha Yisrael (25 Aug 2026)
        'Winter party': ['עמך ישראל'],
        # "Zionist Home – The Reservists" = Hendel's Reservists + Hili Tropper;
        # on 6 Sep Tropper joined Yashar and the Reservists ran with the NEP.
        # Measured together, so compared with both lists together.
        'Zionist Home': ['המילואימניקים והכלכלית', 'ישר'],
    },
}

# Lists that were polled but did not run (withdrew, or folded in a way that
# cannot be traced to one final list).
WITHDREW = {
    '19': {}, '20': {},
    '21': {'Hatnuah': 'התנועה פרשה מהמרוץ (פברואר 2019)'},
    '22': {'Zehut': 'זהות פרשה מהמרוץ (אוגוסט 2019)'},
    '23': {'Green': 'המפלגה הירוקה פרשה (ינואר 2020)'},
    '24': {'Telem': 'תל"ם פרשה (פברואר 2021)', 'Israelis': 'הישראלים פרשה (פברואר 2021)',
           'Tnufa': 'תנופה פרשה (פברואר 2021)', 'JH': 'הבית היהודי פרשה (פברואר 2021)',
           'Jewish Home': 'הבית היהודי פרשה (פברואר 2021)'},
    '25': {},
    '26': {'Blue & White': 'כחול לבן לא רצה',
           'Unity': 'אחדות (ארדן ואדלשטיין) פרשה (4 בספטמבר 2026)'},
}

# (election, wiki table index) -> {label: lists}
TABLE_OVERRIDES = {
    # Before Ra'am and Ta'al left (late January 2021) "Joint List" included both.
    ('24', 2): {'Joint List': ['הרשימה המשותפת', 'רע״ם']},
    ('24', 3): {'Joint List': ['הרשימה המשותפת', 'רע״ם']},
    ('24', 4): {'Joint List': ['הרשימה המשותפת', 'רע״ם']},
    ('24', 5): {'Joint List': ['הרשימה המשותפת', 'רע״ם']},
    ('24', 6): {'Joint List': ['הרשימה המשותפת', 'רע״ם']},
}

# Columns that are only part of the final list (a party that later merged
# into it). Their seats count toward that list, but their vote % must not be
# compared with the whole list's result.
ABSORBED = {
    '19': {'Likud', 'Yisrael Beiteinu', 'National Union', 'Jewish Home'},
    '20': {'Labor', 'Hatnuah', 'Hadash', "UAL - Ta'al", 'Balad', 'Otzma'},
    '21': {'Zionist Union', 'Yesh Atid', 'Hosen', 'Hosen - Telem', "Ta'al", 'Jewish Home'},
    '22': {'Kulanu', 'URWP', 'New Right', 'Labor', 'Gesher', 'Meretz', 'IDP', "Hadash – Ta'al", "Ra'am – Balad"},
    '23': {'Labor- Gesher', 'Dem. Union', 'New Right', 'NU', 'JH', 'JH – NU', 'UJH'},
    '24': {'Gesher', "Ta'al", 'Derekh Eretz', 'RZ', 'OY', 'Otzma Yehudit', 'Otzma Yehudit - Noam'},
    '25': {'Blue & White', 'New Hope', 'Yamina', 'Zionist Spirit', 'Zionist Spirit/ Yamina', 'JH / Yamina',
           'Religious Zionist', 'Otzma Yehudit'},
    '26': {'Yesh Atid', 'Bennett 2026', 'RZP', 'Zehut', 'Reserv.', 'Winter party', "Hadash –Ta'al", 'Balad'},
}

# Lists that ran but are missing from wiki_official_results.json: name -> CEC letter.
FINAL_EXTRA = {
    '19': {'עוצמה לישראל': 'נץ', 'עם שלם': 'ץ'},
    '20': {'יחד': 'קץ'},
}

LIST_NOTES_HE = [
    'כשסקר מדד שתי רשימות שהתאחדו אחר כך (למשל כחול לבן ותקווה חדשה ב-2022), משווים את סכום המנדטים שלהן לתוצאת הרשימה המאוחדת.',
    'כשסקר מדד רשימה אחת שהתפצלה אחר כך (למשל הרשימה המשותפת לפני שבל"ד יצאה ב-2022), משווים אותה לסכום הרשימות שיצאו ממנה.',
    'רשימה שפרשה מהמרוץ לפני הבחירות לא נספרת בהשוואה ברמת הרשימה, כי הסקר לא יכול היה לדעת. הסקר מסומן.',
    '2022: "רוח ציונית" ו"ימינה" של איילת שקד הושוו לרשימת הבית היהודי שבראשה רצה.',
    '2021: גשר של אורלי לוי הושווה לליכוד (היא הצטרפה לרשימת הליכוד); דרך ארץ הושווה לתקווה חדשה.',
    '2021: עוצמה יהודית ונעם הושוו לציונות הדתית, שבתוכה רצו.',
    '2019 (אפריל): המחנה הציוני הושווה לעבודה; התנועה פרשה. חוסן, תל"ם ויש עתיד הושוו לכחול לבן.',
    '2019 (ספטמבר): כולנו הושוותה לליכוד; ימין חדש ואיחוד מפלגות הימין לימינה; מרצ והמפלגה הדמוקרטית למחנה הדמוקרטי.',
    '2015: עוצמה הושוותה לרשימת יחד, שבתוכה רצה. 2013: האיחוד הלאומי הושווה לבית היהודי.',
]

# ---------------------------------------------------------------- blocs
# The two blocs the bloc-accuracy measure uses, per election (final list
# names as in wiki_official_results.json). Kept here so the poll code stands
# alone.
# NETANYAHU: the right and religious parties of Netanyahu's camp in that
# election (K21 without Yisrael Beiteinu, which then refused to join). Parties
# that joined a government of his without being in the camp (Yesh Atid and
# Hatnuah in 2013) are not counted.
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
# K26, before any recommendation exists: an assumption from the lists' public
# positions, shown on the page as an assumption.
K26_BLOCS = {
    'right': ['הליכוד', 'יהדות התורה', 'ש״ס', 'עוצמה יהודית', 'הציונות הדתית', 'עמך ישראל',
              'המילואימניקים והכלכלית'],
    'center': ['ישר', 'ביחד', 'הדמוקרטים', 'ישראל ביתנו'],
    'arab': ['הרשימה המשותפת', 'רע״ם'],
}
K26_BLOCS_NOTE_HE = ('הנחה עד שהרשימות ימליצו על מועמד אחרי הבחירות. המילואימניקים והכלכלית '
                     'משויכת לגוש הימין וישראל ביתנו לגוש המרכז, לפי הצהרות לפני הבחירות.')

# ---------------------------------------------------------------- pollsters
# (key, Hebrew name, pattern). First match wins, so specific before general.
POLLSTERS = [
    ('mp_tm', 'פרויקט המדגם, המדד, סטט-נט ואסקריה', r'MP\+TM'),
    ('fuchs', 'קמיל פוקס / פרויקט המדגם (חדשות 13)',
     r'Camil+e? Fuchs|Panel (Project )?HaMidgam|HaMidgam Project|Midgam Project|^Statnet$|Dialog(ue)?'),
    ('midgam', 'מדגם (מנו גבע)', r'Midgam|Meno Geva|Mano Geva'),
    ('maagar', 'מאגר מוחות', r"Ma'?agar|MM\+SN"),
    ('lazar', 'מכון לזר', r'LRI|Lazar'),
    ('panels', 'פאנלס פוליטיקס', r'Panels?( ?Politics| Polls)?\b|PanelPolitics'),
    ('kantar', 'קנטר (לשעבר TNS-טלסקר)', r'KANTAR|Kantar|TNS|Teleseker'),
    ('direct', 'דירקט פולס', r'Direct [Pp]olls'),
    ('filber', 'שלמה פילבר ו-NEXT DATA', r'SF\+ND|Filber'),
    ('smith', 'מכון סמית', r'Smith'),
    ('dahaf', 'מכון דחף', r'Dahaf'),
    ('geocart', 'גיאוקרטוגרפיה', r'Geo ?[Cc]artograph'),
    ('sarid', 'מכון שריד', r'Sarid'),
    ('newwave', 'ניו ווייב', r'New Wave'),
    ('miskar', 'מסקר', r'Miskar'),
    ('tatika', 'יוסי טטיקה', r'Tatika'),
    ('tri', 'TRI', r'\bTRI\b'),
    ('shvakim', 'שווקים פנורמה', r'Shvakim'),
    ('202', '202 Strategies', r'202 Strategies'),
    ('number10', 'Number 10 Strategies', r'Number 10'),
]

OUTLETS = [
    ('kan11', 'כאן 11 (ובעבר ערוץ 1)', r'\bKan\b(?! Radio)|Channel ?11?\b'),
    ('kanb', 'כאן ב (רשת ב)', r'Reshet Bet|(?<!Galay )(?<!Galei )Israel Radio|Kan Radio'),
    ('ch12', 'חדשות 12 (ובעבר ערוץ 2)', r'Channel ?12|HaHadashot 12|Keshet|Channel ?2\b|News Company'),
    ('mako', 'מאקו (אתר קשת)', r'\bMako\b|MAKO'),
    ('ch13', 'חדשות 13 (ובעבר ערוץ 10)', r'Channel ?13|Ten News|Channel ?10\b'),
    ('ch14', 'ערוץ 14 (ובעבר ערוץ 20)', r'Channel ?14|Channel ?20'),
    ('ch16', 'ערוץ 16', r'Channel ?16'),
    ('i24', 'i24NEWS', r'i24'),
    ('knesset', 'ערוץ הכנסת', r'Knesset'),
    ('galatz', 'גלי צה"ל', r'Army Radio|Galatz|Galei Tzahal'),
    ('fm103', '103FM', r'103 ?[Ff][Mm]'),
    ('galeiisrael', 'גלי ישראל', r'Galei Israel|Galay Israel'),
    ('kolbarama', 'קול ברמה', r'Kol B[a-z]*ramah?'),
    ('maariv', 'מעריב', r'Maariv|\bNRG\b|Sof Hashavua'),
    ('yedioth', 'ידיעות אחרונות / ynet', r'Yedi?oth?|Yediot'),
    ('israelhayom', 'ישראל היום', r'Israel Hayom|Yisrael Hayom'),
    ('haaretz', 'הארץ', r'Haaretz'),
    ('walla', 'וואלה', r'Walla'),
    ('globes', 'גלובס', r'Globes'),
    ('jpost', 'ג\'רוזלם פוסט', r'Jerusalem Post'),
    ('makor', 'מקור ראשון', r'Makor Rishon'),
    ('arutz7', 'ערוץ 7', r'Arutz (Sheva|7)'),
    ('zman', 'זמן ישראל', r'Zman Yisrael'),
    ('toi', 'טיימס אוף ישראל', r'Times of Israel'),
    ('nana10', 'נענע 10', r'Nana 10'),
    ('hot', 'HOT', r'\bHOT\b'),
    ('srugim', 'סרוגים', r'Srugim'),
    ('bizportal', 'ביזפורטל', r'Bizportal'),
    ('saloona', 'סלונה', r'Saloona'),
    ('bhadrei', 'בחדרי חרדים', r'Bchardei'),
    ('jnet', 'Jerusalem Net', r'Jerusalem Net'),
    ('israelpost', 'ישראל פוסט', r'Yisrael Post'),
    ('ice', 'אייס', r'\bIce\b'),
]

# Rows not counted: commissioned by a party, or not published by a media outlet.
EXCLUDE = [
    (r'Midgam/Labor', 'סקר שהזמינה מפלגה (העבודה)'),
    (r'Israel Beitenu', 'סקר שהזמינה מפלגה (ישראל ביתנו)'),
    (r'S\.M\.L\.T', 'לא צוין כלי תקשורת'),
    (r' / [–—]', 'פרסום עצמי של הסוקר, בלי כלי תקשורת'),
]

# Single rows not counted, found by checking the cited article:
# (election, date, firm as written, publisher as written) -> reason.
EXCLUDE_ROWS = {
    ('23', '2020-01-09', 'Midgam', 'Arutz Sheva'):
        'סקר פנימי: לפי הכתבה בערוץ 7 הוא הוזמן בידי גורמים בימין',
}

MERGE_NOTES_HE = [
    'קנטר, TNS וטלסקר הם אותה חברה בשמות שונים לאורך השנים (טלסקר נקנתה בידי TNS, שהפכה לקנטר).',
    'סקרי חדשות 13 רשומים בוויקיפדיה פעם בשם קמיל פוקס ופעם בשם פרויקט המדגם או סטט-נט. טבלת הסוקרים בוויקיפדיה מציינת שהם עבדו יחד עבור ערוץ 13, ולכן הם מאוחדים כאן. גם מכון דיאלוג, שבראשו עמד קמיל פוקס, מאוחד איתם.',
    'פרויקט המדגם של חדשות 13 אינו "מדגם" של מנו גבע (חדשות 12). אלה שני גופים שונים.',
    'פאנלס פוליטיקס ומכון לזר נשארים נפרדים, כפי שהם רשומים בוויקיפדיה.',
    'ערוץ 2 נספר כחדשות 12, ערוץ 10 כחדשות 13, ערוץ 1 ככאן 11, ערוץ 20 כערוץ 14 ו-NRG כמעריב, כי אלה אותם גופי חדשות לפני שינוי השם.',
    'מאקו (אתר האינטרנט של קשת) נספר בנפרד מחדשות 12: סקרים שפורסמו במאקו נעשו לעתים בידי מכון אחר (למשל פאנלס פוליטיקס ב-2022).',
]


def classify(firm_raw, publisher_raw):
    """-> (pollster_key, pollster_he, [(outlet_key, outlet_he)], excluded_reason)"""
    text = f'{firm_raw} / {publisher_raw}'
    for pat, why in EXCLUDE:
        if re.search(pat, text):
            return None, None, [], why
    pollster = (None, None)
    for key, he, pat in POLLSTERS:
        if re.search(pat, firm_raw) or (key == 'panels' and re.search(pat, text)):
            pollster = (key, he)
            break
    outlets = []
    for key, he, pat in OUTLETS:
        src = text
        if key == 'maariv' and pollster[0] == 'panels':
            src = text.replace('Maariv Panels', 'Maariv')
        if re.search(pat, src) and key not in [o[0] for o in outlets]:
            outlets.append((key, he))
    # No outlet named (the old one-column tables): the row still counts for the
    # pollster ranking and is left out of the outlet ranking.
    return pollster[0], pollster[1], outlets, None
