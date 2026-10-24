import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHandler, createRecordLoader, citationNumbers} from './worker.mjs';
import Search from '../../assistant-search.js';
const origin='https://jelliottdev.github.io';
const record={id:'fixture',status:'published',title:'Reverse primes',question:'Reverse a row?',summary:'Fixture',tags:['reverse'],scope:{pages:['lp2-15'],representation:'raw runes',procedure:'reverse values',parameters:'one row',exclusions:'other rows'},outcome:'inconclusive',finding:'One row only',limitations:'Other rows were not tested',article:'Fixture'};
let docs=Search.experimentDocs([record]),calls=0;
const env={SITE_ORIGIN:origin,IDEA_LIMIT:{limit:async()=>({success:true})},AI:{run:async()=>{calls++;return {choices:[{message:{content:'One row only [1].'}}]};}}};
const request=(query='reverse',pages=[],headers={})=>new Request('https://fixture.workers.dev/ask',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json',...headers},body:JSON.stringify({query,pages})});
const handle=createHandler(async()=>docs);
// Complete evidence carries editorial type, but the type is not a new experiment.
const typed={...record,record_type:{id:'method',label:'Bounded solving test',description:'A specified rule on unsolved material.'}};
const typedDocs=Search.experimentDocs([typed]);
assert.deepEqual(JSON.parse(typedDocs[0].text).record_type,typed.record_type);
const typedHandler=createHandler(async()=>typedDocs);
let captured;
const typedResponse=await typedHandler(request(),{...env,AI:{run:async(model,options)=>{
 captured=options.messages;
 return {choices:[{message:{content:'This is a bounded test [1].'}}]};
}}});
assert(captured[0].content.includes('bounded solving tests'));
assert(captured[0].content.includes('source audit'));
for(const principle of ['user’s aim','ordered compound methods','reusing saved output','not wildcards','Do not invent a variation'])assert(captured[0].content.includes(principle));
const supplied=JSON.parse(captured[1].content).records;
assert.deepEqual(JSON.parse(supplied[0].text).record_type,typed.record_type);
assert.equal((await typedResponse.json()).sources[0].recordType,'method',
  'The Worker passes editorial type to the browser alongside complete evidence');
assert.equal((await (await createHandler(async()=>[])(request(),env)).json()).reason,'no-matching-records');
assert.equal((await (await handle(request('Vigenere on page 31'),env)).json()).reason,'no-matching-records');assert.equal(calls,0);
for(const query of ['has anyone tried LP2–15','has anyone tested page #15','has anyone tested pages #15–#16']){
 assert.equal((await (await handle(request(query),env)).json()).reason,'no-matching-records');
 assert.equal(calls,0,'Page punctuation must not trigger inference');
}
let r=await handle(request(),env);assert.equal(r.status,200);assert.equal((await r.json()).sources[0].id,'fixture');assert.equal(calls,1);
r=await handle(request('  reverse  '),env);assert.equal((await r.json()).cached,true);assert.equal(calls,1);
// Exact content changes invalidate answers, including changed limits.
docs=Search.experimentDocs([{...record,limitations:'Only two rows'}]);await handle(request(),env);assert.equal(calls,2);
assert.equal((await handle(request('reverse',[],{Origin:'https://other.example'}),env)).status,403);
assert.equal((await handle(request('x'.repeat(1501)),env)).status,400);
assert.equal((await handle(request('reverse',['lp2-99']),env)).status,400);
assert.equal((await handle(request('reverse',['lp2-01','lp2-02','lp2-03']),env)).status,400);
assert.equal((await handle(request(),{...env,IDEA_LIMIT:{limit:async()=>({success:false})}})).status,429);
const broken=createHandler(async()=>docs);let failures=0;
const failed={...env,AI:{run:async()=>{failures++;throw Error('quota');}}};
assert.equal((await broken(request(),failed)).status,503);assert.equal((await broken(request(),failed)).status,503);assert.equal(failures,1);
const invalid=createHandler(async()=>docs);
r=await invalid(request(),{...env,AI:{run:async()=>({choices:[{message:{content:'Made up [9].'}}]})}});assert.equal((await r.json()).reason,'unverified-answer');
// Concurrent equal requests share one inference in this isolate.
let concurrent=0;const shared=createHandler(async()=>docs);
await Promise.all([1,2,3].map(()=>shared(request(),{...env,AI:{run:async()=>{concurrent++;await new Promise(r=>setTimeout(r,15));return {choices:[{message:{content:'One test [1].'}}]};}}})));assert.equal(concurrent,1);
assert.deepEqual(citationNumbers('Invalid [0].',2),[]);
assert.equal((await handle(new Request('https://fixture.workers.dev/ask',{method:'OPTIONS',headers:{Origin:origin}}),env)).status,204);
console.log('PASS: technique gate, cache reuse/invalidation, duplicate suppression, validation, CORS, rate limit and outage cooldown. All inference mocked.');

// Registry freshness and optional-page failures are tested without a network request.
let clock=0, registryFetches=0, contextFetches=0;
let registryRecords=[record];
const loader=createRecordLoader(async url=>{
 if(url.endsWith('/experiments.json')){
  registryFetches++;
  await Promise.resolve();
  return Response.json({records:registryRecords});
 }
 contextFetches++;
 throw Error('Supporting page index unavailable');
},()=>clock);
const loaded=await Promise.all([loader(),loader(),loader()]);
assert.equal(registryFetches,1,'Concurrent cold loads share the same registry fetch');
assert.equal(contextFetches,1);
assert(loaded.every(d=>d.length===1&&d[0].kind==='experiment'));
await loader();assert.equal(registryFetches,1,'Fresh evidence is cached');
clock=300001;registryRecords=[{...record,finding:'Newly published finding'}];
const refreshed=await loader();
assert.equal(registryFetches,2);
assert(refreshed[0].text.includes('Newly published finding'));
for(const response of [()=>Response.json({documents:{invalid:true}}),()=>new Response('not JSON'),()=>new Response('',{status:503})]){
 const optional=createRecordLoader(async url=>url.endsWith('/experiments.json')?Response.json({records:[record]}):response());
 assert.equal((await optional())[0].kind,'experiment');
}
let failedFetches=0;
const recovery=createRecordLoader(async url=>{
 if(url.endsWith('/experiments.json')){
  failedFetches++;
  if(failedFetches===1)throw Error('Registry unavailable');
  return Response.json({records:[]});
 }
 throw Error('An empty registry should not request supporting context');
});
await assert.rejects(recovery);
assert.deepEqual(await recovery(),[],'A failed load does not poison later retries');
assert.equal(failedFetches,2);
console.log('PASS: five-minute evidence refresh, shared cold loads, optional-context failure and registry retry. All fetches mocked.');

const published=JSON.parse(readFileSync(new URL('../../data/experiments.json',import.meta.url),'utf8')).records;
const realDocs=Search.experimentDocs(published);
let realCalls=0;
const realHandler=createHandler(async()=>realDocs);
const realEnv={...env,AI:{run:async(model,options)=>{
 realCalls++;
 const evidence=JSON.parse(options.messages[1].content).records;
 assert(evidence.length>=1&&evidence.length<=2);
 for(const source of evidence){
  assert.equal(source.kind,'experiment');
  assert.equal(source.text,realDocs.find(d=>d.id===source.id).text,'Full evidence reaches the model unchanged');
 }
 return {choices:[{message:{content:'Mock comparison of the recorded scope [1].'}}]};
}}};
for(const [query,expected] of [
 ['Fibonacci on LP2-31','lp2-fibonacci-openings'],
 ['reverse words on LP2-31','lp2-word-reversal'],
 ['reverse word order on LP2-31','lp2-word-order-reversal'],
 ['OutGuess on LP2-31','outguess-keyed-lp2'],
 ['keyed OutGuess on LP2-31','outguess-keyed-lp2'],
 ['OutGuess without a key','outguess-default-key'],
]){
 const response=await realHandler(request(query),realEnv);
 assert.equal(response.status,200);
 const first=(await response.json()).sources[0].id;
 assert((Array.isArray(expected)?expected:[expected]).includes(first), `${query}: unexpected leading source ${first}`);
}
assert.equal(realCalls,6);
for(const query of ['dead tree on LP2-55']){
 assert.equal((await (await realHandler(request(query),realEnv)).json()).reason,'no-matching-records',query);
}
for(const [query,expected] of [['trigrams on LP2-31','lp2-trigram-repeats'],
 ['different language than English','parallel-languages'],
 ['lag six within words c prime = 24 minus 2c mod 29','word-internal-affine-lags']]){
 const response=await (await realHandler(request(query),realEnv)).json();
 assert.equal(response.sources[0].id,expected,query);
}
assert.equal((await (await realHandler(request('has anyone tried LP2-31'),realEnv)).json()).reason,'no-matching-records');
assert.equal(realCalls,9);
console.log('PASS: current published experiments retain complete scope through the hosted handler; page-only queries still skip inference. Model binding mocked.');

// Confirmed interpretation is model context, never a bag of retrieval keywords.
// An unrelated phrase repeated in the context must not displace the explicitly
// requested Fibonacci method. The original (non-confirmation) API still works.
const confirmedRequest=(query,confirmedQuery,pages=[])=>new Request('https://fixture.workers.dev/ask',{
 method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},
 body:JSON.stringify({query,pages,...(confirmedQuery===undefined?{}:{confirmedQuery})})
});
let contextCalls=0,contextMessages=[];
const contextHandler=createHandler(async()=>realDocs);
const contextEnv={...env,AI:{run:async(model,options)=>{
 contextCalls++;contextMessages.push(JSON.parse(options.messages[1].content));
 return {choices:[{message:{content:'Mock fixed-scope comparison [1].'}}]};
}}};
const compact='Fibonacci on LP2-31';
const complete='Confirmed interpretation; not an executed experiment.\n'+
 'Rules: preserve the exact phase and page selection.\n'+
 'Original wording retained separately: '+('OutGuess reverse words '.repeat(50)).trimEnd();
