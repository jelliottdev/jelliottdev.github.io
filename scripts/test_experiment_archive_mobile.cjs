const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
const output=process.env.SCREENSHOT_DIR||path.resolve('..','..','outputs','research-index');
(async()=>{
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try{
    const page=await browser.newPage();
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    for(const width of [320,390,1440]){
      await page.setViewportSize({width,height:860});
      await page.goto(base+'#/experiments');
      await page.waitForSelector('#experiment-query');
      assert.equal(await page.locator('#browse-experiments,#idea-page-one').count(),0);
      await page.getByRole('link',{name:'Browse the research index'}).click();
      await page.waitForSelector('#research-query');
      assert((await page.locator('.research-record').count())<=20);
      assert.equal(await page.locator('.research-records details').count(),0);
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px directory overflow`);
      await page.locator('#research-query').fill('LP2-15');
      assert((await page.locator('.research-record').count())>0);
      await page.locator('#research-sort').selectOption('recent');
      assert(new URL(page.url()).hash.includes('sort=recent'));
      await page.locator('#research-query').fill('no-such-research-fixture');
      await page.getByRole('heading',{name:'No matching research'}).waitFor();
      await page.getByRole('button',{name:'Clear filters'}).click();
      assert.equal(await page.locator('#research-query').inputValue(),'');
      assert.equal(await page.locator('#research-sort').inputValue(),'title');
      await page.screenshot({path:path.join(output,`research-${width}.png`)});
    }
    await page.goto(base+'#/experiments?browse=LP2-15&section=browse-experiments');
    await page.waitForSelector('#research-query');
    assert.equal(await page.locator('#research-query').inputValue(),'LP2-15');
    assert(new URL(page.url()).hash.startsWith('#/research?'));
    await page.locator('.research-record h2 a').first().click();
    await page.waitForSelector('.experiment-finding');
    assert(await page.locator('.experiment-finding').isVisible());
    assert.equal(await page.getByText('Human review is pending').count(),0);
    assert.deepEqual(errors,[]);
    console.log('PASS: focused checker, separate paginated research directory, filtering/reset, recent sort, mobile overflow, legacy links and visible findings.');
  }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
