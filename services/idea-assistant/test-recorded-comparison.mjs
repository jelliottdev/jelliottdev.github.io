/* Actual authored row-record metadata; all fetches, limits and inference mocked. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHandler,createRecordLoader} from './worker.mjs';
import C from '../../claim-specification.js';
import Research from '../../claim-research.js';
import Recorded from '../../recorded-comparison.js';
import Search from '../../assistant-search.js';
import Markdown from '../../assistant-markdown.js';

const origin='https://jelliottdev.github.io',known=value=>C.field('specified',value);
const registry=JSON.parse(readFileSync(new URL('../../data/experiments.json',import.meta.url),'utf8'));
const ids=['lp2-row-column-routes','lp2-row-column-english'];
const authored=ids.map(id=>{
 const published=registry.records.find(record=>record.id===id);assert(published);
 const record=JSON.parse(readFileSync(new URL('../../experiments/records/'+id+'/record.json',import.meta.url),'utf8'));
 assert.equal(record.status,'published');assert.equal(record.recorded_comparison.version,1);
 return {...published,...record}; // Editorial type is supplied by the generated registry.
});
const actualDocs=Search.experimentDocs(authored);
function idea({pages=['lp2-15'],operations=[{id:'reverse_row_runes',label:'Reverse rune order within rows'}],rules={},scopeExtra={}}={}){
 return Research.prepare(C.confirm(C.createDraft({source:{text:'Compare the exact confirmed row reversal.'},aim:known('Find readable text'),
  method:known({operations}),scope:known({pages,...scopeExtra}),rules}),{id:'worker-overlap-fixture',at:'2026-10-24T12:00:00Z'})).request;
}
const post=body=>new Request('https://fixture.workers.dev/ask',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(body)});
function fixture({ai=true,allowed=true}={}){
 const state={fetches:[],limits:0,models:0,modelInputs:[]};
 const load=createRecordLoader(async(url,options)=>{
  state.fetches.push({url,options});
  if(url.endsWith('/data/experiments.json'))return Response.json({schema:registry.schema,records:authored});
  if(url.endsWith('/data/assistant-index.json'))return Response.json({documents:[{id:'lp2-15',kind:'page',href:'#/page/lp2-15',text:'Supporting page context is not an executed solving test.'}]});
  throw Error('Unexpected fetch: '+url);
 });
 const env={SITE_ORIGIN:origin,IDEA_LIMIT:{limit:async()=>{state.limits++;return {success:allowed};}},...(ai?{AI:{run:async(_model,options)=>{
  state.models++;state.modelInputs.push(JSON.parse(options.messages[1].content));return {choices:[{message:{content:'The supplied condition requires a separate comparison [1].'}}]};
 }}}:{})};
 return {state,env,handle:createHandler(load)};
}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('LP2-15 returns exact authored overlap with source binding and zero model calls',async()=>{
 const {state,env,handle}=fixture(),request=idea();
 const response=await handle(post(request),env),data=await response.json();assert.equal(response.status,200);
 const expected=Recorded.compare({snapshot:Research.validate(request).snapshot,documents:actualDocs});assert(expected);
 assert.equal(data.kind,'recorded-overlap');assert.equal(data.answer,expected.answer);
 assert.deepEqual(data.sources,expected.sources);assert.deepEqual(data.sources.map(source=>source.id),ids);
 assert.equal(data.claimBinding,await Research.binding(request));assert.equal(state.models,0);assert.equal(state.limits,1);
 assert.deepEqual(Markdown.citationNumbers(data.answer,data.sources.length),[1,2]);
 for(const source of data.sources){const exact=actualDocs.find(doc=>doc.id===source.id);assert.equal(source.text,exact.text);assert.equal(source.href,exact.href);}
 assert.equal(state.fetches.length,2);assert(state.fetches.every(call=>call.options.cache==='no-cache'));
 const again=await (await handle(post(request),env)).json();assert.equal(again.answer,data.answer);assert.equal(state.models,0);assert.equal(state.limits,2,'Every direct request retains the rate-limit gate');assert.equal(state.fetches.length,2,'Normal bounded record-loader caching remains available');
});
await test('LP2-49 and LP2-55 retain only the executed opening evaluation',async()=>{
 const {state,env,handle}=fixture();
 for(const page of ['lp2-49','lp2-55']){
  const request=idea({pages:[page]}),response=await handle(post(request),env),data=await response.json();
  assert.equal(response.status,200);assert.equal(data.kind,'recorded-overlap');assert.deepEqual(data.sources.map(source=>source.id),[ids[0]]);
  assert(data.answer.includes('nine fixed known openings'));assert(!data.answer.includes('English quadgrams'));
  assert.equal(data.claimBinding,await Research.binding(request));
 }
 assert.equal(state.models,0);
});
await test('empty, outside, compound and explicit-condition requests reach the ordinary model path',async()=>{
 const {state,env,handle}=fixture();
 const requests=[idea({pages:['lp2-50']}),idea({pages:['lp2-56']}),
  idea({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'},{id:'vigenere',label:'Apply Vigenere',key:'ABC'}]}),
  idea({rules:{boundaryMode:known('fixed_spaces')}}),idea({rules:{evaluation:C.field('not_applicable')}}),
  idea({scopeExtra:{description:'Only lines 2–3'}})];
 for(const request of requests){
  const before=state.models,response=await handle(post(request),env),data=await response.json();assert.equal(response.status,200,JSON.stringify(data));
  assert.notEqual(data.kind,'recorded-overlap');assert.equal(state.models,before+1,'Unsupported direct scope/conditions must not bypass ordinary inference');
  assert.equal(data.claimBinding,await Research.binding(request));assert.equal(state.modelInputs.at(-1).idea,Research.validate(request).confirmedQuery);
  for(const record of state.modelInputs.at(-1).records){assert.equal(record.recordedComparison,undefined);assert.equal(JSON.parse(record.text).recorded_comparison,undefined,'Direct execution metadata must not consume model context');}
 }
});
await test('valid authored overlap works without AI binding while unsupported requests fail configured-model gate',async()=>{
 const {state,env,handle}=fixture({ai:false}),request=idea();
 const response=await handle(post(request),env),data=await response.json();assert.equal(response.status,200);assert.equal(data.kind,'recorded-overlap');assert.equal(state.models,0);
 assert.equal((await handle(post(idea({rules:{reset:known('per_page')}})),env)).status,503);
});
await test('rate limit and Origin still precede source loading and direct comparison',async()=>{
 const {state,env,handle}=fixture({allowed:false}),request=idea();
 const denied=await handle(post(request),env);assert.equal(denied.status,429);assert.equal((await denied.json()).claimBinding,await Research.binding(request));assert.equal(state.fetches.length,0);assert.equal(state.models,0);
 const bad=new Request(post(request),{headers:{Origin:'https://other.example','Content-Type':'application/json'}});
 assert.equal((await handle(bad,env)).status,403);assert.equal(state.limits,1);assert.equal(state.fetches.length,0);
 const absent={SITE_ORIGIN:origin};assert.equal((await handle(post(request),absent)).status,503);assert.equal(state.fetches.length,0);
});
await test('legacy text-only requests never acquire canonical direct-operation authority',async()=>{
 const {state,env,handle}=fixture();
 const response=await handle(post({query:'Reverse rune order within rows on LP2-15',pages:['lp2-15']}),env),data=await response.json();
 assert.equal(response.status,200);assert.notEqual(data.kind,'recorded-overlap');assert.equal(state.models,1);assert.equal(data.claimBinding,undefined);
});
console.log(`PASS ${groups} Worker recorded-comparison groups; actual authored metadata, mocked fetch/rate/model bindings, no hosted calls or experiment runs.`);
