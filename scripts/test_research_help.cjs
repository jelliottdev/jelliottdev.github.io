const assert=require('node:assert/strict'),Help=require('../research-help.js'),F=require('../record-followup-view.js'),registry=require('../data/experiments.json');
const records=Object.fromEntries(registry.records.map(r=>[r.id,r])),before=JSON.stringify(records),groups=Help.choices(records),html=Help.render(records);
assert(groups.length>0);assert.equal(JSON.stringify(records),before);
assert(html.includes('No theory or coding needed'));assert(html.includes('Saved results are refreshed for each selected check.'));
for(const {record,checks} of groups){assert.deepEqual(checks,F.available(record));assert(html.includes('run.html#record='+record.id+'&amp;followup='+checks[0].id));}
const original=groups.find(g=>g.checks.length>1),elements=new Map(),get=key=>{if(!elements.has(key))elements.set(key,{});return elements.get(key);},index=groups.indexOf(original),element={dataset:{helpCheck:String(index)},querySelector:get};
Help.bind({querySelectorAll:()=>[element]},records);const select=get('select'),last=original.checks.at(-1);select.value=last.id;select.onchange();assert.equal(get('[data-help-question]').textContent,last.question);assert.equal(get('[data-help-review]').href,'run.html#record='+original.record.id+'&followup='+last.id);select.value='unknown';select.onchange();assert.equal(select.value,last.id,'Unknown choices cannot change the source-bound destination');
assert.equal(Help.choices({...records,bogus:{id:'bogus',community:true,browser_followups:original.checks}}).length,groups.length);
assert(Help.render({}).includes('No maintained browser checks'));assert(!Help.render({}).includes('run.html#'));
const altered=structuredClone(records);altered[groups[0].record.id].title='<img src=x onerror=alert(1)>';assert(!Help.render(altered).includes('<img'));assert(Help.render(altered).includes('&lt;img'));
console.log('PASS maintained discovery, exact review links, selection, unavailable work, escaping and immutable source');

const annotated=structuredClone(records),group=Help.choices(annotated).find(g=>g.checks.length>1);for(const [i,check]of group.checks.entries())check.motivation='Source purpose '+i+'.';const annotatedGroups=Help.choices(annotated),pos=annotatedGroups.findIndex(g=>g.record.id===group.record.id),nodes=new Map(),find=k=>{if(!nodes.has(k))nodes.set(k,{});return nodes.get(k);};Help.bind({querySelectorAll:()=>[{dataset:{helpCheck:String(pos)},querySelector:find}]},annotated);const selection=find('select'),choice=group.checks.at(-1);selection.value=choice.id;selection.onchange();assert.equal(find('[data-help-purpose]').textContent,choice.motivation);assert.equal(find('[data-help-question]').textContent,choice.question);assert(find('[data-help-review]').href.endsWith(choice.id));assert(Help.render(annotated).includes(group.checks[0].motivation));console.log('PASS source purpose follows selected rule without changing exact question or review destination');


