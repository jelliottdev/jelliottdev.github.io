'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),base='experiments/records/keyword-skip-family/';
const read=file=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const result=read(base+'control-summary.json'),api=require('../keyword-skip-view.js'),data=api.validate(result);
const controls=read(base+'reproduction/controls-results.json');
assert.equal(data.known.total,controls.domain_count);assert.equal(data.known.score_passes,controls.domain_full_passes);assert.equal(data.known.exact_recoveries,controls.domain_exact_recoveries);
assert.equal(data.whole.total,controls.full_grids.length);assert.equal(data.whole.exact_recoveries,controls.full_grids.filter(row=>row.exact_gate_hit).length);
assert.equal(data.known.total,617);assert.equal(data.wrong,42);assert.equal(data.whole.exact_recoveries,3);
const alphabet=read('data/index.json').alphabet;
for(const side of ['expected','recovered'])assert.deepEqual(data.example[side+'_labels'],data.example[side+'_indices'].map(n=>alphabet[n].latin),'Display labels correspond to the canonical rune indices');
const example=controls.controls.find(row=>row.keyword===data.example.keyword&&row.reading===data.example.reading);
assert(example&&example.full_gate&&!example.exact_recovery,'The illustrated output actually passed the score gate and failed exact recovery');
const start=data.example.excerpt_start-1,end=start+data.example.expected_indices.length;
assert.deepEqual(data.example.recovered_indices,example.full[0].plain.slice(start,end));
const correct=controls.full_grids.find(row=>row.reading===data.example.reading&&row.exact_gate_hit).full_outputs.find(row=>row.exact).plain;
assert.deepEqual(data.example.expected_indices,correct.slice(start,end),'The illustrated original matches the independently recovered known passage');
const html=api.content(data);
for(const text of ['617 / 617','575 / 617','42 accepted outputs were wrong','3 of 4','623 keyword labels','reused two known passages','not probabilities of solving LP2'])assert(html.includes(text),text);
assert.equal((html.match(/class="keyword-skip-changed"/g)||[]).length,2*data.example.expected_indices.filter((n,i)=>n!==data.example.recovered_indices[i]).length);
assert(html.includes('Rune '+data.example.first_difference+': '));assert(!html.includes('<details>'),'The control failure and example are always visible');
for(const mutate of [r=>r.known_key.exact_recoveries=618,r=>r.known_key.score_passes=616,r=>r.example.expected_indices[0]=29,r=>r.example.first_difference+=1,r=>r.example.recovered_labels[0]='<svg>',r=>r.whole_search.exact_recoveries=5]){const r=structuredClone(result);mutate(r);assert.throws(()=>api.validate(r));}
const record=read(base+'record.json'),visual=record.visuals.find(v=>v.path===base+'control-recovery.svg');assert(api.canRender(record,visual));assert(!api.canRender({...record,reproduction:{outputs:[]}},visual));assert(!api.canRender(record,{path:base+'../unsafe.svg'}));
const source=fs.readFileSync(path.join(root,'keyword-skip-view.js'),'utf8');
function runtime(){const timers=new Map();let seq=0;const c={module:{exports:{}},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++seq,fn);return seq},clearTimeout(id){timers.delete(id)}};vm.createContext(c);vm.runInContext(source,c);return{api:c.module.exports,timers};}
function harness(run=runtime()){
 const doc={body:{},activeElement:null},requests=[];
 const node=()=>({innerHTML:'',textContent:'',hidden:false,disabled:false,listeners:{},addEventListener(t,fn){this.listeners[t]=fn},focus(options){doc.activeElement=this;this.options=options}});
 const view=node(),status=node(),retry=node(),heading=node();retry.hidden=true;view.querySelector=()=>heading;
 const nodes={'[data-keyword-content]':view,'[data-keyword-status]':status,'[data-keyword-retry]':retry};const figure={isConnected:true,ownerDocument:doc,querySelector:s=>nodes[s]};let active=true;
 const options={isCurrent:()=>active,fetcher:(url,opts)=>new Promise((resolve,reject)=>requests.push({url,signal:opts.signal,resolve,reject}))};
 return{...run,doc,view,status,retry,heading,figure,requests,options,respond(i=0,value=result){requests[i].resolve({ok:true,json:async()=>value})},leave(){active=false}};
}
(async()=>{
 const h=harness(),load=h.api.bind(h.figure,h.options),other=harness({api:h.api,timers:h.timers}),shared=h.api.bind(other.figure,other.options);assert.equal(h.requests.length,1);assert.equal(other.requests.length,0);assert.equal(h.requests[0].url,base+'control-summary.json');h.respond();await load;await shared;assert(h.view.innerHTML.includes('42 accepted'));assert(h.retry.hidden);assert.equal(h.timers.size,0);
 const warm=harness({api:h.api,timers:h.timers});await warm.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0);
 const bad=harness(),failed=bad.api.bind(bad.figure,bad.options);bad.respond(0,{});await failed;assert(!bad.retry.hidden);assert(bad.view.innerHTML.includes('control-recovery.svg'));bad.doc.activeElement=bad.retry;const retried=bad.retry.listeners.click();await bad.retry.listeners.click();assert.equal(bad.requests.length,2);bad.doc.activeElement=bad.doc.body;bad.respond(1);await retried;assert.equal(bad.doc.activeElement,bad.heading);assert.equal(bad.heading.options.preventScroll,true);
 for(const error of [false,true]){const stale=harness(),pending=stale.api.bind(stale.figure,stale.options);stale.leave();const before=stale.status.textContent;if(error)stale.requests[0].reject(Error());else stale.respond();await pending;assert.equal(stale.view.innerHTML,'');assert.equal(stale.status.textContent,before);}
 const timeout=harness(),pending=timeout.api.bind(timeout.figure,timeout.options);[...timeout.timers.values()][0]();await pending;assert(timeout.requests[0].signal.aborted);assert(!timeout.retry.hidden);const retry=timeout.retry.listeners.click(),elsewhere={};timeout.doc.activeElement=elsewhere;timeout.respond(1);await retry;assert.equal(timeout.doc.activeElement,elsewhere);
 console.log('PASS keyword-skip native view: actual617/575/42 and3/4 controls, per-rune differences, declared paths, bounded/shared loading, malformed/retry/timeout/stale/focus safeguards.');
})().catch(error=>{console.error(error);process.exitCode=1});
