import {DatabaseSync} from 'node:sqlite';
/* Fixed GP word-sum plans; synthetic assets only, no provider or target runs. */
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {createHash,webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {planCard,createPrepareTaskHandler} from './prepare-task.mjs';
import {loadRecordPlan} from './record-plans.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
import Package from '../../local-run-package.js';
const at='2026-10-24T12:00:00.000Z',origin='https://jelliottdev.github.io',sha=text=>createHash('sha256').update(text).digest('hex');
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
function card(table='reversed',boundaries='non-rune',extra={}){return H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic reversed prime assignments and word sums'},aim:known('Measure word sums'),method:known({operations:[{id:'word_prime_sums',label:'Word prime sums',table,boundaries}]}),scope:known({pages:['lp2-15']}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'word-prime-sums',table,boundaries})},...extra}),{id:'fixture',at}));}
const raw='ᚠᚢ-ᚦ\nᚩ.ᚠ',reviewed='ᚠᚢ-ᚦ.ᚩᚠ';
const frontendSource=readFileSync(new URL('../../record-followups.js',import.meta.url),'utf8'),exportNeedle='const api={reference,validateOrigins,createWorkspace}';assert(frontendSource.includes(exportNeedle));
const frontendContext={module:{exports:{}},require:createRequire(new URL('../../record-followups.js',import.meta.url)),btoa,TextEncoder,crypto:webcrypto};vm.createContext(frontendContext);vm.runInContext(frontendSource.replace(exportNeedle,'const api={cardProgram,validatePlan,reference,validateOrigins,createWorkspace}'),frontendContext);
const frontend=frontendContext.module.exports;
async function prepare(input){
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0008_prepared_plans.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 const stored=C.serialize(input),hash=sha(stored),proposalId='p_'+hash;sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(proposalId,hash,stored,'unused',at);
 let calls=0,ai=0;const handle=createPrepareTaskHandler({fetcher:async url=>{calls++;assert.equal(url,origin+'/data/pages/lp2-15.json');return Response.json({id:'lp2-15',raw,reviewed_text:reviewed});}}),env={SITE_ORIGIN:origin,PROPOSALS:{prepare(sql){assert(/^(?:SELECT|INSERT INTO prepared_plans)/.test(sql));return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null};}};}},TASK_LIMIT:{limit:async()=>({success:true})},AI:{run(){ai++;throw Error('No AI grammar for word sums');}}},request=new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify({proposalId,parentTaskId:null})});
 const original=L.run;L.run=task=>{
  assert.match(task.title,/^Synthetic local reference 1: layout-(?:forward|reversed) for [a-f0-9]{64}$/,'Preparation may run only the fixed independent synthetic controls');
  assert.deepEqual(task.pages.map(page=>page.id),['lp1-00','lp1-01'],'Preparation must not execute manuscript target pages');
  assert(task.pages.every(page=>page.text!==raw&&page.text!==reviewed),'Official target text cannot be relabeled as a control');
  return original(task);
 };try{const response=await handle(request,env);const value=await response.json();assert.equal(sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);return {response,value,calls,ai};}finally{L.run=original;sqlite.close();}
}
for(const table of ['canonical','reversed'])for(const boundaries of ['non-rune','hyphen-period']){
 const input=card(table,boundaries),before=structuredClone(input),plan=planCard(input);assert(!plan.reason,plan.reason);assert.deepEqual(plan.steps,[]);assert.deepEqual(plan.criterion,{kind:'word-prime-sums',table,boundaries});assert.deepEqual(input,before);assert(plan.notes.some(n=>n.includes('does not reverse digits or rune order')));
 const front=frontend.cardProgram(input);assert.deepEqual(JSON.parse(JSON.stringify(front.steps)),plan.steps);assert.deepEqual(JSON.parse(JSON.stringify(front.criterion)),plan.criterion);
 const {response,value,calls,ai}=await prepare(input);assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.match(value.preparation.id,/^prep_[a-f0-9]{64}$/);assert.deepEqual(value.task.criterion,plan.criterion);assert.deepEqual(value.task.steps,[]);assert(value.task.title.includes(table+' table'));assert.equal(value.task.pages[0].text,raw);assert.equal(calls,1);assert.equal(ai,0);await L.checkIdentity(value.task);
 // Independent hand totals for synthetic bytes; this is not manuscript data.
 const result=L.run(value.task);assert.equal(result.wordSums.total,table==='canonical'?19:529);assert.deepEqual(result.wordSums.pages[0].words.map(w=>w.sum),table==='canonical'?(boundaries==='non-rune'?[5,5,7,2]:[5,12,2]):(boundaries==='non-rune'?[216,103,101,109]:[216,204,109]));
}
const malformed=[];
for(const family of Object.keys(C.METHOD_FAMILIES)){
 const input=card();input.method.value.operations[0].declaredFamilyId=family;const before=structuredClone(input),back=planCard(input),front=frontend.cardProgram(input);assert(!back.reason,back.reason);assert.deepEqual(JSON.parse(JSON.stringify(front.steps)),back.steps);assert.deepEqual(JSON.parse(JSON.stringify(front.criterion)),back.criterion);assert.equal(front.snapshot.method.value.operations[0].declaredFamilyId,family);assert.deepEqual(input,before,'Valid maintained family metadata survives without changing the numeric method');
}
for(const family of ['invented-family','',null,1,['prime-indices'],{id:'prime-indices'}]){const input=card();input.method.value.operations[0].declaredFamilyId=family;assert.throws(()=>frontend.cardProgram(input),'Malformed family metadata is not silently accepted by the frontend');assert(planCard(input).reason,'Backend rejects the same malformed family metadata');const rejected=await prepare(input);assert.equal(rejected.value.state,'needs-adapter');assert.equal(rejected.calls,0);assert.equal(rejected.ai,0);}
for(const field of ['label','table','boundaries']){const c=card();delete c.method.value.operations[0][field];malformed.push(c);}
for(const [key,value]of [['label','Word prime sums except F'],['table','custom'],['boundaries','spaces'],['unit','word'],['reset','page'],['unknown',true]]){const c=card();c.method.value.operations[0][key]=value;malformed.push(c);}
for(const evaluation of ['measurement',{kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'},{kind:'word-prime-sums',table:'reversed',boundaries:'hyphen-period'},{kind:'word-prime-sums',table:'reversed',boundaries:'non-rune',unknown:true}]){const c=card();c.rules.evaluation=known(evaluation);malformed.push(c);}
for(const [key,value]of [['reset','page'],['initialState',0],['boundaryMode','within_words'],['exceptionalCases','Skip F'],['searchBounds','Try all tables']]){const c=card();c.rules[key]=known(value);malformed.push(c);}
const mixed=card();mixed.method.value.operations.push({id:'reverse_runes',unit:'word'});malformed.push(mixed);const wrong=card();wrong.method.value.operations=[{id:'reverse_runes',unit:'word'}];malformed.push(wrong);
for(const c of malformed){let rejected=false;try{rejected=!!planCard(c).reason}catch{rejected=true}assert(rejected);const out=await prepare(c);assert.notEqual(out.value.state,'plan-ready');assert.equal(out.calls,0);assert.equal(out.ai,0);}
const args={recordId:'synthetic-word-sums',followupId:'fixed-table'};
async function fixture(){const input=card(),controlTask=await L.prepare({title:'Synthetic full word-sum ledger',alphabet,pages:[{id:'lp1-01',text:'ᚠᚢ-ᚦ.ᚠ'}],steps:[],criterion:planCard(input).criterion}),controlResult=L.run(controlTask);assert.deepEqual(controlResult.wordSums.pages[0].words.map(w=>w.sum),[216,103,109]);
 const recipe={id:args.followupId,title:'Synthetic source-bound word sums',question:'What are the fixed word totals?',scope_change:'One explicit synthetic page.',limitation:'Numerical sums are not decoded words.',card:input,inputs:{version:'raw',alphabet_sha256:sha(L.stable(alphabet)),pages:[{id:'lp2-15',text_sha256:sha(raw)}]},control:{label:'Synthetic known word-sum ledger',task:controlTask,expected_result_sha256:sha(L.stable(controlResult))}},record={id:args.recordId,status:'published',browser_followups:[recipe]},calls=[],files=new Map([['/experiments/records/'+args.recordId+'/record.json',record],['/data/index.json',{alphabet}],['/data/pages/lp2-15.json',{id:'lp2-15',raw}]]);
 return {recipe,calls,fetcher:async(url,options)=>{const u=new URL(url);assert.equal(u.origin,origin);assert.equal(options.redirect,'manual');calls.push(u.pathname);assert(files.has(u.pathname));return Response.json(files.get(u.pathname));}};
}
async function load(f){const original=L.run,executed=[];L.run=task=>{assert.equal(task.pages[0].id,'lp1-01','Only the synthetic ledger may run during preparation');executed.push(task.taskId);return original(task);};try{return {value:await loadRecordPlan(args,{fetcher:f.fetcher}),executed};}finally{L.run=original;}}
const f=await fixture(),loaded=await load(f);assert.equal(loaded.value.state,'plan-ready');assert.deepEqual(loaded.value.task.steps,[]);assert.deepEqual(loaded.value.task.criterion,loaded.value.control.task.criterion);assert.deepEqual(loaded.executed,[f.recipe.control.task.taskId]);assert.equal(f.calls.length,3);
const {snapshot,...projection}=loaded.value;assert.deepEqual(JSON.parse(JSON.stringify(await frontend.validatePlan(projection,args,webcrypto))),projection);
const entry={origin:projection.origin,control:projection.control,question:projection.question,scopeChange:projection.scopeChange,limitation:projection.limitation},runner=readFileSync(new URL('../../tools/research_runner.py',import.meta.url),'utf8'),guard=readFileSync(new URL('../../tools/verify_controls.py',import.meta.url),'utf8'),zip=await Package.build(projection.task,runner,'http://127.0.0.1:8765/run.html#task='+projection.task.taskId,[entry],guard),folder=mkdtempSync(path.join(tmpdir(),'word-sum-package-'));
try{writeFileSync(path.join(folder,'package.zip'),zip);const code=`import pathlib,subprocess,sys,zipfile\np=pathlib.Path(sys.argv[1])\nwith zipfile.ZipFile(p/'package.zip') as z: z.extractall(p)\nsubprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','results.json'],cwd=p,check=True,stdout=subprocess.PIPE)\nsys.stdout.buffer.write((p/'results.json').read_bytes())`;const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',code,folder],{encoding:'utf8',maxBuffer:2000000}));assert.deepEqual(await L.verify(projection.task,result),L.run(projection.task));}finally{assert.equal(path.dirname(path.resolve(folder)),path.resolve(tmpdir()));assert(path.basename(folder).startsWith('word-sum-package-'));rmSync(folder,{recursive:true,force:true});}
for(const mutate of [async f=>f.recipe.control.expected_result_sha256='0'.repeat(64),async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{...f.recipe.control.task.criterion,table:'canonical'}})},async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{...f.recipe.control.task.criterion,boundaries:'hyphen-period'}})},async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,pages:[{id:'lp1-01',text:'---...'}]});f.recipe.control.expected_result_sha256=sha(L.stable(L.run(f.recipe.control.task)))},async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{kind:'exact-prefix',values:[0,1,2,0]}})}]){const broken=await fixture();await mutate(broken);await assert.rejects(()=>load(broken));assert(!broken.calls.some(p=>p.startsWith('/data/pages/')));}
console.log('PASS word prime sum plans: explicit canonical/reversed mappings, both boundaries and hand totals, strict op/evaluation/conflict rejection, no AI fallback, exact authored ledger control/hash, no target preparation-time execution.');
