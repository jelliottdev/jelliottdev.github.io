/* Exact historical fixed-source recovery; no target execution or hosted writes. */
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import E from '../local-experiment.js';
import {loadRecordPlan,loadSavedRecordPlan,recordPlanDigest as sha,createRecordPlanHandler} from '../services/idea-assistant/record-plans.mjs';
import {fixture,prepare,create,seed,idea} from './test_authored_prefix_reuse.mjs';
import {createLocalTaskHandler} from '../services/idea-assistant/local-tasks.mjs';
const root=new URL('../',import.meta.url),copy=structuredClone;
const sourceFiles=readdirSync(new URL('experiments/records/',root)).flatMap(id=>{try{const bytes=readFileSync(new URL('experiments/records/'+id+'/record.json',root)),record=JSON.parse(bytes);return record.status==='published'?(record.browser_followups||[]).filter(r=>!Object.hasOwn(r,'kind')).map(recipe=>({bytes,record,recipe})):[];}catch{return [];}});
assert(sourceFiles.length>0,'The complete maintained fixed source set must not be empty');
const witnessIds=new Set(sourceFiles.map(s=>s.recipe.control.task.taskId)),originalRun=E.run;
E.run=task=>{assert(witnessIds.has(task.taskId),'Source validation must never execute manuscript work');return originalRun(task);};
let getterReads=0;await assert.rejects(()=>loadSavedRecordPlan({get recordId(){getterReads++;return 'anything';},followupId:'first',recordSha256:'0'.repeat(64),protocolSha256:'0'.repeat(64)}),/identity/);assert.equal(getterReads,0);
let checked=0;
try{
 for(const {bytes,record,recipe} of sourceFiles){
  const ref={recordId:record.id,followupId:recipe.id},calls=[];let mode='current',changedInput=false;
  const origin={...ref,recordSha256:await sha(bytes),protocolSha256:await sha(E.stable(recipe))};
  const fetcher=async url=>{
   const path=new URL(url).pathname;calls.push(path);
   if(path==='/experiments/records/'+ref.recordId+'/record.json')return mode==='missing'?new Response(null,{status:404}):new Response(mode==='current'?bytes:JSON.stringify({...record,browser_followups:[]}),{headers:{'Content-Type':'application/json'}});
   if(path==='/published-sources/records/'+origin.recordSha256+'.json')return new Response(bytes,{headers:{'Content-Type':'application/json'}});
   let value=JSON.parse(readFileSync(new URL(path.slice(1),root),'utf8'));
   if(changedInput&&path.startsWith('/data/pages/')){value.raw+='ᚠ';if(value.reviewed_text)value.reviewed_text+='ᚠ';}
   if(changedInput&&path==='/data/local-run-inputs.json')for(const p of value.pages){p.raw+='ᚠ';if(p.reviewed_text)p.reviewed_text+='ᚠ';}
   return Response.json(value);
  };
  const current=await loadRecordPlan(ref,{fetcher});assert.deepEqual(current.origin,origin);
  for(mode of ['changed','missing']){const saved=await loadSavedRecordPlan(origin,{fetcher});assert.deepEqual(saved,current);assert(calls.includes('/published-sources/records/'+origin.recordSha256+'.json'));}
  mode='changed';await assert.rejects(()=>loadRecordPlan(ref,{fetcher}),/unavailable/);
  changedInput=true;await assert.rejects(()=>loadSavedRecordPlan(origin,{fetcher}),/input|aggregate|bundle|pin/i);changedInput=false;
  await assert.rejects(()=>loadSavedRecordPlan({...origin,protocolSha256:'0'.repeat(64)},{fetcher}),/declaration changed/);
  checked++;
 }
}finally{E.run=originalRun;}
console.log('PASS all '+checked+' fixed recipes retain exact source/task/control/card across changed or missing current records; current input changes and forged protocol pins reject');
// An issued, evidence-bound remainder may finish from its exact archived source.
// A fresh request or direct origin submission cannot acquire that authority.
const f=await fixture();try{
 const originalBytes=new TextEncoder().encode(JSON.stringify(f.record)),originalOrigin=copy(f.loaded.origin);
 const previous=await seed(f,idea(f,['lp2-01'],'Earlier unchanged output','measurement'),['lp2-01'],'Unchanged private measurement',{kind:'measurement'});
 const pending=await prepare(f);assert.deepEqual(pending.task.pages.map(p=>p.id),['lp2-02','lp2-03']);
 const calls=[],fetcher=async(url,options)=>{
  const path=new URL(url).pathname;calls.push(path);
  if(path==='/published-sources/records/'+originalOrigin.recordSha256+'.json')return new Response(originalBytes,{headers:{'Content-Type':'application/json'}});
  return f.fetcher(url,options);
 };
 assert.equal(await sha(originalBytes),originalOrigin.recordSha256);
 f.record.browser_followups=[];
 f.tasks=createLocalTaskHandler({fetcher,now:()=>new Date('2026-10-25T12:00:00.000Z')});
 const admitted=await create(f,pending);assert.deepEqual(admitted.selectedRecordOrigin,originalOrigin);assert(calls.some(p=>p.startsWith('/published-sources/records/')));
 assert.deepEqual(admitted.plan,pending.task);assert.equal(f.sqlite.prepare('SELECT task_json FROM local_tasks WHERE id=?').get(previous.task.taskId).task_json,E.stable(previous.task));
 await f.call('tasks','/tasks',{proposalId:f.owner.id,task:pending.task,inputVersion:'raw',parentTaskId:null,origin:originalOrigin},422);
 await f.call('prepare','/prepare-task',{proposalId:f.owner.id,parentTaskId:null,includeDerivedPrefixEvidence:true,recordOrigin:originalOrigin},422);
 const handler=createRecordPlanHandler({fetcher}),response=await handler(new Request('https://worker.example/record-plans',{method:'POST',headers:{origin:'https://jelliottdev.github.io','Content-Type':'application/json'},body:JSON.stringify({recordId:originalOrigin.recordId,followupId:originalOrigin.followupId})}),f.env);assert.equal(response.status,422);
 console.log('PASS issued private remainder completes from the original archive; fresh preparation, direct origin admission and record discovery remain current-only');
}finally{f.sqlite.close();}
