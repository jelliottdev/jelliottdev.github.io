import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import F from '../research-family.js';
import L from '../local-experiment.js';
import {createFamilyRunHandler} from '../services/idea-assistant/family-runs.mjs';

const origin='https://jelliottdev.github.io',path='/families/deor-feedback-v1',at='2026-10-24T12:00:00.000Z';
const hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(L.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
const raw=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8'));
// Small independent synthetic manuscript fixture. No network or production writes.
for(const page of raw.pages)page.raw=page.id==='lp2-50'?'':raw.alphabet.map(a=>a.rune).join('')+'-ᚠᚠ\nᚢᚦ';
function fixture(){
 const sqlite=new DatabaseSync(':memory:');sqlite.exec(readFileSync(new URL('../services/idea-assistant/migrations/0010_family_case_results.sql',import.meta.url),'utf8'));
 let bundle=structuredClone(raw),beforeBatch=null,calls=0;
 const db={prepare(sql){return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),_sql:sql,_args:args};}};},async batch(statements){
  assert(statements.length,'D1 batches must contain SQL');
  if(beforeBatch){const fn=beforeBatch;beforeBatch=null;fn();}
  sqlite.exec('BEGIN');try{const results=statements.map(s=>sqlite.prepare(s._sql).run(...s._args));sqlite.exec('COMMIT');return results;}catch(error){sqlite.exec('ROLLBACK');throw error;}
 }};
 const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async()=>({success:true})},AI:{run(){throw Error('No AI allowed');}}};
 const handle=createFamilyRunHandler({now:()=>new Date(at),fetcher:async(url,options)=>{calls++;assert.equal(url,origin+'/data/local-run-inputs.json');assert.equal(options.redirect,'manual');return Response.json(bundle);}});
 return {sqlite,env,handle,setBundle(value){bundle=value;},get bundle(){return bundle;},setBeforeBatch(fn){beforeBatch=fn;},get calls(){return calls;}};
}
function req(action='',body,options={}){return new Request('https://worker.example'+path+(action?'/'+action:''),{method:body===undefined?'GET':'POST',headers:{origin,'content-type':'application/json',...options.headers},...(body===undefined?{}:{body:JSON.stringify(body)}),...options});}
async function call(f,action,body,status=200){const response=await f.handle(req(action,body),f.env);assert.equal(response.status,status,await response.clone().text());return response.json();}
async function prepared(f,count=2){const snapshot=await F.snapshot(f.bundle),caseIds=F.caseIds(snapshot).slice(0,count);return call(f,'prepare',{revision:snapshot.revision,caseIds});}
function submission(prepared){return {plan:prepared.plan,results:prepared.plan.cases.map(c=>({caseId:c.id,result:L.run(c.task)})),controls:prepared.controls.map(c=>({caseId:c.caseId,results:c.suite.cases.map(f=>({id:f.id,result:L.run(f.task)}))}))};}
function count(f){return f.sqlite.prepare('SELECT COUNT(*) n FROM family_case_results').get().n;}
function fill(f,n){const insert=f.sqlite.prepare('INSERT INTO family_case_results VALUES(?,?,?,?,?,?,?,?,?,?)');for(let i=0;i<n;i++)insert.run('fixture','old','filler-'+i,'t','{}','h','{}',0,at,at.slice(0,10));}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}

