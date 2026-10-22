const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';

(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:500}});
  await page.goto(base+'#/reader/lp2-15');
  await page.waitForSelector('#reader-page');
  await page.locator('[data-reader-view="text"]').click();
  await page.locator('#reader-mode').selectOption('latin');
  await page.locator('#reader-size').fill('25');
  await page.evaluate(()=>scrollTo(0,720));
  await page.waitForTimeout(80);
  const textPosition=await page.evaluate(()=>scrollY);
  assert(textPosition>500,'text has a useful scroll position');
  await page.locator('[data-reader-view="image"]').click();
  await page.evaluate(()=>scrollTo(0,180));
  await page.waitForTimeout(80);
  const imagePosition=await page.evaluate(()=>scrollY);
  assert(imagePosition>90,'image has a separate scroll position');
  await page.locator('[data-reader-view="text"]').click();
  await page.waitForTimeout(80);
  assert(Math.abs((await page.evaluate(()=>scrollY))-textPosition)<80,'switching restores text position');
  await page.reload();
  await page.waitForSelector('#reader-page');
  await page.waitForTimeout(100);
  assert.equal(await page.locator('.reader-workspace').getAttribute('data-view'),'text');
  assert.equal(await page.locator('#reader-mode').inputValue(),'latin');
  assert.equal(await page.locator('#reader-size').inputValue(),'25');
  assert(Math.abs((await page.evaluate(()=>scrollY))-textPosition)<80,'reload restores reading position');
  await page.locator('[data-reader-view="image"]').click();
  await page.waitForTimeout(80);
  assert(Math.abs((await page.evaluate(()=>scrollY))-imagePosition)<80,'reload retains image position');
  assert.match(page.url(),/#\/reader\/lp2-15\?view=image$/,'view is shareable');
  await page.close();

  const tablet=await browser.newPage({viewport:{width:1200,height:800}});
  await tablet.goto(base+'#/reader/lp2-15?view=compare');
  await tablet.waitForSelector('#reader-page');
  assert.equal(await tablet.locator('.reader-workspace').getAttribute('data-view'),'compare');
  await tablet.setViewportSize({width:950,height:800});
  await tablet.waitForFunction(()=>document.querySelector('.reader-workspace')?.dataset.view==='image');
  assert.match(tablet.url(),/#\/reader\/lp2-15\?view=image$/,'narrow content updates the shared view');
  await tablet.close();
  console.log('PASS: reader restores independent image/text positions, text version and size; shared view follows available content width.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
