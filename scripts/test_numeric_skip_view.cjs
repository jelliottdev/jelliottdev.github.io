/* Actual search/step receipts and production lifecycle; no solver, browser or network. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ids=['numeric-stream-skip-grid','artifact-stream-skip-grid','fibonacci-stream-skip-grid'],api=require('../numeric-skip-view.js'),fixtures={};
for(const id of ids){
 const base='experiments/records/'+id+'/',artifact=id===ids[1],fib=id===ids[2],planName=id===ids[0]?'frozen-plan.json':'plan.json';
 const record=read(base+'record.json'),plan=read(base+planName),results=read(base+'results.json'),receipt=artifact?read(base+'figure-receipt.json'):undefined;
 fixtures[id]={record,plan,results,receipt,payloads:{[base+planName]:plan,[base+'results.json']:results,...(artifact?{[base+'figure-receipt.json']:receipt}:{})}};
 const data=api.validate(id,plan,results,receipt),html=api.content(data);
 assert.equal(data.screens,fib?92510:artifact?23100:36300);assert.equal(data.full,fib?900:artifact?194:322);assert.equal(data.passes,0);
 for(const count of [data.screens,data.full,data.passes])assert(html.includes('<strong>'+count.toLocaleString('en-US')+'</strong>'));
 assert.equal((html.match(/numeric-skip-stages/g)||[]).length,1);assert(html.includes('First 50-rune checks'));assert(html.includes('Complete-page checks'));assert(html.includes('Passed the fixed English-score test'));
 assert(html.includes(data.best.score.toFixed(3).replace('-','−')));assert(html.includes('−5.5'));assert(html.includes('score alone cannot confirm plaintext'));
 assert(api.canRender(record,record.visuals[0]));assert(api.render(id).includes('download>Download the original SVG'));
 const missing=structuredClone(record);missing.reproduction.outputs=missing.reproduction.outputs.filter(f=>!f.path.endsWith('results.json'));assert(!api.canRender(missing,record.visuals[0]));
 if(artifact){
  const byRune=new Map(read('data/index.json').alphabet.map(a=>[a.rune,a.index]));
  const ciphertext=[...read('data/pages/lp2-49.json').raw].filter(r=>byRune.has(r)).map(r=>byRune.get(r));
  assert.equal(ciphertext[receipt.rune_position_zero_based-1],receipt.previous_transformed_cipher_index);
  assert.equal(ciphertext[receipt.rune_position_zero_based],receipt.current_transformed_cipher_index);
  assert.equal(results.best_full.full_indices[receipt.rune_position_zero_based],receipt.candidate_plain_index);
  assert.equal((receipt.candidate_plain_index-receipt.rejected_key_value+29)%29,ciphertext[28]);
  assert.equal((receipt.candidate_plain_index-receipt.accepted_key_value+29)%29,ciphertext[29]);
  assert(html.includes('28 − 2 = 26 (mod 29)'));assert(html.includes('28 − 3 = 25 (mod 29)'));assert(html.includes('same candidate rune again'));assert(html.includes('not confirmed plaintext'));
  const wrong=structuredClone(receipt);wrong.rejected_key_value=1;assert.throws(()=>api.validate(id,plan,results,wrong));
 }else if(fib){
  assert.equal(results.source_labeled_screens,10*data.screens);assert(html.includes('925,100'));assert(html.includes('not extra tests'));
  assert(!html.includes('numeric-skip-step'),'Fibonacci summary does not invent an alias/skip demonstration');
 }else{
  assert.equal(results.stream_logs.reduce((n,row)=>n+row.screens,0),data.screens);
  assert.equal(results.stream_logs.reduce((n,row)=>n+row.full_survivors,0),data.full);
  assert(!html.includes('numeric-skip-step'),'Numeric results do not invent a skip trace');
 }
 const bad=structuredClone(results);if(fib)bad.canonical_full_confirmations++;else if(artifact)bad.source_gate_passes=1;else bad.full_survivors++;assert.throws(()=>api.validate(id,plan,bad,receipt));
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
 assert.equal(first.requests.length,2);assert.equal(second.requests.length,3,'Different studies cannot share the wrong cache');
 const twin=harness(ids[0],sharedRun),same=twin.api.bind(twin.figure,twin.options);assert.equal(twin.requests.length,0);
 first.respond();second.respond();await Promise.all([a,b,same]);assert(first.view.innerHTML.includes('36,300'));assert(second.view.innerHTML.includes('23,100'));assert.equal(sharedRun.timers.size,0);
 const warm=harness(ids[1],sharedRun);await warm.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0);
 for(const id of ids){
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
 console.log('PASS: all three actual stage counts/scores, Fibonacci alias qualification, artifact ciphertext equations/slot semantics, fixed declarations/fallback,16px fluid markup, independent shared caches, JSON/response timeouts, retry/focus/stale guards. Source/DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1});
