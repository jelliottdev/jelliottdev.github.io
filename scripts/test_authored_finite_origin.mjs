/* SQLite admission/projection tests with synthetic manuscript inputs. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import E from '../local-experiment.js';
import Compiler from '../factored-finite-search-compiler.js';
import Q from '../factored-finite-question.js';
import Controls from '../local-plan-controls.js';
import {issue,authorize} from '../services/idea-assistant/prepared-plans.mjs';
import {createLocalTaskHandler} from '../services/idea-assistant/local-tasks.mjs';
import {loadFiniteRecordPlan} from '../services/idea-assistant/finite-record-plans.mjs';
import {createAuthoredFiniteSourceLoader,checkedAuthoredFiniteMember,finiteSnapshotMember} from '../services/idea-assistant/authored-finite-origin.mjs';
const hash=v=>createHash('sha256').update(typeof v==='string'?v:E.stable(v)).digest('hex'),origin='https://jelliottdev.github.io',at='2026-10-25T12:00:00.000Z';
const recipe=JSON.parse(execFileSync('python',['-c',"import sys,json;sys.path.insert(0,'scripts');from test_authored_finite_followups import fixture;print(json.dumps(fixture(),ensure_ascii=True))"],{encoding:'utf8',maxBuffer:2*1024*1024})),bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8'));
for(const page of bundle.pages)page.raw=bundle.alphabet.slice(0,8).map(v=>v.rune).join('').repeat(8);
for(const pin of recipe.inputs.pages)pin.text_sha256=hash(bundle.pages.find(p=>p.id===pin.id).raw);
const record={id:'synthetic-finite-origin',status:'published',browser_followups:[recipe]},ref={recordId:record.id,followupId:recipe.id};let requests=0;
const fetcher=async url=>{requests++;return Response.json(url.endsWith('/record.json')?record:bundle);},source=await loadFiniteRecordPlan(ref,{fetcher}),compiled=await Compiler.compileLanguageComparison(recipe.card,bundle),selected=(await Q.select(compiled.domain,(await Q.cases(compiled.domain,{cursor:0,limit:1})).cases)).cases[0],member=compiled.members.find(m=>m.programId===selected.programId),basis={kind:'authored-finite-member-v1',origin:source.origin,domainId:compiled.domain.id,memberBasis:{kind:'factored-output-settings',settings:member.settings,caseId:selected.id}},task=selected.task,controls=await Controls.prepare(task),proposalId='p_'+hash(recipe.card);
const sqlite=new DatabaseSync(':memory:'),dir=new URL('../services/idea-assistant/migrations/',import.meta.url);for(const name of readdirSync(dir).filter(n=>/^\d{4}_.*\.sql$/.test(n)).sort())sqlite.exec(readFileSync(new URL(name,dir),'utf8'));
const db={prepare(sql){return {bind(...args){return {sql,args,first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};},async batch(items){sqlite.exec('BEGIN');try{const out=items.map(({sql,args})=>({success:true,meta:{changes:Number(sqlite.prepare(sql).run(...args).changes)}}));sqlite.exec('COMMIT');return out;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};
sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,proposalId.slice(2),E.stable(recipe.card),'unused',at);sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(proposalId,at,at.slice(0,10));
const binding={db,proposalId,card:recipe.card,task,inputVersion:'raw',parentTaskId:null,controls},env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async()=>({success:true})}},handler=createLocalTaskHandler({fetcher,now:()=>new Date(at)}),call=async(path,body)=>{const response=await handler(new Request('https://worker.example'+path,{method:body?'POST':'GET',headers:{origin,'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{})}),env);return {status:response.status,value:await response.json()};};
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
try{
await test('source-bound member issue and authorization preserve full origin and selected witness',async()=>{
 const loader=createAuthoredFiniteSourceLoader(fetcher),before=requests;const receipt=await issue({...binding,authority:'idea',basis,createdAt:at,loadAuthoredSource:loader}),authorized=await authorize({...binding,preparationId:receipt.id,loadAuthoredSource:loader});assert(authorized);assert.equal(requests-before,2,'One per-request source+bundle load');assert.deepEqual(authorized.reviewed.origin,source.origin);assert.deepEqual(authorized.reviewed.snapshot,recipe);assert.deepEqual(authorized.reviewed.control,recipe.control.members.find(m=>E.stable(m.settings)===E.stable(member.settings)).control);assert.deepEqual(authorized.reviewed.scopeRelation.card,recipe.card);binding.preparationId=receipt.id;
});
await test('wrong source domain card settings pages and output criterion cannot be admitted',async()=>{
 for(const change of [v=>v.basis.domainId='0'.repeat(64),v=>v.basis.origin.recordSha256='0'.repeat(64),v=>v.basis.memberBasis.settings.reverse(),v=>v.task.pages[0].text+='ᚠ',v=>v.task.criterion={kind:'measurement'}]){const value=structuredClone({basis,card:recipe.card,task,inputVersion:'raw'});change(value);await assert.rejects(()=>checkedAuthoredFiniteMember({...value,fetcher}));}
 const wrong=structuredClone(basis);wrong.memberBasis.caseId='0'.repeat(64);await assert.rejects(()=>issue({...binding,authority:'idea',basis:wrong,createdAt:at,fetcher}));
});
await test('page-group admission retains the same family and exact selected case identities',async()=>{
 const cases=(await Q.cases(compiled.domain,{cursor:0,limit:2})).cases,group=await E.prepare({...task,pages:compiled.domain.pages.filter(p=>cases.some(c=>c.pageId===p.id))}),groupControls=await Controls.prepare(group),groupBasis={...basis,memberBasis:{kind:'factored-page-group-v1',domainId:compiled.domain.id,settings:member.settings,caseIds:cases.map(c=>c.id)}},bound={...binding,task:group,controls:groupControls,fetcher},receipt=await issue({...bound,authority:'idea',basis:groupBasis,createdAt:at});assert(await authorize({...bound,preparationId:receipt.id}));const wrong=structuredClone(groupBasis);wrong.memberBasis.domainId='0'.repeat(64);await assert.rejects(()=>issue({...bound,authority:'idea',basis:wrong,createdAt:at}));wrong.memberBasis.domainId=compiled.domain.id;wrong.memberBasis.caseIds[0]='0'.repeat(64);await assert.rejects(()=>issue({...bound,authority:'idea',basis:wrong,createdAt:at}));
});
await test('create persists finite snapshot and relation; linked retry rechecks changed published source',async()=>{
 const body={proposalId,task,inputVersion:'raw',parentTaskId:null,preparationId:binding.preparationId},created=await call('/tasks',body);assert.equal(created.status,200,JSON.stringify(created.value));assert.equal(created.value.origins.length,1);const meta=created.value.origins[0];assert.deepEqual(meta.origin,source.origin);assert.equal(meta.scopeRelation.kind,'finite-settings-member');assert.deepEqual(meta.scopeRelation.settings,member.settings);assert.deepEqual(meta.scopeRelation.remainingPages,task.pages.map(p=>p.id));assert.equal(meta.scopeRelation.declaredPages.length,56);assert(created.value.controls);
 record.note='Source edited after preparation';const rejected=await call('/tasks',body);assert.equal(rejected.status,409);assert.equal(sqlite.prepare('SELECT count(*) n FROM local_task_all_origins').get().n,1);
});
await test('saved results and snapshot projection survive external edits but stored snapshot corruption fails',async()=>{
 const result=E.run(task),saved=await call('/tasks/'+task.taskId+'/results',{result});assert.equal(saved.status,200,JSON.stringify(saved.value));assert.deepEqual(saved.value.latestRun.result,result);const before=sqlite.prepare('SELECT result_json FROM local_task_results WHERE task_id=?').get(task.taskId).result_json,reloaded=await call('/tasks/'+task.taskId+'?idea='+proposalId);assert.equal(reloaded.status,200);assert.deepEqual(reloaded.value.origins[0].origin,source.origin);const row=sqlite.prepare('SELECT snapshot_json FROM authored_finite_snapshots').get(),changed=JSON.parse(row.snapshot_json);changed.control.members[0].control.label+=' tampered';assert.throws(()=>sqlite.prepare('UPDATE authored_finite_snapshots SET snapshot_json=?').run(E.stable(changed)),/immutable/);sqlite.exec('DROP TRIGGER authored_finite_snapshots_immutable');sqlite.prepare('UPDATE authored_finite_snapshots SET snapshot_json=?').run(E.stable(changed));assert.equal((await call('/tasks/'+task.taskId+'?idea='+proposalId)).status,503);assert.equal(sqlite.prepare('SELECT result_json FROM local_task_results WHERE task_id=?').get(task.taskId).result_json,before);
});
await test('full-page and partial member projection both retain the finite dimension',async()=>{
 const full=await E.prepare({...task,pages:compiled.domain.pages});const projected=await finiteSnapshotMember(full,recipe);assert.equal(projected.scopeRelation.remainingPages.length,56);assert.equal(projected.scopeRelation.declaredPages.length,56);assert.deepEqual(projected.scopeRelation.settings,member.settings);
});
console.log(groups+' authored finite origin groups passed.');
}finally{sqlite.close();}
