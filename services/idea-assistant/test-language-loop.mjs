/* One actual service journey; all storage/assets are local and no hosted writes occur. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import Evaluators from '../../output-evaluators.js';
import {createProposalHandler} from './proposals.mjs';
import {createCommunityIdeaHandler} from './community-ideas.mjs';
import {createPrepareTaskHandler} from './prepare-task.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import {createTaskExtensionHandler} from './task-extensions.mjs';
import {authorize} from './prepared-plans.mjs';

const origin='https://jelliottdev.github.io',at='2026-10-25T12:00:00.000Z',criterion=Evaluators.criterion();
const bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),pages=new Map(bundle.pages.map(page=>[page.id,page]));
const sqlite=new DatabaseSync(':memory:');for(const name of readdirSync(new URL('./migrations/',import.meta.url)).filter(name=>/^\d{4}_.*\.sql$/.test(name)).sort())sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
const db={prepare(sql){return {bind(...args){return {sql,args,first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};},async batch(statements){sqlite.exec('BEGIN IMMEDIATE');try{const output=statements.map(s=>({success:true,meta:{changes:Number(sqlite.prepare(s.sql).run(...s.args).changes)}}));sqlite.exec('COMMIT');return output;}catch(error){sqlite.exec('ROLLBACK');throw error;}}};
let fetches=0,aiCalls=0;
const fetcher=async(url,options)=>{fetches++;assert.equal(options.redirect,'manual');assert(options.signal);if(url===origin+'/data/local-run-inputs.json')return Response.json(bundle);const match=url.match(/^https:\/\/jelliottdev\.github\.io\/data\/pages\/(lp[12]-\d{2})\.json$/);assert(match&&pages.has(match[1]),'Only pinned local official assets may be fetched');return Response.json(pages.get(match[1]));};
const rate={limit:async()=>({success:true})},env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:rate,PROPOSAL_LIMIT:rate,AI:{run:async()=>{aiCalls++;return {choices:[{message:{content:JSON.stringify({version:1,steps:[{source:{operationIndex:0,start:0,quote:'Reverse each row except positions chosen later'},step:{op:'reverse',unit:'line'}}],unsupported:['The exceptional positions and their selection rule are unspecified.']})}}]};}}};
const now=()=>new Date(at),handlers={proposals:createProposalHandler({now}),ideas:createCommunityIdeaHandler({now}),prepare:createPrepareTaskHandler({now,fetcher}),tasks:createLocalTaskHandler({now,fetcher}),extensions:createTaskExtensionHandler({now,fetcher})};
const field=value=>C.field('specified',value,{kind:'supplied',refs:['local journey fixture']});
function specification({aim='decipher',detail='Investigate decoding on the selected pages',ids=['lp2-15'],evaluation=criterion,method={id:'reverse_row_runes',label:'Reverse rune order within rows'}}={}){return C.confirm(C.createDraft({source:{text:'PRIVATE ORIGINAL SOURCE STRING'},aim:field({outcomeId:aim,detail}),method:field({operations:[method]}),scope:field({pages:ids}),rules:{inputVersion:field('raw'),evaluation:field(evaluation)}}),{id:'local-user-review',at});}
function request(path,body){return new Request('https://worker.example'+path,{method:body===undefined?'GET':'POST',headers:{origin,'CF-Connecting-IP':'203.0.113.7',...(body===undefined?{}:{'Content-Type':'application/json'})},...(body===undefined?{}:{body:JSON.stringify(body)})});}
async function call(kind,path,body,status=200){const response=await handlers[kind](request(path,body),env),value=await response.json();assert.equal(response.status,status,JSON.stringify(value));return value;}
async function save(spec){const card=H.cardData(spec),receipt=await call('proposals','/proposals',{requestId:crypto.randomUUID(),fragment:H.encode(spec),originalIdea:'PRIVATE ORIGINAL SOURCE STRING'});assert.equal(receipt.status,'received');const idea=await call('ideas','/ideas',{proposalId:receipt.id});assert.equal(idea.id,receipt.id);assert.deepEqual(idea.card,card);assert(!JSON.stringify(idea).includes('PRIVATE ORIGINAL'));return {id:receipt.id,card};}
const count=table=>sqlite.prepare('SELECT COUNT(*) n FROM '+table).get().n;
async function prepare(idea){return call('prepare','/prepare-task',{proposalId:idea.id,parentTaskId:null});}
async function create(idea,plan){
 assert.equal(plan.state,'plan-ready');await Controls.validate(plan.controls,plan.task);
 assert(await authorize({db,preparationId:plan.preparation.id,proposalId:idea.id,card:idea.card,task:plan.task,inputVersion:'raw',parentTaskId:null,controls:plan.controls}),'The reviewed receipt must bind the exact original card, model and task');
 const registered=await call('tasks','/tasks',{proposalId:idea.id,task:plan.task,inputVersion:'raw',parentTaskId:null,preparationId:plan.preparation.id});assert.deepEqual(registered.plan,plan.task);return registered;
}
async function browserComputation(plan){for(const fixture of plan.controls.cases){const result=await E.verify(fixture.task,E.run(fixture.task)),actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(result))))].map(n=>n.toString(16).padStart(2,'0')).join('');assert.equal(actual,fixture.expectedResultSha256);}return E.verify(plan.task,E.run(plan.task));}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
let original,firstPlan,registered,firstResult;
try{
 await test('save normalized decipher idea, explicitly publish it, prepare and review an exact diagnostic plan',async()=>{
  const spec=specification(),before=C.serialize(spec);original=await save(spec);assert.equal(original.card.outcome.value.outcomeId,'decipher');assert.equal(count('local_tasks'),0);
  firstPlan=await prepare(original);assert.equal(firstPlan.state,'plan-ready');assert.deepEqual(firstPlan.task.criterion,criterion);assert.equal(firstPlan.task.pages[0].text,pages.get('lp2-15').raw);assert.equal(count('local_tasks'),0);assert.equal(aiCalls,0);assert.equal(C.serialize(spec),before);
  registered=await create(original,firstPlan);assert.equal(registered.state,'not-run');assert.equal(registered.card.outcome.value.outcomeId,'decipher');assert.deepEqual(registered.plan.criterion,criterion);assert.equal(count('local_task_results'),0);
 });
 await test('independent checks precede computation; forged score is rejected and genuine result survives reload',async()=>{
  firstResult=await browserComputation(firstPlan);assert.equal(firstResult.languageScore.pages[0].status,'compared');assert.equal(firstResult.languageScore.pages[0].models.length,8);assert.deepEqual(firstResult.matches,[]);assert(!Object.hasOwn(firstResult,'accepted'));assert(!Object.hasOwn(firstResult.languageScore,'winner'));
  const forged=structuredClone(firstResult);forged.languageScore.pages[0].models[0].total++;await call('tasks','/tasks/'+registered.id+'/results',{result:forged},422);assert.equal(count('local_task_results'),0);
  const saved=await call('tasks','/tasks/'+registered.id+'/results',{result:firstResult});assert.equal(saved.state,'results-verified');assert.match(saved.verification,/does not establish/);assert.equal(count('local_task_results'),1);
  handlers.tasks=createLocalTaskHandler({now,fetcher});const reloaded=await call('tasks','/tasks/'+registered.id);assert.deepEqual(reloaded.latestRun.result,firstResult);assert.deepEqual(reloaded.plan.criterion,criterion);assert.equal(reloaded.card.outcome.value.outcomeId,'decipher');assert(!JSON.stringify(reloaded).includes('PRIVATE ORIGINAL'));
 });
 await test('a differently classified and worded idea reuses original evidence without creating a duplicate execution',async()=>{
  const renamed=await save(specification({aim:'measure',detail:'Compare rune order, not a decoding conclusion',method:{id:'reverse_row_runes',label:'Reverse rune order within each row'}}));assert.notEqual(renamed.id,original.id);const before=count('local_tasks'),prepared=await prepare(renamed);assert.equal(prepared.state,'scope-covered');assert.deepEqual(prepared.coverage.coveredPages,['lp2-15']);assert.deepEqual(prepared.coverage.remainingPages,[]);assert.equal(prepared.coverage.evidence[0].taskId,registered.id);assert.equal(count('local_tasks'),before);assert(!Object.hasOwn(prepared,'task'));
  const reloaded=await call('ideas','/ideas/'+renamed.id);assert.equal(reloaded.tasks.length,0);assert.deepEqual(reloaded.coverage.coveredPages,['lp2-15']);assert.deepEqual(reloaded.coverage.requestedTask.criterion,criterion);assert.equal(reloaded.card.outcome.value.outcomeId,'measure');
 });
 await test('expanded scope prepares only open pages and preserves the original question, model and pinned evidence',async()=>{
  const expanded=await save(specification({ids:['lp2-15','lp2-16'],detail:'Same decoding hypothesis over an expanded selection'})),plan=await prepare(expanded);assert.equal(plan.state,'plan-ready');assert.deepEqual(plan.coverage.coveredPages,['lp2-15']);assert.deepEqual(plan.coverage.remainingPages,['lp2-16']);assert.deepEqual(plan.task.pages.map(p=>p.id),['lp2-16']);assert.deepEqual(plan.task.criterion,criterion);assert.equal(expanded.card.outcome.value.outcomeId,'decipher');
  const preparedRow=sqlite.prepare('SELECT basis_json FROM prepared_plans WHERE id=?').get(plan.preparation.id),basis=JSON.parse(preparedRow.basis_json);assert.equal(basis.kind,'evidence-remainder');assert.equal(basis.evidence[0].taskId,registered.id);const child=await create(expanded,plan),result=await browserComputation(plan);await call('tasks','/tasks/'+child.id+'/results',{result});
  const reloaded=await call('ideas','/ideas/'+expanded.id);assert.deepEqual(reloaded.coverage.remainingPages,[]);assert.deepEqual(reloaded.coverage.coveredPages,['lp2-15','lp2-16']);assert.equal(reloaded.coverage.evidence.length,2);assert.equal(reloaded.card.outcome.value.outcomeId,'decipher');
 });
 await test('remaining-page extension retains the exact evaluator and separate per-page semantics',async()=>{
  const before=count('local_tasks'),extension=await call('extensions','/tasks/'+registered.id+'/extensions',{scope:'remaining-lp2'});assert.equal(extension.state,'plan-ready');assert.deepEqual(extension.task.criterion,criterion);assert.deepEqual(extension.task.steps,firstPlan.task.steps);assert.deepEqual(extension.coveredPages,['lp2-15','lp2-16']);assert.deepEqual(extension.coverage.coveredPages,['lp2-16']);assert(extension.coverage.evidence.some(ref=>ref.pages.includes('lp2-16')));assert(!extension.task.pages.some(page=>['lp2-15','lp2-16'].includes(page.id)));assert(extension.task.pages.some(page=>page.id==='lp2-50'&&page.text===pages.get('lp2-50').raw));await Controls.validate(extension.controls,extension.task);assert.equal(count('local_tasks'),before);
 });
 await test('unsupported readability and unsupported rules stop honestly without execution, receipts or fake coverage',async()=>{
  for(const options of [{evaluation:{kind:'readability'}},{method:{id:'described_method',label:'Reverse each row except positions chosen later'}}]){
   const idea=await save(specification(options)),before={tasks:count('local_tasks'),results:count('local_task_results'),receipts:count('prepared_plans'),requests:count('idea_computation_evidence')},sourceReads=fetches,denied=await prepare(idea);assert.equal(denied.state,'needs-adapter');assert(!Object.hasOwn(denied,'coverage'));assert(!Object.hasOwn(denied,'task'));assert.equal(fetches,sourceReads);assert.deepEqual({tasks:count('local_tasks'),results:count('local_task_results'),receipts:count('prepared_plans'),requests:count('idea_computation_evidence')},before);const view=await call('ideas','/ideas/'+idea.id);assert.equal(view.tasks.length,0);assert(!Object.hasOwn(view,'coverage'));assert.equal(view.card.outcome.value.outcomeId,'decipher');
  }
  assert.equal(aiCalls,1,'Only the opaque unsupported method may consult the source-bound wording adapter');
 });
 console.log('Language diagnostic service journey: '+groups+' gates passed; real SQLite, pinned local manuscript inputs, no hosted writes.');
}finally{sqlite.close();}
