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
await test('missing keys, malformed or explicit unsupported values never become choice prompts',()=>{
 const candidates=[{id:'repeating_key'},{id:'repeating_key',key:[]},{id:'repeating_key',key:[29]},{id:'repeating_key',key,direction:'beaufort'},{id:'repeating_key',key,reset:null},{id:'repeating_key',key,direction:undefined},{id:'repeating_key',key,unit:'line'},{id:'repeating_key',key,interrupts:[0]},{id:'repeating_key',key,label:'Repeating key except when an F rune occurs'},{id:'plaintext_autokey',key},{id:'vigenere',key},{id:'finite_key',key}];
 for(const operation of candidates){let result;try{result=planCard(card(operation));}catch{continue;}assert(result.reason);assert.notEqual(result.state,'needs-clarification');assert(!Object.hasOwn(result,'clarification'));}
});
await test('compounds and conflicting or unsupported global rules retain legacy rejection',()=>{
 for(const rules of [{reset:C.field('not_applicable')},{reset:known('line')},{boundaryMode:known('within_words')},{initialState:known(0)},{searchBounds:known({keyLength:4})},{reset:C.field('unrestricted')}]){const input=card(undefined,rules),before=structuredClone(input),result=planCard(input);assert(result.reason);assert.notEqual(result.state,'needs-clarification');assert.deepEqual(input,before);}
 const input=card();input.method.value.operations.push({id:'reverse_runes',unit:'line'});const result=planCard(input);assert(result.reason);assert.notEqual(result.state,'needs-clarification');
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
await test('old clients and invalid or conflicting methods retain adapter rejection',async()=>{
 for(const [input,opt] of [[card(),{}],[card({id:'repeating_key',key,direction:'beaufort'}),{includeMethodClarification:true}],[card({id:'repeating_key',key,reset:'line'},{reset:known('word')}),{includeMethodClarification:true}]]){
  const f=handlerFixture(input),{status,value}=await f.submit(opt);assert.equal(status,200);assert.equal(value.state,'needs-adapter');assert.equal(typeof value.reason,'string');assert(!Object.hasOwn(value,'clarification'));f.assertUnchanged(1);f.sqlite.close();
 }
});
await test('new request flag is strictly optional true; malformed contracts cannot reach preparation',async()=>{
 const f=handlerFixture(card());for(const extra of [{includeMethodClarification:false},{includeMethodClarification:1},{includeMethodClarification:'true'},{includeMethodClarification:true,extra:1}])assert.equal((await f.submit(extra)).status,400);f.assertUnchanged();f.sqlite.close();
});
console.log(groups+' keyed clarification compiler and handler groups passed');
