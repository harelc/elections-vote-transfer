// Dismissable webinar invitation modal.
// Single source of truth — included from every desktop + mobile page.
// Auto-hides after the webinar date and remembers per-user dismissal.
(function () {
  'use strict';

  var STORAGE_KEY  = 'kn_webinar_modal_2026_05_27_dismissed';
  var WEBINAR_END  = new Date('2026-05-28T00:00:00');
  var REG_URL      = 'https://tinyurl.com/knesset-elections-data-webinar';
  var POSTER_PATH  = (location.pathname.indexOf('/m/') !== -1)
                       ? '../images/webinar_poster.jpg'
                       : 'images/webinar_poster.jpg';

  // 1. Skip if past webinar date.
  if (Date.now() > WEBINAR_END.getTime()) return;

  // 2. Skip if user has dismissed.
  try {
    if (localStorage.getItem(STORAGE_KEY) === '1') return;
  } catch (e) { /* private mode etc. — fall through and show */ }

  function init() {
    // Idempotency guard if script accidentally loaded twice.
    if (document.getElementById('kn-webinar-modal')) return;

    var style = document.createElement('style');
    style.textContent = [
      '#kn-webinar-modal{position:fixed;inset:0;background:rgba(15,23,42,0.78);',
      'backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);',
      'z-index:99999;display:flex;align-items:center;justify-content:center;',
      'padding:16px;animation:knFadeIn 0.25s ease-out;}',
      '@keyframes knFadeIn{from{opacity:0}to{opacity:1}}',
      '@keyframes knSlideIn{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}',
      '#kn-webinar-modal .kn-card{position:relative;background:#fff;border-radius:14px;',
      'max-width:680px;width:100%;max-height:92vh;overflow:auto;',
      'box-shadow:0 25px 60px rgba(0,0,0,0.45);',
      'animation:knSlideIn 0.3s ease-out;}',
      '#kn-webinar-modal .kn-close{position:absolute;top:8px;left:8px;',
      'width:34px;height:34px;border:none;background:rgba(255,255,255,0.9);',
      'color:#1a1c20;font-size:24px;line-height:1;border-radius:50%;cursor:pointer;',
      'display:flex;align-items:center;justify-content:center;font-weight:600;',
      'box-shadow:0 2px 8px rgba(0,0,0,0.2);transition:transform 0.15s,background 0.15s;}',
      '#kn-webinar-modal .kn-close:hover{transform:scale(1.08);background:#fff;}',
      '#kn-webinar-modal .kn-poster{display:block;width:100%;height:auto;border-radius:14px 14px 0 0;}',
      '#kn-webinar-modal .kn-actions{padding:18px 22px 22px;text-align:center;font-family:Heebo,Assistant,system-ui,sans-serif;}',
      '#kn-webinar-modal .kn-cta{display:inline-block;background:#1e40af;color:#fff;',
      'padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:1.05rem;',
      'box-shadow:0 4px 12px rgba(30,64,175,0.35);transition:transform 0.15s,box-shadow 0.15s;}',
      '#kn-webinar-modal .kn-cta:hover{transform:translateY(-1px);box-shadow:0 6px 16px rgba(30,64,175,0.5);background:#1e3a8a;}',
      '#kn-webinar-modal .kn-dismiss{display:block;margin-top:10px;color:#6b7280;font-size:0.85rem;',
      'background:none;border:none;cursor:pointer;text-decoration:underline;font-family:inherit;}',
      '#kn-webinar-modal .kn-dismiss:hover{color:#1a1c20;}',
      '@media (max-width:480px){#kn-webinar-modal .kn-card{max-width:96vw;}',
      '#kn-webinar-modal .kn-cta{padding:11px 24px;font-size:1rem;}}'
    ].join('');
    document.head.appendChild(style);

    var overlay = document.createElement('div');
    overlay.id = 'kn-webinar-modal';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'הזמנה לוובינר');
    overlay.innerHTML =
      '<div class="kn-card" dir="rtl">' +
        '<button class="kn-close" aria-label="סגור">×</button>' +
        '<a href="' + REG_URL + '" target="_blank" rel="noopener">' +
          '<img class="kn-poster" src="' + POSTER_PATH + '" alt="וובינר חינמי על ניתוח תוצאות הבחירות לכנסת">' +
        '</a>' +
        '<div class="kn-actions">' +
          '<a class="kn-cta" href="' + REG_URL + '" target="_blank" rel="noopener">להרשמה לוובינר ←</a>' +
          '<button class="kn-dismiss" type="button">אל תציגו שוב</button>' +
        '</div>' +
      '</div>';

    function dismiss(persist) {
      overlay.style.animation = 'knFadeIn 0.2s ease-in reverse';
      setTimeout(function () { overlay.remove(); }, 180);
      if (persist) {
        try { localStorage.setItem(STORAGE_KEY, '1'); } catch (e) { /* ignore */ }
      }
    }

    overlay.querySelector('.kn-close').addEventListener('click', function () { dismiss(true); });
    overlay.querySelector('.kn-dismiss').addEventListener('click', function () { dismiss(true); });
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) dismiss(false); // backdrop click — don't persist
    });
    document.addEventListener('keydown', function escHandler(e) {
      if (e.key === 'Escape' && document.body.contains(overlay)) {
        dismiss(false);
        document.removeEventListener('keydown', escHandler);
      }
    });

    document.body.appendChild(overlay);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
