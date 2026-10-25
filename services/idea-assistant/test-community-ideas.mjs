import {applyMigrations} from './sqlite-test-migrations.mjs';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import C from '../../claim-specification.js';
import S from '../../claim-share.js';
import L from '../../local-experiment.js';
import {canonicalProposal} from './proposals.mjs';
import {createCommunityIdeaHandler} from './community-ideas.mjs';

const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
function fixture(){
 const sqlite=new DatabaseSync(':memory:');
 applyMigrations(sqlite);
 const db={sqlite,reads:0,fail:false,queries:[],projected:[],prepare(sql){db.queries.push(sql);return {bind(...args){return {sql,args,
  first:async()=>{db.reads++;return sqlite.prepare(sql).get(...args)||null;},
  all:async()=>{db.reads++;const results=sqlite.prepare(sql).all(...args);db.projected.push(...results);return {results};}};}};},async batch(statements){
  sqlite.exec('BEGIN IMMEDIATE');try{if(db.fail)throw Error('PRIVATE database failure');const result=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return result;}catch(error){sqlite.exec('ROLLBACK');throw error;}
 }};
 let day=at;const rates=[];const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async value=>{rates.push(value);return {success:true};}}};
 return {db,env,rates,setDay:value=>{day=value;},handle:createCommunityIdeaHandler({now:()=>new Date(day)})};
}
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
async function proposal(f,key='FOO'){
 const draft=C.createDraft({source:{text:'PRIVATE original prompt',materials:[{name:'PRIVATE file'}]},aim:known('solve LP2'),
  method:known({operations:[{id:'vigenere',label:'Vigenere',key,sourceText:'PRIVATE extraction'}]}),scope:known({pages:['lp2-15']})});
 const fragment=S.encode(C.confirm(draft,{id:'PRIVATE confirmation',at}));
 const p=await canonicalProposal({requestId:crypto.randomUUID(),fragment,originalIdea:'PRIVATE original wording',note:'PRIVATE note',sourceUrl:'https://github.com/example/project'});
 f.db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(p.id,p.cardHash,p.cardJson,p.fragment,at);
 f.db.sqlite.prepare('INSERT INTO proposal_submissions(request_id,proposal_id,request_hash,note,source_url,received_at,received_day,original_idea) VALUES(?,?,?,?,?,?,?,?)').run(p.requestId,p.id,p.requestHash,p.note,p.sourceUrl,at,at.slice(0,10),p.originalIdea);
 return p;
}
function request(path='/ideas',{method='POST',body,headers={}}={}){
 return new Request('https://worker.example'+path,{method,headers:{origin,...(method==='POST'?{'content-type':'application/json'}:{}),...headers},...(body!==undefined?{body:JSON.stringify(body)}:{})});
}
const post=id=>request('/ideas',{body:{proposalId:id}}),get=(id,query='')=>request('/ideas/'+id+query,{method:'GET'});
async function task(f,p,i,{verified=false,createdAt=at}={}){
 const plan=await L.prepare({title:'Task '+i,alphabet:Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ').map((rune,n)=>({rune,latin:'R'+n,prime:n+2})),
  pages:[{id:'lp2-15',text:'ᚠᚢᚦ'}],steps:[],criterion:{kind:'measurement'}});
 const text=L.stable(plan);
 f.db.sqlite.prepare('INSERT INTO local_tasks(id,task_hash,create_hash,proposal_id,card_json,task_json,input_version,parent_task_id,created_at,created_day) VALUES(?,?,?,?,?,?,?,?,?,?)')
  .run(plan.taskId,await digest(text),'0'.repeat(64),p.id,p.cardJson,text,'raw',null,createdAt,createdAt.slice(0,10));
 associate(f,p,plan,createdAt);
 if(verified){const result=L.stable(await L.verify(plan,L.run(plan)));f.db.sqlite.prepare('INSERT INTO local_task_results(id,task_id,result_json,created_at,created_day) VALUES(?,?,?,?,?)').run(await digest(result),plan.taskId,result,at,at.slice(0,10));}
 return plan;
}
function associate(f,p,plan,createdAt=at){f.db.sqlite.prepare('INSERT INTO local_task_ideas(task_id,proposal_id,input_version,parent_task_id,created_at,created_day) VALUES(?,?,?,?,?,?)').run(plan.taskId,p.id,'raw',null,createdAt,createdAt.slice(0,10));}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}

