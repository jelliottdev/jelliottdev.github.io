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
    for (const width of [320, 390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      await page.goto(base + '#/experiments/lp2-row-column-routes');
      await page.waitForSelector('.experiment-article');
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px overflow`);
      assert(await page.getByRole('link', {name: 'Download this experiment (ZIP)'}).isVisible());
      assert.equal(await page.locator('.experiment-command pre').innerText(), 'python experiments/records/lp2-row-column-routes/run.py --check');
      assert(await page.getByRole('button', {name: 'Copy command'}).isVisible());
      if (width === 390) {
        await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], {origin: new URL(base).origin});
        await page.getByRole('button', {name: 'Copy command'}).click();
        assert.equal(await page.evaluate(() => navigator.clipboard.readText()), 'python experiments/records/lp2-row-column-routes/run.py --check');
      }
      assert.equal(await page.locator('body').innerText().then(text => text.includes('Human review pending')), false);
      assert.equal(await page.locator('.route-trace img').count(), 0);
      const displayedRows = await page.locator('.route-trace tbody tr').evaluateAll(rows => rows.map(row => [...row.cells].map(cell => cell.textContent.trim())));
      assert.deepEqual(displayedRows, expectedRows);
      assert.equal(await page.locator('.route-demo-table tbody tr').count(), 4);
      assert(await page.evaluate(() => document.querySelector('#experiment-scope').compareDocumentPosition(document.querySelector('.route-demo')) & Node.DOCUMENT_POSITION_FOLLOWING));
      const exactScope = page.locator('.experiment-article details').filter({has: page.getByText('Exclusions and exact method', {exact: true})}).first();
      assert.equal(await exactScope.getAttribute('open'), null);
      assert.match(await page.locator('.route-demo-reading').innerText(), /2 → 8 → 27 → 20/);
      await page.getByRole('button', {name: 'Rows first'}).click();
      await page.getByRole('button', {name: 'Alternate direction'}).click();
      assert.match(await page.locator('.route-demo-reading').innerText(), /2 → 5 → 17 → 21 → 1 → 12 → 13 → 8/);
      assert.equal(await page.locator('[data-route-cell="1-3"] .route-demo-step').innerText(), '#5');
      await page.getByRole('button', {name: 'Columns first'}).click();
      await page.getByRole('button', {name: 'Same direction'}).click();
      if (width === 390) {
        await page.getByRole('link', {name: /Jump to files and steps/}).click();
        assert.match(page.url(), /section=experiment-reproduce/);
        assert(await page.locator('#experiment-reproduce').isVisible());
        await page.goto(base + '#/experiments/lp2-row-column-routes');
        await page.waitForSelector('.route-demo');
      }
      await page.evaluate(() => { document.activeElement.blur(); scrollTo(0, 0); });
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
    for (const width of [320, 390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      await page.goto(base + '#/experiments/lp1-width-selection');
      await page.waitForSelector('.width-selection-figure');
      assert.equal(await page.locator('.width-selection-figure tbody tr').count(), 6);
      assert.equal(await page.locator('.width-selection-figure img').count(), 0);
      assert.equal((await page.locator('.experiment-limit').innerText()).toLowerCase().includes('human review pending'), false);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px width-selection overflow`);
      assert.equal(await page.locator('.width-selection-detail').getAttribute('open'), null);
      await page.screenshot({path: path.join(output, `width-selection-${width}.png`), fullPage: true});
      await page.close();
    }
    const outguess = await browser.newPage({viewport: {width: 390, height: 844}});
    await outguess.goto(base + '#/experiments/outguess-guard-sweep');
    await outguess.waitForSelector('#experiment-scope');
    const visibleScope = await outguess.locator('#experiment-scope').locator('xpath=..').innerText();
    assert.match(visibleScope, /77 original JPEGs; literal Default key/);
    assert.equal(visibleScope.includes('bdc1810e59cb1152'), false);
    assert.match(await outguess.locator('.experiment-figure figcaption').first().innerText(), /Bar lengths count images/);
    await outguess.close();
    for (const width of [320, 390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      await page.goto(base + '#/experiments/parallel-language-blocks');
      await page.waitForSelector('.language-block-figure');
      assert.equal(await page.locator('.language-block-figure tbody tr').count(), 8);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px language figure overflow`);
      await page.getByRole('button', {name: 'GP grouping'}).click();
      assert.match(await page.locator('.language-block-figure tbody tr').first().innerText(), /0\.12385/);
      assert.equal(await page.locator('.language-block-figure button[aria-pressed="true"]').innerText(), 'GP grouping');
      await page.getByRole('button', {name: 'Letters', exact: true}).click();
      await page.evaluate(() => { document.activeElement.blur(); scrollTo(0, 0); });
      await page.screenshot({path: path.join(output, `language-blocks-${width}.png`), fullPage: true});
      await page.close();
    }
    console.log('PASS: experiment layout at 320, 390 and 1280px; route, width, and language visuals match saved results.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1)});
