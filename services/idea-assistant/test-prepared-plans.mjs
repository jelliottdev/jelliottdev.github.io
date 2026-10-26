/* Immutable admission bindings: real SQLite, fixed synthetic tasks, no hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import Variants from '../../task-variants.js';
import {issue,authorize} from './prepared-plans.mjs';
import {STORAGE_LIMITS} from './storage-limits.mjs';
const at='2026-10-24T12:00:00.000Z',sha=v=>createHash('sha256').update(v).digest('hex');
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const f=value=>C.field('specified',value);
function makeCard(extra={}){return H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic plan fixture'},aim:f('Measure'),
 method:f({operations:[{id:'affine',a:7,b:7}]}),scope:f({pages:['lp2-15']}),rules:{inputVersion:f('raw'),evaluation:f('measurement')},...extra}),{id:'fixture',at}));}
async function fixture(includeV9=true){
 const sqlite=new DatabaseSync(':memory:');
 for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql','0008_prepared_plans.sql','0009_word_boundary_preparations.sql']){if(!includeV9&&name==='0009_word_boundary_preparations.sql')continue;sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));}
 const db={prepare(sql){return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null};}};}},card=makeCard(),cardHash=sha(C.serialize(card)),proposalId='p_'+cardHash;
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,cardHash,C.serialize(card),'unused',at);
 const task=await E.prepare({title:'Synthetic prepared target',alphabet,pages:[{id:'lp2-15',text:'ᚠᚢ-ᚦ'}],steps:[{op:'affine',a:7,b:7}],criterion:{kind:'measurement'}});
 const controls=await Controls.prepare(task),args={db,proposalId,card,task,inputVersion:'raw',parentTaskId:null,controls,authority:'idea',basis:{kind:'compiled-card',normalizedCard:card},createdAt:at,storageLimits:{preparations:4}};
 return {sqlite,db,args};
}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('exact issued binding, timestamp-independent retries and no task/result creation',async()=>{
 const {sqlite,args}=await fixture(),before=JSON.stringify(args.card),receipt=await issue(args);
 assert.match(receipt.id,/^prep_[a-f0-9]{64}$/);assert.equal(receipt.cardHash,sha(C.serialize(args.card)));assert.equal(receipt.taskHash,sha(E.stable(args.task)));assert.equal(receipt.controlsHash,sha(E.stable(args.controls)));
 assert.equal(JSON.stringify(args.card),before);assert.deepEqual(await issue({...args,createdAt:'2026-10-25T01:00:00.000Z'}),receipt);
 assert.deepEqual(await authorize({...args,preparationId:receipt.id}),receipt);assert.deepEqual(await authorize(args),receipt);
 assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,1);
 assert.throws(()=>sqlite.prepare("UPDATE prepared_plans SET authority='remaining-lp2'").run(),/immutable/);
});
await test('legacy incomplete cards remain readable but consequential questions cannot issue or authorize preparations',async()=>{
 const {sqlite,db,args}=await fixture(),{validateCard}=await import('./idea-relations.mjs');
 for(const change of [c=>c.unresolved=[{kind:'source_note',text:'Keep every F rune unchanged.'}],c=>{c.method.value.operations=[{id:'reverse_row_runes',label:'Reverse each row'}];c.rules.wordBoundaries={status:'specified',value:'preserve'};c.rules.boundaryMode={status:'unspecified'};}]){
  const card=structuredClone(args.card);change(card);const text=C.serialize(card),hash=sha(text),proposalId='p_'+hash;sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,hash,text,'historical-unreviewed',at);assert.equal(C.serialize(validateCard(text)),text,'Read-only canonical identity must remain available');const request={...args,proposalId,card,basis:{kind:'compiled-card',normalizedCard:card}};await assert.rejects(issue(request),/Review consequential questions/);assert.equal(await authorize(request),null);assert.equal(C.serialize(card),text);
 }
 assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
});
await test('genuine concurrent issuance is idempotent and cannot exceed the global daily cap',async()=>{
 const {sqlite,args}=await fixture(),receipts=await Promise.all(Array.from({length:12},()=>issue(args)));
 assert(receipts.every(r=>r.id===receipts[0].id));assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,1);
 // Seed unrelated immutable rows to exercise the injected SQL cap without running
 // irrelevant control suites. The real receipt remains unchanged and valid.
 const row=sqlite.prepare('SELECT * FROM prepared_plans').get(),keys=Object.keys(row),insert=sqlite.prepare('INSERT INTO prepared_plans('+keys.join(',')+') VALUES('+keys.map(()=>'?').join(',')+')');
 for(let n=0;n<3;n++)insert.run(...keys.map(k=>k==='id'?'prep_'+String(n).padStart(64,'0'):row[k]));
 assert.deepEqual(await issue(args),receipts[0],'Exact retries survive a full issuance day');
 const task=await E.prepare({...args.task,title:'Another bounded task'}),controls=await Controls.prepare(task),changed={...args,task,controls};
 await assert.rejects(issue(changed),e=>e.code==='preparation-limit');assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,4);
 assert(await issue({...changed,createdAt:'2026-10-25T00:00:00.000Z'}));
});
await test('distinct concurrent preparations cannot overshoot an injected boundary and exact retries survive it',async()=>{
 const {sqlite,args}=await fixture(),requests=[];
 for(let i=0;i<6;i++){const task=await E.prepare({...args.task,title:'Concurrent preparation '+i}),controls=await Controls.prepare(task);requests.push({...args,task,controls,storageLimits:{preparations:3}});}
 const outcomes=await Promise.allSettled(requests.map(issue));assert.equal(outcomes.filter(r=>r.status==='fulfilled').length,3);assert(outcomes.filter(r=>r.status==='rejected').every(r=>r.reason.code==='preparation-limit'));
 assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,3);
 const accepted=outcomes.findIndex(r=>r.status==='fulfilled');assert.deepEqual(await issue(requests[accepted]),outcomes[accepted].value);
});
await test('production preparation capacity is bound in SQL without manufacturing thousands of receipts',async()=>{
 const {sqlite,args}=await fixture(),statements=[],db={prepare(sql){return {bind(...values){statements.push({sql,values});return {first:async()=>sqlite.prepare(sql).get(...values)||null};}};}};
 await issue({...args,db,storageLimits:undefined});
 assert.equal(statements.find(s=>s.sql.startsWith('INSERT INTO prepared_plans')).values.at(-1),STORAGE_LIMITS.preparations);
 assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,1);
});
await test('unissued, stale and altered bindings never authorize or mutate storage',async()=>{
 const {sqlite,args}=await fixture();assert.equal(await authorize(args),null);const receipt=await issue(args),before=sqlite.prepare('SELECT total_changes() n').get().n;
 for(const change of [{preparationId:'prep_'+'f'.repeat(64)},{inputVersion:'reviewed'},{parentTaskId:'f'.repeat(64)},
  {proposalId:'p_'+'f'.repeat(64)},{card:makeCard({aim:f('Explain a feature')})}])assert.equal(await authorize({...args,preparationId:receipt.id,...change}),null);
 for(const delta of [{title:'Changed title'},{steps:[{op:'affine',a:7,b:8}]},{criterion:{kind:'exact-prefix',values:[1]}},{pages:[{id:'lp2-16',text:'ᚠᚢ-ᚦ'}]}]){
  const task=await E.prepare({...args.task,...delta}),controls=await Controls.prepare(task);
  assert.equal(await authorize({...args,preparationId:receipt.id,task,controls}),null);assert.equal(await authorize({...args,task,controls}),null);
 }
 const bad=structuredClone(args.controls);bad.cases[0].expectedResultSha256='0'.repeat(64);assert.equal(await authorize({...args,controls:bad}),null);
 assert.equal(sqlite.prepare('SELECT total_changes() n').get().n,before);
});
await test('basis is immutable hashed server evidence and JSON-only; full replay rejects fabricated controls',async()=>{
 const {sqlite,args}=await fixture(),first=await issue(args);
 const mapped={kind:'mapped-card',normalizedCard:args.card,mapping:{version:1,steps:[{source:'Synthetic reviewed mapping'}],unsupported:[]}};
 const second=await issue({...args,basis:mapped});assert.notEqual(second.id,first.id);assert.deepEqual(await authorize({...args,preparationId:second.id}),second);
 const before=sqlite.prepare('SELECT total_changes() n').get().n,bad=structuredClone(args.controls);bad.targetId='f'.repeat(64);
 await assert.rejects(issue({...args,controls:bad}));
 const getter={kind:'compiled-card'};Object.defineProperty(getter,'normalizedCard',{enumerable:true,get(){throw Error('Must not invoke getter');}});
 await assert.rejects(issue({...args,basis:getter}),/data fields/);await assert.rejects(issue({...args,basis:{kind:'unknown'}}));
 assert.equal(sqlite.prepare('SELECT total_changes() n').get().n,before);
});
await test('remaining-page authority binds the original idea parent and exact unchanged protocol',async()=>{
 const {sqlite,args}=await fixture(),parent=args.task,taskJSON=E.stable(parent),taskHash=sha(taskJSON);
 sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(parent.taskId,taskHash,'0'.repeat(64),args.proposalId,C.serialize(args.card),taskJSON,'raw',null,at,at.slice(0,10));
 sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(parent.taskId,args.proposalId,'raw',null,at,at.slice(0,10));
 const task=await E.prepare({...parent,title:'Remaining scope',pages:[{id:'lp2-16',text:'ᚦᚢ'}]}),controls=await Controls.prepare(task),basis={kind:'remaining-lp2',parentTaskId:parent.taskId,parentTaskHash:taskHash,protocolHash:sha(E.stable({steps:task.steps,criterion:task.criterion,alphabet:task.alphabet})),coveredPages:['lp2-15'],remainingPages:['lp2-16']};
 const expanded={...args,task,controls,parentTaskId:parent.taskId,authority:'remaining-lp2',basis},receipt=await issue(expanded);
 assert.equal(receipt.authority,'remaining-lp2');assert.deepEqual(await authorize({...expanded,preparationId:receipt.id}),receipt);
 for(const delta of [{parentTaskHash:'0'.repeat(64)},{protocolHash:'0'.repeat(64)},{remainingPages:['lp2-17']},{coveredPages:['lp2-16']}])await assert.rejects(issue({...expanded,basis:{...basis,...delta}}));
 const unknown='f'.repeat(64);await assert.rejects(issue({...expanded,parentTaskId:unknown,basis:{...basis,parentTaskId:unknown}}));
});
await test('word-boundary authority binds exact parent, rule toggle and immutable original idea',async()=>{
 for(const criterion of [{kind:'word-prime-sums',table:'reversed',boundaries:'non-rune'},
  {kind:'word-affine-count',lag:6,a:27,b:24,boundaries:'hyphen-period'}]){
  const {sqlite,args}=await fixture(),parent=await E.prepare({...args.task,title:'Synthetic word measurement',steps:[],criterion}),taskJSON=E.stable(parent),taskHash=sha(taskJSON);
  sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(parent.taskId,taskHash,'0'.repeat(64),args.proposalId,C.serialize(args.card),taskJSON,'raw',null,at,at.slice(0,10));
  sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(parent.taskId,args.proposalId,'raw',null,at,at.slice(0,10));
  const task=await Variants.prepare(parent),controls=await Controls.prepare(task),v=Variants.inspect(parent),basis={kind:'word-boundaries',parentTaskId:parent.taskId,parentTaskHash:taskHash,from:v.from,to:v.to};
  const change={...args,task,controls,parentTaskId:parent.taskId,authority:'word-boundaries',basis},receipt=await issue(change);
  assert.equal(receipt.authority,'word-boundaries');assert.equal(receipt.cardHash,sha(C.serialize(args.card)));assert.deepEqual(await authorize({...change,preparationId:receipt.id}),receipt);
  const before=sqlite.prepare('SELECT total_changes() n').get().n;
  for(const delta of [{parentTaskHash:'0'.repeat(64)},{from:v.to},{to:v.from},{extra:1}])await assert.rejects(issue({...change,basis:{...basis,...delta}}));
  for(const delta of [{title:'Other child title'},{pages:[{id:'lp2-16',text:task.pages[0].text}]},{criterion:parent.criterion},{steps:[{op:'affine',a:1,b:0}]}]){
   const changed=await E.prepare({...task,...delta}),suite=await Controls.prepare(changed);await assert.rejects(issue({...change,task:changed,controls:suite}));
   assert.equal(await authorize({...change,task:changed,controls:suite,preparationId:receipt.id}),null);
  }
  assert.equal(sqlite.prepare('SELECT total_changes() n').get().n,before);assert.equal(sqlite.prepare('SELECT card_json FROM proposals WHERE id=?').get(args.proposalId).card_json,C.serialize(args.card));
 }
});
await test('migration nine preserves issued receipts, keys, indexes and immutability for older clients',async()=>{
 const {sqlite,args}=await fixture(false),receipt=await issue(args),rows=sqlite.prepare('SELECT * FROM prepared_plans ORDER BY id').all();
 const beforeIndexes=sqlite.prepare("SELECT name,sql FROM sqlite_master WHERE type='index' AND tbl_name='prepared_plans' ORDER BY name").all();
 const beforeFKs=sqlite.prepare('PRAGMA foreign_key_list(prepared_plans)').all();
 sqlite.exec(readFileSync(new URL('./migrations/0009_word_boundary_preparations.sql',import.meta.url),'utf8'));
 assert.deepEqual(sqlite.prepare('SELECT * FROM prepared_plans ORDER BY id').all(),rows);
 assert.deepEqual(sqlite.prepare("SELECT name,sql FROM sqlite_master WHERE type='index' AND tbl_name='prepared_plans' ORDER BY name").all(),beforeIndexes);
 assert.deepEqual(sqlite.prepare('PRAGMA foreign_key_list(prepared_plans)').all(),beforeFKs);
 assert.deepEqual(sqlite.prepare('PRAGMA foreign_key_check').all(),[]);
 assert.equal(sqlite.prepare('PRAGMA foreign_keys').get().foreign_keys,1);
 assert.deepEqual(await authorize({...args,preparationId:receipt.id}),receipt);assert.deepEqual(await authorize(args),receipt);
 assert.deepEqual(await issue(args),receipt);
 assert.throws(()=>sqlite.prepare("UPDATE prepared_plans SET authority='word-boundaries'").run(),/immutable/);
 const row=rows[0],keys=Object.keys(row),insert=sqlite.prepare('INSERT INTO prepared_plans('+keys.join(',')+') VALUES('+keys.map(()=>'?').join(',')+')');
 assert.throws(()=>insert.run(...keys.map(k=>k==='id'?'prep_'+'f'.repeat(64):k==='proposal_id'?'p_'+'f'.repeat(64):row[k])),/FOREIGN KEY/);
 assert.throws(()=>insert.run(...keys.map(k=>k==='id'?'prep_'+'f'.repeat(64):k==='parent_task_id'?'f'.repeat(64):row[k])),/FOREIGN KEY/);
 assert.throws(()=>insert.run(...keys.map(k=>k==='id'?'prep_'+'f'.repeat(64):k==='authority'?'arbitrary':row[k])),/CHECK constraint/);
});
await test('missing migration and storage faults remain errors, never an admission fallback',async()=>{
 const {sqlite,args}=await fixture();sqlite.exec('DROP TABLE prepared_plans');await assert.rejects(authorize(args),/no such table/);await assert.rejects(issue(args),/no such table/);
});
console.log('PASS '+groups+' immutable prepared-plan authorization groups; synthetic computations only, real SQLite, no hosted calls.');
