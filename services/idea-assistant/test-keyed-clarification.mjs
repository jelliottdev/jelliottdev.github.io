/* Compiler-only clarification of one supported literal repeating-key method. */
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import {createHash} from 'node:crypto';
import {planCard,createPrepareTaskHandler} from './prepare-task.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
const at='2026-10-25T12:00:00.000Z',known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']}),key=[23,18,3,4],reason='A keyed step needs explicit GP indices (0–28), add or subtract, and a page, line or word reset.';
function card(operation={id:'repeating_key',label:'Repeating key',key},rules={}){return H.cardData(C.confirm(C.createDraft({source:{text:'Try this explicit DEOR index key; ask me which arithmetic and restart rule to use.'},aim:known('solve LP2'),method:known({operations:[operation]}),scope:known({pages:['lp2-15']}),rules:{evaluation:known({kind:'exact-prefix',values:[24,7,24]}),...rules}}),{id:'test',at}));}
function answer(input,value){const next=structuredClone(input),question=planCard(input);assert.equal(question.state,'needs-clarification');assert(question.clarification.choices.some(choice=>choice.value===value));next.method.value.operations[question.clarification.operationIndex][question.clarification.parameter]=value;return next;}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('missing choices are typed, explicit and ordered; no key or setting is invented',()=>{
 const input=card(),before=structuredClone(input),first=planCard(input);assert.equal(first.reason,reason);assert.deepEqual(first,{state:'needs-clarification',field:'method',reason,clarification:{version:1,kind:'keyed-operation',operationIndex:0,operationId:'repeating_key',parameter:'direction',choices:[{id:'subtract',value:'subtract',label:'Subtract key indices'},{id:'add',value:'add',label:'Add key indices'}]}});assert.deepEqual(input,before);assert(!Object.hasOwn(first,'task'));assert(!Object.hasOwn(first,'steps'));
 const second=planCard(answer(input,'subtract'));assert.equal(second.clarification.parameter,'reset');assert.deepEqual(second.clarification.choices.map(x=>x.value),['page','line','word']);assert.deepEqual(input,before);
});
await test('all six supplied choices yield the exact canonical card and task of direct explicit input',async()=>{
 const bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),pages=[{id:'lp2-15',text:bundle.pages.find(p=>p.id==='lp2-15').raw}];
 for(const direction of ['subtract','add'])for(const reset of ['page','line','word']){
  const input=card(),resolved=answer(answer(input,direction),reset),explicit=card({id:'repeating_key',label:'Repeating key',key,direction,reset}),plan=planCard(resolved),direct=planCard(explicit);
  assert(!plan.reason);assert.deepEqual(plan,direct);assert.equal(C.serialize(resolved),C.serialize(explicit));assert.deepEqual(resolved.outcome,input.outcome);assert.deepEqual(resolved.scope,input.scope);assert.deepEqual(resolved.rules,input.rules);assert.deepEqual(resolved.method.value.operations[0].key,key);
  const prepare=p=>E.prepare({title:'Literal repeating-key check',pages,alphabet:bundle.alphabet,steps:p.steps,criterion:p.criterion});assert.deepEqual(await prepare(plan),await prepare(direct));
 }
});
await test('one supplied parameter is retained and only the absent parameter is requested',()=>{
 let input=card({id:'repeating_key',key,direction:'add'});assert.equal(planCard(input).clarification.parameter,'reset');assert.equal(answer(input,'line').method.value.operations[0].direction,'add');
 input=card({id:'repeating_key',key,reset:'word'});assert.equal(planCard(input).clarification.parameter,'direction');assert.equal(answer(input,'subtract').method.value.operations[0].reset,'word');
 input=card({id:'repeating_key',key,reset:'line'},{reset:known('reset at each line')});assert.equal(planCard(input).clarification.parameter,'direction');assert(!planCard(answer(input,'add')).reason,'An agreeing explicit global reset must not block the missing arithmetic choice');
});
await test('one indexed incomplete repeating key is clarified only when its entire ordered compound compiles',async()=>{
 const bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),text=bundle.alphabet.slice(0,7).map(r=>r.rune).join('')+'- /\n'+bundle.alphabet.slice(7,10).map(r=>r.rune).join(''),pages=[{id:'lp2-15',text}];
 for(const index of [0,1,2])for(const direction of ['subtract','add'])for(const reset of ['page','line','word']){
  const input=card(),operations=[{id:'reverse_runes',unit:'line'},{id:'affine',a:7,b:4}];operations.splice(index,0,{id:'repeating_key',label:'Repeating key',key});input.method.value.operations=operations;const original=structuredClone(input),first=planCard(input);assert.equal(first.state,'needs-clarification');assert.equal(first.clarification.operationIndex,index);assert.equal(first.clarification.parameter,'direction');assert(!Object.hasOwn(first,'steps'));
  const afterDirection=answer(input,direction);assert.equal(planCard(afterDirection).clarification.operationIndex,index);assert.equal(planCard(afterDirection).clarification.parameter,'reset');assert(!Object.hasOwn(afterDirection.method.value.operations[index],'reset'),'A validation-only probe must never supply a proposed reset');
  const resolved=answer(afterDirection,reset),direct=structuredClone(input);direct.method.value.operations[index].direction=direction;direct.method.value.operations[index].reset=reset;assert.equal(C.serialize(resolved),C.serialize(direct));assert.deepEqual(input,original);const actual=planCard(resolved),expected=planCard(direct);assert.deepEqual(actual,expected);const task=await E.prepare({title:'Indexed compound',pages,alphabet:bundle.alphabet,steps:actual.steps,criterion:actual.criterion}),result=E.run(task);assert.deepEqual(await E.verify(task,result),result);assert.deepEqual(actual.steps.map(s=>s.op),operations.map(op=>({reverse_runes:'reverse',affine:'affine',repeating_key:'keyed-shift'}[op.id])));
 }
 const scoped=card();scoped.method.value.operations=[{id:'reverse_runes',unit:'word'},{id:'repeating_key',key},{id:'cumulative_difference',reset:'page'}];scoped.rules.boundaryMode={status:'specified',value:'within_words'};scoped.rules.initialState={status:'specified',value:0};assert.equal(planCard(scoped).clarification.operationIndex,1);assert(!planCard(answer(answer(scoped,'subtract'),'line')).reason,'Supported companion-only rules are retained, not attributed to the key');
});
await test('ambiguous missing targets, unsupported companion steps and other incomplete keyed modes produce no invented choice',()=>{
 const variants=[
  [{id:'repeating_key',key},{id:'repeating_key',key:[1,2]}],
  [{id:'repeating_key',key},{id:'reverse_runes'}],
  [{id:'repeating_key',key},{id:'plaintext_autokey',key:[1,2]}],
  [{id:'repeating_key',key},{id:'finite_key',key:[1,2]}],
  [{id:'reverse_runes',unit:'line'},{id:'plaintext_autokey',key}],
  [{id:'reverse_runes',unit:'line'},{id:'finite_key',key}],
  [{id:'reverse_runes',unit:'line'},{id:'repeating_key',key,direction:'beaufort'}],
  [{id:'repeating_key',key},...Array.from({length:8},()=>({id:'affine',a:1,b:0}))]
 ];
 for(const operations of variants){const input=card();input.method.value.operations=operations;const before=structuredClone(input),result=planCard(input);assert(result.reason);assert.notEqual(result.state,'needs-clarification');assert(!Object.hasOwn(result,'clarification'));assert.deepEqual(input,before);}
});
await test('fully specified autokey and finite-stream companions retain their own exact settings',async()=>{
 const bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),pages=[{id:'lp2-15',text:bundle.alphabet.slice(0,6).map(r=>r.rune).join('')}];
 for(const id of ['plaintext_autokey','ciphertext_autokey','finite_key']){
  const companion={id,key:[1,2,3,4,5,6],direction:'add',reset:'page'},input=card();input.method.value.operations=[companion,...input.method.value.operations];const before=structuredClone(input),prompt=planCard(input);assert.equal(prompt.clarification.operationIndex,1);
  const resolved=answer(answer(input,'subtract'),'word'),plan=planCard(resolved);assert(!plan.reason);assert.deepEqual(resolved.method.value.operations[0],companion);assert.deepEqual(input,before);const task=await E.prepare({title:'Explicit keyed companion',pages,alphabet:bundle.alphabet,steps:plan.steps,criterion:plan.criterion});assert.deepEqual(await E.verify(task,E.run(task)),E.run(task));
 }
});
await test('missing keys, malformed or explicit unsupported values never become choice prompts',()=>{
 const candidates=[{id:'repeating_key'},{id:'repeating_key',key:[]},{id:'repeating_key',key:[29]},{id:'repeating_key',key,direction:'beaufort'},{id:'repeating_key',key,reset:null},{id:'repeating_key',key,direction:undefined},{id:'repeating_key',key,unit:'line'},{id:'repeating_key',key,interrupts:[0]},{id:'repeating_key',key,label:'Repeating key except when an F rune occurs'},{id:'plaintext_autokey',key},{id:'vigenere',key},{id:'finite_key',key}];
 for(const operation of candidates){let result;try{result=planCard(card(operation));}catch{continue;}assert(result.reason);assert.notEqual(result.state,'needs-clarification');assert(!Object.hasOwn(result,'clarification'));}
});
await test('conflicting global rules and unsupported companion steps retain legacy rejection',()=>{
 for(const rules of [{reset:C.field('not_applicable')},{reset:known('line')},{boundaryMode:known('within_words')},{initialState:known(0)},{searchBounds:known({keyLength:4})},{reset:C.field('unrestricted')}]){const input=card(undefined,rules),before=structuredClone(input),result=planCard(input);assert(result.reason);assert.notEqual(result.state,'needs-clarification');assert.deepEqual(input,before);}
 const input=card();input.method.value.operations.push({id:'unknown_method',label:'Unspecified companion cipher'});const result=planCard(input);assert(result.reason);assert.notEqual(result.state,'needs-clarification');
});
function handlerFixture(input){
 const sqlite=new DatabaseSync(':memory:');for(const file of readdirSync(new URL('./migrations/',import.meta.url)).filter(file=>/^\d{4}_.*\.sql$/.test(file)).sort())sqlite.exec(readFileSync(new URL('./migrations/'+file,import.meta.url),'utf8'));
 const hash=createHash('sha256').update(C.serialize(input)).digest('hex'),proposalId='p_'+hash;sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,hash,C.serialize(input),'unused',at);
 let ai=0,fetches=0,writes=0;const env={SITE_ORIGIN:'https://jelliottdev.github.io',PROPOSALS:{prepare(sql){return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>{writes++;return sqlite.prepare(sql).run(...args);}};}};}},TASK_LIMIT:{limit:async()=>({success:true})},AI:{run(){ai++;throw Error('No AI call is needed for a typed choice');}}};
 const handler=createPrepareTaskHandler({fetcher(){fetches++;throw Error('Clarification must not load manuscript inputs');}});
 return {sqlite,proposalId,async submit(extra={},override){const response=await handler(new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin:env.SITE_ORIGIN,'content-type':'application/json'},body:JSON.stringify(override||{proposalId,parentTaskId:null,...extra})}),env);return {status:response.status,value:await response.json()};},assertUnchanged(expectedAI=0){assert.equal(ai,expectedAI);assert.equal(fetches,0);assert.equal(writes,0);for(const table of ['local_tasks','local_task_results','prepared_plans','idea_computation_evidence'])assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM '+table).get().n,0);assert.equal(sqlite.prepare('SELECT card_json FROM proposals WHERE id=?').get(proposalId).card_json,C.serialize(input));}};
}
await test('opted-in handler returns only the missing supported choice before AI, source fetch or writes',async()=>{
 for(const operation of [{id:'repeating_key',key},{id:'repeating_key',key,direction:'add'},{id:'repeating_key',key,reset:'line'}]){
  const input=card(operation),f=handlerFixture(input),expected=planCard(input),result=await f.submit({includeMethodClarification:true});assert.equal(result.status,200);assert.deepEqual(result.value,{state:'needs-clarification',proposalId:f.proposalId,field:'method',reason:expected.reason,clarification:expected.clarification});assert(!['task','controls','preparation'].some(k=>Object.hasOwn(result.value,k)));f.assertUnchanged();f.sqlite.close();
 }
});
await test('opted-in compound handler binds its exact step index before any AI, source or storage work',async()=>{
 const input=card();input.method.value.operations=[{id:'reverse_runes',unit:'line'},...input.method.value.operations,{id:'affine',a:7,b:4}];const fixture=handlerFixture(input);try{const result=await fixture.submit({includeMethodClarification:true});assert.equal(result.status,200);assert.equal(result.value.state,'needs-clarification');assert.equal(result.value.clarification.operationIndex,1);assert.equal(result.value.clarification.parameter,'direction');fixture.assertUnchanged();}finally{fixture.sqlite.close();}
});
await test('old clients and invalid or conflicting methods retain adapter rejection',async()=>{
 for(const [input,opt] of [[card(),{}],[card({id:'repeating_key',key,direction:'beaufort'}),{includeMethodClarification:true}],[card({id:'repeating_key',key,reset:'line'},{reset:known('word')}),{includeMethodClarification:true}]]){
  const f=handlerFixture(input),{status,value}=await f.submit(opt);assert.equal(status,200);assert.equal(value.state,'needs-adapter');assert.equal(typeof value.reason,'string');assert(!Object.hasOwn(value,'clarification'));f.assertUnchanged(1);f.sqlite.close();
 }
});
await test('new request flag is strictly optional true; malformed contracts cannot reach preparation',async()=>{
 const f=handlerFixture(card());for(const extra of [{includeMethodClarification:false},{includeMethodClarification:1},{includeMethodClarification:'true'},{includeMethodClarification:true,extra:1}])assert.equal((await f.submit(extra)).status,400);f.assertUnchanged();f.sqlite.close();
});
console.log(groups+' keyed clarification compiler and handler groups passed');
