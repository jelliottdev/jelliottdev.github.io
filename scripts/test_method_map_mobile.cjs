const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
const output=process.env.SCREENSHOT_DIR||path.resolve('..','..','outputs','method-map');

(async()=>{
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  for(const width of [320,390,1440]){
    await page.setViewportSize({width,height:860});
    await page.goto(base+'#/wiki/solving-methods'); await page.reload();
    await page.waitForSelector('.method-group');
    assert((await page.locator('.method-group').count())>3);
    assert.equal(await page.locator('.method-group > details[open]').count(),0,'categories closed by default');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px default overflow`);
    await page.screenshot({path:path.join(output,`methods-${width}-default.png`)});
    await page.locator('.method-group > details > summary').first().click();
    assert((await page.locator('.method-family:visible').count())>0);
    assert.equal(await page.locator('#family-fixed-substitution h3 a').getAttribute('href'),'#/wiki/method-fixed-substitution');
    await page.locator('#family-fixed-substitution > details > summary').click();
    assert((await page.locator('#family-fixed-substitution > details li a:visible').count())>0);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px expanded overflow`);
    await page.screenshot({path:path.join(output,`methods-${width}-expanded.png`)});
  }
  await page.goto(base+'#/wiki/solving-methods?section=family-fixed-substitution');
  await page.waitForSelector('#family-fixed-substitution');
  assert.equal(await page.locator('#family-fixed-substitution').isVisible(),true,'family deep link opens its category');
  assert.equal(await page.locator('#family-fixed-substitution').locator('xpath=ancestor::details[1]').getAttribute('open'),'');
  assert.deepEqual(errors,[]);
  await browser.close();
  console.log('PASS: collapsed method categories, expanded families, deep link, and 320/390/1440 widths.');
})().catch(error=>{console.error(error);process.exit(1)});
