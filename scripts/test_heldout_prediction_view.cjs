/* Actual saved study plus production UI lifecycle. No model/browser/network calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),base='experiments/records/heldout-rune-prediction/';
const read=file=>JSON.parse(fs.readFileSync(path.join(root,base+file),'utf8'));
const result=read('results.json'),observed=read('reproduction/observed.json'),api=require('../heldout-prediction-view.js');
const data=api.validate(result);
assert.deepEqual(data.predictors.map(row=>row.bits),observed.observed.values.slice(0,16),'Public display preserves all exact producer losses');
assert.equal(data.rank,observed.comparison.family_rank);assert.equal(data.rows,1001);
assert.deepEqual(Object.fromEntries(Object.entries(data.groups).map(([key,rows])=>[key,rows.length])),{better:2,equivalent:3,worse:11});
assert.deepEqual(data.groups.better.map(row=>[row.name,row.controls]),[['KT4',97],['KT5',27]]);
assert.equal(data.groups.better[0].gain.toFixed(6),'0.000106');assert.equal(data.groups.better[1].gain.toFixed(6),'0.000207');
assert.equal(data.packedBytes,7928);assert.equal(data.packedTotal,18);
assert.equal(data.packedGross,12);
const html=api.content(data);
for(const text of ['2 / 16','3 / 16','11 / 16','36 / 1,001','about 3.6%','35 comparison streams plus the manuscript itself','0 of 12 known patterns','0 of 18 synthetic examples','7,928 bytes','not significance results'])assert(html.includes(text),text);
assert.equal((html.match(/<tr>/g)||[]).length,17,'All16 losses remain available in one optional table');
assert(html.includes('KT1–3, PPM1–8'));assert(html.includes('KT6–8'),'Contiguous model labels stay compact without omitting models');
assert(html.indexOf('0 of 12 known patterns')<html.indexOf('<details>'),'Power failure is never hidden in the score disclosure');
assert(api.render().includes('download>Download the SVG summary'));
for(const mutate of [r=>r.predictors.pop(),r=>r.predictors[3].uniform_classification='worse',r=>r.predictors[0].name='<img>',r=>r.predictors[4].gain_over_uniform=1,
 r=>r.family.controls_at_least_as_strong=36,r=>delete r.family.rank_fraction,r=>r.marginal_flag_count=1,r=>r.compression.packed.reference_max_bytes=7929,
 r=>r.compression.packed.plant_detections=1,r=>r.compression.packed.gross_plant_count=18,r=>r.predictors[0].nulls_at_least_as_good=1001]){
 const bad=structuredClone(result);mutate(bad);assert.throws(()=>api.validate(bad));
}
const record=read('record.json'),visual=record.visuals.find(v=>v.path===base+'predictive-controls.svg');
assert(api.canRender(record,visual));assert(!api.canRender({...record,reproduction:{outputs:[]}},visual));
assert(!api.canRender(record,{path:base+'../../unknown.svg'}));
const ctx={esc:String,HeldoutPredictionView:api};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),ctx);
assert(ctx.experimentVisual(record,visual).includes('heldout-results'));
delete ctx.HeldoutPredictionView;assert(ctx.experimentVisual(record,visual).includes('<img'),'Missing module keeps archived figure');
const source=fs.readFileSync(path.join(root,'heldout-prediction-view.js'),'utf8');
function runtime(){const timers=new Map();let number=0;const c={module:{exports:{}},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++number,fn);return number},clearTimeout(id){timers.delete(id)}};vm.createContext(c);vm.runInContext(source,c);return{api:c.module.exports,timers};}
function harness(run=runtime()){
 const doc={body:{},activeElement:null},requests=[];
 const node=()=>({innerHTML:'',textContent:'',hidden:false,disabled:false,listeners:{},addEventListener(t,fn){this.listeners[t]=fn},focus(options){doc.activeElement=this;this.focusOptions=options}});
 const view=node(),status=node(),retry=node(),heading=node();retry.hidden=true;view.querySelector=()=>heading;
 const nodes={'[data-heldout-content]':view,'[data-heldout-status]':status,'[data-heldout-retry]':retry};
 const figure={isConnected:true,ownerDocument:doc,querySelector:s=>nodes[s]};let current=true;
 const options={isCurrent:()=>current,fetcher:(url,options)=>new Promise((resolve,reject)=>requests.push({url,signal:options.signal,resolve,reject}))};
 const respond=(i=0,value=result)=>requests[i].resolve({ok:true,json:async()=>value});
 return{...run,doc,view,status,retry,heading,figure,requests,options,respond,leave(){current=false}};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const h=harness(),load=h.api.bind(h.figure,h.options),sibling=harness({api:h.api,timers:h.timers}),shared=h.api.bind(sibling.figure,sibling.options);
 assert.equal(h.requests.length,1);assert.equal(sibling.requests.length,0);assert.equal(h.requests[0].url,base+'results.json');h.respond();await load;await shared;
 assert(h.view.innerHTML.includes('0 of 12'));assert(h.retry.hidden);assert.equal(h.timers.size,0);
 const warm=harness({api:h.api,timers:h.timers});await warm.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0);
 const failed=harness(),bad=failed.api.bind(failed.figure,failed.options);failed.respond(0,{});await bad;
 assert(!failed.retry.hidden);assert(failed.view.innerHTML.includes('predictive-controls.svg'));assert(failed.status.textContent.includes('Retry'));
 failed.doc.activeElement=failed.retry;const retry=failed.retry.listeners.click();await failed.retry.listeners.click();assert.equal(failed.requests.length,2);
 failed.doc.activeElement=failed.doc.body;failed.respond(1);await retry;assert.equal(failed.doc.activeElement,failed.heading);assert.equal(failed.heading.focusOptions.preventScroll,true);
 for(const error of [false,true]){const stale=harness(),pending=stale.api.bind(stale.figure,stale.options);stale.leave();const before=stale.status.textContent;if(error)stale.requests[0].reject(Error('offline'));else stale.respond();await pending;assert.equal(stale.view.innerHTML,'');assert.equal(stale.status.textContent,before);}
 const timeout=harness(),waiting=timeout.api.bind(timeout.figure,timeout.options);[...timeout.timers.values()][0]();await waiting;assert(timeout.requests[0].signal.aborted);assert(!timeout.retry.hidden);
 const recovered=timeout.retry.listeners.click(),elsewhere={};timeout.doc.activeElement=elsewhere;timeout.respond(1);await recovered;const currentHTML=timeout.view.innerHTML;
 timeout.respond(0,{});await flush();assert.equal(timeout.view.innerHTML,currentHTML);assert.equal(timeout.doc.activeElement,elsewhere,'Late completion cannot steal user focus');
 const css=fs.readFileSync(path.join(root,'style.css'),'utf8');assert(css.includes('.heldout-results{font-size:16px'));assert(css.includes('64px minmax(0,1fr)'));
 console.log('PASS held-out native view: exact16 source losses,2/3/11 groups,97/27 controls,36/1001 denominator, visible0/12positive and0/18total controls, declared paths, optional fullscores, malformed/sharedcache/timeout/retry/focus/stale behavior.');
})().catch(error=>{console.error(error);process.exitCode=1});
