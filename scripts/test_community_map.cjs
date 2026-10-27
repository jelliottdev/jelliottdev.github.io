'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const M=require('../community-map.js'),B=require('../research-browser-model.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),I=require('../research-index.js');
const load=name=>JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'..',name),'utf8'));
const base=B.build(load('data/research-map.json'),load('data/experiments.json')),before=JSON.stringify(base);
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
function entry(n,{aim='solve LP2',operations=[{id:'reverse_row_runes',label:'Reverse rune order within rows'}],verified=0}={}){
 const draft=C.createDraft({source:{text:'PRIVATE original'},aim:known(aim),method:known({operations}),scope:known({pages:['lp2-15']})});
 return {id:'p_'+String(n).padStart(64,'0'),card:H.cardData(C.confirm(draft,{id:'fixture',at:'2026-10-24T12:00:00.000Z'})),createdAt:'2026-10-24T12:00:00.000Z',tasks:[],taskCount:verified?11:0,verifiedTaskCount:verified};
}
const entries=[entry(1),entry(2,{verified:1}),entry(3,{aim:'test a pattern'}),entry(4,{operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'},{id:'custom',label:'Then an unspecified key rule'}]})];
const merged=M.merge(base,entries),nodes=new Map(merged.views.all.nodes.map(n=>[n.id,n]));
assert.equal(JSON.stringify(base),before,'Community navigation must not rewrite archived evidence');
assert.equal(merged.community_count,4);assert.equal(nodes.get('all-research').members.length,base.views.all.nodes.find(n=>n.id==='all-research').members.length+4);
for(const e of entries){const id='idea-'+e.id.slice(2),record=merged.records[id],leaf=nodes.get('record:'+id);assert.equal(record.href,'run.html#idea='+e.id);assert.equal(record.outcome,'');assert.equal(record.record_type.id,'idea');assert.equal(merged.views.all.nodes.filter(n=>n.record_id===id).length,1);assert(leaf);assert(!JSON.stringify(record).includes('PRIVATE'));}
assert.equal(M.label(merged.records['idea-'+entries[0].id.slice(2)]),'Untested idea');
assert.equal(merged.records['idea-'+entries[1].id.slice(2)].verified_task_count,1);assert.deepEqual(merged.records['idea-'+entries[1].id.slice(2)].task_summaries,[]);
assert.equal(M.label(merged.records['idea-'+entries[1].id.slice(2)]),'Computation available','Older verified task counts even outside displayed summaries');
assert.equal(nodes.get('record:idea-'+entries[2].id.slice(2)).parent,'aim:understand');
assert.equal(nodes.get('record:idea-'+entries[3].id.slice(2)).parent,'solve-lp2','Partially classified combinations stay at their outcome');
for(const [id,record]of Object.entries(base.records))assert.deepEqual(merged.records[id],record);
assert.equal(I.select(Object.values(merged.records),I.state(new URLSearchParams('type=idea'))).allRecords.length,4);
assert.throws(()=>M.merge(base,[entries[0],entries[0]]));
for(const mutation of [e=>e.verifiedTaskCount=-1,e=>e.verifiedTaskCount=12,e=>e.card.method.value.operations[0].label='<script>opaque</script>']){
 const e=structuredClone(entries[1]);mutation(e);if(e.verifiedTaskCount<0||e.verifiedTaskCount>e.taskCount)assert.throws(()=>M.validate({schema:'liberpedia-community-research-v1',entries:[e],nextCursor:null}));
 else assert.equal(M.merge(base,[e]).records['idea-'+e.id.slice(2)].title,'<script>opaque</script>');
}
const inconsistent=structuredClone(entries[1]);inconsistent.tasks=[{id:'b'.repeat(64),title:'Synthetic pending',state:'not-run'}];inconsistent.taskCount=1;inconsistent.verifiedTaskCount=1;assert.throws(()=>M.validate({schema:'liberpedia-community-research-v1',entries:[inconsistent],nextCursor:null}));
const shared=entry(9,{aim:'measure a pattern'});shared.hasSharedComputation=true;const sharedRecord=M.merge(base,[shared]).records['idea-'+shared.id.slice(2)];assert.equal(M.label(sharedRecord),'Computation available');assert.equal(sharedRecord.task_count,0);assert.equal(sharedRecord.verified_task_count,0);assert.deepEqual(sharedRecord.task_summaries,[]);
const notShared=structuredClone(shared);notShared.hasSharedComputation=false;assert.equal(M.label(M.merge(base,[notShared]).records['idea-'+shared.id.slice(2)]),'Untested idea');
for(const value of ['true',1,null,{}])assert.throws(()=>M.validate({schema:'liberpedia-community-research-v1',entries:[{...shared,hasSharedComputation:value}],nextCursor:null}));
const Work=require('../research-work.js');
const finiteCard=H.cardData(C.confirm(C.createDraft({source:{text:'Try these explicit settings.'},aim:known('Solve LP2'),method:known({operations:[{id:'affine',label:'Affine substitution',b:0}]}),scope:known({pages:['lp2-15']}),rules:{searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'a',values:[1,2]}]}),inputVersion:known('raw'),evaluation:known({kind:'exact-prefix',values:[0,1]})}}),{id:'finite',at:'2026-10-25T12:00:00.000Z'}));
for(const patch of [
 {taskCount:0,verifiedTaskCount:0,tasks:[]},
 {taskCount:2,verifiedTaskCount:1,tasks:[{id:'c'.repeat(64),title:'Saved matching member',state:'results-verified'},{id:'d'.repeat(64),title:'Intentionally unrun after match',state:'not-run'}]},
 {taskCount:0,verifiedTaskCount:0,tasks:[],hasSharedComputation:true}
]){
 const original={...entry(20),card:finiteCard,...patch},record=M.merge(base,[original]).records['idea-'+original.id.slice(2)];assert.deepEqual(record.finite_search,{kind:'finite-settings',version:1});assert.equal(record.evidence_state,'question-review');assert.equal(M.label(record),'Review question');assert.equal(Work.describe(record).href,'run.html#idea='+original.id);assert.equal(Work.describe(record).kind,'question');assert(Work.matches(record,'questions'));assert(!Work.matches(record,'pending'));assert(!JSON.stringify(record).includes('prefix-found'));
}
const fabricated={...entry(21),finite_search:{kind:'finite-settings',version:1}};assert.throws(()=>M.validate({schema:'liberpedia-community-research-v1',entries:[fabricated],nextCursor:null}),'A caller flag cannot replace the decoded original card');
console.log('PASS community map preserves evidence, routes active cards, separates computation state, filters and validates');

