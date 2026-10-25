const assert=require('node:assert/strict'),Help=require('../research-help.js'),F=require('../record-followup-view.js'),registry=require('../data/experiments.json');
const records=Object.fromEntries(registry.records.map(r=>[r.id,r])),before=JSON.stringify(records),groups=Help.choices(records),html=Help.render(records);
assert(groups.length>0);assert.equal(JSON.stringify(records),before);
assert(html.includes('No theory or coding needed'));assert(html.includes('Review a prepared check, run it here, then choose whether to save the result.'));assert(!html.includes('Saved results are refreshed'));
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
 const calls=[],top=new Map(),topGet=key=>{if(!top.has(key))top.set(key,{textContent:'',hidden:key==='[data-help-start-choice]',open:false});return top.get(key);};
 const destroy=Help.bind({querySelectorAll:()=>rows,querySelector:topGet},records,{createReadiness(options){
  const call={...options,activated:0,retried:0,destroyed:0};calls.push(call);
  return {activate(){call.activated++;},retry(){call.retried++;},destroy(){call.destroyed++;}};
 }});
 return {rows,calls,destroy,topGet};
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

assert.equal((html.match(/<details\b/g)||[]).length,1,'The full chooser has one native disclosure');
assert(/<details class="research-help-all" data-help-browse><summary>Browse all prepared checks<svg/.test(html),'Browsing starts closed with the shared chevron');
assert(!/<details[^>]*\bopen\b/.test(html));assert(html.includes('Finding a check with work remaining…'));
const suggested=readinessFixture([multiIndex,singleIndex]),suggestedFirst=suggested.calls[0],suggestedSecond=suggested.calls[1],top=suggested.topGet;
suggestedSecond.onState({state:'remaining',remainingCount:2});
assert.equal(top('[data-help-start-title]').textContent,suggestedSecond.check.title,'The first verified remaining check becomes the starting point');
assert.equal(top('[data-help-start-purpose]').textContent,suggestedSecond.check.motivation);assert.equal(top('[data-help-start-count]').textContent,'2 pages remain to check.');assert.equal(top('[data-help-start-status]').hidden,true);assert.equal(top('[data-help-start-choice]').hidden,false);
const exactSuggestedHref='run.html#record='+suggestedSecond.record.id+'&followup='+suggestedSecond.check.id;assert.equal(top('[data-help-start-link]').href,exactSuggestedHref);
suggestedFirst.onState({state:'remaining',remainingCount:45});assert.equal(top('[data-help-start-link]').href,exactSuggestedHref,'Later remaining checks do not replace the first suggestion');
suggested.rows[0].get('select').value=suggested.rows[0].group.checks.at(-1).id;suggested.rows[0].get('select').onchange();suggested.calls.at(-1).onState({state:'remaining',remainingCount:4});
assert.equal(top('[data-help-start-link]').href,exactSuggestedHref,'Changing another selector cannot redirect the captured suggestion');
suggestedSecond.onState({state:'remaining',remainingCount:1});assert.equal(top('[data-help-start-count]').textContent,'1 page remains to check.');assert.equal(top('[data-help-start-link]').href,exactSuggestedHref,'A refreshed count never replaces the chosen context or destination');
suggestedSecond.onState({state:'results'});assert.equal(top('[data-help-start-count]').textContent,'Results are saved for every declared page.');assert.equal(top('[data-help-start-link]').textContent,'View results','New evidence updates the chosen action in place');
suggestedSecond.onState({state:'answered'});assert.equal(top('[data-help-start-link]').textContent,'View answer');suggestedSecond.onState({state:'loading'});assert.equal(top('[data-help-start-link]').textContent,'Review check');assert.equal(top('[data-help-start-count]').textContent,'Checking saved results…');suggestedSecond.onState({state:'unavailable'});assert.equal(top('[data-help-start-link]').textContent,'Review check');assert.equal(top('[data-help-start-count]').textContent,'Saved results could not be checked.');
const chosenTitle=top('[data-help-start-title]').textContent;suggested.destroy();suggestedSecond.onState({state:'remaining',remainingCount:99});assert.equal(top('[data-help-start-title]').textContent,chosenTitle);assert.equal(top('[data-help-start-count]').textContent,'Saved results could not be checked.');assert.equal(top('[data-help-browse]').ontoggle,null);

const completed=readinessFixture([multiIndex,singleIndex]);completed.calls[0].onState({state:'results'});assert.equal(completed.topGet('[data-help-start-choice]').hidden,true);completed.calls[1].onState({state:'answered'});
assert.equal(completed.topGet('[data-help-start-status]').textContent,'These checks have saved results. Browse the full list to view them or choose another rule.','Completed initial choices do not imply every variant is complete');completed.destroy();
const unknown=readinessFixture([multiIndex,singleIndex]);unknown.calls[0].onState({state:'results'});unknown.calls[1].onState({state:'unavailable'});assert.equal(unknown.topGet('[data-help-start-status]').textContent,'We couldn’t confirm a check with work remaining. Browse the prepared checks below.');unknown.destroy();
const errors=readinessFixture([singleIndex]);errors.calls[0].onState({state:'unavailable'});assert.equal(errors.topGet('[data-help-start-choice]').hidden,true);assert.match(errors.topGet('[data-help-start-status]').textContent,/couldn’t confirm/);errors.destroy();

const manual=readinessFixture([multiIndex,singleIndex]),browse=manual.topGet('[data-help-browse]');browse.open=true;browse.ontoggle();const manualText=manual.topGet('[data-help-start-status]').textContent;assert.equal(manualText,'Choose any check with pages remaining below.');
manual.calls[0].onState({state:'remaining',remainingCount:45});manual.calls[1].onState({state:'results'});assert.equal(manual.topGet('[data-help-start-status]').textContent,manualText);assert.equal(manual.topGet('[data-help-start-choice]').hidden,true,'Opening all checks suppresses later top recommendation reflow');
browse.open=false;browse.ontoggle();manual.calls[1].onState({state:'remaining',remainingCount:1});assert.equal(manual.topGet('[data-help-start-choice]').hidden,true,'Closing the list does not resume automatic selection');manual.destroy();
const toggleRace=readinessFixture([singleIndex]);toggleRace.topGet('[data-help-browse]').open=true;toggleRace.calls[0].onState({state:'remaining',remainingCount:1});assert.equal(toggleRace.topGet('[data-help-start-choice]').hidden,true,'Native open state suppresses recommendation even before its asynchronous toggle event');toggleRace.destroy();
assert.equal(JSON.stringify(records),before,'Recommendation selection leaves every source field unchanged');
console.log('PASS one suggested starting point, fixed context/destination with refreshed status/actions, complete and unknown fallbacks, manual browse suppression, toggle race and late cleanup.');
