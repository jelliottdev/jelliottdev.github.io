/* Fixed measurement comparisons: real SQLite, synthetic text, no hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import Variants from '../../task-variants.js';
import {canonicalProposal} from './proposals.mjs';
import {issue,authorize} from './prepared-plans.mjs';
import {createTaskVariantHandler} from './task-variants.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import {boundaryComparison} from './boundary-comparison.mjs';
import {findEvidence} from './task-evidence.mjs';
const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const sha=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
function fixture({migration9=true,discoverEvidence}={}){
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql','0008_prepared_plans.sql',...(migration9?['0009_word_boundary_preparations.sql']:[]),'0010_family_case_results.sql','0011_task_protocol_lookup.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 const queries=[],rates=[],db={prepare(sql){queries.push(sql);return {bind(...args){return {sql,args,first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{const out=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return out;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};
 const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async v=>{rates.push(v);return {success:true};}},AI:{run(){throw Error('No model call allowed');}}};
 return {sqlite,db,env,queries,rates,handle:createTaskVariantHandler({now:()=>new Date(at),discoverEvidence})};
}
async function addIdea(f,{name='fixture',published=true}={}){
 const draft=C.createDraft({source:{text:'PRIVATE original '+name},aim:known({outcomeId:'measure',wording:'Measure',detail:name}),method:known({operations:[{id:'word_prime_sums',label:'Word prime sums',table:'canonical',boundaries:'non-rune'}]}),scope:known({pages:['lp2-15']})});
 const p=await canonicalProposal({requestId:crypto.randomUUID(),fragment:H.encode(C.confirm(draft,{id:name,at}))});
 f.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(p.id,p.cardHash,p.cardJson,p.fragment,at);if(published)f.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(p.id,at,at.slice(0,10));return p;
}
async function insert(f,p,task,{saved=true,version='raw',parentTaskId=null}={}){
 const text=L.stable(task);f.sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(task.taskId,await sha(text),'0'.repeat(64),p.id,p.cardJson,text,version,parentTaskId,at,at.slice(0,10));
 await associate(f,p,task,{version,parentTaskId});
 if(saved){const result=L.stable(L.run(task));f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run(await sha(result),task.taskId,result,at,at.slice(0,10));}return task;
}
async function associate(f,p,task,{version='raw',parentTaskId=null}={}){f.sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(task.taskId,p.id,version,parentTaskId,at,at.slice(0,10));}
async function parent(f,p,{kind='word-prime-sums',boundaries='non-rune',steps=[],saved=true,version='raw'}={}){
 const criterion=kind==='word-prime-sums'?{kind,table:'reversed',boundaries}:kind==='word-affine-count'?{kind,lag:1,a:2,b:3,boundaries}:{kind};
 return insert(f,p,await L.prepare({title:'Synthetic word measurement',pages:[{id:'lp2-15',text:'ᚠᚢ /\r\nᚦ-ᚩ.ᚠ'}],alphabet,steps,criterion}),{saved,version});
}
const request=(id,{body={variant:'word-boundaries'},method='POST',headers={},path='/tasks/'+id+'/variants'}={})=>new Request('https://worker.example'+path,{method,headers:{origin,'content-type':'application/json',...headers},...(method==='POST'?{body:typeof body==='string'?body:JSON.stringify(body)}:{})});
async function call(f,t,options){const response=await f.handle(request(t.taskId,options),f.env);return {response,value:response.status===204?null:await response.json()};}
async function noTargets(fn){const original=L.run;L.run=t=>{assert.match(t.title,/^Synthetic local reference 1:/,'Planning must never run a target');return original(t);};try{return await fn();}finally{L.run=original;}}
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
await test('both measurement kinds and boundary directions produce exact source-bound child receipts without target execution',async()=>{
 for(const kind of ['word-prime-sums','word-affine-count'])for(const boundaries of ['non-rune','hyphen-period']){
  const f=fixture(),p=await addIdea(f),t=await parent(f,p,{kind,boundaries}),before=f.sqlite.prepare('SELECT * FROM local_tasks').all(),results=f.sqlite.prepare('SELECT * FROM local_task_results').all();
  const {response,value}=await noTargets(()=>call(f,t));assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.equal(value.proposalId,p.id);assert.equal(value.parentTaskId,t.taskId);assert.equal(value.from,boundaries);assert.notEqual(value.to,boundaries);assert.equal(value.variant,'word-boundaries');
  assert.deepEqual(value.task,await Variants.prepare(t));assert.equal(value.preparation.authority,'word-boundaries');await Controls.validate(value.controls,value.task);
  assert(await authorize({db:f.db,preparationId:value.preparation.id,proposalId:p.id,card:JSON.parse(p.cardJson),task:value.task,inputVersion:'raw',parentTaskId:t.taskId,controls:value.controls}));
  assert.deepEqual(f.sqlite.prepare('SELECT * FROM local_tasks').all(),before);assert.deepEqual(f.sqlite.prepare('SELECT * FROM local_task_results').all(),results);assert(!JSON.stringify(value).includes('PRIVATE'));
  const again=await noTargets(()=>call(f,t));assert.deepEqual(again.value,value);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,1);
 }
});
await test('saved original result is required before controls or receipt creation',async()=>{
 const f=fixture(),p=await addIdea(f),t=await parent(f,p,{saved:false}),before=f.sqlite.prepare('SELECT total_changes() n').get().n;
 const {response,value}=await noTargets(()=>call(f,t));assert.equal(response.status,200);assert.equal(value.state,'runs-pending');assert.deepEqual(value.pendingTasks,[{id:t.taskId,pages:['lp2-15']}]);assert(!Object.hasOwn(value,'task'));assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
});
await test('public associated context is selected without exposing private original card or version',async()=>{
 const f=fixture(),hidden=await addIdea(f,{published:false}),t=await parent(f,hidden);
 assert.equal((await call(f,t)).response.status,404);const p=await addIdea(f,{name:'public'});await associate(f,p,t,{version:'reviewed'});
 const {value}=await noTargets(()=>call(f,t));assert.equal(value.proposalId,p.id);assert.equal(value.inputVersion,'reviewed');assert.equal(value.preparation.cardHash,p.cardHash);assert(!JSON.stringify(value).includes(hidden.id));
});
await test('existing exact comparisons reopen without receipt writes; conflicting stored versions fail',async()=>{
 for(const version of ['raw','reviewed']){
  const f=fixture(),p=await addIdea(f),t=await parent(f,p),child=await Variants.prepare(t);await insert(f,p,child,{version,saved:false});const before=f.sqlite.prepare('SELECT total_changes() n').get().n;
  const {response,value}=await noTargets(()=>call(f,t));assert.equal(response.status,version==='raw'?200:409);if(version==='raw'){assert.equal(value.state,'existing-task');assert.equal(value.taskId,child.taskId);}assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 }
});
await test('repeated toggles reopen canonical original without changing either association parent',async()=>{
 const f=fixture(),p=await addIdea(f),seed=await parent(f,p),opposite=await Variants.prepare(seed),canonical=await Variants.prepare(opposite);
 await insert(f,p,canonical,{parentTaskId:null});await insert(f,p,opposite,{parentTaskId:canonical.taskId});
 const links=f.sqlite.prepare('SELECT * FROM local_task_ideas ORDER BY task_id').all(),before=f.sqlite.prepare('SELECT total_changes() n').get().n;
 const {response,value}=await noTargets(()=>call(f,opposite));assert.equal(response.status,200);assert.equal(value.state,'scope-covered');assert([canonical.taskId,seed.taskId].includes(value.coverage.exactTaskId));assert.deepEqual(value.coverage.remainingPages,[]);
 assert.deepEqual(f.sqlite.prepare('SELECT * FROM local_task_ideas ORDER BY task_id').all(),links);assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before+1,'Only the complete requested comparison is remembered');assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);
});
await test('new comparison receipt is admitted through unchanged generic task endpoint and cannot authorize changed measurement',async()=>{
 const f=fixture(),p=await addIdea(f),t=await parent(f,p),{value}=await noTargets(()=>call(f,t));let fetches=0;
 const handle=createLocalTaskHandler({now:()=>new Date(at),fetcher:async url=>{fetches++;assert.equal(url,origin+'/data/pages/lp2-15.json');return Response.json({id:'lp2-15',raw:t.pages[0].text});}});
 const create=async task=>handle(new Request('https://worker.example/tasks',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify({proposalId:p.id,task,inputVersion:'raw',parentTaskId:t.taskId,preparationId:value.preparation.id})}),f.env);
 const changed=await L.prepare({...value.task,criterion:{...value.task.criterion,table:'canonical'}});assert.equal((await create(changed)).status,409);assert.equal(fetches,0);
 const response=await create(value.task);assert.equal(response.status,200,await response.clone().text());assert.equal(fetches,1);const opened=await call(f,t);assert.equal(opened.value.state,'existing-task');assert.equal(opened.value.taskId,value.task.taskId);
});
await test('unsupported transforms and criteria cannot turn into a boundary comparison',async()=>{
 for(const options of [{kind:'measurement'},{steps:[{op:'reverse',unit:'line'}]}]){const f=fixture(),p=await addIdea(f),t=await parent(f,p,options),{response}=await noTargets(()=>call(f,t));assert.equal(response.status,422);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);}
});
await test('stored task, public card, result and existing-child corruption fail closed',async()=>{
 for(const damage of [async(f,p,t)=>f.sqlite.prepare('UPDATE local_tasks SET task_hash=? WHERE id=?').run('f'.repeat(64),t.taskId),async f=>f.sqlite.prepare('UPDATE proposals SET card_hash=?').run('0'.repeat(64)),async f=>f.sqlite.prepare('UPDATE local_task_results SET result_json=?').run('{}'),async(f,p,t)=>{const child=await Variants.prepare(t);await insert(f,p,child);f.sqlite.prepare('UPDATE local_tasks SET task_hash=? WHERE id=?').run('f'.repeat(64),child.taskId);},async f=>f.sqlite.exec('DROP TABLE prepared_plans')]){
  const f=fixture(),p=await addIdea(f),t=await parent(f,p);await damage(f,p,t);assert.equal((await noTargets(()=>call(f,t))).response.status,503);
 }
});
await test('origin, body, duplicate JSON keys, route, method and configuration are strict; rate gate precedes DB',async()=>{
 const f=fixture(),p=await addIdea(f),t=await parent(f,p);
 assert.equal((await call(f,t,{headers:{origin:'https://evil.example'}})).response.status,403);
 for(const body of [null,[],{variant:'other'},{variant:'word-boundaries',steps:[]},'{"variant":"word-boundaries","variant":"word-boundaries"}',{variant:'x'.repeat(1100)}])assert.equal((await call(f,t,{body})).response.status,400);
 for(const method of ['GET','PUT','DELETE'])assert.equal((await call(f,t,{method})).response.status,405);
 for(const path of ['/tasks/bad/variants','/tasks/'+t.taskId+'/variants?extra=1'])assert.equal((await call(f,t,{path})).response.status,404);
 const pre=await f.handle(request(t.taskId,{method:'OPTIONS',headers:{'access-control-request-method':'POST','access-control-request-headers':'content-type'}}),f.env);assert.equal(pre.status,204);
 assert.equal(f.queries.length,0);assert.equal(f.rates.length,0);
 assert.equal((await f.handle(request(t.taskId),{...f.env,TASK_LIMIT:{limit:async()=>({success:false})}})).status,429);assert.equal(f.queries.length,0);
 for(const key of ['SITE_ORIGIN','PROPOSALS','TASK_LIMIT'])assert.equal((await f.handle(request(t.taskId),{...f.env,[key]:undefined})).status,503);
 assert.equal((await f.handle(request('0'.repeat(64)),f.env)).status,404);
});
await test('migration9 preserves old receipt rows, indices, foreign keys and immutability while adding only new authority',async()=>{
 const f=fixture({migration9:false}),p=await addIdea(f),t=await parent(f,p),controls=await Controls.prepare(t);
 const receipt=await issue({db:f.db,proposalId:p.id,card:JSON.parse(p.cardJson),task:t,inputVersion:'raw',parentTaskId:null,controls,authority:'idea',basis:{kind:'compiled-card',normalizedCard:JSON.parse(p.cardJson)},createdAt:at});
 const before=f.sqlite.prepare('SELECT * FROM prepared_plans').all();f.sqlite.exec(readFileSync(new URL('./migrations/0009_word_boundary_preparations.sql',import.meta.url),'utf8'));assert.deepEqual(f.sqlite.prepare('SELECT * FROM prepared_plans').all(),before);
 assert(await authorize({db:f.db,preparationId:receipt.id,proposalId:p.id,card:JSON.parse(p.cardJson),task:t,inputVersion:'raw',parentTaskId:null,controls}));
 assert.throws(()=>f.sqlite.prepare('UPDATE prepared_plans SET created_day=?').run('2026-10-25'),/immutable/);assert.equal(f.sqlite.prepare('PRAGMA foreign_key_check').all().length,0);
 const indices=f.sqlite.prepare('PRAGMA index_list(prepared_plans)').all().map(r=>r.name);assert(indices.includes('prepared_plans_binding'));assert(indices.includes('prepared_plans_day'));
 assert.equal((await noTargets(()=>call(f,t))).value.preparation.authority,'word-boundaries');
});
await test('read-only opposite-boundary lookup exposes exact public proof without target execution or new records',async()=>{
 const f=fixture(),p=await addIdea(f),t=await parent(f,p,{kind:'word-affine-count'}),opposite=await Variants.prepare(t),other=await addIdea(f,{name:'another category'}),source=await L.prepare({...opposite,title:'A different idea already checked this grouping'});await insert(f,other,source);
 const before=f.sqlite.prepare('SELECT total_changes() n').get().n,value=await noTargets(()=>boundaryComparison({db:f.db,task:t,inputVersion:'raw'}));
 assert.deepEqual(value.task,opposite);assert.deepEqual(value.coverage.requestedTask,opposite);assert.deepEqual(value.coverage.coveredPages,['lp2-15']);assert.equal(value.coverage.exactTaskId,source.taskId);assert(!value.coverageUnavailable);assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 for(const altered of [await L.prepare({...t,steps:[{op:'affine',a:1,b:0}]}),await L.prepare({...t,criterion:{kind:'measurement'}}),await L.prepare({...t,criterion:{kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'}})])assert.equal(await boundaryComparison({db:f.db,task:altered,inputVersion:'raw'}),null);
 const unavailable=await boundaryComparison({db:f.db,task:t,inputVersion:'raw',discoverEvidence:async()=>{throw Error('Unavailable');}});assert.deepEqual(unavailable,{task:opposite,coverageUnavailable:true});
 const incomplete=await boundaryComparison({db:f.db,task:t,inputVersion:'raw',discoverEvidence:async args=>({...await findEvidence(args),coveredPages:[],remainingPages:['lp2-15'],evidence:[],exactTaskId:null,truncated:true})});assert.equal(incomplete.coverageUnavailable,true);assert.equal(incomplete.coverage.truncated,true);assert.deepEqual(incomplete.task,opposite);
});
await test('dedicated GET boundary route works for saved and pending originals without recursive default GET work',async()=>{
 for(const saved of [true,false]){
  const f=fixture(),p=await addIdea(f),t=await parent(f,p,{kind:'word-affine-count',saved}),opposite=await Variants.prepare(t),other=await addIdea(f,{name:'public source'});await insert(f,other,await L.prepare({...opposite,title:'Existing opposite boundary'}));
  const discoveries=[],handle=createLocalTaskHandler({discoverEvidence:async args=>{discoveries.push(args.task.taskId);return findEvidence(args);}}),before=f.sqlite.prepare('SELECT total_changes() n').get().n;
  const response=await noTargets(()=>handle(request(t.taskId,{method:'GET',path:'/tasks/'+t.taskId+'/boundary-comparison'}),f.env));assert.equal(response.status,200);const comparison=await response.json();assert.deepEqual(comparison.task,opposite);assert.deepEqual(comparison.coverage.coveredPages,['lp2-15']);assert.deepEqual(discoveries,[opposite.taskId]);
  discoveries.length=0;const main=await handle(request(t.taskId,{method:'GET',path:'/tasks/'+t.taskId}),f.env);assert.equal(main.status,200);assert(!Object.hasOwn(await main.json(),'boundaryComparison'));assert(!discoveries.includes(opposite.taskId));assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
  assert.equal((await handle(request(t.taskId,{method:'POST',path:'/tasks/'+t.taskId+'/boundary-comparison'}),f.env)).status,405);assert.equal((await handle(request(t.taskId,{method:'GET',path:'/tasks/'+t.taskId+'/boundary-comparison?extra=1'}),f.env)).status,404);
 }
});
await test('shared complete boundary proof skips a duplicate while partial proof admits only its immutable remainder',async()=>{
 const f=fixture(),p=await addIdea(f),base=await parent(f,p,{kind:'word-affine-count'}),pages=[...base.pages,{id:'lp2-16',text:'ᚢᚦ /ᚠ-ᚩ'}],t=await insert(f,p,await L.prepare({...base,title:'Two requested pages',pages})),opposite=await Variants.prepare(t),other=await addIdea(f,{name:'shared first page'}),first=await L.prepare({...opposite,title:'Separate first-page result',pages:[opposite.pages[0]]});await insert(f,other,first);
 const {response,value}=await noTargets(()=>call(f,t));assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.deepEqual(value.coverage.coveredPages,['lp2-15']);assert.deepEqual(value.coverage.requestedTask,opposite);assert.deepEqual(value.task.pages,[pages[1]]);assert.deepEqual(value.task.criterion,opposite.criterion);assert.equal(value.preparation.authority,'word-boundaries');
 const basis=JSON.parse(f.sqlite.prepare('SELECT basis_json FROM prepared_plans WHERE id=?').get(value.preparation.id).basis_json);assert.equal(basis.requestedTaskId,opposite.taskId);assert.equal(basis.evidence[0].taskId,first.taskId);
 const admission={db:f.db,proposalId:p.id,card:JSON.parse(p.cardJson),task:value.task,inputVersion:'raw',parentTaskId:t.taskId,controls:value.controls,authority:'word-boundaries',createdAt:at};assert(await authorize({...admission,preparationId:value.preparation.id}));
 const bad=structuredClone(basis);bad.evidence[0].pages=['lp2-16'];await assert.rejects(issue({...admission,basis:bad}));
 const changed=await L.prepare({...value.task,criterion:{...value.task.criterion,boundaries:t.criterion.boundaries}});await assert.rejects(issue({...admission,task:changed,controls:await Controls.prepare(changed),basis}));
 const handle=createLocalTaskHandler({fetcher:async url=>{const id=/([^/]+)\.json$/.exec(url)[1];return Response.json({id,raw:pages.find(p=>p.id===id).text});}});
 const created=await handle(new Request('https://worker.example/tasks',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify({proposalId:p.id,task:value.task,inputVersion:'raw',parentTaskId:t.taskId,preparationId:value.preparation.id})}),f.env);assert.equal(created.status,200,await created.clone().text());assert.deepEqual((await created.json()).card,JSON.parse(p.cardJson));
 const result=L.run(value.task),submitted=await handle(new Request('https://worker.example/tasks/'+value.task.taskId+'/results',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify({result})}),f.env);assert.equal(submitted.status,200);
 const preparations=f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,complete=await noTargets(()=>call(f,t));assert.equal(complete.value.state,'scope-covered');assert.deepEqual(complete.value.coverage.remainingPages,[]);assert.equal(complete.value.coverage.evidence.length,2);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,preparations);
});
await test('incomplete boundary evidence never authorizes an uncertain duplicate comparison',async()=>{
 const f=fixture({discoverEvidence:async args=>({...await findEvidence(args),truncated:true})}),p=await addIdea(f),t=await parent(f,p,{kind:'word-affine-count'}),before=f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n;
 const {response,value}=await noTargets(()=>call(f,t));assert.equal(response.status,503);assert.equal(value.state,'coverage-unavailable');assert.equal(value.coverageUnavailable,true);assert.equal(value.coverage.truncated,true);assert.deepEqual(value.coverage.requestedTask,await Variants.prepare(t));assert(!Object.hasOwn(value,'task'));assert(!Object.hasOwn(value,'preparation'));assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,before);
});
console.log('PASS '+groups+' fixed word-boundary variant endpoint groups; synthetic inputs, no hosted calls or target planning execution.');