function readinessFixture(indices){
 const rows=indices.map(index=>{
  const nodes=new Map(),group=groups[index],get=key=>{
   if(key==='select'&&group.checks.length===1)return null;
   if(!nodes.has(key))nodes.set(key,{textContent:'',hidden:true,dataset:{}});return nodes.get(key);
  };
  return {dataset:{helpCheck:String(index)},querySelector:get,nodes,get,group};
 });
 const calls=[];
 const destroy=Help.bind({querySelectorAll:()=>rows},records,{createReadiness(options){
  const call={...options,activated:0,retried:0,destroyed:0};calls.push(call);
  return {activate(){call.activated++;},retry(){call.retried++;},destroy(){call.destroyed++;}};
 }});
 return {rows,calls,destroy};
}
const multiIndex=groups.findIndex(g=>g.checks.length>1),singleIndex=groups.findIndex(g=>g.checks.length===1),ready=readinessFixture([multiIndex,singleIndex]),row=ready.rows[0],one=ready.rows[1],first=ready.calls[0];
assert.equal(ready.calls.length,2,'Only the initial selected recipe in each row starts readiness');
assert.equal(first.check.id,row.group.checks[0].id);assert.equal(first.record.id,row.group.record.id);assert.equal(first.activated,1);
assert.equal(row.get('[data-help-status]').textContent,'Checking saved results…');assert.equal(row.get('[data-help-review]').textContent,'Review check');assert.equal(row.get('[data-help-retry]').hidden,true);
for(const [value,message,label]of [
 [{state:'remaining',remainingCount:2},'2 pages remain to check.','Review remaining check'],
 [{state:'remaining',remainingCount:1},'1 page remains to check.','Review remaining check'],
 [{state:'results'},'Results are saved for every declared page.','View results'],
 [{state:'answered'},'This question already has an answer.','View answer'],
 [{state:'unavailable'},'Saved results could not be checked.','Review check'],
 [{state:'remaining',remainingCount:0},'Saved results could not be checked.','Review check'],
 [{state:'remaining',remainingCount:'2'},'Saved results could not be checked.','Review check'],
 [{state:'other'},'Saved results could not be checked.','Review check']
]){
 first.onState(value);assert.equal(row.get('[data-help-status]').textContent,message);assert.equal(row.get('[data-help-status]').hidden,false);assert.equal(row.get('[data-help-review]').textContent,label);
 assert.equal(row.get('[data-help-retry]').hidden,label!=='Review check');assert.equal(row.get('[data-help-status]').dataset.state,label==='Review check'?'unavailable':value.state);
}
row.get('[data-help-retry]').onclick();assert.equal(first.retried,1);assert.equal(row.get('[data-help-status]').textContent,'Checking saved results…');assert.equal(row.get('[data-help-retry]').hidden,true);
first.onState({state:'answered'});const readySelect=row.get('select'),changed=row.group.checks.at(-1);readySelect.value=changed.id;readySelect.onchange();
assert.equal(first.destroyed,1,'Changing the rule destroys its previous readiness controller');assert.equal(ready.calls.length,3);assert.equal(ready.calls[2].check.id,changed.id);assert.equal(ready.calls[2].activated,1);
assert.equal(row.get('[data-help-status]').textContent,'Checking saved results…','A new selection synchronously clears the previous answer');assert.equal(row.get('[data-help-review]').textContent,'Review check');
assert.equal(row.get('[data-help-question]').textContent,changed.question);assert.equal(row.get('[data-help-purpose]').textContent,changed.motivation);assert(row.get('[data-help-review]').href.endsWith(changed.id));
first.onState({state:'answered'});assert.equal(row.get('[data-help-status]').textContent,'Checking saved results…','Late old-rule callbacks cannot overwrite a newer selection');
readySelect.value='unknown';readySelect.onchange();assert.equal(readySelect.value,changed.id);assert.equal(ready.calls.length,3,'An invalid selection neither changes the destination nor starts a probe');
ready.calls[1].onState({state:'remaining',remainingCount:3});assert.equal(one.get('[data-help-status]').textContent,'3 pages remain to check.','Rows without selectors also receive readiness');
const lateRetry=row.get('[data-help-retry]').onclick;ready.destroy();ready.destroy();
assert.equal(first.destroyed,1);assert.equal(ready.calls[1].destroyed,1);assert.equal(ready.calls[2].destroyed,1,'Destroy cleans every active controller exactly once');
ready.calls[2].onState({state:'answered'});assert.equal(row.get('[data-help-status]').hidden,true,'Late callbacks after destruction are ignored');assert.equal(row.get('[data-help-status]').dataset.state,undefined);lateRetry();assert.equal(ready.calls[2].retried,0);
assert.equal(readySelect.onchange,null);assert.equal(row.get('[data-help-retry]').onclick,null);assert.equal(JSON.stringify(records),before,'Readiness never changes source records');
assert(/data-help-status role="status" aria-live="polite" hidden/.test(html));assert(html.indexOf('data-help-status')<html.indexOf('class="research-help-actions"'),'One live status precedes existing actions');
const noProbe=readinessFixture([]);noProbe.destroy();
console.log('PASS readiness labels, retry, selected-only probes, exact selector synchrony, invalid states and selections, controller cleanup and stale callback isolation.');
const failedNodes=new Map(),failedGet=key=>{if(key==='select')return null;if(!failedNodes.has(key))failedNodes.set(key,{});return failedNodes.get(key);};let attempts=0;
const cleanupFailure=Help.bind({querySelectorAll:()=>[{dataset:{helpCheck:String(singleIndex)},querySelector:failedGet}]},records,{createReadiness(){attempts++;throw Error('Unavailable');}});
assert.equal(failedGet('[data-help-status]').textContent,'Saved results could not be checked.');assert.equal(failedGet('[data-help-retry]').hidden,false);failedGet('[data-help-retry]').onclick();assert.equal(attempts,2,'Retry also recovers from controller initialization failures');cleanupFailure();
