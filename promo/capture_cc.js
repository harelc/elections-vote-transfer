#!/usr/bin/env node
/* Capture command-center (k26.html) screenshots for the CC promo video.
   Usage: node promo/capture_cc.js
   Serves from the local dev server on 127.0.0.1:8888. */
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'screens_cc');
fs.mkdirSync(OUT, { recursive: true });
const BASE = 'http://127.0.0.1:8888/k26.html?e26=1';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1760, height: 1100, deviceScaleFactor: 1.5 });
    page.on('pageerror', e => console.log('PAGEERROR', e.message));

    // --- Simulated partial-count banner (labelled simulation in the video) ---
    await page.setRequestInterception(true);
    page.on('request', req => {
        if (req.url().includes('k26_status.json')) {
            req.respond({
                status: 200, contentType: 'application/json',
                body: JSON.stringify({
                    kind: 'partial', as_of: '2026-10-27T23:41:00+02:00',
                    ballots: 6130, ballots_total: 12018,
                    source_he: 'ספירה חלקית, ועדת הבחירות המרכזית',
                    source_en: 'Partial count, Central Elections Committee',
                }),
            });
        } else req.continue();
    });

    await page.goto(BASE, { waitUntil: 'networkidle0', timeout: 90000 });
    await sleep(1800);
    await page.evaluate(() => {
        [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'הבנתי')?.click();
    });
    await sleep(600);

    const shot = (name) => page.screenshot({ path: path.join(OUT, name) });
    const elShot = async (sel, name) => {
        const el = await page.$(sel);
        if (!el) { console.log('MISSING', sel); return; }
        await el.screenshot({ path: path.join(OUT, name) });
        console.log('ok', name);
    };

    // 1. Full top of the CC (hero, pills, banner, gemara header row)
    await shot('cc_top.png'); console.log('ok cc_top.png');

    // 2. Count banner close
    await elShot('#count-banner', 'cc_banner.png');

    // 3. Hemisphere (votes pane top)
    await elShot('#pane-votes', 'cc_votes.png');
    await elShot('.hemi-wrap', 'cc_hemi.png');

    // 4. Hemisphere with rich hover card
    const seatBox = await page.evaluate(() => {
        const c = document.querySelectorAll('.hemi-seat')[30];
        const r = c.getBoundingClientRect();
        return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    });
    await page.mouse.move(seatBox.x, seatBox.y);
    await sleep(500);
    await elShot('.hemi-wrap', 'cc_hover.png');

    // 5. Sankey stage (default tab)
    await elShot('#pane-stage', 'cc_sankey.png');

    // 6. Geomap pane (center column, below stage)
    await page.evaluate(() => document.getElementById('pane-geomap').scrollIntoView({ block: 'center' }));
    await sleep(2200);
    await elShot('#pane-geomap', 'cc_map.png');

    // 7. Turnout pane + suspects pane (end margin)
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(400);
    await elShot('#pane-turnout', 'cc_turnout.png');
    await elShot('#pane-suspects', 'cc_suspects.png');

    // 8. Seat-calculator stage tab (embedded dhondt)
    await page.evaluate(() => {
        document.querySelector('[data-stage="dhondt"]').click();
        window.scrollTo(0, 0);
    });
    await sleep(3500);
    await elShot('#pane-stage', 'cc_dhondt.png');

    await browser.close();
    console.log('DONE', OUT);
}
main().catch(e => { console.error(e); process.exit(1); });
