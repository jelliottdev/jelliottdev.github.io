/* Real SQLite and existing task handlers; synthetic software checks, no hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import C from '../claim-specification.js';
import H from '../claim-share.js';
import E from '../local-experiment.js';
import Finite from '../finite-program-question.js';
import Compiler from '../finite-search-compiler.js';
import {createFiniteSearchHandler} from '../services/idea-assistant/finite-search.mjs';
import {issue} from '../services/idea-assistant/prepared-plans.mjs';
const at='2026-10-25T12:00:00.000Z',origin='https://jelliottdev.github.io',known=value=>C.field('specified',value,{kind:'supplied',refs:['software:explicit']}),hash=value=>createHash('sha256').update(C.serialize(value)).digest('hex');
function card({outcome='Solve LP2',prefix=[1,2]}={}){return H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic software QA. Two explicit affine settings; not a proposed decryption.'},aim:known(outcome),method:known({operations:[{id:'affine',label:'Affine substitution',a:1}]}),scope:known({pages:['lp2-15','lp2-16']}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:prefix}),searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'b',values:[1,2]}]})}}),{id:'software',at}));}
function fixture(){
 const sqlite=new DatabaseSync(':memory:'),dir=new URL('../services/idea-assistant/migrations/',import.meta.url);for(const name of readdirSync(dir).filter(n=>/^\d{4}_.*\.sql$/.test(n)).sort())sqlite.exec(readFileSync(new URL(name,dir),'utf8'));
 const bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8'));bundle.pages.forEach(p=>{p.raw='ᚠᚢᚦ';p.reviewed_text=null;});
 let writes=0,rates=0,fetches=0,failLookup=false;const queries=[];
 const db={prepare(sql){queries.push(sql);return {bind(...args){return {sql,args,first:async()=>{if(failLookup&&/FROM local_tasks t JOIN local_task_results/.test(sql))throw Error('Offline');if(!/^\s*SELECT\b/i.test(sql))writes++;return sqlite.prepare(sql).get(...args)||null;},all:async()=>{if(failLookup&&/FROM local_tasks t JOIN local_task_results/.test(sql))throw Error('Offline');return {results:sqlite.prepare(sql).all(...args)};},run:async()=>{writes++;return sqlite.prepare(sql).run(...args);}};}};},async batch(items){sqlite.exec('BEGIN');try{const results=items.map(item=>{writes++;return {success:true,meta:{changes:Number(sqlite.prepare(item.sql).run(...item.args).changes)}};});sqlite.exec('COMMIT');return results;}catch(error){sqlite.exec('ROLLBACK');throw error;}}};
 const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async()=>{rates++;return {success:true};}}},fetcher=async url=>{fetches++;if(url===origin+'/data/local-run-inputs.json')return Response.json(bundle);const id=url.match(/\/data\/pages\/(lp[12]-\d{2})\.json$/)?.[1];assert(id,'Unexpected external URL '+url);return Response.json(bundle.pages.find(p=>p.id===id));},handler=createFiniteSearchHandler({fetcher,now:()=>new Date(at)});
 function add(value){const id='p_'+hash(value);sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,id.slice(2),C.serialize(value),'unused',at);sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(id,at,at.slice(0,10));return id;}
 async function call(id,action,body,extra={}){const response=await handler(new Request('https://worker.example/finite-search/'+id+'/'+action,{method:'POST',headers:{origin,'Content-Type':'application/json',...extra},body:JSON.stringify(body)}),env);return {status:response.status,value:await response.json()};}
 return {sqlite,db,bundle,env,handler,add,call,queries,setFail:value=>failLookup=value,counts:()=>({writes,rates,fetches,tasks:sqlite.prepare('SELECT COUNT(*) AS n FROM local_tasks').get().n,results:sqlite.prepare('SELECT COUNT(*) AS n FROM local_task_results').get().n,preparations:sqlite.prepare('SELECT COUNT(*) AS n FROM prepared_plans').get().n})};
}
const selection=compiled=>compiled.domain.cases.map(c=>({settings:compiled.members.find(m=>m.programId===c.programId).settings,pageId:c.pageId}));
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
await test('read-only evidence, admitted batch creation, real result saving and cross-outcome reuse preserve one original idea',async()=>{
 const f=fixture();try{const original=card(),id=f.add(original),compiled=await Compiler.compile(original,f.bundle),before=C.serialize(original),base=f.counts();
 let evidence=await f.call(id,'evidence',{inputVersion:'raw'});assert.equal(evidence.status,200);assert.deepEqual(evidence.value.sources,[]);assert.equal(evidence.value.lookupComplete,true);assert.equal(f.counts().writes,base.writes);
 const prepared=await f.call(id,'prepare',{inputVersion:'raw',cases:selection(compiled)});assert.equal(prepared.status,200,JSON.stringify(prepared.value));assert.equal(prepared.value.cases.length,4);assert.equal(f.counts().tasks,0);assert.equal(f.counts().results,0);
 const createBody={cases:prepared.value.cases.map(c=>({task:c.task,inputVersion:'raw',parentTaskId:null,preparationId:c.preparation.id}))},created=await f.call(id,'create',createBody);assert.equal(created.status,200,JSON.stringify(created.value));assert.equal(created.value.tasks.length,4);assert.equal(f.counts().tasks,4);
 const results={results:created.value.tasks.map(task=>({taskId:task.id,result:E.run(task.plan)}))},saved=await f.call(id,'results',results);assert.equal(saved.status,200,JSON.stringify(saved.value));assert.equal(saved.value.receipts.length,4);for(const receipt of saved.value.receipts){assert.deepEqual(Object.keys(receipt).sort(),['latestRun','state','taskId']);assert.equal(receipt.state,'results-verified');}
 evidence=await f.call(id,'evidence',{inputVersion:'raw'});assert.equal(evidence.status,200);const proof=await Finite.summarize(compiled.domain,evidence.value.sources,{lookupComplete:evidence.value.lookupComplete});assert.equal(Finite.decision(proof).answer,'prefix-found');assert.equal(proof.coveredCaseIds.length,4);
 const other=card({outcome:'Reproduce a result'}),otherId=f.add(other),beforeReuse=f.counts(),reuse=await f.call(otherId,'evidence',{inputVersion:'raw'});assert.equal(reuse.status,200);assert.equal(reuse.value.sources.length,4);assert.equal(f.counts().writes,beforeReuse.writes);assert.equal(f.sqlite.prepare('SELECT card_json FROM proposals WHERE id=?').get(id).card_json,before);
 const rateBefore=f.counts().rates;assert.equal((await f.call(id,'create',createBody)).status,200);assert.equal(f.counts().rates,rateBefore+1,'One outer rate check per batch, not one per case');assert.equal(f.counts().tasks,4,'Retry keeps exact original tasks');
 }finally{f.sqlite.close();}
});
await test('a completed negative proves only all declared page/setting cases, and partial evidence remains explicit',async()=>{
 const f=fixture();try{const original=card({prefix:[28,28]}),id=f.add(original),compiled=await Compiler.compile(original,f.bundle),picked=selection(compiled),prepared=await f.call(id,'prepare',{inputVersion:'raw',cases:picked});assert.equal(prepared.status,200);const created=await f.call(id,'create',{cases:prepared.value.cases.map(c=>({task:c.task,inputVersion:'raw',parentTaskId:null,preparationId:c.preparation.id}))});assert.equal(created.status,200);
 await f.call(id,'results',{results:created.value.tasks.slice(0,1).map(t=>({taskId:t.id,result:E.run(t.plan)}))});let found=await f.call(id,'evidence',{inputVersion:'raw'}),proof=await Finite.summarize(compiled.domain,found.value.sources,{lookupComplete:found.value.lookupComplete});assert.equal(Finite.decision(proof).state,'missing-evidence');assert.equal(proof.missingCaseIds.length,3);
 const final=await f.call(id,'results',{results:created.value.tasks.slice(1).map(t=>({taskId:t.id,result:E.run(t.plan)}))});assert.equal(final.status,200);found=await f.call(id,'evidence',{inputVersion:'raw'});proof=await Finite.summarize(compiled.domain,found.value.sources,{lookupComplete:found.value.lookupComplete});assert.equal(Finite.decision(proof).answer,'prefix-not-found');
 }finally{f.sqlite.close();}
});
await test('bad later creation or submission member leaves no partial writes; forged scope/settings cannot obtain preparation',async()=>{
 const f=fixture();try{const original=card(),id=f.add(original),compiled=await Compiler.compile(original,f.bundle),prepared=await f.call(id,'prepare',{inputVersion:'raw',cases:selection(compiled)});assert.equal(prepared.status,200);const create={cases:prepared.value.cases.map(c=>({task:c.task,inputVersion:'raw',parentTaskId:null,preparationId:c.preparation.id}))},bad=structuredClone(create);bad.cases[3].preparationId='prep_'+'0'.repeat(64);const before=f.counts();assert.equal((await f.call(id,'create',bad)).status,409);assert.equal(f.counts().tasks,0);assert.equal(f.counts().writes,before.writes);
 const invalid=structuredClone(selection(compiled).slice(0,2));invalid[1].settings[0].value=27;assert.notEqual((await f.call(id,'prepare',{inputVersion:'raw',cases:invalid})).status,200);assert.equal(f.counts().preparations,before.preparations);
 const created=await f.call(id,'create',create),results=created.value.tasks.map(t=>({taskId:t.id,result:E.run(t.plan)}));results[3].result.transformed[0].text='forged';const prior=f.counts();assert.notEqual((await f.call(id,'results',{results})).status,200);assert.equal(f.counts().results,0);assert.equal(f.counts().writes,prior.writes);
 }finally{f.sqlite.close();}
});
await test('lookup failures remain retryable and read-only; origin/version/body failures never create cases',async()=>{
 const f=fixture();try{const id=f.add(card()),before=f.counts();f.setFail(true);assert.equal((await f.call(id,'evidence',{inputVersion:'raw'})).status,503);assert.equal(f.counts().writes,before.writes);f.setFail(false);assert.equal((await f.call(id,'evidence',{inputVersion:'raw'})).status,200);assert.equal((await f.call(id,'evidence',{inputVersion:'reviewed'})).status,400);assert.equal((await f.call(id,'evidence',{inputVersion:'raw'},{origin:'https://example.invalid'})).status,403);assert.equal(f.counts().tasks,0);assert.equal(f.counts().results,0);
 }finally{f.sqlite.close();}
});
await test('a valid generic preparation cannot stand in for finite-domain membership',async()=>{
 const f=fixture();try{const original=card(),id=f.add(original),compiled=await Compiler.compile(original,f.bundle),prepared=await f.call(id,'prepare',{inputVersion:'raw',cases:selection(compiled).slice(0,1)});assert.equal(prepared.status,200);const item=prepared.value.cases[0];
 const generic=await issue({db:f.db,proposalId:id,card:original,task:item.task,inputVersion:'raw',parentTaskId:null,controls:item.controls,authority:'idea',basis:{kind:'compiled-card',normalizedCard:original},createdAt:at});
 const before=f.counts(),created=await f.call(id,'create',{cases:[{task:item.task,inputVersion:'raw',parentTaskId:null,preparationId:generic.id}]});assert.equal(created.status,409);assert.equal(f.counts().writes,before.writes);assert.equal(f.counts().tasks,0);
 }finally{f.sqlite.close();}
});
console.log(groups+' finite search HTTP groups passed');
