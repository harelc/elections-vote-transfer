/**
 * i18n module for קולות נודדים / Migrating Votes
 * Provides Hebrew ↔ English toggle across all pages.
 */
(function () {
    'use strict';

    /* ── Election 26 feature flag ── */
    const SHOW_E26 = new URLSearchParams(location.search).has('e26');

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
        nav_animation:         { he: '▶ אנימציה', en: '▶ Animation' },

        /* ── Mobile tabs ── */
        tab_map:               { he: 'מפה', en: 'Map' },
        tab_sankey:            { he: 'נדידה', en: 'Flow' },
        tab_tsne:              { he: 'פיזור', en: 'Cluster' },
        tab_scatter:           { he: 'השוואה', en: 'Compare' },
        tab_dhondt:            { he: 'מנדטים', en: 'Seats' },

        /* ── Sankey page ── */
        from_election:         { he: 'מבחירות', en: 'From election' },
        to_election:           { he: 'לבחירות', en: 'To election' },
        eligible_voters:       { he: 'בעלי זכות בחירה', en: 'Eligible voters' },
        voted:                 { he: 'הצביעו', en: 'Voted' },
        turnout_pct:           { he: 'אחוז הצבעה', en: 'Turnout' },
        common_precincts:      { he: 'קלפיות משותפות', en: 'Common precincts' },
        correlation_label:     { he: 'מקדם פירסון:', en: 'Pearson coefficient:' },
        regression_label:      { he: 'משוואת רגרסיה:', en: 'Regression equation:' },
        r_squared:             { he: 'R²:', en: 'R²:' },
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
        loading_please_wait:   { he: 'טוען נתונים, נא להמתין...', en: 'Loading data, please wait...' },
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
        official_results:      { he: 'תוצאות רשמיות - כנסת ה-{n}', en: 'Official results – Knesset {n}' },
        below_threshold:       { he: 'לא עברה', en: 'Below threshold' },
        abstention_label:      { he: 'הצג לא מצביעים', en: 'Show non-voters' },
        abstention_off:        { he: 'ללא', en: 'Hidden' },
        abstention_on:         { he: 'מוצג', en: 'Shown' },
        abstention_off_short:  { he: 'ללא לא מצביעים', en: 'No non-voters' },
        abstention_on_short:   { he: 'עם לא מצביעים', en: 'With non-voters' },
        did_not_vote:          { he: 'לא הצביעו', en: 'Did not vote' },

        /* ── T-SNE page ── */
        tsne_title:            { he: 'התפלגות קלפיות', en: 'Ballot Distribution' },
        tsne_subtitle:         { he: 'מיפוי T-SNE של קלפיות לפי התפלגות ההצבעה', en: 'T-SNE mapping of ballot boxes by voting distribution' },
        umap_subtitle:         { he: 'מיפוי UMAP של קלפיות לפי התפלגות ההצבעה', en: 'UMAP mapping of ballot boxes by voting distribution' },
        projection_method:     { he: 'שיטת הטלה', en: 'Projection method' },
        filter_by_settlement:  { he: 'סינון לפי יישוב', en: 'Filter by settlement' },
        search_ballot:         { he: 'חיפוש קלפי', en: 'Search ballot' },
        color_by:              { he: 'צביעה לפי:', en: 'Color by:' },
        color_by_short:        { he: 'צביעה לפי', en: 'Color by' },
        zoom_hint:             { he: 'גודל = מספר מצביעים | גלגל לזום | גרירה להזזה', en: 'Size = number of voters | Scroll to zoom | Drag to pan' },
        dynamic_range:         { he: 'טווח דינמי', en: 'Dynamic range' },
        turnout:               { he: 'אחוז הצבעה', en: 'Turnout' },
        socioeconomic:         { he: 'אשכול חברתי-כלכלי', en: 'Socioeconomic cluster' },
        cross_entropy:         { he: 'מרחק מהממוצע הארצי', en: 'Distance from national avg.' },
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
        geomap_subtitle:       { he: 'מפה גיאוגרפית של קלפיות הצבעה', en: 'Geographic map of polling stations' },
        display_settings:      { he: 'הגדרות תצוגה', en: 'Display settings' },
        color_mode:            { he: 'צביעה:', en: 'Color:' },
        winner:                { he: 'מפלגה מנצחת', en: 'Winning party' },
        specific_party:        { he: 'מפלגה ספציפית', en: 'Specific party' },
        filter_settlement:     { he: 'סנן לפי יישוב...', en: 'Filter by settlement...' },
        stations:              { he: 'תחנות', en: 'Stations' },

        /* ── Scatter page ── */
        scatter_title:         { he: 'השוואת תמיכה במפלגות', en: 'Party Support Comparison' },
        scatter_subtitle:      { he: 'השוואת תמיכה במפלגות לפי קלפיות', en: 'Comparing party support across ballot boxes' },
        x_axis:                { he: 'ציר X:', en: 'X axis:' },
        x_axis_horizontal:     { he: 'ציר X (אופקי)', en: 'X Axis (horizontal)' },
        y_axis:                { he: 'ציר Y:', en: 'Y axis:' },
        y_axis_vertical:       { he: 'ציר Y (אנכי)', en: 'Y Axis (vertical)' },
        statistics:            { he: 'סטטיסטיקות', en: 'Statistics' },
        scale_type:            { he: 'סוג סקאלה:', en: 'Scale type:' },
        scale_linear:          { he: 'לינארי', en: 'Linear' },
        scale_log:             { he: 'לוגריתמי', en: 'Logarithmic' },
        election:              { he: 'בחירות', en: 'Election' },
        party:                 { he: 'מפלגה', en: 'Party' },
        pct_unit:              { he: 'אחוזים', en: 'Percentages' },
        abs_unit:              { he: 'מספרים מוחלטים', en: 'Absolute numbers' },
        units:                 { he: 'יחידות:', en: 'Units:' },
        all_settlements:       { he: 'כל היישובים', en: 'All settlements' },
        swap_axes:             { he: 'החלף צירים', en: 'Swap axes' },
        legend_small_ballot:   { he: 'קלפי קטנה', en: 'Small ballot' },
        legend_large_ballot:   { he: 'קלפי גדולה', en: 'Large ballot' },
        reset_zoom:            { he: 'איפוס תקריב', en: 'Reset zoom' },

        scatter_methodology_text: { he: 'כל נקודה מייצגת קלפי אחת. מיקום הנקודה נקבע לפי אחוז התמיכה במפלגה הנבחרת בציר X (אופקי) ובציר Y (אנכי). ניתן להשוות מפלגות מאותן בחירות או מבחירות שונות - במקרה של בחירות שונות, מוצגות רק קלפיות שקיימות בשתי הבחירות. קו המגמה (מקווקו) מציג את קו הרגרסיה הליניארית.', en: 'Each dot represents one ballot box. Its position is determined by support percentage for the selected party on the X axis (horizontal) and Y axis (vertical). You can compare parties from the same or different elections — when comparing different elections, only ballot boxes that exist in both are shown. The dashed trend line shows the linear regression.' },

        /* ── d'Hondt page ── */
        dhondt_title:          { he: 'מחשבון באדר-עופר', en: 'D\'Hondt Calculator' },
        dhondt_subtitle:       { he: 'מחשבון חלוקת מנדטים בשיטת באדר-עופר', en: 'Seat allocation calculator using the D\'Hondt method' },
        threshold:             { he: 'אחוז חסימה', en: 'Electoral threshold' },
        threshold_pct:         { he: 'אחוז חסימה:', en: 'Threshold:' },
        knesset_size_label:    { he: 'גודל הכנסת:', en: 'Knesset size:' },
        surplus_agreements:    { he: 'הסכמי עודפים', en: 'Surplus agreements' },
        add_agreement:         { he: 'הוסף הסכם', en: 'Add agreement' },
        no_agreements:         { he: 'אין הסכמים', en: 'No agreements' },
        choose:                { he: 'בחר...', en: 'Choose...' },
        reset:                 { he: 'איפוס', en: 'Reset' },
        reset_to_official:     { he: 'איפוס לתוצאות רשמיות', en: 'Reset to official results' },
        dhondt_election_label: { he: 'בחירות:', en: 'Election:' },
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
        irregular_subtitle:    { he: 'זיהוי קלפיות עם דפוסי הצבעה חריגים', en: 'Identifying ballot boxes with irregular voting patterns' },
        irregular_methodology_text: { he: 'המערכת מנתחת את תוצאות כל קלפי ומחפשת דפוסים חריגים בכמה קטגוריות: טעויות הזנה (קולות שנרשמו בעמודה לא נכונה), מספרים עגולים חשודים, חריגות סטטיסטיות (תוצאות שלא מתאימות לאף אשכול דמוגרפי), ותוצאות חריגות למפלגות שוליים. הנתונים מבוססים על תוצאות רשמיות מאתר ועדת הבחירות המרכזית.', en: 'The system analyzes results from every ballot box and searches for irregular patterns across several categories: data entry errors (votes recorded in the wrong party column), suspicious round numbers, statistical outliers (results that don\'t match any known demographic cluster), and unusually high results for fringe parties. Data is based on official results from the Central Elections Committee website.' },
        tsne_methodology_text:      { he: 'מפת הקלפיות מבוססת על אלגוריתם <bdi><a href="https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding" target="_blank" style="color:var(--accent-primary)">T-SNE</a> (t-distributed Stochastic Neighbor Embedding)</bdi> — טכניקת הפחתת מימדים שממירה נתונים רב-מימדיים (התפלגות ההצבעה לפי מפלגות) לנקודות דו-מימדיות. קלפיות עם דפוסי הצבעה דומים ממוקמות קרוב זו לזו במפה. גודל הנקודה משקף את מספר המצביעים, והצבע מציג את שיעור ההצבעה או תמיכה במפלגה נבחרת.', en: 'The ballot map is based on the <a href="https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding" target="_blank" style="color:var(--accent-primary)">T-SNE</a> algorithm (t-distributed Stochastic Neighbor Embedding) — a dimensionality reduction technique that converts high-dimensional data (party vote distributions) into 2D points. Ballot boxes with similar voting patterns are placed close together on the map. Dot size reflects voter count, and color shows turnout rate or support for a selected party.' },
        dhondt_methodology_text:    { he: 'שיטת באדר-עופר (D\'Hondt) היא שיטה לחלוקת מנדטים יחסית המיושמת בישראל. בכל סיבוב, מחלקים את מספר הקולות של כל מפלגה במספר המנדטים שכבר קיבלה + 1. המפלגה עם התוצאה הגבוהה ביותר מקבלת את המנדט הבא. התהליך חוזר עד לחלוקת כל 120 המנדטים. מפלגות שעברו את אחוז החסימה יכולות לחתום על הסכם עודפים — קולותיהן מצורפות יחד לחישוב המנה, אך המנדט ניתן למפלגה עם המנה הגבוהה ביותר בתוך ההסכם.', en: 'The Bader-Ofer method (D\'Hondt) is a proportional seat allocation system used in Israel. In each round, each party\'s vote count is divided by the number of seats it has already received + 1. The party with the highest quotient wins the next seat. This repeats until all 120 seats are allocated. Parties that pass the electoral threshold can sign surplus agreements — their votes are combined for quotient calculation, but the seat goes to the party with the highest quotient within the agreement.' },
        stat_analyzed:         { he: 'קלפיות נותחו', en: 'Ballots analyzed' },
        stat_suspects:         { he: 'חשודות שנמצאו', en: 'Suspects found' },
        stat_fixed:            { he: 'תוקנו באתר הרשמי', en: 'Fixed on official site' },
        stat_remaining:        { he: 'נותרו חריגות', en: 'Remaining irregular' },
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
        credits_line:          { he: '© הראל קין', en: '© Harel Cain' },
        source_code:           { he: 'קוד מקור', en: 'Source code' },
        bmc_text:              { he: 'אהבתם? עזרו לתמוך בפיתוח האתר ובעלויות שלו - קנו לי קפה', en: 'Like it? Help support the site\'s development – buy me a coffee' },
        bmc_title:             { he: 'קנו לי כוס קפה ☕', en: 'Buy me a coffee ☕' },
        bmc_line1:             { he: 'אהבתם? רוצים לתמוך בפיתוח האתר?', en: 'Enjoying this? Want to support development?' },
        bmc_line2:             { he: 'קנו לי כוס קפה ☕', en: 'Buy me a coffee ☕' },

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

        /* ── Election labels ── */
        election_21:               { he: 'כנסת 21', en: 'Knesset 21' },
        election_22:               { he: 'כנסת 22', en: 'Knesset 22' },
        election_23:               { he: 'כנסת 23', en: 'Knesset 23' },
        election_24:               { he: 'כנסת 24', en: 'Knesset 24' },
        election_25:               { he: 'כנסת 25', en: 'Knesset 25' },
        election_26:               { he: 'כנסת 26', en: 'Knesset 26' },

        /* ── Dashboard ── */
        nav_home:                  { he: 'ראשי', en: 'Home' },
        dashboard_title:           { he: 'קולות נודדים', en: 'Migrating Votes' },
        dashboard_subtitle:        { he: 'ניתוח אינטראקטיבי של נתוני בחירות לכנסת ישראל', en: 'Interactive analysis of Israeli Knesset election data' },
        dashboard_stat_elections:  { he: 'כנסות', en: 'Elections' },
        dashboard_stat_ballots:    { he: 'קלפיות', en: 'Ballot boxes' },
        dashboard_stat_settlements:{ he: 'יישובים', en: 'Settlements' },
        dashboard_stat_visitors:   { he: 'מבקרים באתר', en: 'Site visitors' },
        dashboard_stat_lists:      { he: 'רשימות', en: 'Lists' },
        card_sankey_desc:          { he: 'תרשים נדידת קולות בין בחירות עוקבות', en: 'Vote flow diagram between consecutive elections' },
        card_animation_desc:       { he: 'אנימציה של נדידת קולות מ-2003 עד 2022', en: 'Animated vote flow from 2003 to 2022' },
        card_tsne_desc:            { he: 'מיפוי קלפיות לפי דמיון דפוסי הצבעה', en: 'Ballot box mapping by voting pattern similarity' },
        card_geomap_desc:          { he: 'מפה גיאוגרפית של קלפיות הצבעה', en: 'Geographic map of polling stations' },
        card_scatter_desc:         { he: 'השוואת תמיכה בין מפלגות לפי קלפיות', en: 'Compare party support across ballot boxes' },
        card_dhondt_desc:          { he: 'חלוקת מנדטים בשיטת באדר-עופר', en: 'Seat allocation using the D\'Hondt method' },
        card_irregular_desc:       { he: 'זיהוי קלפיות עם דפוסי הצבעה חריגים', en: 'Identifying ballot boxes with irregular voting patterns' },
        card_regional_desc:        { he: 'סימולציית בחירות אזוריות לכנסת', en: 'Simulating regional elections for the Knesset' },
        card_settlement_desc:      { he: 'פרופיל הצבעה מפורט לכל יישוב', en: 'Detailed voting profile for each settlement' },
        card_party_desc:           { he: 'מעקב אחרי מפלגות לאורך הבחירות', en: 'Track parties across elections' },

        /* ── Data stories & archive ── */
        stories_title:             { he: 'הידעתם?', en: 'Did you know?' },
        story_1_title:             { he: 'נאמנות ברזל: כמעט כל מצביע יש עתיד נשאר', en: 'Iron loyalty: nearly every Yesh Atid voter stayed' },
        story_1_body:              { he: 'בין בחירות 24 ל-25, יש עתיד שמרה על 99.7% מהמצביעים. ש״ס הגיעה ל-100.1%. לעומתן, כחול לבן שמרה על 21.5% בלבד בחירה קודמת.', en: 'Between elections 24→25, Yesh Atid retained 99.7% of voters. Shas hit 100.1%. Meanwhile Blue and White kept just 21.5% one election earlier.' },
        story_2_title:             { he: '60 נקודות מפרידות בין העיירות המשתתפות ביותר לפחות', en: '60 points separate the highest and lowest turnout towns' },
        story_2_body:              { he: 'תפרח מצביעה ב-86.8%. סאגור ב-27.9%. לשתיהן מעל 500 מצביעים. הפער ממפה כמעט בדיוק את השסע האתנו-דתי.', en: 'Tifrah votes at 86.8%. Saghur at 27.9%. Both have 500+ voters. The gap maps almost perfectly onto the ethno-religious divide.' },
        story_3_title:             { he: 'נדנוד ההצבעה הערבית: תנודה של 22 נקודות ב-4 שנים', en: 'Arab vote swing: 22 points in 4 years' },
        story_3_body:              { he: 'מ-66.1% (בחירות 23, עידן הרשימה המשותפת) לשפל של 44.2% (בחירות 24, אחרי הפיצול). בנגב, לקייה הכפילה את ההשתתפות מ-22% ל-47%.', en: 'From 66.1% (election 23, Joint List era) to a 44.2% low (election 24, post-split). In the Negev, Laqye doubled its turnout from 22% to 47%.' },
        story_4_title:             { he: 'יישובים שבהם התוצאה נגמרה בפער של 0.1%', en: 'Settlements where the result came down to 0.1%' },
        story_4_body:              { he: 'בבסמה, רע״ם מנצחת את בל״ד ב-0.1%. בגבעת שמואל (13,476 מצביעים), הציונות הדתית עוקפת את הליכוד ב-0.1%.', en: 'In Basma, Ra\'am beats Balad by 0.1%. In Givat Shmuel (13,476 voters), Religious Zionism edges Likud by 0.1%.' },
        story_5_title:             { he: 'יש עתיד ניצחה ב-45% מהיישובים — אבל פחות מנדטים מהליכוד', en: 'Yesh Atid won 45% of settlements — but fewer seats than Likud' },
        story_5_body:              { he: 'בבחירות 25, יש עתיד ניצחה ב-504 מתוך 1,120 יישובים. הליכוד ניצח ב-305 בלבד, אך זכה ביותר מנדטים. רוחב מול עומק.', en: 'In election 25, Yesh Atid won 504 of 1,120 settlements. Likud won only 305, yet got more seats. Breadth vs. depth.' },
        story_cta_sankey:          { he: 'גלו בתרשים הנדידה', en: 'Explore in vote flow' },
        story_cta_geomap:          { he: 'גלו במפה', en: 'Explore on map' },
        story_cta_scatter:         { he: 'גלו בהשוואה', en: 'Explore in comparison' },
        story_cta_dhondt:          { he: 'גלו בחישוב המנדטים', en: 'Explore seat calculator' },
        archive_title:             { he: 'מהארכיון: כרזות בחירות', en: 'From the archive: Election posters' },
        archive_credit:            { he: 'ארכיון דן הדני, האוסף הלאומי לתצלומים ע״ש משפחת פריצקר, הספרייה הלאומית', en: 'Dan Hadani Archive, Pritsker Family National Photography Collection, National Library of Israel' },

        /* ── Party profile ── */
        party_profile:             { he: 'פרופיל מפלגה', en: 'Party Profile' },
        nav_party:                 { he: 'פרופיל מפלגה', en: 'Party Profile' },
        seats_trend:               { he: 'מנדטים ותמיכה', en: 'Seats & Support' },
        voter_migration:           { he: 'נדידת מצביעים', en: 'Voter Migration' },
        geographic_strongholds:    { he: 'מעוזים גיאוגרפיים', en: 'Geographic Strongholds' },
        also_known_as:             { he: 'שמות נוספים:', en: 'Also known as:' },
        election_history:          { he: 'היסטוריית בחירות', en: 'Election History' },
        where_from:                { he: 'מאיפה הגיעו מצביעים', en: 'Where voters came from' },
        where_to:                  { he: 'לאן הלכו מצביעים', en: 'Where voters went' },
        national_support:          { he: 'תמיכה ארצית', en: 'National support' },
        top_strongholds:           { he: 'יישובים חזקים', en: 'Top strongholds' },
        bottom_strongholds:        { he: 'יישובים חלשים', en: 'Weakest settlements' },
        merged_into:               { he: 'מוזגה לתוך', en: 'Merged into' },
        did_not_run:               { he: 'לא התמודדה', en: 'Did not run' },
        search_party:              { he: 'חיפוש מפלגה...', en: 'Search party...' },
        support_pct:               { he: '% תמיכה', en: '% support' },
        symbol_label:              { he: 'סמל', en: 'Symbol' },
        leader_col:                { he: 'מנהיג', en: 'Leader' },
        transition_label:          { he: 'מעבר:', en: 'Transition:' },
        party_analytics:           { he: 'מדדים סטטיסטיים', en: 'Statistical Metrics' },
        geographic_concentration:  { he: 'ריכוז גיאוגרפי', en: 'Geographic Concentration' },
        effective_settlements:     { he: 'יישובים אפקטיביים (1/HHI)', en: 'Effective settlements (1/HHI)' },
        effective_settlements_tip: { he: 'כמה יישובים עם חלוקת קולות שווה היו נותנים את אותה רמת ריכוז (1/HHI)', en: 'How many settlements with equal vote shares would produce the same concentration level (1/HHI)' },
        hhi_label:                 { he: 'מדד הרפינדל (HHI)', en: 'Herfindahl Index (HHI)' },
        settlements_for_half:      { he: 'יישובים ל-50% קולות', en: 'Settlements for 50% of votes' },
        settlements_for_90:        { he: 'יישובים ל-90% קולות', en: 'Settlements for 90% of votes' },
        similar_parties:           { he: 'מפלגות דומות', en: 'Similar Parties' },
        cosine_similarity:         { he: 'דמיון קוסינוס', en: 'Cosine similarity' },
        ballot_correlation:        { he: 'מקדם פירסון (קלפיות)', en: 'Pearson coefficient (ballots)' },
        volatility_label:          { he: 'תנודתיות', en: 'Volatility' },
        percentile_label:          { he: 'אחוזון', en: 'Percentile' },
        volatility_explainer:      { he: 'מדד פדרסן — סכום השינויים המוחלטים בתמיכה בין בחירות. ערך גבוה = הצבעה משתנה מאוד', en: 'Pedersen index — sum of absolute changes in party support between elections. Higher = more volatile voting' },
        hhi_explainer:             { he: 'מדד ריכוז הרפינדל — ככל שהערך נמוך יותר, הקולות מפוזרים ביותר יישובים. מספר "יישובים אפקטיביים" = מספר היישובים שווי-משקל המקביל לריכוז הנמדד', en: 'Herfindahl concentration index — lower values mean votes spread across more settlements. "Effective settlements" = equivalent number of equal-weight settlements' },
        settlements_50_explainer:  { he: 'מספר היישובים הגדולים ביותר שמרכזים מחצית מהקולות', en: 'Number of largest settlements that account for half of all votes' },
        settlements_90_explainer:  { he: 'מספר היישובים הגדולים ביותר שמרכזים 90% מהקולות', en: 'Number of largest settlements that account for 90% of votes' },
        cosine_explainer:          { he: 'דמיון קוסינוס — עד כמה שתי מפלגות מופיעות באותם יישובים. 1 = התפלגות זהה, 0 = אין חפיפה', en: 'Cosine similarity — how much two parties appear in the same settlements. 1 = identical distribution, 0 = no overlap' },
        ballot_corr_explainer:     { he: 'מקדם פירסון ברמת הקלפי — ערך חיובי = כשמפלגה אחת חזקה, גם השנייה חזקה. שלילי = מתחרות', en: 'Pearson coefficient at ballot level — positive = parties are strong together, negative = they compete' },

        /* ── Settlement profile ── */
        settlement_profile:        { he: 'פרופיל יישוב', en: 'Settlement Profile' },
        voting_trends:             { he: 'מגמות הצבעה', en: 'Voting Trends' },
        latest_breakdown:          { he: 'פירוט בחירות אחרונות', en: 'Latest Election Breakdown' },
        ballot_table:              { he: 'טבלת קלפיות', en: 'Ballot Table' },
        population:                { he: 'אוכלוסייה', en: 'Population' },
        district:                  { he: 'מחוז', en: 'District' },
        settlement_type:           { he: 'סוג יישוב', en: 'Settlement type' },
        wiki_source:               { he: 'מקור: ויקיפדיה', en: 'Source: Wikipedia' },
        go_to_profile:             { he: 'פרופיל יישוב', en: 'Settlement profile' },
        venue:                     { he: 'מקום', en: 'Venue' },
        winning_party:             { he: 'מפלגה מנצחת', en: 'Winning party' },
        legend_single_ballot:      { he: 'קלפי בודדת — הצבע מייצג את המפלגה המנצחת', en: 'Single ballot — color is the winning party' },
        legend_spread_cluster:     { he: 'מקבץ של אתרי הצבעה שונים — לחץ כדי להתקרב', en: 'Multiple voting sites — click to zoom in' },
        legend_colocated_cluster:  { he: 'מקבץ קלפיות באותו מקום', en: 'Ballots at same location' },
        legend_pie_explain:        { he: 'צבעי העוגה במקבצים: חלוקת המפלגה המנצחת בכל קלפי', en: 'Cluster pie colors: winning party share per ballot' },
        search_settlement_profile: { he: 'חיפוש יישוב...', en: 'Search settlement...' },

        /* ── Mobile about ── */
        about:                 { he: 'אודות', en: 'About' },
        about_site:            { he: 'אודות האתר', en: 'About the site' },
        about_description:     { he: 'אתר קולות נודדים מאפשר לחקור את דפוסי ההצבעה בבחירות לכנסת ישראל, ולראות כיצד קולות נודדים בין מפלגות מבחירות לבחירות.', en: 'Migrating Votes allows you to explore voting patterns in Israeli Knesset elections, and see how votes migrate between parties from one election to the next.' },
        license:               { he: 'רישיון', en: 'License' },

        /* ── Watermark (PNG export) ── */
        watermark_created:     { he: 'נוצר באתר קולות נודדים, כל הזכויות שמורות', en: 'Created with Migrating Votes – all rights reserved' },

        /* ── d'Hondt party names (for hardcoded lists) ── */
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

        /* ── Regional elections page ── */
        nav_regional:          { he: 'בחירות אזוריות', en: 'Regional Elections' },
        tab_regional:          { he: 'אזורי', en: 'Regional' },
        regional_title:        { he: 'הבחירות האזוריות', en: 'Regional Elections' },
        regional_subtitle:     { he: 'סימולציית בחירות אזוריות לכנסת ישראל', en: 'Simulating regional elections for the Israeli Knesset' },
        regions_label:         { he: 'מחוזות בחירה:', en: 'Electoral districts:' },
        national_seats_label:  { he: 'מנדטים ארציים:', en: 'National seats:' },
        regional:              { he: 'אזורי', en: 'Regional' },
        national:              { he: 'ארצי', en: 'National' },
        threshold_label:       { he: 'אחוז חסימה:', en: 'Threshold:' },
        simulation_results:    { he: 'תוצאות הסימולציה', en: 'Simulation Results' },
        actual_seats:          { he: 'מנדטים בפועל', en: 'Actual seats' },
        simulated_seats:       { he: 'מנדטים בסימולציה', en: 'Simulated seats' },
        difference:            { he: 'הפרש', en: 'Difference' },
        region_summary:        { he: 'סיכום אזורים', en: 'Region Summary' },
        region_col:            { he: 'אזור', en: 'Region' },
        eligible_col:          { he: 'בזב״ה', en: 'Eligible' },
        seats_col:             { he: 'מנדטים', en: 'Seats' },
        ratio_col:             { he: 'בזב״ה/מנדט', en: 'Elig./seat' },
        region_details:        { he: 'פרטי אזור', en: 'Region Details' },
        region_seats:          { he: '{n} מנדטים', en: '{n} seats' },
        eligible_in_region:    { he: 'בעלי זכות בחירה:', en: 'Eligible voters:' },
        stations_in_region:    { he: 'קלפיות:', en: 'Stations:' },
        click_region:          { he: 'לחצו על אזור במפה לפרטים', en: 'Click a region on the map for details' },
        no_coords_note:        { he: '{n} קלפיות ללא קואורדינטות (לא נכללו באזורים)', en: '{n} stations without coordinates (excluded from regions)' },
        regional_seats_label:  { he: 'מנדטים אזוריים:', en: 'Regional seats:' },
        district_method_label: { he: 'שיטת חלוקה:', en: 'District method:' },
        method_dhondt:         { he: 'באדר-עופר', en: "d'Hondt" },
        method_fptp:           { he: 'זוכה-לוקח-הכל', en: 'Winner takes all' },
        explainer_link:        { he: 'הסבר מונפש →', en: 'Animated explainer →' },

        /* ── Mobile per-page info texts ── */
        about_this_view:       { he: 'על תצוגה זו', en: 'About this view' },
        sankey_info:           { he: 'תרשים הנדידה מציג את זרימת הקולות בין שתי בחירות עוקבות לכנסת. הרוחב של כל קשר מייצג את מספר הקולות שעברו ממפלגה אחת לאחרת. החישוב מבוסס על רגרסיה של אלפי קלפיות עם אילוצי אי-שליליות וסטוכסטיות.', en: 'The migration diagram shows vote flow between two consecutive Knesset elections. Each link\'s width represents the number of votes that transferred between parties. The calculation is based on regression across thousands of ballot boxes with non-negativity and stochasticity constraints.' },
        tsne_info:             { he: 'מפת הפיזור מציגה את כל הקלפיות כנקודות דו-מימדיות באמצעות אלגוריתם T-SNE. קלפיות עם דפוסי הצבעה דומים ממוקמות קרוב זו לזו. גודל הנקודה משקף את מספר המצביעים, והצבע מציג שיעור הצבעה, תמיכה במפלגה, או אשכול חברתי-כלכלי.', en: 'The distribution map displays all ballot boxes as 2D points using the T-SNE algorithm. Boxes with similar voting patterns are placed close together. Dot size reflects voter count, and color shows turnout, party support, or socioeconomic cluster.' },
        geomap_info:           { he: 'המפה הגיאוגרפית מציגה את מיקומן הפיזי של כל הקלפיות על פני מפת ישראל. ניתן לצבוע לפי מפלגה מנצחת, אחוז הצבעה, מפלגה ספציפית או אשכול חברתי-כלכלי. לחצו על קלפי או אשכול לפרטים.', en: 'The geographic map shows the physical location of all ballot boxes across Israel. Color by winning party, turnout, specific party support, or socioeconomic cluster. Click a station or cluster for details.' },
        scatter_info:          { he: 'גרף ההשוואה מציג כל קלפי כנקודה לפי אחוזי תמיכה בשתי מפלגות. ציר X מציג מפלגה אחת וציר Y מפלגה אחרת. ניתן להשוות מפלגות מאותן בחירות או מבחירות שונות, ולסנן לפי יישוב.', en: 'The comparison chart plots each ballot box by support percentage for two parties. The X axis shows one party and the Y axis another. Compare parties from the same or different elections, and filter by settlement.' },
        dhondt_info:           { he: 'מחשבון באדר-עופר מדמה את חלוקת 120 מנדטי הכנסת. ניתן לערוך את מספרי הקולות, לשנות את אחוז החסימה ולהוסיף הסכמי עודפים. בכל סיבוב, קולות כל מפלגה מחולקים במנדטים שקיבלה + 1, והמפלגה עם המנה הגבוהה ביותר מקבלת מנדט.', en: 'The D\'Hondt calculator simulates the allocation of the Knesset\'s 120 seats. Edit vote counts, change the electoral threshold, and add surplus agreements. In each round, each party\'s votes are divided by seats received + 1, and the highest quotient wins the next seat.' },
        regional_info:         { he: 'סימולטור הבחירות האזוריות מחלק את הארץ למחוזות בחירה ומקצה מנדטים בכל מחוז בנפרד. ניתן לבחור מספר מחוזות, שיטת חלוקה (באדר-עופר או זוכה-לוקח-הכל), ולשלב מנדטים ארציים. הסימולציה חושפת כיצד שינוי שיטת הבחירות משפיע על הרכב הכנסת.', en: 'The regional elections simulator divides the country into electoral districts and allocates seats per district separately. Choose the number of districts, allocation method (D\'Hondt or winner-takes-all), and mix national seats. The simulation reveals how changing the electoral system affects Knesset composition.' },
        regional_methodology_text: { he: 'הסימולטור מחלק את כלל הקלפיות בעלות קואורדינטות גיאוגרפיות למחוזות בחירה באמצעות חלוקה בינארית חוזרת: בכל שלב, המחוז בעל מספר הבוחרים הגדול ביותר נחצה לשניים לאורך הציר שמייצר את החלוקה המרובעת ביותר, כך שמספר הבוחרים מתחלק שווה בשווה. התוצאה היא מחוזות רציפים גיאוגרפית ומאוזנים באוכלוסייה. המנדטים מחולקים למחוזות לפי מכסת הייר (<bdi><a href="https://en.wikipedia.org/wiki/Hare_quota" target="_blank" style="color:var(--accent-primary)">Hare quota</a></bdi>) עם שארית גדולה ביותר. בכל מחוז מוקצים מנדטים לפי שיטת באדר-עופר או לפי זוכה-לוקח-הכל (<bdi>FPTP</bdi>), בהתאם לבחירת המשתמש. במצב מעורב, חלק מהמנדטים מוקצים ארצית (עם אחוז חסימה) והשאר אזורית. ככל שמספר המחוזות עולה ומספר המנדטים לכל מחוז יורד, מפלגות גדולות מרוויחות על חשבון מפלגות קטנות — עד למקרה הקיצוני של מחוזות עם מנדט אחד כל אחד, שהוא למעשה שיטת <bdi>FPTP</bdi> מלאה.', en: 'The simulator partitions all ballot stations with geographic coordinates into electoral districts using recursive binary splitting: at each step, the district with the most eligible voters is split in two along whichever axis produces squarer children, balancing the voter population evenly. This produces geographically contiguous, population-balanced districts. Seats are apportioned to districts using the <a href="https://en.wikipedia.org/wiki/Hare_quota" target="_blank" style="color:var(--accent-primary)">Hare quota</a> with largest remainder. Within each district, seats are allocated using D\'Hondt or winner-takes-all (FPTP), depending on user selection. In mixed mode, some seats are allocated nationally (with an electoral threshold) and the rest regionally. As the number of districts increases and seats per district decreases, large parties gain at the expense of smaller ones — reaching the extreme case of single-seat districts, which is effectively a full FPTP system.' },
        feedback_question:     { he: 'רעיונות? מחשבות? הצעות? דונו כאן', en: 'Ideas? Thoughts? Suggestions? Discuss them here' },
        nav_discussions:       { he: 'דיונים', en: 'Discussions' },
        discussions_title:     { he: 'דיונים', en: 'Discussions' },
        discussions_subtitle:  { he: 'שאלות, רעיונות ודיונים על האתר ועל בחירות', en: 'Questions, ideas and discussions about the site and elections' },
        forum_feedback:        { he: 'משוב על האתר', en: 'Site Feedback' },
        forum_features:        { he: 'הצעות לפיצ\'רים', en: 'Feature Ideas' },
        forum_elections:       { he: 'תאוריית בחירות', en: 'Elections Theory' },
        forum_data:            { he: 'נתונים ומתודולוגיה', en: 'Data & Methodology' },
        forum_general:         { he: 'שיחה חופשית', en: 'General' },

        /* ── Rankings page ── */
        nav_rankings:          { he: 'דירוגים', en: 'Rankings' },
        tab_rankings:          { he: 'דירוגים', en: 'Rankings' },
        rankings_subtitle:     { he: 'דירוגי תנודתיות יישובים וריכוז גיאוגרפי', en: 'Settlement Volatility & Geographic Concentration Rankings' },
        card_rankings_desc:    { he: 'דירוג יישובים לפי תנודתיות הצבעה ומפלגות לפי ריכוז גיאוגרפי', en: 'Rank settlements by voting volatility and parties by geographic concentration' },
        volatility_rankings_title: { he: 'תנודתיות יישובים (מדד פדרסן)', en: 'Settlement Volatility (Pedersen Index)' },
        party_concentration_title: { he: 'ריכוז גיאוגרפי של מפלגות', en: 'Party Geographic Concentration' },
        pedersen_explanation:  { he: '<strong>מדד פדרסן (Pedersen Index)</strong> — פותח על ידי מורנס פדרסן (<bdi><a href="https://en.wikipedia.org/wiki/Pedersen_index" target="_blank" style="color:var(--accent-primary)">Mogens Pedersen</a>, 1979</bdi>) — מודד את סך השינוי בתמיכה המפלגתית בין שתי בחירות עוקבות.<br><br><strong>נוסחה:</strong><br><span class="katex-display-wrapper">\\[PI = \\frac{1}{2}\\sum_{i=1}^{N}\\left|\\, p_{i,t} - p_{i,\\,t-1}\\right|\\]</span>כאשר \\(p_{i,t}\\) הוא אחוז התמיכה במפלגה \\(i\\) בבחירות \\(t\\), ו-\\(N\\) מספר המפלגות. ערך של 0% מציין שום שינוי, ו-100% מציין שינוי מוחלט. הממוצע המוצג הוא על פני ארבעה מעברי בחירות (21→22, 22→23, 23→24, 24→25).<br><br><strong>מיזוג משפחות מפלגתיות:</strong> מפלגות שפוצלו או מוזגו בין בחירות מחושבות כמשפחה אחת, כדי למדוד שינוי אמיתי בהעדפות הבוחרים:<br>• <strong>21→22:</strong> הליכוד+כולנו; חד״ש-תע״ל+רע״ם-בל״ד↔הרשימה המשותפת; הבית היהודי+הימין החדש↔ימינה<br>• <strong>22→23:</strong> העבודה-גשר+המחנה הדמוקרטי↔עבודה-גשר-מרצ<br>• <strong>23→24:</strong> כחול לבן↔יש עתיד+תקווה חדשה; עבודה-גשר-מרצ↔העבודה+מרצ; הרשימה המשותפת↔רע״ם; ימינה↔הציונות הדתית<br>• <strong>24→25:</strong> כחול לבן+תקווה חדשה↔המחנה הממלכתי; ימינה↔הציונות הדתית; הרשימה המשותפת↔חד״ש-תע״ל+בל״ד<br><br>🟢 <strong>ירוק (מתחת ל-10%)</strong>: יציבות גבוהה — הצבעה עקבית<br>🟡 <strong>צהוב (10%-25%)</strong>: תנודתיות בינונית<br>🔴 <strong>אדום (מעל 25%)</strong>: תנודתיות גבוהה — שינויים משמעותיים בדפוסי ההצבעה', en: '<strong>The Pedersen Index</strong> — developed by <a href="https://en.wikipedia.org/wiki/Pedersen_index" target="_blank" style="color:var(--accent-primary)">Mogens Pedersen</a> (1979) — measures the total change in party support between two consecutive elections.<br><br><strong>Formula:</strong><br><span class="katex-display-wrapper">\\[PI = \\frac{1}{2}\\sum_{i=1}^{N}\\left|\\, p_{i,t} - p_{i,\\,t-1}\\right|\\]</span>where \\(p_{i,t}\\) is party \\(i\\)\'s vote share in election \\(t\\), and \\(N\\) is the number of parties. A value of 0% means no change, and 100% means complete change. The displayed average is across four election transitions (21→22, 22→23, 23→24, 24→25).<br><br><strong>Party family merging:</strong> Parties that split or merged between elections are computed as one family, to measure actual voter preference shifts:<br>• <strong>21→22:</strong> Likud+Kulanu; Hadash-Taal+Ra\'am-Balad↔Joint List; Jewish Home+New Right↔Yamina<br>• <strong>22→23:</strong> Labor-Gesher+Democratic Camp↔Labor-Gesher-Meretz<br>• <strong>23→24:</strong> Blue&amp;White↔Yesh Atid+New Hope; Labor-Gesher-Meretz↔Labor+Meretz; Joint List↔Ra\'am; Yamina↔Religious Zionism<br>• <strong>24→25:</strong> Blue&amp;White+New Hope↔National Unity; Yamina↔Religious Zionism; Joint List↔Hadash-Taal+Balad<br><br>🟢 <strong>Green (below 10%)</strong>: High stability — consistent voting<br>🟡 <strong>Yellow (10%-25%)</strong>: Moderate volatility<br>🔴 <strong>Red (above 25%)</strong>: High volatility — significant shifts in voting patterns' },
        hhi_explanation:       { he: '<strong>מדד הרפינדל-הירשמן (Herfindahl-Hirschman Index, HHI)</strong> — פותח על ידי אורריס הרפינדל (<bdi><a href="https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index" target="_blank" style="color:var(--accent-primary)">Orris Herfindahl</a></bdi>) ואלברט הירשמן (<bdi>Albert Hirschman</bdi>) — מודד עד כמה הקולות של מפלגה מרוכזים ביישובים מעטים.<br><br><strong>נוסחה:</strong> המדד מחושב <strong>עבור כל מפלגה בנפרד</strong>. לכל מפלגה \\(P\\), מחלקים את קולותיה ביישוב \\(i\\) בסך כל קולותיה בכל היישובים:<br><span class="katex-display-wrapper">\\[s_i = \\frac{v_{P,i}}{\\displaystyle\\sum_{j=1}^{N} v_{P,j}}\\]</span>כאשר \\(v_{P,i}\\) הוא מספר הקולות של מפלגה \\(P\\) ביישוב \\(i\\), ו-\\(N\\) מספר היישובים. כלומר \\(s_i\\) הוא החלק <em>היחסי</em> של היישוב מתוך סך כל הקולות של אותה מפלגה. לאחר מכן:<br><span class="katex-display-wrapper">\\[HHI_P = \\sum_{i=1}^{N} s_i^2\\]</span>הערך נע בין \\(\\frac{1}{N}\\) (פיזור מושלם — שווה בכל היישובים) ל-\\(1\\) (כל הקולות ביישוב אחד).<br><br><strong>יישובים אפקטיביים:</strong><br><span class="katex-display-wrapper">\\[N_{\\text{eff}} = \\frac{1}{HHI_P}\\]</span>כמה יישובים עם חלוקה שווה היו נותנים את אותו ריכוז. הערכים הם ממוצע על פני כל הבחירות שבהן המפלגה (או המשפחה הפוליטית שלה) התמודדה.<br><br>לדוגמה: ליהדות התורה 8 יישובים אפקטיביים — הקולות מרוכזים כאילו באו מ-8 ערים בלבד. לליכוד 48 — הקולות מפוזרים הרבה יותר.<br><br><strong>יישובים ל-50%/75%/90%/98%</strong>: כמה מהיישובים הגדולים ביותר של המפלגה נדרשים כדי להגיע לאחוז מסוים מסך הקולות שלה.', en: '<strong>The Herfindahl-Hirschman Index (HHI)</strong> — developed by <a href="https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index" target="_blank" style="color:var(--accent-primary)">Orris Herfindahl</a> and Albert Hirschman — measures how concentrated a party\'s votes are across settlements.<br><br><strong>Formula:</strong> The index is computed <strong>separately for each party</strong>. For each party \\(P\\), divide its votes in settlement \\(i\\) by its total votes across all settlements:<br><span class="katex-display-wrapper">\\[s_i = \\frac{v_{P,i}}{\\displaystyle\\sum_{j=1}^{N} v_{P,j}}\\]</span>where \\(v_{P,i}\\) is party \\(P\\)\'s votes in settlement \\(i\\), and \\(N\\) is the number of settlements. In other words, \\(s_i\\) is the <em>relative</em> share of settlement \\(i\\) within that party\'s own total. Then:<br><span class="katex-display-wrapper">\\[HHI_P = \\sum_{i=1}^{N} s_i^2\\]</span>Values range from \\(\\frac{1}{N}\\) (perfect dispersion — equal in all settlements) to \\(1\\) (all votes in one settlement).<br><br><strong>Effective settlements:</strong><br><span class="katex-display-wrapper">\\[N_{\\text{eff}} = \\frac{1}{HHI_P}\\]</span>How many settlements with equal shares would produce the same concentration. Values are averaged across all elections in which the party (or its political family) ran.<br><br>Example: UTJ has 8 effective settlements — meaning its votes are concentrated as if coming from just 8 cities. In contrast, Likud has 48 — much more broadly distributed.<br><br><strong>Settlements for 50%/75%/90%/98%</strong>: how many of the party\'s largest settlements are needed to reach a given percentage of its total votes.' },
        size_filter_label:     { he: 'סינון לפי גודל:', en: 'Filter by size:' },
        size_all:              { he: 'הכל', en: 'All' },
        size_small:            { he: 'קטן <1,000', en: 'Small <1,000' },
        size_medium:           { he: 'בינוני 1,000-10,000', en: 'Medium 1,000-10,000' },
        size_large:            { he: 'גדול 10,000+', en: 'Large 10,000+' },
        showing_count:         { he: 'מציג {x} מתוך {y} יישובים', en: 'Showing {x} of {y} settlements' },
        tab_settlements:       { he: 'יישובים', en: 'Settlements' },
        tab_parties:           { he: 'מפלגות', en: 'Parties' },
        rank_col:              { he: '#', en: '#' },
        avg_volatility:        { he: 'ממוצע', en: 'Average' },
        median_label:          { he: 'חציון', en: 'Median' },
        mean_label:            { he: 'ממוצע', en: 'Mean' },
        total_settlements_label: { he: 'סה״כ יישובים', en: 'Total settlements' },
        settlements_for_75:    { he: 'יישובים ל-75% קולות', en: 'Settlements for 75% of votes' },
        settlements_for_98:    { he: 'יישובים ל-98% קולות', en: 'Settlements for 98% of votes' },
        see_all_rankings:      { he: 'כל הדירוגים →', en: 'All rankings →' },

        /* ── UMAP note ── */
        umap_note:             { he: '<strong>למה <bdi><a href="https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding" target="_blank" style="color:var(--accent-primary)">T-SNE</a></bdi> ולא <bdi><a href="https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction#Uniform_manifold_approximation_and_projection" target="_blank" style="color:var(--accent-primary)">UMAP</a></bdi>?</strong> <bdi>UMAP (Uniform Manifold Approximation and Projection)</bdi> היא אלטרנטיבה פופולרית ל-<bdi>T-SNE</bdi> שמהירה יותר ומשמרת טוב יותר מבנים גלובליים. בחרנו ב-<bdi>T-SNE</bdi> כי הוא מייצר הפרדה ויזואלית טובה יותר בין אשכולות דמוגרפיים — שזה בדיוק מה שחשוב בהדמיה של דפוסי הצבעה. המרחקים בין האשכולות ב-<bdi>T-SNE</bdi> אינם משמעותיים, אבל ההפרדה הברורה בין קבוצות מפצה על כך.', en: '<strong>Why <a href="https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding" target="_blank" style="color:var(--accent-primary)">T-SNE</a> and not <a href="https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction#Uniform_manifold_approximation_and_projection" target="_blank" style="color:var(--accent-primary)">UMAP</a>?</strong> UMAP (Uniform Manifold Approximation and Projection) is a popular alternative to T-SNE that is faster and better preserves global structure. We chose T-SNE because it produces better visual separation between demographic clusters — which is exactly what matters for visualizing voting patterns. The distances between T-SNE clusters are not meaningful, but the clear separation between groups makes up for this.' },
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
        'בנט 26': 'Bennett-26',
        'ביחד': 'Together (Beyachad)',
        'הדמוקרטים': 'The Democrats',
        'עוצמה יהודית': 'Jewish Power',
        'ישר': 'Yashar',
    };

    /* ── State ── */
    // Determine language immediately (before DOMContentLoaded) so page scripts can read it
    const _urlParams = new URLSearchParams(window.location.search);
    const _urlLang = _urlParams.get('lang');
    const _storedLang = localStorage.getItem('lang');
    let currentLang = (_urlLang === 'en' || _urlLang === 'he') ? _urlLang
        : (_storedLang === 'en' || _storedLang === 'he') ? _storedLang
        : 'he';

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
        if (currentLang === 'en') {
            if (electionObj.name_en) return electionObj.name_en;
            // Derive English from Hebrew: "הכנסת ה-24" → "Knesset 24"
            const m = (electionObj.name || '').match(/(\d+)/);
            if (m) return `Knesset ${m[1]}`;
        }
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

    /** Check if a settlement (by Hebrew name) matches a search query.
     *  In English mode, searches English transliteration (case-insensitive) + Hebrew fallback.
     *  In Hebrew mode, searches Hebrew name. */
    function settlementMatches(hebrewName, query) {
        if (!hebrewName || !query) return false;
        if (currentLang === 'he') return hebrewName.includes(query);
        const enName = settlementName(hebrewName);
        return enName.toLowerCase().includes(query.toLowerCase()) || hebrewName.includes(query);
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

        // Update giscus language if embedded
        const giscusFrame = document.querySelector('iframe.giscus-frame');
        if (giscusFrame) {
            giscusFrame.contentWindow.postMessage(
                { giscus: { setConfig: { lang: isHe ? 'he' : 'en' } } },
                'https://giscus.app'
            );
        }

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

    /** Render shared navigation into .view-switcher element. */
    const navViews = [
        { id: 'home',      href: 'index.html',     i18n: 'nav_home',      text: 'ראשי' },
        { id: 'geomap',    href: 'geomap.html',    i18n: 'nav_geomap',   text: 'מפה גיאוגרפית' },
        { id: 'tsne',      href: 'tsne.html',      i18n: 'nav_tsne',     text: 'התפלגות קלפיות' },
        { id: 'sankey',    href: 'sankey.html',     i18n: 'nav_sankey',    text: 'נדידת קולות' },
        { id: 'scatter',   href: 'scatter.html',   i18n: 'nav_scatter',  text: 'השוואת מפלגות' },
        { id: 'dhondt',    href: 'dhondt.html',    i18n: 'nav_dhondt',   text: 'מחשבון באדר-עופר' },
        { id: 'regional',  href: 'regional.html',  i18n: 'nav_regional', text: 'בחירות אזוריות' },
        { id: 'irregular', href: 'irregular.html',  i18n: 'nav_irregular', text: 'קלפיות חריגות' },
    ];

    function renderNav(activeId) {
        const nav = document.querySelector('.view-switcher');
        if (!nav) return;

        // Preserve export button if present
        const exportBtn = nav.querySelector('.header-export');

        // Propagate e26 flag across nav links
        function addE26(href) {
            if (!SHOW_E26) return href;
            return href + (href.includes('?') ? '&' : '?') + 'e26=1';
        }

        function viewLink(v) {
            const cls = 'view-btn' + (v.cls ? ' ' + v.cls : '');
            if (v.id === activeId) {
                return '<span class="' + cls + ' active" data-i18n="' + v.i18n + '">' + v.text + '</span>';
            }
            return '<a href="' + addE26(v.href) + '" class="' + cls + '" data-i18n="' + v.i18n + '">' + v.text + '</a>';
        }

        const extraLinks = [
            { id: 'settlement', href: 'settlement.html', i18n: 'settlement_profile', text: 'פרופיל יישוב' },
            { id: 'party',      href: 'party.html',      i18n: 'party_profile',      text: 'פרופיל מפלגה' },
            { id: 'rankings',   href: 'rankings.html',   i18n: 'nav_rankings',       text: 'דירוגים' },
            { id: 'discussions', href: 'discussions.html', i18n: 'nav_discussions',    text: 'דיונים' },
        ];

        // Main views row
        nav.innerHTML = navViews.map(viewLink).join('\n');

        // Extras row (below main views)
        let extrasRow = nav.parentElement.querySelector('.nav-extras');
        if (!extrasRow) {
            extrasRow = document.createElement('div');
            extrasRow.className = 'nav-extras';
            nav.parentElement.appendChild(extrasRow);
        }
        extrasRow.innerHTML = extraLinks.map(viewLink).join('\n');
        if (exportBtn) extrasRow.appendChild(exportBtn);
        injectLangToggle('.nav-extras');
        applyTranslations();
    }

    /** Floating mobile BMC banner — shows once per session after 3s delay. */
    function renderMobileBMC() {
        if (sessionStorage.getItem('bmc_dismissed')) return;
        setTimeout(() => {
            if (sessionStorage.getItem('bmc_dismissed')) return;
            const bar = document.createElement('div');
            bar.className = 'bmc-float';
            bar.innerHTML =
                '<img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" alt="">' +
                '<a href="https://www.buymeacoffee.com/harelc" target="_blank" class="bmc-float-text" style="color:inherit;text-decoration:none;line-height:1.3;">' +
                    '<span style="display:block;font-size:0.7rem;font-weight:400;">' + t('bmc_line1') + '</span>' +
                    '<span style="display:block;font-size:0.75rem;font-weight:600;">' + t('bmc_line2') + '</span>' +
                '</a>' +
                '<button class="bmc-float-close" aria-label="Close">\u2715</button>';
            bar.querySelector('.bmc-float-close').addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                sessionStorage.setItem('bmc_dismissed', '1');
                bar.remove();
            });
            document.body.appendChild(bar);
        }, 3000);
    }

    /** Inject the Buy Me a Coffee button. */
    function renderBMC() {
        if (document.querySelector('.bmc-button')) return;
        if (sessionStorage.getItem('bmc_dismissed')) return;
        const wrap = document.createElement('div');
        wrap.className = 'bmc-button';
        const a = document.createElement('a');
        a.href = 'https://www.buymeacoffee.com/harelc';
        a.target = '_blank';
        a.className = 'bmc-link';
        a.setAttribute('data-i18n-title', 'bmc_title');
        a.title = t('bmc_title');
        a.innerHTML = '<img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" alt="Buy me a coffee">' +
            '<span data-i18n="bmc_text">' + t('bmc_text') + '</span>';
        wrap.appendChild(a);
        const close = document.createElement('button');
        close.className = 'bmc-close';
        close.innerHTML = '\u2715';
        close.title = 'Dismiss';
        close.onclick = function(e) {
            e.stopPropagation();
            wrap.remove();
            sessionStorage.setItem('bmc_dismissed', '1');
        };
        wrap.appendChild(close);
        document.body.appendChild(wrap);
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
        settlementMatches,
        fmtNum,
        getLang,
        isRTL,
        setLang,
        applyTranslations,
        injectLangToggle,
        renderNav,
        renderBMC,
        renderMobileBMC,
        dict,
        partyNameMap,
        SHOW_E26,
    };
})();
