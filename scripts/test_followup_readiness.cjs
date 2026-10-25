'use strict';
const assert=require('node:assert/strict'),{createHash}=require('node:crypto'),E=require('../local-experiment.js'),Evidence=require('../computation-evidence.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),Live=require('../followup-readiness.js'),Prefix=require('./test_ordinary_prefix_evidence_client.cjs');
const clone=structuredClone,hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),textHash=v=>createHash('sha256').update(v).digest('hex'),at='2026-10-25T12:00:00.000Z',field=v=>C.field('specified',v),config={endpoint:'https://worker.example/ask',recordPlanEndpoint:'https://worker.example/record-plans',localTaskEndpoint:'https://worker.example/tasks'};
async function receipt(task){const result=E.run(task);return {task,inputVersion:'raw',run:{id:hash(result),createdAt:at,result}};}
async function fixture({prefix=false,positive=false,full=false}={}){
 const p=await Prefix.fixture({prefix:positive?7:28,complete:full}),bundle=p.bundle;
 const card=prefix?p.card:H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic readiness test'},aim:field('measure'),scope:field({pages:['lp2-15','lp2-17']}),method:field({operations:[{id:'word_prime_sums',label:'Word prime sums',table:'canonical',boundaries:'non-rune'}]}),rules:{representation:field('GP29'),inputVersion:field('raw'),evaluation:field({kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'})}}),{id:'readiness',at}));
 const task=prefix?p.requestedTask:await E.prepare({title:'Synthetic sums',pages:card.scope.value.pages.map(id=>({id,text:bundle.pages.find(page=>page.id===id).raw})),alphabet:bundle.alphabet,steps:[],criterion:card.rules.evaluation.value});
 const controlTask=await E.prepare({...task,title:'Synthetic implementation control',pages:[{id:'lp1-00',text:bundle.alphabet[0].rune}]}),control={label:'Synthetic control',task:controlTask,expected_result_sha256:hash(E.run(controlTask))};
 const recipe={id:'source-check',title:task.title,question:'Does this exact synthetic check have saved evidence?',scope_change:'Use the declared two pages.',limitation:'Only this exact synthetic check.',card,inputs:{version:'raw',alphabet_sha256:hash(bundle.alphabet),pages:task.pages.map(page=>({id:page.id,text_sha256:textHash(page.text)}))},control};
 const record={id:'source-record',browser_followups:[recipe]},saved=await receipt(await E.prepare({...task,title:'Saved original calculation',pages:full?task.pages:task.pages.slice(0,1)})),sources=new Map([[saved.task.taskId,saved]]);
 const coverage=async originals=>({...await Evidence.compare(task,'raw',originals),requestedTask:task,inputVersion:'raw',truncated:false});
 const plan={state:'plan-ready',origin:{recordId:record.id,followupId:recipe.id,recordSha256:hash(record),protocolSha256:hash(recipe)},card,task,inputVersion:'raw',control,question:recipe.question,scopeChange:recipe.scope_change,limitation:recipe.limitation,coverage:await coverage([saved]),...(prefix?{derivedCoverage:p.value}:{})},calls=[];
 const fetcher=async(url,init={})=>{calls.push({url,init});assert(init.signal);assert.equal(init.cache,'no-store');if(url===config.recordPlanEndpoint){assert.equal(init.method,'POST');assert.deepEqual(JSON.parse(init.body),{recordId:record.id,followupId:recipe.id,includeExisting:true,includeExistingContext:true,includeDerivedPrefixEvidence:true});return Response.json(plan);}assert(!init.method||init.method==='GET','No publish/create/result requests');const source=sources.get(url.split('/').pop());assert(source,'Only saved original receipts may be fetched');return Response.json({id:source.task.taskId,title:source.task.title,plan:source.task,inputVersion:'raw',state:'results-verified',latestRun:source.run});};
 return {record,recipe,task,saved,plan,bundle,coverage,calls,fetcher,sources};
}
function controller(f,extra={}){return Live.createController({record:f.record,check:f.recipe,config,loadInputs:()=>f.bundle,fetcher:f.fetcher,...extra});}
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
(async()=>{
 await test('lazy immutable source, real remaining measurement and full strict results; no missing target run',async()=>{
  for(const full of [false,true]){const f=await fixture({full}),before=clone(f.record),states=[],c=controller(f,{onState:s=>states.push(s)});assert.equal(f.calls.length,0);const run=E.run;E.run=()=>assert.fail('No new requested work may run');try{const state=await c.activate();assert.deepEqual(state,{state:full?'results':'remaining',...(full?{}:{remainingCount:1}),totalPages:2});await c.activate();assert.equal(f.calls.length,2);assert.deepEqual(states.map(s=>s.state),['loading',full?'results':'remaining']);assert.deepEqual(f.record,before);}finally{E.run=run;c.destroy();}}
 });
 await test('strict full prefix, derived early positive and derived full negative answer the exact question',async()=>{
  for(const settings of [{full:true},{positive:true},{full:true,derivedOnly:true}]){const f=await fixture({prefix:true,...settings});if(settings.derivedOnly)f.plan.coverage=await f.coverage([]);const c=controller(f);assert.deepEqual(await c.activate(),{state:'answered',totalPages:2});c.destroy();}
  const f=await fixture({prefix:true});f.plan.coverage=await f.coverage([]);const c=controller(f);assert.deepEqual(await c.activate(),{state:'remaining',remainingCount:1,totalPages:2});c.destroy();
 });
 await test('strict and derived proof page unions cover the scope without double-counting overlap',async()=>{
  const f=await fixture({prefix:true}),second=await receipt(await E.prepare({...f.task,title:'Earlier output on other page',pages:[f.task.pages[1]],criterion:{kind:'measurement'}}));
  f.plan.derivedCoverage.sources=[second];f.plan.derivedCoverage.sourceLocations=[{taskId:second.task.taskId,href:'run.html#task='+second.task.taskId,label:'Original computation'}];f.plan.derivedCoverage.summary={coveredPages:['lp2-17'],matchingPages:[],remainingPages:['lp2-15']};
  const c=controller(f);assert.deepEqual(await c.activate(),{state:'answered',totalPages:2});c.destroy();
 });
 await test('forged strict claims, saved receipts, derived claims and absent derived proof fail unavailable',async()=>{
  for(const mutate of [f=>f.plan.coverage.remainingPages=[],f=>f.plan.coverage.coveredPages=['lp2-15','lp2-17'],f=>f.saved.run.id='0'.repeat(64),f=>f.plan.origin.protocolSha256='0'.repeat(64),f=>f.plan.task.criterion.table='reversed',f=>f.plan.card.scope.value.pages.pop()]){const f=await fixture();mutate(f);const c=controller(f);assert.deepEqual(await c.activate(),{state:'unavailable'});c.destroy();}
  for(const mutate of [f=>f.plan.derivedCoverage.summary.matchingPages=['lp2-17'],f=>delete f.plan.derivedCoverage,f=>f.plan.derivedCoverage.sources[0].run.result.metrics.runes++]){const f=await fixture({prefix:true});mutate(f);const c=controller(f);assert.deepEqual(await c.activate(),{state:'unavailable'});c.destroy();}
 });
 await test('incomplete lookup never advertises work; verified affirmative proof can still answer',async()=>{
  for(const prefix of [false,true]){const f=await fixture({prefix});f.plan.coverage.truncated=true;const c=controller(f);assert.deepEqual(await c.activate(),{state:'unavailable'});c.destroy();}
  const f=await fixture({prefix:true,positive:true});f.plan.derivedCoverage.lookupComplete=false;const c=controller(f);assert.deepEqual(await c.activate(),{state:'answered',totalPages:2});c.destroy();
 });
 await test('source pins reject changed official text or alphabet before a plan request',async()=>{
  for(const mutate of [f=>f.bundle.pages.find(p=>p.id==='lp2-15').raw+=' ',f=>f.bundle.alphabet[0].prime=997]){const f=await fixture();mutate(f);const c=controller(f);assert.deepEqual(await c.activate(),{state:'unavailable'});assert.equal(f.calls.length,0);c.destroy();}
 });
 await test('destroyed queued controller never loads; retry aborts old generation and suppresses late updates',async()=>{
  const f=await fixture(),states=[];let release,entered;const waiting=new Promise(r=>release=r),started=new Promise(r=>entered=r);let loads=0,oldSignal;
  const c=controller(f,{onState:s=>states.push(s),loadInputs:async({signal})=>{if(++loads===1){oldSignal=signal;entered();await waiting;}return f.bundle;}}),first=c.activate();await started;const second=await c.retry();assert.equal(second.state,'remaining');assert(oldSignal.aborted);release();assert.equal(await first,null);assert.deepEqual(states.map(s=>s.state),['loading','loading','remaining']);c.destroy();
  const dead=controller(f,{loadConfig:()=>assert.fail('Queued destroyed work must not start')});dead.destroy();const count=f.calls.length;assert.equal(await dead.activate(),null);assert.equal(await dead.retry(),null);assert.equal(f.calls.length,count);
  let open;const gate=new Promise(r=>open=r),seen=[],late=controller(f,{onState:s=>seen.push(s),loadInputs:async()=>{await gate;return f.bundle;}}),pending=late.activate();late.destroy();open();assert.equal(await pending,null);assert.deepEqual(seen,[{state:'loading'}]);
 });
 await test('shared loaders are supported; missing service and failed bounded response remain unavailable',async()=>{
  const f=await fixture();let configLoads=0,inputLoads=0;const c=controller(f,{config:undefined,loadConfig:async()=>{configLoads++;return config;},loadInputs:async()=>{inputLoads++;return f.bundle;}});assert.equal((await c.activate()).state,'remaining');assert.equal(configLoads,1);assert.equal(inputLoads,1);c.destroy();
  const bad=controller(f,{config:{...config,recordPlanEndpoint:'http://evil.invalid/record-plans'}});assert.deepEqual(await bad.activate(),{state:'unavailable'});bad.destroy();
  const oversized=controller(f,{fetcher:async()=>new Response('{}',{headers:{'content-length':String(8*1024*1024+1)}})});assert.deepEqual(await oversized.activate(),{state:'unavailable'});oversized.destroy();
 });
 await test('browser UMD uses the same shared validators and readiness states',async()=>{
  const fs=require('node:fs'),vm=require('node:vm'),context=vm.createContext({LocalExperiment:E,RecordFollowups:require('../record-followups.js'),VerifiedEvidenceClient:require('../verified-evidence-client.js'),OrdinaryPrefixEvidenceClient:require('../ordinary-prefix-evidence-client.js'),LocalInputBundle:require('../local-input-bundle.js'),ClaimSpecification:C,FiniteJSON:require('../finite-json.js'),TextEncoder,AbortController,AbortSignal,DOMException,URL,crypto:globalThis.crypto});
  vm.runInContext(fs.readFileSync(require.resolve('../followup-readiness.js'),'utf8'),context);const f=await fixture(),browser=context.FollowupReadiness.createController({record:f.record,check:f.recipe,config,loadInputs:()=>f.bundle,fetcher:f.fetcher});assert.equal((await browser.activate()).state,'remaining');browser.destroy();
 });
 console.log(`PASS ${groups} readiness groups: source pins, immutable exact/derived receipts, conservative states and lifecycle`);
})().catch(error=>{console.error(error);process.exitCode=1;});