await test('snapshot and bounded preparation are read-only, exact and source-bound',async()=>{
 const f=fixture(),snapshot=await call(f,'');assert.equal(snapshot.family.totalCases,990);assert.equal(snapshot.family.configurations.length,18);assert.equal(snapshot.family.pages.length,55);assert.deepEqual(snapshot.coverage,{completed:[],matched:[]});
 const p=await prepared(f,12);assert.equal(p.plan.cases.length,12);assert.equal(p.controls.length,12);assert.equal(count(f),0);
 assert(p.controls.every(c=>c.suite.cases.length===2));assert.equal(f.calls,2);
 const ids=F.caseIds(snapshot.family);await call(f,'prepare',{revision:snapshot.family.revision,caseIds:ids.slice(0,13)},400);await call(f,'prepare',{revision:snapshot.family.revision,caseIds:[ids[0],ids[0]]},400);
 await call(f,'prepare',{revision:'old',caseIds:[ids[0]]},409);await call(f,'prepare',{revision:snapshot.family.revision,caseIds:[ids[0]],extra:true},400);
});
await test('complete batch is independently verified, saved atomically and idempotent',async()=>{
 const f=fixture(),p=await prepared(f),body=submission(p),original=L.verify;let replays=0;L.verify=async(...args)=>{replays++;return original(...args);};
 try{const accepted=await call(f,'results',body);assert.deepEqual(accepted.accepted,p.plan.cases.map(c=>c.id));assert.equal(replays,2);assert.equal(count(f),2);
  const coverage=await call(f,'');assert.deepEqual(coverage.coverage.completed,accepted.accepted);assert.equal(replays,2,'GET never replays target computations');
  await call(f,'results',body);assert.equal(count(f),2);assert.equal(replays,4);
 }finally{L.verify=original;}
});
await test('tampered target, controls, missing cases or extra fields never create partial coverage',async()=>{
 for(const mutate of [b=>{b.results[1].result.transformed[0].text+='ᚠ';},b=>{b.controls[1].results[0].result.metrics.runes++;},b=>{b.controls[1].results[1]=b.controls[1].results[0];},b=>{b.results.pop();},b=>{b.results[1].caseId=b.results[0].caseId;},b=>{b.plan.cases[0].task.title='Changed';}]){
  const f=fixture(),body=submission(await prepared(f));mutate(body);await call(f,'results',body,422);assert.equal(count(f),0);
 }
 const f=fixture(),body=submission(await prepared(f));body.extra=true;await call(f,'results',body,400);assert.equal(count(f),0);
});
await test('official source revision changes invalidate old plans and isolate old coverage',async()=>{
 const f=fixture(),p=await prepared(f);await call(f,'results',submission(p));const next=structuredClone(f.bundle);next.pages.find(p=>p.id==='lp2-00').raw+='ᚠ';f.setBundle(next);
 await call(f,'results',submission(p),422);assert.deepEqual((await call(f,'')).coverage,{completed:[],matched:[]});assert.equal(count(f),2);
});
await test('quota checked before target replay and concurrent quota race rolls back whole batch',async()=>{
 const f=fixture(),body=submission(await prepared(f));fill(f,999);const original=L.verify;L.verify=async()=>{throw Error('Quota must reject before replay');};
 try{await call(f,'results',body,429);assert.equal(count(f),999);}finally{L.verify=original;}
 const race=fixture(),raceBody=submission(await prepared(race));race.setBeforeBatch(()=>fill(race,999));await call(race,'results',raceBody,429);assert.equal(count(race),999);assert.equal(race.sqlite.prepare('SELECT COUNT(*) n FROM family_case_results WHERE family_id=?').get('deor-feedback-v1').n,0);
});
await test('exact duplicate submission consumes no quota at daily maximum',async()=>{
 const f=fixture(),body=submission(await prepared(f));await call(f,'results',body);fill(f,998);await call(f,'results',body);assert.equal(count(f),1000);
});
await test('stored result corruption fails closed without target reruns',async()=>{
 const f=fixture(),body=submission(await prepared(f));await call(f,'results',body);f.sqlite.prepare('UPDATE family_case_results SET matched=1-matched').run();await call(f,'',undefined,503);
});
await test('saved case evidence survives a fresh handler and is independently identified without target replay',async()=>{
 const f=fixture(),body=submission(await prepared(f)),caseId=body.plan.cases[0].id;await call(f,'results',body);
 const reloaded=createFamilyRunHandler({fetcher:async()=>Response.json(f.bundle)}),original=L.verify;L.verify=async()=>{throw Error('Reading saved evidence must not replay targets');};
 try{const response=await reloaded(req('cases/'+encodeURIComponent(caseId)),f.env);assert.equal(response.status,200);const evidence=await response.json();
  assert.deepEqual(Object.keys(evidence).sort(),['familyId','revision','caseId','task','result','resultId','verifiedAt'].sort());assert.equal(evidence.familyId,'deor-feedback-v1');assert.equal(evidence.revision,body.plan.revision);assert.equal(evidence.caseId,caseId);assert.deepEqual(evidence.task,body.plan.cases[0].task);assert.deepEqual(evidence.result,body.results[0].result);assert.equal(evidence.resultId,await hash(body.results[0].result));assert.equal(evidence.verifiedAt,at);
  await call(f,'cases/not-a-case',undefined,404);const unused=F.caseIds((await F.snapshot(f.bundle))).at(-1);await call(f,'cases/'+unused,undefined,404);
  f.sqlite.prepare('UPDATE family_case_results SET result_json=? WHERE case_id=?').run('{}',caseId);await call(f,'cases/'+caseId,undefined,503);
 }finally{L.verify=original;}
});
await test('full 990-case coverage validates official inputs once and prepares in bounded chunks',async()=>{
 const f=fixture();f.setBundle(JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8')));
 const preparer=await F.createPreparer(f.bundle),ids=F.caseIds(preparer.snapshot),insert=f.sqlite.prepare('INSERT INTO family_case_results VALUES(?,?,?,?,?,?,?,?,?,?)');
 for(let offset=0;offset<ids.length;offset+=12){const plan=await preparer.prepare(ids.slice(offset,offset+12));for(const item of plan.cases){const result=L.run(item.task);insert.run(plan.familyId,plan.revision,item.id,item.task.taskId,L.stable(item.task),await hash(result),L.stable(result),Number(result.matches[0].matched),at,at.slice(0,10));}}
 const original=F.createPreparer,verify=L.verify;let factories=0,batches=0;
 F.createPreparer=async(...args)=>{factories++;const prepared=await original(...args);return {...prepared,prepare:async selected=>{batches++;assert(selected.length<=12);return prepared.prepare(selected);}};};
 L.verify=async()=>{throw Error('Coverage retrieval must not replay targets');};
 try{const started=performance.now(),output=await call(f,'');console.log('Real-input 990-case coverage GET: '+Math.round(performance.now()-started)+' ms (local SQLite fixture)');assert.equal(output.coverage.completed.length,990);assert.deepEqual(output.coverage.completed,ids);assert.equal(factories,1);assert.equal(batches,83);}finally{F.createPreparer=original;L.verify=verify;}
});
await test('cancelled requests never publish coverage, including cancellation during replay',async()=>{
 const f=fixture(),body=submission(await prepared(f)),controller=new AbortController(),original=L.verify;
 L.verify=async(...args)=>{const result=await original(...args);controller.abort();return result;};
 try{const response=await f.handle(req('results',body,{signal:controller.signal}),f.env);assert.equal(response.status,499);assert.equal(count(f),0);}finally{L.verify=original;}
 const already=new AbortController();already.abort();assert.equal((await f.handle(req('',undefined,{signal:already.signal}),f.env)).status,499);assert.equal(count(f),0);
});
await test('origin, method, CORS, body bounds, rate limits and unavailable sources are enforced',async()=>{
 const f=fixture();assert.equal((await f.handle(req('',undefined,{headers:{origin:'https://wrong.example'}}),f.env)).status,403);
 assert.equal((await f.handle(req('',undefined,{method:'POST'}),f.env)).status,405);
 assert.equal((await f.handle(req('prepare',undefined,{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}}),f.env)).status,204);
 assert.equal((await f.handle(req('prepare',undefined,{method:'OPTIONS',headers:{origin,'access-control-request-method':'GET'}}),f.env)).status,403);
 const large=new Request('https://worker.example'+path+'/results',{method:'POST',headers:{origin,'content-type':'application/json','content-length':'2097153'},body:'{}'});assert.equal((await f.handle(large,f.env)).status,400);
 f.env.TASK_LIMIT.limit=async()=>({success:false});await call(f,'',undefined,429);assert.equal(f.calls,0);
 const bad=createFamilyRunHandler({fetcher:async()=>new Response('',{status:503})});assert.equal((await bad(req(''),fixture().env)).status,422);
});
console.log('Family result handler: '+groups+' groups passed');
