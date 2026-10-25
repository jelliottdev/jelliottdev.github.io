import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import C from '../../claim-specification.js';
import S from '../../claim-share.js';
import L from '../../local-experiment.js';
import {canonicalProposal} from './proposals.mjs';
import {createCommunityFeedHandler} from './community-feed.mjs';

const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
function fixture({relation=true}={}){
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql',...(relation?['0006_task_ideas.sql']:[]),'0011_task_protocol_lookup.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 const db={sqlite,queries:[],projected:[],fail:false,prepare(sql){
  assert.match(sql,/^\s*(?:SELECT|WITH)\b/i,'Feed must never issue a write');db.queries.push(sql);
  return {bind(...args){return {all:async()=>{if(db.fail)throw Error('PRIVATE SQL failure');const results=sqlite.prepare(sql).all(...args);db.projected.push(...results);return {results};}};}};
 }};
 return {db,env:{SITE_ORIGIN:origin,PROPOSALS:db},handle:createCommunityFeedHandler()};
}
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
async function idea(f,index,{published=true,createdAt=at,aim='solve LP2'}={}){
 const draft=C.createDraft({source:{text:'PRIVATE original '+index},aim:known(aim),
  method:known({operations:[{id:'vigenere',label:'Vigenere',key:'KEY'+index,sourceText:'PRIVATE extraction'}]}),scope:known({pages:['lp2-15']})});
 const p=await canonicalProposal({requestId:crypto.randomUUID(),fragment:S.encode(C.confirm(draft,{id:'PRIVATE confirmation',at})),note:'PRIVATE note',originalIdea:'PRIVATE original wording',sourceUrl:'https://github.com/example/source'});
 f.db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(p.id,p.cardHash,p.cardJson,p.fragment,createdAt);
 f.db.sqlite.prepare('INSERT INTO proposal_submissions(request_id,proposal_id,request_hash,note,source_url,received_at,received_day,original_idea) VALUES(?,?,?,?,?,?,?,?)').run(p.requestId,p.id,p.requestHash,p.note,p.sourceUrl,createdAt,createdAt.slice(0,10),p.originalIdea);
 if(published)f.db.sqlite.prepare('INSERT INTO research_ideas(proposal_id,created_at,created_day) VALUES(?,?,?)').run(p.id,createdAt,createdAt.slice(0,10));
 return p;
}
async function task(f,p,index,{verified=false,associateTask=true,changes={},inputVersion='raw'}={}){
 const plan=await L.prepare({title:'Task '+index,alphabet:Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ').map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),pages:[{id:'lp2-15',text:'ᚠᚢᚦ'}],steps:[],criterion:{kind:'measurement'},...changes});
 const text=L.stable(plan);
 f.db.sqlite.prepare('INSERT INTO local_tasks(id,task_hash,create_hash,proposal_id,card_json,task_json,input_version,parent_task_id,created_at,created_day) VALUES(?,?,?,?,?,?,?,?,?,?)').run(plan.taskId,await digest(text),'0'.repeat(64),p.id,p.cardJson,text,inputVersion,null,at,at.slice(0,10));
 if(associateTask)associate(f,p,plan,at,inputVersion);
 if(verified){const result=L.stable(await L.verify(plan,L.run(plan)));f.db.sqlite.prepare('INSERT INTO local_task_results(id,task_id,result_json,created_at,created_day) VALUES(?,?,?,?,?)').run(await digest(result),plan.taskId,result,at,at.slice(0,10));}
 return plan;
}
function associate(f,p,plan,createdAt=at,inputVersion='raw'){f.db.sqlite.prepare('INSERT INTO local_task_ideas(task_id,proposal_id,input_version,parent_task_id,created_at,created_day) VALUES(?,?,?,?,?,?)').run(plan.taskId,p.id,inputVersion,null,createdAt,createdAt.slice(0,10));}
async function cacheRequest(f,p,plan,{inputVersion='raw',createdAt=at}={}){const text=L.stable(plan);f.db.sqlite.prepare('INSERT INTO idea_computation_evidence(proposal_id,requested_task_id,requested_task_json,requested_task_hash,input_version,created_at) VALUES(?,?,?,?,?,?)').run(p.id,plan.taskId,text,await digest(text),inputVersion,createdAt);}
function request(query='',{method='GET',headers={},path='/community-research'}={}){return new Request('https://worker.example'+path+query,{method,headers:{origin,...headers}});}
const view=async f=>{const response=await f.handle(request(),f.env);assert.equal(response.status,200);return response.json();};
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}

await test('only explicit public entries appear; active card exact; private contributions never selected or returned',async()=>{
 const f=fixture(),publicIdea=await idea(f,1),privateIdea=await idea(f,2,{published:false});await task(f,privateIdea,90,{verified:true});
 const changes=f.db.sqlite.prepare('SELECT total_changes() n').get().n,body=await view(f);
 assert.deepEqual(Object.keys(body).sort(),['entries','nextCursor','schema']);assert.equal(body.schema,'liberpedia-community-research-v1');assert.equal(body.nextCursor,null);assert.equal(body.entries.length,1);
 assert.deepEqual(body.entries[0],{id:publicIdea.id,card:JSON.parse(publicIdea.cardJson),createdAt:at,tasks:[],taskCount:0,verifiedTaskCount:0});
 for(const secret of ['PRIVATE','original_idea','fragment','source_url','request_hash','note',privateIdea.id])assert(!JSON.stringify(body).includes(secret),secret);
 assert(f.db.queries.every(sql=>!/(?:original_idea|proposal_submissions|fragment|source_url|review_reason)/.test(sql)));
 assert.equal(f.db.sqlite.prepare('SELECT total_changes() n').get().n,changes,'Public feed is read only');
 assert.equal(f.db.queries.length,2,'One idea query and one batched metadata query');
});
await test('task metadata limited10 with exact total count and accepted-result state, no full plan/result payloads',async()=>{
 const f=fixture(),p=await idea(f,3),plans=[];for(let i=0;i<12;i++)plans.push(await task(f,p,i,{verified:i%2===0}));
 const body=await view(f),entry=body.entries[0];assert.equal(entry.taskCount,12);assert.equal(entry.verifiedTaskCount,6);assert.equal(entry.tasks.length,10);
 const expected=plans.map((plan,i)=>({id:plan.taskId,title:plan.title,state:i%2===0?'results-verified':'not-run'})).sort((a,b)=>(a.state==='results-verified')-(b.state==='results-verified')||b.id.localeCompare(a.id)).slice(0,10);
 assert.deepEqual(entry.tasks,expected);
 const sql=f.db.queries[1];assert.match(sql,/ROW_NUMBER\(\) OVER \(PARTITION BY proposal_id/);assert.match(sql,/COUNT\(\*\) OVER/);assert.match(sql,/WHERE r.position<=10/);
 assert.match(sql,/json_extract\(t.task_json,'\$\.title'\) AS title/);assert.match(sql,/json_extract\(t.task_json,'\$\.taskId'\) AS embedded_id/);
 assert(!sql.includes('result_json'));assert(f.db.projected.every(row=>!Object.hasOwn(row,'task_json')&&!Object.hasOwn(row,'result_json')));
 assert.deepEqual(Object.keys(entry.tasks[0]).sort(),['id','state','title']);
});
await test('older unfinished work stays reachable ahead of ten newer completed computations',async()=>{
 const f=fixture(),p=await idea(f,'old-pending'),pending=await task(f,p,301);
 f.db.sqlite.prepare('UPDATE local_task_ideas SET created_at=?,created_day=? WHERE task_id=?').run('2026-10-23T12:00:00.000Z','2026-10-23',pending.taskId);
 for(let i=0;i<12;i++)await task(f,p,302+i,{verified:true});
 const entry=(await view(f)).entries[0];assert.equal(entry.taskCount,13);assert.equal(entry.verifiedTaskCount,12);assert.equal(entry.tasks.length,10);assert.equal(entry.tasks[0].id,pending.taskId);assert.equal(entry.tasks[0].state,'not-run');assert.equal(entry.tasks.filter(t=>t.state==='not-run').length,1);
 assert.equal(f.db.queries.length,2);assert(!JSON.stringify(entry.tasks).includes('task_json'));assert(!JSON.stringify(entry).includes('PRIVATE original'));
});

await test('latest50 stable cursor pagination preserves timestamp ties and constant query count',async()=>{
 const f=fixture(),all=[];for(let i=0;i<61;i++)all.push(await idea(f,'page'+i));
 const first=await view(f);assert.equal(first.entries.length,50);assert.equal(typeof first.nextCursor,'string');assert.equal(f.db.queries.length,2,'Query count is independent of50 entries');
 f.db.queries=[];const response=await f.handle(request('?before='+first.nextCursor),f.env);assert.equal(response.status,200);const second=await response.json();assert.equal(second.entries.length,11);assert.equal(second.nextCursor,null);assert.equal(f.db.queries.length,2);
 assert.deepEqual([...first.entries,...second.entries].map(e=>e.id),all.map(p=>p.id).sort().reverse());assert.equal(new Set([...first.entries,...second.entries].map(e=>e.id)).size,61);
 const empty=fixture();assert.deepEqual(await view(empty),{schema:'liberpedia-community-research-v1',entries:[],nextCursor:null});assert.equal(empty.db.queries.length,1);
});
await test('shared computation counted once per associated public idea and no private association leaks',async()=>{
 const f=fixture(),one=await idea(f,'shared-one'),two=await idea(f,'shared-two'),privateIdea=await idea(f,'shared-private',{published:false});
 const plan=await task(f,one,70,{verified:true});associate(f,two,plan,'2026-10-25T01:00:00.000Z');associate(f,privateIdea,plan);
 const body=await view(f);assert.equal(body.entries.length,2);assert.equal(f.db.queries.length,2);
 for(const entry of body.entries){assert.equal(entry.taskCount,1);assert.equal(entry.verifiedTaskCount,1);assert.deepEqual(entry.tasks,[{id:plan.taskId,title:plan.title,state:'results-verified'}]);}
 assert(!JSON.stringify(body).includes(privateIdea.id));assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
});
await test('shared saved work crosses title/category and partial page batches without inflating owned counts',async()=>{
 const f=fixture(),owner=await idea(f,'reuse-owner'),other=await idea(f,'reuse-other',{aim:'measure a pattern'}),source=await task(f,owner,170,{verified:true});
 const requested=await L.prepare({...source,title:'A different title in another category',pages:[...source.pages,{id:'lp2-16',text:'ᚩᚱ'}]});await cacheRequest(f,other,requested);
 const body=await view(f),entry=body.entries.find(e=>e.id===other.id);assert.equal(entry.hasSharedComputation,true);assert.equal(entry.taskCount,0);assert.equal(entry.verifiedTaskCount,0);assert.deepEqual(entry.tasks,[]);assert.equal(f.db.queries.length,2);
 assert(!Object.hasOwn(body.entries.find(e=>e.id===owner.id),'hasSharedComputation'),'Legacy cards without a cached request gain no extra field');
 assert(f.db.projected.every(row=>!Object.hasOwn(row,'task_json')&&!Object.hasOwn(row,'requested_task_json')&&!Object.hasOwn(row,'result_json')));
 const explain=f.db.sqlite.prepare('EXPLAIN QUERY PLAN '+f.db.queries[0]).all();assert(explain.some(row=>row.detail.includes('local_tasks_protocol_lookup')),'Shared discovery uses the protocol expression index');
});
await test('shared status requires exact bytes/criterion/version and a public accepted source',async()=>{
 for(const variation of ['text','page','criterion','steps','alphabet','private','no-result','version','association-version','origin-version']){
  const f=fixture(),owner=await idea(f,'source-'+variation,{published:variation!=='private'}),other=await idea(f,'target-'+variation),source=await task(f,owner,180,{verified:variation!=='no-result',inputVersion:variation==='origin-version'?'reviewed':'raw'});
  const changes={title:'Requested '+variation};if(variation==='text')changes.pages=[{id:'lp2-15',text:'ᚠᚢᚦ '}];if(variation==='page')changes.pages=[{id:'lp2-16',text:'ᚠᚢᚦ'}];if(variation==='criterion')changes.criterion={kind:'exact-prefix',values:[0]};if(variation==='steps')changes.steps=[{op:'affine',a:1,b:1}];if(variation==='alphabet')changes.alphabet=source.alphabet.slice().reverse();
  if(variation==='association-version')f.db.sqlite.prepare('UPDATE local_task_ideas SET input_version=? WHERE task_id=?').run('reviewed',source.taskId);
  if(variation==='origin-version')f.db.sqlite.prepare('UPDATE local_task_ideas SET input_version=? WHERE task_id=?').run('raw',source.taskId);
  await cacheRequest(f,other,await L.prepare({...source,...changes}),{inputVersion:variation==='version'?'reviewed':'raw'});
  const entry=(await view(f)).entries.find(e=>e.id===other.id);assert(!Object.hasOwn(entry,'hasSharedComputation'),variation);
 }
});
await test('shared projection follows latest frozen request and notices later accepted results',async()=>{
 const f=fixture(),owner=await idea(f,'latest-owner'),other=await idea(f,'latest-other'),source=await task(f,owner,190),matching=await L.prepare({...source,title:'Initial matching request'});await cacheRequest(f,other,matching);
 assert(!Object.hasOwn((await view(f)).entries.find(e=>e.id===other.id),'hasSharedComputation'));
 const result=L.stable(await L.verify(source,L.run(source)));f.db.sqlite.prepare('INSERT INTO local_task_results(id,task_id,result_json,created_at,created_day) VALUES(?,?,?,?,?)').run(await digest(result),source.taskId,result,at,at.slice(0,10));
 assert.equal((await view(f)).entries.find(e=>e.id===other.id).hasSharedComputation,true);
 await cacheRequest(f,other,await L.prepare({...source,title:'Latest request is another text',pages:[{id:'lp2-15',text:'ᚦᚢᚠ'}]}),{createdAt:'2026-10-24T13:00:00.000Z'});
 assert(!Object.hasOwn((await view(f)).entries.find(e=>e.id===other.id),'hasSharedComputation'));
});
await test('task order uses association time rather than original computation time',async()=>{
 const f=fixture(),p=await idea(f,'association-order'),plans=[await task(f,p,80),await task(f,p,81)].sort((a,b)=>a.taskId.localeCompare(b.taskId));
 f.db.sqlite.prepare('UPDATE local_task_ideas SET created_at=?,created_day=? WHERE task_id=? AND proposal_id=?').run('2026-10-25T01:00:00.000Z','2026-10-25',plans[0].taskId,p.id);
 const body=await view(f);assert.deepEqual(body.entries[0].tasks.map(t=>t.id),plans.map(t=>t.taskId));
});
await test('verified total includes older accepted result outside displayed10 summaries',async()=>{
 const f=fixture(),p=await idea(f,'old-verified'),privateIdea=await idea(f,'private-verified',{published:false});
 const oldest=await task(f,p,120,{verified:true});
 f.db.sqlite.prepare('UPDATE local_task_ideas SET created_at=?,created_day=? WHERE task_id=? AND proposal_id=?').run('2026-10-23T01:00:00.000Z','2026-10-23',oldest.taskId,p.id);
 for(let i=0;i<10;i++)await task(f,p,121+i);await task(f,privateIdea,140,{verified:true});
 const body=await view(f);assert.equal(f.db.queries.length,2);assert.equal(body.entries.length,1);const entry=body.entries[0];
 assert.equal(entry.taskCount,11);assert.equal(entry.verifiedTaskCount,1);assert.equal(entry.tasks.length,10);assert(entry.tasks.every(t=>t.state==='not-run'));assert(entry.tasks.every(t=>t.id!==oldest.taskId));
 assert(!JSON.stringify(body).includes(privateIdea.id));assert(f.db.queries.every(sql=>!sql.includes('result_json')));
});
await test('migration backfill keeps existing public task visible without publishing private originals',async()=>{
 const f=fixture({relation:false}),p=await idea(f,'backfill-public'),privateIdea=await idea(f,'backfill-private',{published:false});
 const plan=await task(f,p,90,{verified:true,associateTask:false});await task(f,privateIdea,91,{associateTask:false});
 f.db.sqlite.exec(readFileSync(new URL('./migrations/0006_task_ideas.sql',import.meta.url),'utf8'));
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas').get().n,2);
 const body=await view(f);assert.equal(body.entries.length,1);assert.equal(body.entries[0].id,p.id);assert.equal(body.entries[0].taskCount,1);assert.deepEqual(body.entries[0].tasks,[{id:plan.taskId,title:plan.title,state:'results-verified'}]);
});
await test('origin, method, route and preflight gates need no mutation bindings and perform no rejected reads',async()=>{
 const f=fixture();
 for(const supplied of ['', 'https://other.example'])assert.equal((await f.handle(request('',{headers:{origin:supplied}}),f.env)).status,403);
 for(const supplied of [undefined,'not-an-origin',origin+'/path'])assert.equal((await f.handle(request(),{...f.env,SITE_ORIGIN:supplied})).status,503);
 assert.equal((await f.handle(request(),{...f.env,PROPOSALS:undefined})).status,503);
 for(const method of ['POST','PUT','DELETE','HEAD']){const response=await f.handle(request('',{method}),f.env);assert.equal(response.status,405);assert.equal(response.headers.get('Allow'),'GET, OPTIONS');}
 for(const path of ['/community-research/','/ideas','/community-research/private'])assert.equal((await f.handle(request('',{path}),f.env)).status,404);
 const preflight=await f.handle(request('',{method:'OPTIONS',headers:{'access-control-request-method':'GET','access-control-request-headers':'content-type'}}),f.env);assert.equal(preflight.status,204);assert.equal(preflight.headers.get('access-control-allow-origin'),origin);
 assert.equal((await f.handle(request('',{method:'OPTIONS',headers:{'access-control-request-method':'POST'}}),f.env)).status,403);
 assert.equal((await f.handle(request('',{method:'OPTIONS',headers:{'access-control-request-method':'GET','access-control-request-headers':'authorization'}}),f.env)).status,403);
 assert.equal(f.db.queries.length,0);
 const response=await f.handle(request(),f.env);assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(response.headers.get('vary'),'Origin');
});
await test('malformed, oversized and type-confused cursors fail before database',async()=>{
 const f=fixture(),encode=value=>btoa(JSON.stringify(value)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 const valid=encode({createdAt:at,id:'p_'+'0'.repeat(64)});
 const bad=['?before=invalid','?before=','?before='+('a'.repeat(241)),'?other=1','?before='+valid+'&before='+valid,
  ...[{createdAt:'2026-99-01',id:'p_'+'0'.repeat(64)},{createdAt:at,id:['p_'+'0'.repeat(64)]},{createdAt:at,id:'0'.repeat(64)},{createdAt:at,id:'p_'+'0'.repeat(64),extra:true}].map(value=>'?before='+encode(value))];
 for(const query of bad)assert.equal((await f.handle(request(query),f.env)).status,400,query);
 assert.equal(f.db.queries.length,0);assert.equal((await f.handle(request('?before='+valid),f.env)).status,200);
});
await test('corrupt cards, task identities/titles and SQL failures fail closed with no private details',async()=>{
 for(const mutate of [async(f,p)=>f.db.sqlite.prepare('UPDATE proposals SET card_hash=? WHERE id=?').run('0'.repeat(64),p.id),
  async(f,p)=>{const plan=await task(f,p,4);f.db.sqlite.prepare('UPDATE local_tasks SET task_json=? WHERE id=?').run(JSON.stringify({...plan,taskId:'0'.repeat(64)}),plan.taskId);},
  async(f,p)=>{const plan=await task(f,p,4);f.db.sqlite.prepare('UPDATE local_tasks SET task_json=? WHERE id=?').run(JSON.stringify({...plan,title:'x'.repeat(301)}),plan.taskId);},
  async(f,p)=>{const plan=await task(f,p,4);f.db.sqlite.exec('DROP INDEX local_tasks_protocol_lookup');f.db.sqlite.prepare('UPDATE local_tasks SET task_json=? WHERE id=?').run('not valid json',plan.taskId);},
  async(f)=>{f.db.fail=true;}]){
  const f=fixture(),p=await idea(f,4);await mutate(f,p);const response=await f.handle(request(),f.env);assert.equal(response.status,503);const body=await response.json();assert(!JSON.stringify(body).includes('PRIVATE'));assert(!Object.hasOwn(body,'entries'));
 }
});
console.log('PASS '+groups+' community feed groups: SQLite migrations1–6 and11; read-only indexed shared metadata; no network/model/deploy.');
