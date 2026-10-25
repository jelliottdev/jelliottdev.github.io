import {DatabaseSync} from 'node:sqlite';
/* Exact canonical interrupter plans only: mocked storage/assets/provider, no network. */
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {createRequire} from 'node:module';
import {createHash,webcrypto} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {planCard,createPrepareTaskHandler} from './prepare-task.mjs';
import {createAIPlanner,validateCandidate} from './propose-task-plan.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
import RunUI from '../../run.js';
import Package from '../../local-run-package.js';
let id;
const at='2026-10-24T12:00:00.000Z',origin='https://jelliottdev.github.io';
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
const base={id:'interrupted_repeating_key',label:'Interrupted repeating key',key:[1,2,28],direction:'subtract',reset:'page',interrupts:[0,19]};
const card=(operation=base,rules={})=>H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic explicit interrupter specification'},aim:known('Measure the output'),method:known({operations:[operation]}),scope:known({pages:['lp2-15']}),rules}),{id:'fixture',at}));
const makeFixture=input=>{
 const sqlite=new DatabaseSync(':memory:');for(const name of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql','0005_research_ideas.sql','0006_task_ideas.sql','0007_task_origins.sql','0008_prepared_plans.sql','0009_word_boundary_preparations.sql','0010_family_case_results.sql','0011_task_protocol_lookup.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 const stored=C.serialize(input),hash=createHash('sha256').update(stored).digest('hex');id='p_'+hash;sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,hash,stored,'unused',at);
 let reads=0,calls=0,inference=0;const env={SITE_ORIGIN:origin,PROPOSALS:{prepare(sql){assert(/^\s*(?:SELECT\b|INSERT INTO (?:prepared_plans|idea_computation_evidence)\b)/.test(sql));return {bind(...args){return {first:async()=>{reads++;return sqlite.prepare(sql).get(...args)||null;},all:async()=>{reads++;return {results:sqlite.prepare(sql).all(...args)};},run:async()=>sqlite.prepare(sql).run(...args)};}};}},TASK_LIMIT:{limit:async()=>({success:true})},AI:{run(){inference++;throw Error('No model call permitted');}}};
 const handle=createPrepareTaskHandler({fetcher:async url=>{calls++;assert.equal(url,origin+'/data/pages/lp2-15.json');return Response.json({id:'lp2-15',raw:'ᚢᚠᚩ\nᚱ',reviewed_text:'ᚱᚠᚩ'});}});
 return {env,handle,sqlite,get reads(){return reads},get calls(){return calls},get inference(){return inference}};
};
const request=()=>new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify({proposalId:id,parentTaskId:null})});
for(const direction of ['add','subtract'])for(const reset of ['page','line','word']){
 const operation={...base,direction,reset},input=card(operation,{reset:known('reset at each '+reset),inputVersion:known('reviewed'),evaluation:known({kind:'exact-prefix',values:[0,1]})}),before=structuredClone(input),plan=planCard(input);
 assert(!plan.reason,plan.reason);assert.deepEqual(plan.steps,[{op:'interrupted-keyed-shift',key:[1,2,28],direction,reset,interrupts:[0,19]}]);assert.equal(plan.inputVersion,'reviewed');assert.deepEqual(plan.criterion,{kind:'exact-prefix',values:[0,1]});assert.deepEqual(input,before);assert(plan.notes.some(n=>n.includes('current step input')&&n.includes('do not advance')));
}
const invalid=[...['label','key','direction','reset','interrupts'].map(key=>{const op={...base};delete op[key];return op}),...[[],[29],[-1],[0,0],[19,0],[1.5],'F',Array(30).fill(0)].map(interrupts=>({...base,interrupts})),...[[],Array(257).fill(1),[29],[-1],[1.5],'ABC'].map(key=>({...base,key})),...['mode','phase','carry','a','unit','skip'].map(key=>({...base,[key]:1})),{...base,label:'Interrupted repeating key except the heading'}];
for(const operation of invalid){const input=card(operation);assert(planCard(input).reason);const f=makeFixture(input),response=await f.handle(request(),f.env),value=await response.json();assert.equal(value.state,'needs-adapter');assert.equal(f.calls,0);assert.equal(f.inference,0,'Failed canonical compilation cannot be repaired by an AI downgrade');}
for(const rules of [{reset:known('word')},{reset:C.field('not_applicable')},{initialState:known(0)},{initialState:known(1)},{exceptionalCases:known('Skip another rune')},{searchProtocol:known('Continue across pages')}])assert(planCard(card(base,rules)).reason);
assert(planCard(card({id:'repeating_key',label:'Repeating key',key:[1],direction:'subtract',reset:'page',interrupts:[0]})).reason,'Ordinary keyed methods cannot silently consume interrupters');
const max=planCard(card({...base,key:Array(256).fill(28),interrupts:Array.from({length:29},(_,i)=>i)}));assert(!max.reason,max.reason);assert.equal(max.steps[0].interrupts.length,29);
const f=makeFixture(card()),response=await f.handle(request(),f.env),value=await response.json();assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.match(value.preparation.id,/^prep_[a-f0-9]{64}$/);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert(value.task.title.includes('Interrupted repeating-key subtraction'));assert(!value.task.title.includes('Cumulative'));assert.deepEqual(value.task.steps,planCard(card()).steps);await L.checkIdentity(value.task);assert.equal(f.calls,1);assert.equal(f.inference,0);
// Candidate validation also rejects attempted downgrades from explicit fields.
const phrase='repeating key with key indices [1], subtract, reset at each page',downgrade={version:1,steps:[{source:{operationIndex:0,start:0,quote:phrase},step:{op:'keyed-shift',key:[1],mode:'repeat',direction:'subtract',reset:'page'}}],unsupported:[]};
for(const operation of [{...base,label:phrase},{id:'described_method',label:phrase,interrupts:[0]},{id:'repeating_key',label:phrase,key:[1],direction:'subtract',reset:'page',interrupts:[0]}]){
 const input=card(operation);assert(validateCandidate(input,downgrade,{compile:planCard}).reason);let calls=0;const result=await createAIPlanner({compile:planCard,AI:{run(){calls++;return {};}}})(input);assert(result.reason);assert.equal(calls,0);
}
// Execute the actual private frontend compiler; add a test-only export in the
// VM source rather than maintaining a parallel card-to-program implementation.
const frontendSource=readFileSync(new URL('../../record-followups.js',import.meta.url),'utf8'),exportNeedle='const api={reference,validateOrigins,createWorkspace}';
assert(frontendSource.includes(exportNeedle));
const frontendContext={module:{exports:{}},require:createRequire(new URL('../../record-followups.js',import.meta.url)),btoa,TextEncoder,crypto:webcrypto};
vm.createContext(frontendContext);vm.runInContext(frontendSource.replace(exportNeedle,'const api={cardProgram,reference,validateOrigins,createWorkspace}'),frontendContext);
const cardProgram=frontendContext.module.exports.cardProgram;
for(const direction of ['add','subtract'])for(const reset of ['page','line','word']){
 const operation={...base,direction,reset},input=card(operation,{inputVersion:known('raw'),representation:known('GP29'),reset:known(reset),evaluation:known({kind:'exact-prefix',values:[0,2,3]})}),before=structuredClone(input),compiled=cardProgram(input),backend=planCard(input);
 assert.deepEqual(JSON.parse(JSON.stringify(compiled.steps)),backend.steps);assert.deepEqual(JSON.parse(JSON.stringify(compiled.pages)),backend.pages);assert.deepEqual(JSON.parse(JSON.stringify(compiled.criterion)),backend.criterion);assert.equal(compiled.inputVersion,backend.inputVersion);assert.deepEqual(input,before);
 assert.deepEqual(C.classifyMethod(input.method).familyIds,['polyalphabetic']);assert.equal(C.classifyMethod(input.method).complete,true,'Interrupters reuse the maintained repeating-key family');
 const text=RunUI.stepText(backend.steps[0]);assert(text.includes('['+base.key.join(', ')+']'));assert(text.includes(direction+' modulo 29'));assert(text.includes('restart at each '+reset));assert(text.includes('Copy input rune indices [0, 19] unchanged without advancing the key'));assert(text.includes('this step’s input, not decoded text'));
}
for(const operation of [{...base,label:'Interrupted repeating key except F'},{...base,mode:'repeat'},{...base,phase:1},{...base,arbitrary:'ignored'}]){
 const input=card(operation,{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:[0]})});assert.throws(()=>cardProgram(input),'Frontend refuses unsupported fields and wording rather than dropping them');
}
// The optional package verifies a full synthetic control, then reproduces the
// same interrupted task independently through the fixed Python runner.
const steps=planCard(card()).steps,criterion={kind:'exact-prefix',values:[0,2,3]},syntheticText='ᚠᚩᚳ',task=await L.prepare({title:'Synthetic interrupted reproduction',alphabet,pages:[{id:'lp2-15',text:syntheticText}],steps,criterion}),controlTask=await L.prepare({title:'Synthetic interrupted known answer',alphabet,pages:[{id:'lp1-01',text:syntheticText}],steps,criterion});
assert.deepEqual(Array.from(L.run(controlTask).transformed[0].text),[alphabet[0].rune,alphabet[2].rune,alphabet[3].rune]);
const runner=readFileSync(new URL('../../tools/research_runner.py',import.meta.url),'utf8'),guard=readFileSync(new URL('../../tools/verify_controls.py',import.meta.url),'utf8'),origins=[{origin:{recordId:'synthetic-interrupted',followupId:'fixed-rule',recordSha256:'a'.repeat(64),protocolSha256:'b'.repeat(64)},control:{label:'Synthetic interrupted control',task:controlTask,expected_result_sha256:createHash('sha256').update(L.stable(L.run(controlTask))).digest('hex')},question:'Does the exact synthetic prefix match?',scopeChange:'Only the declared synthetic page.',limitation:'A synthetic prefix is not a manuscript result.'}];
const zip=await Package.build(task,runner,'http://127.0.0.1:8765/run.html#task='+task.taskId,origins,guard),folder=mkdtempSync(path.join(tmpdir(),'interrupted-package-'));
try{
 writeFileSync(path.join(folder,'package.zip'),zip);
 const code=`import json,pathlib,subprocess,sys,zipfile\np=pathlib.Path(sys.argv[1])\nwith zipfile.ZipFile(p/'package.zip') as z: z.extractall(p)\nsubprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','results.json'],cwd=p,check=True,stdout=subprocess.PIPE)\nsys.stdout.buffer.write((p/'results.json').read_bytes())`;
 const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',code,folder],{encoding:'utf8',maxBuffer:2000000}));assert.deepEqual(await L.verify(task,result),L.run(task));
}finally{assert.equal(path.dirname(path.resolve(folder)),path.resolve(tmpdir()));assert(path.basename(folder).startsWith('interrupted-package-'));rmSync(folder,{recursive:true,force:true});}
console.log('PASS interrupted repeating-key planning: exact canonical fields, all directions/resets, source version/criterion, max bounds, no mutation, explicit titles, malformed/conflicting rejection before source fetch, no AI downgrade.');
console.log('PASS interrupted shared integration: actual frontend compiler parity, maintained polyalphabetic family, faithful step copy, malformed frontend refusal, complete synthetic package control and independent Python reproduction.');
