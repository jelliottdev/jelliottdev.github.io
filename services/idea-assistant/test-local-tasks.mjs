import {createHash} from 'node:crypto';
import {issue as issuePreparation} from './prepared-plans.mjs';
/* Real SQLite persistence, mocked official page fetches. No hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import L from '../../local-experiment.js';
import PlanControls from '../../local-plan-controls.js';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import {planCard} from './prepare-task.mjs';
import {STORAGE_LIMITS} from './storage-limits.mjs';
let proposalId;
const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const alphabet=Array.from({length:29},(_,i)=>({rune:String.fromCharCode(65+i),latin:'R'+i,prime:i+2}));
const source={id:'lp2-15',raw:'ABC A\nBA',reviewed_text:'ABC B\nBA'};
const card=H.cardData(C.confirm(C.createDraft({source:{text:'PRIVATE ORIGINAL'},method:C.field('specified',{operations:[{id:'described_method',label:'Reverse rows'}]},{kind:'supplied',refs:['source:text']})}),{id:'test',at}));
function adapter({publicOriginal=true}={}){
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql','0008_prepared_plans.sql','0009_word_boundary_preparations.sql','0010_family_case_results.sql','0011_task_protocol_lookup.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 proposalId='p_'+createHash('sha256').update(C.serialize(card)).digest('hex');
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,proposalId.slice(2),C.serialize(card),'unused',at);
 if(publicOriginal)sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(proposalId,at,at.slice(0,10));
 const db={sqlite,reads:0,fail:false,prepare(sql){return {bind(...args){return {sql,args,first:async()=>{db.reads++;return sqlite.prepare(sql).get(...args)||null;},all:async()=>{db.reads++;return {results:sqlite.prepare(sql).all(...args)};},run:async()=>sqlite.prepare(sql).run(...args)};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{if(db.fail)throw Error('Injected storage failure');const result=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return result;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};return db;
}
function fixture(options){
 const db=adapter(options),urls=[],rates=[];let date=at,fetchFailure=false;
 const env={SITE_ORIGIN:origin,PROPOSALS:db,PROPOSAL_LIMIT:{limit:async value=>{rates.push(value);return {success:true};}}};
 const handle=createLocalTaskHandler({storageLimits:{tasks:50,results:50,taskIdeaLinks:50},now:()=>new Date(date),fetcher:async(url,options)=>{urls.push(url);assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'manual');assert(options.signal);if(fetchFailure)throw Error('Offline');return Response.json(source);}});
 return {db,env,handle,urls,rates,setDate:value=>date=value,setFetchFailure:value=>fetchFailure=value};
}
async function task(title='Reverse rows',version='raw',extra={}){return L.prepare({title,pages:[{id:source.id,text:version==='raw'?source.raw:source.reviewed_text}],alphabet,steps:[{op:'reverse',unit:'line'}],criterion:{kind:'measurement'},...extra});}
const body=task=>({proposalId,task,inputVersion:'raw',parentTaskId:null});
const request=(path,method='GET',data,extra={})=>new Request('https://worker.example'+path,{method,headers:{origin,...(data!==undefined?{'content-type':'application/json'}:{}),'CF-Connecting-IP':'203.0.113.9',...extra},...(data!==undefined?{body:JSON.stringify(data)}:{})});
const call=(f,path,method,data,extra)=>f.handle(request(path,method,data,extra),f.env);
// Trusted unit fixture setup only: issuance is explicit and never part of call().
async function approved(f,data){
 try{L.validateTask(data.task);await L.checkIdentity(data.task);}catch{return data;}
 const row=f.db.sqlite.prepare('SELECT card_json FROM proposals WHERE id=?').get(data.proposalId);
 if(!row||Object.hasOwn(data,'origin')||Object.keys(data).some(k=>!['proposalId','task','inputVersion','parentTaskId'].includes(k))||!['raw','reviewed'].includes(data.inputVersion))return data;
 if(data.parentTaskId&&!f.db.sqlite.prepare('SELECT 1 FROM local_task_ideas WHERE task_id=? AND proposal_id=?').get(data.parentTaskId,data.proposalId))return data;
 const stored=JSON.parse(row.card_json),controls=await PlanControls.prepare(data.task);
 await issuePreparation({db:f.db,proposalId:data.proposalId,card:stored,task:data.task,inputVersion:data.inputVersion,parentTaskId:data.parentTaskId,controls,authority:'idea',basis:{kind:'compiled-card',normalizedCard:stored},createdAt:at});
 return data; // Deliberately exercise old-client exact-previous-issuance lookup.
}
async function preparedCall(f,path,method,data,extra){return call(f,path,method,await approved(f,data),extra);}

let count=0;async function test(name,fn){await fn();console.log('PASS '+name);count++;}
await test('strict origin, routes, methods, bindings and preflight fail closed',async()=>{
 const f=fixture();assert.equal((await call(f,'/tasks','POST',body(await task()),{origin:'https://evil.example'})).status,403);
 assert.equal((await call(f,'/tasks','POST',body(await task()),{origin:''})).status,403);
 assert.equal((await call(f,'/tasks','GET')).status,405);assert.equal((await call(f,'/tasks/nope')).status,404);
 for(const key of ['PROPOSALS','PROPOSAL_LIMIT','SITE_ORIGIN'])assert.equal((await f.handle(request('/tasks','POST',body(await task())),{...f.env,[key]:null})).status,503);
 const pre=new Request('https://worker.example/tasks',{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}});
 assert.equal((await f.handle(pre,f.env)).status,204);assert.equal(f.db.reads,0);assert.equal(f.rates.length,0);
});
await test('only exact server-issued plans admit new generic tasks or idea associations',async()=>{
 const f=fixture(),t=await task(),before=f.db.sqlite.prepare('SELECT total_changes() n').get().n;
 const missing=await call(f,'/tasks','POST',body(t));assert.equal(missing.status,409);assert.match((await missing.json()).error,/prepared plan/);
 assert.equal(f.urls.length,0);assert.equal(f.db.sqlite.prepare('SELECT total_changes() n').get().n,before);
 await approved(f,body(t));const preparationId=f.db.sqlite.prepare('SELECT id FROM prepared_plans').get().id;
 const mutations=[await task('Changed title'),await task('Reverse rows','raw',{steps:[{op:'reverse',unit:'word'}]}),await task('Reverse rows','raw',{criterion:{kind:'exact-prefix',values:[0]}}),await task('Reverse rows','raw',{pages:[{id:'lp2-14',text:source.raw}]}),await task('Reverse rows','raw',{alphabet:alphabet.map((r,i)=>({...r,prime:r.prime+(i===0?100:0)}))})];
 const writes=f.db.sqlite.prepare('SELECT total_changes() n').get().n;
 for(const changed of mutations)assert.equal((await call(f,'/tasks','POST',{...body(changed),preparationId})).status,409);
 assert.equal((await call(f,'/tasks','POST',{...body(t),inputVersion:'reviewed',preparationId})).status,409);
 assert.equal((await call(f,'/tasks','POST',{...body(t),preparationId:'prep_'+'f'.repeat(64)})).status,409);
 for(const invalid of [null,4,{},'wrong'])assert.equal((await call(f,'/tasks','POST',{...body(t),preparationId:invalid})).status,400);
 assert.equal((await call(f,'/tasks','POST',{...body(t),preparationId,origin:{}})).status,400);
 assert.equal(f.db.sqlite.prepare('SELECT total_changes() n').get().n,writes);assert.equal(f.urls.length,0);
 const second=addIdea(f,'different idea'),afterIdea=f.db.sqlite.prepare('SELECT total_changes() n').get().n;
 assert.equal((await call(f,'/tasks','POST',{...body(t),proposalId:second,preparationId})).status,409);
 assert.equal(f.db.sqlite.prepare('SELECT total_changes() n').get().n,afterIdea);
 assert.equal((await call(f,'/tasks','POST',{...body(t),preparationId})).status,200);
 assert.equal((await call(f,'/tasks','POST',{...body(t),proposalId:second,preparationId})).status,409,'Existing computation does not authorize a new idea association');
 await approved(f,{...body(t),proposalId:second});assert.equal((await call(f,'/tasks','POST',{...body(t),proposalId:second})).status,200);
 assert.equal((await call(f,'/tasks','POST',body(t))).status,200,'Exact existing link retry needs no new receipt');
 const other=await task('Child'),parentData={...body(other),parentTaskId:t.taskId};await approved(f,parentData);
 const parentReceipt=f.db.sqlite.prepare('SELECT id FROM prepared_plans WHERE task_id=?').get(other.taskId).id;
 assert.equal((await call(f,'/tasks','POST',{...body(other),preparationId:parentReceipt})).status,409,'Parent cannot be discarded from the issued binding');
 assert.equal((await call(f,'/tasks','POST',{...parentData,preparationId:parentReceipt})).status,200);
 const unavailable=fixture();unavailable.db.sqlite.exec('DROP TABLE prepared_plans');
 assert.equal((await call(unavailable,'/tasks','POST',body(await task()))).status,503);
 assert.equal(unavailable.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(unavailable.urls.length,0);
});
await test('create/GET exact task, card reference and source text; no original idea projected',async()=>{
 const f=fixture(),t=await task(),response=await preparedCall(f,'/tasks','POST',body(t)),r=await response.json();assert.equal(response.status,200);
 assert.equal(r.id,t.taskId);assert.equal(r.state,'not-run');assert.deepEqual(r.plan,t);assert.deepEqual(r.card,card);assert(!JSON.stringify(r).includes('PRIVATE'));
 assert.match(r.verification,/computation only/);assert.equal(f.urls.length,1);assert.equal(f.rates[0].key,'203.0.113.9');
 const get=await call(f,'/tasks/'+t.taskId);assert.equal(get.status,200);const getBody=await get.json();const {linkedProposalId,linkedInputVersion,linkedParentTaskId,...originalView}=r;assert.deepEqual(getBody,originalView);
 const retry=await preparedCall(f,'/tasks','POST',body(t));assert.equal(retry.status,200);assert.equal(f.urls.length,1);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
 assert.equal((await call(f,'/tasks/'+t.taskId,'GET',undefined,{origin:''})).status,403);
});
await test('identity, proposal, exact input version and parent cannot be silently changed',async()=>{
 const f=fixture(),t=await task(),bad=structuredClone(t);bad.title='Altered';assert.equal((await preparedCall(f,'/tasks','POST',body(bad))).status,400);
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),extra:true})).status,400);
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:'p_'+'b'.repeat(64)})).status,404);
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),parentTaskId:'b'.repeat(64)})).status,404);
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),inputVersion:'reviewed'})).status,422);
 f.setFetchFailure(true);assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,422);f.setFetchFailure(false);
 const parent=await task('Parent');await preparedCall(f,'/tasks','POST',body(parent));
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),parentTaskId:parent.taskId})).status,200);
 assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,409);
 const reviewed=await task('Reviewed','reviewed');assert.equal((await preparedCall(f,'/tasks','POST',{...body(reviewed),inputVersion:'reviewed'})).status,200);
});
await test('official source verification uses at most four workers and cancels the shared batch on mismatch',async()=>{
 const f=fixture();let active=0,maxActive=0,calls=0;const signals=[];
 const pages=Array.from({length:9},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:source.raw}));
 const handle=createLocalTaskHandler({now:()=>new Date(at),fetcher:async(url,options)=>{
  assert.match(url,/^https:\/\/jelliottdev\.github\.io\/data\/pages\/lp2-0[0-8]\.json$/);signals.push(options.signal);
  calls++;active++;maxActive=Math.max(maxActive,active);await new Promise(resolve=>setTimeout(resolve,1));active--;
  return Response.json({id:url.split('/').pop().slice(0,-5),raw:source.raw});
 }});
 const t=await task('Nine pages','raw',{pages});assert.equal((await handle(request('/tasks','POST',await approved(f,body(t))),f.env)).status,200);assert.equal(calls,9);assert.equal(maxActive,4);assert(signals.every(signal=>signal===signals[0]));
 const g=fixture();let signal;
 const bad=createLocalTaskHandler({fetcher:async(url,options)=>{signal=options.signal;return Response.json({id:'wrong',raw:source.raw});}});
 assert.equal((await bad(request('/tasks','POST',await approved(g,body(t))),g.env)).status,422);assert.equal(signal.aborted,true);assert.equal(g.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
await test('result replay binds all outputs; normalized valid result idempotent, latest result verified on GET',async()=>{
 const f=fixture(),t=await task();await preparedCall(f,'/tasks','POST',body(t));const path='/tasks/'+t.taskId+'/results',result=L.run(t);
 const wrong=structuredClone(result);wrong.transformed[0].text+='X';assert.equal((await call(f,path,'POST',{result:wrong})).status,422);
 assert.equal((await call(f,path,'POST',{result,extra:true})).status,422);
 const response=await call(f,path,'POST',{result}),r=await response.json();assert.equal(response.status,200);assert.equal(r.state,'results-verified');assert.deepEqual(r.latestRun.result,result);
 assert.deepEqual(await(await call(f,path,'POST',{result})).json(),r);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);
 const get=await(await call(f,'/tasks/'+t.taskId)).json();assert.equal(get.state,'results-verified');assert.deepEqual(get.latestRun,r.latestRun);
 const retry=await(await preparedCall(f,'/tasks','POST',body(t))).json();assert.equal(retry.state,'results-verified');assert.deepEqual(retry.latestRun,r.latestRun);
 f.db.sqlite.prepare('UPDATE local_task_results SET result_json=?').run(JSON.stringify(wrong));assert.equal((await call(f,'/tasks/'+t.taskId)).status,503);
});
await test('generic projections derive task-bound controls without changing stored task identities',async()=>{
 const f=fixture(),t=await task(),before=L.stable(t);
 const response=await preparedCall(f,'/tasks','POST',body(t)),view=await response.json();assert.equal(response.status,200);
 assert.equal(view.controls.targetId,t.taskId);await PlanControls.validate(view.controls,t);
 assert.equal(L.stable(t),before);assert.deepEqual(view.plan,t);
 assert.equal(f.db.sqlite.prepare('SELECT task_json FROM local_tasks WHERE id=?').get(t.taskId).task_json,before);
 const result=L.run(t),saved=await(await call(f,'/tasks/'+t.taskId+'/results','POST',{result})).json();
 assert.equal(saved.state,'results-verified');await PlanControls.validate(saved.controls,t);
 const reloaded=await(await call(f,'/tasks/'+t.taskId)).json();assert.deepEqual(reloaded.controls,view.controls);assert.deepEqual(reloaded.latestRun,saved.latestRun);
 // A visitor cannot provide a stale or invented control protocol alongside output.
 const changes=f.db.sqlite.prepare('SELECT total_changes() AS n').get().n;
 for(const controls of [view.controls,{...view.controls,targetId:'f'.repeat(64)}]){
  assert.equal((await call(f,'/tasks/'+t.taskId+'/results','POST',{result,controls})).status,422);
 }
 assert.equal(f.db.sqlite.prepare('SELECT total_changes() AS n').get().n,changes);
});
await test('failed, stale or tampered server-derived controls prevent writes and target replay',async()=>{
 const f=fixture(),t=await task();
 for(const failure of ['throw','stale','digest']){
  const broken=createLocalTaskHandler({now:()=>new Date(at),fetcher:()=>{throw Error('No source fetch after a failed control');},
   prepareControls:async target=>{if(failure==='throw')throw Error('Reference disagrees');const suite=await PlanControls.prepare(target);if(failure==='stale')suite.targetId='f'.repeat(64);else suite.cases[0].expectedResultSha256='0'.repeat(64);return suite;}});
  const before=f.db.sqlite.prepare('SELECT total_changes() AS n').get().n;
  assert.equal((await broken(request('/tasks','POST',body(t)),f.env)).status,422);
  assert.equal(f.db.sqlite.prepare('SELECT total_changes() AS n').get().n,before);
 }
 assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,200);
 const broken=createLocalTaskHandler({prepareControls:async()=>{throw Error('Reference disagrees');}}),originalVerify=L.verify;
 let targetReplays=0;
 try{
  L.verify=async(...args)=>{if(args[0].taskId===t.taskId)targetReplays++;return originalVerify(...args);};
  const before=f.db.sqlite.prepare('SELECT total_changes() AS n').get().n;
  assert.equal((await broken(request('/tasks/'+t.taskId+'/results','POST',{result:L.run(t)}),f.env)).status,422);
  assert.equal(f.db.sqlite.prepare('SELECT total_changes() AS n').get().n,before);assert.equal(targetReplays,0);
  assert.equal((await call(f,'/tasks/'+t.taskId+'/results','POST',{result:L.run(t)})).status,200);
  targetReplays=0;assert.equal((await broken(request('/tasks/'+t.taskId),f.env)).status,503);assert.equal(targetReplays,0);
 }finally{L.verify=originalVerify;}
});
await test('streamed body limits, rate limits and storage errors cannot write partial tasks',async()=>{
 const f=fixture(),t=await task(),reads=f.db.reads;
 const denied={...f.env,PROPOSAL_LIMIT:{limit:async()=>({success:false})}};
 assert.equal((await f.handle(request('/tasks','POST',body(t)),denied)).status,429);assert.equal(f.db.reads,reads);
 assert.equal((await preparedCall(f,'/tasks','POST',body(t),{'content-type':'text/plain'})).status,400);
 assert.equal((await preparedCall(f,'/tasks','POST',body(t),{'content-length':'2097153'})).status,400);
 const chunks=new ReadableStream({start(controller){controller.enqueue(new Uint8Array(2097153));controller.close();}});
 const oversized=new Request('https://worker.example/tasks',{method:'POST',headers:{origin,'content-type':'application/json'},body:chunks,duplex:'half'});
 assert.equal((await f.handle(oversized,f.env)).status,400);
 f.db.fail=true;assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,503);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
await test('injected atomic task cap50/day, concurrent retries, and next-day restoration',async()=>{
 const f=fixture(),tasks=await Promise.all(Array.from({length:60},(_,i)=>task('Task '+i)));
 const responses=await Promise.all(tasks.map(t=>preparedCall(f,'/tasks','POST',body(t))));assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,10);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,50);
 assert.equal((await preparedCall(f,'/tasks','POST',body(tasks[0]))).status,200);
 f.setDate('2026-10-25T00:00:00.000Z');assert.equal((await preparedCall(f,'/tasks','POST',body(tasks[59]))).status,200);
 const g=fixture(),t=await task();const dup=await Promise.all(Array.from({length:5},()=>preparedCall(g,'/tasks','POST',body(t))));assert(dup.every(r=>r.status===200));assert.equal(g.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
});
await test('injected atomic distinct result cap50/day retains duplicate retries without consuming quota',async()=>{
 const f=fixture(),tasks=[];
 for(let i=0;i<51;i++){if(i===50)f.setDate('2026-10-25T00:00:00.000Z');const t=await task('Result '+i);tasks.push(t);assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,200);}
 f.setDate('2026-10-26T00:00:00.000Z');
 const responses=await Promise.all(tasks.map(t=>call(f,'/tasks/'+t.taskId+'/results','POST',{result:L.run(t)})));
 assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,1);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,50);
 assert.equal((await call(f,'/tasks/'+tasks[0].taskId+'/results','POST',{result:L.run(tasks[0])})).status,200);
 f.setDate('2026-10-27T00:00:00.000Z');assert.equal((await call(f,'/tasks/'+tasks[50].taskId+'/results','POST',{result:L.run(tasks[50])})).status,200);
});
await test('production defaults bind the larger budgets in actual atomic task/link/result statements',async()=>{
 const f=fixture(),batches=[],originalBatch=f.db.batch;
 f.db.batch=async statements=>{batches.push(...statements);return originalBatch(statements);};
 const handle=createLocalTaskHandler({now:()=>new Date(at),fetcher:async()=>Response.json(source)}),t=await task('Production default quotas');
 assert.equal((await handle(request('/tasks','POST',await approved(f,body(t))),f.env)).status,200);
 assert.equal((await handle(request('/tasks/'+t.taskId+'/results','POST',{result:L.run(t)}),f.env)).status,200);
 const tasks=batches.find(s=>s.sql.includes('INSERT INTO local_tasks ')),links=batches.find(s=>s.sql.includes('INSERT INTO local_task_ideas ')),results=batches.find(s=>s.sql.includes('INSERT INTO local_task_results '));
 assert.deepEqual(tasks.args.slice(-4),[at.slice(0,10),STORAGE_LIMITS.tasks,at.slice(0,10),STORAGE_LIMITS.taskIdeaLinks]);
 assert.equal(links.args.at(-1),STORAGE_LIMITS.taskIdeaLinks);assert.equal(results.args.at(-1),STORAGE_LIMITS.results);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);
});
await test('migration backfills original task provenance without changing it',async()=>{
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,proposalId.slice(2),C.serialize(card),'unused',at);
 const id='1'.repeat(64);sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(id,'hash','create',proposalId,C.serialize(card),'{}','raw',null,at,at.slice(0,10));
 const before=sqlite.prepare('SELECT * FROM local_tasks').get();sqlite.exec(readFileSync(new URL('./migrations/0006_task_ideas.sql',import.meta.url),'utf8'));
 assert.deepEqual(sqlite.prepare('SELECT * FROM local_tasks').get(),before);
 const link=sqlite.prepare('SELECT * FROM local_task_ideas').get();assert.equal(link.task_id,id);assert.equal(link.proposal_id,proposalId);assert.equal(link.input_version,'raw');assert.equal(link.parent_task_id,null);assert.equal(link.created_at,at);
 sqlite.close();
});
function addIdea(f,label,value=card,isPublic=false){
 if(value===card){value=structuredClone(card);value.outcome=H.cardData(C.confirm(C.createDraft({source:{text:'fixture'},aim:C.field('specified',{outcomeId:'measure',wording:'Measure',detail:label},{kind:'supplied',refs:['fixture']})}),{id:'fixture',at})).outcome;}
 const id='p_'+createHash('sha256').update(C.serialize(value)).digest('hex');
 f.db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,id.slice(2),C.serialize(value),'unused',at);if(isPublic)f.db.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(id,at,at.slice(0,10));return id;
}
await test('different real goal cards reuse the same computation and saved result without exposing private original context',async()=>{
 const f=fixture({publicOriginal:false}),field=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
 const cards=['decipher','measure'].map(outcomeId=>H.cardData(C.confirm(C.createDraft({source:{text:'DO NOT PROJECT ORIGINAL'},aim:field({outcomeId,wording:C.OUTCOMES[outcomeId],detail:''}),method:field({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'}]}),scope:field({pages:['lp2-15']}),rules:{evaluation:field('measurement')}}),{id:outcomeId,at})));
 f.db.sqlite.prepare('DELETE FROM proposals WHERE id=?').run(proposalId);proposalId=addIdea(f,'original',cards[0]);
 const plans=await Promise.all(cards.map(value=>{const plan=planCard(value);assert(!plan.reason);return task('Local test: rune reversal','raw',{steps:plan.steps,criterion:plan.criterion})}));
 assert.notDeepEqual(cards[0],cards[1]);assert.equal(plans[0].taskId,plans[1].taskId);
 const t=plans[0];assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,200);const original=f.db.sqlite.prepare('SELECT * FROM local_tasks WHERE id=?').get(t.taskId);
 assert.equal((await call(f,'/tasks/'+t.taskId)).status,404);assert.equal((await call(f,'/tasks/'+t.taskId+'/results','POST',{result:L.run(t)})).status,404);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 const second=addIdea(f,'second',cards[1],true);
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second})).status,200);
 const run=await(await call(f,'/tasks/'+t.taskId+'/results','POST',{result:L.run(t)})).json();
 const response=await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second}),shared=await response.json();assert.equal(response.status,200);assert.equal(shared.linkedProposalId,second);assert.equal(shared.linkedInputVersion,'raw');assert.equal(shared.linkedParentTaskId,null);assert.equal(shared.proposalId,second);assert.deepEqual(shared.card,cards[1]);assert.equal(shared.state,'results-verified');assert.deepEqual(shared.latestRun,run.latestRun);assert.deepEqual(shared.relatedIdeaIds,[second]);assert(!JSON.stringify(shared).includes('DO NOT PROJECT ORIGINAL'));assert(!JSON.stringify(shared).includes(proposalId));
 assert.equal(f.urls.length,1,'Identical raw task reuses already verified exact source bytes');assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas').get().n,2);
 assert.deepEqual(f.db.sqlite.prepare('SELECT * FROM local_tasks WHERE id=?').get(t.taskId),original);
 const link=f.db.sqlite.prepare('SELECT * FROM local_task_ideas WHERE proposal_id=?').get(second);f.setDate('2026-10-25T00:00:00Z');const retry=await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second});assert.equal(retry.status,200);assert.deepEqual(f.db.sqlite.prepare('SELECT * FROM local_task_ideas WHERE proposal_id=?').get(second),link);
 const get=await(await call(f,'/tasks/'+t.taskId)).json();assert.deepEqual(get.relatedIdeaIds,[second]);assert(!Object.hasOwn(get,'linkedProposalId'));assert.equal(get.proposalId,second);assert.deepEqual(get.card,cards[1]);assert(!JSON.stringify(get).includes(proposalId));
});
await test('public task projection uses public association version/parent/date and never private original parent',async()=>{
 const f=fixture({publicOriginal:false}),parent=await task('Private parent computation');assert.equal((await preparedCall(f,'/tasks','POST',body(parent))).status,200);
 const t=await task('Shared computation');assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),parentTaskId:parent.taskId})).status,200);
 const before=f.db.sqlite.prepare('SELECT * FROM local_tasks WHERE id=?').get(t.taskId);
 const publicCard=H.cardData(C.confirm(C.createDraft({source:{text:'Public normalized fixture'},aim:C.field('specified','Measure repeat counts',{kind:'supplied',refs:['fixture']}),method:C.field('specified',{operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'}]},{kind:'supplied',refs:['fixture']})}),{id:'public',at}));
 const second=addIdea(f,'second',publicCard,true);f.setDate('2026-10-25T01:00:00.000Z');
 const previous=source.reviewed_text;try{source.reviewed_text=source.raw;const response=await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second,inputVersion:'reviewed'});assert.equal(response.status,200);const created=await response.json();assert.equal(created.proposalId,second);assert.equal(created.inputVersion,'reviewed');assert.equal(created.parentTaskId,null);}finally{source.reviewed_text=previous;}
 const response=await call(f,'/tasks/'+t.taskId);assert.equal(response.status,200);const visible=await response.json();
 assert.equal(visible.proposalId,second);assert.deepEqual(visible.card,publicCard);assert.equal(visible.inputVersion,'reviewed');assert.equal(visible.parentTaskId,null);assert.equal(visible.createdAt,'2026-10-25T01:00:00.000Z');assert.deepEqual(visible.plan,t);
 assert(!JSON.stringify(visible).includes(proposalId));assert(!JSON.stringify(visible).includes(parent.taskId));assert.equal((await call(f,'/tasks/'+parent.taskId)).status,404);
 assert.deepEqual(f.db.sqlite.prepare('SELECT * FROM local_tasks WHERE id=?').get(t.taskId),before,'Public context cannot rewrite immutable original provenance');
 const result=await call(f,'/tasks/'+t.taskId+'/results','POST',{result:L.run(t)});assert.equal(result.status,200);assert(!JSON.stringify(await result.json()).includes(proposalId));
});
await test('public context prefers canonical only when public, otherwise earliest public association',async()=>{
 const f=fixture({publicOriginal:false}),t=await task();await preparedCall(f,'/tasks','POST',body(t));
 const first=addIdea(f,'first',card,true),second=addIdea(f,'second',card,true);
 f.setDate('2026-10-25T01:00:00.000Z');await preparedCall(f,'/tasks','POST',{...body(t),proposalId:first});
 f.setDate('2026-10-26T01:00:00.000Z');await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second});
 assert.equal((await(await call(f,'/tasks/'+t.taskId)).json()).proposalId,first);
 f.db.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(proposalId,at,at.slice(0,10));
 assert.equal((await(await call(f,'/tasks/'+t.taskId)).json()).proposalId,proposalId);
 const privateThird=addIdea(f,'private-third');const echo=await(await preparedCall(f,'/tasks','POST',{...body(t),proposalId:privateThird})).json();assert.equal(echo.proposalId,privateThird);assert.equal(echo.linkedProposalId,privateThird);assert(!echo.relatedIdeaIds.includes(privateThird),'A requested private association can be echoed without publishing it');
});
await test('shared links still validate proposals, parents and changed source versions before writing',async()=>{
 const f=fixture(),t=await task();await preparedCall(f,'/tasks','POST',body(t));
 let second='p_'+'b'.repeat(64);assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second})).status,404);second=addIdea(f,'second');
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second,parentTaskId:'f'.repeat(64)})).status,404);
 const before=f.urls.length;assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second,inputVersion:'reviewed'})).status,422);assert.equal(f.urls.length,before+1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas').get().n,1);
 const old=source.reviewed_text;try{source.reviewed_text=source.raw;assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second,inputVersion:'reviewed'})).status,200);}finally{source.reviewed_text=old;}
 assert.equal(f.urls.length,before+2,'Different input version gets an independent official-source check');const versionLink=await(await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second,inputVersion:'reviewed'})).json();assert.equal(versionLink.linkedInputVersion,'reviewed');assert.equal(versionLink.inputVersion,'reviewed');assert.equal(f.db.sqlite.prepare('SELECT input_version FROM local_tasks').get().input_version,'raw');
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:second})).status,409,'An existing idea association cannot silently change its input version');
 const parent=await task('Existing parent');await preparedCall(f,'/tasks','POST',body(parent));const third=addIdea(f,'third');await preparedCall(f,'/tasks','POST',{...body(parent),proposalId:third});
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:third,parentTaskId:parent.taskId})).status,200);assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:third,parentTaskId:null})).status,409);
 const fourth=addIdea(f,'fourth');f.db.fail=true;assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:fourth})).status,503);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas WHERE proposal_id=?').get(fourth).n,0);
 f.db.fail=false;f.db.sqlite.prepare('UPDATE local_tasks SET task_hash=? WHERE id=?').run('0'.repeat(64),t.taskId);assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:fourth})).status,503,'Stored full-task integrity remains required even for reuse');
});
await test('atomic association cap, duplicate retries, rollback and bounded public-only related IDs',async()=>{
 const f=fixture({publicOriginal:false}),t=await task();await preparedCall(f,'/tasks','POST',body(t));f.setDate('2026-10-25T00:00:00Z');
 const ids=Array.from({length:60},(_,i)=>addIdea(f,'association '+i,card,true));
 const responses=await Promise.all(ids.map(id=>preparedCall(f,'/tasks','POST',{...body(t),proposalId:id})));assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,10);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas WHERE created_day=?').get('2026-10-25').n,50);
 const linked=f.db.sqlite.prepare('SELECT proposal_id FROM local_task_ideas WHERE created_day=? LIMIT 1').get('2026-10-25').proposal_id;
 assert.equal((await preparedCall(f,'/tasks','POST',{...body(t),proposalId:linked})).status,200);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas WHERE created_day=?').get('2026-10-25').n,50);
 const blocked=await task('No orphan at link cap');assert.equal((await preparedCall(f,'/tasks','POST',body(blocked))).status,429);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks WHERE id=?').get(blocked.taskId).n,0);
 f.setDate('2026-10-26T00:00:00Z');const last=ids.find(id=>!f.db.sqlite.prepare('SELECT 1 FROM local_task_ideas WHERE proposal_id=?').get(id));const duplicate=await Promise.all(Array.from({length:4},()=>preparedCall(f,'/tasks','POST',{...body(t),proposalId:last})));assert(duplicate.every(r=>r.status===200));assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas WHERE proposal_id=?').get(last).n,1);
 const view=await(await call(f,'/tasks/'+t.taskId)).json();assert.equal(view.relatedIdeaIds.length,50);assert.equal(view.relatedIdeasTruncated,true);assert(!view.relatedIdeaIds.includes(proposalId),'Private original association is not listed as a public related idea');assert(view.relatedIdeaIds.every(id=>ids.includes(id)));
});
await test('official-source redirect is rejected without task or result persistence',async()=>{
 const f=fixture(),t=await task();let calls=0;
 const handle=createLocalTaskHandler({fetcher:async(url,options)=>{calls++;assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'manual');return new Response(null,{status:302,headers:{location:'https://untrusted.example/page.json'}});}});
 const response=await handle(request('/tasks','POST',await approved(f,body(t))),f.env);assert.equal(response.status,422);assert.equal(calls,1,'No redirect destination is fetched');assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 assert.equal((await handle(request('/tasks/'+t.taskId+'/results','POST',{result:L.run(t)}),f.env)).status,404);
});
await test('large-scope source verification uses one aggregate and preserves exact raw/reviewed snapshots',async()=>{
 const officialAlphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
 const ids=[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))];
 const selected=Array.from({length:55},(_,i)=>'lp2-'+String(i).padStart(2,'0'));
 const bundle={schema:'liberpedia-local-inputs-v1',alphabet:officialAlphabet,pages:ids.map((id,i)=>({id,raw:'ᚠᚢ-ᚦ  \r\n'+i,reviewed_text:id==='lp1-00'?null:id==='lp2-00'?'':'ᚢᚠ-ᚦ\r\n '+i}))};
 const buildTask=async(version,b=bundle)=>L.prepare({title:'Synthetic55-page '+version+' task',alphabet:officialAlphabet,steps:[{op:'reverse',unit:'line'}],criterion:{kind:'measurement'},pages:selected.map(id=>({id,text:b.pages.find(p=>p.id===id)[version==='raw'?'raw':'reviewed_text']}))});
 for(const version of ['raw','reviewed']){
  const f=fixture(),t=await buildTask(version);let calls=0;
  const handle=createLocalTaskHandler({fetcher:async(url,options)=>{calls++;assert.equal(url,origin+'/data/local-run-inputs.json');assert.equal(options.redirect,'manual');assert(options.signal);return Response.json(bundle);}});
  const response=await handle(request('/tasks','POST',await approved(f,{...body(t),inputVersion:version})),f.env),value=await response.json();assert.equal(response.status,200);assert.deepEqual(value.plan,t);assert.equal(value.inputVersion,version);assert.equal(calls,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
  assert.equal((await handle(request('/tasks','POST',await approved(f,{...body(t),inputVersion:version})),f.env)).status,200);assert.equal(calls,1,'Exact stored retry does not refetch75 inputs');
 }
 for(const failure of ['changed-text','changed-alphabet','null-reviewed','missing-reviewed','duplicate-page','redirect','oversize']){
  const f=fixture(),version='reviewed',t=await buildTask(version),altered=structuredClone(bundle);let calls=0;
  if(failure==='changed-text')altered.pages.find(p=>p.id==='lp2-00').reviewed_text='ᚠ';
  if(failure==='changed-alphabet')altered.alphabet[0].prime=997;
  if(failure==='null-reviewed')altered.pages.find(p=>p.id==='lp2-00').reviewed_text=null;
  if(failure==='missing-reviewed')delete altered.pages.find(p=>p.id==='lp2-00').reviewed_text;
  if(failure==='duplicate-page')altered.pages[1]=altered.pages[0];
  const handle=createLocalTaskHandler({fetcher:async url=>{calls++;assert.equal(url,origin+'/data/local-run-inputs.json');return failure==='redirect'?new Response(null,{status:302,headers:{location:'https://evil.example/source'}}):failure==='oversize'?new Response('{}',{headers:{'content-type':'application/json','content-length':'2097153'}}):Response.json(altered);}});
  const response=await handle(request('/tasks','POST',await approved(f,{...body(t),inputVersion:version})),f.env);assert.equal(response.status,422,failure);assert.equal(calls,1,'Invalid bundle cannot trigger individual-page fallback');assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 }
});
await test('submission verifies once and checks exact committed bytes without a second replay',async()=>{
 const f=fixture(),t=await task();assert.equal((await preparedCall(f,'/tasks','POST',body(t))).status,200);
 const result=L.run(t),original=L.verify;let replays=0;
 try{
  L.verify=async(...args)=>{if(args[0].taskId===t.taskId)replays++;return original(...args);};
  const first=await call(f,'/tasks/'+t.taskId+'/results','POST',{result});assert.equal(first.status,200);assert.equal(replays,1);
  const saved=await first.json();assert.deepEqual(saved.latestRun.result,result);
  const retry=await call(f,'/tasks/'+t.taskId+'/results','POST',{result});assert.equal(retry.status,200);assert.equal(replays,2,'Every submitted result is still independently replayed');
  f.db.sqlite.prepare('UPDATE local_task_results SET result_json=? WHERE id=?').run(JSON.stringify({...result,metrics:{...result.metrics,runes:999}}),saved.latestRun.id);
  const corrupt=await call(f,'/tasks/'+t.taskId+'/results','POST',{result});assert.equal(corrupt.status,503);assert.equal(replays,3,'A corrupt stored receipt cannot bypass fresh admission or be projected as verified');
 }finally{L.verify=original;}
});
console.log('PASS '+count+' SQLite-backed local-task groups; all official-source fetches injected, no execution of external code.');
