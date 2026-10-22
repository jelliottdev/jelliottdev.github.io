const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.goto(base+'#/overview');
  await page.waitForFunction(()=>!document.querySelector('.loading'));
  await page.locator('#menu').click();
  assert(await page.locator('#sidebar .mobile-nav').isVisible());
  assert(!await page.locator('#sidebar .desktop-nav').isVisible());
  assert.equal(await page.locator('#sidebar .mobile-nav > a, #sidebar .mobile-nav > details').count(),6);
  if(process.env.MENU_SCREENSHOT)await page.screenshot({path:process.env.MENU_SCREENSHOT});
  await page.locator('#sidebar .mobile-nav summary').filter({hasText:'Research'}).click();
  const research=page.locator('#sidebar .mobile-nav details').filter({hasText:'Research'});
  assert(await research.locator('a[href="#/experiments"]').isVisible());
  await research.locator('a[href="#/experiments"]').click();
  await page.waitForURL('**/#/experiments');
  assert.equal(await page.locator('#menu').getAttribute('aria-expanded'),'false');
  await page.locator('#menu').click();
  assert(await research.isVisible());
  assert(await research.evaluate(el=>el.open));
  assert.equal(await research.locator('a[href="#/experiments"]').getAttribute('aria-current'),'page');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#menu').getAttribute('aria-expanded'),'false');
  console.log('PASS: short mobile navigation, grouped destinations, route handoff and Escape.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