await test('migration never publishes old private proposals; explicit entry exposes normalized card only',async()=>{
 const f=fixture(),p=await proposal(f);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,0);
 assert.equal((await f.handle(get(p.id),f.env)).status,404);
 const response=await f.handle(post(p.id),f.env),body=await response.json();assert.equal(response.status,200);
 assert.deepEqual(body.card,JSON.parse(p.cardJson));assert.equal(body.id,p.id);assert.equal(body.createdAt,at);assert.deepEqual(body.tasks,[]);assert.equal(body.tasksTruncated,false);assert.equal(body.nextCursor,null);
 for(const secret of ['PRIVATE','original_idea','fragment','note','source_url','request_hash'])assert(!JSON.stringify(body).includes(secret),secret);
 const retry=await(await f.handle(post(p.id),f.env)).json();assert.deepEqual(retry,body);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,1);
 const before=f.db.sqlite.prepare('SELECT * FROM proposal_submissions').all();await f.handle(get(p.id),f.env);assert.deepEqual(f.db.sqlite.prepare('SELECT * FROM proposal_submissions').all(),before);
});
await test('same-site CORS, methods, routes, bindings and no list endpoint fail closed',async()=>{
 const f=fixture(),p=await proposal(f);
 for(const value of ['', 'https://other.example'])assert.equal((await f.handle(request('/ideas',{body:{proposalId:p.id},headers:{origin:value}}),f.env)).status,403);
 assert.equal((await f.handle(post(p.id),{...f.env,SITE_ORIGIN:undefined})).status,503);
 assert.equal((await f.handle(post(p.id),{...f.env,PROPOSALS:undefined})).status,503);
 assert.equal((await f.handle(post(p.id),{...f.env,TASK_LIMIT:undefined})).status,503);
 assert.equal((await f.handle(request('/ideas',{method:'GET'}),f.env)).status,405);
 assert.equal((await f.handle(request('/ideas/'+p.id,{body:{proposalId:p.id}}),f.env)).status,405);
 for(const path of ['/ideas/','/ideas/not-an-id','/ideas/'+p.id+'/extra','/other'])assert.equal((await f.handle(request(path,{method:'GET'}),f.env)).status,404);
 for(const [path,method]of [['/ideas','POST'],['/ideas/'+p.id,'GET']]){
  const response=await f.handle(request(path,{method:'OPTIONS',headers:{'access-control-request-method':method,'access-control-request-headers':'content-type'}}),f.env);
  assert.equal(response.status,204);assert.equal(response.headers.get('access-control-allow-origin'),origin);
 }
 assert.equal((await f.handle(request('/ideas',{method:'OPTIONS',headers:{'access-control-request-method':'POST','access-control-request-headers':'authorization'}}),f.env)).status,403);
 assert.equal(f.rates.length,0);assert.equal(f.db.reads,0);
});
await test('mutations rate-limit before every DB access, including retries; fallback limiter works',async()=>{
 const f=fixture(),p=await proposal(f);const denied={...f.env,TASK_LIMIT:{limit:async()=>({success:false})}};
 assert.equal((await f.handle(post(p.id),denied)).status,429);assert.equal(f.db.reads,0);
 const fallback={...f.env,TASK_LIMIT:undefined,PROPOSAL_LIMIT:f.env.TASK_LIMIT};assert.equal((await f.handle(post(p.id),fallback)).status,200);
 const reads=f.db.reads;assert.equal((await f.handle(post(p.id),denied)).status,429);assert.equal(f.db.reads,reads);
 assert.equal((await f.handle(get(p.id),{...f.env,TASK_LIMIT:undefined})).status,200,'Read-only fetch needs no mutation limiter');
});
await test('daily cap atomic under concurrent inserts and retries do not consume slots',async()=>{
 const f=fixture(),proposals=[];for(let i=0;i<60;i++)proposals.push(await proposal(f,'KEY'+i));
 const responses=await Promise.all(proposals.map(p=>f.handle(post(p.id),f.env)));
 assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,10);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,50);
 const saved=f.db.sqlite.prepare('SELECT proposal_id FROM research_ideas LIMIT 1').get().proposal_id;
 assert.equal((await f.handle(post(saved),f.env)).status,200);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,50);
 const unsaved=proposals.find((p,i)=>responses[i].status===429);
 f.setDay('2026-10-25T00:00:01.000Z');assert.equal((await f.handle(post(unsaved.id),f.env)).status,200);
 const g=fixture(),p=await proposal(g);const duplicate=await Promise.all(Array.from({length:8},()=>g.handle(post(p.id),g.env)));assert(duplicate.every(r=>r.status===200));assert.equal(g.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,1);
});
await test('bounded task summaries crosscheck embedded IDs and accepted results without fetching plans or results',async()=>{
 const f=fixture(),p=await proposal(f),other=await proposal(f,'OTHER');await f.handle(post(p.id),f.env);
 const a=await task(f,p,1),b=await task(f,p,2,{verified:true});await task(f,other,3,{verified:true});
 const body=await(await f.handle(get(p.id),f.env)).json();assert.equal(body.tasks.length,2);
 const byId=new Map(body.tasks.map(t=>[t.id,t]));assert.deepEqual(byId.get(a.taskId),{id:a.taskId,title:'Task 1',state:'not-run'});assert.deepEqual(byId.get(b.taskId),{id:b.taskId,title:'Task 2',state:'results-verified'});
 assert(body.tasks.every(t=>Object.keys(t).sort().join(',')==='id,state,title'));assert(!JSON.stringify(body).includes('task_json'));
 const sql=f.db.queries.find(q=>q.includes('FROM local_task_ideas a'));
 assert.match(sql,/json_extract\(t.task_json,'\$\.title'\) AS title/);assert.match(sql,/json_extract\(t.task_json,'\$\.taskId'\) AS embedded_id/);
 assert.doesNotMatch(sql,/\bSELECT\s+\*|\bid\s*,\s*task_hash\s*,\s*task_json/);assert(f.db.queries.every(q=>!q.includes('result_json')));
 assert(f.db.projected.every(row=>!Object.hasOwn(row,'task_json')&&!Object.hasOwn(row,'result_json')));
 f.db.sqlite.prepare('UPDATE local_tasks SET task_json=? WHERE id=?').run(JSON.stringify({...a,taskId:'0'.repeat(64)}),a.taskId);
 assert.equal((await f.handle(get(p.id),f.env)).status,503);
});
await test('bounded50 summaries use stable validated cursor with no loss or duplicates',async()=>{
 const f=fixture(),p=await proposal(f);await f.handle(post(p.id),f.env);for(let i=0;i<52;i++)await task(f,p,i);
 const one=await(await f.handle(get(p.id),f.env)).json();assert.equal(one.tasks.length,50);assert.equal(one.tasksTruncated,true);assert.equal(typeof one.nextCursor,'string');
 const two=await(await f.handle(get(p.id,'?before='+one.nextCursor),f.env)).json();assert.equal(two.tasks.length,2);assert.equal(two.tasksTruncated,false);assert.equal(two.nextCursor,null);assert.equal(new Set([...one.tasks,...two.tasks].map(t=>t.id)).size,52);
 for(const query of ['?before=invalid','?before='+one.nextCursor+'&before='+one.nextCursor,'?other=1','?before='+btoa(JSON.stringify({createdAt:at,id:'bad'}))])assert.equal((await f.handle(get(p.id,query),f.env)).status,400);
 const arrayCursor=btoa(JSON.stringify({createdAt:at,id:['0'.repeat(64)]})).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 assert.equal((await f.handle(get(p.id,'?before='+arrayCursor),f.env)).status,400);
});
await test('one computation appears under every linked public idea without publishing private associations',async()=>{
 const f=fixture(),one=await proposal(f,'ONE'),two=await proposal(f,'TWO'),privateIdea=await proposal(f,'PRIVATE-ASSOCIATION');
 await f.handle(post(one.id),f.env);await f.handle(post(two.id),f.env);
 const plan=await task(f,one,80,{verified:true});associate(f,two,plan,'2026-10-25T01:00:00.000Z');associate(f,privateIdea,plan);
 for(const p of [one,two]){const response=await f.handle(get(p.id),f.env);assert.equal(response.status,200);const body=await response.json();assert.deepEqual(body.tasks,[{id:plan.taskId,title:plan.title,state:'results-verified'}]);}
 assert.equal((await f.handle(get(privateIdea.id),f.env)).status,404);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_ideas').get().n,3);
});
await test('per-idea task order uses first association timestamp rather than task origin',async()=>{
 const f=fixture(),p=await proposal(f,'ORDER');await f.handle(post(p.id),f.env);
 const plans=[await task(f,p,90),await task(f,p,91)].sort((a,b)=>a.taskId.localeCompare(b.taskId));
 f.db.sqlite.prepare('UPDATE local_task_ideas SET created_at=?,created_day=? WHERE task_id=? AND proposal_id=?').run('2026-10-25T01:00:00.000Z','2026-10-25',plans[0].taskId,p.id);
 const body=await(await f.handle(get(p.id),f.env)).json();assert.deepEqual(body.tasks.map(t=>t.id),plans.map(t=>t.taskId));
});
await test('malicious and oversized bodies never persist; storage errors do not leak',async()=>{
 const f=fixture(),p=await proposal(f);
 for(const body of [{proposalId:p.id,original_idea:'PRIVATE'},{proposalId:p.id,note:'private'},{proposalId:'p_'+'A'.repeat(64)},{proposalId:12},[],null,{}])assert.equal((await f.handle(request('/ideas',{body}),f.env)).status,400);
 assert.equal((await f.handle(request('/ideas',{body:{proposalId:p.id},headers:{'content-type':'text/plain'}}),f.env)).status,400);
 const stream=new ReadableStream({start(controller){controller.enqueue(new TextEncoder().encode('x'.repeat(1025)));controller.close();}});
 const oversized=new Request('https://worker.example/ideas',{method:'POST',headers:{origin,'content-type':'application/json'},body:stream,duplex:'half'});assert.equal((await f.handle(oversized,f.env)).status,400);
 for(const text of [`{"proposalId":"${p.id}","proposalId":"${p.id}"}`,`{"proposalId":"${p.id}","proposal\\u0049d":"${p.id}"}`]){
  const duplicate=new Request('https://worker.example/ideas',{method:'POST',headers:{origin,'content-type':'application/json'},body:text});assert.equal((await f.handle(duplicate,f.env)).status,400);
 }
 assert.equal(f.db.reads,0);assert.equal(f.rates.length,0);
 assert.equal((await f.handle(post('p_'+'0'.repeat(64)),f.env)).status,404);
 f.db.fail=true;const response=await f.handle(post(p.id),f.env);assert.equal(response.status,503);assert(!JSON.stringify(await response.json()).includes('PRIVATE'));assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,0);
});
await test('corrupt proposal identity never publishes or returns a public card',async()=>{
 const f=fixture(),p=await proposal(f);f.db.sqlite.prepare('UPDATE proposals SET card_hash=? WHERE id=?').run('0'.repeat(64),p.id);
 assert.equal((await f.handle(post(p.id),f.env)).status,503);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM research_ideas').get().n,0);
});
console.log('PASS '+groups+' community-idea groups: real SQLite migrations1–6; no remote calls, mutations, model or deploy.');
