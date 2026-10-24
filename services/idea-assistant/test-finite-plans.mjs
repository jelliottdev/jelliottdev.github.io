/* Full finite-plan loop on synthetic text, real SQLite, no hosted writes or AI. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
import F from '../../record-followups.js';
import {planCard,createPrepareTaskHandler} from './prepare-task.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import {validateCandidate} from './propose-task-plan.mjs';
const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z',pid='p_'+'c'.repeat(64);
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
const key=Array.from({length:277},(_,i)=>(i*i+7)%29),criterion={kind:'exact-prefix',values:[0,1,2]};
const source={id:'lp2-15',raw:key.map((k,i)=>alphabet[(i%29+k)%29].rune).join('')};
function card(operation={id:'finite_key',label:'Finite key stream',key,direction:'subtract',reset:'page'},rules={}){return H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic finite-stream fixture'},aim:known('Test a pattern'),method:known({operations:[operation]}),scope:known({pages:[source.id]}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known(criterion),...rules}}),{id:'fixture',at}));}
const db={sqlite:new DatabaseSync(':memory:'),prepare(sql){return {bind(...args){return {sql,args,first:async()=>db.sqlite.prepare(sql).get(...args)||null};}};},async batch(statements){db.sqlite.exec('BEGIN IMMEDIATE');try{const result=statements.map(s=>({success:true,meta:{changes:Number(db.sqlite.prepare(s.sql).run(...s.args).changes)}}));db.sqlite.exec('COMMIT');return result;}catch(e){db.sqlite.exec('ROLLBACK');throw e;}}};
for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql'])db.sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
const current=card(),before=structuredClone(current);db.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(pid,pid.slice(2),E.stable(current),'unused',at);db.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(pid,at,at.slice(0,10));
const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async()=>({success:true})},PROPOSAL_LIMIT:{limit:async()=>({success:true})},AI:{run(){throw Error('No model call allowed');}}};
const fetcher=async(url,options)=>{assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'manual');return Response.json(source);};
const req=(path,data)=>new Request('https://worker.example'+path,{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(data)});
let groups=0;async function test(name,f){await f();groups++;console.log('PASS '+name);}
let task;
try{
 await test('277 explicit values survive standardization, classification and deterministic compilation',async()=>{
  const plan=planCard(current);assert(!plan.reason,plan.reason);assert.deepEqual(plan.steps,[{op:'finite-shift',key,direction:'subtract',reset:'page'}]);assert(plan.notes.some(s=>s.includes('never wrap')));assert.deepEqual(current,before);assert.deepEqual(C.classifyMethod(known({operations:[{id:'finite_key'}]})).familyIds,['number-streams']);
  for(const rules of [{reset:known('word')},{initialState:known(0)},{reset:C.field('not_applicable')}])assert(planCard(card(undefined,rules)).reason);
  for(const operation of [{id:'finite_key',key,direction:'subtract'},{id:'finite_key',key,direction:'subtract',reset:'page',mode:'repeat'},{id:'finite_key',key:[29],direction:'subtract',reset:'page'},{id:'finite_key',label:'Finite key stream except F',key,direction:'subtract',reset:'page'}])assert(planCard(card(operation)).reason);
  assert.throws(()=>card({id:'finite_key',key:Array(20000).fill(28),direction:'subtract',reset:'page'}),/limit|exceeds/i,'Large streams do not silently evade card-size bounds');
 });
 await test('closed text grammar preserves finite identity and never invents a named sequence',async()=>{
  const phrase='finite key stream with key indices [1,2,3], subtract, reset at each word',input=card({id:'described_method',label:phrase}),step={op:'finite-shift',key:[1,2,3],direction:'subtract',reset:'word'},candidate={version:1,steps:[{source:{operationIndex:0,start:0,quote:phrase},step}],unsupported:[]};
  const mapped=validateCandidate(input,candidate,{compile:planCard});assert(!mapped.reason,mapped.reason);assert.deepEqual(mapped.plan.steps,[step]);assert.equal(mapped.card.method.value.operations[0].id,'finite_key');
  for(const changed of [{...step,key:[1,2,4]},{...step,op:'keyed-shift',mode:'repeat'}])assert(validateCandidate(input,{...candidate,steps:[{...candidate.steps[0],step:changed}]},{compile:planCard}).reason);
  const named='finite prime key stream, subtract, reset at each page';assert(validateCandidate(card({id:'described_method',label:named}),{...candidate,steps:[{source:{operationIndex:0,start:0,quote:named},step}]},{compile:planCard}).reason);
 });
 await test('preparation, task persistence, exact result replay and reopening preserve finite semantics',async()=>{
  const response=await createPrepareTaskHandler({fetcher})(req('/prepare-task',{proposalId:pid,parentTaskId:null}),env),plan=await response.json();assert.equal(response.status,200);assert.equal(plan.state,'plan-ready');task=plan.task;assert.equal(task.steps[0].key.length,277);assert(task.title.startsWith('Finite key stream subtraction'));assert(!task.title.includes('Cumulative'));assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
  const handle=createLocalTaskHandler({fetcher}),saved=await handle(req('/tasks',{proposalId:pid,task,inputVersion:'raw',parentTaskId:null}),env);assert.equal(saved.status,200);assert.deepEqual((await saved.json()).plan,task);
  const result=E.run(task);assert(result.matches[0].matched);assert.equal(result.transformed[0].text,key.map((_,i)=>alphabet[i%29].rune).join(''));
  const returned=await handle(req('/tasks/'+task.taskId+'/results',{result}),env);assert.equal(returned.status,200);assert.equal((await returned.json()).state,'results-verified');
  const reopened=await handle(new Request('https://worker.example/tasks/'+task.taskId,{headers:{origin}}),env);assert.equal(reopened.status,200);assert.deepEqual((await reopened.json()).latestRun.result,result);
  const short=card({id:'finite_key',key:key.slice(0,276),direction:'subtract',reset:'page'});db.sqlite.prepare('UPDATE proposals SET card_json=? WHERE id=?').run(E.stable(short),pid);const denied=await createPrepareTaskHandler({fetcher})(req('/prepare-task',{proposalId:pid,parentTaskId:null}),env);assert.equal((await denied.json()).state,'needs-adapter');assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
 });
 await test('authored client review accepts the exact finite card and control without execution',async()=>{
  const controlTask=await E.prepare({...task,title:'Synthetic finite recovery control',pages:[{id:'lp1-00',text:source.raw}]}),result=E.run(controlTask),sha=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(result)));
  const value={state:'plan-ready',origin:{recordId:'fixture',followupId:'finite',recordSha256:'a'.repeat(64),protocolSha256:'b'.repeat(64)},card:current,task,inputVersion:'raw',control:{label:'Synthetic positive control',task:controlTask,expected_result_sha256:Buffer.from(sha).toString('hex')},question:'Does the planted opening match?',scopeChange:'Synthetic source only.',limitation:'Not a manuscript result.'};
  const doc={getElementById(){return null;}},host={innerHTML:''},config={recordPlanEndpoint:'https://mock.example/record-plans'};let calls=0;const run=E.run;E.run=()=>{throw Error('No execution during review');};let view;
  try{view=F.createWorkspace(doc,host,{reference:F.reference('#record=fixture&followup=finite'),config,request:async()=>{calls++;return Response.json(value);},validEndpoint:()=>true,planHTML:()=>'<p>Finite stream plan</p>',isLive:()=>true});await view.ready;assert(view.getState().plan);assert.equal(calls,1);assert(host.innerHTML.includes('Finite stream plan'));}finally{E.run=run;view?.destroy();}
 });
}finally{db.sqlite.close();}
console.log(groups+' finite-plan integration groups passed; synthetic source only.');
