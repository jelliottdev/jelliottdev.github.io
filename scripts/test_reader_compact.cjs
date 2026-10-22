const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
const output=process.env.SCREENSHOT_DIR||path.resolve('..','..','outputs','reader-compact');
const sizes=[[320,720],[360,780],[390,844],[430,932],[667,375],[768,1024],[1024,768]];

(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const [width,height] of sizes){
   const page=await browser.newPage({viewport:{width,height},hasTouch:width<=760});
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   await page.goto(base+'#/reader/lp2-15');
   await page.waitForSelector('#reader-page');
   assert.equal(await page.locator('#reader-page').inputValue(),'lp2-15');
   const image=page.locator('#reader-sheet');
   const imageTop=(await image.boundingBox()).y;
   if(width<=360&&height>500)assert(imageTop<270,`${width}px image starts too low: ${imageTop}`);
   if(width>=390&&width<=760)assert(imageTop<225,`${width}px image starts too low: ${imageTop}`);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px reader overflow`);
   await page.screenshot({path:path.join(output,`reader-${width}x${height}.png`)});
   if(width<=760){
    const search=page.locator('#reader-search-toggle');
    assert(await search.isVisible());
    await search.click();
    assert(await page.locator('#search').isVisible());
    assert.equal(await page.locator('#search').evaluate(el=>document.activeElement===el),true);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#search').isVisible(),false);
    assert.equal(await search.getAttribute('aria-expanded'),'false');
    if(width===320){
     await page.locator('#reader-zoom').click();
     assert(await page.locator('#image-dialog').isVisible());
     for(const id of ['zoom-out','zoom-in','fit','fit-width','close-viewer']){
      const box=await page.locator('#'+id).boundingBox();
      assert(box.height>=44,`${id} touch target too short: ${box.height}`);
     }
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'viewer overflow');
     await page.screenshot({path:path.join(output,'viewer-320x720.png')});
     await page.locator('#close-viewer').click();
     await page.locator('[data-reader-view="text"]').click();
     assert(await page.locator('.manuscript-text').isVisible());
     await page.locator('[data-reader-view="image"]').click();
     assert(await image.isVisible());
    }
   }
   assert.deepEqual(errors,[]);
   await page.close();
  }
  console.log('PASS: compact reader at 320/360/390/430 portrait, short landscape, 768/1024 tablets; search, tabs, viewer targets and overflow.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
