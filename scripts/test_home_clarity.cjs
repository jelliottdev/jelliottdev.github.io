const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.goto(base+'#/overview');
  await page.waitForSelector('.home-task-links');
  assert.equal(await page.locator('.home-start a').count(),2);
  assert.equal(await page.locator('.feature-entry').count(),3);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  if(process.env.HOME_SCREENSHOT)await page.screenshot({path:process.env.HOME_SCREENSHOT,fullPage:true});
  await page.goto(base+'#/wiki/quick-start');
  await page.waitForSelector('#first-reading');
  assert((await page.locator('.wiki-article h2').first().innerText()).includes('Try one reading'));
  assert.equal(await page.locator('.quick-start-next:not([open])').count(),2);
  await page.setViewportSize({width:900,height:900});
  assert(await page.locator('.mobile-article-contents').isVisible());
  await page.goto(base+'#/does-not-exist');
  await page.waitForSelector('h1');
  assert.equal(await page.locator('h1').innerText(),'Page not found');
  const failed=await browser.newPage();
  await failed.route('**/data/index.json',route=>route.fulfill({status:503,body:'Unavailable'}));
  await failed.goto(base+'#/overview');
  await failed.waitForSelector('.error');
  assert(await failed.getByRole('link',{name:'static reference index'}).isVisible());
  console.log('PASS: focused home, early reading exercise, tablet contents, not-found and loading fallback.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
