/* Explicit user decisions stay separate from immutable public-card identity. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{createHash,webcrypto}=require('node:crypto'),C=require('../claim-specification.js'),H=require('../claim-share.js'),E=require('../local-experiment.js'),K=require('../keyed-method-clarification.js');
const at='2026-10-25T12:00:00.000Z',known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']}),key=[23,18,3,4],clone=v=>JSON.parse(JSON.stringify(v)),hash=v=>createHash('sha256').update(C.serialize(v)).digest('hex');
function card(op={id:'repeating_key',label:'Repeating key',key},rules={}){return H.cardData(C.confirm(C.createDraft({source:{text:'Use an explicit repeating key.'},aim:known('solve LP2'),method:known({operations:[op]}),scope:known({pages:['lp2-15']}),rules:{evaluation:known({kind:'exact-prefix',values:[24,7,24]}),...rules}}),{id:'fixture',at}));}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 const {planCard}=await import('../services/idea-assistant/prepare-task.mjs');
 const response=input=>{const p=planCard(input);return {state:p.state,proposalId:'p_'+hash(input),field:p.field,reason:p.reason,clarification:p.clarification};};
 await test('real backend choice binds exact original card; nothing is confirmed or saved by the helper',async()=>{
  const input=card(),reply=response(input),before=clone(input),s=await K.verify(input,reply);assert.equal(K.inspect(s),s);assert.equal(s.proposalId,reply.proposalId);assert.deepEqual(s.card,input);assert.equal(s.question.parameter,'direction');assert.equal(s.draft.status,'draft');assert.equal(s.draft.execution,'not_run');assert.equal(s.draft.confirmation,null);assert.deepEqual(s.choices,[]);assert.deepEqual(input,before);assert(Object.isFrozen(s.card.method.value.operations[0].key));assert.throws(()=>K.inspect(clone(s)));assert.throws(()=>{s.question.choices[0].value='guess';},TypeError);
 });
 await test('every explicit combination equals direct canonical input and task after separate user confirmation',async()=>{
  const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')),pages=[{id:'lp2-15',text:bundle.pages.find(p=>p.id==='lp2-15').raw}];
  for(const direction of ['subtract','add'])for(const reset of ['page','line','word']){
   const original=card(),a=await K.verify(original,response(original)),b=K.choose(a,direction),done=K.choose(b,reset);assert.equal(a.question.parameter,'direction');assert.equal(b.question.parameter,'reset');assert.equal(done.question,null);assert.equal(done.draft.status,'draft');assert.equal(done.draft.confirmation,null);assert.deepEqual(done.card,original);assert.equal(done.proposalId,a.proposalId);assert.deepEqual(done.draft.aim,a.draft.aim);assert.deepEqual(done.draft.scope,a.draft.scope);assert.deepEqual(done.draft.rules,a.draft.rules);
   assert.equal(done.draft.method.provenance.kind,'user_clarification');for(const parameter of ['direction','reset'])assert(done.draft.method.provenance.refs.includes('keyed-operation-v1:'+parameter));assert.deepEqual(done.draft.clarifications.map(c=>c.choice),[direction,reset]);assert.deepEqual(done.choices.map(x=>x.parameter),['direction','reset']);assert(!Object.hasOwn(done.choices[0].before,'direction'));assert.equal(done.choices[0].after.direction,direction);assert(!Object.hasOwn(done.choices[1].before,'reset'));assert.equal(done.choices[1].after.reset,reset);assert(Object.isFrozen(done.choices[1].before));
   const confirmed=C.confirm(done.draft,{id:'explicit-review-confirmation',at}),canonical=H.cardData(confirmed),direct=card({id:'repeating_key',label:'Repeating key',key,direction,reset});assert.equal(C.serialize(canonical),C.serialize(direct));assert.notEqual(hash(canonical),hash(original));const p=planCard(canonical),d=planCard(direct),prepare=value=>E.prepare({title:'Same literal key program',pages,alphabet:bundle.alphabet,steps:value.steps,criterion:value.criterion});assert.deepEqual(await prepare(p),await prepare(d));
   const shared=H.decode(H.encode(confirmed)).draft;assert.equal(shared.method.provenance.kind,'project_context');assert.deepEqual(shared.clarifications,[],'Shared canonical cards intentionally do not preserve the local choice audit');assert.throws(()=>K.choose(done,'page'));assert.deepEqual(original,done.card);
  }
 });
 await test('stale responses, fabricated choices, unknown fields and already supplied settings are rejected',async()=>{
  const input=card(),valid=response(input),other=card({id:'repeating_key',key:[1,2,3]});
  for(const change of [v=>v.proposalId='p_'+'0'.repeat(64),v=>v.clarification.parameter='key',v=>v.clarification.choices.push({id:'guess',value:'guess',label:'Guess'}),v=>v.clarification.choices[0].value='guess',v=>v.clarification.operationIndex=1,v=>v.clarification.version=2,v=>v.task={},v=>v.field='evaluation']){const bad=clone(valid);change(bad);await assert.rejects(()=>K.verify(input,bad));}
  await assert.rejects(()=>K.verify(other,valid));await assert.rejects(()=>K.verify(card({id:'repeating_key',key,direction:'add'}),valid));const s=await K.verify(input,valid);for(const value of ['ADD','guess',undefined,{},'page'])assert.throws(()=>K.choose(s,value));assert.throws(()=>K.choose(clone(s),'add'));
 });
 await test('supplied constraints and unsupported methods cannot be smuggled in with a forged typed response',async()=>{
  const valid=response(card()),inputs=[card({id:'repeating_key',key,reset:'line'},{reset:known('word')}),card({id:'repeating_key',key,direction:'beaufort'}),card({id:'plaintext_autokey',key}),card({id:'repeating_key'}),card(undefined,{searchBounds:known({max:100})}),card(undefined,{evaluation:known({kind:'readability'})}),card(undefined,{reset:C.field('not_applicable')})];
  for(const input of inputs){const forged={...clone(valid),proposalId:'p_'+hash(input)};await assert.rejects(()=>K.verify(input,forged));}
  const compatible=card({id:'repeating_key',key,reset:'line'},{reset:known('reset at each line')}),s=await K.verify(compatible,response(compatible));assert.equal(s.question.parameter,'direction');assert.equal(K.choose(s,'add').question,null);
 });
 await test('asynchronous verification captures original bytes and browser UMD uses the same closed semantics',async()=>{
  const input=card(),reply=response(input),promise=K.verify(input,reply);input.method.value.operations[0].key[0]=0;reply.clarification.choices[0].value='guess';const s=await promise;assert.equal(s.card.method.value.operations[0].key[0],23);assert.equal(s.question.choices[0].value,'subtract');
  const context={crypto:webcrypto,TextEncoder,TextDecoder,btoa,atob};vm.createContext(context);for(const file of ['claim-specification.js','claim-share.js','experiment-protocols.js','output-evaluators.js','keyed-method-clarification.js'])vm.runInContext(fs.readFileSync(file,'utf8'),context);const b=await context.KeyedMethodClarification.verify(card(),response(card()));assert.equal(context.KeyedMethodClarification.choose(b,'add').question.parameter,'reset');
 });
 console.log(groups+' keyed method clarification groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
