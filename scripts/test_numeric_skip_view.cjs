/* Actual search/step receipts and production lifecycle; no solver, browser or network. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ids=['numeric-stream-skip-grid','artifact-stream-skip-grid','fibonacci-stream-skip-grid'],api=require('../numeric-skip-view.js'),fixtures={};
for(const id of ids){
 const base='experiments/records/'+id+'/',artifact=id===ids[1],fib=id===ids[2],planName=id===ids[0]?'frozen-plan.json':'plan.json';
 const record=read(base+'record.json'),plan=read(base+planName),results=read(base+'results.json'),receipt=artifact?read(base+'figure-receipt.json'):undefined;
 const controlPath=fib?'preflight-independent-check.json':artifact?'control/summary.json':'controls/summary.json',control=read(base+controlPath);
 fixtures[id]={record,plan,results,receipt,control,payloads:{[base+planName]:plan,[base+'results.json']:results,[base+controlPath]:control,...(artifact?{[base+'figure-receipt.json']:receipt}:{})}};
 const data=api.validate(id,plan,results,receipt,control),html=api.content(data);
 assert.equal(data.screens,fib?92510:artifact?23100:36300);assert.equal(data.full,fib?900:artifact?194:322);assert.equal(data.passes,0);
 for(const count of [data.screens,data.full,data.passes])assert(html.includes('<strong>'+count.toLocaleString('en-US')+'</strong>'));
 assert.equal((html.match(/numeric-skip-stages/g)||[]).length,1);assert(html.includes('First 50-rune checks'));assert(html.includes('Complete-page checks'));assert(html.includes('Passed the fixed English-score test'));
 assert(html.includes(data.best.score.toFixed(3).replace('-','−')));assert(html.includes('−5.5'));assert(html.includes('score alone cannot confirm plaintext'));
 const expectedControl=fib?{total:841,exact:805}:artifact?{total:420,exact:402}:{total:660,exact:634};
 assert.equal(data.controls.total,expectedControl.total);assert.equal(data.controls.exact,expectedControl.exact);assert.equal(data.controls.score,expectedControl.total);
 const actualControl=fib?control:control.branches[artifact?'numeric2A':'numeric'];
 assert.equal(data.controls.exact,actualControl.exact_complete_recovery);
 assert.equal(data.controls.score,fib?actualControl.score_gate_passes:actualControl.full_gate_pass);
 assert(html.includes('Correct reading recovered'));assert(html.includes('Passed the English-score test'));
 assert(html.includes(`<strong>${expectedControl.exact} / ${expectedControl.total}</strong>`));
 assert(html.includes(`<strong>${expectedControl.total} / ${expectedControl.total}</strong>`));
 assert(html.includes((expectedControl.total-expectedControl.exact)+' incorrect outputs still passed'));
 assert(html.includes('not independent success probabilities'));
 assert(JSON.stringify(control).length<25000,'Only compact receipts are used, never full control traces');
 assert(api.canRender(record,record.visuals[0]));assert(api.render(id).includes('download>Download the original SVG'));
 const missing=structuredClone(record);missing.reproduction.outputs=missing.reproduction.outputs.filter(f=>!f.path.endsWith('results.json'));assert(!api.canRender(missing,record.visuals[0]));
 const unlistedControl=structuredClone(record);for(const group of ['inputs','outputs'])unlistedControl.reproduction[group]=unlistedControl.reproduction[group].filter(f=>f.path!==base+controlPath);assert(!api.canRender(unlistedControl,record.visuals[0]),'A compact receipt must be explicitly declared');
 if(artifact){
  assert(html.includes('Puzzle numbers and sequences: search results'),'The heading covers mathematical sequences as well as puzzle-derived values');
  assert(!html.includes('Artifact keys:'),'The old heading understated this stream catalog');
  const byRune=new Map(read('data/index.json').alphabet.map(a=>[a.rune,a.index]));
  const ciphertext=[...read('data/pages/lp2-49.json').raw].filter(r=>byRune.has(r)).map(r=>byRune.get(r));
  assert.equal(ciphertext[receipt.rune_position_zero_based-1],receipt.previous_transformed_cipher_index);
  assert.equal(ciphertext[receipt.rune_position_zero_based],receipt.current_transformed_cipher_index);
  assert.equal(results.best_full.full_indices[receipt.rune_position_zero_based],receipt.candidate_plain_index);
  assert.equal((receipt.candidate_plain_index-receipt.rejected_key_value+29)%29,ciphertext[28]);
  assert.equal((receipt.candidate_plain_index-receipt.accepted_key_value+29)%29,ciphertext[29]);
  assert(html.includes('28 − 2 = 26 (mod 29)'));assert(html.includes('28 − 3 = 25 (mod 29)'));assert(html.includes('same candidate rune again'));assert(html.includes('not confirmed plaintext'));
  const wrong=structuredClone(receipt);wrong.rejected_key_value=1;assert.throws(()=>api.validate(id,plan,results,wrong,control));
 }else if(fib){
  assert.equal(results.source_labeled_screens,10*data.screens);assert(html.includes('925,100'));assert(html.includes('not extra tests'));
  assert(!html.includes('numeric-skip-step'),'Fibonacci summary does not invent an alias/skip demonstration');
 }else{
  assert.equal(results.stream_logs.reduce((n,row)=>n+row.screens,0),data.screens);
  assert.equal(results.stream_logs.reduce((n,row)=>n+row.full_survivors,0),data.full);
  assert(!html.includes('numeric-skip-step'),'Numeric results do not invent a skip trace');
 }
 const bad=structuredClone(results);if(fib)bad.canonical_full_confirmations++;else if(artifact)bad.source_gate_passes=1;else bad.full_survivors++;assert.throws(()=>api.validate(id,plan,bad,receipt,control));
 assert.throws(()=>api.validate(id,plan,results,receipt,{}),'Missing compact control metrics fail safely');
 const badControl=structuredClone(control);if(fib)badControl.score_gate_passes--;else badControl.branches[artifact?'numeric2A':'numeric'].exact_complete_recovery++;assert.throws(()=>api.validate(id,plan,results,receipt,badControl));
}
for(const [id,planName,svg,controlName,counts] of [
 ['payload-phase-skip-grid','frozen-plan.json','payload-phases.svg','frozen-plan.json',[30112,234,1616,1540]],
 ['page-number-prime-skip-grid','plan.json','page-ramp-search.svg','control-check.json',[660,7,112,98]]
]){
 const base='experiments/records/'+id+'/',record=read(base+'record.json'),plan=read(base+planName),results=read(base+'results.json'),control=read(base+controlName),receipt=id.startsWith('page-')?read(base+'figure-receipt.json'):undefined;
 fixtures[id]={record,plan,results,control,receipt,payloads:{[base+planName]:plan,[base+'results.json']:results,[base+controlName]:control,...(receipt?{[base+'figure-receipt.json']:receipt}:{})}};
 ids.push(id);const data=api.validate(id,plan,results,receipt,control),html=api.content(data);
 assert.deepEqual([data.screens,data.full,data.controls.total,data.controls.exact],counts);assert.equal(data.controls.score,counts[2]);assert.equal(data.passes,0);
 assert(api.canRender(record,record.visuals.find(v=>v.path===base+svg)));assert(html.includes('Correct reading recovered'));assert(html.includes('not independent success probabilities'));
 const invalid=structuredClone(control);if(receipt)invalid.exact_recoveries++;else invalid.control_decision.exact_full++;assert.throws(()=>api.validate(id,plan,results,receipt,invalid));
 if(receipt){
  const byRune=new Map(read('data/index.json').alphabet.map(a=>[a.rune,a.index]));
  const c=[...read('data/pages/lp2-39.json').raw].filter(r=>byRune.has(r)).map(r=>28-byRune.get(r));
  assert.equal(c[104],19);assert.equal(c[105],20);assert.equal((c[104]-c[105]+29)%29,28);
  assert(html.includes('(19 \u2212 20) mod 29 = 28'));assert(html.includes('104 to 106'));assert(html.includes('not confirmed plaintext'));
  const bad=structuredClone(receipt);bad.signed_slope=1;assert.throws(()=>api.validate(id,plan,results,bad,control));
 }
}
assert.throws(()=>api.render('fibonacci-streams'),'No unapproved record/payload is supported');
const integrated={esc:String,NumericSkipView:api};vm.createContext(integrated);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),integrated);
for(const f of Object.values(fixtures))assert(integrated.experimentVisual(f.record,f.record.visuals[0]).includes('data-skip-study'));
delete integrated.NumericSkipView;assert(integrated.experimentVisual(fixtures[ids[0]].record,fixtures[ids[0]].record.visuals[0]).includes('<img'));
const css=fs.readFileSync(path.join(root,'style.css'),'utf8'),stageRule=css.match(/\.numeric-skip-stages li\{([^}]+)\}/)?.[1]||'';
assert(css.includes('.numeric-skip-view p{font-size:16px'));assert(stageRule.includes('grid-template-columns:minmax(0,1fr) auto'));assert(stageRule.includes('font-size:16px'));assert(css.includes('.numeric-skip-view [data-skip-retry][hidden]{display:none}'));
const source=fs.readFileSync(path.join(root,'numeric-skip-view.js'),'utf8');
function runtime(){const timers=new Map();let id=0;const c={module:{exports:{}},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++id,fn);return id},clearTimeout(id){timers.delete(id)}};vm.createContext(c);vm.runInContext(source,c);return {api:c.module.exports,timers};}
function harness(id,run=runtime()){
 const doc={body:{},activeElement:null},requests=[];
 const node=()=>({textContent:'',innerHTML:'',hidden:false,disabled:false,listeners:{},addEventListener(type,fn){this.listeners[type]=fn},focus(options){doc.activeElement=this;this.focusOptions=options}});
 const status=node(),retry=node(),view=node(),heading=node();retry.hidden=true;view.querySelector=()=>heading;
 const nodes={'[data-skip-status]':status,'[data-skip-retry]':retry,'[data-skip-content]':view};
 const figure={dataset:{skipStudy:id},ownerDocument:doc,isConnected:true,querySelector:s=>nodes[s]};let current=true;
 const options={isCurrent:()=>current,fetcher:(url,options)=>new Promise((resolve,reject)=>requests.push({url,signal:options.signal,resolve,reject}))};
 const respond=(offset=0,invalid=false)=>requests.slice(offset).forEach(r=>{assert(Object.hasOwn(fixtures[id].payloads,r.url),'Only the current declared fixed payload paths can be fetched');r.resolve({ok:true,json:async()=>invalid?{}:fixtures[id].payloads[r.url]})});
 return {...run,id,figure,status,retry,view,heading,doc,requests,options,respond,leave(){current=false}};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const sharedRun=runtime(),first=harness(ids[0],sharedRun),second=harness(ids[1],sharedRun);
 const a=first.api.bind(first.figure,first.options),b=second.api.bind(second.figure,second.options);
 assert.equal(first.requests.length,3);assert.equal(second.requests.length,4,'Different studies cannot share the wrong cache');
 const twin=harness(ids[0],sharedRun),same=twin.api.bind(twin.figure,twin.options);assert.equal(twin.requests.length,0);
 first.respond();second.respond();await Promise.all([a,b,same]);assert(first.view.innerHTML.includes('36,300'));assert(second.view.innerHTML.includes('23,100'));assert.equal(sharedRun.timers.size,0);
 const warm=harness(ids[1],sharedRun);await warm.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0);
 for(const id of ids){
  const brokenReceipt=harness(id),receiptLoad=brokenReceipt.api.bind(brokenReceipt.figure,brokenReceipt.options);
  const receiptRequests=brokenReceipt.requests.length;
  for(const request of brokenReceipt.requests)request.resolve({ok:true,json:async()=>/summary\.json$|preflight-independent-check\.json$|control-check\.json$|payload-phase-skip-grid\/frozen-plan\.json$/.test(request.url)?{}:fixtures[id].payloads[request.url]});
  await receiptLoad;assert(!brokenReceipt.retry.hidden);assert.equal(brokenReceipt.view.innerHTML,'','An invalid compact receipt cannot display misleading control counts');
  const receiptRetry=brokenReceipt.retry.listeners.click();brokenReceipt.respond(receiptRequests);await receiptRetry;assert(brokenReceipt.retry.hidden);assert(brokenReceipt.view.innerHTML.includes('Correct reading recovered'));
  const fail=harness(id),start=fail.api.bind(fail.figure,fail.options);fail.respond(0,true);await start;
  assert(!fail.retry.hidden);assert.equal(fail.view.innerHTML,'');assert(fail.status.textContent.includes('download'));
  fail.doc.activeElement=fail.retry;const n=fail.requests.length,retry=fail.retry.listeners.click();await fail.retry.listeners.click();assert.equal(fail.requests.length,n*2);
  fail.doc.activeElement=fail.doc.body;fail.requests[n].reject(Error('offline'));await retry;assert.equal(fail.doc.activeElement,fail.retry,'A failed keyboard retry remains reachable');
  const recovery=fail.retry.listeners.click();const offset=fail.requests.length-n;fail.doc.activeElement=fail.doc.body;fail.respond(offset);await recovery;
  assert(fail.retry.hidden);assert.equal(fail.doc.activeElement,fail.heading);assert.equal(fail.heading.focusOptions.preventScroll,true);
  for(const error of [true,false]){const stale=harness(id),pending=stale.api.bind(stale.figure,stale.options);stale.leave();const before=stale.status.textContent;if(error)stale.requests[0].reject(Error('offline'));else stale.respond();await pending;assert.equal(stale.status.textContent,before);assert.equal(stale.view.innerHTML,'');}
  for(const bodyOnly of [false,true]){
   const timeout=harness(id),pending=timeout.api.bind(timeout.figure,timeout.options);const originalCount=timeout.requests.length,resolveBodies=[];
   if(bodyOnly)for(const r of timeout.requests)r.resolve({ok:true,json:()=>new Promise(resolve=>{resolveBodies.push(resolve)})});
   await flush();[...timeout.timers.values()][0]();await pending;assert(timeout.requests.every(r=>r.signal.aborted));assert(!timeout.retry.hidden);
   const again=timeout.retry.listeners.click(),elsewhere={};timeout.doc.activeElement=elsewhere;timeout.respond(originalCount);await again;const saved=timeout.view.innerHTML;
   if(bodyOnly)resolveBodies.forEach(resolve=>resolve({}));else timeout.respond(0,true);await flush();assert.equal(timeout.view.innerHTML,saved);assert.equal(timeout.doc.activeElement,elsewhere);
  }
 }
 console.log('PASS: all five actual stage/control counts/scores, compact-receipt declaration/validation/retry, Fibonacci alias qualification, artifact ciphertext equations/slot semantics,16px fluid markup, independent shared caches, JSON/response timeouts, focus/stale guards. Source/DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1});
