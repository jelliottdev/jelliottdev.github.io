'use strict';
// Exact original intake -> canonical card -> maintained planner, no model calls.
const assert=require('node:assert/strict'),C=require('../claim-specification.js'),H=require('../claim-share.js'),I=require('../investigate.js'),E=require('../local-experiment.js');
const at='2026-10-25T12:00:00.000Z',known=v=>C.field('specified',v),copy=structuredClone;
function card(text,scope){const initial=I.initialDraft(text),draft=C.revise(initial,{aim:known('Solve LP2'),...(scope?{scope:known({pages:scope})}:{}),rules:{inputVersion:known('reviewed'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:[24,7,24]})}});return {initial,draft,card:H.cardData(C.confirm(draft,{id:'software',at}))};}
(async()=>{const {createAIPlanner,validateCandidate}=await import('../services/idea-assistant/propose-task-plan.mjs'),{planCard}=await import('../services/idea-assistant/prepare-task.mjs');let groups=0,calls=0;const planner=createAIPlanner({compile:planCard}),env={AI:{run(){calls++;assert.fail('Exact reversal intake must not call a model');}}},test=async(name,fn)=>{await fn();groups++;console.log('PASS '+name);};
 await test('line word and page reversal with exact scope clauses preserve full original source and require no model',async()=>{
  for(const unit of ['line','word','page'])for(const tail of ['LP2-15','LP2-15 and LP2-16','LP2-15–17']){
   const text='Reverse each '+unit+' on '+tail+'.',f=card(text),before=copy(f.card),out=await planner(f.card,env);assert(!out.reason,out.reason);assert.deepEqual(out.plan.steps,[{op:'reverse',unit}]);assert.equal(out.plan.inputVersion,'reviewed');assert.deepEqual(out.plan.criterion,f.card.rules.evaluation.value);assert.deepEqual(out.card.outcome,f.card.outcome);assert.deepEqual(out.card.scope,f.card.scope);assert.deepEqual(out.card.rules,f.card.rules);assert.deepEqual(f.card,before);assert.equal(f.draft.source.text,text);assert.equal(out.mapping.steps[0].source.quote,text);assert.equal(out.mapping.steps[0].source.start,0);assert.equal(out.plan.pages.length,tail.includes('–')?3:tail.includes('and')?2:1);
  }
  assert.equal(calls,0);
 });
 await test('mismatched partial duplicate invalid and conditional page clauses cannot become a faithful plan',async()=>{
  for(const [text,pages]of [
   ['Reverse each word on LP2-15',['lp2-16']],
   ['Reverse each line on LP2-15',['lp2-15','lp2-16']],
   ['Reverse each page on LP2-15 and LP2-15',['lp2-15']],
   ['Reverse each word on LP2-17–15',['lp2-15','lp2-16','lp2-17']],
   ['Reverse each word on LP2-99',['lp2-15']],
   ['Reverse each line on LP2-15, lines 2–3',['lp2-15']],
   ['Reverse each word on LP2-15 except the heading',['lp2-15']],
   ['Reverse each line on LP2-15 then skip one rune',['lp2-15']],
   ['Do not reverse each page on LP2-15',['lp2-15']],
   ['Reverse word blocks on LP2-15',['lp2-15']],
   ['Reverse the order of lines on LP2-15',['lp2-15']],
   ['Reverse each word on LP2-15 then reverse each line on LP2-16',['lp2-15','lp2-16']]
  ]){const f=card(text,pages),before=copy(f.card),candidate={version:1,steps:f.card.method.value.operations.map((op,operationIndex)=>({source:{operationIndex,start:0,quote:op.label},step:{op:'reverse',unit:'word'}})),unsupported:[]};assert(validateCandidate(f.card,candidate,{compile:planCard}).reason,text);const out=await planner(f.card,{});assert(out.reason,text);assert.deepEqual(f.card,before);}
 });
 await test('word reversal means rune order within each word, while word-block reordering stays unsupported',async()=>{
  const f=card('Reverse each word on LP2-15'),out=await planner(f.card,env);assert(!out.reason);const bundle=require('../data/local-run-inputs.json'),r=bundle.alphabet.slice(0,5).map(a=>a.rune),text=r[0]+r[1]+' '+r[2]+r[3]+r[4],task=await E.prepare({title:'Isolated reversal semantics',alphabet:bundle.alphabet,pages:[{id:'lp2-15',text}],steps:out.plan.steps,criterion:out.plan.criterion});assert.equal(E.run(task).transformed[0].text,r[1]+r[0]+' '+r[4]+r[3]+r[2]);assert.equal(calls,0);
 });
 console.log(groups+' closed reversal intake adapter groups passed; no hosted calls or writes');
})().catch(e=>{console.error(e);process.exitCode=1;});
