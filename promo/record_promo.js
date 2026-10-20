#!/usr/bin/env node
/**
 * Records promo/promo.html (the election-night ad) to a vertical 1080x1920 MP4.
 *
 * The page exposes window.Promo.render(t), so frames are driven by time
 * directly. Run promo/capture_screens.js first to refresh the screenshots.
 * The Sankey film frames in promo/film/ are extracted from promo/sankey_film.mp4
 * (recorded with: node record_animation.js --width 1080 --height 1350 --speed 2.5
 * --output promo/sankey_film.mp4) on first run.
 *
 * Usage:
 *   node promo/record_promo.js [--fps 30] [--output promo/election_night_he.mp4]
 *   node promo/record_promo.js --stills 1,6,13,40   # PNGs at those seconds
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
const OUTPUT = getArg('output', path.join(__dirname, 'election_night_he.mp4'));
const STILLS = getArg('stills', '');
const FRAMES_DIR = path.join(__dirname, '.promo-frames');
const FILM_DIR = path.join(__dirname, 'film');
const FILM_SOURCE = path.join(__dirname, 'sankey_film.mp4');

function run(cmd, cmdArgs) {
    const child = spawn(cmd, cmdArgs, { stdio: 'inherit' });
    return new Promise((resolve, reject) => child.on('close', c => c === 0 ? resolve() : reject(new Error(`${cmd} ${c}`))));
}

// promo.html steps through these frames; FILM_FRAMES there must match the count.
async function ensureFilmFrames() {
    if (fs.existsSync(FILM_DIR) && fs.readdirSync(FILM_DIR).length) return;
    fs.mkdirSync(FILM_DIR, { recursive: true });
    await run('ffmpeg', ['-loglevel', 'error', '-y', '-t', '20.5', '-i', FILM_SOURCE,
        '-vf', 'setpts=PTS/2.3,fps=30,scale=860:-1', '-q:v', '3', path.join(FILM_DIR, 'f_%04d.jpg')]);
    console.log(`Extracted ${fs.readdirSync(FILM_DIR).length} film frames`);
}

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
    await ensureFilmFrames();
    const server = await serve(__dirname);
    const port = server.address().port;
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--font-render-hinting=none'],
        defaultViewport: { width: 1080, height: 1920, deviceScaleFactor: 1 },
    });
    const page = await browser.newPage();
    await page.goto(`http://127.0.0.1:${port}/promo.html?record=1`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => window.Promo && window.Promo.ready);
    const duration = await page.evaluate(() => window.Promo.duration);
    if (STILLS) {
        for (const s of STILLS.split(',').map(Number)) {
            await page.evaluate((t) => window.Promo.render(t), s);
            const out = path.join(__dirname, `still_${String(s).replace('.', '_')}.png`);
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
        if (i % 30 === 0) process.stdout.write(`\r${i}/${total} frames`);
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
