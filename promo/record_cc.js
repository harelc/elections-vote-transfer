#!/usr/bin/env node
/**
 * Records promo/cc.html (the command-center ad, landscape 1920x1080) to MP4.
 * The page exposes window.Promo.render(t); frames are driven by time directly.
 * Run promo/capture_cc.js first to refresh the screenshots.
 *
 * Usage:
 *   node promo/record_cc.js [--fps 30] [--output promo/cc_ad_he.mp4]
 *   node promo/record_cc.js --stills 2,7,13,18   # PNGs at those seconds
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
const FPS = parseInt(getArg('fps', '30'));
const OUTPUT = getArg('output', path.join(__dirname, 'cc_ad_he.mp4'));
const STILLS = getArg('stills', '');
const FRAMES_DIR = path.join(__dirname, '.cc-frames');

function serve(root) {
    const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css',
        '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
    const server = http.createServer((req, res) => {
        const file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
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
    const server = await serve(__dirname);
    const port = server.address().port;
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--font-render-hinting=none'],
        defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
    });
    const page = await browser.newPage();
    await page.goto(`http://127.0.0.1:${port}/cc.html?record=1`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => window.Promo && window.Promo.ready);
    const duration = await page.evaluate(() => window.Promo.duration);
    if (STILLS) {
        for (const s of STILLS.split(',').map(Number)) {
            await page.evaluate((t) => window.Promo.render(t), s);
            const out = path.join(__dirname, `cc_still_${String(s).replace('.', '_')}.png`);
            await page.screenshot({ path: out });
            console.log('Wrote', path.relative(process.cwd(), out));
        }
        await browser.close();
        server.close();
        return;
    }

    if (fs.existsSync(FRAMES_DIR)) fs.rmSync(FRAMES_DIR, { recursive: true });
    fs.mkdirSync(FRAMES_DIR);
    const total = Math.round(duration * FPS);
    for (let i = 0; i < total; i++) {
        await page.evaluate((t) => window.Promo.render(t), i / FPS);
        await page.screenshot({ path: path.join(FRAMES_DIR, `f_${String(i).padStart(5, '0')}.png`) });
        if (i % 60 === 0) process.stdout.write(`\r${i}/${total} frames`);
    }
    console.log(`\nCaptured ${total} frames (${duration.toFixed(1)}s)`);
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
