/* Selected-case authority: real SQLite, official bytes, no target computations. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
import Questions from '../../finite-program-question.js';
import Controls from '../../local-plan-controls.js';
import {compileFiniteSearch} from './finite-search-plans.mjs';
import {prepareFiniteCases,compileFiniteMember} from './finite-search-admission.mjs';
import {authorize,issue} from './prepared-plans.mjs';
const at='2026-10-25T12:00:00.000Z',sha=v=>createHash('sha256').update(v).digest('hex'),clone=v=>JSON.parse(JSON.stringify(v));
const known=v=>C.field('specified',v,{kind:'supplied',refs:['visitor:original']});
function makeCard(){return H.cardData(C.confirm(C.createDraft({source:{text:'Try affine a one or twenty-eight and b zero or one against this opening.'},aim:known('Solve LP2'),method:known({operations:[{id:'affine',label:'Affine substitution'}]}),scope:known({pages:['lp2-15','lp2-16']}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:[0,1]}),searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'a',values:[1,28]},{operation:0,name:'b',values:[0,1]}]})}}),{id:'visitor',at}));}
const selected=(a,b,pageId='lp2-15')=>({settings:[{operation:0,name:'a',value:a},{operation:0,name:'b',value:b}],pageId});
function fixture(){const sqlite=new DatabaseSync(':memory:');for(const name of readdirSync(new URL('./migrations/',import.meta.url)).filter(n=>n.endsWith('.sql')).sort())sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));const db={prepare(sql){return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null};}};}},card=makeCard(),serialized=C.serialize(card),proposalId='p_'+sha(serialized);sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,sha(serialized),serialized,'unused',at);return {sqlite,db,card,proposalId,bundle:JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),createdAt:at};}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('selected cases exactly equal canonical client selections and bind immutable original idea',async()=>{
 const f=fixture(),before=clone({card:f.card,bundle:f.bundle}),out=await prepareFiniteCases({...f,cases:[selected(1,0),selected(28,1,'lp2-16')]}),domain=(await compileFiniteSearch(f.card,f.bundle)).domain;
 assert.equal(out.cases.length,2);assert.equal(out.inputVersion,'raw');
 for(const item of out.cases){const expected=(await Questions.select(domain,[item.caseId])).cases[0];assert.deepEqual(item.task,expected.task);assert.deepEqual(item.controls,await Controls.prepare(expected.task));assert.equal(item.preparation.authority,'idea');assert.deepEqual(await authorize({...f,...item,inputVersion:'raw',parentTaskId:null,preparationId:item.preparation.id}),item.preparation);const basis=JSON.parse(f.sqlite.prepare('SELECT basis_json FROM prepared_plans WHERE id=?').get(item.preparation.id).basis_json);assert.deepEqual(basis,{kind:'finite-settings',settings:item.settings,caseId:item.caseId});}
 assert.deepEqual({card:f.card,bundle:f.bundle},before);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,1);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 assert.deepEqual(await prepareFiniteCases({...f,cases:[selected(28,1,'lp2-16'),selected(1,0)]}),out);
});
await test('invalid later cases, duplicate semantics, excessive selection and corrupt controls issue nothing',async()=>{
 for(const cases of [[selected(1,0),selected(2,0)],[selected(1,0),selected(1,0)],Array.from({length:13},()=>selected(1,0)),[selected(1,0,'lp2-17')]]){const f=fixture();await assert.rejects(prepareFiniteCases({...f,cases}));assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);}
 const f=fixture();let n=0;await assert.rejects(prepareFiniteCases({...f,cases:[selected(1,0),selected(28,1)],prepareControls:async(...args)=>{const suite=await Controls.prepare(...args);if(++n===2)suite.targetId='f'.repeat(64);return suite;}}));assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);
});
await test('changed scope, parameters, criterion, task hash or receipt cannot authorize',async()=>{
 const f=fixture(),item=(await prepareFiniteCases({...f,cases:[selected(1,0)]})).cases[0],args={...f,...item,inputVersion:'raw',parentTaskId:null,preparationId:item.preparation.id};
 for(const delta of [{inputVersion:'reviewed'},{preparationId:'prep_'+'f'.repeat(64)},{parentTaskId:'f'.repeat(64)}])assert.equal(await authorize({...args,...delta}),null);
 for(const delta of [{title:'Different task'},{steps:[{op:'affine',a:28,b:0}]},{criterion:{kind:'exact-prefix',values:[1,0]}},{pages:[{id:'lp2-16',text:item.task.pages[0].text}]}]){const task=await E.prepare({...item.task,...delta}),controls=await Controls.prepare(task);assert.equal(await authorize({...args,task,controls}),null);}
 const changed=clone(f.card);changed.scope.value.pages=['lp2-16'];assert.equal(await authorize({...args,card:changed}),null);
 for(const basis of [{kind:'finite-settings',settings:selected(28,0).settings,caseId:item.caseId},{kind:'finite-settings',settings:item.settings,caseId:'f'.repeat(64)},{kind:'finite-settings',settings:item.settings,caseId:item.caseId,extra:true}])await assert.rejects(issue({...args,authority:'idea',basis}));
});
await test('source and declaration are captured before digest, without executing targets',async()=>{
 const f=fixture();let release,started=false;const gate=new Promise(resolve=>release=resolve),crypto={subtle:{async digest(...args){if(!started){started=true;await gate;}return globalThis.crypto.subtle.digest(...args);}}},before=f.bundle.pages.find(p=>p.id==='lp2-15').raw;
 const pending=prepareFiniteCases({...f,cases:[selected(1,0)],crypto});assert(started);f.bundle.pages.find(p=>p.id==='lp2-15').raw='changed';f.card.scope.value.pages=['lp2-17'];release();const out=await pending;assert.equal(out.cases[0].task.pages[0].text,before);
 const original=E.run;let synthetic=0;E.run=task=>{assert(task.title.startsWith('Synthetic local reference '),'Admission must execute only independently generated controls');assert.deepEqual(task.pages.map(p=>p.id),['lp1-00','lp1-01']);synthetic++;return original(task);};try{const g=fixture(),out=await prepareFiniteCases({...g,cases:[selected(1,0)]});assert.equal(out.cases.length,1);assert(synthetic>0);}finally{E.run=original;}
});
await test('member compatibility and raw/reviewed settings never silently default',async()=>{
 const f=fixture();assert.deepEqual(compileFiniteMember(f.card,selected(28,1).settings).plan.steps,[{op:'affine',a:28,b:1}]);
 for(const change of [c=>c.rules.inputVersion={status:'unspecified'},c=>c.rules.evaluation=known('measurement'),c=>c.method.value.operations[0].a=1]){const c=clone(f.card);change(c);assert.throws(()=>compileFiniteMember(c,selected(1,0).settings));}
 let called=false;const bad=fixture();Object.defineProperty(bad.card.scope,'value',{enumerable:true,get(){called=true;return {};}});await assert.rejects(prepareFiniteCases({...bad,cases:[selected(1,0)]}));assert.equal(called,false);
});
console.log(groups+' finite admission groups passed; real SQLite and official source bytes, no hosted calls');
