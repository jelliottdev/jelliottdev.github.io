const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';

(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [390,1440]){
   const page=await browser.newPage({viewport:{width,height:844}});
   await page.goto(base+'#/search/Atbash');
   await page.waitForSelector('[data-search-kind="guide"]');
   await page.locator('[data-search-kind="guide"]').click();
   assert.equal(await page.locator('[data-search-kind="guide"]').getAttribute('aria-pressed'),'true');
   assert.match(new URL(page.url()).hash,/kind=guide/);
   assert.equal(await page.locator('#ranked-search-results .wiki-search-hit').count(),
    await page.locator('#ranked-search-results .wiki-search-hit[href^="#/wiki/"]').count());
   await page.reload();
   await page.waitForSelector('[data-search-kind="guide"]');
   assert.equal(await page.locator('[data-search-kind="guide"]').getAttribute('aria-pressed'),'true',
    'Result type must survive reload and shared links');
   await page.goto(base+'#/search/zzzzzznotfound?kind=source&release=LP1&type=runic-text');
   await page.waitForSelector('#clear-search-filters');
   assert.equal(await page.locator('[data-search-kind="source"]').getAttribute('aria-pressed'),'true');
   assert.equal(await page.locator('#search-release').inputValue(),'LP1');
   await page.locator('#clear-search-filters').click();
   assert.equal(await page.locator('[data-search-kind="all"]').getAttribute('aria-pressed'),'true');
   assert.equal(await page.locator('#search-release').inputValue(),'');
   assert.equal(await page.locator('#search-page-type').inputValue(),'');
   assert.equal(new URL(page.url()).hash,'#/search/zzzzzznotfound');
   assert.equal(await page.evaluate(()=>document.activeElement.dataset.searchKind),'all',
    'Keyboard focus must remain in search controls when the reset button disappears');
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),
    `${width}px search controls must not overflow`);
   if(process.env.SCREENSHOT_PATH&&width===390)await page.screenshot({path:process.env.SCREENSHOT_PATH,fullPage:true});
   await page.route('https://example.com/source',route=>route.fulfill({body:'External source reached'}));
   await page.goto(base+'#/overview');
   await page.waitForSelector('#search-suggestions',{state:'attached'});
   await page.locator('#search-suggestions').evaluate(panel=>{
    panel.hidden=false;panel.innerHTML='<a href="https://example.com/source">Source result</a>';
   });
   await page.locator('#search-suggestions a').click();
   await page.waitForURL('https://example.com/source');
   assert.equal(await page.locator('body').innerText(),'External source reached');
   await page.close();
  }
  console.log('PASS: result type survives share/reload; filtered empty state resets URL, controls and focus; source suggestions open external URLs at 390px and 1440px.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
