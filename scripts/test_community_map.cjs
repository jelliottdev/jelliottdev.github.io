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
console.log('PASS community map preserves evidence, routes active cards, separates computation state, filters and validates');
