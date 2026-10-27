// Download the CEC K26 ballot-level results file (expb.csv) through a
// real Chrome. media26.bechirot.gov.il sits behind a gov.il bot
// challenge: a plain fetch/curl gets a 404 maintenance page or an
// empty 202 challenge, while a browser solves the challenge (202 ->
// cookie -> 200 download). Used by .github/workflows/k26-refresh.yml
// when the plain curl download does not yield the CSV; also runnable
// locally:  node download_expb.js data/k26_inbox/snapshot.bin
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const OUT = path.resolve(process.argv[2] || 'data/k26_inbox/snapshot.bin');
const URL = process.env.K26_RESULTS_URL || 'https://media26.bechirot.gov.il/files/expb.csv';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const dlDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'expb-dl-'));
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36');
    // Let Chrome save the file itself instead of rendering it.
    const client = await page.target().createCDPSession();
    await client.send('Page.setDownloadBehavior', { behavior: 'allow', downloadPath: dlDir });
    // Warm up on the results site (sets cookies, proves the client).
    try { await page.goto('https://votes26.bechirot.gov.il/', { waitUntil: 'networkidle2', timeout: 60000 }); } catch (e) { /* challenge nav errors are fine */ }
    await sleep(3000);
    // Navigate at the file: first hit is the 202 challenge, the browser
    // re-requests with the cookie and the 200 arrives as a download.
    for (let attempt = 1; attempt <= 3; attempt++) {
      try { await page.goto(URL + '?', { waitUntil: 'networkidle2', timeout: 60000 }); } catch (e) { /* a download aborts navigation — expected */ }
      const deadline = Date.now() + 45000;
      while (Date.now() < deadline) {
        await sleep(1500);
        const done = fs.readdirSync(dlDir).filter(f => !f.endsWith('.crdownload'));
        const partial = fs.readdirSync(dlDir).filter(f => f.endsWith('.crdownload'));
        if (done.length && !partial.length) {
          const src = path.join(dlDir, done[0]);
          const size = fs.statSync(src).size;
          if (size < 1000) throw new Error(`downloaded only ${size} bytes — challenge not solved?`);
          fs.mkdirSync(path.dirname(OUT), { recursive: true });
          fs.copyFileSync(src, OUT);
          console.log(`wrote ${OUT}: ${size} bytes (attempt ${attempt})`);
          return;
        }
      }
      console.log(`attempt ${attempt}: no completed download yet — retrying`);
    }
    throw new Error('no download completed after 3 attempts');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
