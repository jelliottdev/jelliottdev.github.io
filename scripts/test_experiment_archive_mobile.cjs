const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
const output=process.env.SCREENSHOT_DIR||path.resolve('..','..','outputs','experiment-archive');

(async()=>{
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  for(const width of [320,390,1440]){
    await page.setViewportSize({width,height:860});
    await page.goto(base+'#/experiments');
    await page.waitForSelector('#browse-experiments');
    const archive=page.locator('#browse-experiments');
    assert.equal(await archive.getAttribute('open'),null,'archive is collapsed by default');
    assert.equal(await page.locator('#experiment-browse-query').isVisible(),false);
    assert.equal(await page.getByText('Human review is pending').count(),0);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px default overflow`);
    await page.screenshot({path:path.join(output,`experiments-${width}-default.png`)});
    await archive.locator('summary').first().click();
    await page.locator('#experiment-browse-query').fill('LP2-15');
    assert((await page.locator('.experiment-browse-family:visible').count())>0);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px expanded overflow`);
    await page.screenshot({path:path.join(output,`experiments-${width}-browse.png`)});
  }
  await page.goto(base+'#/experiments?section=browse-experiments');
  await page.waitForSelector('#browse-experiments');
  assert.equal(await page.locator('#browse-experiments').getAttribute('open'),'');
  await page.goto(base+'#/experiments/lp2-15-mobius-panel');
  await page.waitForFunction(()=>!document.querySelector('.loading'));
  assert.equal(await page.getByText('Human review is pending').count(),0);
  assert.equal(await page.locator('.experiment-review').getAttribute('open'),null);
  await page.setViewportSize({width:390,height:860});
  await page.screenshot({path:path.join(output,'record-390.png')});
  assert.deepEqual(errors,[]);
  await browser.close();
  console.log('PASS: archive disclosure, direct browse link, mobile widths, no horizontal overflow, and review-detail hierarchy.');
})().catch(error=>{console.error(error);process.exit(1)});
