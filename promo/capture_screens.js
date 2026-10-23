#!/usr/bin/env node
/**
 * Captures the site pages that appear inside promo/promo.html.
 *
 * Phone shots come from the m/ pages, desktop shots from pages with no m/ twin.
 * Writes PNGs to promo/screens/. Map tiles need network access.
 *
 * Usage:
 *   node promo/capture_screens.js [--lang he|en] [--only geomap,sankey]
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const http = require('http');

const args = process.argv.slice(2);
function getArg(name, defaultVal) {
    const idx = args.indexOf('--' + name);
    return idx >= 0 && args[idx + 1] ? args[idx + 1] : defaultVal;
}

const LANG = getArg('lang', 'he');
const ONLY = getArg('only', '').split(',').filter(Boolean);
const OUT_DIR = path.join(__dirname, 'screens');
const SITE = path.join(__dirname, '..', 'site');

const PHONE = { width: 412, height: 892, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true };
const DESKTOP = { width: 1440, height: 900, deviceScaleFactor: 1.5 };
const MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';

const SHOTS = [
    { id: 'geomap', url: 'm/geomap.html', view: PHONE, wait: 4000 },
    { id: 'sankey', url: 'm/sankey.html', view: PHONE, wait: 2500 },
    { id: 'dhondt', url: 'm/dhondt.html', view: PHONE, wait: 1500, css: '.turnout-banner{display:none!important}' },
    { id: 'tsne', url: 'm/tsne.html', view: PHONE, wait: 3500 },
    // The simulated K26 count has no anomalies, so this shot uses K25.
    { id: 'irregular', url: 'm/irregular.html', view: PHONE, wait: 2500,
        act: () => [...document.querySelectorAll('button')].find(b => b.textContent.trim() === '25').click() },
    { id: 'settlement', url: 'm/settlement.html?name=' + encodeURIComponent('חיפה'), view: PHONE, wait: 3000 },
    { id: 'turnout', url: 'turnout.html', view: DESKTOP, wait: 2000 },
    { id: 'fraud', url: 'fraud-sim.html', view: DESKTOP, wait: 4000 },
];

function serve(root) {
    const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css',
        '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
    const server = http.createServer((req, res) => {
        let rel = decodeURIComponent(req.url.split('?')[0]);
        if (rel.endsWith('/')) rel += 'index.html';
        const file = path.join(root, rel);
        if (!file.startsWith(root)) { res.writeHead(403); res.end(); return; }
        fs.readFile(file, (err, body) => {
            if (err) { res.writeHead(404); res.end(); return; }
            res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
            res.end(body);
        });
    });
    return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function main() {
    fs.mkdirSync(OUT_DIR, { recursive: true });
    const server = await serve(SITE);
    const port = server.address().port;
    const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--font-render-hinting=none'] });

    for (const shot of SHOTS) {
        if (ONLY.length && !ONLY.includes(shot.id)) continue;
        const page = await browser.newPage();
        if (shot.view.isMobile) await page.setUserAgent(MOBILE_UA);
        await page.setViewport(shot.view);
        await page.evaluateOnNewDocument((lang) => {
            localStorage.setItem('k26_intro_v1', '1');
            localStorage.setItem('lang', lang);
            localStorage.setItem('e26_seen', '1');
            localStorage.setItem('fraud-sim-intro-seen-v1', '1');
            sessionStorage.setItem('bmc_dismissed', '1');
            sessionStorage.setItem('e26_notice_closed', '1');
        }, LANG);
        const sep = shot.url.includes('?') ? '&' : '?';
        await page.goto(`http://127.0.0.1:${port}/${shot.url}${sep}e26=1&lang=${LANG}`,
            { waitUntil: 'networkidle0', timeout: 90000 });
        await page.evaluate(() => document.fonts.ready);
        if (shot.act) await page.evaluate(shot.act);
        await new Promise(r => setTimeout(r, shot.wait));
        await page.addStyleTag({ content: '#e26-widget,.bmc-banner,#bmc-banner{display:none!important}' + (shot.css || '') });
        const out = path.join(OUT_DIR, `${shot.id}_${LANG}.png`);
        await page.screenshot({ path: out });
        console.log('Wrote', path.relative(process.cwd(), out));
        await page.close();
    }

    await browser.close();
    server.close();
}

main().catch(err => { console.error(err); process.exit(1); });
