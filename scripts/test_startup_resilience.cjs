const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';

(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const cases=[
   {asset:'data/topics.json',path:'topics',fallback:'The topic index',healthy:'pages',notice:'search/Atbash',schema:true},
   {asset:'data/evidence/reading-methods.json',path:'readings',notice:'readings',healthy:'page/lp1-01'},
   {asset:'data/evidence/spelling-sums.json',path:'spelling',fallback:'The spelling reference',healthy:'pages'},
   {asset:'data/article-search.json',path:'wiki',fallback:'Guides',healthy:'page/lp1-01',notice:'search/Atbash'},
   {asset:'data/evidence/embedded-payloads.json',path:'reader/lp1-00',notice:'reader/lp1-00',healthy:'page/lp1-01'},
   {asset:'data/guide-categories.json',path:'wiki',healthy:'wiki/quick-start'}
  ];
  for(const item of cases){
   const page=await browser.newPage();
   const errors=[];
   page.on('pageerror',error=>errors.push(error.message));
   await page.route('**/'+item.asset,route=>route.fulfill({status:503,body:'Unavailable'}));
   await page.goto(base+'#/overview');
   await page.waitForSelector('.home-task-links');
   assert.equal(await page.locator('.error').count(),0,`${item.asset}: homepage remains usable`);
   await page.goto(base+'#/'+item.path);
   await page.waitForFunction(()=>!document.querySelector('#main .loading'));
   if(item.fallback){
    assert((await page.locator('#main').innerText()).includes(item.fallback),`${item.asset}: affected section explained`);
    assert(await page.getByRole('link',{name:'Open the static reference'}).isVisible(),`${item.asset}: static fallback`);
   }else{
    assert.equal(await page.locator('#main .error').count(),0,`${item.asset}: route remains usable`);
   }
   if(item.notice){
    await page.goto(base+'#/'+item.notice);
    await page.waitForSelector('.data-notice');
    assert((await page.locator('.data-notice').innerText()).includes('temporarily unavailable'),`${item.asset}: omission disclosed`);
   }
   await page.goto(base+'#/'+item.healthy);
   await page.waitForFunction(()=>!document.querySelector('#main .loading'));
   assert.equal(await page.locator('#main .error').count(),0,`${item.asset}: unrelated route remains usable`);
   assert.deepEqual(errors,[],`${item.asset}: no uncaught browser errors`);
   await page.close();
  }
  const bad=await browser.newPage();
  await bad.route('**/data/topics.json',route=>route.fulfill({json:{unexpected:true}}));
  await bad.goto(base+'#/topics');
  await bad.waitForSelector('#main .error');
  assert((await bad.locator('#main').innerText()).includes('The topic index'));
  await bad.close();
  const stalled=await browser.newPage();
  await stalled.route('**/data/topics.json',()=>{}); // Leave the request unanswered.
  const started=Date.now();
  await stalled.goto(base+'#/overview');
  await stalled.waitForSelector('.home-task-links',{timeout:8000});
  assert(Date.now()-started<7500,'an optional request has a bounded startup wait');
  await stalled.goto(base+'#/topics');
  await stalled.waitForSelector('#main .error');
  assert((await stalled.locator('#main').innerText()).includes('The topic index'));
  await stalled.close();
  const core=await browser.newPage();
  await core.route('**/data/index.json',route=>route.fulfill({status:503,body:'Unavailable'}));
  await core.goto(base+'#/overview');
  await core.waitForSelector('#main .error');
  assert(await core.getByRole('link',{name:'static reference index'}).isVisible());
  await core.close();
  console.log('PASS: essential and optional startup failures stay within their actual scope.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
