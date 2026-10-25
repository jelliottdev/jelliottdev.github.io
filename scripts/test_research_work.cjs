'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const W=require('../research-work.js'),F=require('../record-followup-view.js'),B=require('../research-browser-model.js');
const data=JSON.parse(fs.readFileSync('data/experiments.json','utf8')),prepared=data.records.find(r=>F.available(r).length);
assert(prepared,'Real prepared record fixture must exist');
const summary=(n,state='not-run')=>({id:String(n).padStart(64,'0'),title:'Synthetic experiment '+n,state});
const proposal='p_'+'a'.repeat(64),record=(total,verified,tasks=[])=>({id:'idea-'+proposal.slice(2),community:true,proposal_id:proposal,task_count:total,verified_task_count:verified,task_summaries:tasks,evidence_state:verified?'computation-available':'untested'});
const before=JSON.stringify(prepared),work=W.describe(prepared);assert.equal(work.kind,'prepared');assert.equal(work.count,F.available(prepared).length);assert.equal(work.href,'run.html#record='+prepared.id+'&followup='+F.available(prepared)[0].id);assert.equal(JSON.stringify(prepared),before);
assert(W.matches(prepared,'1'));assert(W.matches(prepared,'prepared'));assert(!W.matches(prepared,'pending'));assert(W.matches(prepared,''));assert(W.matches(prepared,'all'));assert(!W.matches(prepared,'garbage'));assert.equal(W.describe({id:'fake',browser_followups:[]}),null);
const unfinished=record(12,3,[summary(1,'results-verified'),summary(2),summary(3)]),saved=JSON.stringify(unfinished),d=W.describe(unfinished);assert.deepEqual(d,{kind:'unfinished',count:9,label:'9 unfinished experiments',href:'run.html#task='+summary(2).id});assert(W.matches(unfinished,'pending'));assert(W.matches(unfinished,'unfinished'));assert(!W.matches(unfinished,'1'));assert.equal(JSON.stringify(unfinished),saved);assert.equal(unfinished.evidence_state,'computation-available');
assert.equal(W.describe(record(12,3,[])).href,'run.html#idea='+proposal);assert.equal(W.describe(record(1,0,[summary(1)])).label,'1 unfinished experiment');assert.deepEqual(W.describe(record(0,0)),{kind:'question',count:1,label:'Review saved idea',href:'run.html#idea='+proposal});assert.equal(W.describe(record(3,3,[summary(1,'results-verified')])),null);assert.equal(W.describe({...record(1,0,[summary(1)]),browser_followups:prepared.browser_followups}).kind,'unfinished');
for(const state of ['untested','computation-available']){const original={...record(0,0),evidence_state:state},before=JSON.stringify(original);assert(W.matches(original,'questions'));assert(!W.matches(original,'pending'));assert(!W.matches(original,'prepared'));assert.equal(W.describe(original).label,'Review saved idea');assert.equal(JSON.stringify(original),before);}
for(const bad of [record(-1,0),record(1,2),record(1,-1),record(1.5,0),record(2,0,[summary(1,'results-verified')]),record(2,2,[summary(1)]),record(1,0,[summary(1),summary(2)]),record(2,0,[summary(1),summary(1)]),record(1,0,[{...summary(1),state:'unknown'}]),record(1,0,[{...summary(1),extra:1}]),{...record(1,0),task_summaries:undefined},{...record(1,0),proposal_id:'unsafe'}, {...record(1,0),id:'idea-incorrect'}])assert.equal(W.describe(bad),null);
const full=record(3,1,[summary(1,'results-verified'),summary(2),summary(3)]);assert(W.describe(full));const copied=W.communityTasks({taskCount:3,verifiedTaskCount:1,tasks:full.task_summaries});copied.tasks[0].state='not-run';assert.equal(full.task_summaries[0].state,'results-verified');
const selector=()=>({outcome:'',q:'',type:'',method:'',family:'',sort:''});for(const [query,expected]of [['followups=1','1'],['followups=pending','pending'],['followups=other',''],['','']])assert.equal(B.read('#'+query,'graph',selector).followups,expected);assert.equal(B.read('#/research?followups=pending','graph',selector).followups,'pending');
const ctx={RecordFollowupView:F};vm.createContext(ctx);vm.runInContext(fs.readFileSync('research-work.js','utf8'),ctx);assert.equal(ctx.ResearchWork.describe(unfinished).count,9);assert.equal(ctx.ResearchWork.describe(record(0,0)).label,'Review saved idea');
// Early matches deliberately leave member tasks unrun; those are not proof of
// an unanswered finite question. Only the original workspace checks the union.
const finiteMarker={kind:'finite-settings',version:1};
for(const candidate of [record(0,0),record(2,1,[summary(1,'results-verified'),summary(2)]),record(2,2,[summary(1,'results-verified'),summary(2,'results-verified')])]){
 const finite={...candidate,finite_search:finiteMarker},prior=JSON.stringify(finite);
 assert.deepEqual(W.describe(finite),{kind:'question',count:1,label:'Check declared settings',href:'run.html#idea='+proposal});assert(W.matches(finite,'questions'));assert(!W.matches(finite,'pending'));assert(!W.matches(finite,'prepared'));assert.equal(JSON.stringify(finite),prior);
}
assert(!W.matches(unfinished,'questions'));assert(!W.isFiniteQuestion({...record(0,0),finite_search:{...finiteMarker,answer:'found'}}));
assert.equal(B.read('#followups=questions','graph',selector).followups,'questions');
console.log('PASS prepared declarations, exact pending task counts, partial summaries, safe links, state separation, consistency rejection, legacy filters and browser export');

for(const record of data.records.filter(r=>F.recipes(r).length&&!F.available(r).length)){assert.equal(W.describe(record),null);assert(!W.matches(record,'prepared'));assert(F.render(record).includes('Review reproduction'));}
