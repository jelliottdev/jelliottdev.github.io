'use strict';
const assert=require('node:assert/strict'),{createHash,webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),C=require('../claim-specification.js'),Q=require('../task-parameter-question.js'),Client=require('../parameter-variation-client.js'),{fixture:openingFixture}=require('./test_derived_openings_evidence_client.cjs');
const copy=structuredClone,hash=v=>createHash('sha256').update(typeof v==='string'?v:E.stable(v)).digest('hex'),baseURL='https://fixture.invalid';
async function fixture({complete=true,published=true}={}){
 const f=await openingFixture({complete,published,match:false}),card=copy(f.input.card);card.method.value.operations[0].unit='page';
 const task=await E.prepare({...f.input.requestedTask,title:'Invented saved parent',steps:[{op:'reverse',unit:'page'}]},webcrypto),result=E.run(task),proposalId='p_'+hash(C.serialize(card)),selection={version:1,step:0,parameter:'unit',value:'word'},derivation=await Q.prepare({parentTask:task,parentCard:card,inputVersion:'raw',selection},webcrypto),run={id:hash(result),createdAt:f.source.run.createdAt,result},source={kind:'saved-task',proposalId,taskId:task.taskId},context={task,card,source,inputVersion:'raw',run},receipt={taskId:task.taskId,taskSha256:hash(task),resultId:run.id,createdAt:run.createdAt,inputVersion:'raw'},preview={schema:'liberpedia-parameter-question-preview-v1',source:{reference:source,receipt},parentQuestion:{proposalId,cardSha256:proposalId.slice(2)},derivation},previewHash=hash(preview),childProposalId='p_'+hash(C.serialize(derivation.card));
 const wire=copy(f.input.value);wire.requestedTaskId=derivation.task.taskId;
 const coverage={schema:'liberpedia-parameter-question-coverage-v1',previewHash,taskId:derivation.task.taskId,inputVersion:'raw',coveredPages:[],remainingPages:derivation.task.pages.map(p=>p.id),lookupComplete:true,finding:{kind:'opening-check',matchingPages:[]},evidence:[],derivedOpenings:wire},calls=[],overrides={};
 const fetcher=async(url,options)=>{
  const path=new URL(url).pathname;calls.push({path,method:options.method});if(options.method==='GET')return f.input.publishedOptions.fetcher(url,options);
  const body=JSON.parse(options.body);if(path==='/parameter-questions/preview')return Response.json({preview,previewHash,childProposalId});
  if(path==='/parameter-questions/coverage'){assert.equal(body.includeDerivedOpeningEvidence,true);return Response.json(overrides.coverage||coverage);}
  if(overrides.preparation&&path==='/parameter-questions/create'){const origin={schema:'liberpedia-question-derivation-v1',parentProposalId:proposalId,childProposalId,previewHash,source:preview.source,selection:derivation.selection,childTaskId:derivation.task.taskId};return Response.json({id:hash(origin),parentProposalId:proposalId,childProposalId,requestId:body.requestId,createdAt:run.createdAt});}
  if(overrides.preparation&&path==='/parameter-questions/prepare'){assert.equal(body.includeDerivedOpeningEvidence,true);return Response.json(overrides.preparation);}
  assert.fail('No write or admission is allowed in this read-only fixture: '+path);
 };
 return {coverage,calls,context,selection,overrides,derivation,childProposalId,controller:Client.create({context,baseURL,crypto:webcrypto,fetcher,pageURL:baseURL+'/run.html'})};
}
async function noTargets(fn){const run=E.run;E.run=()=>assert.fail('No target execution in the contribution client');try{return await fn();}finally{E.run=run;}}
(async()=>{let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('full derived coverage independently reloads the archived original while strict coverage remains empty',async()=>{
 const f=await fixture();await noTargets(()=>f.controller.preview(f.selection));const state=f.controller.getState();assert.deepEqual(state.coverage.coveredPages,[]);assert.equal(state.coverage.evidence.length,0);assert.equal(state.coverage.remainingPages.length,2);assert(state.effectiveCoverage.derived);assert.equal(state.effectiveCoverage.coveredPages.length,2);assert.deepEqual(state.effectiveCoverage.remainingPages,[]);assert.deepEqual(state.effectiveCoverage.evidence,[]);assert(state.effectiveCoverage.sourceLinks[0].href.startsWith('run.html#published='));assert(f.calls.some(c=>c.method==='GET'));await assert.rejects(f.controller.create(),/already cover/);assert(!f.calls.some(c=>/create|prepare|\/tasks/.test(c.path)));
});
await test('partial local reuse cannot masquerade as full or strict evidence and cancellation discards the checked union',async()=>{
 const f=await fixture({complete:false,published:false});await noTargets(()=>f.controller.preview(f.selection));const s=f.controller.getState();assert.equal(s.effectiveCoverage.coveredPages.length,1);assert.equal(s.effectiveCoverage.remainingPages.length,1);assert.deepEqual(s.coverage.coveredPages,[]);assert.equal(s.effectiveCoverage.sourceLinks[0].label,'Original computation');assert(!f.calls.some(c=>c.method==='GET'));f.controller.cancel();assert.equal(f.controller.getState().effectiveCoverage,null);await assert.rejects(f.controller.create());
});
await test('forged derived summaries changed origin and rehashed false publication cannot authorize publication',async()=>{
 for(const mutate of [v=>v.derivedOpenings.summary.coveredPages=[],v=>v.derivedOpenings.requestedTaskId='0'.repeat(64),v=>v.derivedOpenings.originals[0].origin.revision='0'.repeat(64),v=>v.derivedOpenings.originals[0].source.provenance.verificationMeaning='altered']){const f=await fixture(),bad=copy(f.coverage);mutate(bad);f.overrides.coverage=bad;await assert.rejects(noTargets(()=>f.controller.preview(f.selection)));assert.equal(f.controller.getState().effectiveCoverage,null);await assert.rejects(f.controller.create());assert(!f.calls.some(c=>/create|prepare|\/tasks/.test(c.path)));}
});
await test('a fresh earlier-output answer after explicit question creation never admits a duplicate task',async()=>{
 for(const tamper of [false,true]){
  const f=await fixture(),strict=copy(f.coverage);delete strict.derivedOpenings;f.overrides.coverage=strict;
  const wire=copy(f.coverage.derivedOpenings);if(tamper)wire.summary.matchingPages=['lp2-15'];
  f.overrides.preparation={state:'derived-prefix-answer',proposalId:f.childProposalId,parentTaskId:null,inputVersion:'raw',coverage:{requestedTask:f.derivation.task,inputVersion:'raw',coveredPages:[],remainingPages:f.derivation.task.pages.map(p=>p.id)},derivedOpenings:wire};
  await noTargets(()=>f.controller.preview(f.selection));
  if(tamper)await assert.rejects(noTargets(()=>f.controller.create()));else{const result=await noTargets(()=>f.controller.create());assert.equal(result.state,'question-created');assert.equal(result.href,'run.html#idea='+f.childProposalId);}
  assert(f.calls.some(c=>c.path==='/parameter-questions/create'));assert(f.calls.some(c=>c.path==='/parameter-questions/prepare'));assert(!f.calls.some(c=>c.path==='/tasks'));
 }
});
console.log(groups+' parameter derived-opening client groups passed; strict proof stays distinct and no hosted writes or target runs occur.');})().catch(error=>{console.error(error);process.exitCode=1;});
