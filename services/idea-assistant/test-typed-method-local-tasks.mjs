/* Typed MD2 through actual durable handlers. Every page is invented; no hosted calls. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import MD from '../../method-design.js';
import MI from '../../method-implementation.js';
import V from '../../declarative-rune-program.js';
import Language from '../../language-score.js';
import Controls from '../../local-plan-controls-dispatch.js';
import {issue} from './prepared-plans.mjs';
import {applyMigrations} from './sqlite-test-migrations.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
const hash=v=>createHash('sha256').update(C.serialize(v)).digest('hex'),at='2026-10-27T12:00:00.000Z',f=v=>C.field('specified',v);
async function fixture(evaluation={kind:'output-measurements'}){
 const sqlite=new DatabaseSync(':memory:');applyMigrations(sqlite);
 const db={prepare(sql){return {bind(...args){return {sql,args,first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{const rows=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return rows;}catch(e){sqlite.exec('ROLLBACK');throw e;}}},bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),a=bundle.alphabet[0].rune;
 for(const page of bundle.pages){page.raw=a+a+a+' '+a+a;page.reviewed_text=page.raw;}
 bundle.pages.find(p=>p.id==='lp2-01').raw=a+a+' '+a+a+a;
 const parent=H.cardData(C.confirm(C.createDraft({source:{text:'Could extra repeated runes be padding?'},aim:f('Measure'),method:f({operations:[{id:'affine',a:1,b:0}]}),scope:f({pages:['lp2-00']}),rules:{inputVersion:f('raw'),evaluation:f('measurement')}}),{id:'fixture',at}));
 const proposal={schema:MD.TYPED_SCHEMA,name:'Repeated-rune removal',hypothesis:'Measure output after collapsing repeated runs.',pages:['lp2-00','lp2-01'],inputVersion:'raw',representation:{kind:'gp29'},keyUse:{kind:'not-used',material:'',application:''},steps:['Within each word keep the first rune of each equal run.'],parameters:[],evaluation,controls:[{kind:'implementation-sanity-v2'}],assumptions:['This measurement alone cannot identify filler.']};
 const draft=await MD.toDraft(proposal,{parentId:'p_'+hash(parent),parentCard:parent}),card=H.cardData(C.confirm(draft,{id:'fixture',at})),proposalId='p_'+hash(card);
 const implementation=await MI.fromTypedDraft(proposal,{steps:[{op:'collapse-adjacent-repeats',unit:'word',policy:'all-but-first'}],coverage:{steps:[{status:'implemented',programSteps:[1],note:'Keep the first rune within each word run.'}],requirements:[]}}),token=await MI.bind({proposal,implementation}),task=await V.prepare(MI.compileBody(token,{bundle})),controls=await Controls.prepare(task),basis={kind:'method-implementation-v1',implementation,review:{schema:'liberpedia-method-implementation-review-v1',proposalSha256:hash(proposal),implementationSha256:hash(implementation)}};
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,hash(card),C.serialize(card),'unused',at);
 sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(proposalId,at,at.slice(0,10));
 let reads=0;const fetcher=async(url,options)=>{reads++;assert.equal(url,'https://jelliottdev.github.io/data/local-run-inputs.json');assert.equal(options.redirect,'manual');return new Response(JSON.stringify(bundle),{headers:{'Content-Type':'application/json'}});};
 return {sqlite,bundle,parent,implementation,proposal,reads:()=>reads,args:{db,proposalId,card,task,inputVersion:'raw',parentTaskId:null,controls,authority:'idea',basis,createdAt:at,fetcher}};
}

const origin='https://jelliottdev.github.io';
function request(path,method='GET',body,signal){return new Request('https://worker.example'+path,{method,headers:{origin,...(body!==undefined?{'Content-Type':'application/json'}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{}),...(signal?{signal}:{})});}
async function setup(evaluation){
 const x=await fixture(evaluation);x.receipt=await issue(x.args);
 x.env={SITE_ORIGIN:origin,PROPOSALS:x.args.db,PROPOSAL_LIMIT:{limit:async()=>({success:true})}};
 x.handle=createLocalTaskHandler({fetcher:x.args.fetcher,now:()=>new Date(at),discoverEvidence:()=>{throw Error('V2 cannot borrow legacy coverage');},prepareControls:()=>{throw Error('V2 cannot use V1 control memo/cache');}});
 x.body={proposalId:x.args.proposalId,task:x.args.task,inputVersion:'raw',parentTaskId:null,preparationId:x.receipt.id};
 x.call=(path,method,body,signal)=>x.handle(request(path,method,body,signal),x.env);
 x.taskPath='/tasks/'+x.args.task.taskId;x.resultPath=x.taskPath+'/results';
 return x;
}
async function status(response,expected){assert.equal(response.status,expected,await response.clone().text());return response.json();}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('typed reviewed checks survive real issue create save and historical reload with exact code-owned facts',async()=>{
 for(const evaluation of [{kind:'output-measurements'},{kind:'exact-prefix',values:[0,0]},{kind:'exact-prefix-set',openings:[{id:'one',values:[0]},{id:'two',values:[1,2]}]},Language.criterion()]){
  const x=await setup(evaluation),before=C.serialize(x.args.card),facts=MI.typedRequirements(x.proposal);
  assert.equal(x.bundle.pages.length,75);assert(x.bundle.pages.every(p=>p.raw.length<20),'Every official fixture page must be invented, never target data');assert.equal(x.proposal.schema,MD.TYPED_SCHEMA);assert.deepEqual(MD.readCard(x.args.card).proposal,x.proposal);
  assert.deepEqual(x.args.card.rules.searchProtocol.value.parentId,'p_'+hash(x.parent));
  assert.deepEqual(x.implementation.criterion,facts.criterion);assert.deepEqual(x.args.task.pages.map(p=>p.id),x.proposal.pages);
  const control=x.implementation.coverage.find(c=>c.part==='control');assert.equal(control.status,'implemented');assert.match(control.note,/does not mean|planned/i);assert(!/controls passed/i.test(control.note));
  const projection=await status(await x.call('/tasks','POST',x.body),200);assert.equal(projection.state,'not-run');assert(!Object.hasOwn(projection,'latestRun'));assert.equal(projection.controls.version,2);assert.deepEqual(projection.methodImplementation,{implementation:x.implementation,review:x.args.basis.review});
  const result=V.run(x.args.task),saved=await status(await x.call(x.resultPath,'POST',{result}),200);assert.equal(saved.state,'results-verified');assert.deepEqual(saved.latestRun.result,result);
  const rows=()=>['prepared_plans','local_tasks','local_task_results'].map(t=>Number(x.sqlite.prepare('SELECT COUNT(*) n FROM '+t).get().n)),counts=rows();x.bundle.pages.forEach(p=>p.raw+='!');const reads=x.reads();
  const loaded=await status(await x.call(x.taskPath+'?idea='+x.args.proposalId),200);assert.equal(x.reads(),reads,'Historical receipt reads must not refetch today’s source');assert.deepEqual(rows(),counts);assert.deepEqual(loaded.methodImplementation,projection.methodImplementation);assert.deepEqual(loaded.latestRun,saved.latestRun);assert.deepEqual(MD.readCard(loaded.card).proposal,x.proposal);assert.equal(C.serialize(x.args.card),before);
  await status(await x.call('/tasks','POST',x.body),409);assert.deepEqual(rows(),counts);x.sqlite.close();
 }
});
await test('changed typed criterion or review binding cannot admit an old program or write tasks',async()=>{
 const x=await setup({kind:'exact-prefix',values:[0]});
 const changedTask=structuredClone(x.args.task);changedTask.criterion={kind:'measurement'};changedTask.taskId=await V.identity(changedTask);await status(await x.call('/tasks','POST',{...x.body,task:changedTask}),409);
 const changed=structuredClone(x.proposal);changed.evaluation={kind:'output-measurements'};assert.notEqual(hash(changed),hash(x.proposal));await assert.rejects(()=>MI.bind({proposal:changed,implementation:x.implementation}));
 const i=structuredClone(x.implementation);i.criterion={kind:'measurement'};await assert.rejects(()=>issue({...x.args,basis:{...x.args.basis,implementation:i}}));
 assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);x.sqlite.close();
});
await test('described scientific evaluation remains unresolved and cannot be forged into issued measurement',async()=>{
 const x=await fixture();const p=structuredClone(x.proposal);p.evaluation={kind:'described',description:'Establish significance against a seeded random-null experiment.'};p.controls=[{kind:'described',description:'Use a scientific random baseline with a declared seed.'}];
 const i=await MI.fromTypedDraft(p,{steps:x.implementation.steps,coverage:{steps:[{status:'implemented',programSteps:[1],note:'Exact procedure only.'}],requirements:[]}}),binding=await MI.bind({proposal:p,implementation:i});assert.equal(MI.inspect(binding).ready,false);assert.equal(i.criterion,null);assert(i.coverage.filter(c=>['control','evaluation'].includes(c.part)).every(c=>c.status==='unsupported'));assert.throws(()=>MI.compileBody(binding,{bundle:x.bundle}));
 const forged=structuredClone(i);forged.criterion={kind:'measurement'};forged.issues=[];for(const row of forged.coverage)row.status='implemented';await assert.rejects(()=>MI.bind({proposal:p,implementation:forged}));await assert.rejects(()=>issue({...x.args,basis:{...x.args.basis,implementation:forged}}));assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);x.sqlite.close();
});
await test('fresh official input and cancellation remain mandatory even for typed reviewed source and existing tasks',async()=>{
 const x=await setup();const abort=new AbortController();abort.abort();await status(await x.call('/tasks','POST',x.body,abort.signal),409);assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 x.bundle.pages.find(p=>p.id==='lp2-01').raw+='!';await status(await x.call('/tasks','POST',x.body),409);assert.equal(x.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert(x.reads()>0);x.sqlite.close();
});
console.log(groups+' typed durable method groups passed; invented pages only, no hosted writes.');
