/**
 * Deep links: reproduce a page's configuration from its URL.
 *
 * Usage per page:
 *   const e = DL.get('e');                       // read (validated by caller)
 *   DL.sync({ e: cur, mode: mode }, { e: '25' }); // live-update address bar
 *   DL.addCopyButton();                           // 📤 share button next to 📷 export
 *   DL.qrDataURL(DL.url())                        // QR of current view for PNGs
 *
 * sync() deletes params that equal their default, preserves unrelated
 * params (lang, e26, …), and debounces replaceState so slider drags and
 * rapid pill clicks don't thrash history.
 */
(function () {
    const params = new URLSearchParams(location.search);
    let timer = null;

    function get(k) { return params.get(k); }

    function build(state, defaults) {
        const u = new URL(location.href);
        u.hash = '';
        for (const [k, v] of Object.entries(state || {})) {
            const dflt = defaults && defaults[k];
            if (v == null || v === '' || (dflt !== undefined && String(v) === String(dflt))) {
                u.searchParams.delete(k);
            } else {
                u.searchParams.set(k, String(v));
            }
        }
        return u;
    }

    function sync(state, defaults) {
        clearTimeout(timer);
        timer = setTimeout(() => {
            try { history.replaceState(null, '', build(state, defaults)); } catch (e) { /* file:// */ }
        }, 120);
    }

    /** Canonical shareable URL for the current (or given) state. */
    function url(state, defaults) {
        const u = state ? build(state, defaults) : new URL(location.href);
        u.hash = '';
        u.searchParams.delete('desktop'); // device bypass must not leak into shared links
        // QR codes / copied links should point at the live site, not localhost.
        if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
            return 'https://kolot-nodedim.netlify.app' + u.pathname.replace(/^\/site\//, '/') + u.search;
        }
        return u.toString();
    }

    /** QR PNG data-URL for text via bundled qrcode.min.js; null if too long/unavailable. */
    function qrDataURL(text, cellSize) {
        if (typeof qrcode === 'undefined') return null;
        try {
            const qr = qrcode(0, 'M');
            qr.addData(text);
            qr.make();
            const n = qr.getModuleCount(), cell = cellSize || 4, quiet = 2;
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = (n + quiet * 2) * cell;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#000000';
            for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
                if (qr.isDark(r, c)) ctx.fillRect((c + quiet) * cell, (r + quiet) * cell, cell, cell);
            }
            return canvas.toDataURL('image/png');
        } catch (e) { return null; }
    }

    function isEn() {
        return (typeof i18n !== 'undefined' && i18n.getLang) ? i18n.getLang() === 'en' : false;
    }

    function addCopyButton(anchorSelector) {
        const anchor = anchorSelector
            ? document.querySelector(anchorSelector)
            : (document.querySelector('#export-png') || document.querySelector('#export-png-btn') || document.querySelector('.header-export'));
        if (!anchor || document.getElementById('copy-link-btn')) return null;
        const btn = document.createElement('button');
        btn.id = 'copy-link-btn';
        btn.type = 'button';
        const inTopBar = anchor.classList && anchor.classList.contains('top-bar');
        btn.className = inTopBar ? 'info-toggle' : ((anchor.tagName === 'BUTTON' && anchor.className) || 'export-btn header-export');
        const label = () => { btn.textContent = inTopBar ? '📤' : (isEn() ? '📤 Share' : '📤 שתפו'); };
        label();
        btn.title = isEn() ? 'Share a link that reproduces this exact view' : 'שיתוף קישור שמשחזר את המבט הזה בדיוק';
        window.addEventListener('langchange', label);
        btn.addEventListener('click', async () => {
            const link = url();
            // Native share sheet where available (mobile, some desktops)…
            if (navigator.share) {
                try {
                    await navigator.share({ title: document.title, url: link });
                    return;
                } catch (e) {
                    if (e && e.name === 'AbortError') return; // user dismissed the sheet
                    // any other failure falls through to copy
                }
            }
            // …otherwise copy the deep link to the clipboard.
            let ok = false;
            try { await navigator.clipboard.writeText(link); ok = true; }
            catch (e) {
                const ta = document.createElement('textarea');
                ta.value = link; ta.style.position = 'fixed'; ta.style.opacity = '0';
                document.body.appendChild(ta); ta.select();
                try { ok = document.execCommand('copy'); } catch (e2) { /* ignore */ }
                ta.remove();
                if (!ok) window.prompt(isEn() ? 'Copy this link:' : 'העתיקו את הקישור:', link);
            }
            if (ok) {
                btn.textContent = inTopBar ? '✓' : (isEn() ? '✓ Link copied' : '✓ הקישור הועתק');
                setTimeout(label, 1600);
            }
        });
        if (inTopBar) anchor.insertBefore(btn, anchor.querySelector('.info-toggle, .lang-toggle'));
        else anchor.parentNode.insertBefore(btn, anchor);
        return btn;
    }

    window.DL = { get, params, sync, url, qrDataURL, addCopyButton, addShareButton: addCopyButton };
})();
