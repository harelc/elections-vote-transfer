#!/usr/bin/env node
/* Capture REAL interaction states of the CC (k26.html on :8888) for the promo:
   - cc_sankey_hover.png : Sankey with the K25 Likud node hovered (links highlighted, tooltip up)
   - cc_map_zoom.png     : geomap after wheel-zooming into the centre
   - cc_map_popup.png    : zoomed geomap with a cluster tooltip under the cursor
   Same viewport/element shots as capture_cc.js so frames align with the base captures.
   Usage: node promo/capture_interactions.js */
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

    await page.goto(BASE, { waitUntil: 'networkidle0', timeout: 90000 });
    await sleep(1800);
    await page.evaluate(() => {
        [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'הבנתי')?.click();
    });
    await sleep(600);

    const elShot = async (sel, name) => {
        const el = await page.$(sel);
        if (!el) { console.log('MISSING', sel); return; }
        await el.screenshot({ path: path.join(OUT, name) });
        console.log('ok', name);
    };

    // --- Sankey: hover the K25 (left column) Likud node ---
    const sankeyInfo = await page.evaluate(() => {
        const stage = document.getElementById('pane-stage');
        const sr = stage.getBoundingClientRect();
        const rects = [...stage.querySelectorAll('svg rect')]
            .map(r => ({ r, b: r.getBoundingClientRect(), fill: r.getAttribute('fill') }))
            .filter(o => o.b.height > 20);
        const xs = rects.map(o => o.b.x);
        const rightX = Math.max(...xs);
        const likud = rects.filter(o => Math.abs(o.b.x - rightX) < 3 && o.fill === '#2563eb')
            .sort((a, b) => b.b.height - a.b.height)[0];
        const b = likud.b;
        return {
            cx: b.x + b.width / 2, cy: b.y + b.height / 2,
            elW: sr.width, elH: sr.height,
            fx: (b.x + b.width / 2 - sr.x) / sr.width,
            fy: (b.y + b.height / 2 - sr.y) / sr.height,
        };
    });
    console.log('sankey likud node', JSON.stringify(sankeyInfo));
    await page.mouse.move(sankeyInfo.cx, sankeyInfo.cy);
    await sleep(1000);
    const hoverCheck = await page.evaluate((pt) => {
        const el = document.elementFromPoint(pt.x, pt.y);
        const stage = document.getElementById('pane-stage');
        const t = stage.querySelector('.tooltip.visible');
        return { atPoint: el ? (el.tagName + '|' + (el.getAttribute('fill') || '')) : null,
                 stageTip: t ? t.textContent.slice(0, 60) : null };
    }, { x: sankeyInfo.cx, y: sankeyInfo.cy });
    console.log('hover check', JSON.stringify(hoverCheck));
    const tip = await page.evaluate(() => {
        const t = document.querySelector('.tooltip.visible');
        if (!t) return null;
        const stage = document.getElementById('pane-stage').getBoundingClientRect();
        const b = t.getBoundingClientRect();
        return { fx: (b.x - stage.x) / stage.width, fy: (b.y - stage.y) / stage.height,
                 fw: b.width / stage.width, fh: b.height / stage.height, text: t.textContent.slice(0, 80) };
    });
    console.log('sankey tooltip', JSON.stringify(tip));
    // clip screenshot (no scrollIntoView — that would shift the hover target)
    const stageEl = await page.$('#pane-stage');
    const sBox = await stageEl.boundingBox();
    await page.screenshot({ path: path.join(OUT, 'cc_sankey_hover.png'),
        clip: { x: sBox.x, y: sBox.y, width: sBox.width, height: sBox.height } });
    console.log('ok cc_sankey_hover.png (clip)');

    // --- Geomap: wheel-zoom into the centre, then hover a cluster ---
    await page.mouse.move(10, 10);
    await page.evaluate(() => document.getElementById('pane-geomap').scrollIntoView({ block: 'center' }));
    await sleep(2500);
    const mapInfo = await page.evaluate(() => {
        const pane = document.getElementById('pane-geomap');
        const pr = pane.getBoundingClientRect();
        const c = pane.querySelector('canvas').getBoundingClientRect();
        return { cx: c.x + c.width / 2, cy: c.y + c.height / 2,
                 fx: (c.x + c.width / 2 - pr.x) / pr.width, fy: (c.y + c.height / 2 - pr.y) / pr.height,
                 elW: pr.width, elH: pr.height };
    });
    console.log('map canvas centre', JSON.stringify(mapInfo));
    await page.mouse.move(mapInfo.cx, mapInfo.cy);
    await page.mouse.wheel({ deltaY: -1200 });
    await sleep(800);
    await page.mouse.wheel({ deltaY: -1200 });
    await sleep(1500);
    // park the cursor at the canvas corner so no tooltip is up for the plain zoom shot
    await page.mouse.move(mapInfo.cx - 260, mapInfo.cy - 320);
    await sleep(700);
    await elShot('#pane-geomap', 'cc_map_zoom.png');
    // hover the centre cluster -> cluster tooltip (known-good point)
    await page.mouse.move(mapInfo.cx, mapInfo.cy, { steps: 14 });
    await sleep(1100);
    const ctip = await page.evaluate(() => {
        const t = document.querySelector('.cluster-tooltip');
        if (!t || t.getBoundingClientRect().width === 0) return null;
        const pane = document.getElementById('pane-geomap').getBoundingClientRect();
        const b = t.getBoundingClientRect();
        return { fx: (b.x - pane.x) / pane.width, fy: (b.y - pane.y) / pane.height, text: t.textContent.slice(0, 80) };
    });
    console.log('map cluster tooltip', JSON.stringify(ctip));
    await elShot('#pane-geomap', 'cc_map_popup.png');

    await browser.close();
    console.log('DONE', OUT);
}
main().catch(e => { console.error(e); process.exit(1); });
