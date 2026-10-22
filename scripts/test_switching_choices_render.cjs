const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const base = process.env.WIKI_BASE_URL || 'http://127.0.0.1:8765/';
const output = process.env.SCREENSHOT_DIR || path.resolve('..', '..', 'outputs', 'visual-system');

(async () => {
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  try {
    for (const width of [320, 390]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      await page.goto(base + '#/wiki/method-adaptive-rules?section=example');
      await page.waitForSelector('.switching-choices-example');
      assert.equal(await page.locator('.switching-choices-example tbody[data-variant="fixed"] tr').count(), 8);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px overflow`);
      await page.locator('.switching-choices-example').scrollIntoViewIfNeeded();
      await page.screenshot({path: path.join(output, `switching-choices-${width}.png`)});
      await page.locator('.switching-choices-comparison summary').click();
      assert.equal(await page.locator('.switching-choices-example tbody[data-variant="zero-shift"] tr').count(), 8);
      await page.close();
    }
    console.log('PASS: the source-backed choice tables render and expand at 320 and 390px.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
