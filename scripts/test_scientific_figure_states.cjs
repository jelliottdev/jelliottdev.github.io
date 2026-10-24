/* Source-data-backed interactive figure state tests. No browser or inference. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..');
const read=file=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const affine=read('experiments/records/word-internal-affine-lags/results.json');
const blocks=read('experiments/records/block-boundary-doublets/results.json');
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const timers=new Map();let timerId=0;
const context={esc,AbortController,document:{body:{},activeElement:null},
 setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++timerId,fn);return timerId},clearTimeout(id){timers.delete(id)}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
function element(value=''){
 return {value,disabled:false,hidden:false,innerHTML:'',textContent:'',listeners:{},focus(){context.document.activeElement=this},
 addEventListener(type,fn){(this.listeners[type]??=[]).push(fn)},async fire(type){for(const fn of this.listeners[type]||[])await fn()}};
}
function figure(kind){
 const controls=[element(),element()],readout=element(),retry=element();retry.hidden=true;
 const selectors={'.affine-lag-readout':readout,'[data-figure-retry]':retry};
 const names=kind==='affine'?['[data-affine-a]','[data-affine-b]']:['[data-block-size]','[data-block-phase]'];
 names.forEach((name,n)=>selectors[name]=controls[n]);
 return {kind,controls,readout,retry,isConnected:true,dataset:{results:kind},querySelector:name=>selectors[name]};
}
const bind=f=>{context.main={querySelector:()=>f};return f.kind==='affine'?context.bindAffineLagFigure():context.bindBlockBoundaryFigure()};
const saved=f=>f.kind==='affine'?affine:blocks;
const deferred=()=>{let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve}};
const okay=data=>({ok:true,json:async()=>data});
async function recovery(kind){
 const f=figure(kind);let calls=0;context.fetch=async()=>{calls++;return {ok:false}};
 await bind(f);
 assert(f.controls.every(c=>c.disabled),'Failed figures have no enabled dead controls');
 assert(f.readout.textContent.includes('could not load'));assert.equal(f.retry.hidden,false);assert.equal(f.retry.disabled,false);
 assert(f.controls.every(c=>!c.listeners.change),'A failed load binds no change handlers');
 const request=deferred();context.fetch=()=>{calls++;return request.promise};context.document.activeElement=f.retry;
 const retry=f.retry.fire('click');
 assert(f.controls.every(c=>c.disabled));assert.equal(f.retry.disabled,true);assert.equal(f.retry.hidden,false);
 assert(f.readout.textContent.includes('Loading'));
 await f.retry.fire('click');assert.equal(calls,2,'Repeated clicks cannot start duplicate requests');
 request.resolve(okay(saved(f)));await retry;
 assert(f.controls.every(c=>!c.disabled));assert.equal(f.retry.hidden,true);
 assert.equal(context.document.activeElement,f.controls[0],'Successful keyboard retry returns focus to an enabled control');
 assert(f.controls.every(c=>c.listeners.change.length===1));
 if(kind==='affine'){
  assert(f.readout.innerHTML.includes('77 matching pairs'));
  const mean=affine.affine_family.word_shuffle_expected_by_a_b[27][24].toFixed(1);
  assert(f.readout.innerHTML.includes('Average after shuffling within words: '+mean));
  f.controls[0].value='0';f.controls[1].value='0';await f.controls[0].fire('change');
  assert(f.readout.innerHTML.includes('Actual text: '+affine.affine_family.counts_by_a_b[0][0]+' matching pairs'));
  assert(!f.readout.innerHTML.includes('Only <strong>3 of 2,000</strong>'),'Selected-rule qualification is not attached to a different formula');
 }else{
  f.controls[0].value='2';await f.controls[0].fire('change');f.controls[1].value='0';await f.controls[1].fire('change');
  const row=blocks.all_placements.find(r=>r.size===2&&r.phase===0);
  assert.equal(row.matches,51);assert.equal(blocks.doublet_count,86);
  assert(f.readout.innerHTML.includes('<strong>51 doublets</strong>'));
  assert(f.readout.innerHTML.includes('of 86 on these edges'));
  assert(f.readout.innerHTML.includes('width:'+((51/86)*100).toFixed(1)+'%'),'Bar uses all86 doublets, rather than saturating at30');
  f.controls[1].value='1';await f.controls[1].fire('change');
  assert(f.readout.innerHTML.includes('width:'+((35/86)*100).toFixed(1)+'%'),'Different source counts retain different proportions');
  f.controls[0].value='5';await f.controls[0].fire('change');f.controls[1].value='4';await f.controls[1].fire('change');
  f.controls[0].value='2';await f.controls[0].fire('change');assert.equal(f.controls[1].value,'0','An unavailable phase resets to a valid phase');
 }
}
async function stale(kind,fail){
 const f=figure(kind),request=deferred();context.fetch=()=>request.promise;
 const pending=bind(f);assert(f.controls.every(c=>c.disabled));
 const oldText=f.readout.textContent;f.isConnected=false;
 const newer=figure(kind);newer.readout.textContent='New route';context.main={querySelector:()=>newer};
 request.resolve(fail?{ok:false}:okay(saved(f)));await pending;
 assert.equal(f.readout.textContent,oldText);assert.equal(f.readout.innerHTML,'');
 assert.equal(newer.readout.textContent,'New route');assert.equal(newer.readout.innerHTML,'');
 assert(f.controls.every(c=>!c.listeners.change),'A stale completion attaches no listeners');
}
async function timeout(kind,bodyOnly){
 const f=figure(kind),stalled=deferred();let signal;
 context.fetch=(url,options)=>{signal=options.signal;return bodyOnly?Promise.resolve({ok:true,json:()=>stalled.promise}):stalled.promise};
 const pending=bind(f);assert.equal(timers.size,1);[...timers.values()][0]();await pending;
 assert(signal.aborted);assert.equal(timers.size,0);assert.equal(f.retry.hidden,false);assert.equal(f.retry.disabled,false);
 assert(f.controls.every(c=>c.disabled),'Timed-out figures expose retry rather than dead selectors');
 context.fetch=async()=>okay(saved(f));context.document.activeElement=f.retry;await f.retry.fire('click');
 const recovered=f.readout.innerHTML;assert(f.controls.every(c=>!c.disabled));assert.equal(f.retry.hidden,true);
 stalled.resolve(bodyOnly?{}:okay({}));await new Promise(resolve=>setImmediate(resolve));
 assert.equal(f.readout.innerHTML,recovered,'Late timed-out response/body cannot replace a successful retry');
 assert(f.controls.every(c=>c.listeners.change.length===1),'Late completion cannot attach duplicate handlers');
 assert.equal(timers.size,0);
}
const guard=setTimeout(()=>{console.error('Figure lifecycle test did not finish');process.exitCode=1},5000);
(async()=>{
 for(const kind of ['affine','block']){
  await recovery(kind);await stale(kind,false);await stale(kind,true);
  await timeout(kind,false);await timeout(kind,true);
  const retryFigure=figure(kind);context.fetch=async()=>({ok:false});await bind(retryFigure);
  const retryRequest=deferred();context.fetch=()=>retryRequest.promise;context.document.activeElement=retryFigure.retry;
  const retryPending=retryFigure.retry.fire('click');context.document.activeElement=context.document.body;
  retryRequest.resolve({ok:false});await retryPending;
  assert.equal(context.document.activeElement,retryFigure.retry,'A failed keyboard retry restores its re-enabled action if focus fell to the body');
  const nextRequest=deferred();context.fetch=()=>nextRequest.promise;const nextPending=retryFigure.retry.fire('click');
  const elsewhere=element();context.document.activeElement=elsewhere;nextRequest.resolve(okay(saved(retryFigure)));await nextPending;
  assert.equal(context.document.activeElement,elsewhere,'A completed retry does not steal focus from a user who moved elsewhere');
  const f=figure(kind);context.fetch=async()=>okay(kind==='affine'?{affine_family:{counts_by_a_b:Array(29).fill([]),word_shuffle_expected_by_a_b:Array(29).fill([])}}:{...blocks,doublet_count:0});
  await bind(f);assert(f.controls.every(c=>c.disabled));assert.equal(f.retry.hidden,false);
  assert(f.controls.every(c=>!c.listeners.change),'Malformed payloads fail before handlers are attached');
 }
 for(const [id,asset] of [['word-internal-affine-lags','comparison.svg'],['block-boundary-doublets','boundaries.svg']]){
  const html=context.experimentVisual({id},{path:'experiments/records/'+id+'/'+asset});
  assert(html.includes('data-figure-retry hidden'));assert.equal((html.match(/<select [^>]+ disabled>/g)||[]).length,2);
  assert(html.includes('role="status"'));
 }
 console.log('PASS: actual saved counts,51/86 bar scale, controls/loading/error/retry, valid phase changes, malformed data and stale navigation. DOM stubs do not verify rendering.');
})().catch(error=>{console.error(error);process.exitCode=1}).finally(()=>clearTimeout(guard));
