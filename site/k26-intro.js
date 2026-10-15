/* First-visit K26 welcome. Loaded by i18n.js once per browser. */
(function () {
    'use strict';

    var KEY = 'k26_intro_v1';
    var POLLS_CLOSE = new Date('2026-10-27T22:00:00+02:00').getTime();
    var kind = 'simulated';
    var prevOverflow = '';
    var timer = null;

    var UNITS = [
        { ms: 86400000, one: 'k26_intro_day', many: 'k26_intro_days' },
        { ms: 3600000, one: 'k26_intro_hour', many: 'k26_intro_hours' },
        { ms: 60000, one: 'k26_intro_minute', many: 'k26_intro_minutes' },
        { ms: 1000, one: 'k26_intro_second', many: 'k26_intro_seconds' }
    ];

    function t(key) {
        return window.i18n.t(key);
    }

    function countdownHtml() {
        if (kind === 'partial' || Date.now() >= POLLS_CLOSE) return '';
        var cells = UNITS.map(function (u, i) {
            return '<div class="k26i-unit" data-unit="' + i + '">' +
                '<span class="k26i-num"></span>' +
                '<span class="k26i-unit-name"></span>' +
                '</div>';
        }).join('');
        return '<div class="k26i-countdown" role="timer" aria-live="off">' +
            '<div class="k26i-units">' + cells + '</div>' +
            '<div class="k26i-countdown-label">' + t('k26_intro_countdown_label') + '</div>' +
            '</div>';
    }

    function tick() {
        var overlay = document.getElementById('k26-intro');
        if (!overlay) return;
        var left = POLLS_CLOSE - Date.now();
        var box = overlay.querySelector('.k26i-countdown');
        if (!box) return;
        if (left <= 0) {
            box.remove();
            return;
        }
        UNITS.forEach(function (u, i) {
            var value = Math.floor(left / u.ms);
            left -= value * u.ms;
            var cell = box.querySelector('[data-unit="' + i + '"]');
            cell.querySelector('.k26i-num').textContent = i === 0 ? String(value) : String(value).padStart(2, '0');
            cell.querySelector('.k26i-unit-name').textContent = t(value === 1 ? u.one : u.many);
        });
    }

    function stepClass(index) {
        var active = kind === 'partial' ? 1 : 0;
        if (index < active) return 'is-done';
        if (index === active) return 'is-now';
        return 'is-next';
    }

    function panelHtml() {
        var partial = kind === 'partial';
        var steps = [
            ['k26_intro_now', 'k26_intro_now_d'],
            ['k26_intro_night', 'k26_intro_night_d'],
            ['k26_intro_done', 'k26_intro_done_d']
        ].map(function (pair, i) {
            return '<li class="' + stepClass(i) + '">' +
                '<span class="k26i-step-name">' + t(pair[0]) + '</span>' +
                '<span class="k26i-step-text">' + t(pair[1]) + '</span>' +
                '</li>';
        }).join('');
        var ready = ['k26_intro_ready_1', 'k26_intro_ready_2', 'k26_intro_ready_3'].map(function (key) {
            return '<li>' + t(key) + '</li>';
        }).join('');
        return '<div class="k26i-panel">' +
            '<button type="button" class="k26i-x" aria-label="' + t('k26_intro_close') + '">×</button>' +
            '<div class="k26i-scroll">' +
            '<h2 id="k26-intro-title">' + t(partial ? 'k26_intro_title_partial' : 'k26_intro_title') + '</h2>' +
            countdownHtml() +
            '<p class="k26i-lead">' + t(partial ? 'k26_intro_lead_partial' : 'k26_intro_lead') + '</p>' +
            '<ol class="k26i-steps">' + steps + '</ol>' +
            '<h3 class="k26i-ready-title">' + t('k26_intro_ready_title') + '</h3>' +
            '<ul class="k26i-ready">' + ready + '</ul>' +
            '</div>' +
            '<div class="k26i-actions">' +
                '<button type="button" class="k26i-dismiss">' + t('k26_intro_got_it') + '</button>' +
            '</div>' +
            '</div>';
    }

    function ensureStyle() {
        if (document.getElementById('k26-intro-style')) return;
        var style = document.createElement('style');
        style.id = 'k26-intro-style';
        style.textContent = [
            '#k26-intro{position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;',
            'padding:16px;background:rgba(10,12,16,0.72);}',
            '@media (prefers-reduced-motion: no-preference){',
            '#k26-intro{animation:k26iFade .18s ease-out;}',
            '#k26-intro .k26i-panel{animation:k26iRise .22s ease-out;}}',
            '@keyframes k26iFade{from{opacity:0}to{opacity:1}}',
            '@keyframes k26iRise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}',
            '#k26-intro .k26i-panel{position:relative;width:min(600px,100%);max-height:min(92vh,820px);',
            'display:flex;flex-direction:column;overflow:hidden;',
            'background:#1e212a;color:#f3f5f8;border:1px solid #3a4050;border-top:3px solid #f0b429;',
            'border-radius:2px;padding:1.35rem 1.35rem 0.95rem;text-align:start;',
            'font-family:Heebo,Inter,sans-serif;box-shadow:0 18px 50px rgba(0,0,0,.45);}',
            '#k26-intro .k26i-panel:focus{outline:none;}',
            '#k26-intro .k26i-scroll{overflow:auto;min-height:0;}',
            '#k26-intro .k26i-x{position:absolute;top:8px;inset-inline-end:8px;width:32px;height:32px;',
            'border:0;background:transparent;color:#939aab;font-size:1.35rem;line-height:1;cursor:pointer;font-family:inherit;}',
            '#k26-intro .k26i-x:hover{color:#f3f5f8;}',
            '#k26-intro h2{font-size:1.55rem;font-weight:700;line-height:1.25;margin:0 0 0.9rem;margin-inline-end:2rem;letter-spacing:0;}',
            '#k26-intro .k26i-countdown{margin:0 0 1.1rem;padding:0.9rem 0 0.8rem;border-top:1px solid #3a4050;border-bottom:1px solid #3a4050;}',
            '#k26-intro .k26i-units{display:flex;justify-content:space-between;gap:0.5rem;}',
            '#k26-intro .k26i-unit{flex:1;display:flex;flex-direction:column;align-items:center;min-width:0;}',
            '#k26-intro .k26i-num{font-size:3rem;font-weight:700;line-height:1;color:#f0b429;',
            'font-variant-numeric:tabular-nums;font-feature-settings:"tnum";}',
            '#k26-intro .k26i-unit-name{margin-top:0.3rem;font-size:0.82rem;color:#c8ceda;}',
            '#k26-intro .k26i-countdown-label{margin-top:0.7rem;text-align:center;font-size:0.85rem;color:#939aab;}',
            '#k26-intro .k26i-lead{margin:0 0 1.1rem;color:#c8ceda;font-size:0.97rem;line-height:1.6;}',
            '#k26-intro .k26i-steps{list-style:none;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));',
            'gap:0.75rem;margin:0 0 1.15rem;padding:0;}',
            '#k26-intro .k26i-steps li{min-width:0;padding-top:0.55rem;border-top:2px solid #3a4050;}',
            '#k26-intro .k26i-steps .is-now{border-top-color:#f0b429;}',
            '#k26-intro .k26i-steps .is-done{border-top-color:#6b7280;}',
            '#k26-intro .k26i-step-name{display:block;font-weight:600;font-size:0.92rem;margin-bottom:0.2rem;}',
            '#k26-intro .is-now .k26i-step-name{color:#f0b429;}',
            '#k26-intro .is-done .k26i-step-name{color:#939aab;}',
            '#k26-intro .k26i-step-text{display:block;color:#c8ceda;font-size:0.82rem;line-height:1.4;}',
            '#k26-intro .is-done .k26i-step-text{color:#939aab;}',
            '#k26-intro .k26i-ready-title{font-size:0.95rem;font-weight:600;margin:0 0 0.45rem;}',
            '#k26-intro .k26i-ready{list-style:none;margin:0;padding:0;}',
            '#k26-intro .k26i-ready li{position:relative;padding-inline-start:1.5rem;margin-bottom:0.4rem;',
            'font-size:0.88rem;line-height:1.45;color:#c8ceda;}',
            '#k26-intro .k26i-ready li::before{content:"✓";position:absolute;inset-inline-start:0;top:0;',
            'color:#10b981;font-weight:700;}',
            '#k26-intro .k26i-actions{display:flex;justify-content:flex-end;margin-top:0.9rem;}',
            '#k26-intro .k26i-dismiss{background:#f0b429;color:#1a1408;border:0;font:inherit;font-weight:600;',
            'font-size:0.95rem;padding:0.5rem 1.3rem;border-radius:2px;cursor:pointer;}',
            '#k26-intro .k26i-dismiss:hover{background:#f6d78a;}',
            '#k26-intro .k26i-dismiss:focus-visible,#k26-intro .k26i-x:focus-visible{outline:2px solid #f0b429;outline-offset:2px;}',
            '@media (max-width:560px){#k26-intro .k26i-steps{grid-template-columns:1fr;gap:0.55rem;}',
            '#k26-intro .k26i-num{font-size:2.2rem;}',
            '#k26-intro h2{font-size:1.3rem;}}'
        ].join('');
        document.head.appendChild(style);
    }

    function remember() {
        try { localStorage.setItem(KEY, '1'); } catch (e) {}
    }

    function close() {
        var overlay = document.getElementById('k26-intro');
        if (!overlay) return;
        overlay.remove();
        clearInterval(timer);
        document.body.style.overflow = prevOverflow;
        document.removeEventListener('keydown', onKey);
        remember();
    }

    function onKey(e) {
        if (e.key === 'Escape') {
            close();
            return;
        }
        if (e.key !== 'Tab') return;
        var overlay = document.getElementById('k26-intro');
        if (!overlay) return;
        var nodes = overlay.querySelectorAll('a, button');
        if (!nodes.length) return;
        var first = nodes[0];
        var last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    }

    function render(overlay) {
        overlay.innerHTML = panelHtml();
        overlay.querySelector('.k26i-x').addEventListener('click', close);
        overlay.querySelector('.k26i-dismiss').addEventListener('click', close);
        tick();
    }

    function open(nextKind) {
        if (document.getElementById('k26-intro')) return;
        kind = nextKind === 'partial' ? 'partial' : 'simulated';
        ensureStyle();
        var overlay = document.createElement('div');
        overlay.id = 'k26-intro';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'k26-intro-title');
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) close();
        });
        prevOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        document.body.appendChild(overlay);
        render(overlay);
        timer = setInterval(tick, 1000);
        document.addEventListener('keydown', onKey);
        var panel = overlay.querySelector('.k26i-panel');
        panel.setAttribute('tabindex', '-1');
        panel.focus();
    }

    window.addEventListener('langchange', function () {
        var overlay = document.getElementById('k26-intro');
        if (overlay) render(overlay);
    });
    window.K26Intro = { open: open };
})();
