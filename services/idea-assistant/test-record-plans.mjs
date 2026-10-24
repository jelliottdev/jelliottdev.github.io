/* Offline official-source fixtures and real SQLite. No AI or target execution. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
import {createRecordPlanHandler,loadRecordPlan,validOrigin,recordPlanDigest as sha} from './record-plans.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const known=v=>C.field('specified',v,{kind:'supplied',refs:['source:text']});
const alphabet=Array.from({length:29},(_,i)=>({rune:String.fromCodePoint(0x16a0+i),latin:'R'+i,prime:i+2}));
async function fixture(){
 const card=H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic authored fixture'},aim:known('Test a fixed opening'),method:known({operations:[{id:'reverse_runes',label:'Reverse rune order within each line',unit:'line'}]}),scope:known({pages:['lp2-15']}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:[2,1,0]})}}),{id:'test',at}));
 const text=alphabet[0].rune+alphabet[1].rune+alphabet[2].rune,steps=[{op:'reverse',unit:'line'}],criterion={kind:'exact-prefix',values:[2,1,0]};
 const controlTask=await L.prepare({title:'Synthetic recovery fixture',pages:[{id:'lp1-00',text}],alphabet,steps,criterion});
 const recipe={id:'synthetic-example',title:'Reviewed reversal',question:'Does the fixed opening match?',scope_change:'Apply the stated operation to this page.',limitation:'A prefix comparison only.',card,inputs:{version:'raw',alphabet_sha256:await sha(L.stable(alphabet)),pages:[{id:'lp2-15',text_sha256:await sha(text)}]},control:{label:'Synthetic exact recovery',task:controlTask,expected_result_sha256:await sha(L.stable(L.run(controlTask)))}};
 const record={id:'example-record',status:'published',browser_followups:[recipe]},files=new Map([['/experiments/records/example-record/record.json',record],['/data/index.json',{alphabet}],['/data/pages/lp2-15.json',{id:'lp2-15',raw:text}]]),calls=[],signals=[];
 const fetcher=async(url,options)=>{const u=new URL(url);assert.equal(u.origin,origin);assert.equal(options.redirect,'manual');assert(options.signal);calls.push(u.pathname);signals.push(options.signal);const v=files.get(u.pathname);if(v instanceof Response)return v;if(v===undefined)throw Error('Unavailable');return Response.json(v);};
 return {card,recipe,record,files,fetcher,calls,signals};
}
const request=(data,extra={})=>new Request('https://worker.example/record-plans',{method:'POST',headers:{origin,'content-type':'application/json',...extra},body:JSON.stringify(data)});
const args={recordId:'example-record',followupId:'synthetic-example'};
const env={SITE_ORIGIN:origin,TASK_LIMIT:{limit:async()=>({success:true})}};
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
await test('authored source, exact pins and synthetic control prepare without AI or target evaluation',async()=>{
 const f=await fixture(),before=structuredClone(f.record),response=await createRecordPlanHandler({fetcher:f.fetcher})(request(args),env),plan=await response.json();assert.equal(response.status,200);assert.equal(plan.state,'plan-ready');assert.deepEqual(plan.card,f.card);assert.deepEqual(plan.control,f.recipe.control);assert.equal(plan.origin.protocolSha256,await sha(L.stable(f.recipe)));assert.equal(plan.origin.recordSha256,await sha(JSON.stringify(f.record)));assert(!('snapshot'in plan));assert.deepEqual(plan.task.steps,f.recipe.control.task.steps);assert.equal(plan.inputVersion,'raw');assert.equal(f.calls.length,3);assert.deepEqual(f.record,before);await L.checkIdentity(plan.task);
});
await test('strict route/origin/method/body and rate guard run before all source access',async()=>{
 const f=await fixture(),handle=createRecordPlanHandler({fetcher:f.fetcher});
 assert.equal((await handle(request(args,{origin:'https://evil.example'}),env)).status,403);
 assert.equal((await handle(request(args),{...env,TASK_LIMIT:null})).status,503);
 assert.equal((await handle(request(args),{...env,TASK_LIMIT:{limit:async()=>({success:false})}})).status,429);
 for(const body of [{...args,extra:true},{recordId:'../secret',followupId:args.followupId},{...args,followupId:'x'.repeat(101)}])assert.equal((await handle(request(body),env)).status,400);
 assert.equal((await handle(request({padding:'x'.repeat(1024)}),env)).status,400);
 assert.equal((await handle(new Request('https://worker.example/record-plans',{headers:{origin}}),env)).status,405);
 assert.equal((await handle(new Request('https://worker.example/record-plans?x=1',{headers:{origin}}),env)).status,404);
 const pre=new Request('https://worker.example/record-plans',{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}});assert.equal((await handle(pre,env)).status,204);assert.equal(f.calls.length,0);
});
await test('changed source, alphabet, rules, criterion and control cannot become reviewed plans',async()=>{
 const mutations=[f=>f.record.status='draft',f=>f.record.id='other',f=>f.record.browser_followups.push(structuredClone(f.recipe)),f=>f.recipe.extra=true,f=>f.recipe.inputs.pages[0].text_sha256='0'.repeat(64),f=>f.recipe.inputs.alphabet_sha256='0'.repeat(64),f=>f.recipe.inputs.version='reviewed',f=>f.recipe.card.rules.evaluation=C.field(),f=>f.recipe.card.rules.inputVersion=C.field(),f=>f.recipe.card.rules.representation=C.field(),f=>f.recipe.control.expected_result_sha256='0'.repeat(64),f=>f.recipe.control.task.title='tampered',f=>f.recipe.card.rules.exceptionalCases=known('Except F'),f=>f.recipe.card.method.value.operations[0].unit='word'];
 for(const mutate of mutations){const f=await fixture();mutate(f);assert.equal((await createRecordPlanHandler({fetcher:f.fetcher})(request(args),env)).status,422);}
 const f=await fixture();f.recipe.control.task=await L.prepare({...f.recipe.control.task,steps:[{op:'reverse',unit:'word'}]});f.recipe.control.expected_result_sha256=await sha(L.stable(L.run(f.recipe.control.task)));await assert.rejects(()=>loadRecordPlan(args,{fetcher:f.fetcher}));
 const failed=await fixture();failed.recipe.control.task=await L.prepare({...failed.recipe.control.task,pages:[{id:'lp1-00',text:alphabet[0].rune.repeat(3)}]});failed.recipe.control.expected_result_sha256=await sha(L.stable(L.run(failed.recipe.control.task)));await assert.rejects(()=>loadRecordPlan(args,{fetcher:failed.fetcher}),/control failed/);
});
await test('raw record byte pin includes BOM and page batches share four-worker bound',async()=>{
 const f=await fixture(),bytes=new TextEncoder().encode('\ufeff'+JSON.stringify(f.record));f.files.set('/experiments/records/example-record/record.json',new Response(bytes,{headers:{'content-type':'application/json'}}));const plan=await loadRecordPlan(args,{fetcher:f.fetcher});assert.equal(plan.origin.recordSha256,await sha(bytes));assert.notEqual(plan.origin.recordSha256,await sha(JSON.stringify(f.record)));
 const g=await fixture(),text=g.files.get('/data/pages/lp2-15.json').raw,ids=Array.from({length:9},(_,i)=>'lp2-'+String(i).padStart(2,'0'));g.card.scope.value.pages=ids;g.recipe.inputs.pages=await Promise.all(ids.map(async id=>({id,text_sha256:await sha(text)})));for(const id of ids)g.files.set('/data/pages/'+id+'.json',{id,raw:text});let active=0,max=0;
 const fetcher=async(url,options)=>{if(url.includes('/data/pages/')){active++;max=Math.max(max,active);await new Promise(r=>setTimeout(r,1));active--;}return g.fetcher(url,options);};const batch=await loadRecordPlan(args,{fetcher});assert.equal(max,4);assert.deepEqual(batch.task.pages.map(p=>p.id),ids);assert(g.signals.every(s=>s===g.signals[0]));
});
await test('source redirects, malformed/oversized streams and shared deadline fail closed',async()=>{
 for(const response of [new Response(null,{status:302,headers:{location:'https://evil.example'}}),new Response('{',{headers:{'content-type':'application/json'}}),new Response(' '.repeat(512*1024+1),{headers:{'content-type':'application/json'}})]){const f=await fixture();f.files.set('/experiments/records/example-record/record.json',response);assert.equal((await createRecordPlanHandler({fetcher:f.fetcher})(request(args),env)).status,422);assert.equal(f.calls.length,1);}
 let signal;const handle=createRecordPlanHandler({timeoutMs:5,fetcher:async(_,options)=>{signal=options.signal;return new Promise(()=>{});}});const response=await handle(request(args),env);assert.equal(response.status,422);assert.equal(signal.aborted,true);
});
await test('actual authored recipe compiles and verifies its control using pinned published files only',async()=>{
 const path='lp2-known-vigenere-keys',record=JSON.parse(readFileSync(new URL('../../experiments/records/'+path+'/record.json',import.meta.url),'utf8'));
 const recipe=record.browser_followups?.[0];assert(recipe,'Authored recipe exists');
 const fetcher=async(url,options)=>{assert.equal(options.redirect,'manual');const pathname=new URL(url).pathname;return new Response(readFileSync(new URL('../..'+pathname,import.meta.url)),{headers:{'content-type':'application/json'}});};
 const plan=await loadRecordPlan({recordId:path,followupId:recipe.id},{fetcher});assert.equal(plan.task.pages.length,55);assert.deepEqual(plan.task.steps,recipe.control.task.steps);assert.deepEqual(plan.card,recipe.card);assert(plan.control.task.pages.every(p=>p.id!=='lp2-50'));
});
function database(){const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));return {sqlite,prepare(sql){return {bind(...args){return {sql,args,first:async()=>sqlite.prepare(sql).get(...args)||null};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{const result=statements.map(s=>({meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return result;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};}
await test('origins bind exact card/task, persist immutable snapshots and project public associations only',async()=>{
 const f=await fixture(),plan=await loadRecordPlan(args,{fetcher:f.fetcher}),db=database(),id='p_'+'a'.repeat(64),privateId='p_'+'b'.repeat(64),handler=createLocalTaskHandler({fetcher:f.fetcher,now:()=>new Date(at)}),taskEnv={...env,PROPOSALS:db};
 for(const pid of [id,privateId])db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(pid,pid.slice(2),L.stable(f.card),'private-fragment',at);
 const post=async(body)=>handler(new Request('https://worker.example/tasks',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(body)}),taskEnv),base={proposalId:privateId,task:plan.task,inputVersion:'raw',parentTaskId:null,origin:plan.origin};
 assert(validOrigin(plan.origin),JSON.stringify(plan.origin));await L.checkIdentity(base.task);
 let response=await post(base);assert.equal(response.status,200);assert.deepEqual((await response.json()).origins,[],'Private association origin is not projected');
 db.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(id,at,at.slice(0,10));response=await post({...base,proposalId:id});assert.equal(response.status,200);const value=await response.json();assert.equal(value.origins.length,1);assert.deepEqual(value.origins[0],{origin:plan.origin,control:plan.control,question:plan.question,scopeChange:plan.scopeChange,limitation:plan.limitation});assert(!JSON.stringify(value).includes(privateId));assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
 assert.equal((await post({...base,proposalId:id})).status,200);assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_origins').get().n,2);
 assert.throws(()=>db.sqlite.prepare("UPDATE local_task_origins SET snapshot_json='{}'").run(),/immutable/);
 const badOrigin={...plan.origin,recordSha256:'0'.repeat(64)};assert.equal((await post({...base,proposalId:id,origin:badOrigin})).status,422);
 const differentTask=await L.prepare({...plan.task,title:'Changed title'});assert.equal((await post({...base,proposalId:id,task:differentTask})).status,422);
 const otherCard=structuredClone(f.card);otherCard.scope.value.pages=['lp2-14'];db.sqlite.prepare('UPDATE proposals SET card_json=? WHERE id=?').run(L.stable(otherCard),id);assert.equal((await post({...base,proposalId:id})).status,422);db.sqlite.prepare('UPDATE proposals SET card_json=? WHERE id=?').run(L.stable(f.card),id);
 // A second recipe may produce the exact same task without overwriting provenance.
 f.recipe.id='another-origin';const second=await loadRecordPlan({...args,followupId:f.recipe.id},{fetcher:f.fetcher});assert.equal(second.task.taskId,plan.task.taskId);assert.equal((await post({...base,proposalId:id,origin:second.origin})).status,200);
 f.record.status='draft';const get=await handler(new Request('https://worker.example/tasks/'+plan.task.taskId,{headers:{origin}}),taskEnv);assert.equal(get.status,200);const saved=await get.json();assert.equal(saved.origins.length,2);assert.deepEqual(saved.origins[0].control,plan.control);assert(!JSON.stringify(saved).includes(privateId));
 // Generic creation never copies existing reviewed origins to another idea.
 const third='p_'+'c'.repeat(64);db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(third,third.slice(2),L.stable(f.card),'unused',at);assert.equal((await post({...base,proposalId:third,origin:undefined})).status,200);assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_origins WHERE proposal_id=?').get(third).n,0);
 f.record.status='published';for(let i=0;i<10;i++){f.recipe.id='extra-origin-'+i;const extra=await loadRecordPlan({...args,followupId:f.recipe.id},{fetcher:f.fetcher}),response=await post({...base,proposalId:id,origin:extra.origin});assert.equal(response.status,200);const saved=await response.json();assert.deepEqual(saved.card,f.card,'POST card keeps the requested linked idea context');assert(saved.origins.length<=10);assert.deepEqual(saved.origins[0].origin,extra.origin,'POST prioritizes the exact requested origin even beyond the public cap');if(i>=8)assert.equal(saved.originsTruncated,true);}
 const bounded=await (await handler(new Request('https://worker.example/tasks/'+plan.task.taskId,{headers:{origin}}),taskEnv)).json();assert.equal(bounded.origins.length,10);assert.equal(bounded.originsTruncated,true);assert(!JSON.stringify(bounded).includes(privateId));
 const sorted=await (await handler(new Request('https://worker.example/tasks/'+plan.task.taskId,{headers:{origin}}),taskEnv)).json();assert.deepEqual(sorted.origins,bounded.origins,'GET keeps stable bounded ordering without a preferred POST origin');
 db.sqlite.close();
});
console.log('PASS '+groups+' authored record-plan groups; official sources mocked, controls only, no hosted calls.');
