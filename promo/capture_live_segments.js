#!/usr/bin/env node
/* Capture GENUINELY LIVE interaction segments for the CC promo.
   Drives the real k26.html (served on :8888) with a real scripted mouse:
   - sankey_live.mp4 : eased travel to the K26 Likud node, the page's own
     hover highlight + tooltip fire, dwell, travel away.
   - map_live.mp4    : real wheel-zoom into the geomap, eased travel to a
     cluster pie, the page's own cluster tooltip opens, dwell, travel away.
   Frames come from CDP Page.startScreencast while the events are dispatched;
   they are cropped to the pane element and encoded to 7.0s MP4 segments.
   Timings/coordinates are fixed below, so runs are reproducible.
   Usage: node promo/capture_live_segments.js */
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const BASE = 'http://127.0.0.1:8888/k26.html?e26=1';
const SEG_DIR = path.join(__dirname, 'segments');
const TMP = path.join(__dirname, '.live-frames');
const sleep = ms => new Promise(r => setTimeout(r, ms));

function run(cmd, args) {
    return new Promise((resolve, reject) => {
        const p = spawn(cmd, args, { stdio: 'inherit' });
        p.on('close', c => c === 0 ? resolve() : reject(new Error(cmd + ' exit ' + c)));
    });
}

async function moveEased(page, x0, y0, x1, y1, durMs) {
    const steps = Math.max(8, Math.round(durMs / 33));
    for (let i = 1; i <= steps; i++) {
        const q = i / steps, e = q < 0.5 ? 2 * q * q : 1 - Math.pow(-2 * q + 2, 2) / 2;
        await page.mouse.move(x0 + (x1 - x0) * e, y0 + (y1 - y0) * e);
        await sleep(durMs / steps);
    }
}

async function startScreencast(page, dir) {
    if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true });
    fs.mkdirSync(dir, { recursive: true });
    const client = await page.createCDPSession();
    const frames = [];
    let idx = 0, firstTs = null;
    client.on('Page.screencastFrame', ev => {
        if (firstTs === null) firstTs = ev.metadata.timestamp;
        const file = path.join(dir, 'f_' + String(idx).padStart(5, '0') + '.jpg');
        fs.writeFileSync(file, Buffer.from(ev.data, 'base64'));
        frames.push({ file: path.basename(file), ts: ev.metadata.timestamp - firstTs });
        idx++;
        client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }).catch(() => {});
    });
    await client.send('Page.startScreencast', { format: 'jpeg', quality: 82, everyNthFrame: 1 });
    return { client, frames };
}

async function encodeSegment(frames, dir, crop, out, seconds) {
    const list = frames.map((f, i) => {
        const d = i + 1 < frames.length ? Math.min(0.5, Math.max(0.008, frames[i + 1].ts - f.ts)) : 0.05;
        return `file '${f.file}'\nduration ${d.toFixed(3)}`;
    }).join('\n') + `\nfile '${frames[frames.length - 1].file}'\n`;
    const listPath = path.join(dir, 'list.txt');
    fs.writeFileSync(listPath, list);
    await run('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', listPath,
        '-vf', `crop=${crop.w}:${crop.h}:${crop.x}:${crop.y},scale=${crop.outW}:${crop.outH}`,
        '-r', '30', '-t', String(seconds), '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
        '-g', '5', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]);
    console.log('segment:', path.relative(process.cwd(), out), frames.length, 'frames');
}

