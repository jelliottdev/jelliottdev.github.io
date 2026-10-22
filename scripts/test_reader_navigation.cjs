const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';

(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [320,390,1440]){
   const page=await browser.newPage({viewport:{width,height:844},hasTouch:width<760});
   let heldPage,seenPage;
   const pageRequested=new Promise(resolve=>seenPage=resolve);
   await page.route('**/data/pages/lp2-16.json',route=>{heldPage=route;seenPage()});
   await page.goto(base+'#/reader/lp2-15');
   await page.waitForSelector('#reader-page');
   await page.keyboard.press('ArrowRight');
   await page.waitForURL('**/#/reader/lp2-16');
   await pageRequested;
   await page.keyboard.press('ArrowRight');
   await page.waitForURL('**/#/reader/lp2-17');
   await page.waitForFunction(()=>document.querySelector('#reader-page')?.value==='lp2-17');
   await heldPage.continue();
   assert.equal(await page.locator('#reader-page').inputValue(),'lp2-17',
    'An older delayed page must not replace the latest page');

   let heldImage,seenImage;
   const imageRequested=new Promise(resolve=>seenImage=resolve);
   await page.route('**/images/lp2-18.jpg',route=>{heldImage=route;seenImage()});
   const next=page.locator('.reader-pagination a[aria-label="Next page"]');
   if(width<760)await next.tap();else await next.click();
   await page.waitForFunction(()=>document.querySelector('#reader-page')?.value==='lp2-18');
   await imageRequested;
   assert.equal(await page.locator('#reader-sheet img').getAttribute('alt'),'Original LP2 · Page 18');
   const sheetHeight=await page.locator('#reader-sheet').evaluate(el=>el.getBoundingClientRect().height);
   assert(sheetHeight>50,
    'Image dimensions reserve a tappable page area during the image request');
   await page.locator('.reader-image-loading').waitFor({state:'visible'});
   assert.equal(await page.locator('#reader-sheet').evaluate(el=>el.getBoundingClientRect().height),sheetHeight,
    'Showing the loading status must not move the manuscript sheet');
   const statusBox=await page.locator('.reader-image-loading').boundingBox();
   const imageBox=await page.locator('#reader-sheet').boundingBox();
   assert(statusBox.x>=imageBox.x&&statusBox.x+statusBox.width<=imageBox.x+imageBox.width,
    'Loading status must stay within the image pane');
   assert(statusBox.y>imageBox.y&&statusBox.y+statusBox.height<844,
    `Loading status must be visible without scrolling: ${JSON.stringify({width,statusBox,imageBox})}`);
   if(process.env.SCREENSHOT_PATH&&width===390)await page.screenshot({path:process.env.SCREENSHOT_PATH,fullPage:false});
   if(width<760)await next.tap();else await next.click();
   await page.waitForFunction(()=>document.querySelector('#reader-page')?.value==='lp2-19');
   await heldImage.continue();
   assert.match(await page.locator('#reader-sheet img').getAttribute('src'),/lp2-19\.jpg$/);
   await page.waitForFunction(()=>document.querySelector('#reader-sheet img')?.naturalWidth>0);
   assert.equal(await page.locator('.reader-image-loading').isVisible(),false,
    'A completed old image must not leave a loading state on the new page');

   await page.route('**/images/lp2-20.jpg',route=>route.abort());
   if(width<760)await next.tap();else await next.click();
   await page.waitForFunction(()=>document.querySelector('#reader-page')?.value==='lp2-20');
   await page.locator('.reader-image-error').waitFor({state:'visible'});
   assert.equal(await page.locator('.reader-image-error a').getAttribute('href'),'images/lp2-20.jpg');
   assert.equal(await page.locator('#reader-sheet').isVisible(),false,
    'Failed image must not leave a blank full-height sheet above the recovery link');
   assert.equal(await page.locator('#reader-zoom').isDisabled(),true,
    'Do not offer an enlarge action for an unavailable image');
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px reader overflow`);
   await page.close();
  }
  console.log('PASS: rapid keyboard navigation follows URL during delayed page JSON; slow-image status preserves layout; touch/click pagination and failed-image recovery work at 320px, 390px and 1440px.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
