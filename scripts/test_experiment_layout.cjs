const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const base = process.env.WIKI_BASE_URL || 'http://127.0.0.1:8765/';
const output = process.env.SCREENSHOT_DIR || path.resolve('..', '..', 'outputs', 'experiment-layout');
const results = JSON.parse(fs.readFileSync(path.resolve('experiments/records/lp2-row-column-routes/results.json'), 'utf8'));
const sourcePage = results.pages.find(item => item.page === 'lp2-31');
const route = sourcePage.cases.find(item => item.axis === 'column' && !item.outer_reverse && !item.inner_reverse && !item.alternating);
const expectedRows = route.source_ordinals.slice(0, 6).map((ordinal, i) => {
  const position = sourcePage.source_positions[ordinal];
  return [String(i + 1), `${position.line} · ${position.rune_position}`, String(position.index)];
});

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
      assert.equal(await page.locator('.route-trace img').count(), 0);
      const displayedRows = await page.locator('.route-trace tbody tr').evaluateAll(rows => rows.map(row => [...row.cells].map(cell => cell.textContent.trim())));
      assert.deepEqual(displayedRows, expectedRows);
      await page.screenshot({path: path.join(output, `row-column-${width}.png`), fullPage: true});
      await page.evaluate(() => scrollTo(0, 500));
      await page.waitForTimeout(250);
      assert(await page.evaluate(() => document.querySelector('.topbar').getBoundingClientRect().bottom <= 0), `${width}px header obscures reading`);
      await page.goto(base + '#/experiments/lp2-row-column-routes?section=experiment-family');
      await page.waitForSelector('#experiment-family:visible');
      assert(await page.locator('#experiment-family').evaluate(el => el.closest('details').open));
      await page.close();
    }
    for (const id of ['lp2-word-order-reversal', 'lp2-word-reversal']) {
      const saved = JSON.parse(fs.readFileSync(path.resolve(`experiments/records/${id}/results.json`), 'utf8'));
      const resultPage = saved.pages.find(item => item.page === 'lp2-31');
      const [split, joined] = resultPage.cases;
      const first = id === 'lp2-word-order-reversal' ? 0 : split.source_ordinals.findIndex((value, i) => value !== joined.source_ordinals[i]);
      const expected = Array.from({length: 6}, (_, offset) => {
        const i = first + offset;
        return [String(i), String(split.source_ordinals[i]), String(joined.source_ordinals[i])];
      });
      const page = await browser.newPage({viewport: {width: 390, height: 844}});
      await page.goto(base + `#/experiments/${id}`);
      await page.waitForSelector('.route-trace');
      assert.equal(await page.locator('.route-trace img').count(), 0);
      const displayed = await page.locator('.route-trace tbody tr').evaluateAll(rows => rows.map(row => [...row.cells].map(cell => cell.textContent.trim())));
      assert.deepEqual(displayed, expected);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${id} overflow`);
      await page.screenshot({path: path.join(output, `${id}-390.png`), fullPage: true});
      await page.close();
    }
    console.log('PASS: experiment layout at 390 and 1280px; three native traces match saved results.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1)});
