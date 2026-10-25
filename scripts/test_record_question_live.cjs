'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{createHash}=require('node:crypto'),E=require('../local-experiment.js'),Evidence=require('../computation-evidence.js'),V=require('../task-variants.js'),Live=require('../record-question-live.js'),Client=require('../verified-evidence-client.js'),F=require('../research-family.js'),FQ=require('../family-question-evidence.js');
const clone=v=>JSON.parse(JSON.stringify(v)),hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),at='2026-10-25T12:00:00.000Z',config={endpoint:'https://worker.example/ask',localTaskEndpoint:'https://worker.example/tasks',recordPlanEndpoint:'https://worker.example/record-plans'},bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8'));
const boundaryRecord=JSON.parse(fs.readFileSync('experiments/records/word-internal-affine-lags/record.json','utf8')),familyRecord=JSON.parse(fs.readFileSync('experiments/records/wulfic-autokey-seed-families/record.json','utf8'));
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}const response=value=>new Response(JSON.stringify(value),{headers:{'content-type':'application/json'}});
async function receipt(task){const result=E.run(task);return {task,inputVersion:'raw',run:{id:hash(result),createdAt:at,result}};}
async function fixture(){
 const record=clone(boundaryRecord),recipe=record.browser_followups[0];recipe.inputs.pages=recipe.inputs.pages.slice(0,1);recipe.card.scope.value.pages=recipe.inputs.pages.map(p=>p.id);
 const task=await E.prepare({title:recipe.title,pages:recipe.inputs.pages.map(p=>({id:p.id,text:bundle.pages.find(x=>x.id===p.id).raw})),alphabet:bundle.alphabet,steps:[],criterion:recipe.card.rules.evaluation.value}),other=await V.prepare(task),a=await receipt(task),b=await receipt(other),sources=new Map([a,b].map(s=>[s.task.taskId,s]));
 const coverage=async(t,src)=>({...await Evidence.compare(t,'raw',src),requestedTask:t,inputVersion:'raw',truncated:false});
 const plan={state:'plan-ready',origin:{recordId:record.id,followupId:recipe.id,protocolSha256:hash(recipe)},task,inputVersion:'raw',coverage:await coverage(task,[a]),boundaryComparison:{task:other,coverage:await coverage(other,[b])}};
 const calls=[];const fetcher=async(url,init={})=>{calls.push({url,init});if(url===config.recordPlanEndpoint){assert.equal(init.method,'POST');assert.deepEqual(JSON.parse(init.body),{recordId:record.id,followupId:recipe.id,includeExisting:true,includeBoundaryComparison:true});return response(plan);}const s=sources.get(url.split('/').pop());if(!s)throw Error('Unexpected request '+url);return response({id:s.task.taskId,title:s.task.title,plan:s.task,inputVersion:'raw',state:'results-verified',latestRun:s.run});};
 return {record,recipe,task,other,a,b,plan,coverage,calls,fetcher};
}
(async()=>{
 await test('boundary live answer is lazy, exact and read-only; no target execution API',async()=>{
  const f=await fixture(),states=[],original=clone(f.record),controller=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>bundle,fetcher:f.fetcher,onState:s=>states.push(s)});assert.equal(f.calls.length,0);const publicRun=E.run;E.run=()=>{throw Error('No public target execution allowed');};try{const decision=await controller.activate();assert.equal(decision.state,'answered');assert.match(decision.limit,/not a significance test/);assert.deepEqual(states.map(x=>x.state),['loading','answered']);assert.equal(f.calls.length,3);await controller.activate();assert.equal(f.calls.length,3);assert.deepEqual(f.record,original);}finally{E.run=publicRun;controller.destroy();}
 });
 await test('partial coverage offers only missing comparison pages; incomplete search never calls them new work',async()=>{
  const f=await fixture();f.plan.boundaryComparison.coverage=await f.coverage(f.other,[]);let c=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>bundle,fetcher:f.fetcher});let d=await c.activate();assert.equal(d.state,'missing-evidence');assert.deepEqual(d.next.pages,f.other.pages.map(p=>p.id));c.destroy();f.plan.boundaryComparison.coverage.truncated=true;c=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>bundle,fetcher:f.fetcher});d=await c.activate();assert.equal(d.state,'unavailable');assert.equal(d.next.kind,'retry-evidence');c.destroy();
 });
 await test('changed source result, scope, recipe pin and failed lookup remain unavailable',async()=>{
  for(const change of [f=>f.b.run.result.transformed[0].text='changed',f=>f.plan.boundaryComparison.coverage.remainingPages=['lp2-55'],f=>f.plan.origin.protocolSha256='0'.repeat(64),f=>{f.plan.boundaryComparison.coverageUnavailable=true;}]){const f=await fixture();change(f);const states=[],c=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>bundle,fetcher:f.fetcher,onState:s=>states.push(s)});assert.equal(await c.activate(),null);assert.deepEqual(states.map(s=>s.state),['loading','unavailable']);assert(!states.some(s=>s.decision?.next?.kind==='run-missing-evidence'));c.destroy();}
 });
 await test('destroy and retry suppress late response/late failure with abort signals',async()=>{
  const f=await fixture(),states=[];let release;const wait=new Promise(resolve=>release=resolve);let first=true;const fetcher=async(url,init)=>{if(first){first=false;await wait;throw Error('Stale failure');}return f.fetcher(url,init);};const c=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>bundle,fetcher,onState:s=>states.push(s)}),a=c.activate();await new Promise(r=>setTimeout(r,5));const b=c.retry();assert.equal((await b).state,'answered');release();await a;assert.deepEqual(states.map(s=>s.state),['loading','loading','answered']);c.destroy();const late=[],dead=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>new Promise(r=>setTimeout(()=>r(bundle),10)),fetcher:f.fetcher,onState:s=>late.push(s)}),p=dead.activate();dead.destroy();await p;assert.deepEqual(late.map(s=>s.state),['loading']);
 });
 await test('DEOR question uses one compact wire and locally verified evidence, not coverage flags',async()=>{
  const prep=await F.createPreparer(bundle),snapshot=prep.snapshot,empty={familyId:snapshot.id,revision:snapshot.revision,sources:[],cases:[],lookupComplete:true},states=[],calls=[];let wire=empty;
  const fetcher=async(url,init)=>{calls.push(url);assert(!init.method||init.method==='GET');assert.equal(url,'https://worker.example/families/deor-feedback-v1/question');return response(wire);};
  const c=Live.createController({record:familyRecord,questionId:'deor-warning-opening',config,loadInputs:()=>bundle,fetcher,onState:s=>states.push(s)});assert.equal(calls.length,0);const partial=await c.activate();assert.equal(partial.state,'missing-evidence');assert.equal(partial.next.caseIds.length,12);assert.equal(calls.length,1);
  const proof=await FQ.summarize({snapshot,bundle,sources:[]}),sources=[],cases=[];for(let i=0;i<proof.missingCaseIds.length;i+=12){const plan=await prep.prepare(proof.missingCaseIds.slice(i,i+12));for(const item of plan.cases){cases.push({caseId:item.id,sourceIndex:sources.length});sources.push(await receipt(item.task));}}
  wire={...empty,sources,cases};const complete=await c.retry();assert.equal(complete.state,'answered');assert.equal(complete.answer,'prefix-not-found');assert.equal(complete.next,null);assert.equal(calls.length,2);wire={...wire,revision:'0'.repeat(64)};assert.equal(await c.retry(),null);assert.equal(states.at(-1).state,'unavailable');c.destroy();
 });
 await test('shared coverage loader rejects unverified clones and selected corrupt receipts',async()=>{
  const f=await fixture(),client=Client.create({request:f.fetcher,endpoint:config.localTaskEndpoint,validEndpoint:()=>true});const checked=await client.checkCoverage(f.plan.coverage);assert.equal(client.getSources(checked).length,1);assert.throws(()=>client.getSources(clone(checked)));f.a.run.id='0'.repeat(64);await assert.rejects(()=>client.checkCoverage(f.plan.coverage));
 });
 await test('oversized and unreadable source bodies fail unavailable; streaming stops and cancels at byte bound',async()=>{
  for(const mode of ['declared','streamed','invalid-utf8','broken-stream','unreadable']){
   const f=await fixture(),states=[];let reads=0,cancelled=false;
   const sourceResponse=mode==='unreadable'?{ok:true}:{ok:true,headers:{get:()=>mode==='declared'?String(2*1024*1024+1):null},body:{getReader:()=>({async read(){reads++;if(mode==='broken-stream')throw Error('Connection lost');if(mode==='invalid-utf8')return reads===1?{value:new Uint8Array([0xff]),done:false}:{done:true};return {done:false,value:new Uint8Array(1024*1024+1)};},async cancel(){cancelled=true;},releaseLock(){}})}};
   const c=Live.createController({record:f.record,questionId:'layout-boundary-sensitivity',config,loadInputs:()=>bundle,fetcher:(url,init)=>url===config.recordPlanEndpoint?f.fetcher(url,init):Promise.resolve(sourceResponse),onState:s=>states.push(s)});
   assert.equal(await c.activate(),null);assert.deepEqual(states.map(s=>s.state),['loading','unavailable']);assert(!states.at(-1).decision);
   if(mode==='declared')assert.equal(reads,0,'Oversized declared body must not be read');
   if(mode==='streamed'){assert.equal(reads,2,'Do not consume the rest of an oversized body');assert.equal(cancelled,true);}
   if(mode==='broken-stream')assert.equal(cancelled,true);c.destroy();
  }
 });
 console.log(groups+' live question test groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
