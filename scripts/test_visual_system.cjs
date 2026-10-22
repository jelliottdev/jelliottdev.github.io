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
    for (const width of [320, 390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(base + '#/overview');
      await page.waitForSelector('.home-release-strip');
      assert.equal(await page.locator('.home-release-strip a').count(), 2);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px home overflow`);
      await page.screenshot({path: path.join(output, `home-${width}.png`), fullPage: true});
      if (width < 761) {
        await page.locator('#menu').click();
        assert(await page.locator('.mobile-nav a[href="#/experiments"]').isVisible());
        await page.screenshot({path: path.join(output, `navigation-${width}.png`)});
        await page.locator('#menu').click();
      } else {
        await page.goto(base + '#/wiki/works-and-influences');
        await page.waitForSelector('.wiki-article');
        const group = page.locator('.desktop-nav .nav-group').filter({has: page.locator('a[href="#/wiki/works-and-influences"]')});
        assert.equal(await group.getAttribute('open'), '', 'Current sidebar group should open');
        assert(await group.locator('a.active').isVisible());
        await page.screenshot({path: path.join(output, 'article-desktop.png')});
      }
      assert.deepEqual(errors, []);
      await page.close();
    }
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.goto(base + '#/wiki/atbash?section=complete-mapping');
    await page.waitForSelector('.full-mapping');
    assert.equal(await page.locator('.pair-table tbody tr').count(), 15);
    await page.locator('.full-mapping').scrollIntoViewIfNeeded();
    await page.screenshot({path: path.join(output, 'atbash-390.png')});
    await page.goto(base + '#/wiki/cipher-invariants?section=worked');
    await page.waitForSelector('.sequence-figure');
    assert.equal(await page.locator('.sequence-case').count(), 4);
    assert.equal(await page.locator('.sequence-figure img').count(), 0);
    await page.locator('.sequence-figure').scrollIntoViewIfNeeded();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'diagram overflow');
    await page.screenshot({path: path.join(output, 'invariants-390.png')});
    await page.close();
    console.log('PASS: neutral home/navigation and responsive text diagrams at 320, 390, and 1280px.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exit(1)});
