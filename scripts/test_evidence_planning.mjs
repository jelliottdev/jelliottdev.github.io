/* Full local SQLite loop: original cards, official inputs, reused witnesses, remainder admission. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import L from '../local-experiment.js';
import C from '../claim-specification.js';
import H from '../claim-share.js';
import {createPrepareTaskHandler} from '../services/idea-assistant/prepare-task.mjs';
import {createLocalTaskHandler} from '../services/idea-assistant/local-tasks.mjs';
import {createCommunityIdeaHandler} from '../services/idea-assistant/community-ideas.mjs';
import {createCommunityFeedHandler} from '../services/idea-assistant/community-feed.mjs';
import {issue} from '../services/idea-assistant/prepared-plans.mjs';
import Controls from '../local-plan-controls.js';
import Family from '../research-family.js';
const origin='https://jelliottdev.github.io',at='2026-10-25T12:00:00.000Z',sha=v=>createHash('sha256').update(L.stable(v)).digest('hex');
const alphabet=JSON.parse(readFileSync(new URL('../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']}),criterion={kind:'exact-prefix',values:[28,28]};
function fixture(){
 const sqlite=new DatabaseSync(':memory:'),directory=new URL('../services/idea-assistant/migrations/',import.meta.url);
 for(const name of readdirSync(directory).filter(n=>n.endsWith('.sql')).sort())sqlite.exec(readFileSync(new URL(name,directory),'utf8'));
 const db={prepare(sql){return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args),sql,args};}};},async batch(items){sqlite.exec('BEGIN');try{const out=items.map(item=>sqlite.prepare(item.sql).run(...item.args));sqlite.exec('COMMIT');return out;}catch(error){sqlite.exec('ROLLBACK');throw error;}}};
 const raw=new Map(['lp2-01','lp2-02','lp2-03'].map((id,i)=>[id,alphabet.slice(i,i+4).map(a=>a.rune).join('')+' '+alphabet[i].rune]));
 const fetcher=async url=>{const id=/\/data\/pages\/(lp2-\d{2})\.json$/.exec(url)?.[1];assert(raw.has(id));return Response.json({id,raw:raw.get(id),reviewed_text:null});};
 const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async()=>({success:true})},AI:{run(){throw Error('No model during exact reuse');}}};
 return {sqlite,db,raw,env,prepare:createPrepareTaskHandler({fetcher,now:()=>new Date(at)}),tasks:createLocalTaskHandler({fetcher,now:()=>new Date(at)}),ideas:createCommunityIdeaHandler({now:()=>new Date(at)}),feed:createCommunityFeedHandler()};
}
function idea(f,pages,aim='Solve LP2',evaluation=criterion,publish=true,operations=[{id:'reverse_runes',label:'Reverse rune order within each word',unit:'word'}]){
 const card=H.cardData(C.confirm(C.createDraft({source:{text:'Original wording stays outside the computation identity'},aim:known(aim),method:known({operations}),scope:known({pages}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known(evaluation)}}),{id:'fixture',at})),hash=sha(card),id='p_'+hash;
 f.sqlite.prepare('INSERT OR IGNORE INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,hash,L.stable(card),'fixture',at);
 if(publish)f.sqlite.prepare('INSERT OR IGNORE INTO research_ideas VALUES(?,?,?)').run(id,at,at.slice(0,10));return {id,card};
}
async function seed(f,owner,pages,title){
 const task=await L.prepare({title,pages:pages.map(id=>({id,text:f.raw.get(id)})),alphabet,steps:[{op:'reverse',unit:'word'}],criterion});
 const result=await L.verify(task,L.run(task)),id=sha(result);
 f.sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(task.taskId,sha(task),'0'.repeat(64),owner.id,L.stable(owner.card),L.stable(task),'raw',null,at,at.slice(0,10));
 f.sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(task.taskId,owner.id,'raw',null,at,at.slice(0,10));
 f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run(id,task.taskId,L.stable(result),at,at.slice(0,10));return {task,result,id};
}
async function call(f,handler,path,body,status=200){const response=await f[handler](new Request('https://worker.example'+path,{method:body===undefined?'GET':'POST',headers:{origin,'content-type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})}),f.env);const value=await response.json();assert.equal(response.status,status,JSON.stringify(value));return value;}
const prepare=(f,owner)=>call(f,'prepare','/prepare-task',{proposalId:owner.id,parentTaskId:null});
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}

await test('different intents and older titles reuse exact saved computations without tasks or new results',async()=>{
 const f=fixture(),old=idea(f,['lp2-01'],'Measure rune frequencies'),source=await seed(f,old,['lp2-01'],'Earlier descriptive title'),incoming=idea(f,['lp2-01'],'Solve Liber Primus');
 assert.notEqual(old.id,incoming.id);assert.equal(source.result.matches[0].matched,false);
 const plan=await prepare(f,incoming);assert.equal(plan.state,'scope-covered');assert.deepEqual(plan.coverage.coveredPages,['lp2-01']);assert.equal(plan.coverage.exactTaskId,source.task.taskId);assert.equal(plan.task,undefined);assert.equal(plan.preparation,undefined);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);
 const restored=await call(f,'ideas','/ideas/'+incoming.id);assert.equal(restored.tasks.length,0);assert.deepEqual(restored.card,incoming.card);assert.deepEqual(restored.coverage.coveredPages,['lp2-01']);
 const feed=await call(f,'feed','/community-research');assert.equal(feed.entries.find(e=>e.id===incoming.id).hasSharedComputation,true);
});
await test('union coverage skips only saved pages, admits the exact remainder and updates after its accepted result',async()=>{
 const f=fixture(),one=idea(f,['lp2-01'],'Measure rune frequencies'),two=idea(f,['lp2-02'],'Reproduce the transformation'),incoming=idea(f,['lp2-01','lp2-02','lp2-03']);
 await seed(f,one,['lp2-01'],'Old first page');await seed(f,two,['lp2-02'],'A separate page batch');const value=await prepare(f,incoming);
 assert.equal(value.state,'plan-ready');assert.deepEqual(value.coverage.coveredPages,['lp2-01','lp2-02']);assert.deepEqual(value.task.pages.map(p=>p.id),['lp2-03']);assert.equal(value.coverage.requestedTask.pages.length,3);
 const body={proposalId:incoming.id,task:value.task,inputVersion:value.inputVersion,parentTaskId:null,preparationId:value.preparation.id};
 const changed=await L.prepare({...value.task,steps:[{op:'affine',a:1,b:1}]});await call(f,'tasks','/tasks',{...body,task:changed},409);
 const created=await call(f,'tasks','/tasks',body);assert.equal(created.id,value.task.taskId);assert.deepEqual(created.card,incoming.card);
 await call(f,'tasks','/tasks/'+created.id+'/results',{result:L.run(value.task)});
 const second=await prepare(f,incoming);assert.equal(second.state,'scope-covered');assert.deepEqual(second.coverage.remainingPages,[]);assert.equal(second.coverage.evidence.length,3);assert.equal(second.coverage.exactTaskId,null);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,3);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,3);
 const reload=await call(f,'ideas','/ideas/'+incoming.id);assert.equal(reload.coverage.coveredPages.length,3);assert.equal(reload.tasks.length,1,'shared source tasks are not copied into the idea');
});
await test('an existing pending task discovers later shared work without copying its result',async()=>{
 const f=fixture(),incoming=idea(f,['lp2-01','lp2-02']);
 const prepared=await prepare(f,incoming);
 const created=await call(f,'tasks','/tasks',{proposalId:incoming.id,task:prepared.task,inputVersion:prepared.inputVersion,parentTaskId:null,preparationId:prepared.preparation.id});
 const old=idea(f,['lp2-01'],'Measure rune frequencies');await seed(f,old,['lp2-01'],'Later accepted computation');
 const partial=await call(f,'tasks','/tasks/'+created.id);
 assert.equal(partial.state,'not-run');assert.equal(partial.latestRun,undefined);assert.deepEqual(partial.coverage.coveredPages,['lp2-01']);assert.deepEqual(partial.coverage.remainingPages,['lp2-02']);
 const second=idea(f,['lp2-02'],'Reproduce the transformation');await seed(f,second,['lp2-02'],'Second accepted computation');
 const full=await call(f,'tasks','/tasks/'+created.id);assert.deepEqual(full.coverage.remainingPages,[]);assert.equal(full.state,'not-run');assert.equal(full.latestRun,undefined);
 f.sqlite.exec('DROP INDEX local_tasks_protocol_lookup; ALTER TABLE local_task_results RENAME TO unavailable_results; CREATE TABLE local_task_results(id TEXT,task_id TEXT,result_json TEXT,created_at TEXT,created_day TEXT);');
 // Fail only the shared lookup while keeping the requested plan and its empty own result lookup valid.
 const originalPrepare=f.db.prepare.bind(f.db);f.db.prepare=sql=>{if(sql.includes('json_extract(t.task_json'))throw Error('Lookup unavailable');return originalPrepare(sql);};
 const unavailable=await call(f,'tasks','/tasks/'+created.id);assert.equal(unavailable.coverageUnavailable,true);assert.equal(unavailable.plan.taskId,created.id);assert.equal(unavailable.state,'not-run');assert.equal(unavailable.coverage,undefined);
});
await test('a forged evidence basis cannot remove an untested page or change its computation',async()=>{
 const f=fixture(),old=idea(f,['lp2-01'],'Measure rune frequencies'),incoming=idea(f,['lp2-01','lp2-02']);await seed(f,old,['lp2-01'],'Saved');const value=await prepare(f,incoming);
 const row=f.sqlite.prepare('SELECT basis_json FROM prepared_plans WHERE id=?').get(value.preparation.id),basis=JSON.parse(row.basis_json);assert.equal(basis.kind,'evidence-remainder');
 const originalTask=value.task,controls=await Controls.prepare(originalTask);
 const args={db:f.db,proposalId:incoming.id,card:incoming.card,task:originalTask,inputVersion:'raw',parentTaskId:null,controls,authority:'idea',createdAt:at};
 const bad=structuredClone(basis);bad.evidence[0].pages=['lp2-02'];await assert.rejects(issue({...args,basis:bad}));
 const changed=await L.prepare({...originalTask,steps:[{op:'affine',a:1,b:1}]});await assert.rejects(issue({...args,task:changed,controls:await Controls.prepare(changed),basis}));
});
await test('family evidence authorizes only the missing idea pages and keeps original receipts',async()=>{
 const f=fixture(),bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8'));for(const page of bundle.pages)if(f.raw.has(page.id))page.raw=f.raw.get(page.id);
 const warning={kind:'exact-prefix',values:[24,7,24,4,9,21,17,18,20,10,18,1]},operation={id:'vigenere',label:'Vigenere',key:[23,18,3,4],direction:'subtract',reset:'page'},incoming=idea(f,['lp2-01','lp2-02'],'Solve LP2',warning,true,[operation]);
 const family=await Family.prepare(bundle,['repeat--subtract--page--lp2-01']),item=family.cases[0],result=L.run(item.task);
 f.sqlite.prepare('INSERT INTO family_case_results VALUES(?,?,?,?,?,?,?,?,?,?)').run(family.familyId,family.revision,item.id,item.task.taskId,L.stable(item.task),sha(result),L.stable(result),Number(result.matches[0].matched),at,at.slice(0,10));
 const plan=await prepare(f,incoming);assert.equal(plan.state,'plan-ready');assert.deepEqual(plan.task.pages.map(p=>p.id),['lp2-02']);assert.equal(plan.coverage.familySources[0].caseId,item.id);assert.deepEqual(plan.coverage.coveredPages,['lp2-01']);
 const created=await call(f,'tasks','/tasks',{proposalId:incoming.id,task:plan.task,inputVersion:plan.inputVersion,parentTaskId:null,preparationId:plan.preparation.id});
 await call(f,'tasks','/tasks/'+created.id+'/results',{result:L.run(plan.task)});
 const all=await prepare(f,incoming);assert.equal(all.state,'scope-covered');assert.deepEqual(all.coverage.remainingPages,[]);assert.equal(all.coverage.evidence.length,2);assert.equal(all.coverage.familySources.length,1);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM family_case_results').get().n,1);
 const reload=await call(f,'ideas','/ideas/'+incoming.id);assert.deepEqual(reload.coverage.familySources,all.coverage.familySources);assert.equal(reload.tasks.length,1);
});
await test('different bytes or success criteria retain genuinely new work; private sources never count',async()=>{
 const f=fixture(),old=idea(f,['lp2-01'],'Measure rune frequencies'),incoming=idea(f,['lp2-01']);await seed(f,old,['lp2-01'],'Original bytes');f.raw.set('lp2-01',f.raw.get('lp2-01')+alphabet[10].rune);
 const changed=await prepare(f,incoming);assert.equal(changed.state,'plan-ready');assert.equal(changed.coverage,undefined);assert.equal(changed.task.pages[0].text,f.raw.get('lp2-01'));
 const alternate=idea(f,['lp2-01'],'Solve LP2',{kind:'exact-prefix',values:[0,1]});assert.equal((await prepare(f,alternate)).coverage,undefined);
 const privateFixture=fixture(),hidden=idea(privateFixture,['lp2-01'],'Measure rune frequencies',criterion,false);await seed(privateFixture,hidden,['lp2-01'],'Hidden fixture');const publicIdea=idea(privateFixture,['lp2-01']);assert.equal((await prepare(privateFixture,publicIdea)).coverage,undefined);
});
console.log('Cross-idea planning: '+groups+' end-to-end SQLite groups passed; no hosted writes.');
