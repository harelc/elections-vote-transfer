#!/usr/bin/env node
/**
 * Records the chained Sankey animation to an MP4 video.
 *
 * Usage:
 *   node record_animation.js [options]
 *
 * Options:
 *   --fps N         Frame rate (default: 30)
 *   --width N       Viewport width (default: 1920)
 *   --height N      Viewport height (default: 1080)
 *   --speed N       Animation speed multiplier (default: 1)
 *   --output FILE   Output file (default: animation.mp4)
 *   --duration N    Max duration in seconds (default: 60)
 *   --quality N     CRF quality 0-51, lower=better (default: 18)
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const { execSync, spawn } = require('child_process');

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name, defaultVal) {
    const idx = args.indexOf('--' + name);
    return idx >= 0 && args[idx + 1] ? args[idx + 1] : defaultVal;
}

const FPS = parseInt(getArg('fps', '30'));
const WIDTH = parseInt(getArg('width', '1920'));
const HEIGHT = parseInt(getArg('height', '1080'));
const SPEED = parseFloat(getArg('speed', '1'));
const OUTPUT = getArg('output', 'animation.mp4');
const MAX_DURATION = parseInt(getArg('duration', '60'));
const QUALITY = parseInt(getArg('quality', '18'));

const FRAME_MS = 1000 / FPS;
const MAX_FRAMES = MAX_DURATION * FPS;
const FRAMES_DIR = path.join(__dirname, '.animation-frames');

async function main() {
    // Clean up / create frames directory
    if (fs.existsSync(FRAMES_DIR)) {
        fs.rmSync(FRAMES_DIR, { recursive: true });
    }
    fs.mkdirSync(FRAMES_DIR);

    console.log(`Recording: ${WIDTH}x${HEIGHT} @ ${FPS}fps, speed ${SPEED}x`);
    console.log(`Max duration: ${MAX_DURATION}s (${MAX_FRAMES} frames)`);
    console.log(`Output: ${OUTPUT}`);

    // Start a local HTTP server for the site
    const http = require('http');
    const handler = require('fs');
    const serverPath = path.join(__dirname, 'site');

    const server = http.createServer((req, res) => {
        let filePath = path.join(serverPath, req.url === '/' ? 'index.html' : req.url);
        // Remove query string
        filePath = filePath.split('?')[0];
        const ext = path.extname(filePath).toLowerCase();
        const mimeTypes = {
            '.html': 'text/html',
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml',
        };
        const contentType = mimeTypes[ext] || 'application/octet-stream';

        fs.readFile(filePath, (err, content) => {
            if (err) {
                res.writeHead(404);
                res.end('Not found: ' + filePath);
            } else {
                res.writeHead(200, { 'Content-Type': contentType });
                res.end(content);
            }
        });
    });

    await new Promise(resolve => server.listen(0, resolve));
    const PORT = server.address().port;
    console.log(`Local server on port ${PORT}`);

    // Launch browser
    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            `--window-size=${WIDTH},${HEIGHT}`,
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '--font-render-hinting=none',
        ],
        defaultViewport: { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 },
    });

    const page = await browser.newPage();

    // Inject time control BEFORE any scripts load
    await page.evaluateOnNewDocument((frameMs, speed) => {
        // Controlled time
        window.__fakeTime = 0;
        window.__frameMs = frameMs;
        window.__animDone = false;

        // Override performance.now
        const origPerfNow = performance.now.bind(performance);
        performance.now = () => window.__fakeTime;

        // Override Date.now
        Date.now = () => window.__fakeTime;

        // Fake setTimeout/clearTimeout
        let __nextTimerId = 1;
        const __pendingTimers = new Map(); // id -> {fn, fireAt}

        window.__origSetTimeout = window.setTimeout;
        window.__origClearTimeout = window.clearTimeout;

        window.setTimeout = (fn, delay = 0, ...args) => {
            const id = __nextTimerId++;
            __pendingTimers.set(id, {
                fn: () => fn(...args),
                fireAt: window.__fakeTime + delay
            });
            return id;
        };

        window.clearTimeout = (id) => {
            __pendingTimers.delete(id);
        };

        // Fake setInterval/clearInterval
        window.setInterval = (fn, interval, ...args) => {
            const id = __nextTimerId++;
            const fire = () => {
                fn(...args);
                if (__pendingTimers.has(id)) {
                    __pendingTimers.set(id, {
                        fn: fire,
                        fireAt: window.__fakeTime + interval
                    });
                }
            };
            __pendingTimers.set(id, {
                fn: fire,
                fireAt: window.__fakeTime + interval
            });
            return id;
        };
        window.clearInterval = window.clearTimeout;

        // Fake requestAnimationFrame
        let __rafCallbacks = [];
        let __nextRafId = 1;
        window.requestAnimationFrame = (cb) => {
            const id = __nextRafId++;
            __rafCallbacks.push({ id, cb });
            return id;
        };
        window.cancelAnimationFrame = (id) => {
            __rafCallbacks = __rafCallbacks.filter(r => r.id !== id);
        };

        // Advance time by one frame — called from Puppeteer
        window.__advanceFrame = () => {
            window.__fakeTime += frameMs;

            // Fire expired timers
            const toFire = [];
            for (const [id, timer] of __pendingTimers) {
                if (timer.fireAt <= window.__fakeTime) {
                    toFire.push({ id, fn: timer.fn });
                }
            }
            for (const { id, fn } of toFire) {
                __pendingTimers.delete(id);
                try { fn(); } catch(e) { console.error('Timer error:', e); }
            }

            // Fire requestAnimationFrame callbacks
            const rafs = __rafCallbacks.slice();
            __rafCallbacks = [];
            for (const { cb } of rafs) {
                try { cb(window.__fakeTime); } catch(e) { console.error('RAF error:', e); }
            }
        };

        // Also override d3's internal timer if loaded later
        window.__patchD3Timer = () => {
            if (window.d3 && window.d3.now) {
                window.d3.now = () => window.__fakeTime;
            }
        };
    }, FRAME_MS, SPEED);

    // Navigate to animation page
    console.log('Loading animation page...');
    await page.goto(`http://localhost:${PORT}/animation.html`, {
        waitUntil: 'networkidle0',
        timeout: 30000,
    });

    // Patch d3.now after d3 is loaded
    await page.evaluate(() => {
        window.__patchD3Timer();
        // Also patch d3.timer's internal clock
        if (window.d3 && d3.timerFlush) {
            // d3-timer uses performance.now which we already overrode
            // but we need to flush manually
        }
    });

    // Wait for data to load and animation to initialize
    // The animation starts automatically via `new ChainedSankeyAnimation()`
    // We need to let the constructor run and data fetch complete
    console.log('Waiting for animation to initialize...');

    // Advance time in small steps to let fetch promises resolve
    // and the animation class to construct
    for (let i = 0; i < 30; i++) {
        await page.evaluate(() => window.__advanceFrame());
        await new Promise(r => setTimeout(r, 50)); // real-time wait for network
    }

    // Check if animation is ready
    const ready = await page.evaluate(() => {
        return document.getElementById('loading')?.style.display === 'none';
    });

    if (!ready) {
        console.log('Waiting more for data load...');
        for (let i = 0; i < 60; i++) {
            await page.evaluate(() => window.__advanceFrame());
            await new Promise(r => setTimeout(r, 100));
            const ok = await page.evaluate(() =>
                document.getElementById('loading')?.style.display === 'none'
            );
            if (ok) break;
        }
    }

    // Hide UI controls for recording
    await page.evaluate(() => {
        const controls = document.getElementById('controls');
        if (controls) controls.style.display = 'none';
        const backLink = document.getElementById('back-link');
        if (backLink) backLink.style.display = 'none';
    });

    console.log('Starting frame capture...');
    let frameNum = 0;
    let consecutiveIdleFrames = 0;
    const startTime = Date.now();

    for (frameNum = 0; frameNum < MAX_FRAMES; frameNum++) {
        // Advance fake time by one frame
        await page.evaluate(() => {
            window.__advanceFrame();
            // Also flush d3 timers
            if (window.d3 && d3.timerFlush) {
                try { d3.timerFlush(); } catch(e) {}
            }
        });

        // Take screenshot
        const framePath = path.join(FRAMES_DIR, `frame_${String(frameNum).padStart(5, '0')}.png`);
        await page.screenshot({ path: framePath, type: 'png' });

        // Progress indicator
        if (frameNum % FPS === 0) {
            const sec = frameNum / FPS;
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            process.stdout.write(`\rFrame ${frameNum} (${sec.toFixed(0)}s animation / ${elapsed}s real)`);
        }

        // Check if animation is done (outro visible + some hold time)
        const animState = await page.evaluate(() => {
            const outro = document.getElementById('outro-overlay');
            return {
                outroVisible: outro?.classList.contains('visible'),
                fakeTime: window.__fakeTime
            };
        });

        if (animState.outroVisible) {
            consecutiveIdleFrames++;
            // Hold outro for 4 seconds then stop
            if (consecutiveIdleFrames > FPS * 4) {
                console.log(`\nOutro held for 4s, stopping at frame ${frameNum}`);
                break;
            }
        } else {
            consecutiveIdleFrames = 0;
        }
    }

    const totalFrames = frameNum + 1;
    console.log(`\nCaptured ${totalFrames} frames (${(totalFrames / FPS).toFixed(1)}s)`);

    // Close browser & server
    await browser.close();
    server.close();

    // Compile with ffmpeg
    console.log('Compiling video with ffmpeg...');
    const ffmpegArgs = [
        '-y',
        '-framerate', String(FPS),
        '-i', path.join(FRAMES_DIR, 'frame_%05d.png'),
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', String(QUALITY),
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        OUTPUT
    ];

    console.log(`ffmpeg ${ffmpegArgs.join(' ')}`);

    const ffmpeg = spawn('ffmpeg', ffmpegArgs, { stdio: 'inherit' });
    await new Promise((resolve, reject) => {
        ffmpeg.on('close', code => {
            if (code === 0) resolve();
            else reject(new Error(`ffmpeg exited with code ${code}`));
        });
    });

    // Clean up frames
    console.log('Cleaning up frames...');
    fs.rmSync(FRAMES_DIR, { recursive: true });

    const stats = fs.statSync(OUTPUT);
    console.log(`\nDone! ${OUTPUT} (${(stats.size / 1024 / 1024).toFixed(1)} MB)`);
}

main().catch(err => {
    console.error('Error:', err);
    process.exit(1);
});
