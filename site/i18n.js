/**
 * i18n module for קולות נודדים / Migrating Votes
 * Provides Hebrew ↔ English toggle across all pages.
 */
(function () {
    'use strict';

    /* ── Translation dictionary ─────────────────────────────────── */
    const dict = {
        /* ── Site-wide ── */
        site_title:            { he: 'קולות נודדים', en: 'Migrating Votes' },
        site_subtitle:         { he: 'ניתוח מעבר קולות בין בחירות לכנסת ישראל', en: 'Analyzing vote transfers between Israeli Knesset elections' },

        /* ── Nav (desktop) ── */
        nav_sankey:            { he: 'נדידת קולות', en: 'Vote Flow' },
        nav_tsne:              { he: 'התפלגות קלפיות', en: 'Ballot Clusters' },
        nav_geomap:            { he: 'מפה גיאוגרפית', en: 'Geographic Map' },
        nav_scatter:           { he: 'השוואת מפלגות', en: 'Party Comparison' },
        nav_dhondt:            { he: 'מחשבון באדר-עופר', en: 'D\'Hondt Calculator' },
        nav_irregular:         { he: 'קלפיות חריגות', en: 'Irregular Ballots' },
        export_png:            { he: '📷 ייצוא PNG', en: '📷 Export PNG' },

        /* ── Mobile tabs ── */
        tab_map:               { he: 'מפה', en: 'Map' },
        tab_sankey:            { he: 'נדידה', en: 'Flow' },
        tab_tsne:              { he: 'פיזור', en: 'Cluster' },
        tab_scatter:           { he: 'השוואה', en: 'Compare' },
        tab_dhondt:            { he: 'מנדטים', en: 'Seats' },

        /* ── Sankey page ── */
        from_election:         { he: 'מבחירות', en: 'From election' },
        to_election:           { he: 'לבחירות', en: 'To election' },
        eligible_voters:       { he: 'בעלי זכות', en: 'Eligible voters' },
        voted:                 { he: 'הצביעו', en: 'Voted' },
        turnout_pct:           { he: 'אחוז הצבעה', en: 'Turnout' },
        common_precincts:      { he: 'קלפיות משותפות', en: 'Common precincts' },
        r_squared:             { he: 'R² (מידת התאמה)', en: 'R² (goodness of fit)' },
        pct_display:           { he: 'תצוגת אחוזים:', en: 'Percent display:' },
        pct_from_prev:         { he: 'מהבחירות הקודמות', en: 'From previous election' },
        pct_from_next:         { he: 'מהבחירות החדשות', en: 'From new election' },
        pct_prev_short:        { he: '% מהקודמות', en: '% from prev' },
        pct_next_short:        { he: '% מהחדשות', en: '% from new' },
        source_parties:        { he: 'מפלגות מקור', en: 'Source parties' },
        target_parties:        { he: 'מפלגות יעד', en: 'Target parties' },
        parties_label:         { he: 'מפלגות', en: 'Parties' },
        prev_election:         { he: 'בחירות קודמות', en: 'Previous election' },
        new_election:          { he: 'בחירות חדשות', en: 'New election' },
        loading:               { he: 'טוען נתונים...', en: 'Loading data...' },
        error_loading:         { he: 'שגיאה בטעינת הנתונים', en: 'Error loading data' },
        error_init:            { he: 'שגיאה באתחול', en: 'Initialization error' },
        no_data:               { he: 'אין נתונים להצגה', en: 'No data to display' },
        total_votes:           { he: 'סה״כ קולות:', en: 'Total votes:' },
        total_votes_short:     { he: 'סה״כ קולות', en: 'Total votes' },
        votes:                 { he: 'קולות', en: 'votes' },
        seats:                 { he: 'מנדטים', en: 'seats' },
        seats_mandatim:        { he: 'מנדטים', en: 'seats' },
        leader_label:          { he: 'מנהיג:', en: 'Leader:' },
        ideology_label:        { he: 'אידאולוגיה:', en: 'Ideology:' },
        founded_label:         { he: 'שנת הקמה:', en: 'Founded:' },
        from_votes_of:         { he: 'מקולות {party} בבחירות הקודמות', en: 'Of {party} votes in previous election' },
        from_votes_of_new:     { he: 'מקולות {party} בבחירות החדשות', en: 'Of {party} votes in new election' },
        votes_from_common:     { he: '{n} קולות (מתוך הקלפיות המשותפות)', en: '{n} votes (from common precincts)' },
        votes_from_common_only:{ he: '{n} קולות (מתוך הקלפיות המשותפות בלבד)', en: '{n} votes (from common precincts only)' },
        in_prev_election:      { he: 'בבחירות הקודמות', en: 'In previous election' },
        in_new_election:       { he: 'בבחירות החדשות', en: 'In new election' },
        official_results:      { he: 'תוצאות רשמיות - כנסת ה-{n}', en: 'Official results – {n}th Knesset' },
        below_threshold:       { he: 'לא עברה', en: 'Below threshold' },

        /* ── T-SNE page ── */
        tsne_title:            { he: 'התפלגות קלפיות', en: 'Ballot Distribution' },
        color_by:              { he: 'צביעה לפי:', en: 'Color by:' },
        turnout:               { he: 'אחוז הצבעה', en: 'Turnout' },
        socioeconomic:         { he: 'אשכול חברתי-כלכלי', en: 'Socioeconomic cluster' },
        party_support:         { he: 'תמיכה במפלגה', en: 'Party support' },
        search_settlement:     { he: 'חיפוש יישוב...', en: 'Search settlement...' },
        search_station:        { he: 'חיפוש תחנה, קלפי או מיקום...', en: 'Search station, ballot or location...' },
        settlement:            { he: 'יישוב', en: 'Settlement' },
        ballot:                { he: 'קלפי', en: 'Ballot' },
        location:              { he: 'מיקום', en: 'Location' },
        voters:                { he: 'מצביעים', en: 'Voters' },
        clear_filter:          { he: 'נקה סינון', en: 'Clear filter' },
        no_results:            { he: 'לא נמצאו תוצאות', en: 'No results found' },
        low:                   { he: 'נמוך', en: 'Low' },
        high:                  { he: 'גבוה', en: 'High' },

        /* ── Geomap page ── */
        geomap_title:          { he: 'מפה גיאוגרפית', en: 'Geographic Map' },
        color_mode:            { he: 'צביעה:', en: 'Color:' },
        winner:                { he: 'מפלגה מנצחת', en: 'Winning party' },
        specific_party:        { he: 'מפלגה ספציפית', en: 'Specific party' },
        filter_settlement:     { he: 'סנן לפי יישוב...', en: 'Filter by settlement...' },
        stations:              { he: 'תחנות', en: 'Stations' },

        /* ── Scatter page ── */
        scatter_title:         { he: 'השוואת תמיכה במפלגות', en: 'Party Support Comparison' },
        x_axis:                { he: 'ציר X:', en: 'X axis:' },
        y_axis:                { he: 'ציר Y:', en: 'Y axis:' },
        election:              { he: 'בחירות', en: 'Election' },
        party:                 { he: 'מפלגה', en: 'Party' },
        pct_unit:              { he: 'אחוזים', en: 'Percentages' },
        abs_unit:              { he: 'מספרים מוחלטים', en: 'Absolute numbers' },
        units:                 { he: 'יחידות:', en: 'Units:' },
        all_settlements:       { he: 'כל היישובים', en: 'All settlements' },

        /* ── D'Hondt page ── */
        dhondt_title:          { he: 'מחשבון באדר-עופר', en: 'D\'Hondt Calculator' },
        threshold:             { he: 'אחוז חסימה', en: 'Electoral threshold' },
        threshold_pct:         { he: 'אחוז חסימה:', en: 'Threshold:' },
        surplus_agreements:    { he: 'הסכמי עודפים', en: 'Surplus agreements' },
        add_agreement:         { he: 'הוסף הסכם', en: 'Add agreement' },
        no_agreements:         { he: 'אין הסכמים', en: 'No agreements' },
        choose:                { he: 'בחר...', en: 'Choose...' },
        reset:                 { he: 'איפוס', en: 'Reset' },
        reset_to_official:     { he: 'איפוס לתוצאות רשמיות', en: 'Reset to official results' },
        knesset_composition:   { he: 'הרכב הכנסת (120 מושבים)', en: 'Knesset Composition (120 seats)' },
        seats_120:             { he: '120 מושבים', en: '120 seats' },
        right_bloc:            { he: 'גוש ימין-חרדי', en: 'Right-Haredi bloc' },
        left_bloc:             { he: 'גוש מרכז-שמאל-ערבי', en: 'Center-Left-Arab bloc' },
        seat_allocation:       { he: 'חלוקת המנדטים', en: 'Seat Allocation' },
        in_surplus_agreement:  { he: 'בהסכם עודפים', en: 'In surplus agreement' },
        votes_to_gain:         { he: '+{n} לתוספת מנדט', en: '+{n} to gain a seat' },
        votes_to_lose:         { he: '-{n} לאיבוד מנדט', en: '-{n} to lose a seat' },
        gain_from:             { he: 'מ{party}', en: 'from {party}' },
        lose_to:               { he: 'ל{party}', en: 'to {party}' },
        step:                  { he: 'צעד:', en: 'Step:' },
        edit_votes:            { he: 'עריכת קולות', en: 'Edit votes' },
        settings:              { he: 'הגדרות', en: 'Settings' },

        /* ── Irregular page ── */
        irregular_title:       { he: 'קלפיות חריגות', en: 'Irregular Ballots' },
        anomaly_types:         { he: 'סוגי חריגות:', en: 'Anomaly types:' },
        severity:              { he: 'חומרה', en: 'Severity' },
        high_severity:         { he: 'גבוהה', en: 'High' },
        medium_severity:       { he: 'בינונית', en: 'Medium' },
        low_severity:          { he: 'נמוכה', en: 'Low' },
        data_entry_error:      { he: 'שגיאת הקלדה', en: 'Data entry error' },
        round_numbers:         { he: 'מספרים עגולים', en: 'Round numbers' },
        turnout_anomaly:       { he: 'חריגת הצבעה', en: 'Turnout anomaly' },
        statistical_outlier:   { he: 'חריג סטטיסטי', en: 'Statistical outlier' },
        extreme_dominance:     { he: 'שליטה קיצונית', en: 'Extreme dominance' },
        small_party_spike:     { he: 'זינוק מפלגה קטנה', en: 'Small party spike' },
        sort_by:               { he: 'מיון:', en: 'Sort:' },
        by_severity:           { he: 'לפי חומרה', en: 'By severity' },
        by_settlement:         { he: 'לפי יישוב', en: 'By settlement' },
        found_n_anomalies:     { he: 'נמצאו {n} חריגות', en: '{n} anomalies found' },

        /* ── Footer / Methodology ── */
        methodology_short:     { he: 'מתודולוגיה:', en: 'Methodology:' },
        methodology_text:      { he: 'כל קלפי מהווה תצפית רועשת (noisy observation) של דפוס מעבר הקולות הארצי. המצביעים בכל קלפי נוהגים באופן דומה לאוכלוסייה הכללית, אך גודל המדגם הקטן (מאות בוחרים) יוצר רעש סטטיסטי. על ידי רגרסיה על אלפי קלפיות ברחבי הארץ, ניתן לשחזר את מטריצת המעבר הארצית האמיתית.', en: 'Each ballot box is a noisy observation of the national vote transfer pattern. Voters in each box behave similarly to the general population, but the small sample size (hundreds of voters) creates statistical noise. By regressing over thousands of ballot boxes nationwide, we can recover the true national transfer matrix.' },
        read_more_methodology: { he: 'קראו עוד על המתודולוגיה...', en: 'Read more about the methodology...' },
        credits_line:          { he: '© הראל קין', en: '© Harel Kain' },
        source_code:           { he: 'קוד מקור', en: 'Source code' },
        bmc_text:              { he: 'אהבתם? עזרו לתמוך בפיתוח האתר ובעלויות שלו - קנו לי קפה', en: 'Like it? Help support the site\'s development – buy me a coffee' },
        bmc_title:             { he: 'קנו לי כוס קפה ☕', en: 'Buy me a coffee ☕' },

        /* ── Methodology modal ── */
        about_methodology:     { he: 'על המתודולוגיה', en: 'About the Methodology' },
        method_basic_idea:     { he: '🎯 הרעיון הבסיסי', en: '🎯 The Basic Idea' },
        method_math_model:     { he: '📊 המודל המתמטי', en: '📊 The Mathematical Model' },
        method_optimization:   { he: '⚙️ האופטימיזציה', en: '⚙️ The Optimization' },
        method_r_squared:      { he: '📈 מדד איכות: R²', en: '📈 Quality Metric: R²' },
        method_limitations:    { he: '⚠️ מגבלות ואזהרות', en: '⚠️ Limitations and Caveats' },
        method_further:        { he: '📚 קריאה נוספת', en: '📚 Further Reading' },

        method_p1: { he: 'דמיינו שאתם רוצים לדעת לאן עברו הקולות של מפלגה X בבחירות הקודמות. ברור שחלק מהמצביעים נשארו נאמנים, אחרים עברו למפלגה Y, ואחרים למפלגה Z. אבל איך אפשר לדעת את הפילוח הזה בלי לשאול כל אזרח איך הצביע?', en: 'Imagine you want to know where party X\'s voters went in the previous election. Clearly some stayed loyal, others moved to party Y or Z. But how can you determine this breakdown without asking every citizen how they voted?' },
        method_p2: { he: 'הפתרון: <strong>להסתכל על קלפיות בודדות</strong>. בכל קלפי יש כמה מאות מצביעים, ויש לנו את תוצאות ההצבעה שלהם בשתי בחירות עוקבות. אם בקלפי מסוימת הייתה תמיכה גבוהה במפלגה X בבחירות הקודמות, ובבחירות הנוכחיות יש תמיכה גבוהה במפלגה Y - זה רמז שמצביעי X עברו ל-Y.', en: 'The solution: <strong>look at individual ballot boxes</strong>. Each box has a few hundred voters, and we have their voting results in two consecutive elections. If a certain box had high support for party X in the previous election, and high support for party Y in the current election — that\'s a hint that X voters moved to Y.' },
        method_p3: { he: 'כמובן, קלפי בודדת היא מדגם קטן ורועש. אבל כשמנתחים <strong>אלפי קלפיות</strong> יחד, הרעש מתקזז והתמונה האמיתית מתגלה.', en: 'Of course, a single ballot box is a small, noisy sample. But when analyzing <strong>thousands of boxes</strong> together, the noise cancels out and the true picture emerges.' },
        method_p4: { he: 'אנחנו מחפשים <strong>מטריצת מעבר</strong> M, כך שכל תא M[i,j] מייצג את ההסתברות שמצביע שהצביע למפלגה i בבחירות הקודמות יצביע למפלגה j בבחירות הנוכחיות.', en: 'We seek a <strong>transfer matrix</strong> M where each cell M[i,j] represents the probability that a voter who voted for party i in the previous election will vote for party j in the current one.' },
        method_p5: { he: 'המודל מניח שהתפלגות ההצבעה בכל קלפי מקיימת את המשוואה:', en: 'The model assumes each ballot box\'s voting distribution satisfies:' },
        method_p6: { he: 'המטריצה M מחושבת באמצעות <strong>אופטימיזציה קמורה</strong> (Convex Optimization), שמוצאת את M שממזערת את סכום ריבועי השגיאות:', en: 'Matrix M is computed via <strong>convex optimization</strong>, finding M that minimizes the sum of squared errors:' },
        method_constraints: { he: 'תחת האילוצים הבאים:', en: 'Subject to:' },
        method_nonneg: { he: '<strong>אי-שליליות:</strong> M[i,j] ≥ 0 (לא ייתכן מעבר שלילי)', en: '<strong>Non-negativity:</strong> M[i,j] ≥ 0 (no negative transfers)' },
        method_stochastic: { he: '<strong>סטוכסטיות:</strong> סכום כל שורה שווה ל-1 (כל המצביעים הולכים למקום כלשהו)', en: '<strong>Stochasticity:</strong> each row sums to 1 (every voter goes somewhere)' },
        method_solver: { he: 'הפתרון מתקבל באמצעות הספרייה CVXPY עם הפותר SCS.', en: 'Solved using CVXPY with the SCS solver.' },
        method_r2_desc: { he: 'מדד R² (R-squared) מציין כמה טוב המודל מסביר את השונות בנתונים. ערך 1.0 מציין התאמה מושלמת, וערך 0 מציין שהמודל לא מסביר כלום.', en: 'R² (R-squared) indicates how well the model explains variance in the data. A value of 1.0 means perfect fit; 0 means the model explains nothing.' },
        method_r2_range: { he: 'בפועל, אנחנו מקבלים ערכי R² בטווח 0.7-0.9, שמעידים על התאמה טובה אך לא מושלמת - מה שהגיוני, כי המודל הוא פישוט של המציאות.', en: 'In practice we obtain R² values of 0.7–0.9, indicating good but imperfect fit — reasonable, since the model is a simplification of reality.' },
        method_lim_uniform: { he: '<strong>הנחת אחידות:</strong> המודל מניח שדפוס המעבר זהה בכל הארץ. במציאות, מצביעי ליכוד בתל אביב עשויים להתנהג אחרת ממצביעי ליכוד בירושלים.', en: '<strong>Uniformity assumption:</strong> The model assumes the transfer pattern is identical nationwide. In reality, Likud voters in Tel Aviv may behave differently from those in Jerusalem.' },
        method_lim_new: { he: '<strong>מצביעים חדשים ונפטרים:</strong> המודל מתעלם מכניסת מצביעים חדשים (בני 18+) וממצביעים שנפטרו. אלה מיוצגים באופן מאולץ כ"מעבר" ממפלגה כלשהי.', en: '<strong>New and deceased voters:</strong> The model ignores new eligible voters (18+) and those who passed away. These are forced into appearing as "transfers" from some party.' },
        method_lim_changes: { he: '<strong>שינויים בהרכב הקלפי:</strong> תושבים עוברים דירה, קלפיות מתפצלות או מתמזגות. אנחנו משווים רק קלפיות עם אותו מזהה, מה שמפספס חלק מהתמונה.', en: '<strong>Ballot box changes:</strong> Residents move, boxes split or merge. We only compare boxes with the same ID, missing part of the picture.' },
        method_lim_causal: { he: '<strong>קורלציה ≠ סיבתיות:</strong> המודל מוצא קשרים סטטיסטיים, לא מוכיח שמצביעים באמת עברו. יכולים להיות גורמים נסתרים שמסבירים את הקורלציות.', en: '<strong>Correlation ≠ causation:</strong> The model finds statistical associations, not proof that voters actually switched. Hidden factors may explain the correlations.' },
        method_lim_uncertainty: { he: '<strong>אי-ודאות:</strong> התוצאות הן אומדנים סטטיסטיים עם שולי שגיאה. מעברים קטנים (פחות מ-5%) עשויים להיות רעש סטטיסטי ולא מגמה אמיתית.', en: '<strong>Uncertainty:</strong> Results are statistical estimates with margins of error. Small transfers (<5%) may be noise rather than genuine trends.' },
        method_code_link: { he: 'הקוד המלא זמין ב', en: 'Full source code available on ' },

        /* ── Mobile about ── */
        about:                 { he: 'אודות', en: 'About' },
        about_site:            { he: 'אודות האתר', en: 'About the site' },
        about_description:     { he: 'אתר קולות נודדים מאפשר לחקור את דפוסי ההצבעה בבחירות לכנסת ישראל, ולראות כיצד קולות נודדים בין מפלגות מבחירות לבחירות.', en: 'Migrating Votes allows you to explore voting patterns in Israeli Knesset elections, and see how votes migrate between parties from one election to the next.' },
        license:               { he: 'רישיון', en: 'License' },

        /* ── Watermark (PNG export) ── */
        watermark_created:     { he: 'נוצר באתר קולות נודדים, כל הזכויות שמורות', en: 'Created with Migrating Votes – all rights reserved' },

        /* ── D'Hondt party names (for hardcoded lists) ── */
        party_likud:           { he: 'הליכוד', en: 'Likud' },
        party_yesh_atid:       { he: 'יש עתיד', en: 'Yesh Atid' },
        party_rz:              { he: 'הציונות הדתית', en: 'Religious Zionism' },
        party_national_unity:  { he: 'המחנה הממלכתי', en: 'National Unity' },
        party_shas:            { he: 'ש״ס', en: 'Shas' },
        party_utj:             { he: 'יהדות התורה', en: 'United Torah Judaism' },
        party_yb:              { he: 'ישראל ביתנו', en: 'Yisrael Beiteinu' },
        party_raam:            { he: 'רע״ם', en: 'Ra\'am' },
        party_hadash_taal:     { he: 'חד״ש-תע״ל', en: 'Hadash-Taal' },
        party_labor:           { he: 'העבודה', en: 'Labor' },
        party_meretz:          { he: 'מרצ', en: 'Meretz' },
        party_balad:           { he: 'בל״ד', en: 'Balad' },
        party_jewish_home:     { he: 'הבית היהודי', en: 'The Jewish Home' },
        party_hofesh:          { he: 'חופש כלכלי', en: 'Economic Freedom' },
        party_beometz:         { he: 'באומץ בשבילך', en: 'Courageously For You' },
        party_hakalkalit:      { he: 'הכלכלית החדשה', en: 'The New Economy' },
    };

    /* ── Party Hebrew→English name map (for data-driven parties) ── */
    const partyNameMap = {
        'הליכוד': 'Likud',
        'יש עתיד': 'Yesh Atid',
        'הציונות הדתית': 'Religious Zionism',
        'המחנה הממלכתי': 'National Unity',
        'ש״ס': 'Shas',
        'יהדות התורה': 'United Torah Judaism',
        'ישראל ביתנו': 'Yisrael Beiteinu',
        'רע״ם': 'Ra\'am',
        'חד״ש-תע״ל': 'Hadash-Taal',
        'העבודה': 'Labor',
        'מרצ': 'Meretz',
        'בל״ד': 'Balad',
        'הבית היהודי': 'The Jewish Home',
        'כחול לבן': 'Blue and White',
        'ימינה': 'Yamina',
        'תקווה חדשה': 'New Hope',
        'הרשימה המשותפת': 'Joint List',
        'הימין החדש': 'New Right',
        'זהות': 'Zehut',
        'כולנו': 'Kulanu',
        'המחנה הדמוקרטי': 'Democratic Union',
        'העבודה-גשר': 'Labor-Gesher',
        'עבודה-גשר-מרצ': 'Labor-Gesher-Meretz',
        'רע״ם-בל״ד': 'Ra\'am-Balad',
        'חופש כלכלי': 'Economic Freedom',
        'באומץ בשבילך': 'Courageously For You',
        'הכלכלית החדשה': 'The New Economy',
    };

    /* ── State ── */
    let currentLang = 'he';

    /* ── Core functions ── */

    /** Translate a key, with optional {param} interpolation. */
    function t(key, params) {
        const entry = dict[key];
        if (!entry) return key;
        let text = entry[currentLang] || entry.he || key;
        if (params) {
            Object.keys(params).forEach(k => {
                text = text.replace(new RegExp('\\{' + k + '\\}', 'g'), params[k]);
            });
        }
        return text;
    }

    /** Get party display name: uses info.name_en from data or the static map. */
    function partyName(partyObj) {
        if (currentLang === 'he') {
            return typeof partyObj === 'string' ? partyObj : (partyObj.name || partyObj);
        }
        if (typeof partyObj === 'string') {
            return partyNameMap[partyObj] || partyObj;
        }
        // If it's an object with info.name_en
        if (partyObj.info && partyObj.info.name_en) return partyObj.info.name_en;
        if (partyObj.name_en) return partyObj.name_en;
        return partyNameMap[partyObj.name] || partyObj.name;
    }

    /** Get leader display name from a party info object. */
    function leaderName(info) {
        if (!info) return '';
        if (currentLang === 'en' && info.leader_en) return info.leader_en;
        return info.leader || '';
    }

    /** Get election display name from an election object. */
    function electionName(electionObj) {
        if (!electionObj) return '';
        if (currentLang === 'en' && electionObj.name_en) return electionObj.name_en;
        return electionObj.name || '';
    }

    /** Settlement name English lookup (loaded lazily). */
    let _settlementMap = null;
    let _settlementMapLoading = false;

    function loadSettlementNames() {
        if (_settlementMap || _settlementMapLoading) return;
        _settlementMapLoading = true;
        // Determine path prefix: mobile pages are in m/ subfolder
        const prefix = location.pathname.includes('/m/') ? '../' : '';
        fetch(prefix + 'data/settlement_names_en.json')
            .then(r => r.json())
            .then(data => { _settlementMap = data; })
            .catch(() => { _settlementMap = {}; })
            .finally(() => { _settlementMapLoading = false; });
    }

    // Pre-load if starting in English
    if (currentLang === 'en') loadSettlementNames();

    /** Get settlement display name (English transliteration or Hebrew original). */
    function settlementName(name) {
        if (!name) return '';
        if (currentLang === 'he') return name;
        if (!_settlementMap) {
            loadSettlementNames();
            return name; // Return Hebrew until loaded
        }
        return _settlementMap[name] || name;
    }

    /** Locale-aware number formatting. */
    function fmtNum(n) {
        if (n == null) return '';
        return n.toLocaleString(currentLang === 'he' ? 'he-IL' : 'en-US');
    }

    /** Get current language. */
    function getLang() {
        return currentLang;
    }

    /** Check if current language is RTL. */
    function isRTL() {
        return currentLang === 'he';
    }

    /* ── DOM operations ── */

    /** Apply translations to elements with data-i18n attributes. */
    function applyTranslations(root) {
        const scope = root || document;

        // data-i18n="key" → textContent
        scope.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const params = el.getAttribute('data-i18n-params');
            el.textContent = t(key, params ? JSON.parse(params) : undefined);
        });

        // data-i18n-html="key" → innerHTML
        scope.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            el.innerHTML = t(key);
        });

        // data-i18n-placeholder="key" → placeholder
        scope.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
        });

        // data-i18n-title="key" → title
        scope.querySelectorAll('[data-i18n-title]').forEach(el => {
            el.title = t(el.getAttribute('data-i18n-title'));
        });
    }

    /** Set language and update the page. */
    function setLang(lang) {
        currentLang = lang;
        if (lang === 'en') loadSettlementNames();
        const isHe = lang === 'he';

        // Update dir & lang on html
        document.documentElement.setAttribute('dir', isHe ? 'rtl' : 'ltr');
        document.documentElement.setAttribute('lang', isHe ? 'he' : 'en');

        // Update font
        document.body.style.fontFamily = isHe
            ? "'Heebo', sans-serif"
            : "'Inter', 'Heebo', sans-serif";

        // Persist
        localStorage.setItem('lang', lang);

        // Update URL param without reload
        const url = new URL(window.location);
        if (lang === 'he') {
            url.searchParams.delete('lang');
        } else {
            url.searchParams.set('lang', lang);
        }
        history.replaceState(null, '', url);

        // Apply static translations
        applyTranslations();

        // Update toggle buttons
        document.querySelectorAll('.lang-toggle').forEach(btn => {
            btn.textContent = isHe ? 'EN' : 'עב';
            btn.setAttribute('title', isHe ? 'Switch to English' : 'עבור לעברית');
        });

        // Dispatch event for page-specific re-renders
        window.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
    }

    /** Inject a language toggle button into a container. */
    function injectLangToggle(selector) {
        const container = document.querySelector(selector);
        if (!container) return;
        // Don't double-inject
        if (container.querySelector('.lang-toggle')) return;

        const btn = document.createElement('button');
        btn.className = 'lang-toggle';
        btn.type = 'button';
        btn.textContent = currentLang === 'he' ? 'EN' : 'עב';
        btn.setAttribute('title', currentLang === 'he' ? 'Switch to English' : 'עבור לעברית');
        btn.addEventListener('click', () => {
            setLang(currentLang === 'he' ? 'en' : 'he');
        });
        container.appendChild(btn);
    }

    /* ── Initialization ── */
    function init() {
        // Determine initial language: URL param > localStorage > default he
        const urlParams = new URLSearchParams(window.location.search);
        const urlLang = urlParams.get('lang');
        const storedLang = localStorage.getItem('lang');
        const lang = (urlLang === 'en' || urlLang === 'he') ? urlLang
            : (storedLang === 'en' || storedLang === 'he') ? storedLang
            : 'he';

        currentLang = lang;

        // Set initial direction without triggering events
        const isHe = lang === 'he';
        document.documentElement.setAttribute('dir', isHe ? 'rtl' : 'ltr');
        document.documentElement.setAttribute('lang', isHe ? 'he' : 'en');
        document.body.style.fontFamily = isHe
            ? "'Heebo', sans-serif"
            : "'Inter', 'Heebo', sans-serif";

        // Apply translations on DOM ready
        applyTranslations();
    }

    // Run init as early as possible
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    /* ── Public API ── */
    window.i18n = {
        t,
        partyName,
        leaderName,
        electionName,
        settlementName,
        fmtNum,
        getLang,
        isRTL,
        setLang,
        applyTranslations,
        injectLangToggle,
        dict,
        partyNameMap,
    };
})();