async function main() {
    fs.mkdirSync(SEG_DIR, { recursive: true });
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1760, height: 1450, deviceScaleFactor: 1.5 });
    page.on('pageerror', e => console.log('PAGEERROR', e.message));
    await page.goto(BASE, { waitUntil: 'networkidle0', timeout: 90000 });
    await sleep(2200);
    await page.evaluate(() => {
        [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'הבנתי')?.click();
    });
    await sleep(700);

    // ---------------- Sankey segment (7s) ----------------
    await page.evaluate(() => document.getElementById('pane-stage').scrollIntoView({ block: 'start' }));
    await sleep(1000);
    const sk = await page.evaluate(() => {
        const stage = document.getElementById('pane-stage');
        const sr = stage.getBoundingClientRect();
        const rects = [...stage.querySelectorAll('svg rect')]
            .map(r => ({ b: r.getBoundingClientRect(), fill: r.getAttribute('fill') }))
            .filter(o => o.b.height > 20);
        const rightX = Math.max(...rects.map(o => o.b.x));
        const likud = rects.filter(o => Math.abs(o.b.x - rightX) < 3 && o.fill === '#2563eb')
            .sort((a, b) => b.b.height - a.b.height)[0].b;
        return { el: { x: sr.x, y: sr.y, w: sr.width, h: sr.height },
                 node: { x: likud.x + likud.width / 2, y: likud.y + likud.height / 2 },
                 neutral: { x: sr.x + sr.width * 0.55, y: sr.y + 70 },
                 away: { x: sr.x + sr.width * 0.55, y: sr.y + sr.height * 0.42 } };
    });
    console.log('sankey geometry', JSON.stringify(sk));
    await page.mouse.move(sk.neutral.x, sk.neutral.y);
    await sleep(400);
    let sc = await startScreencast(page, path.join(TMP, 'sankey'));
    const t0 = Date.now();
    const at = async (sec, fn) => { const w = t0 + sec * 1000 - Date.now(); if (w > 0) await sleep(w); await fn(); };
    await at(1.1, () => moveEased(page, sk.neutral.x, sk.neutral.y, sk.node.x, sk.node.y, 1400));
    await at(5.7, () => moveEased(page, sk.node.x, sk.node.y, sk.away.x, sk.away.y, 900));
    await at(7.0, async () => {});
    await sc.client.send('Page.stopScreencast');
    const dsf = 1; // CDP screencast frames are CSS-pixel sized (1760x1450)
    await encodeSegment(sc.frames, path.join(TMP, 'sankey'),
        { w: Math.round(sk.el.w * dsf), h: Math.round(sk.el.h * dsf), x: Math.round(sk.el.x * dsf), y: Math.round(sk.el.y * dsf), outW: 978, outH: 1838 },
        path.join(SEG_DIR, 'sankey_live.mp4'), 7);

    // ---------------- Geomap segment (7s) ----------------
    await page.mouse.move(20, 20);
    await page.evaluate(() => document.getElementById('pane-geomap').scrollIntoView({ block: 'center' }));
    await sleep(2600);
    const mp = await page.evaluate(() => {
        const pane = document.getElementById('pane-geomap');
        const pr = pane.getBoundingClientRect();
        const c = pane.querySelector('canvas').getBoundingClientRect();
        return { el: { x: pr.x, y: pr.y, w: pr.width, h: pr.height },
                 canvas: { x: c.x, y: c.y, w: c.width, h: c.height } };
    });
    console.log('map geometry', JSON.stringify(mp));
    const cv = f => ({ x: mp.canvas.x + mp.canvas.w * f[0], y: mp.canvas.y + mp.canvas.h * f[1] });
    const park = cv([0.86, 0.16]), centre = cv([0.50, 0.50]), pie = cv([0.243, 0.327]), awayM = cv([0.68, 0.74]);
    await page.mouse.move(park.x, park.y);
    await sleep(400);
    sc = await startScreencast(page, path.join(TMP, 'map'));
    const m0 = Date.now();
    const atm = async (sec, fn) => { const w = m0 + sec * 1000 - Date.now(); if (w > 0) await sleep(w); await fn(); };
    await atm(1.0, () => moveEased(page, park.x, park.y, centre.x, centre.y, 600));
    await atm(1.7, () => page.mouse.wheel({ deltaY: -1200 }));
    await atm(2.4, () => page.mouse.wheel({ deltaY: -1200 }));
    await atm(3.2, () => moveEased(page, centre.x, centre.y, pie.x, pie.y, 800));
    // micro-drift during the dwell so the hover stays alive and human
    await atm(4.6, () => page.mouse.move(pie.x + 4, pie.y + 3));
    await atm(5.9, () => moveEased(page, pie.x, pie.y, awayM.x, awayM.y, 800));
    await atm(7.0, async () => {});
    await sc.client.send('Page.stopScreencast');
    await encodeSegment(sc.frames, path.join(TMP, 'map'),
        { w: Math.round(mp.el.w * dsf), h: Math.round(mp.el.h * dsf), x: Math.round(mp.el.x * dsf), y: Math.round(mp.el.y * dsf), outW: 978, outH: 1390 },
        path.join(SEG_DIR, 'map_live.mp4'), 7);

    await browser.close();
    fs.rmSync(TMP, { recursive: true });
    console.log('DONE', SEG_DIR);
}
main().catch(e => { console.error(e); process.exit(1); });
