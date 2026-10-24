/* Authored generic measurements: known synthetic recovery, never target execution. */
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {createHash,webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {loadRecordPlan} from './record-plans.mjs';
import {planCard} from './prepare-task.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
import Package from '../../local-run-package.js';
const sha=value=>createHash('sha256').update(value).digest('hex'),at='2026-10-24T12:00:00.000Z';
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
const args={recordId:'synthetic-measurement',followupId:'fixed-measurement'},text='ᚠᚩᚳ';
async function fixture(interrupted=false){
 const operation=interrupted?{id:'interrupted_repeating_key',label:'Interrupted repeating key',key:[1,2],direction:'subtract',reset:'page',interrupts:[0,19]}:{id:'reverse_runes',label:'Reverse rune order within each line',unit:'line'};
 const card=H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic exact measurement'},aim:known('Measure rune repeats'),method:known({operations:[operation]}),scope:known({pages:['lp2-15']}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known('measurement')}}),{id:'fixture',at})),plan=planCard(card);
 assert(!plan.reason,plan.reason);assert.deepEqual(plan.criterion,{kind:'measurement'});
 const criterion={kind:'exact-prefix',values:interrupted?[0,2,3]:[5,3,0]},controlTask=await L.prepare({title:'Synthetic known-answer recovery',pages:[{id:'lp1-01',text}],alphabet,steps:plan.steps,criterion});
 const recipe={id:args.followupId,title:'Synthetic target: do not execute during preparation',question:'What changes under the fixed rule?',scope_change:'Only the declared synthetic page.',limitation:'A measurement is not a language or decryption test.',card,inputs:{version:'raw',alphabet_sha256:sha(L.stable(alphabet)),pages:[{id:'lp2-15',text_sha256:sha(text)}]},control:{label:'Known synthetic recovery',task:controlTask,expected_result_sha256:sha(L.stable(L.run(controlTask)))}};
 const record={id:args.recordId,status:'published',browser_followups:[recipe]},files=new Map([['/experiments/records/'+args.recordId+'/record.json',record],['/data/index.json',{alphabet}],['/data/pages/lp2-15.json',{id:'lp2-15',raw:text}]]),calls=[];
 const fetcher=async(url,options)=>{const u=new URL(url);assert.equal(u.origin,'https://jelliottdev.github.io');assert.equal(options.redirect,'manual');calls.push(u.pathname);assert(files.has(u.pathname));return Response.json(files.get(u.pathname));};
 return {recipe,record,files,calls,fetcher};
}
async function loadWithoutTargetRun(f){
 const original=L.run,executed=[];L.run=task=>{assert.equal(task.pages.length,1);assert.equal(task.pages[0].id,'lp1-01','Preparing a plan must never execute manuscript target bytes');executed.push(task.taskId);return original(task);};
 try{return {value:await loadRecordPlan(args,{fetcher:f.fetcher}),executed};}finally{L.run=original;}
}
const frontendSource=readFileSync(new URL('../../record-followups.js',import.meta.url),'utf8'),exportNeedle='const api={reference,validateOrigins,createWorkspace}';assert(frontendSource.includes(exportNeedle));
const frontendContext={module:{exports:{}},require:createRequire(new URL('../../record-followups.js',import.meta.url)),btoa,TextEncoder,crypto:webcrypto};vm.createContext(frontendContext);vm.runInContext(frontendSource.replace(exportNeedle,'const api={validatePlan,reference,validateOrigins,createWorkspace}'),frontendContext);
const validatePlan=frontendContext.module.exports.validatePlan,runner=readFileSync(new URL('../../tools/research_runner.py',import.meta.url),'utf8'),guard=readFileSync(new URL('../../tools/verify_controls.py',import.meta.url),'utf8');
for(const interrupted of [false,true]){
 const f=await fixture(interrupted),before=structuredClone(f.record),{value,executed}=await loadWithoutTargetRun(f);
 assert.equal(value.state,'plan-ready');assert.deepEqual(value.task.criterion,{kind:'measurement'});assert.equal(value.card.rules.evaluation.value,'measurement');assert.equal(value.control.task.criterion.kind,'exact-prefix');assert.deepEqual(value.task.steps,value.control.task.steps);assert.deepEqual(value.task.pages,[{id:'lp2-15',text}]);assert.deepEqual(executed,[f.recipe.control.task.taskId]);assert.deepEqual(f.record,before);await L.checkIdentity(value.task);assert.equal(f.calls.length,3);
 const {snapshot,...projection}=value,checked=await validatePlan(projection,args,webcrypto);assert.deepEqual(JSON.parse(JSON.stringify(checked)),projection,'Actual frontend projection accepts the exact authored generic-measurement plan');
 for(const criterion of [{kind:'measurement'},{kind:'word-affine-count',lag:1,a:1,b:0,boundaries:'non-rune'}]){const invalid=structuredClone(projection);invalid.control.task=await L.prepare({...invalid.control.task,criterion});await assert.rejects(()=>validatePlan(invalid,args,webcrypto));}
 const partial=structuredClone(projection);partial.control.task=await L.prepare({...partial.control.task,criterion:{kind:'exact-prefix',values:partial.control.task.criterion.values.slice(0,1)}});partial.control.expected_result_sha256=sha(L.stable(L.run(partial.control.task)));await assert.rejects(()=>validatePlan(partial,args,webcrypto),'A true but partial synthetic prefix cannot certify a descriptive measurement');
 const wrong=structuredClone(projection);wrong.control.task=await L.prepare({...wrong.control.task,steps:[{op:'affine',a:1,b:1}]});await assert.rejects(()=>validatePlan(wrong,args,webcrypto));
 const entry={origin:value.origin,control:value.control,question:value.question,scopeChange:value.scopeChange,limitation:value.limitation},address='http://127.0.0.1:8765/run.html#task='+value.task.taskId,zip=await Package.build(value.task,runner,address,[entry],guard),folder=mkdtempSync(path.join(tmpdir(),'measurement-control-package-'));
 try{
  writeFileSync(path.join(folder,'package.zip'),zip);
  const code=`import pathlib,subprocess,sys,zipfile\np=pathlib.Path(sys.argv[1])\nwith zipfile.ZipFile(p/'package.zip') as z: z.extractall(p)\nsubprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','results.json'],cwd=p,check=True,stdout=subprocess.PIPE)\nsys.stdout.buffer.write((p/'results.json').read_bytes())`;
  const reproduced=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',code,folder],{encoding:'utf8',maxBuffer:2000000}));assert.deepEqual(await L.verify(value.task,reproduced),L.run(value.task));assert.deepEqual(reproduced.matches,[],'The synthetic recovery prefix is never imposed on a generic measurement target');
 }finally{assert.equal(path.dirname(path.resolve(folder)),path.resolve(tmpdir()));assert(path.basename(folder).startsWith('measurement-control-package-'));rmSync(folder,{recursive:true,force:true});}
 const fake=structuredClone(entry);fake.control.expected_result_sha256='0'.repeat(64);await assert.rejects(()=>Package.build(value.task,runner,address,[fake],guard),/result changed/);
}
const mutations=[
 async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{kind:'exact-prefix',values:[5]}});f.recipe.control.expected_result_sha256=sha(L.stable(L.run(f.recipe.control.task)));assert(L.run(f.recipe.control.task).matches[0].matched)},
 async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{kind:'measurement'}})},
 async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{kind:'word-affine-count',lag:1,a:1,b:0,boundaries:'non-rune'}})},
 async f=>{f.recipe.control.task.criterion={kind:'exact-prefix',values:[]}},
 async f=>{f.recipe.control.task.criterion={kind:'exact-prefix',values:[0],unknown:true}},
 async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,steps:[{op:'reverse',unit:'word'}]})},
 async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,alphabet:[...alphabet].reverse()})},
 async f=>{f.recipe.control.expected_result_sha256='0'.repeat(64)},
 async f=>{f.recipe.control.task=await L.prepare({...f.recipe.control.task,criterion:{kind:'exact-prefix',values:[0]}});f.recipe.control.expected_result_sha256=sha(L.stable(L.run(f.recipe.control.task)))},
];
for(const mutate of mutations){const f=await fixture();await mutate(f);await assert.rejects(()=>loadWithoutTargetRun(f));assert(!f.calls.some(path=>path.startsWith('/data/pages/')),'An invalid or failed control stops before target fetching');}
// A statistical measurement still requires its own matching statistical
// control; the generic-measurement allowance must not weaken that contract.
const stats=await fixture(),criterion={kind:'word-affine-count',lag:1,a:1,b:0,boundaries:'non-rune'};
stats.recipe.card.method.value.operations=[{id:'word_affine_count',label:'Within-word affine pair count',lag:1,a:1,b:0,boundaries:'non-rune'}];stats.recipe.card.rules.evaluation=known(criterion);
await assert.rejects(()=>loadWithoutTargetRun(stats));assert(!stats.calls.some(path=>path.startsWith('/data/pages/')));
console.log('PASS authored generic measurement controls: explicit measurement target, exact synthetic prefix for classical/interrupted rules, full control hash/prefix, malformed/statistical/steps/alphabet rejection, unchanged records, no preparation-time target execution or failed-control target fetch.');
console.log('PASS generic-measurement frontend/package: actual private projection validator accepts exact provenance and rejects incompatible controls; extracted fixed Python guard verifies synthetic prefix then independently reproduces measurement without a target prefix.');
