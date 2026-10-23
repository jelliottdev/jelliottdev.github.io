const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';

(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [320,390]){
   const page=await browser.newPage({viewport:{width,height:844},hasTouch:width===320});
   await page.goto(base+'#/overview');
   await page.waitForSelector('#search-suggestions',{state:'attached'});
   await page.locator('#menu').click();
   assert.equal(await page.locator('#menu').getAttribute('aria-expanded'),'true');
   assert.equal(await page.locator('#main').evaluate(el=>el.inert),true);
   await page.locator('#search').click();
   assert.equal(await page.locator('#menu').getAttribute('aria-expanded'),'false',
    'The search field must remain usable while the mobile drawer is open');
   await page.locator('#search').fill('Atbash');
   const suggestion=page.locator('#search-suggestions a[href="#/wiki/atbash"]').first();
   await suggestion.waitFor({state:'visible'});
   if(width===320)await suggestion.tap();
   else{await page.locator('#search').press('ArrowDown');assert.equal(await page.evaluate(()=>document.activeElement.getAttribute('href')),'#/wiki/atbash');await page.keyboard.press('Enter')}
   await page.waitForURL('**/#/wiki/atbash');
   await page.waitForSelector('h1');
   assert.match(await page.locator('h1').first().innerText(),/Atbash/i);
   assert.equal(await page.locator('#search').inputValue(),'',
    'Header search must not look like an active filter on an article');
   await page.goto(base+'#/search/Atbash');
   await page.waitForSelector('#ranked-search-results .wiki-search-hit');
   assert.equal(await page.locator('#search').inputValue(),'Atbash');
   await page.locator('#ranked-search-results a[href="#/wiki/atbash"]').first().click();
   await page.waitForURL('**/#/wiki/atbash');
   assert.equal(await page.locator('#search').inputValue(),'');
   await page.goBack();
   await page.waitForSelector('#ranked-search-results .wiki-search-hit');
   assert.equal(await page.locator('#search').inputValue(),'Atbash',
    'Returning to search restores the query that produced those results');

   await page.goto(base+'#/research');
   await page.waitForSelector('#research-query');
   const browse=page.locator('#research-query');
   await browse.fill('LP2-15');
   await page.waitForFunction(()=>location.hash.includes('q=LP2-15'));
   const matching=page.locator('.research-record');
   const count=await matching.count();
   assert(count>0,'The research directory must contain LP2-15 records');
   const record=matching.locator('h2 a').first();
   await record.scrollIntoViewIfNeeded();
   const previousScroll=await page.evaluate(()=>scrollY);
   if(width===320)await record.tap();
   else{await record.focus();await page.keyboard.press('Enter')}
   await page.waitForURL(/#\/experiments\/[^?]+$/);
   await page.waitForSelector('.experiment-article');
   await page.goBack();
   await page.waitForSelector('#research-query');
   assert.equal(await browse.inputValue(),'LP2-15','Browser Back restores the directory query');
   assert.equal(await matching.count(),count,'Browser Back restores the same matching records');
   assert(Math.abs(await page.evaluate(()=>scrollY)-previousScroll)<4,'Browser Back restores the directory scroll position');
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px overflow`);
   if(process.env.SCREENSHOT_PATH&&width===320)await page.screenshot({path:process.env.SCREENSHOT_PATH,fullPage:false});
   await page.close();
  }
  console.log('PASS: mobile drawer-to-search handoff, touch and keyboard suggestions, experiment family activation, and filtered archive return at 320px and 390px.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
