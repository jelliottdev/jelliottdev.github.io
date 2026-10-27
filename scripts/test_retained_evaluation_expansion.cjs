'use strict';
// Derives definitions only. Existing retained targets are never executed.
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),Q=require('../task-parameter-question.js'),C=require('../claim-specification.js'),F=require('../fixed-plan-compiler.js'),catalog=require('../published-program-source-catalog-data.js');
const copy=structuredClone,selection=value=>({parameter:'evaluation',value});
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{const run=E.run,verify=E.verify;E.run=E.verify=()=>assert.fail('No retained target execution or replay is needed to derive a criterion');try{
 await test('all 58 retained LP2-54 feedback definitions can gain either maintained evaluation unchanged',async()=>{
  const entries=catalog.entries.filter(e=>e.recordId==='lp2-54-header-feedback');assert.equal(entries.length,58);
  for(const entry of entries){const receipt=JSON.parse(fs.readFileSync(entry.path,'utf8')),source=receipt.entries.find(e=>e.recordId===entry.recordId&&e.caseId===entry.caseId&&e.revision===entry.revision),before=E.stable(source),q=await Q.archived({task:source.task,inputVersion:source.inputVersion},webcrypto);assert.equal(source.task.criterion.kind,'exact-prefix-set');assert.deepEqual(source.task.criterion.openings.map(o=>o.values),[[24],[10],[3]]);
   for(const choice of Q.evaluationChoices(source.task)){const input={parentTask:source.task,parentCard:q.card,inputVersion:source.inputVersion,selection:choice.selection},d=await Q.prepare(input,webcrypto);assert.notEqual(d.task.taskId,source.task.taskId);assert.deepEqual(d.task.pages,source.task.pages);assert.deepEqual(d.task.steps,source.task.steps);assert.deepEqual(d.card.outcome,q.card.outcome);assert.deepEqual(F.compile(d.card).criterion,choice.criterion);await Q.validate(input,d,webcrypto);}assert.equal(E.stable(source),before);
  }
 });
 await test('maintained Warning and language criteria omit exactly their identical destination',async()=>{
  const entry=catalog.entries.find(e=>e.recordId==='lp2-54-header-feedback'),source=JSON.parse(fs.readFileSync(entry.path,'utf8')).entries[0];
  for(const id of ['warning-opening','language-samples']){const criterion=C.EVALUATION_CHOICES.find(c=>c.id===id).value,task=await E.prepare({...source.task,criterion},webcrypto),choices=Q.evaluationChoices(task);assert.equal(choices.length,1);assert.notEqual(choices[0].selection.value,id);const base=await Q.archived({task:source.task,inputVersion:'raw'},webcrypto),card=copy(base.card);card.rules.evaluation={status:'specified',value:copy(criterion)};const input={parentTask:task,parentCard:card,inputVersion:'raw',selection:selection(id)};await assert.rejects(Q.prepare(input,webcrypto),/different maintained/);input.selection=choices[0].selection;const derived=await Q.prepare(input,webcrypto);assert.deepEqual(derived.task.steps,task.steps);assert.deepEqual(derived.card.outcome,card.outcome);}
 });
 await test('word-statistic criteria remain excluded and literal singleton sets are not silently equated',async()=>{
  const entry=catalog.entries.find(e=>e.recordId==='lp2-54-header-feedback'),source=JSON.parse(fs.readFileSync(entry.path,'utf8')).entries[0],warning=C.EVALUATION_CHOICES.find(c=>c.id==='warning-opening').value;
  const set=await E.prepare({...source.task,criterion:{kind:'exact-prefix-set',openings:[{id:'named-warning',values:warning.values}]}},webcrypto);assert.equal(Q.evaluationChoices(set).length,2,'An exact named criterion retains its identity, even with equivalent literal values');
  for(const criterion of [{kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'},{kind:'word-affine-count',lag:1,a:1,b:0,boundaries:'non-rune'}])assert.deepEqual(Q.evaluationChoices(await E.prepare({...source.task,criterion},webcrypto)),[]);
  const zero=await E.prepare({...source.task,steps:[]},webcrypto);assert.deepEqual(Q.evaluationChoices(zero),[]);
 });
 console.log(groups+' retained evaluation-expansion groups passed; no manuscript computation.');
}finally{E.run=run;E.verify=verify;}})().catch(e=>{console.error(e);process.exitCode=1;});
