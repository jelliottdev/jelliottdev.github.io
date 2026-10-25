/* Full authored-family loader QA. Synthetic controls only; no target execution. */
import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import C from '../claim-specification.js';
import H from '../claim-share.js';
import E from '../local-experiment.js';
import Evaluators from '../output-evaluators.js';
import Compiler from '../factored-finite-search-compiler.js';
import {compileFiniteRecordPlan,loadFiniteRecordPlan,LIMITS} from '../services/idea-assistant/finite-record-plans.mjs';
import {createRecordPlanHandler} from '../services/idea-assistant/record-plans.mjs';
const copy=structuredClone,hash=v=>createHash('sha256').update(typeof v==='string'||v instanceof Uint8Array?v:E.stable(v)).digest('hex'),known=v=>C.field('specified',v,{kind:'supplied',refs:['software:explicit']}),encode=v=>new TextEncoder().encode(JSON.stringify(v));
const bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8'));
const keys=[[23,10,1,10,9,10,16,26],[0,10,4,0,1,19,0,18,4,18,9,0,18]],rotations=keys.flatMap(key=>key.map((_,i)=>key.slice(i).concat(key.slice(0,i)))),pages=Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0'));
function card(evaluation=Evaluators.criterion(),version='raw'){
 return H.cardData(C.confirm(C.createDraft({source:{text:'Software fixture: compare every rotation of the two historical keys in both directions.'},aim:known({outcomeId:'decipher',detail:'Comparison only, not a reading.'}),method:known({operations:[{id:'repeating_key',label:'Repeating key',reset:'page'}]}),scope:known({pages}),rules:{inputVersion:known(version),representation:known('GP29'),evaluation:known(evaluation),searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'key',values:rotations},{operation:0,name:'direction',values:['add','subtract']}]})}}),{id:'software',at:'2026-10-25T12:00:00.000Z'}));
}
async function fixture(evaluation,version='raw'){
 const input=card(evaluation,version),b=copy(bundle);if(version==='reviewed')for(const p of b.pages)if(pages.includes(p.id))p.reviewed_text=p.raw;
 const compiled=await (evaluation==='measurement'?Compiler.compileOutputInspection:evaluation?.kind==='exact-prefix'?Compiler.compile:Compiler.compileLanguageComparison)(input,b,webcrypto),members=[];
 // Invert each repeating shift independently to construct an exact full-output witness.
 const values=Array.from({length:64},(_,i)=>(i*7+3)%29);
 for(const member of compiled.members){const step=compiled.domain.programs.find(p=>p.id===member.programId).steps[0],text=values.map((value,i)=>b.alphabet[(value+(step.direction==='subtract'?1:-1)*step.key[i%step.key.length]+29)%29].rune).join(''),task=await E.prepare({title:'Synthetic complete family witness',alphabet:b.alphabet,pages:[{id:'lp2-00',text}],steps:[step],criterion:{kind:'exact-prefix',values}},webcrypto),result=E.run(task);assert(result.matches[0].matched);members.push({settings:member.settings,control:{label:'Full synthetic output',task,expected_result_sha256:hash(result)}});}
 const recipe={kind:'finite-settings',id:'all-known-key-rotations',title:'Compare every known-key rotation',question:'How do all explicitly declared outputs compare?',scope_change:'All 42 programs on all 56 unsolved pages.',limitation:'Language comparison is not a decryption.',card:input,inputs:{version,alphabet_sha256:hash(b.alphabet),pages:pages.map(id=>({id,text_sha256:hash(b.pages.find(p=>p.id===id)[version==='raw'?'raw':'reviewed_text'])}))},control:{kind:'finite-program-controls',members}},record={id:'software-finite-family',status:'published',browser_followups:[recipe]};
 return {record,bundle:b,compiled,recipe,ref:{recordId:record.id,followupId:recipe.id}};
}
const raw=record=>({bytes:encode(record)}),compile=f=>compileFiniteRecordPlan({...f.ref,raw:raw(f.record),bundle:f.bundle},{crypto:webcrypto});
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
const f=await fixture();
await test('all 42 historical rotated programs and 56 pages compile with complete witnesses and no target runs',async()=>{
 const before=E.stable(f),run=E.run;let count=0;E.run=task=>{assert.equal(task.title,'Synthetic complete family witness');assert.equal(task.criterion.kind,'exact-prefix');assert.equal(task.pages.length,1);count++;return run(task);};let result;try{result=await compile(f);}finally{E.run=run;}
 assert.equal(count,42);assert.equal(result.state,'finite-plan-ready');assert.equal(result.domain.domainId,f.compiled.domain.id);assert.equal(result.domain.programs,42);assert.equal(result.domain.pages,56);assert.equal(result.domain.totalCases,2352);assert.deepEqual(result.domain.criterion,Evaluators.criterion());assert(!Object.hasOwn(result,'task'));assert.deepEqual(result.snapshot,f.recipe);assert.equal(result.origin.recordSha256,hash(encode(f.record)));assert.equal(result.origin.protocolSha256,hash(f.recipe));assert.equal(E.stable(f),before);
});
await test('member omissions duplicates reordering changed steps and false expected outputs fail closed',async()=>{
 for(const change of [x=>x.recipe.control.members.pop(),x=>x.recipe.control.members[1]=copy(x.recipe.control.members[0]),x=>x.recipe.control.members.reverse(),x=>x.recipe.control.members[0].settings[0].value='changed',x=>x.recipe.control.members[0].control.task.steps[0].direction='changed',x=>x.recipe.control.members[0].control.expected_result_sha256='0'.repeat(64),x=>x.recipe.control.members[0].control.task.criterion.values.pop()]){const x=copy(f);change(x);await assert.rejects(()=>compile(x));}
});
await test('whole source and exact input evaluation and canonical card are bound',async()=>{
 for(const change of [x=>x.record.status='draft',x=>x.recipe.kind='other',x=>x.recipe.extra=true,x=>x.recipe.inputs.alphabet_sha256='0'.repeat(64),x=>x.recipe.inputs.pages[0].text_sha256='0'.repeat(64),x=>x.recipe.inputs.pages.reverse(),x=>x.recipe.card.rules.evaluation.value.modelSha256='0'.repeat(64),x=>x.bundle.pages.find(p=>p.id==='lp2-15').raw+='ᚠ']){const x=copy(f);change(x);await assert.rejects(()=>compile(x));}
 const x=copy(f),a=await compile(x);x.record.note='Source presentation changed';const b=await compile(x);assert.notEqual(a.origin.recordSha256,b.origin.recordSha256);assert.equal(a.origin.protocolSha256,b.origin.protocolSha256);assert.equal(a.domain.domainId,b.domain.domainId);
});
await test('shared fetched source avoids duplicate source request and standalone loader uses only two bounded official GETs',async()=>{
 const calls=[],get=async(path,max)=>{calls.push({path,max});assert.equal(path,'/data/local-run-inputs.json');return {value:f.bundle};};await loadFiniteRecordPlan(f.ref,{raw:raw(f.record),get,crypto:webcrypto});assert.equal(calls.length,1);
 const urls=[],fetcher=async(url,options)=>{urls.push(url);assert.equal(options.redirect,'manual');return Response.json(url.endsWith('/record.json')?f.record:f.bundle);};const result=await loadFiniteRecordPlan(f.ref,{fetcher,crypto:webcrypto});assert.equal(urls.length,2);assert.equal(result.domain.totalCases,2352);assert(urls.every(url=>url.startsWith('https://jelliottdev.github.io/')));
 await assert.rejects(()=>loadFiniteRecordPlan({...f.ref,recordId:'../bad'},{fetcher:()=>assert.fail('Invalid references must not fetch'),crypto:webcrypto}));
});
await test('source byte and response bounds plus deadline reject without target execution',async()=>{
 await assert.rejects(()=>compileFiniteRecordPlan({...f.ref,raw:{bytes:new Uint8Array(LIMITS.sourceBytes+1)},bundle:f.bundle},{crypto:webcrypto}));
 await assert.rejects(()=>loadFiniteRecordPlan(f.ref,{fetcher:async()=>new Response('{}',{headers:{'content-type':'application/json','content-length':String(LIMITS.sourceBytes+1)}}),crypto:webcrypto}));
 await assert.rejects(()=>loadFiniteRecordPlan(f.ref,{fetcher:()=>new Promise(()=>{}),timeoutMs:1,crypto:webcrypto}),/timed out/);
});
await test('measurement exact-prefix and reviewed families retain their explicitly declared criterion',async()=>{
 for(const [evaluation,version] of [['measurement','raw'],[{kind:'exact-prefix',values:[1,2]},'raw'],[Evaluators.criterion(),'reviewed']]){const x=await fixture(evaluation,version),result=await compile(x);assert.deepEqual(result.domain.criterion,evaluation==='measurement'?{kind:'measurement'}:evaluation);assert.equal(result.inputVersion,version);assert.equal(result.domain.totalCases,2352);}
});
await test('independent Python constructor full Warning witnesses agree with the maintained JavaScript loader',async()=>{
 const recipe=JSON.parse(execFileSync('python',['-c',"import sys,json;sys.path.insert(0,'scripts');from test_authored_finite_followups import fixture;print(json.dumps(fixture(),ensure_ascii=True))"],{cwd:new URL('..',import.meta.url),encoding:'utf8',maxBuffer:LIMITS.sourceBytes})),record={id:'python-finite-family',status:'published',browser_followups:[recipe]},run=E.run;let count=0;
 E.run=task=>{assert.match(task.title,/synthetic/i);assert.equal(task.criterion.values.length,184);count++;return run(task);};
 let result;try{result=await compileFiniteRecordPlan({recordId:record.id,followupId:recipe.id,raw:raw(record),bundle},{crypto:webcrypto});}finally{E.run=run;}
 assert.equal(count,42);assert.equal(result.domain.totalCases,2352);assert.equal(result.domain.programs,42);assert.equal(result.domain.domainId,f.compiled.domain.id);assert.deepEqual(result.snapshot,recipe);
});
await test('cancelled sources stop before fetching or replaying any further synthetic witness',async()=>{
 const controller=new AbortController();controller.abort();
 await assert.rejects(()=>loadFiniteRecordPlan(f.ref,{signal:controller.signal,fetcher:()=>assert.fail('Aborted loader must not fetch')}),/cancelled/);
 await assert.rejects(()=>compileFiniteRecordPlan({...f.ref,raw:raw(f.record),bundle:f.bundle},{signal:controller.signal,crypto:{subtle:{digest:()=>assert.fail('Aborted compiler must not hash')}}}),/cancelled/);
 for(const stage of ['identity','result']){
  const abort=new AbortController();let release,entered;const waiting=new Promise(resolve=>entered=resolve),crypt={subtle:{async digest(...args){const text=new TextDecoder().decode(args[1]),selected=stage==='identity'?text.includes('Synthetic complete family witness'):text.includes('liberpedia-local-result-v1');if(selected&&!release){await new Promise(resolve=>{release=resolve;entered();});}return webcrypto.subtle.digest(...args);}}},original=E.run;let runs=0;
  E.run=task=>{assert.equal(task.title,'Synthetic complete family witness');runs++;return original(task);};
  try{const pending=compileFiniteRecordPlan({...f.ref,raw:raw(f.record),bundle:f.bundle},{signal:abort.signal,crypto:crypt});await waiting;abort.abort();release();await assert.rejects(()=>pending,/cancelled/);assert.equal(runs,stage==='identity'?0:1);}finally{E.run=original;}
 }
 const abort=new AbortController();let requests=0;await assert.rejects(()=>loadFiniteRecordPlan(f.ref,{signal:abort.signal,raw:raw(f.record),crypto:webcrypto,get:async()=>{requests++;abort.abort();return {value:f.bundle};}}),/cancelled/);assert.equal(requests,1);
});
await test('source prose rejects hidden control and bidi characters while retaining ordinary Unicode',async()=>{
 for(const value of ['bad\u202etitle','bad\u2066title','bad\u2028title','bad\ud800title']){const x=copy(f);x.recipe.title=value;await assert.rejects(()=>compile(x),/text is malformed/);}
 const x=copy(f);x.recipe.title='Compare Vigenère keys 🗝';assert.equal((await compile(x)).snapshot.title,x.recipe.title);
});
await test('real record-plans HTTP reviews the whole source family without evidence queries or task creation',async()=>{
 const origin='https://jelliottdev.github.io',x=copy(f);x.recipe.motivation='Compare every explicitly declared output without inventing a reading.';
 const fetched=[],rateKeys=[],fail=()=>assert.fail('Review must not discover evidence or query/create saved tasks'),handler=createRecordPlanHandler({fetcher:async(url,options)=>{fetched.push({url,options});assert.equal(options.redirect,'manual');assert.equal(options.cache,'no-cache');return Response.json(url===origin+'/experiments/records/'+x.ref.recordId+'/record.json'?x.record:url===origin+'/data/local-run-inputs.json'?x.bundle:fail());},discoverEvidence:fail,discoverPrefixEvidence:fail}),env={SITE_ORIGIN:origin,PROPOSALS:{prepare:fail,batch:fail},TASK_LIMIT:{limit:async value=>{rateKeys.push(value.key);return {success:true};}}};
 const request=(body,extra={})=>new Request('https://worker.example/record-plans',{method:'POST',headers:{origin,'Content-Type':'application/json','CF-Connecting-IP':'127.0.0.7',...extra},body:JSON.stringify(body)}),expected=await compile(x);
 for(const body of [x.ref,{...x.ref,includeExisting:true,includeExistingContext:true,includeBoundaryComparison:true,includeDerivedPrefixEvidence:true},{...x.ref,includeExisting:true,includeMotivation:true}]){
  const before=fetched.length,response=await handler(request(body),env);assert.equal(response.status,200);assert.equal(response.headers.get('Access-Control-Allow-Origin'),origin);assert.equal(response.headers.get('Cache-Control'),'no-store');const value=await response.json();assert.equal(value.state,'finite-plan-ready');assert.deepEqual(value.domain,expected.domain);assert.deepEqual(value.card,expected.card);assert.deepEqual(value.origin,expected.origin);assert.deepEqual(value.snapshot,x.recipe);assert.equal(fetched.length-before,2,'Reuse the already fetched raw record instead of loading it twice');assert(!Object.hasOwn(value,'task'));assert(!Object.hasOwn(value,'coverage'));assert(!Object.hasOwn(value,'existingTask'));assert.equal(Object.hasOwn(value,'motivation'),body.includeMotivation===true);if(body.includeMotivation)assert.equal(value.motivation,x.recipe.motivation);
 }
 assert.deepEqual(rateKeys,['127.0.0.7','127.0.0.7','127.0.0.7']);
 let before=fetched.length,response=await handler(request(x.ref,{origin:'https://other.example'}),env);assert.equal(response.status,403);assert.equal(fetched.length,before);assert.equal(rateKeys.length,3);
 response=await handler(request(x.ref),{...env,TASK_LIMIT:{limit:async()=>({success:false})}});assert.equal(response.status,429);assert.equal(fetched.length,before);
 response=await handler(new Request('https://worker.example/record-plans',{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}}),env);assert.equal(response.status,204);assert.equal(fetched.length,before);assert.equal(rateKeys.length,3);
 response=await handler(request({...x.ref,includeMotivation:true}),env);assert.equal(response.status,400);assert.equal(fetched.length,before,'Invalid flags cannot fetch source material');
});
await test('real record-plans deadline aborts the shared source request before any witnesses',async()=>{
 const origin='https://jelliottdev.github.io',requests=[],run=E.run;E.run=()=>assert.fail('Stalled inputs cannot reach synthetic replay');
 try{const handler=createRecordPlanHandler({timeoutMs:10,fetcher:async(url,options)=>{requests.push({url,signal:options.signal});if(url.endsWith('/record.json'))return Response.json(f.record);return new Promise(()=>{});},discoverEvidence:()=>assert.fail('No evidence lookup')}),response=await handler(new Request('https://worker.example/record-plans',{method:'POST',headers:{origin,'Content-Type':'application/json'},body:JSON.stringify(f.ref)}),{SITE_ORIGIN:origin,TASK_LIMIT:{limit:async()=>({success:true})}});assert.equal(response.status,422);assert.match((await response.json()).reason,/timed out/);assert.equal(requests.length,2);assert(requests.every(r=>r.signal.aborted));}finally{E.run=run;}
});
console.log(groups+' finite authored source loader groups passed; no target calculations or public writes.');
