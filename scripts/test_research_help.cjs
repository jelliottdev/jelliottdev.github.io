'use strict';
const assert=require('node:assert/strict'),Help=require('../research-help.js'),F=require('../record-followup-view.js'),registry=require('../data/experiments.json');
const records=Object.fromEntries(registry.records.map(r=>[r.id,r])),before=JSON.stringify(records),groups=Help.choices(records),html=Help.render(records),tick=()=>new Promise(resolve=>setImmediate(resolve));
// The bounded-discovery tests below deliberately exercise a full eight-choice family.
const multiIndex=groups.findIndex(g=>g.checks.length===8),singleIndex=groups.findIndex(g=>g.checks.length===1),shortMultiIndex=groups.findIndex(g=>g.checks.length===2);
assert(multiIndex>=0&&singleIndex>=0&&shortMultiIndex>=0);
function fixture(indices=[multiIndex,singleIndex],source=records,{failFactory=false}={}){
 const catalogue=Help.choices(source),rows=indices.map(index=>{
  const nodes=new Map(),group=catalogue[index],get=key=>{
   if(key==='select'&&group.checks.length===1)return null;
   if(!nodes.has(key))nodes.set(key,{textContent:'',hidden:true,dataset:{},...(key==='select'?{value:group.checks[0].id}:{}),...(key==='[data-help-review]'?{href:'run.html#record='+group.record.id+'&followup='+group.checks[0].id}:{})});return nodes.get(key);
  };return {dataset:{helpCheck:String(index)},querySelector:get,get,group};
 });
 const calls=[],top=new Map(),topGet=key=>{if(!top.has(key))top.set(key,{textContent:key==='[data-help-start-status]'?'Finding a check with work remaining…':'',hidden:['[data-help-start-choice]','[data-help-more]'].includes(key),open:false,dataset:{}});return top.get(key);};
 const destroy=Help.bind({querySelectorAll:()=>rows,querySelector:topGet},source,{createReadiness(options){
  const call={...options,activated:0,retried:0,destroyed:0};calls.push(call);if(failFactory)throw Error('Unavailable');
  return {activate(){call.activated++;},retry(){call.retried++;},destroy(){call.destroyed++;}};
 }});
 return {rows,calls,destroy,topGet,initial:calls.slice()};
}
function settleInitial(f,states=[]){for(const [i,call]of f.initial.entries())call.onState(states[i]||{state:'results'});}
function choose(row,check){row.get('select').value=check.id;row.get('select').onchange();}
let count=0;async function test(name,fn){await fn();count++;console.log('PASS '+name);}
(async()=>{
await test('finite work is counted as page-and-setting checks, never pages',async()=>{
 const f=fixture([singleIndex]);try{const call=f.calls[0],row=f.rows[0];call.onState({state:'remaining',unit:'cases',remainingCount:2352,totalPages:56,programCount:42});assert.equal(row.get('[data-help-status]').textContent,'2352 checks remain.');call.onState({state:'results',unit:'cases'});assert.equal(row.get('[data-help-status]').textContent,'Results are saved for every declared page and setting.');}finally{f.destroy();}
});
await test('maintained immutable source choices, exact links, escaped prose and empty catalogue',async()=>{
 assert(groups.length>0);assert.equal(JSON.stringify(records),before);assert(html.includes('No theory or coding needed'));assert(html.includes('data-help-more hidden>Look for another check</button>'));
 for(const {record,checks}of groups){assert.deepEqual(checks,F.available(record));assert(html.includes('run.html#record='+record.id+'&amp;followup='+checks[0].id));}
 assert.equal(Help.choices({...records,bogus:{id:'bogus',community:true,browser_followups:groups[multiIndex].checks}}).length,groups.length);
 assert(Help.render({}).includes('No maintained browser checks'));assert(!Help.render({}).includes('run.html#'));
 const altered=structuredClone(records);altered[groups[0].record.id].title='<img src=x onerror=alert(1)>';assert(!Help.render(altered).includes('<img'));assert(Help.render(altered).includes('&lt;img'));
 assert.equal((html.match(/<details\b/g)||[]).length,1);assert(!/<details[^>]*\bopen\b/.test(html));assert(/data-help-status role="status" aria-live="polite" hidden/.test(html));
});
await test('actual known-key choices keep authored titles, purposes and links aligned without promising optional saving',async()=>{
 const index=groups.findIndex(g=>g.record.id==='lp2-known-vigenere-keys');assert(index>=0);const f=fixture([index]);try{
  const row=f.rows[0],group=row.group;assert(group.checks.some(c=>c.kind==='finite-settings'));assert(group.checks.some(c=>c.kind!=='finite-settings'));
  choose(row,group.checks.at(-1));
  for(const check of group.checks){choose(row,check);assert.equal(row.get('[data-help-title]').textContent,check.title);assert.equal(row.get('[data-help-purpose]').textContent,check.motivation);assert.equal(row.get('[data-help-review]').href,'run.html#record='+group.record.id+'&followup='+check.id);assert(f.calls.some(call=>call.check.id===check.id&&call.record.id===group.record.id));}
  assert(html.includes('Choose a prepared check and review what it will do before running it.'));assert(!html.includes('choose whether to save'));assert(html.includes('Choose a check</label>'));assert(!html.includes('Choose a rule</label>'));
  for(const {checks}of groups)assert(html.includes('<h3 data-help-title>'+checks[0].title+'</h3>'));
  const altered=structuredClone(records);altered[group.record.id].browser_followups[0].title='<img src=x onerror=bad> & title';const escaped=Help.render(altered);assert(escaped.includes('&lt;img src=x onerror=bad&gt; &amp; title'));assert(!escaped.includes('<img'));
  assert.equal(JSON.stringify(records),before,'Selecting a title cannot mutate authored sources');
 }finally{f.destroy();}
});
await test('selected-row states, retry, source-bound selection and old listeners unsubscribe without destroying cached probes',async()=>{
 const f=fixture(),row=f.rows[0],first=f.calls[0];assert.equal(f.calls.length,2);assert.equal(first.activated,1);
 for(const [value,message,label]of [
  [{state:'remaining',remainingCount:2},'2 pages remain to check.','Review remaining check'],
  [{state:'remaining',remainingCount:1},'1 page remains to check.','Review remaining check'],
  [{state:'results'},'Results are saved for every declared page.','View results'],
  [{state:'answered'},'This question already has an answer.','View answer'],
  [{state:'unavailable'},'Saved results could not be checked.','Review check'],
  [{state:'remaining',remainingCount:0},'Saved results could not be checked.','Review check'],
  [{state:'remaining',remainingCount:'2'},'Saved results could not be checked.','Review check'],
  [{state:'other'},'Saved results could not be checked.','Review check']]){
  first.onState(value);assert.equal(row.get('[data-help-status]').textContent,message);assert.equal(row.get('[data-help-review]').textContent,label);assert.equal(row.get('[data-help-retry]').hidden,label!=='Review check');
 }
 row.get('[data-help-retry]').onclick();assert.equal(first.retried,1);assert.equal(row.get('[data-help-status]').textContent,'Checking saved results…');
 const changed=row.group.checks.at(-1);choose(row,changed);assert.equal(first.destroyed,0);assert.equal(f.calls.length,3);assert.equal(f.calls[2].check,changed);assert.equal(row.get('[data-help-question]').textContent,changed.question);assert.equal(row.get('[data-help-purpose]').textContent,changed.motivation);assert(row.get('[data-help-review]').href.endsWith(changed.id));
 first.onState({state:'answered'});assert.equal(row.get('[data-help-status]').textContent,'Checking saved results…','An unsubscribed old rule cannot replace the selected row');
 f.calls[2].onState({state:'results'});choose(row,row.group.checks[0]);assert.equal(f.calls.length,3);assert.equal(row.get('[data-help-status]').textContent,'This question already has an answer.','Switching back reuses a previously verified state');assert.equal(first.activated,1);
 row.get('select').value='unknown';row.get('select').onchange();assert.equal(row.get('select').value,first.check.id);assert.equal(f.calls.length,3);
 const oldRetry=row.get('[data-help-retry]').onclick;f.destroy();f.destroy();assert(f.calls.every(c=>c.destroyed===1));first.onState({state:'remaining',remainingCount:99});assert(row.get('[data-help-status]').hidden);oldRetry();assert.equal(first.retried,1);assert.equal(row.get('select').onchange,null);assert.equal(row.get('[data-help-retry]').onclick,null);
});
await test('all displayed initial choices must settle before a sequential alternative pass; first remaining alternative has exact source context',async()=>{
 const f=fixture(),row=f.rows[0],initialHref=row.get('[data-help-review]').href,initialSelection=row.get('select').value;
 f.initial[0].onState({state:'results'});await tick();assert.equal(f.calls.length,2,'Do not start alternatives while another initial row is pending');
 f.initial[1].onState({state:'answered'});await tick();assert.equal(f.calls.length,3);const alternative=f.calls[2];assert.equal(alternative.check,row.group.checks[1]);assert.equal(alternative.record,row.group.record);
 await tick();assert.equal(f.calls.length,3,'Only one alternative may be probed at a time');assert(!f.topGet('[data-help-start-status]').textContent.includes('These prepared checks have saved results'));
 alternative.onState({state:'remaining',remainingCount:4});await tick();assert.equal(f.calls.length,3,'Stop the pass after a verified remaining check');
 assert.equal(f.topGet('[data-help-start-title]').textContent,alternative.check.title);assert.equal(f.topGet('[data-help-start-purpose]').textContent,alternative.check.motivation);assert.equal(f.topGet('[data-help-start-link]').href,'run.html#record='+alternative.record.id+'&followup='+alternative.check.id);assert.equal(f.topGet('[data-help-start-count]').textContent,'4 pages remain to check.');
 assert.equal(row.get('select').value,initialSelection);assert.equal(row.get('[data-help-review]').href,initialHref);assert.equal(row.get('[data-help-status]').textContent,'Results are saved for every declared page.','Background discovery cannot change the displayed rule');
 const chosen=f.topGet('[data-help-start-link]').href;f.initial[0].onState({state:'remaining',remainingCount:45});assert.equal(f.topGet('[data-help-start-link]').href,chosen,'A later result cannot redirect the captured recommendation');
 alternative.onState({state:'answered'});assert.equal(f.topGet('[data-help-start-link]').textContent,'View answer');assert.equal(f.topGet('[data-help-start-link]').href,chosen);
 choose(row,alternative.check);assert.equal(f.calls.length,3,'Selecting a background result reuses its source entry');assert.equal(row.get('[data-help-status]').textContent,'This question already has an answer.');assert.equal(f.topGet('[data-help-start-link]').href,chosen);f.destroy();
});
await test('unavailable alternatives do not stop discovery or invent completion',async()=>{
 const f=fixture();settleInitial(f,[{state:'unavailable'},{state:'results'}]);await tick();f.calls[2].onState({state:'unavailable'});await tick();assert.equal(f.calls.length,4);const next=f.calls[3];next.onState({state:'remaining',remainingCount:1});await tick();assert.equal(f.topGet('[data-help-start-title]').textContent,next.check.title);assert.equal(f.topGet('[data-help-start-count]').textContent,'1 page remains to check.');assert.equal(f.calls.length,4);f.destroy();
});
await test('two-choice families stop at their real boundary and retain unknown results',async()=>{
 for(const state of ['unavailable','remaining']){
  const f=fixture([shortMultiIndex,singleIndex]);settleInitial(f);await tick();assert.equal(f.calls.length,3);
  const alternative=f.calls[2];assert.equal(alternative.check,f.rows[0].group.checks[1]);
  alternative.onState(state==='remaining'?{state,remainingCount:7}:{state});await tick();
  assert.equal(f.calls.length,3,'Do not invent additional checks when this family has only two choices');assert(f.topGet('[data-help-more]').hidden);
  if(state==='remaining'){
   assert.equal(f.topGet('[data-help-start-title]').textContent,alternative.check.title);
   assert.equal(f.topGet('[data-help-start-purpose]').textContent,alternative.check.motivation);
   assert.equal(f.topGet('[data-help-start-link]').href,'run.html#record='+alternative.record.id+'&followup='+alternative.check.id);
  }else{assert.match(f.topGet('[data-help-start-status]').textContent,/could not be checked/);assert(f.topGet('[data-help-start-choice]').hidden);}
  f.destroy();
 }
});
await test('automatic pass is capped at four alternatives; explicit next batch continues without duplicates and claims completion only after all choices',async()=>{
 const f=fixture();settleInitial(f);await tick();
 for(let i=0;i<4;i++){assert.equal(f.calls.length,3+i);assert.equal(f.calls[2+i].check,f.rows[0].group.checks[i+1]);f.calls[2+i].onState({state:i%2?'answered':'results'});await tick();}
 assert.equal(f.calls.length,6);assert.equal(f.topGet('[data-help-more]').hidden,false);assert.equal(f.topGet('[data-help-start-status]').textContent,'The checks reviewed so far have saved results or answers.');assert(f.topGet('[data-help-start-choice]').hidden);
 f.topGet('[data-help-more]').onclick();f.topGet('[data-help-more]').onclick();await tick();assert.equal(f.calls.length,7,'Duplicate activation cannot enqueue another batch');
 for(let i=4;i<7;i++){assert.equal(f.calls[2+i].check,f.rows[0].group.checks[i+1]);f.calls[2+i].onState({state:'answered'});await tick();}
 assert.equal(f.calls.length,9,'Two displayed initial choices plus all seven alternatives');assert(f.topGet('[data-help-more]').hidden);assert.equal(f.topGet('[data-help-start-status]').textContent,'These prepared checks have saved results or answers. Browse the full list to view them.');assert.equal(new Set(f.calls.map(c=>c.record.id+'|'+c.check.id)).size,f.calls.length);f.destroy();
 const unknown=fixture();settleInitial(unknown);await tick();for(let i=0;i<4;i++){unknown.calls[2+i].onState({state:i===1?'unavailable':'results'});await tick();}assert.equal(unknown.topGet('[data-help-start-status]').textContent,'No starting check was confirmed yet. Some saved results could not be checked.');assert(!unknown.topGet('[data-help-more]').hidden);unknown.destroy();
});
await test('manual browse and rule selection stop automatic recommendations, including open-toggle races and in-flight alternatives',async()=>{
 for(const action of ['browse','toggle-race','select']){
  const f=fixture();settleInitial(f);await tick();const active=f.calls[2],initialCalls=f.calls.length;
  if(action==='select')choose(f.rows[0],f.rows[0].group.checks.at(-1));else{f.topGet('[data-help-browse]').open=true;if(action==='browse')f.topGet('[data-help-browse]').ontoggle();}
  active.onState({state:'remaining',remainingCount:2});await tick();assert(f.topGet('[data-help-start-choice]').hidden);assert(f.topGet('[data-help-more]').hidden);assert.equal(f.calls.length,initialCalls+(action==='select'?1:0));
  f.topGet('[data-help-browse]').open=false;f.topGet('[data-help-browse]').ontoggle();active.onState({state:'results'});await tick();assert.equal(f.calls.length,initialCalls+(action==='select'?1:0));assert(f.topGet('[data-help-start-choice]').hidden);f.destroy();
 }
});
await test('close before scheduling or during an alternative destroys all entries and ignores old callbacks and buttons',async()=>{
 for(const timing of ['before-pump','in-flight']){
  const f=fixture();settleInitial(f);if(timing==='in-flight')await tick();const calls=f.calls.slice(),button=f.topGet('[data-help-more]').onclick;f.destroy();await tick();assert.equal(f.calls.length,calls.length);assert(calls.every(c=>c.destroyed===1));const oldText=f.topGet('[data-help-start-status]').textContent;calls.at(-1).onState({state:'remaining',remainingCount:99});button();await tick();assert.equal(f.topGet('[data-help-start-status]').textContent,oldText);assert(f.topGet('[data-help-start-choice]').hidden);assert.equal(f.calls.length,calls.length);assert.equal(f.topGet('[data-help-more]').onclick,null);assert.equal(f.topGet('[data-help-browse]').ontoggle,null);
 }
});
await test('identical followup IDs in different records remain separate exact source entries',async()=>{
 const original=groups[multiIndex].record,a=structuredClone(original),b=structuredClone(original);a.id='source-one';b.id='source-two';b.browser_followups[1].motivation='Purpose belongs to source two.';const source={[a.id]:a,[b.id]:b},saved=JSON.stringify(source),f=fixture([0,1],source);assert.equal(f.calls.length,2);assert.equal(f.calls[0].check.id,f.calls[1].check.id);assert.notEqual(f.calls[0].record.id,f.calls[1].record.id);
 settleInitial(f);await tick();const background=f.calls[2];background.onState({state:'results'});await tick();const sameIdOther=f.rows[1].group.checks[1];choose(f.rows[1],sameIdOther);const selected=f.calls.at(-1);assert.equal(selected.record.id,f.rows[1].group.record.id);assert.equal(selected.check,sameIdOther);assert.equal(selected.check.id,background.check.id);assert.notEqual(selected.record.id,background.record.id);selected.onState({state:'remaining',remainingCount:3});assert.equal(f.rows[1].get('[data-help-purpose]').textContent,sameIdOther.motivation);assert.equal(JSON.stringify(source),saved);f.destroy();
});
await test('factory errors keep an actionable retry and never change source data',async()=>{
 const f=fixture([singleIndex],records,{failFactory:true});assert.equal(f.rows[0].get('[data-help-status]').textContent,'Saved results could not be checked.');assert(!f.rows[0].get('[data-help-retry]').hidden);f.rows[0].get('[data-help-retry]').onclick();assert.equal(f.calls.length,2);await tick();assert.match(f.topGet('[data-help-start-status]').textContent,/could not be checked/);f.destroy();assert.equal(JSON.stringify(records),before);
});
console.log(count+' maintained chooser discovery groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
