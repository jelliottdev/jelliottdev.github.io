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
const typed={...record,record_type:{id:'control',label:'Control',description:'Synthetic recovery control; no unsolved-page decoding.'}};
const typedDocs=Search.experimentDocs([typed]);
assert.deepEqual(JSON.parse(typedDocs[0].text).record_type,typed.record_type);
const typedHandler=createHandler(async()=>typedDocs);
let captured;
await typedHandler(request(),{...env,AI:{run:async(model,options)=>{
 captured=options.messages;
 return {choices:[{message:{content:'This is a synthetic control [1].'}}]};
}}});
assert(captured[0].content.includes('Use each record_type'));
assert(captured[0].content.includes('If record_type is absent'));
const supplied=JSON.parse(captured[1].content).records;
assert.deepEqual(JSON.parse(supplied[0].text).record_type,typed.record_type);
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
 ['trigrams on LP2-31','lp2-trigram-repeats'],
 ['OutGuess on LP2-31',['outguess-default-key','outguess-guard-sweep']],
 ['Have we tried checking if its a different language than English?','parallel-languages'],
]){
 const response=await realHandler(request(query),realEnv);
 assert.equal(response.status,200);
 const first=(await response.json()).sources[0].id;
 assert((Array.isArray(expected)?expected:[expected]).includes(first));
}
assert.equal(realCalls,6);
assert.equal((await (await realHandler(request('has anyone tried LP2-31'),realEnv)).json()).reason,'no-matching-records');
assert.equal(realCalls,6);
console.log('PASS: current published experiments retain complete scope through the hosted handler; page-only queries still skip inference. Model binding mocked.');
