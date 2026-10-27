'use strict';
const assert=require('node:assert/strict'),{webcrypto,createHash}=require('node:crypto'),E=require('../local-experiment.js'),V=require('../task-parameter-variants.js'),Context=require('../published-variation-context.js');
(async()=>{
 const task=require('../published-opening-evidence-data.js').entries[0].task,context={task,inputVersion:'raw'},choice=V.suggestions(task)[0];assert(choice);
 const hints={schema:'liberpedia-archived-variation-navigation-v1',parentTaskHash:createHash('sha256').update(E.stable(task)).digest('hex'),inputVersion:'raw',catalogGeneration:'a'.repeat(64),choices:[{selection:choice.selection,reference:{recordId:'saved-source',revision:'b'.repeat(64),caseId:'saved-case'},matchingPageCount:1}]};
 const run=E.run,verify=E.verify;E.run=E.verify=()=>assert.fail('Navigation must not execute a target');
 try{
  const valid=await Context.checkNavigationHints(hints,context,webcrypto);assert.deepEqual(valid,hints);assert(Object.isFrozen(valid.choices[0].reference));assert.notEqual(valid,hints);
  const mutations=[h=>h.extra=true,h=>h.schema='other',h=>h.parentTaskHash='0'.repeat(64),h=>h.inputVersion='reviewed',h=>h.catalogGeneration='invalid',h=>h.choices.push(structuredClone(h.choices[0])),h=>h.choices[0].matchingPageCount=0,h=>h.choices[0].matchingPageCount=task.pages.length+1,h=>h.choices[0].reference.recordId='../escape',h=>h.choices[0].reference.revision='x',h=>h.choices[0].reference.caseId='javascript:alert(1)',h=>h.choices[0].selection.parameter='invented',h=>h.choices[0].extra=true];
  for(const mutate of mutations){const bad=structuredClone(hints);mutate(bad);assert.equal(await Context.checkNavigationHints(bad,context,webcrypto),null);}
  let hooks=0;const bad=structuredClone(hints);Object.defineProperty(bad,'choices',{enumerable:true,get(){hooks++;return [];}});assert.equal(await Context.checkNavigationHints(bad,context,webcrypto),null);assert.equal(hooks,0);
  const input=structuredClone(hints),pending=Context.checkNavigationHints(input,context,webcrypto);input.choices[0].reference.recordId='mutated';assert.equal((await pending).choices[0].reference.recordId,'saved-source');
  assert.equal(await Context.checkNavigationHints(null,context,webcrypto),null);assert.equal(await Context.checkNavigationHints(hints,{...context,inputVersion:'reviewed'},webcrypto),null);
  console.log('PASS archived navigation hints: exact parent and eligible selections, detached immutable pointers, safe references, malformed optional metadata ignored; no execution.');
 }finally{E.run=run;E.verify=verify;}
})().catch(error=>{console.error(error);process.exitCode=1;});
