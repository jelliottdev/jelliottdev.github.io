'use strict';
/* Structural phase changes only. No manuscript calculations or persistence. */
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js'),V=require('../task-parameter-variants.js'),Q=require('../task-parameter-question.js'),F=require('../fixed-plan-compiler.js');
const bundle=require('../data/local-run-inputs.json'),alphabet=bundle.alphabet,copy=structuredClone;
const choice=(value=1,step=0)=>({version:1,step,parameter:'phase',value});
const body=(key=[1,2,3],reset='page')=>({title:'Invented phase fixture',alphabet,pages:[{id:'lp2-00',text:alphabet.slice(0,8).map(r=>r.rune).join('')+' /\n'+alphabet.slice(1,5).map(r=>r.rune).join('')}],steps:[{op:'keyed-shift',mode:'repeat',key,direction:'subtract',reset}],criterion:{kind:'exact-prefix',values:[0,1]}});
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{const run=E.run;E.run=()=>assert.fail('Phase preparation must not execute target output');try{
await test('every phase changes only the selected literal repeating key for all three reset clocks',async()=>{
 for(const reset of ['page','line','word']){const task=await E.prepare(body([1,2,3,4],reset)),before=E.stable(task),choices=V.list(task).filter(x=>x.selection.parameter==='phase');assert.deepEqual(choices.map(c=>c.selection.value),[1,2,3]);for(const item of choices){assert.equal(item.from,0);const child=await V.prepare(task,item.selection);assert.deepEqual(child.steps,[{...task.steps[0],key:task.steps[0].key.slice(item.selection.value).concat(task.steps[0].key.slice(0,item.selection.value))}]);assert.deepEqual(child.pages,task.pages);assert.deepEqual(child.criterion,task.criterion);assert.deepEqual(child.alphabet,task.alphabet);assert.notEqual(child.taskId,task.taskId);assert.deepEqual(await V.validate(task,child,item.selection),child);assert(Object.isFrozen(child.steps[0].key));}assert.equal(E.stable(task),before);}
});
await test('periodic keys deduplicate and identity, unreachable-prefix and downstream-constant changes disappear',async()=>{
 const periodic=await E.prepare(body([1,2,1,2]));assert.deepEqual(V.list(periodic).filter(x=>x.selection.parameter==='phase').map(x=>x.selection.value),[1]);await assert.rejects(V.prepare(periodic,choice(2)),/unchanged/);
 const constant=await E.prepare(body([7,7,7]));assert.equal(V.list(constant).filter(x=>x.selection.parameter==='phase').length,0);
 const shortBody=body([1,1,2]);shortBody.pages[0].text=alphabet[0].rune;const short=await E.prepare(shortBody);assert(V.list(short).some(x=>x.selection.parameter==='phase'&&x.selection.value===1));assert(!V.suggestions(short).some(x=>x.selection.parameter==='phase'&&x.selection.value===1));
 const later=body();later.steps.push({op:'affine',a:0,b:4});assert.equal(V.suggestions(await E.prepare(later)).filter(x=>x.selection.parameter==='phase').length,0);
 const prior=body();prior.steps.unshift({op:'reverse',unit:'word'},{op:'affine',a:3,b:5});const task=await E.prepare(prior);assert(V.suggestions(task).some(x=>x.selection.parameter==='phase'));const child=await V.prepare(task,choice(1,2));assert.deepEqual(child.steps.slice(0,2),task.steps.slice(0,2));
});
await test('unsupported operations modes malformed selectors and extra child deltas reject',async()=>{
 for(const value of [0,-1,256,1.5,'1',null,[1],true])assert.throws(()=>V.selection(choice(value)));
 const task=await E.prepare(body());for(const value of [3,4,255])await assert.rejects(V.prepare(task,choice(value)));
 for(const mode of ['plaintext-autokey','ciphertext-autokey']){const b=body();b.steps[0].mode=mode;await assert.rejects(V.prepare(await E.prepare(b),choice()),/support/);}
 for(const op of ['finite-shift','interrupted-keyed-shift']){const b=body();b.steps[0]={op,key:Array(30).fill(1),direction:'subtract',reset:'page',...(op==='interrupted-keyed-shift'?{interrupts:[0]}:{})};await assert.rejects(V.prepare(await E.prepare(b),choice()),/support/);}
 const child=await V.prepare(task,choice()),changed=copy(child);changed.steps[0].direction='add';const forged=await E.prepare(changed);await assert.rejects(V.validate(task,forged,choice()),/more than/);const bad=copy(task);bad.taskId='0'.repeat(64);await assert.rejects(V.prepare(bad,choice()));
 let reads=0;const getter=choice();Object.defineProperty(getter,'value',{enumerable:true,get(){reads++;return 1;}});assert.throws(()=>V.selection(getter));assert.equal(reads,0);
});
await test('parent and selection mutations during hashing are rejected',async()=>{
 for(const target of ['parent','selection']){const task=copy(await E.prepare(body())),selection=choice();let first=true;const crypto={subtle:{digest:async(...args)=>{const result=await webcrypto.subtle.digest(...args);if(first){first=false;if(target==='parent')task.steps[0].key[0]=9;else selection.value=2;}return result;}}};await assert.rejects(V.prepare(task,selection,crypto),/changed/);}
});
await test('shared structural delta is detached and rejects malformed target steps without fake task authority',async()=>{
 const steps=[{op:'affine',a:2,b:4},body().steps[0]],before=E.stable(steps),changed=V.changedSteps(steps,choice(1,1));assert.deepEqual(changed[0],steps[0]);assert.deepEqual(changed[1].key,[2,3,1]);assert.equal(E.stable(steps),before);assert(Object.isFrozen(changed[1].key));steps[1].key[0]=9;assert.equal(changed[1].key[2],1);
 assert.deepEqual(V.changedSteps([{op:'affine',a:2,b:4}],{version:1,step:0,parameter:'a',value:0}),[{op:'affine',a:0,b:4}]);
 for(const mutate of [s=>s[0].extra=true,s=>s[0].key=[1,'2'],s=>s[0].mode='unknown',s=>s[0].reset='paragraph',s=>s[0].key=Array(257).fill(1)]){const bad=[copy(body().steps[0])];mutate(bad);assert.throws(()=>V.changedSteps(bad,choice()));}
 let calls=0;const getter=[copy(body().steps[0])];Object.defineProperty(getter[0],'key',{enumerable:true,get(){calls++;return [1,2];}});assert.throws(()=>V.changedSteps(getter,choice()));assert.equal(calls,0);assert.throws(()=>V.changedSteps(Array(9).fill({op:'affine',a:1,b:0}),choice()));
 const longest=await E.prepare(body(Array.from({length:256},(_,i)=>i%29)));assert.equal((await V.prepare(longest,choice(255))).steps[0].key[0],longest.steps[0].key[255]);
});
await test('browser UMD exports the identical bounded structural phase contract',async()=>{
 const vm=require('node:vm'),scope=vm.createContext({LocalExperiment:E,FiniteJSON:require('../finite-json.js'),crypto:webcrypto,TextEncoder,TextDecoder});vm.runInContext(fs.readFileSync('task-parameter-variants.js','utf8'),scope);const browser=scope.TaskParameterVariants,task=await E.prepare(body());assert.equal(E.stable(browser.changedSteps(task.steps,choice())),E.stable(V.changedSteps(task.steps,choice())));assert.equal(E.stable(await browser.prepare(task,choice())),E.stable(await V.prepare(task,choice())));assert.equal(E.stable(browser.list(task)),E.stable(V.list(task)));
});
await test('all 74 current repeated-key programs expose canonical phase children with exact original scope and criterion',async()=>{
 const catalog=JSON.parse(fs.readFileSync('data/published-program-source-catalog.json','utf8')),rows=catalog.entries.filter(e=>e.steps.some(s=>s.op==='keyed-shift'&&s.mode==='repeat'&&s.key.length>1));assert.equal(rows.length,74);let phased=0;
 for(const entry of rows){const task=await E.prepare({title:'Metadata-only phase compatibility',alphabet,pages:entry.pages.map(p=>({id:p.id,text:bundle.pages.find(b=>b.id===p.id).raw})),steps:entry.steps,criterion:entry.criterion}),parent=await Q.archived({task,inputVersion:entry.inputVersion}),choices=V.suggestions(task).filter(c=>c.selection.parameter==='phase');assert(choices.length>0);const result=await Q.prepare({parentTask:task,parentCard:parent.card,inputVersion:entry.inputVersion,selection:choices[0].selection});const plan=F.compile(result.card);assert.deepEqual(plan.steps,result.task.steps);assert.deepEqual(plan.pages,entry.pages.map(p=>p.id));assert.deepEqual(plan.criterion,entry.criterion);assert.deepEqual(result.card.outcome,parent.card.outcome);assert.deepEqual(result.task.pages,task.pages);await Q.validate({parentTask:task,parentCard:parent.card,inputVersion:entry.inputVersion,selection:choices[0].selection},result);phased++;}
 assert.equal(phased,74);
});
}finally{E.run=run;}console.log(groups+' phase variation groups passed; no target execution or novelty claims.');})().catch(error=>{console.error(error);process.exitCode=1;});
