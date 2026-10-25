import {createHash} from 'node:crypto';
/* All provider calls are mocks. Exact grammar, coverage and resource limits. */
import assert from 'node:assert/strict';
import {createAIPlanner,validateCandidate,MODEL,JSON_SCHEMA,PROMPT,LIMITS} from './propose-task-plan.mjs';
import {planCard,createPrepareTaskHandler} from './prepare-task.mjs';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
function card(text,extra={}){return H.cardData(C.confirm(C.createDraft({source:{text:'PRIVATE HUMAN ORIGINAL'},aim:known('solve LP2'),method:known({operations:[{id:'described_method',label:text}]}),scope:known({pages:['lp2-15']}),...extra}),{id:'test',at:'2026-10-24T12:00:00.000Z'}));}
const candidate=(text,quotes,steps)=>({version:1,steps:quotes.map((quote,i)=>({source:{operationIndex:0,start:text.indexOf(quote),quote},step:steps[i]})),unsupported:[]});
const value=v=>({choices:[{message:{content:typeof v==='string'?v:JSON.stringify(v)}}]});
// Keep provider lifecycle tests on a connector-prefixed label, outside the
// deterministic complete-label path while retaining exact source coverage.
const providerCard=(text,extra)=>card('please '+text,extra);
const defer=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
function clock(){let time=0,id=0;const timers=new Map();return {now:()=>time,schedule:(fn,ms)=>{timers.set(++id,{fn,at:time+ms});return id;},unschedule:key=>timers.delete(key),advance(ms){time+=ms;for(const [key,t]of timers)if(t.at<=time){timers.delete(key);t.fn();}}};}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
await test('simple described line, word and affine methods now compile with exact preserved context',async()=>{
 for(const [text,step]of [['reverse each line',{op:'reverse',unit:'line'}],['reverse each word',{op:'reverse',unit:'word'}],['reverse rune order within each page',{op:'reverse',unit:'page'}],['apply affine a=7,b=7',{op:'affine',a:7,b:7}],['cumulative difference reset at each page',{op:'cumulative-difference',reset:'page'}]]){
  const original=card(text),before=structuredClone(original),out=validateCandidate(original,candidate(text,[text],[step]),{compile:planCard});assert(!out.reason,out.reason);assert.deepEqual(out.steps,[step]);assert.deepEqual(original,before);assert.deepEqual(out.card.scope,original.scope);assert.deepEqual(out.card.outcome,original.outcome);
  for(const key of C.RULES.filter(k=>k!=='boundaryMode'))assert.deepEqual(out.card.rules[key],original.rules[key]);assert(out.notes.some(n=>n.includes(text)));assert(out.notes.every(n=>!n.includes('{')&&!n.includes('\"op\"')));assert(out.plan.notes.some(n=>n.includes('preliminary measurement')));
 }
});
await test('fully explicit keyed phrases use closed source grammar without inferred key or reset',async()=>{
 for(const [name,mode]of [['Vigenere','repeat'],['repeating key','repeat'],['plaintext autokey','plaintext-autokey'],['ciphertext-autokey','ciphertext-autokey']]){
  const text=name+' with key indices [1, 0, 28], subtract, reset at each page',step={op:'keyed-shift',key:[1,0,28],mode,direction:'subtract',reset:'page'},input=card(text),before=structuredClone(input),out=validateCandidate(input,candidate(text,[text],[step]),{compile:planCard});assert(!out.reason,out.reason);assert.deepEqual(out.steps,[step]);assert.deepEqual(out.plan.steps,[step]);assert.deepEqual(input,before);assert.deepEqual(out.card.scope,input.scope);assert.deepEqual(out.card.rules,input.rules);assert.deepEqual(out.card.outcome,input.outcome);assert(out.notes.some(n=>n.includes('GP indices [1,0,28]')));
  const wrong=candidate(text,[text],[{...step,key:[1,0,27]}]);assert(validateCandidate(input,wrong,{compile:planCard}).reason);
 }
 const text='Use Vigenere with key indices [1,2,3], add, reset at each word',step={op:'keyed-shift',key:[1,2,3],mode:'repeat',direction:'add',reset:'word'};assert(!validateCandidate(card(text),candidate(text,[text],[step]),{compile:planCard}).reason);
 const phrase='Vigenere with key indices [1,2,3], subtract, reset at each page',repeat={op:'keyed-shift',key:[1,2,3],mode:'repeat',direction:'subtract',reset:'page'};
 const using='using '+phrase+'.';assert(!validateCandidate(card(using),candidate(using,[using],[repeat]),{compile:planCard}).reason);
 for(const conditional of ['Do not '+using,using+' except F',using+' unless the row ends'])assert(validateCandidate(card(conditional),candidate(conditional,[using],[repeat]),{compile:planCard}).reason);
 for(const text of [phrase+' except F','Do not '+phrase,phrase+' then skip one rune',phrase+' carrying state between pages','Use key "'+phrase+'"','Vigenere with key ABC, subtract, reset at each page','Vigenere with key indices [1,2,3], reset at each page','Vigenere with key indices [1,2,3], subtract','Vigenere with key indices [29], subtract, reset at each page','Vigenere with key indices [1,,2], subtract, reset at each page']){
  const quote=text.includes(phrase)?phrase:text;assert(validateCandidate(card(text),candidate(text,[quote],[repeat]),{compile:planCard}).reason,text);
 }
 assert(validateCandidate(card(phrase,{rules:{reset:known('word')}}),candidate(phrase,[phrase],[repeat]),{compile:planCard}).reason);
 const fabricated=card(phrase);fabricated.method.value.operations[0]={id:'vigenere',label:phrase,key:[1,2,3],direction:'subtract',reset:'page'};assert(validateCandidate(fabricated,candidate(phrase,[phrase],[repeat]),{compile:planCard}).reason,'Canonical keyed labels cannot hide extra prose or be repaired through AI');
 const explicit=card(phrase);explicit.method.value.operations[0]={id:'plaintext_autokey',label:phrase,key:[1,2,3],direction:'subtract',reset:'page'};assert(validateCandidate(explicit,candidate(phrase,[phrase],[repeat]),{compile:planCard}).reason,'Explicit autokey cannot become repeat');
});
await test('ordered compounds preserve every operation; exact parameters cannot be invented',async()=>{
 const text='Please reverse each line, then apply affine a=7,b=7.',out=validateCandidate(card(text),candidate(text,['reverse each line','apply affine a=7,b=7'],[{op:'reverse',unit:'line'},{op:'affine',a:7,b:7}]),{compile:planCard});assert(!out.reason,out.reason);assert.deepEqual(out.plan.steps,[{op:'reverse',unit:'line'},{op:'affine',a:7,b:7}]);
 const malformed=candidate(text,['reverse each line','apply affine a=7,b=7'],[{op:'reverse',unit:'line'},{op:'affine',a:8,b:7}]);assert(validateCandidate(card(text),malformed,{compile:planCard}).reason);
});
await test('complete supported labels map deterministically with all source and compiler guards',async()=>{
 const text='using Vigenere with key indices [23,10,1,10,9,10,16,26], subtract, reset at each page.',step={op:'keyed-shift',key:[23,10,1,10,9,10,16,26],mode:'repeat',direction:'subtract',reset:'page'};
 const input=card(text,{aim:known('Reproduce the Welcome opening'),scope:known({pages:['lp1-03']}),rules:{reset:known('reset at each page')}});input.method.value.operations[0].declaredFamilyId='polyalphabetic';const before=structuredClone(input);let calls=0;
 for(const AI of [undefined,{run:async()=>{calls++;throw Error('Must not call provider');}}]){
  const out=await createAIPlanner({compile:planCard,AI})(input);assert(!out.reason,out.reason);assert.deepEqual(out.plan.steps,[step]);assert.deepEqual(out.card.scope,input.scope);assert.deepEqual(out.card.outcome,input.outcome);assert.deepEqual(out.card.rules,input.rules);assert(out.notes.some(note=>note.includes('Proposed interpretation')));
 }
 assert.equal(calls,0);assert.deepEqual(input,before);
 const planner=createAIPlanner({compile:planCard});
 for(const label of [text+' except F','Do not '+text,text+' then skip one rune'])assert((await planner(card(label))).reason);
 assert((await planner(card(text,{rules:{reset:known('word')}}))).reason);
 assert((await createAIPlanner({compile:()=>({reason:'compiler refusal'})})(input)).reason.includes('compiler refusal'));
});
await test('unsupported-empty cannot conceal negation, keys, conditions, omissions or quoted instructions',async()=>{
 const cases=['Do not reverse each line','reverse each line except the heading','reverse each line if F occurs','reverse each line then use key ABC','Use key "reverse each line"','reverse each line without changing spaces only on odd rows'];
 for(const text of cases){const out=validateCandidate(card(text),candidate(text,['reverse each line'],[{op:'reverse',unit:'line'}]),{compile:planCard});assert(out.reason,text);}
 const text='reverse each line then apply affine a=7,b=7',c=candidate(text,['reverse each line','apply affine a=7,b=7'],[{op:'reverse',unit:'line'},{op:'affine',a:7,b:7}]);
 const reverse=structuredClone(c);reverse.steps.reverse();assert(validateCandidate(card(text),reverse,{compile:planCard}).reason);
 const index=structuredClone(c);index.steps[0].source.start=1;assert(validateCandidate(card(text),index,{compile:planCard}).reason);
 const extra=structuredClone(c);extra.scope=['lp2-55'];assert(validateCandidate(card(text),extra,{compile:planCard}).reason);
 const unknown=structuredClone(c);unknown.steps[1].step={op:'eval',code:'anything'};assert(validateCandidate(card(text),unknown,{compile:planCard}).reason);
 assert(validateCandidate(card(text),c).reason);
});
await test('scope, evaluation and explicit rule conflicts remain exact',async()=>{
 const text='reverse each line',c=candidate(text,[text],[{op:'reverse',unit:'line'}]);
 for(const extra of [{scope:known({pages:['lp2-15'],description:'Only line 3'})},{scope:C.field()},{rules:{evaluation:known('English readable')}},{rules:{exceptionalCases:known('Except F')}},{rules:{boundaryMode:known('within_words')}},{unresolved:[{kind:'unknown',text:'Conditional skip'}]}])assert(validateCandidate(card(text,extra),c,{compile:planCard}).reason);
 const prefix=card(text,{rules:{evaluation:known({kind:'exact-prefix',values:[1,2,3]}),inputVersion:known('reviewed')}}),out=validateCandidate(prefix,c,{compile:planCard});assert(!out.reason);assert.deepEqual(out.plan.criterion,{kind:'exact-prefix',values:[1,2,3]});assert.equal(out.plan.inputVersion,'reviewed');
 const textMixed='reverse each line then reverse each word',mixed=validateCandidate(card(textMixed),candidate(textMixed,['reverse each line','reverse each word'],[{op:'reverse',unit:'line'},{op:'reverse',unit:'word'}]),{compile:planCard});assert(!mixed.reason,mixed.reason);assert.deepEqual(mixed.plan.steps,[{op:'reverse',unit:'line'},{op:'reverse',unit:'word'}]);
});
await test('one model call uses strict schema and validated success cache cannot be mutated by caller',async()=>{
 const text='please reverse each word',c=candidate(text,['reverse each word'],[{op:'reverse',unit:'word'}]);let calls=0;
 const propose=createAIPlanner({compile:planCard,AI:{run:async(model,body)=>{calls++;assert.equal(model,MODEL);assert.deepEqual(body.response_format.json_schema.schema,JSON_SCHEMA);assert.equal(body.temperature,0);assert(!body.messages[1].content.includes('PRIVATE HUMAN'));assert(body.messages[0].content===PROMPT);return value(c);}}});
 const first=await propose(card(text));assert(!first.reason);first.notes.push('MUTATED');first.card.scope.value.pages.push('lp2-55');
 const second=await propose(card(text));assert.equal(calls,1);assert(!second.notes.includes('MUTATED'));assert.deepEqual(second.card.scope.value.pages,['lp2-15']);
});
await test('missing exact scope and unresolved conditions cannot spend a model call',async()=>{
 let calls=0;const propose=createAIPlanner({compile:planCard,AI:{run:async()=>{calls++;throw Error();}}});
 assert((await propose(card('reverse each line',{scope:C.field()}))).reason);
 assert((await propose(card('reverse each line',{unresolved:[{kind:'unknown',text:'Needs a key'}]}))).reason);assert.equal(calls,0);
});
await test('unrestricted rules fail before provider while irrelevant inapplicable fields survive',async()=>{
 let calls=0;const text='please cumulative difference reset at each page',step={op:'cumulative-difference',reset:'page'},mapping=candidate(text,['cumulative difference reset at each page'],[step]),propose=createAIPlanner({compile:planCard,AI:{run:async()=>{calls++;return value(mapping);}}});
 for(const key of C.RULES){const input=card(text,{rules:{[key]:C.field('unrestricted')}}),before=structuredClone(input);assert((await propose(input)).reason,key);assert(validateCandidate(input,mapping,{compile:planCard}).reason);assert.deepEqual(input,before);}assert.equal(calls,0,'No provider call is made for any explicitly unrestricted rule');
 for(const key of ['reset','initialState'])assert(validateCandidate(card(text,{rules:{[key]:C.field('not_applicable')}}),mapping,{compile:planCard}).reason);
 const keyedText='Vigenere with key indices [1], subtract, reset at each page',keyed={op:'keyed-shift',key:[1],mode:'repeat',direction:'subtract',reset:'page'};assert(validateCandidate(card(keyedText,{rules:{reset:C.field('not_applicable')}}),candidate(keyedText,[keyedText],[keyed]),{compile:planCard}).reason);
 const input=card(text,{rules:{exceptionalCases:C.field('not_applicable'),searchBounds:C.field('not_applicable')}}),before=structuredClone(input),out=await propose(input);assert(!out.reason,out.reason);assert.equal(calls,1);assert.deepEqual(input,before);assert.deepEqual(out.card.rules,input.rules);assert.equal(out.plan.inputVersion,'raw');assert.deepEqual(out.plan.criterion,{kind:'measurement'});
});
await test('provider malformed/unsupported responses fail without repair or retry',async()=>{
 for(const response of [value('not JSON'),value(' '.repeat(16001)),value({version:1,steps:[],unsupported:[]}),value({version:1,steps:[],unsupported:['Vigenere']})]){
  let calls=0;const propose=createAIPlanner({compile:planCard,AI:{run:async()=>{calls++;return response;}}});assert((await propose(providerCard('reverse each line'))).reason);assert.equal(calls,1);
 }
 let calls=0;const rejected=createAIPlanner({compile:planCard,AI:{run:async()=>{calls++;throw Error('Provider unavailable');}}});assert((await rejected(providerCard('reverse each line'))).reason);assert.equal(calls,1);
});
await test('timeouts retain concurrent slots until actual settlement; same-card joins never retry',async()=>{
 const timers=clock(),jobs=[];let calls=0;
 const propose=createAIPlanner({...timers,compile:planCard,AI:{run:()=>{calls++;const job=defer();jobs.push(job);return job.promise;}}});
 const cards=['reverse each line','reverse each word','apply affine a=7,b=7'].map(t=>providerCard(t));
 const a=propose(cards[0]),same=propose(cards[0]),b=propose(cards[1]),c=propose(cards[2]);await tick();assert.equal(calls,3);
 assert((await propose(providerCard('apply affine a=8,b=7'))).reason.includes('busy'));
 timers.advance(LIMITS.timeoutMs);assert((await a).reason.includes('timed out'));assert((await same).reason.includes('timed out'));await b;await c;
 assert((await propose(cards[0])).reason.includes('timed out'));assert.equal(calls,3);assert((await propose(providerCard('apply affine a=8,b=7'))).reason.includes('busy'));
 jobs[0].resolve(value(candidate('please reverse each line',['reverse each line'],[{op:'reverse',unit:'line'}])));await tick();
 const next=propose(providerCard('apply affine a=8,b=7'));await tick();assert.equal(calls,4);jobs[3].reject(Error());await next;
 jobs[1].reject(Error());jobs[2].reject(Error());await tick();
});
await test('actual prepare route maps once, preserves stored hypothesis and fetches only official pages after validation',async()=>{
 async function fixture(input,mapping,withAI=true){
  const sqlite=new DatabaseSync(':memory:');for(const file of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql','0008_prepared_plans.sql','0009_word_boundary_preparations.sql','0010_family_case_results.sql','0011_task_protocol_lookup.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+file,import.meta.url),'utf8'));
  const stored=C.serialize(input),cardHash=createHash('sha256').update(stored).digest('hex'),id='p_'+cardHash;sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,cardHash,stored,'unused','2026-10-24');
  let calls=0,fetches=0;const env={SITE_ORIGIN:'https://jelliottdev.github.io',TASK_LIMIT:{limit:async()=>({success:true})},PROPOSALS:{prepare(sql){assert(!sql.includes('original_idea'));assert(/^\s*(?:SELECT\b|INSERT INTO (?:prepared_plans|idea_computation_evidence)\b)/.test(sql));return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};}},AI:{run:async()=>{calls++;return value(mapping);}}};
  if(!withAI)delete env.AI;
  const page=input.scope.value?.pages?.[0]||'lp2-15';
  const handle=createPrepareTaskHandler({fetcher:async(url,options)=>{fetches++;assert.equal(url,'https://jelliottdev.github.io/data/pages/'+page+'.json');assert.equal(options.redirect,'manual');return Response.json({id:page,raw:'ᚠᚢ',reviewed_text:'ᚠᚢᚦ'});}});
  const request=new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin:env.SITE_ORIGIN,'content-type':'application/json'},body:JSON.stringify({proposalId:id,parentTaskId:null})});
  const response=await handle(request,env),result=await response.json();assert.equal(response.status,200);assert.equal(sqlite.prepare('SELECT card_json FROM proposals').get().card_json,stored);assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);const preparation=sqlite.prepare('SELECT basis_json FROM prepared_plans').get();sqlite.close();return {result,calls,fetches,preparation:preparation?JSON.parse(preparation.basis_json):null};
 }
 const text='reverse each line, then apply affine a=7,b=7',mapping=candidate(text,['reverse each line','apply affine a=7,b=7'],[{op:'reverse',unit:'line'},{op:'affine',a:7,b:7}]);
 const success=await fixture(card(text,{rules:{inputVersion:known('reviewed'),evaluation:known({kind:'exact-prefix',values:[0,1]})}}),mapping);
 assert.equal(success.preparation.kind,'mapped-card');assert.deepEqual(success.preparation.mapping,mapping);assert.deepEqual(success.preparation.normalizedCard.method.value.operations.map(o=>o.id),['reverse_runes','affine']);assert.equal(success.calls,1);assert.equal(success.fetches,1);assert.equal(success.result.state,'plan-ready');assert.match(success.result.preparation.id,/^prep_[a-f0-9]{64}$/);assert.deepEqual(success.result.task.steps,[{op:'reverse',unit:'line'},{op:'affine',a:7,b:7}]);assert.deepEqual(success.result.task.criterion,{kind:'exact-prefix',values:[0,1]});assert.equal(success.result.task.pages[0].text,'ᚠᚢᚦ');assert(success.result.notes.some(n=>n.includes('Map each rune index')));assert(success.result.notes.every(n=>!n.includes('{')));
 const unsupportedText='reverse each line except the heading',unsupported=await fixture(card(unsupportedText),candidate(unsupportedText,['reverse each line'],[{op:'reverse',unit:'line'}]));assert.equal(unsupported.result.state,'needs-adapter');assert.equal(unsupported.calls,1);assert.equal(unsupported.fetches,0);
 const noScope=await fixture(card('reverse each line',{scope:C.field()}),candidate('reverse each line',['reverse each line'],[{op:'reverse',unit:'line'}]));assert.equal(noScope.result.state,'needs-adapter');assert.equal(noScope.calls,0);assert.equal(noScope.fetches,0);
 const keyed='using Vigenere with key indices [23,10,1,10,9,10,16,26], subtract, reset at each page.',liveCard=card(keyed,{aim:known('Reproduce the Welcome opening'),scope:known({pages:['lp1-03']}),rules:{reset:known('reset at each page')}});liveCard.method.value.operations[0].declaredFamilyId='polyalphabetic';
 const direct=await fixture(liveCard,null,false);assert.equal(direct.result.state,'plan-ready');assert.equal(direct.calls,0);assert.equal(direct.fetches,1);assert.deepEqual(direct.result.task.steps,[{op:'keyed-shift',key:[23,10,1,10,9,10,16,26],mode:'repeat',direction:'subtract',reset:'page'}]);
 const unsupportedOffline=await fixture(card(keyed+' except F'),null,false);assert.equal(unsupportedOffline.result.state,'needs-adapter');assert.equal(unsupportedOffline.calls,0);assert.equal(unsupportedOffline.fetches,0);
});
await test('bounded exact-card cache expires and evicts without category conflation',async()=>{
 const timers=clock();let calls=0;
 const propose=createAIPlanner({...timers,compile:planCard,AI:{run:async(_,body)=>{calls++;const c=JSON.parse(body.messages[1].content).card,text=c.method.value.operations[0].label;return value(candidate(text,['apply affine a=7,b=7'],[{op:'affine',a:7,b:7}]));}}});
 const cards=Array.from({length:51},(_,i)=>providerCard('apply affine a=7,b=7',{aim:known({outcomeId:'measure',detail:'Exact objective '+i,wording:'Exact objective '+i})}));
 for(const c of cards)assert(!(await propose(c)).reason);assert.equal(calls,51);await propose(cards[0]);assert.equal(calls,52);timers.advance(LIMITS.cacheMs+1);await propose(cards[0]);assert.equal(calls,53);
});
console.log('PASS '+groups+' source-bound AI planner groups; mocked provider only, no hosted calls or code execution.');
