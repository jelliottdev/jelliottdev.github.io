/* Real SQLite persistence, mocked official page fetches. No hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import L from '../../local-experiment.js';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
const origin='https://jelliottdev.github.io',proposalId='p_'+'a'.repeat(64),at='2026-10-24T12:00:00.000Z';
const alphabet=Array.from({length:29},(_,i)=>({rune:String.fromCharCode(65+i),latin:'R'+i,prime:i+2}));
const source={id:'lp2-15',raw:'ABC A\nBA',reviewed_text:'ABC B\nBA'};
const card=H.cardData(C.confirm(C.createDraft({source:{text:'PRIVATE ORIGINAL'},method:C.field('specified',{operations:[{id:'described_method',label:'Reverse rows'}]},{kind:'supplied',refs:['source:text']})}),{id:'test',at}));
function adapter(){
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,'a'.repeat(64),C.serialize(card),'unused',at);
 const db={sqlite,reads:0,fail:false,prepare(sql){return {bind(...args){return {sql,args,first:async()=>{db.reads++;return sqlite.prepare(sql).get(...args)||null;}};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{if(db.fail)throw Error('Injected storage failure');const result=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return result;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};return db;
}
function fixture(){
 const db=adapter(),urls=[],rates=[];let date=at,fetchFailure=false;
 const env={SITE_ORIGIN:origin,PROPOSALS:db,PROPOSAL_LIMIT:{limit:async value=>{rates.push(value);return {success:true};}}};
 const handle=createLocalTaskHandler({now:()=>new Date(date),fetcher:async(url,options)=>{urls.push(url);assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'error');assert(options.signal);if(fetchFailure)throw Error('Offline');return Response.json(source);}});
 return {db,env,handle,urls,rates,setDate:value=>date=value,setFetchFailure:value=>fetchFailure=value};
}
async function task(title='Reverse rows',version='raw',extra={}){return L.prepare({title,pages:[{id:source.id,text:version==='raw'?source.raw:source.reviewed_text}],alphabet,steps:[{op:'reverse',unit:'line'}],criterion:{kind:'measurement'},...extra});}
const body=task=>({proposalId,task,inputVersion:'raw',parentTaskId:null});
const request=(path,method='GET',data,extra={})=>new Request('https://worker.example'+path,{method,headers:{origin,...(data!==undefined?{'content-type':'application/json'}:{}),'CF-Connecting-IP':'203.0.113.9',...extra},...(data!==undefined?{body:JSON.stringify(data)}:{})});
const call=(f,path,method,data,extra)=>f.handle(request(path,method,data,extra),f.env);
let count=0;async function test(name,fn){await fn();console.log('PASS '+name);count++;}
await test('strict origin, routes, methods, bindings and preflight fail closed',async()=>{
 const f=fixture();assert.equal((await call(f,'/tasks','POST',body(await task()),{origin:'https://evil.example'})).status,403);
 assert.equal((await call(f,'/tasks','POST',body(await task()),{origin:''})).status,403);
 assert.equal((await call(f,'/tasks','GET')).status,405);assert.equal((await call(f,'/tasks/nope')).status,404);
 for(const key of ['PROPOSALS','PROPOSAL_LIMIT','SITE_ORIGIN'])assert.equal((await f.handle(request('/tasks','POST',body(await task())),{...f.env,[key]:null})).status,503);
 const pre=new Request('https://worker.example/tasks',{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}});
 assert.equal((await f.handle(pre,f.env)).status,204);assert.equal(f.db.reads,0);assert.equal(f.rates.length,0);
});
await test('create/GET exact task, card reference and source text; no original idea projected',async()=>{
 const f=fixture(),t=await task(),response=await call(f,'/tasks','POST',body(t)),r=await response.json();assert.equal(response.status,200);
 assert.equal(r.id,t.taskId);assert.equal(r.state,'not-run');assert.deepEqual(r.plan,t);assert.deepEqual(r.card,card);assert(!JSON.stringify(r).includes('PRIVATE'));
 assert.match(r.verification,/computation only/);assert.equal(f.urls.length,1);assert.equal(f.rates[0].key,'203.0.113.9');
 const get=await call(f,'/tasks/'+t.taskId);assert.equal(get.status,200);assert.deepEqual(await get.json(),r);
 const retry=await call(f,'/tasks','POST',body(t));assert.equal(retry.status,200);assert.equal(f.urls.length,1);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
 assert.equal((await call(f,'/tasks/'+t.taskId,'GET',undefined,{origin:''})).status,403);
});
await test('identity, proposal, exact input version and parent cannot be silently changed',async()=>{
 const f=fixture(),t=await task(),bad=structuredClone(t);bad.title='Altered';assert.equal((await call(f,'/tasks','POST',body(bad))).status,400);
 assert.equal((await call(f,'/tasks','POST',{...body(t),extra:true})).status,400);
 assert.equal((await call(f,'/tasks','POST',{...body(t),proposalId:'p_'+'b'.repeat(64)})).status,404);
 assert.equal((await call(f,'/tasks','POST',{...body(t),parentTaskId:'b'.repeat(64)})).status,404);
 assert.equal((await call(f,'/tasks','POST',{...body(t),inputVersion:'reviewed'})).status,422);
 f.setFetchFailure(true);assert.equal((await call(f,'/tasks','POST',body(t))).status,422);f.setFetchFailure(false);
 const parent=await task('Parent');await call(f,'/tasks','POST',body(parent));
 assert.equal((await call(f,'/tasks','POST',{...body(t),parentTaskId:parent.taskId})).status,200);
 assert.equal((await call(f,'/tasks','POST',body(t))).status,409);
 const reviewed=await task('Reviewed','reviewed');assert.equal((await call(f,'/tasks','POST',{...body(reviewed),inputVersion:'reviewed'})).status,200);
});
await test('official source verification uses at most four workers and cancels the shared batch on mismatch',async()=>{
 const f=fixture();let active=0,maxActive=0,calls=0;const signals=[];
 const pages=Array.from({length:9},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:source.raw}));
 const handle=createLocalTaskHandler({now:()=>new Date(at),fetcher:async(url,options)=>{
  assert.match(url,/^https:\/\/jelliottdev\.github\.io\/data\/pages\/lp2-0[0-8]\.json$/);signals.push(options.signal);
  calls++;active++;maxActive=Math.max(maxActive,active);await new Promise(resolve=>setTimeout(resolve,1));active--;
  return Response.json({id:url.split('/').pop().slice(0,-5),raw:source.raw});
 }});
 const t=await task('Nine pages','raw',{pages});assert.equal((await handle(request('/tasks','POST',body(t)),f.env)).status,200);assert.equal(calls,9);assert.equal(maxActive,4);assert(signals.every(signal=>signal===signals[0]));
 const g=fixture();let signal;
 const bad=createLocalTaskHandler({fetcher:async(url,options)=>{signal=options.signal;return Response.json({id:'wrong',raw:source.raw});}});
 assert.equal((await bad(request('/tasks','POST',body(t)),g.env)).status,422);assert.equal(signal.aborted,true);assert.equal(g.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
await test('result replay binds all outputs; normalized valid result idempotent, latest result verified on GET',async()=>{
 const f=fixture(),t=await task();await call(f,'/tasks','POST',body(t));const path='/tasks/'+t.taskId+'/results',result=L.run(t);
 const wrong=structuredClone(result);wrong.transformed[0].text+='X';assert.equal((await call(f,path,'POST',{result:wrong})).status,422);
 assert.equal((await call(f,path,'POST',{result,extra:true})).status,422);
 const response=await call(f,path,'POST',{result}),r=await response.json();assert.equal(response.status,200);assert.equal(r.state,'results-verified');assert.deepEqual(r.latestRun.result,result);
 assert.deepEqual(await(await call(f,path,'POST',{result})).json(),r);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);
 const get=await(await call(f,'/tasks/'+t.taskId)).json();assert.equal(get.state,'results-verified');assert.deepEqual(get.latestRun,r.latestRun);
 const retry=await(await call(f,'/tasks','POST',body(t))).json();assert.equal(retry.state,'results-verified');assert.deepEqual(retry.latestRun,r.latestRun);
 f.db.sqlite.prepare('UPDATE local_task_results SET result_json=?').run(JSON.stringify(wrong));assert.equal((await call(f,'/tasks/'+t.taskId)).status,503);
});
await test('streamed body limits, rate limits and storage errors cannot write partial tasks',async()=>{
 const f=fixture(),t=await task(),reads=f.db.reads;
 const denied={...f.env,PROPOSAL_LIMIT:{limit:async()=>({success:false})}};
 assert.equal((await f.handle(request('/tasks','POST',body(t)),denied)).status,429);assert.equal(f.db.reads,reads);
 assert.equal((await call(f,'/tasks','POST',body(t),{'content-type':'text/plain'})).status,400);
 assert.equal((await call(f,'/tasks','POST',body(t),{'content-length':'2097153'})).status,400);
 const chunks=new ReadableStream({start(controller){controller.enqueue(new Uint8Array(2097153));controller.close();}});
 const oversized=new Request('https://worker.example/tasks',{method:'POST',headers:{origin,'content-type':'application/json'},body:chunks,duplex:'half'});
 assert.equal((await f.handle(oversized,f.env)).status,400);
 f.db.fail=true;assert.equal((await call(f,'/tasks','POST',body(t))).status,503);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
await test('atomic task cap50/day, concurrent retries, and next-day restoration',async()=>{
 const f=fixture(),tasks=await Promise.all(Array.from({length:60},(_,i)=>task('Task '+i)));
 const responses=await Promise.all(tasks.map(t=>call(f,'/tasks','POST',body(t))));assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,10);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,50);
 assert.equal((await call(f,'/tasks','POST',body(tasks[0]))).status,200);
 f.setDate('2026-10-25T00:00:00.000Z');assert.equal((await call(f,'/tasks','POST',body(tasks[59]))).status,200);
 const g=fixture(),t=await task();const dup=await Promise.all(Array.from({length:5},()=>call(g,'/tasks','POST',body(t))));assert(dup.every(r=>r.status===200));assert.equal(g.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
});
await test('atomic distinct result cap50/day retains duplicate retries without consuming quota',async()=>{
 const f=fixture(),tasks=[];
 for(let i=0;i<51;i++){if(i===50)f.setDate('2026-10-25T00:00:00.000Z');const t=await task('Result '+i);tasks.push(t);assert.equal((await call(f,'/tasks','POST',body(t))).status,200);}
 f.setDate('2026-10-26T00:00:00.000Z');
 const responses=await Promise.all(tasks.map(t=>call(f,'/tasks/'+t.taskId+'/results','POST',{result:L.run(t)})));
 assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,1);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,50);
 assert.equal((await call(f,'/tasks/'+tasks[0].taskId+'/results','POST',{result:L.run(tasks[0])})).status,200);
 f.setDate('2026-10-27T00:00:00.000Z');assert.equal((await call(f,'/tasks/'+tasks[50].taskId+'/results','POST',{result:L.run(tasks[50])})).status,200);
});
console.log('PASS '+count+' SQLite-backed local-task groups; all official-source fetches injected, no execution of external code.');
