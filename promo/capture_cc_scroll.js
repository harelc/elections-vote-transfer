#!/usr/bin/env node
/* Capture a tall full-page surface of the CC (k26.html on :8888) for the promo's
   scroll-down scene. Same viewport / partial-count banner as capture_cc.js.
   Scrolls through the page first so below-fold panes (map tiles, charts) render,
   then takes a full-page screenshot and logs pane positions for scroll framing.
   Usage: node promo/capture_cc_scroll.js */
const puppeteer = require('puppeteer');
const path = require('path');

const OUT = path.join(__dirname, 'screens_cc');
const BASE = 'http://127.0.0.1:8888/k26.html?e26=1';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1760, height: 1100, deviceScaleFactor: 1.5 });
    page.on('pageerror', e => console.log('PAGEERROR', e.message));

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
    await sleep(2000);
    await page.evaluate(() => {
        [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'הבנתי')?.click();
    });
    await sleep(600);

    // Walk down the page so lazy panes render, then back to top
    const pageH = await page.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0; y < pageH; y += 700) {
        await page.evaluate(yy => window.scrollTo(0, yy), y);
        await sleep(450);
    }
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await sleep(1500);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(1200);

    const info = await page.evaluate(() => {
        const top = sel => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { top: Math.round(r.top + window.scrollY), bottom: Math.round(r.bottom + window.scrollY), h: Math.round(r.height) };
        };
        return {
            pageH: document.documentElement.scrollHeight,
            votes: top('#pane-votes'),
            stage: top('#pane-stage'),
            geomap: top('#pane-geomap'),
            turnout: top('#pane-turnout'),
            suspects: top('#pane-suspects'),
        };
    });
    console.log(JSON.stringify(info, null, 1));

    await page.screenshot({ path: path.join(OUT, 'cc_page_full.png'), fullPage: true });
    console.log('ok cc_page_full.png');
    await browser.close();
}
main().catch(e => { console.error(e); process.exit(1); });
