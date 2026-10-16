#!/usr/bin/env node
/**
 * Records the turnout sweep (site/turnout.html) to a square MP4 for social media.
 *
 * Each scenario: hold at the start, sweep national turnout up at a constant
 * rate (pausing on the forecast), then hold with a summary caption. The page
 * renders synchronously per call, so frames are driven directly, not by time.
 *
 * Usage:
 *   node record_turnout.js [options]
 *
 * Options:
 *   --scenarios LIST  Comma list of everyone,right,leftcenter,arab,leftcenter_arab (default: all)
 *   --lang he|en      Language (default: he)
 *   --ratio N         Relative motivation of the scenario's camp (default: 2)
 *   --from N          Start turnout, % (default: 67)
 *   --to N            End turnout, % (default: 85; capped per scenario)
 *   --seconds N       Sweep length per scenario (default: 6)
 *   --fps N           Frame rate (default: 30)
 *   --size N          Square frame size (default: 1080)
 *   --output FILE     Output file (default: turnout_<lang>.mp4)
 *   --still PCT       Write one PNG at this turnout per scenario and exit
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const args = process.argv.slice(2);
function getArg(name, defaultVal) {
    const idx = args.indexOf('--' + name);
    return idx >= 0 && args[idx + 1] ? args[idx + 1] : defaultVal;
}

const SCENARIOS = getArg('scenarios', 'everyone,right,leftcenter,arab,leftcenter_arab').split(',');
const LANG = getArg('lang', 'he');
const RATIO = parseFloat(getArg('ratio', '2'));
const FROM = parseFloat(getArg('from', '67')) / 100;
const TO = parseFloat(getArg('to', '85')) / 100;
const SWEEP_S = parseFloat(getArg('seconds', '6'));
const FPS = parseInt(getArg('fps', '30'));
const SIZE = parseInt(getArg('size', '1080'));
const OUTPUT = getArg('output', `turnout_${LANG}.mp4`);
const STILL = getArg('still', null);
const FRAMES_DIR = path.join(__dirname, '.turnout-frames');

const HOLD_START_S = 1.0;
const HOLD_FORECAST_S = 0.6;
const HOLD_END_S = 2.8;
const OUTRO_S = 3.0;

function serve(root) {
    const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css',
        '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
    const server = http.createServer((req, res) => {
        const file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
        fs.readFile(file, (err, body) => {
            if (err) { res.writeHead(404); res.end(); return; }
            res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
            res.end(body);
        });
    });
    return new Promise(resolve => server.listen(0, () => resolve(server)));
}

async function main() {
    const server = await serve(path.join(__dirname, 'site'));
    const port = server.address().port;
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--font-render-hinting=none'],
        defaultViewport: { width: SIZE, height: SIZE, deviceScaleFactor: 1 },
    });
    const page = await browser.newPage();
    await page.evaluateOnNewDocument((lang) => {
        localStorage.setItem('k26_intro_v1', '1');
        localStorage.setItem('lang', lang);
        sessionStorage.setItem('bmc_dismissed', '1');
        sessionStorage.setItem('e26_notice_closed', '1');
    }, LANG);
    await page.goto(`http://localhost:${port}/turnout.html?record=1&lang=${LANG}`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => window.TurnoutSim && window.TurnoutSim.ready);
    await page.evaluate(() => document.fonts.ready);
    if (SIZE !== 1080) {
        await page.evaluate((s) => { document.body.style.zoom = s / 1080; }, SIZE);
    }

    const sim = (fn, ...a) => page.evaluate((fn, a) => window.TurnoutSim[fn](...a), fn, a);
    const weightsFor = (s) => ({
        everyone: [1, 1, 1], right: [RATIO, 1, 1], leftcenter: [1, RATIO, 1],
        arab: [1, 1, RATIO], leftcenter_arab: [1, RATIO, RATIO],
    })[s];

    if (STILL) {
        for (const s of SCENARIOS) {
            await sim('setWeights', weightsFor(s));
            await sim('setTurnout', parseFloat(STILL) / 100);
            await sim('clearGlow');
            const out = `turnout_still_${s}_${LANG}.png`;
            await page.screenshot({ path: out });
            console.log('Wrote', out);
        }
        await browser.close();
        server.close();
        return;
    }

    if (fs.existsSync(FRAMES_DIR)) fs.rmSync(FRAMES_DIR, { recursive: true });
    fs.mkdirSync(FRAMES_DIR);
    let frame = 0;
    const shoot = async () => {
        await page.screenshot({ path: path.join(FRAMES_DIR, `f_${String(frame++).padStart(5, '0')}.png`) });
    };
    const hold = async (seconds) => { for (let i = 0; i < Math.round(seconds * FPS); i++) await shoot(); };

    const baseline = await sim('baseline');
    for (const s of SCENARIOS) {
        await sim('setWeights', weightsFor(s));
        await sim('caption', null);
        const [lo, hi] = await sim('range');
        const start = Math.max(lo, FROM), end = Math.min(hi, TO);
        await sim('setTurnout', start);
        await sim('clearGlow');
        await hold(HOLD_START_S);
        const n = Math.round(SWEEP_S * FPS);
        let pausedAtForecast = false;
        for (let i = 1; i <= n; i++) {
            const t = start + (end - start) * i / n;
            if (!pausedAtForecast && t >= baseline && start < baseline) {
                await sim('setTurnout', baseline);
                await hold(HOLD_FORECAST_S);
                pausedAtForecast = true;
            }
            await sim('setTurnout', t);
            await shoot();
        }
        await sim('caption', 'summary');
        await hold(HOLD_END_S);
        process.stdout.write(`\r${s} done, ${frame} frames`);
    }
    await sim('caption', 'outro');
    await hold(OUTRO_S);
    console.log(`\nCaptured ${frame} frames (${(frame / FPS).toFixed(1)}s)`);

    await browser.close();
    server.close();

    const ffmpeg = spawn('ffmpeg', ['-y', '-framerate', String(FPS), '-i', path.join(FRAMES_DIR, 'f_%05d.png'),
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUTPUT],
        { stdio: 'inherit' });
    await new Promise((resolve, reject) => ffmpeg.on('close', c => c === 0 ? resolve() : reject(new Error('ffmpeg ' + c))));
    fs.rmSync(FRAMES_DIR, { recursive: true });
    console.log(`Done: ${OUTPUT} (${(fs.statSync(OUTPUT).size / 1048576).toFixed(1)} MB)`);
}

main().catch(err => { console.error(err); process.exit(1); });
