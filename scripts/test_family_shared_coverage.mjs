import {applyMigrations} from '../services/idea-assistant/sqlite-test-migrations.mjs';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import {createHash,webcrypto} from 'node:crypto';
import L from '../local-experiment.js';
import F from '../research-family.js';
import {sharedFamilyCoverage,readSharedFamilyCase} from '../services/idea-assistant/family-shared-coverage.mjs';
const clone=v=>JSON.parse(JSON.stringify(v)),hash=v=>createHash('sha256').update(L.stable(v)).digest('hex'),at='2026-10-24T12:00:00.000Z';
const bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8'));
async function fixture(input=bundle){
 const sqlite=new DatabaseSync(':memory:');applyMigrations(sqlite);
 const queries=[],db={prepare(sql){queries.push(sql);return{bind(...args){return{async all(){return{results:sqlite.prepare(sql).all(...args)};},async first(){return sqlite.prepare(sql).get(...args)||null;}};}};}};
 const preparer=await F.createPreparer(input,webcrypto),caseId=F.caseIds(preparer.snapshot).find(id=>id.startsWith('repeat--subtract--page--lp2-00'));
 const task=(await preparer.prepare([caseId])).cases[0].task;
 let n=0;async function source(changes={},options={}){
  const taskPlan=await L.prepare({...task,title:'Saved task '+(++n),...changes},webcrypto),id='p_'+String(n).padStart(64,'0'),version=options.inputVersion||'raw';
  sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,id.slice(2),'{}','',at);
  if(options.public!==false)sqlite.prepare('INSERT INTO research_ideas(proposal_id,created_at,created_day) VALUES(?,?,?)').run(id,at,at.slice(0,10));
  const taskText=L.stable(taskPlan);sqlite.prepare('INSERT INTO local_tasks(id,task_hash,create_hash,proposal_id,card_json,task_json,input_version,parent_task_id,created_at,created_day) VALUES(?,?,?,?,?,?,?,?,?,?)').run(taskPlan.taskId,hash(taskPlan),'0'.repeat(64),id,'{}',taskText,version,null,at,at.slice(0,10));
  sqlite.prepare('INSERT INTO local_task_ideas(task_id,proposal_id,input_version,parent_task_id,created_at,created_day) VALUES(?,?,?,?,?,?)').run(taskPlan.taskId,id,options.associationVersion||version,null,at,at.slice(0,10));
  let result=null;if(options.verified!==false){result=L.run(taskPlan);sqlite.prepare('INSERT INTO local_task_results(id,task_id,result_json,created_at,created_day) VALUES(?,?,?,?,?)').run(hash(result),taskPlan.taskId,L.stable(result),at,at.slice(0,10));}
  return {task:taskPlan,result};
 }
 return{sqlite,db,queries,preparer,caseId,task,source};
}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('public exact protocol reuses batches/titles and returns original receipt deterministically',async()=>{
 const f=await fixture(),page1=f.preparer.snapshot.pages.find(p=>p.id==='lp2-01'),a=await f.source(),b=await f.source({pages:[page1,f.task.pages[0]]});
 const old=L.run;L.run=()=>{throw Error('Shared coverage must not decode targets.');};let coverage,read;
 try{coverage=await sharedFamilyCoverage({...f,crypto:webcrypto});assert.equal(f.queries.length,18);read=await readSharedFamilyCase({...f,caseId:f.caseId,crypto:webcrypto});}finally{L.run=old;}
 assert.deepEqual(coverage.completed,[f.caseId,f.caseId.replace('lp2-00','lp2-01')].sort());assert.deepEqual(coverage.matched,[]);assert.equal(coverage.sources.length,2);
 const chosen=[a,b].sort((a,b)=>a.task.taskId.localeCompare(b.task.taskId))[0];assert.equal(coverage.sources.find(s=>s.caseId===f.caseId).taskId,chosen.task.taskId);
 assert.deepEqual(read.source.task,chosen.task);assert.deepEqual(read.source.run.result,chosen.result);assert.equal(read.reference.resultId,hash(chosen.result));assert.equal(f.queries.length,20,'Reading one case uses one protocol lookup and one pinned receipt query');
 assert(f.queries.every(sql=>/^\s*SELECT\b/.test(sql)));const sql=f.queries[0];const details=f.sqlite.prepare('EXPLAIN QUERY PLAN '+sql).all(f.task.engine,L.stable(f.task.alphabet),L.stable(f.task.steps),L.stable(f.task.criterion));assert(details.some(row=>row.detail.includes('local_tasks_protocol_lookup')));
});
await test('exact page text/key/criterion/version, publication and accepted results are mandatory',async()=>{
 for(const kind of ['text','key','criterion','reviewed','private','pending','association']){
  const f=await fixture(),changes={},options={};if(kind==='text')changes.pages=[{...f.task.pages[0],text:f.task.pages[0].text+' '}];if(kind==='key')changes.steps=[{...f.task.steps[0],key:[23,12,3,4]}];if(kind==='criterion')changes.criterion={kind:'exact-prefix',values:[24]};if(kind==='reviewed')options.inputVersion='reviewed';if(kind==='private')options.public=false;if(kind==='pending')options.verified=false;if(kind==='association')options.associationVersion='reviewed';await f.source(changes,options);
  assert.deepEqual(await sharedFamilyCoverage({...f,crypto:webcrypto}),{completed:[],matched:[],sources:[]},kind);assert.equal(await readSharedFamilyCase({...f,caseId:f.caseId,crypto:webcrypto}),null);
 }
});
await test('matching and failed prefixes both cover cases, with true matches retained separately',async()=>{
 const input=clone(bundle),warning=[24,7,24,4,9,21,17,18,20,10,18,1],key=[23,18,3,4];input.pages.find(p=>p.id==='lp2-00').raw=warning.map((v,i)=>input.alphabet[(v+key[i%4])%29].rune).join('');
 const f=await fixture(input);await f.source();const coverage=await sharedFamilyCoverage({...f,crypto:webcrypto});assert.deepEqual(coverage.completed,[f.caseId]);assert.deepEqual(coverage.matched,[f.caseId]);
});
await test('corrupt task and result identities fail closed; invalid case IDs rejected',async()=>{
 for(const kind of ['task-hash','result-hash','geometry']){
  const f=await fixture(),saved=await f.source();if(kind==='task-hash')f.sqlite.prepare('UPDATE local_tasks SET task_hash=?').run('0'.repeat(64));
  if(kind==='result-hash')f.sqlite.prepare('UPDATE local_task_results SET id=?').run('0'.repeat(64));
  if(kind==='geometry'){const result=clone(saved.result);result.transformed[0].text+='x';f.sqlite.prepare('UPDATE local_task_results SET id=?,result_json=?').run(hash(result),L.stable(result));}
  await assert.rejects(sharedFamilyCoverage({...f,crypto:webcrypto}));
 }
 const f=await fixture();await assert.rejects(readSharedFamilyCase({...f,caseId:'repeat--subtract--page--lp2-50',crypto:webcrypto}));assert.equal(f.queries.length,0);
});
await test('excessive candidates explicitly stop rather than silently omit coverage',async()=>{
 const f=await fixture();for(let i=0;i<101;i++)await f.source();await assert.rejects(sharedFamilyCoverage({...f,crypto:webcrypto}),/100-source lookup limit/);
});
console.log('PASS '+groups+' reverse shared-family coverage groups; no writes, target decoding or copied receipts during lookup.');
