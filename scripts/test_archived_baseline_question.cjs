'use strict';
/* Genuine zero-step archived checks over invented text; no target execution. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),F=require('../fixed-plan-compiler.js'),Q=require('../task-parameter-question.js'),V=require('../task-parameter-variants.js'),J=require('../finite-json.js');
const alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet,copy=structuredClone,known=value=>C.field('specified',value);
const operation={id:'as_written',label:'Keep the original rune order'},prefix={kind:'exact-prefix',values:[0,1]},set={kind:'exact-prefix-set',openings:[{id:'invented',values:[0,1]},{id:'another',values:[3,2]}]};
async function task(criterion=prefix){return E.prepare({title:'Invented archived unchanged input',pages:[{id:'lp2-00',text:'ᚠᚢ ᚦ\nᚩ-ᚱ'},{id:'lp2-01',text:'ᚱᚩ ᚦ-ᚢ\nᚠ'}],alphabet,steps:[],criterion},webcrypto);}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
const run=E.run;E.run=()=>assert.fail('Canonical baseline must not execute a target');
try{
await test('raw and reviewed literal checks roundtrip through explicit confirmation and share without fake steps',async()=>{
 for(const inputVersion of ['raw','reviewed'])for(const criterion of [prefix,set]){
  const parent=await task(criterion),original=E.stable(parent),archived=await Q.archived({task:parent,inputVersion},webcrypto);
  assert.deepEqual(archived.card.method.value.operations,[operation]);assert.equal(archived.card.outcome.value.outcomeId,'decipher');
  const text=Buffer.from(E.stable(archived.card)).toString('base64url'),imported=H.decode('#idea='+text);
  const confirmed=C.confirm(imported.draft,{id:'explicit-baseline-review',at:'2026-10-27T00:00:00.000Z'}),card=H.cardData(confirmed),compiled=F.compile(card);
  assert.deepEqual(card,archived.card);assert(!compiled.reason&&!compiled.state);assert.deepEqual(compiled.steps,[]);
  assert.deepEqual(compiled.pages,parent.pages.map(page=>page.id));assert.deepEqual(compiled.criterion,parent.criterion);assert.equal(compiled.inputVersion,inputVersion);
  assert.equal(E.stable(parent),original);assert.deepEqual(V.list(parent),[]);assert.deepEqual(V.suggestions(parent),[]);
  assert(F.methodReadiness(card.method).supported);assert(H.sections(card).some(row=>row[1]==='Keep the original rune order'));
 }
});
await test('standalone baseline rejects compounds labels arbitrary parameters and hidden method tails',async()=>{
 const {card}=await Q.archived({task:await task(),inputVersion:'raw'});
 for(const operations of [[{...operation,key:[0]}],[{...operation,a:1}],[{...operation,reset:'page'}],[{...operation,label:'Drop filler runes'}],[{id:'as_written'}],[operation,{id:'affine',label:'Affine substitution',a:1,b:0}],[operation,operation]]){
  const changed=copy(card);changed.method.value.operations=operations;assert(F.compile(changed).reason);assert(!F.methodReadiness(changed.method).supported);
 }
 const changed=copy(card);changed.method.value.extra='except selected runes';assert(F.compile(changed).reason);
});
await test('explicit preserved input and literal criteria cannot be widened to inferred transformations or readability',async()=>{
 const {card}=await Q.archived({task:await task(),inputVersion:'raw'});
 for(const name of ['inputVersion','representation','unmapped','wordBoundaries','evaluation']){
  const changed=copy(card);changed.rules[name]=C.field();const result=F.compile(changed);assert(result.reason||result.state,name);
 }
 for(const [name,value]of [['inputVersion','guess'],['representation','prime-values'],['unmapped','drop'],['wordBoundaries','ignore'],['reset','page'],['boundaryMode','fixed_spaces'],['initialState',0],['exceptionalCases','Skip F'],['searchBounds','all'],['searchProtocol','guess'],['evaluation','measurement'],['evaluation',{kind:'readability'}],['evaluation',{kind:'exact-prefix',values:[]}],['evaluation',C.EVALUATION_CHOICES.find(row=>row.id==='language-samples').value]]){
  const changed=copy(card);changed.rules[name]=known(value);const result=F.compile(changed);assert(result.reason||result.state,name);
 }
 const changed=copy(card);changed.unresolved.push({kind:'source_note',text:'Except F'});assert(F.compile(changed).reason);
});
await test('archived baseline still requires authentic task identity complete GP29 and literal evaluation',async()=>{
 const parent=await task(),bad=copy(parent);bad.pages[0].text+='ᚠ';await assert.rejects(Q.archived({task:bad,inputVersion:'raw'}));
 const other=await E.prepare({...parent,criterion:{kind:'measurement'}});await assert.rejects(Q.archived({task:other,inputVersion:'raw'}),/literal/);
 const alphabetDrift=copy(parent);alphabetDrift.alphabet[0].latin='CHANGED';alphabetDrift.taskId=await E.identity(alphabetDrift,webcrypto);await assert.rejects(Q.archived({task:alphabetDrift,inputVersion:'raw'}),/canonical/);
 const changing={task:copy(parent),inputVersion:'raw'};let release,reached;const gate=new Promise(r=>release=r),started=new Promise(r=>reached=r),crypto={subtle:{async digest(...args){reached();await gate;return webcrypto.subtle.digest(...args);}}};
 const pending=Q.archived(changing,crypto);await started;changing.task.pages[0].text+='ᚠ';release();await assert.rejects(pending,/changed/);
});
await test('neutral family classification does not block an exact selected original-question context',async()=>{
 const Context=require('../task-question-context.js'),parent=await task(set),archived=await Q.archived({task:parent,inputVersion:'raw'}),card=archived.card;
 const family=C.classifyMethod(card.method);assert.deepEqual(family.familyIds,[]);assert.equal(family.complete,false);
 const projection={id:parent.taskId,plan:parent,proposalId:archived.proposalId,card,inputVersion:'raw',parentTaskId:null,linkedProposalId:archived.proposalId,linkedInputVersion:'raw',linkedParentTaskId:null};
 const ids=[...Array.from({length:17},(_,n)=>'lp1-'+String(n).padStart(2,'0')),...Array.from({length:58},(_,n)=>'lp2-'+String(n).padStart(2,'0'))],bundle={schema:'liberpedia-local-inputs-v1',alphabet,pages:ids.map(id=>{const text=parent.pages.find(page=>page.id===id)?.text||'';return {id,raw:text,reviewed_text:text};})};
 const selected=Context.inspect(await Context.verify({taskId:parent.taskId,proposalId:archived.proposalId,projection,bundle},webcrypto));
 assert.equal(selected.comparable,true);assert.deepEqual(selected.card,card);assert.deepEqual(selected.declaredPages,parent.pages.map(page=>page.id));
});
await test('browser shared modules preserve the identical zero-step canonical question',async()=>{
 const context=vm.createContext({LocalExperiment:E,FiniteJSON:J,TaskParameterVariants:V,ExperimentProtocols:require('../experiment-protocols.js'),OutputEvaluators:require('../output-evaluators.js'),TextEncoder,TextDecoder,crypto:webcrypto,btoa,atob});
 for(const name of ['claim-specification.js','claim-share.js','fixed-plan-compiler.js','task-parameter-question.js'])vm.runInContext(fs.readFileSync(name,'utf8'),context);const parent=await task(set),input={task:parent,inputVersion:'raw'};
 assert.equal(E.stable(await context.TaskParameterQuestion.archived(input,webcrypto)),E.stable(await Q.archived(input,webcrypto)));
});
}finally{E.run=run;}
console.log(groups+' archived unchanged-input baseline groups passed; no target execution or fabricated identity steps.');
})().catch(error=>{console.error(error);process.exitCode=1;});
