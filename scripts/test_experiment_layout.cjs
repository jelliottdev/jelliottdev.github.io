const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const base = process.env.WIKI_BASE_URL || 'http://127.0.0.1:8765/';
const output = process.env.SCREENSHOT_DIR || path.resolve('..', '..', 'outputs', 'experiment-layout');

(async () => {
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  try {
    for (const width of [390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      await page.goto(base + '#/experiments/lp2-row-column-routes');
      await page.waitForSelector('.experiment-article');
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px overflow`);
      assert(await page.getByRole('link', {name: 'Download this experiment (ZIP)'}).isVisible());
      assert.equal(await page.locator('body').innerText().then(text => text.includes('Human review pending')), false);
      await page.screenshot({path: path.join(output, `row-column-${width}.png`), fullPage: true});
      await page.evaluate(() => scrollTo(0, 500));
      await page.waitForTimeout(250);
      assert(await page.evaluate(() => document.querySelector('.topbar').getBoundingClientRect().bottom <= 0), `${width}px header obscures reading`);
      await page.goto(base + '#/experiments/lp2-row-column-routes?section=experiment-family');
      await page.waitForSelector('#experiment-family:visible');
      assert(await page.locator('#experiment-family').evaluate(el => el.closest('details').open));
      await page.close();
    }
    console.log('PASS: experiment layout at 390 and 1280px; header scrolls out of reading space.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1)});