const expectedSelection=Search.select(realDocs,compact,[]).map(d=>d.id);
let contextResponse=await contextHandler(confirmedRequest(compact,complete),contextEnv);
assert.equal(contextResponse.status,200);
assert.deepEqual((await contextResponse.json()).sources.map(d=>d.id),expectedSelection);
assert.equal(contextMessages[0].idea,complete,'The complete confirmed wording reaches inference unchanged');
assert.equal(contextMessages[0].records[0].id,'lp2-fibonacci-openings');
for(const evidence of contextMessages[0].records){
 assert.equal(evidence.text,realDocs.find(d=>d.id===evidence.id).text);
}
contextResponse=await contextHandler(confirmedRequest(compact,complete),contextEnv);
assert.equal((await contextResponse.json()).cached,true);
assert.equal(contextCalls,1,'An identical confirmation reuses the same answer');
const amended=complete+'\nChanged rule: restart the key at each word.';
contextResponse=await contextHandler(confirmedRequest(compact,amended),contextEnv);
assert.equal(contextResponse.status,200);await contextResponse.json();
assert.equal(contextCalls,2,'Changed confirmed rules must invalidate an otherwise identical cache key');
assert.equal(contextMessages[1].idea,amended);
assert.deepEqual(contextMessages[1].records.map(d=>d.id),expectedSelection);
contextResponse=await contextHandler(confirmedRequest(compact,undefined),contextEnv);
assert.equal(contextResponse.status,200);await contextResponse.json();
assert.equal(contextCalls,3,'The legacy request does not inherit a different confirmed context');
assert.equal(contextMessages[2].idea,compact);
// Context alone, including method names and pages, cannot trigger inference.
const beforePageOnly=contextCalls;
const pageOnly=await contextHandler(confirmedRequest('has anyone tried LP2-31',complete),contextEnv);
assert.equal((await pageOnly.json()).reason,'no-matching-records');
assert.equal(contextCalls,beforePageOnly);

