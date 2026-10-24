/* Exercise the production Worker with exact cards; no hosted inference. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHandler} from './worker.mjs';
import C from '../../claim-specification.js';
import R from '../../claim-research.js';
import Search from '../../assistant-search.js';
const known=value=>C.field('specified',value),origin='https://jelliottdev.github.io';
const registry=JSON.parse(readFileSync(new URL('../../data/experiments.json',import.meta.url),'utf8'));
const docs=Search.experimentDocs(registry.records);
function card({pages=['lp2-15','lp2-17','lp2-31'],key='Fibonacci',original='Use a numeric stream on the selected pages.',rules={}}={}){
 return R.prepare(C.confirm(C.createDraft({source:{text:original},aim:known('Find readable text'),
  method:known({operations:[{id:'numeric_stream',label:'Numeric stream',generator:key}]}),
  scope:known({pages,description:'Only the first two visible rows; no joins across pages'}),rules}),{id:'fixture',at:'2026-10-24T12:00:00Z'})).request;
}
const post=data=>new Request('https://fixture.workers.dev/ask',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(data)});
let calls=0,seen=[];
const env={SITE_ORIGIN:origin,IDEA_LIMIT:{limit:async()=>({success:true})},AI:{run:async(_model,options)=>{
 calls++;seen.push(JSON.parse(options.messages[1].content));return {choices:[{message:{content:'The cited test has limited inputs [1].'}}]};
}}};
const handle=createHandler(async()=>docs),request=card();
const expected=R.validate(request),binding=await R.binding(request);
let response=await handle(post(request),env),data=await response.json();
assert.equal(response.status,200);assert.equal(data.claimBinding,binding);
assert.deepEqual(expected.pages,['lp2-15','lp2-17','lp2-31']);
assert.deepEqual(data.sources.map(s=>s.id),Search.select(docs,expected.query,expected.pages).map(s=>s.id));
assert.equal(data.sources[0].id,'fibonacci-stream-skip-grid');
assert.equal(seen[0].idea,expected.confirmedQuery);
assert(seen[0].idea.includes('Only the first two visible rows'));
assert(seen[0].idea.includes('"reset":{"status":"unspecified"}'));
assert(seen[0].idea.includes('Fibonacci'));
for(const source of data.sources)assert.equal(source.text,docs.find(d=>d.id===source.id).text);
response=await handle(post(request),env);data=await response.json();
assert.equal(data.cached,true);assert.equal(data.claimBinding,binding);assert.equal(calls,1);
for(const amended of [card({key:'prime'}),card({rules:{reset:known('Restart within each word')}}),card({original:'Different original wording; same standardized steps.'})]){
 const result=await (await handle(post(amended),env)).json();
 assert.equal(result.claimBinding,await R.binding(amended));assert.notEqual(result.claimBinding,binding);assert(!result.cached);
}
assert.equal(calls,4,'Exact changed parameters, rules and original wording invalidate cached context');
const allPages=[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))];
const all=card({pages:allPages});assert.equal((await handle(post(all),env)).status,200);assert.equal(R.validate(all).pages.length,75);
const empty=createHandler(async()=>[]),beforeEmpty=calls;
data=await (await empty(post(request),env)).json();assert.equal(data.reason,'no-matching-records');assert.equal(data.claimBinding,binding);assert.equal(calls,beforeEmpty);
const beforeBad=calls;
for(const bad of [{...request,query:'OutGuess'},{...request,pages:['lp2-01']},{...request,confirmedQuery:'invented scope'},{...request,version:2},{...request,card:{...request.card,version:2}}])assert.equal((await handle(post(bad),env)).status,400);
assert.equal(calls,beforeBad,'Invalid cards fail before inference');
const denied=await handle(post(request),{...env,IDEA_LIMIT:{limit:async()=>({success:false})}});assert.equal(denied.status,429);assert.equal((await denied.json()).claimBinding,binding);
for(const boundary of [null,'within_words','word_blocks','fixed_spaces']){
 const snapshot=C.confirm(C.createDraft({source:{text:'A confirmed row reversal with explicit boundaries.'},aim:known('Find readable text'),
  method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'},
   ...(boundary==='fixed_spaces'?[{id:'described_method',label:'Apply Vigenere with key ABC',key:'ABC'}]:[])]}),
  scope:known({pages:['lp2-15','lp2-17']}),rules:boundary?{wordBoundaries:known('preserve'),boundaryMode:known(boundary)}:{}}),{id:'operand-'+boundary,at:'2026-10-24T12:00:00Z'});
 const prepared=R.prepare(snapshot),before=calls,result=await (await handle(post(prepared.request),env)).json();
 assert.equal(result.claimBinding,await R.binding(prepared.request));
 if(boundary===null){
  assert.equal(result.kind,'recorded-overlap');assert.equal(calls,before,'Reviewed operation overlap requires no model call');
  assert.deepEqual(result.sources.map(s=>s.id).sort(),['lp2-row-column-english','lp2-row-column-routes']);
 }else{
  assert.notEqual(result.kind,'recorded-overlap');
  assert.deepEqual(result.sources.map(s=>s.id),Search.select(docs,prepared.query,prepared.pages,prepared.discovery).map(s=>s.id));
  assert.equal(seen.at(-1).idea,prepared.confirmedQuery,'Model sees the exact confirmed combination, not discovery hints as execution evidence');
 }
 assert(result.sources.some(s=>s.id===(boundary==='within_words'?'lp2-word-reversal':boundary==='word_blocks'?'lp2-word-order-reversal':'lp2-row-column-routes')));
 for(const source of result.sources)assert.equal(source.text,docs.find(d=>d.id===source.id).text);
 const spoofed=await handle(post({...prepared.request,discovery:{steps:[{query:'OutGuess'}]}}),env);
 assert.equal(spoofed.status,400,'A visitor cannot override server-derived method hints');
}
console.log('PASS exact-card Worker: derived retrieval/context, complete page sets and passage, parameters and unknowns, content-bound cache/no-match, rejected overrides, unchanged quotas. All model calls mocked.');
