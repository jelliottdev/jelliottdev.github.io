const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.WIKI_BASE_URL||'http://127.0.0.1:8765/';
const root=path.join(__dirname,'..');
(async()=>{
 const ledger=JSON.parse(fs.readFileSync(path.join(root,'exports/fibonacci-prime-panel.json'),'utf8')).rows;
 const browser=await chromium.launch({channel:'msedge',headless:true});
 for(const width of [320,390,1280]){
  const page=await browser.newPage({viewport:{width,height:900}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(base+'#/wiki/lp2-15-panel?section=construction');
  await page.locator('.fib-panel-live:not([hidden])').waitFor();
  const cells=await page.locator('.fib-panel-cell').evaluateAll(nodes=>nodes.map(node=>({step:Number(node.dataset.step),printed:Number(node.querySelector('strong').textContent)})));
  assert.equal(cells.length,16);
  for(const item of ledger)assert.equal(cells.find(cell=>cell.step===item.step)?.printed,item.printed);
  assert.equal(await page.locator('.fib-panel-fallback').isVisible(),false);
  await page.locator('.fib-panel-cell[data-step="15"]').click();
  assert.match(await page.locator('.fib-panel-reading').innerText(),/4507.*1206/s);
  assert.match(await page.locator('.fib-panel-reading').innerText(),/signed difference is -1206/);
  await page.locator('[data-fib-next]').click();
  assert.match(await page.locator('.fib-panel-reading').innerText(),/7817.*4516/s);
  assert.equal(await page.locator('[data-fib-next]').isDisabled(),true);
  await page.locator('.fib-panel-controls input').focus();
  await page.keyboard.press('ArrowLeft');
  assert.match(await page.locator('.fib-panel-reading').innerText(),/Step 15 of 16/);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px horizontal overflow`);
  assert.deepEqual(errors,[]);
  if(width===390&&process.env.FIB_SCREENSHOT)await page.locator('#fib-panel').screenshot({path:process.env.FIB_SCREENSHOT});
  await page.close();
 }
 assert(fs.readFileSync(path.join(root,'reference/articles/lp2-15-panel.html'),'utf8').includes('exports/fibonacci-prime-panel.svg'),'Static export retains the diagram');
 await browser.close();
 console.log('PASS: sixteen source values, spiral controls, keyboard navigation, static fallback and 320/390/1280px layout.');
})().catch(error=>{console.error(error);process.exit(1)});
