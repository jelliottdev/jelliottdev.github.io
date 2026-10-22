const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');

const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';

(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [320,390]){
   const page=await browser.newPage({viewport:{width,height:800}});
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   await page.goto(base+'#/wiki/quick-start');
   await page.waitForSelector('.rune-line');
   const loaded=await page.evaluate(async()=>{
    const faces=await document.fonts.load('24px "Liberpedia Runic"','ᚱᛝᛠ');
    return {
     count:faces.length,
     status:faces.map(face=>face.status),
     family:getComputedStyle(document.querySelector('.rune-line')).fontFamily,
     requested:performance.getEntriesByType('resource').some(entry=>entry.name.includes('/fonts/NotoSansRunic-Regular.ttf')),
     overflow:document.documentElement.scrollWidth>innerWidth,
    };
   });
   assert.equal(loaded.count,1,`${width}px: bundled font face unavailable`);
   assert.deepEqual(loaded.status,['loaded']);
   assert.match(loaded.family,/Liberpedia Runic/);
   assert(loaded.requested,`${width}px: local font file was not requested`);
   assert(!loaded.overflow,`${width}px: page overflows horizontally`);
   await page.goto(base+'#/reader/lp2-15');
   await page.getByRole('button',{name:'Text',exact:true}).click();
   const reader=await page.locator('#reader-text').evaluate(element=>({
    family:getComputedStyle(element).fontFamily,
    rune:element.textContent.includes('ᚠ'),
   }));
   assert.match(reader.family,/Liberpedia Runic/);
   assert(reader.rune,`${width}px: reader has no manuscript runes`);
   assert.deepEqual(errors,[]);
   if(process.env.RUNE_FONT_SCREENSHOT){
    await page.screenshot({path:process.env.RUNE_FONT_SCREENSHOT.replace('.png',`-${width}.png`),fullPage:true});
   }
  }
  console.log('PASS: bundled rune font loaded on 320px and 390px pages.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
