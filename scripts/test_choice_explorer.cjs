const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.goto(base+'#/wiki/search-space');
  await page.waitForSelector('.choice-explorer-live:not([hidden])');
  assert.equal(await page.locator('#choice-total').innerText(),'58 configurations');
  await page.locator('#choice-pages').fill('4');
  await page.locator('#choice-offsets').fill('3');
  assert.equal(await page.locator('#choice-total').innerText(),'696 configurations');
  assert.equal(await page.locator('#choice-step-shifts').innerText(),'232');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.goto(base+'#/wiki/search-space?section=count');
  await page.waitForSelector('.choice-explorer-live:not([hidden])');
  assert.equal(await page.locator('#choice-total').innerText(),'58 configurations');
  console.log('PASS: choice explorer updates cumulative bounds and stays within mobile viewport.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