// Both independent limits apply before retrieval/inference. Exercise UTF-8,
// because 6,000 permitted characters need more than the former 6,500-byte body.
const boundaryContext='漢'.repeat(6000);
contextResponse=await contextHandler(confirmedRequest(compact,boundaryContext),contextEnv);
assert.equal(contextResponse.status,200);await contextResponse.json();
assert.equal(contextMessages.at(-1).idea,boundaryContext);
const beforeInvalid=contextCalls;
for(const bad of ['x'.repeat(6001),'', '   ',null,42,{method:'reverse'}]){
 assert.equal((await contextHandler(confirmedRequest(compact,bad),contextEnv)).status,400,
  'An invalid confirmed context must be rejected before inference');
}
assert.equal((await contextHandler(confirmedRequest('x'.repeat(1501),complete),contextEnv)).status,400,
 'The optional context does not increase the retrieval-query limit');
const oversizedBody=new Request('https://fixture.workers.dev/ask',{
 method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},
 body:JSON.stringify({query:compact,confirmedQuery:'valid',padding:'x'.repeat(32001)})
});
assert.equal((await contextHandler(oversizedBody,contextEnv)).status,400,'The raw request body remains bounded');
assert.equal(contextCalls,beforeInvalid);
console.log('PASS: confirmed context reaches inference without affecting ranking; independent limits, UTF-8 body and confirmation-bound caches. All inference mocked.');
