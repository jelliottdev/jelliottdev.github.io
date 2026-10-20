import assert from 'node:assert/strict';
import {createHandler, citationNumbers} from './worker.mjs';
import Search from '../../assistant-search.js';
const origin='https://jelliottdev.github.io';
const record={id:'fixture',status:'published',title:'Reverse primes',question:'Reverse a row?',summary:'Fixture',tags:['reverse'],scope:{pages:['lp2-15'],representation:'raw runes',procedure:'reverse values',parameters:'one row',exclusions:'other rows'},outcome:'inconclusive',finding:'One row only',limitations:'Other rows were not tested',article:'Fixture'};
let docs=Search.experimentDocs([record]),calls=0;
const env={SITE_ORIGIN:origin,IDEA_LIMIT:{limit:async()=>({success:true})},AI:{run:async()=>{calls++;return {choices:[{message:{content:'One row only [1].'}}]};}}};
const request=(query='reverse',pages=[],headers={})=>new Request('https://fixture.workers.dev/ask',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json',...headers},body:JSON.stringify({query,pages})});
const handle=createHandler(async()=>docs);
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
