import assert from 'node:assert/strict';
import {createHandler, citationNumbers} from './worker.mjs';

const origin='https://jelliottdev.github.io';
const record={id:'fixture',status:'published',title:'Reverse primes',question:'Reverse a row?',summary:'Fixture',tags:['reverse'],
  scope:{pages:['lp2-15'],representation:'raw runes',procedure:'reverse values',parameters:'one row',exclusions:'other rows'},
  outcome:'inconclusive',finding:'One row only',limitations:'Other rows were not tested',article:'Fixture'};
let calls=0;
const env={SITE_ORIGIN:origin,IDEA_LIMIT:{limit:async()=>({success:true})},
  AI:{run:async()=>{calls++;return {choices:[{message:{content:'This record tested one row only [1].'}}]};}}};
const request=(query='reverse',headers={})=>new Request('https://fixture.workers.dev/ask',{
  method:'POST',headers:{Origin:origin,'Content-Type':'application/json',...headers},body:JSON.stringify({query})});

let response=await createHandler(async()=>[])(request(),env);
assert.equal((await response.json()).reason,'no-matching-records');assert.equal(calls,0);
response=await createHandler(async()=>[{...record,status:'draft'}])(request(),env);
assert.equal((await response.json()).reason,'no-matching-records');assert.equal(calls,0);
const handle=createHandler(async()=>[record]);
response=await handle(request('unrelatedword'),env);
assert.equal((await response.json()).reason,'no-matching-records');assert.equal(calls,0);
response=await handle(request(),env);const answer=await response.json();
assert.equal(response.status,200);assert.equal(answer.sources[0].id,'fixture');assert.equal(calls,1);
assert.equal(response.headers.get('Access-Control-Allow-Origin'),origin);
assert.equal((await handle(request('reverse',{Origin:'https://other.example'}),env)).status,403);
assert.equal((await handle(request('x'.repeat(1501)),env)).status,400);
assert.equal((await handle(request(),{...env,IDEA_LIMIT:{limit:async()=>({success:false})}})).status,429);
assert.equal((await handle(request(),{...env,AI:{run:async()=>{throw Error('quota');}}})).status,503);
response=await handle(request(),{...env,AI:{run:async()=>({choices:[{message:{content:'Made up citation [9].'}}]})}});
assert.equal((await response.json()).reason,'unverified-answer');
assert.deepEqual(citationNumbers('Uncited claim',3),[]);
assert.deepEqual(citationNumbers('Valid [1], [2].',2),[1,2]);
assert.deepEqual(citationNumbers('Invalid [0].',2),[]);
response=await handle(new Request('https://fixture.workers.dev/ask',{method:'OPTIONS',headers:{Origin:origin}}),env);
assert.equal(response.status,204);
console.log('PASS: server retrieval, no inference for empty/draft/unmatched records, CORS, limits, quota fallback, citations. Hosted inference mocked.');
