/* Statistical control/plan/persistence integration; synthetic words only. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
import Control from '../../local-control.js';
import F from '../../record-followups.js';
import {planCard,createPrepareTaskHandler} from './prepare-task.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import {loadRecordPlan} from './record-plans.mjs';
const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z',pid='p_'+'e'.repeat(64);
const parent=JSON.parse(readFileSync(new URL('../../experiments/records/word-internal-affine-lags/record.json',import.meta.url),'utf8')),recipe=parent.browser_followups[0];
const control=recipe.control,criterion=control.task.criterion,alphabet=control.task.alphabet,source={id:'lp2-15',raw:control.task.pages[0].text};
const card=structuredClone(recipe.card);card.scope.value.pages=[source.id];
const db={sqlite:new DatabaseSync(':memory:'),prepare(sql){return {bind(...args){return {sql,args,first:async()=>db.sqlite.prepare(sql).get(...args)||null};}};},async batch(statements){db.sqlite.exec('BEGIN IMMEDIATE');try{const result=statements.map(s=>({success:true,meta:{changes:Number(db.sqlite.prepare(s.sql).run(...s.args).changes)}}));db.sqlite.exec('COMMIT');return result;}catch(e){db.sqlite.exec('ROLLBACK');throw e;}}};
for(const name of readdirSync(new URL('./migrations/',import.meta.url)).filter(n=>/^000[1-7]_/.test(n)).sort())db.sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(pid,pid.slice(2),E.stable(card),'unused',at);db.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(pid,at,at.slice(0,10));
const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async()=>({success:true})},PROPOSAL_LIMIT:{limit:async()=>({success:true})},AI:{run(){throw Error('No model call');}}};
const req=(path,data)=>new Request('https://worker.example'+path,{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(data)});
const fetcher=async(url)=>{assert.equal(url,origin+'/data/pages/'+source.id+'.json');return Response.json(source);};
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
try{
 await test('count-only canonical method exactly binds parameters, boundary and evaluation',async()=>{
  const before=structuredClone(card),plan=planCard(card);assert(!plan.reason,plan.reason);assert.deepEqual(plan.steps,[]);assert.deepEqual(plan.criterion,criterion);assert.deepEqual(card,before);assert.deepEqual(C.classifyMethod(C.field('specified',card.method.value)).familyIds,['repetition']);
  for(const mutate of [c=>c.method.value.operations[0].a=26,c=>c.method.value.operations[0].lag=5,c=>c.method.value.operations[0].boundaries='hyphen-period',c=>c.method.value.operations[0].key=[1],c=>c.method.value.operations.push({id:'affine',a:1,b:0}),c=>c.rules.reset={status:'specified',value:'page'},c=>c.rules.initialState={status:'specified',value:0}]){const c=structuredClone(card);mutate(c);assert(planCard(c).reason);}
  const onlyEval=structuredClone(card);onlyEval.method.value.operations=[{id:'affine',a:1,b:0}];assert(planCard(onlyEval).reason);
 });
 await test('the positive control needs real matches, complete opportunities and a lower conditional expectation',async()=>{
  const result=E.run(control.task);assert(Control.passed(control.task,result));
  for(const mutate of [r=>r.wordPairs.matches--,r=>r.wordPairs.opportunities=0,r=>r.wordPairs.expected={numerator:String(r.wordPairs.opportunities),denominator:'1'},r=>r.wordPairs.expected.denominator='0']){const wrong=structuredClone(result);mutate(wrong);assert(!Control.passed(control.task,wrong));}
  assert(!Control.passed({...control.task,criterion:{kind:'measurement'}},result));
 });
 await test('the public recipe prepares from pinned sources, runs its control only and excludes target execution',async()=>{
  const original=E.run;E.run=task=>{assert(task.title.includes('Synthetic'),'Only the control can run during preparation');return original(task);};
  try{const plan=await loadRecordPlan({recordId:parent.id,followupId:recipe.id},{fetcher:async url=>new Response(readFileSync(new URL('../..'+new URL(url).pathname,import.meta.url)),{headers:{'content-type':'application/json'}})});assert.deepEqual(plan.task.steps,[]);assert.deepEqual(plan.task.criterion,criterion);assert.equal(plan.task.pages.length,56);}finally{E.run=original;}
 });
 await test('synthetic computation saves, reopens and rejects tampered fractions rather than trusting uploaded totals',async()=>{
  const prepared=await createPrepareTaskHandler({fetcher})(req('/prepare-task',{proposalId:pid,parentTaskId:null}),env),body=await prepared.json();assert.equal(body.state,'plan-ready');assert(body.task.title.startsWith('Within-word rune pairs'));const task=body.task;
  const handle=createLocalTaskHandler({fetcher});assert.equal((await handle(req('/tasks',{proposalId:pid,task,inputVersion:'raw',parentTaskId:null}),env)).status,200);
  const result=E.run(task),wrong=structuredClone(result);wrong.wordPairs.expected.numerator='0';assert.equal((await handle(req('/tasks/'+task.taskId+'/results',{result:wrong}),env)).status,422);assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
  const saved=await handle(req('/tasks/'+task.taskId+'/results',{result}),env);assert.equal(saved.status,200);assert.equal((await saved.json()).state,'results-verified');const read=await handle(new Request('https://worker.example/tasks/'+task.taskId,{headers:{origin}}),env);assert.deepEqual((await read.json()).latestRun.result,result);
 });
 await test('authored client review preserves measurement and control without any automatic execution',async()=>{
  const task=await E.prepare({title:'Synthetic word-pair review',pages:[{id:source.id,text:source.raw}],alphabet,steps:[],criterion});
  const value={state:'plan-ready',origin:{recordId:parent.id,followupId:recipe.id,recordSha256:'a'.repeat(64),protocolSha256:'b'.repeat(64)},card,task,inputVersion:'raw',control,question:recipe.question,scopeChange:recipe.scope_change,limitation:recipe.limitation};let view;
  const doc={getElementById(){return null;}},host={innerHTML:''},run=E.run;E.run=()=>{throw Error('Review must not execute');};
  try{view=F.createWorkspace(doc,host,{reference:F.reference('#record='+parent.id+'&followup='+recipe.id),config:{recordPlanEndpoint:'https://mock.example/record-plans'},request:async()=>Response.json(value),validEndpoint:()=>true,planHTML:()=>'<p>Fixed count plan</p>'});await view.ready;assert.deepEqual(view.getState().plan.task.criterion,criterion);assert(host.innerHTML.includes('Fixed count plan'));assert(!host.innerHTML.includes('Follow-up unavailable'));}finally{E.run=run;view?.destroy();}
 });
}finally{db.sqlite.close();}
console.log(groups+' word-pair integration groups passed; no manuscript measurement executed.');
