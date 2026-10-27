/* Private durable authorization checks. Invented selected input; no hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import MD from '../../method-design.js';
import MI from '../../method-implementation.js';
import V from '../../declarative-rune-program.js';
import D from '../../local-experiment-dispatch.js';
import Controls from '../../local-plan-controls-dispatch.js';
import OldControls from '../../local-plan-controls.js';
import {issue} from './prepared-plans.mjs';
import {applyMigrations} from './sqlite-test-migrations.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
const hash=v=>createHash('sha256').update(C.serialize(v)).digest('hex'),at='2026-10-27T12:00:00.000Z',f=v=>C.field('specified',v);
async function fixture(){
 const sqlite=new DatabaseSync(':memory:');applyMigrations(sqlite);
 const db={prepare(sql){return {bind(...args){return {sql,args,first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{const rows=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return rows;}catch(e){sqlite.exec('ROLLBACK');throw e;}}},bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),a=bundle.alphabet[0].rune;
 bundle.pages.find(p=>p.id==='lp2-00').raw=a+a+a+' '+a+a;
 const parent=H.cardData(C.confirm(C.createDraft({source:{text:'Could extra repeated runes be padding?'},aim:f('Measure'),method:f({operations:[{id:'affine',a:1,b:0}]}),scope:f({pages:['lp2-00']}),rules:{inputVersion:f('raw'),evaluation:f('measurement')}}),{id:'fixture',at}));
 const proposal={schema:MD.SCHEMA,name:'Repeated-rune removal',hypothesis:'Measure output after collapsing repeated runs.',pages:['lp2-00'],inputVersion:'raw',representation:'Runes in page order, using alphabet indices zero through twenty-eight',keyUse:{kind:'not-used',material:'',application:''},steps:['Within each word keep the first rune of each equal run.'],parameters:[],evaluation:'Count runes and adjacent rune pairs in the output.',controls:['Check an invented triple repeat and separators.'],assumptions:['This measurement alone cannot identify filler.']};
 const draft=await MD.toDraft(proposal,{parentId:'p_'+hash(parent),parentCard:parent}),card=H.cardData(C.confirm(draft,{id:'fixture',at})),proposalId='p_'+hash(card);
 const coverage=[...proposal.steps.map((_,index)=>({part:'step',index})),...['evaluation','key-use','representation'].map(part=>({part,index:0})),...proposal.controls.map((_,index)=>({part:'control',index}))].map(item=>({...item,status:'implemented',programSteps:item.part==='step'?[1]:[],note:'Explicit calculation mapping for this invented fixture.'}));
 const implementation={schema:MI.SCHEMA,proposalSha256:hash(proposal),steps:[{op:'collapse-adjacent-repeats',unit:'word',policy:'all-but-first'}],criterion:{kind:'measurement'},coverage,issues:[]},token=await MI.bind({proposal,implementation}),task=await V.prepare(MI.compileBody(token,{bundle})),controls=await Controls.prepare(task),basis={kind:'method-implementation-v1',implementation,review:{schema:'liberpedia-method-implementation-review-v1',proposalSha256:hash(proposal),implementationSha256:hash(implementation)}};
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,hash(card),C.serialize(card),'unused',at);
 sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(proposalId,at,at.slice(0,10));
 let reads=0;const fetcher=async(url,options)=>{reads++;assert.equal(url,'https://jelliottdev.github.io/data/local-run-inputs.json');assert.equal(options.redirect,'manual');return new Response(JSON.stringify(bundle),{headers:{'Content-Type':'application/json'}});};
 return {sqlite,bundle,implementation,proposal,reads:()=>reads,args:{db,proposalId,card,task,inputVersion:'raw',parentTaskId:null,controls,authority:'idea',basis,createdAt:at,fetcher}};
}

const origin='https://jelliottdev.github.io';
function request(path,method='GET',body,signal){return new Request('https://worker.example'+path,{method,headers:{origin,...(body!==undefined?{'Content-Type':'application/json'}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{}),...(signal?{signal}:{})});}
async function setup(){
 const x=await fixture();x.receipt=await issue(x.args);
 x.env={SITE_ORIGIN:origin,PROPOSALS:x.args.db,PROPOSAL_LIMIT:{limit:async()=>({success:true})}};
 x.handle=createLocalTaskHandler({fetcher:x.args.fetcher,now:()=>new Date(at),discoverEvidence:()=>{throw Error('V2 cannot borrow legacy coverage');},prepareControls:()=>{throw Error('V2 cannot use V1 control memo/cache');}});
 x.body={proposalId:x.args.proposalId,task:x.args.task,inputVersion:'raw',parentTaskId:null,preparationId:x.receipt.id};
 x.call=(path,method,body,signal)=>x.handle(request(path,method,body,signal),x.env);
 x.taskPath='/tasks/'+x.args.task.taskId;x.resultPath=x.taskPath+'/results';
 return x;
}
async function status(response,expected){assert.equal(response.status,expected,await response.clone().text());return response.json();}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('reviewed V2 task saves, executes invented text, persists and independently reloads exact alignment',async()=>{
 const x=await setup(),projection=await status(await x.call('/tasks','POST',x.body),200);
 assert.equal(projection.state,'not-run');assert.deepEqual(projection.plan,x.args.task);assert.equal(projection.controls.version,2);assert.deepEqual(projection.origins,[]);
 for(const key of ['coverage','coverageUnavailable','reviewedProgram','selectedRecordOrigin'])assert(!Object.hasOwn(projection,key));
 const result=V.run(x.args.task);assert.equal(result.transformed[0].text,x.args.task.alphabet[0].rune+' '+x.args.task.alphabet[0].rune);
 const saved=await status(await x.call(x.resultPath,'POST',{result}),200);assert.equal(saved.state,'results-verified');assert.equal(saved.latestRun.id,hash(result));assert.deepEqual(saved.latestRun.result,result);
 const loaded=await status(await x.call(x.taskPath+'?idea='+x.args.proposalId),200);assert.deepEqual(loaded.latestRun,saved.latestRun);assert.deepEqual(loaded.plan,x.args.task);assert.equal(loaded.card.method.value.operations[0].id,'described_method');
 await status(await x.call('/tasks','POST',x.body),200);await status(await x.call(x.resultPath,'POST',{result}),200);
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,1);
});
await test('preparation is mandatory even for an existing link; fresh source and exact card scope program remain binding',async()=>{
 const x=await setup(),{preparationId,...missing}=x.body;
 await status(await x.call('/tasks','POST',missing),409);
 for(const mutate of [t=>t.pages[0].text+='!',t=>t.pages[0].id='lp2-01',t=>t.steps[0].policy='non-overlapping-pairs',t=>t.criterion={kind:'exact-prefix',values:[0]}]){
  const task=structuredClone(x.args.task);mutate(task);task.taskId=await V.identity(task);await status(await x.call('/tasks','POST',{...x.body,task}),409);
 }
 const otherCard=structuredClone(x.args.card);otherCard.method.value.operations[0].label='Another proposed procedure';const otherId='p_'+hash(otherCard);
 x.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(otherId,hash(otherCard),C.serialize(otherCard),'unused',at);
 x.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(otherId,at,at.slice(0,10));
 await status(await x.call('/tasks','POST',{...x.body,proposalId:otherId}),409);
 await status(await x.call('/tasks','POST',{...x.body,preparationId:'prep_'+'f'.repeat(64)}),409);
 await status(await x.call('/tasks','POST',{...x.body,parentTaskId:'a'.repeat(64)}),400);
 await status(await x.call('/tasks','POST',{...x.body,origin:{}}),400);
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 await status(await x.call('/tasks','POST',x.body),200);await status(await x.call('/tasks','POST',missing),409);
 x.bundle.pages.find(p=>p.id==='lp2-00').raw+='!';await status(await x.call('/tasks','POST',x.body),409);
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
});
await test('output, metric, alignment and receipt tampering never writes a result; stored corrupt output fails replay',async()=>{
 const x=await setup();await status(await x.call('/tasks','POST',x.body),200);const result=V.run(x.args.task);
 const mutations=[r=>r.transformed[0].text+='!',r=>r.metrics.runeCount=999,r=>r.alignment.pages[0].outputToInput[0]=1,r=>r.alignment.pages[0].removed[0].value=1,r=>r.taskId='f'.repeat(64)];
 for(const mutate of mutations){const bad=structuredClone(result);mutate(bad);await status(await x.call(x.resultPath,'POST',{result:bad}),422);}
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 await status(await x.call(x.resultPath,'POST',{result}),200);
 const corrupt=structuredClone(result);corrupt.alignment.pages[0].outputToInput[0]=1;
 x.sqlite.prepare('UPDATE local_task_results SET id=?,result_json=?').run(hash(corrupt),C.serialize(corrupt));
 await status(await x.call(x.taskPath),503);
});
await test('private associations, legacy comparisons, request bounds and cancellation cannot grant V2 writes',async()=>{
 const x=await setup(),abort=new AbortController();abort.abort();
 await status(await x.call('/tasks','POST',x.body,abort.signal),409);
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 await status(await x.call('/tasks','POST',x.body),200);
 await status(await x.call(x.taskPath+'/boundary-comparison'),422);
 await status(await x.call(x.taskPath+'?idea=p_'+'f'.repeat(64)),404);
 const result=V.run(x.args.task);await status(await x.call(x.resultPath,'POST',{result},abort.signal),503);
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 await status(await x.call(x.resultPath,'POST',{result,padding:'x'.repeat(2*1024*1024)}),400);
 x.sqlite.prepare('DELETE FROM research_ideas WHERE proposal_id=?').run(x.args.proposalId);await status(await x.call(x.taskPath),404);
});
console.log(groups+' declarative local-task groups passed; invented selected text only, real private SQLite.');