// Same operation, different evaluation: distinguish the questions without a
// fabricated finding or a claim that task counts establish question coverage.
{
 const check=criterion=>H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic stated idea'},aim:known('Solve LP2'),method:known({operations:[{id:'reverse_runes',label:'Reverse each row',unit:'line'}]}),scope:known({pages:['lp2-15']}),rules:{evaluation:known(criterion)}}),{id:'purpose',at:'2026-10-25T12:00:00.000Z'}));
 const opening={...entry(30),card:check(C.EVALUATION_CHOICES.find(c=>c.id==='warning-opening').value)},language={...entry(31),card:check(C.EVALUATION_CHOICES.find(c=>c.id==='language-samples').value)},before=JSON.stringify([opening,language]),mapped=M.merge(base,[opening,language]),a=mapped.records['idea-'+opening.id.slice(2)],b=mapped.records['idea-'+language.id.slice(2)];
 assert.equal(a.title,b.title,'The original literal method titles stay unchanged');assert.notEqual(a.reader_title,b.reader_title,'The displayed question identities include their different checks');assert(a.reader_intro.includes('first 12 runes'));assert(b.reader_intro.includes('similarity is not a translation'));assert(a.reader_finding.includes('No saved result is listed'));assert(!/no match|not supported|unanswered|solved/i.test(a.reader_finding));assert.equal(JSON.stringify([opening,language]),before);
 const saved={...language,verifiedTaskCount:1,taskCount:1,tasks:[{id:'e'.repeat(64),title:'Synthetic saved check',state:'results-verified'}]},record=M.merge(base,[saved]).records['idea-'+saved.id.slice(2)];assert(record.reader_finding.includes('Open the idea'));assert(!/complete|matching|readable|passed/i.test(record.reader_finding));
 console.log('PASS community question labels distinguish evaluation and keep task availability separate from scientific findings.');
}

// Key material alone cannot select a cipher branch in the method navigation.
{
 const cases=[
  [{id:'finite_key',label:'Finite key stream',key:[1,2],direction:'subtract',reset:'page'},'method:running-key'],
  [{id:'repeating_key',label:'Repeating key',key:[1,2],direction:'subtract',reset:'page'},'method:repeating-key'],
  [{id:'plaintext_autokey',label:'Plaintext autokey',key:[1,2],direction:'subtract',reset:'page'},'method:feedback'],
  [{id:'family_selection',familyId:'number-streams',label:C.METHOD_FAMILIES['number-streams']},'solve-lp2'],
  [{id:'book_code',label:'Book code'},'solve-lp2'],
  [{id:'prime_value_mapping',label:'Prime value mapping'},'method:direct-mapping']
 ];
 for(let i=0;i<cases.length;i++){
  const [op,parent]=cases[i],e=entry(100+i,{operations:[op]}),prior=JSON.stringify(e),mapped=M.merge(base,[e]),leaf=mapped.views.all.nodes.find(n=>n.record_id==='idea-'+e.id.slice(2));
  assert.equal(leaf.parent,parent,op.id);assert.equal(JSON.stringify(e),prior);assert.equal(mapped.records[leaf.record_id].outcome,'');
 }
 console.log('PASS community method navigation separates finite, repeating and feedback application; source-only labels cannot imply a cipher.');
}
