/* Frozen rule/results and production selector lifecycle; no solver/browser/network. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),base='experiments/records/prime-lag-autokey-openings/';
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const plan=read(base+'plan-frozen-original.json'),results=read(base+'results.json'),record=read(base+'record.json');
const api=require('../prime-lag-view.js'),data=api.validate(plan,results),lags=plan.prime_lag_autokey.lags;
assert.deepEqual(data.lags,lags);assert.equal(lags.length,11);
for(const p of lags){
 const rows=api.timeline(p);assert.equal(rows.length,12);
 for(let j=0;j<12;j++){
  assert.equal(rows[j].position,j+1);assert.equal(rows[j].source,j<p?'primer':'earlier');
  assert.equal(rows[j].earlierPosition,j<p?null:j-p+1,'Source j-p is translated to a human one-based position');
 }
 assert.equal((api.positions(p).match(/<li /g)||[]).length,12);
 assert(api.explanation(p).includes('position '+(p+1)));
}
assert.equal(api.timeline(2)[2].earlierPosition,1);assert.equal(api.timeline(11)[11].earlierPosition,1);
for(const p of [13,31])assert(api.timeline(p).every(row=>row.source==='primer'));
assert.equal(lags.filter(p=>p>=13).length*plan.prime_lag_autokey.modes.length*plan.prime_lag_autokey.primers.length,data.longSettings);
assert.equal(data.longPrefixes,29);assert.throws(()=>api.timeline(12));
assert(api.render().includes('j &lt; p'));assert(api.render().includes('p + 1'));assert(api.render().includes('download>Download the original SVG'));
for(const mutate of [p=>p.prime_lag_autokey.lags.push(37),p=>p.prime_lag_autokey.primers.pop(),p=>p.prime_lag_autokey.target='Another target']){
 const bad=structuredClone(plan);mutate(bad);assert.throws(()=>api.validate(bad,results));
}
const bad=structuredClone(results);bad.equivalence_by_page[0].lag13_to31_distinct_prefixes=30;assert.throws(()=>api.validate(plan,bad));
const ctx={esc:String,PrimeLagView:api};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),ctx);
assert(ctx.experimentVisual(record,record.visuals[0]).includes('data-prime-lag'));
assert(ctx.experimentVisual({...record,reproduction:{inputs:[],outputs:[]}},record.visuals[0]).includes('<img'),'Unlisted paths do not authorize native fetching');
delete ctx.PrimeLagView;assert(ctx.experimentVisual(record,record.visuals[0]).includes('<img'),'Static SVG remains the missing-module fallback');
const source=fs.readFileSync(path.join(root,'prime-lag-view.js'),'utf8');
function runtime(){const timers=new Map();let id=0;const c={module:{exports:{}},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++id,fn);return id},clearTimeout(id){timers.delete(id)}};vm.createContext(c);vm.runInContext(source,c);return {api:c.module.exports,timers};}
function harness(run=runtime()){
 const doc={activeElement:null,body:{}},requests=[];
 const node=()=>({value:'',innerHTML:'',textContent:'',disabled:false,hidden:false,listeners:{},addEventListener(type,fn){this.listeners[type]=fn},focus(options){doc.activeElement=this;this.focusOptions=options}});
 const select=node(),status=node(),retry=node(),grid=node(),note=node(),counts=node();select.disabled=true;retry.hidden=true;
 const nodes={'[data-prime-lag]':select,'[data-prime-status]':status,'[data-prime-retry]':retry,'[data-prime-positions]':grid,'[data-prime-explanation]':note,'[data-prime-counts]':counts};
 const figure={isConnected:true,ownerDocument:doc,querySelector:s=>nodes[s]};let current=true;
 const options={isCurrent:()=>current,fetcher:(url,options)=>new Promise((resolve,reject)=>requests.push({url,signal:options.signal,resolve,reject}))};
 const respond=(offset=0,invalid=false)=>requests.slice(offset).forEach(r=>r.resolve({ok:true,json:async()=>invalid?{}:r.url.endsWith('results.json')?results:plan}));
 return {...run,figure,select,status,retry,grid,note,counts,doc,requests,options,respond,leave(){current=false}};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const h=harness(),initial=h.api.bind(h.figure,h.options);assert(h.select.disabled);assert.equal(h.requests.length,2);
 assert(h.requests.every(r=>[base+'plan-frozen-original.json',base+'results.json'].includes(r.url)));
 const sibling=harness({api:h.api,timers:h.timers}),shared=h.api.bind(sibling.figure,sibling.options);assert.equal(sibling.requests.length,0);
 h.respond();await initial;await shared;assert.equal(h.timers.size,0);assert(!h.select.disabled);assert.equal(h.select.value,'13');
 assert.equal((h.select.innerHTML.match(/<option /g)||[]).length,11);assert(h.counts.textContent.includes('348 settings but only 29'));
 const originalSelect=h.select;h.doc.activeElement=h.select;
 for(const p of [2,11,13,31]){h.select.value=String(p);h.select.listeners.change();assert.equal(h.select,originalSelect);assert.equal(h.doc.activeElement,h.select,'Native keyboard selection retains focus');assert.equal((h.grid.innerHTML.match(/prime-lag-feedback/g)||[]).length,Math.max(0,12-p));assert(h.note.innerHTML.includes('position '+(p+1)));}
 const warm=harness({api:h.api,timers:h.timers});await warm.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0);
 const failed=harness(),loading=failed.api.bind(failed.figure,failed.options);failed.respond(0,true);await loading;
 assert(failed.select.disabled);assert(!failed.retry.hidden);assert(failed.status.textContent.includes('download'));assert.equal(failed.grid.innerHTML,'');
 failed.doc.activeElement=failed.retry;const again=failed.retry.listeners.click();await failed.retry.listeners.click();assert.equal(failed.requests.length,4);
 failed.doc.activeElement=failed.doc.body;failed.respond(2);await again;assert(!failed.select.disabled);assert(failed.retry.hidden);assert.equal(failed.doc.activeElement,failed.select);assert.equal(failed.select.focusOptions.preventScroll,true);
 for(const fail of [true,false]){const stale=harness(),request=stale.api.bind(stale.figure,stale.options);stale.leave();const before=stale.status.textContent;if(fail)stale.requests[0].reject(Error('offline'));else stale.respond();await request;assert.equal(stale.status.textContent,before);assert.equal(stale.grid.innerHTML,'');assert(stale.select.disabled);}
 const timeout=harness(),pending=timeout.api.bind(timeout.figure,timeout.options);[...timeout.timers.values()][0]();await pending;
 assert(timeout.requests.every(r=>r.signal.aborted));assert(!timeout.retry.hidden);assert(timeout.select.disabled);
 const recovered=timeout.retry.listeners.click();const elsewhere={};timeout.doc.activeElement=elsewhere;timeout.respond(2);await recovered;const saved=timeout.grid.innerHTML;
 timeout.respond(0,true);await flush();assert.equal(timeout.grid.innerHTML,saved);assert.equal(timeout.doc.activeElement,elsewhere,'Late retry cannot steal focus');
 console.log('PASS: frozen11 delays, source-zero/human-one indexing, lag2/11/13/31 dependency cells, keyboard selection, declaration gating, static fallback, validation/shared-cache/timeout/retry/focus/stale guards. DOM/source only.');
})().catch(error=>{console.error(error);process.exitCode=1});
