const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
const output=process.env.SCREENSHOT_DIR||path.resolve('..','..','outputs','catalogue-mobile');

(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [320,390,768]){
   const page=await browser.newPage({viewport:{width,height:800},hasTouch:width<768});
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   await page.goto(base+'#/pages');
   await page.waitForSelector('.catalogue-item');
   assert.equal(await page.locator('.catalogue-item').count(),75);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px catalogue overflow`);
   await page.screenshot({path:path.join(output,`pages-${width}.png`)});
   await page.locator('#page-query').fill('LP2-15');
   assert.equal(await page.locator('.catalogue-item').count(),1);
   assert((await page.locator('.catalogue-item').first().innerText()).includes('LP2 · Page 15'));
   await page.locator('.catalogue-item h3 a').click();
   assert(page.url().includes('#/page/lp2-15'));
   await page.goto(base+'#/readings');
   await page.waitForSelector('.reading-index-item');
   assert.equal(await page.locator('.reading-index-item').count(),9);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px readings overflow: ${JSON.stringify(await page.evaluate(()=>[...document.querySelectorAll('main *')].map(el=>({tag:el.tagName,cls:el.className,right:Math.round(el.getBoundingClientRect().right)})).filter(item=>item.right>innerWidth).slice(0,10)))}`);
   await page.screenshot({path:path.join(output,`readings-${width}.png`)});
   const firstLink=page.locator('.reading-index-item h2 a').first();
   assert((await firstLink.boundingBox()).height>=44);
   assert.deepEqual(errors,[]);
   await page.close();
  }
  console.log('PASS: catalogue and known readings at 320, 390, and 768px; links, search, touch targets, no horizontal overflow.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
