'use strict';
// Invented pages only; derivation must never execute the target or access storage.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),V=require('../task-parameter-variants.js');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'),alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),text='ᚠᚢ ᚦᚩ-ᚱᚳ\r\nᚷᚹ.ᚻᚾ',copy=value=>JSON.parse(JSON.stringify(value));
const modes=['repeat','plaintext-autokey','ciphertext-autokey'].map(mode=>({op:'keyed-shift',mode,key:[0,28,7],direction:'subtract',reset:'page'}));modes.push({op:'interrupted-keyed-shift',key:[0,28,7],direction:'subtract',reset:'page',interrupts:[0,7]},{op:'finite-shift',key:Array.from({length:25},(_,i)=>i%29),direction:'subtract',reset:'page'},{op:'cumulative-difference',reset:'page'});
const criterion={kind:'exact-prefix-set',openings:[{id:'invented-a',values:[0,1,2]},{id:'invented-b',values:[4,5]}]};
async function task(steps,patch={}){return E.prepare({title:'Invented saved parent',pages:[{id:'lp2-00',text},{id:'lp2-01',text:'ᚪᚫ-ᚣᛡᛠ'}],alphabet,steps,criterion,...patch},webcrypto);}
let groups=0;async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
async function rejectsMutation(start,change){let release;const blocked=new Promise(resolve=>{release=resolve;}),crypto={subtle:{digest:async(...args)=>{await blocked;return webcrypto.subtle.digest(...args);}}},pending=start(crypto);change();release();await assert.rejects(pending,/changed|identity|outside|Unexpected|Missing/);}
(async()=>{
 await test('all six modes expose only supported other values and preserve every unrelated field',async()=>{
  const run=E.run;E.run=()=>assert.fail('No target execution in variant derivation');
  try{for(const mode of modes){
   const parent=await task([mode]),before=E.stable(parent),descriptors=V.list(parent);assert.equal(descriptors.length,mode.op==='cumulative-difference'?2:mode.op==='keyed-shift'?5:3);assert(Object.isFrozen(descriptors));
   for(const descriptor of descriptors){assert(Object.isFrozen(descriptor));assert(Object.isFrozen(descriptor.selection));assert.equal(descriptor.from,parent.steps[0][descriptor.selection.parameter]);
    const child=await V.prepare(parent,descriptor.selection,webcrypto);assert.deepEqual(await V.validate(parent,child,descriptor.selection,webcrypto),child);assert(Object.isFrozen(child));assert.notEqual(child.taskId,parent.taskId);
    const expectedSteps=copy(parent.steps);expectedSteps[0][descriptor.selection.parameter]=descriptor.selection.value;assert.deepEqual(child.steps,expectedSteps);assert.deepEqual(child.pages,parent.pages);assert.deepEqual(child.alphabet,parent.alphabet);assert.deepEqual(child.criterion,parent.criterion);assert.equal(E.stable(parent),before);assert.deepEqual(await V.prepare(parent,descriptor.selection,webcrypto),child);assert.equal(Array.from(child.title).length<=300,true);
   }
  }}finally{E.run=run;}
 });
 await test('eight-step plans change the explicitly selected step, not another matching operation',async()=>{
  const steps=[{op:'reverse',unit:'word'},...modes,copy(modes[0])],parent=await task(steps),selection={version:1,step:7,parameter:'reset',value:'word'},child=await V.prepare(parent,selection,webcrypto);
  assert.equal(child.steps.length,8);assert.deepEqual(child.steps.slice(0,7),parent.steps.slice(0,7));assert.equal(child.steps[7].reset,'word');assert.deepEqual(child.steps[7].key,parent.steps[7].key);assert(V.list(parent).some(d=>d.selection.step===7));
 });
 await test('finite keys retain their full literal tail and reject larger reset segments without wrapping',async()=>{
  const parent=await task([{op:'finite-shift',key:[0,1,2],direction:'add',reset:'word'}],{pages:[{id:'lp2-00',text:'ᚠᚢ ᚦᚩ\nᚱᚳ ᚷᚹ'}]});
  assert.deepEqual(V.list(parent).map(d=>d.selection),[{version:1,step:0,parameter:'direction',value:'subtract'}]);
  for(const value of ['line','page'])await assert.rejects(V.prepare(parent,{version:1,step:0,parameter:'reset',value},webcrypto),/shorter/);
  const long=await task([modes[4]]),child=await V.prepare(long,{version:1,step:0,parameter:'reset',value:'word'},webcrypto);assert.deepEqual(child.steps[0].key,modes[4].key);assert.equal(child.steps[0].key.length,25);
 });
 await test('closed selections refuse no-op, unknown fields, unsupported steps and ambiguous indices',async()=>{
  const parent=await task([modes[0]]),selection={version:1,step:0,parameter:'direction',value:'add'};
  for(const patch of [{version:2},{step:-1},{step:1},{step:0.5},{step:true},{parameter:'key'},{value:'multiply'},{value:'subtract'},{extra:true}])await assert.rejects(V.prepare(parent,{...selection,...patch},webcrypto));
  for(const steps of [[],[{op:'affine',a:1,b:0}]]){const t=await task(steps);assert.deepEqual(V.list(t),[]);await assert.rejects(V.prepare(t,selection,webcrypto));}
  const corrupt=copy(parent);corrupt.taskId='0'.repeat(64);await assert.rejects(V.prepare(corrupt,selection,webcrypto),/changed/);
 });
 await test('safe capture rejects getters, sparse arrays, symbols and unsafe objects without invoking them',async()=>{
  const parent=await task([modes[0]]),selection={version:1,step:0,parameter:'direction',value:'add'};let calls=0;
  const getter=copy(parent);Object.defineProperty(getter,'pages',{enumerable:true,get(){calls++;return parent.pages;}});assert.throws(()=>V.list(getter));await assert.rejects(V.prepare(getter,selection,webcrypto));assert.equal(calls,0);
  const badSelection={...selection};Object.defineProperty(badSelection,'value',{enumerable:true,get(){calls++;return 'add';}});await assert.rejects(V.prepare(parent,badSelection,webcrypto));assert.equal(calls,0);
  for(const change of [t=>delete t.steps[0],t=>{t[Symbol('hidden')]=1;},t=>Object.setPrototypeOf(t,{bad:true}),t=>Object.defineProperty(t,'toJSON',{enumerable:true,value(){calls++;return parent;}}),t=>Object.defineProperty(t,'__proto__',{enumerable:true,value:{bad:true}})]){const bad=copy(parent);change(bad);assert.throws(()=>V.list(bad));await assert.rejects(V.prepare(bad,selection,webcrypto));}assert.equal(calls,0);
 });
 await test('validated children reject rehashed changes to criterion, text, other steps, keys and title',async()=>{
  const parent=await task([modes[0],modes[3]]),selection={version:1,step:0,parameter:'direction',value:'add'},child=await V.prepare(parent,selection,webcrypto);
  for(const change of [t=>{t.title='Different title';},t=>{t.pages[0].text+='ᚠ';},t=>{t.criterion.openings[0].values[0]=3;},t=>{t.steps[0].key[0]=1;},t=>{t.steps[1].interrupts=[1,7];},t=>{t.steps[1].reset='word';}]){const bad=copy(child);change(bad);bad.taskId=await E.identity(bad,webcrypto);await assert.rejects(V.validate(parent,bad,selection,webcrypto),/more than/);}
  const bad=copy(child);bad.taskId='0'.repeat(64);await assert.rejects(V.validate(parent,bad,selection,webcrypto));
 });
 await test('async mutation of parent, child or selection cannot cross the hash boundary',async()=>{
  const selection={version:1,step:0,parameter:'direction',value:'add'},parent=await task([modes[0]]);
  await rejectsMutation(crypto=>V.prepare(parent,selection,crypto),()=>{parent.pages[0].text+='ᚠ';});
  const parent2=await task([modes[0]]),chosen={...selection};await rejectsMutation(crypto=>V.prepare(parent2,chosen,crypto),()=>{chosen.value='subtract';});
  const child=copy(await V.prepare(parent2,selection,webcrypto));await rejectsMutation(crypto=>V.validate(parent2,child,selection,crypto),()=>{child.steps[0].key[0]=1;});
 });
 await test('browser export uses only declared engine and plain JSON helper dependencies',async()=>{
  const context={LocalExperiment:E,FiniteJSON:require('../finite-json.js'),TextEncoder,crypto:webcrypto};vm.createContext(context);vm.runInContext(fs.readFileSync('task-parameter-variants.js','utf8'),context);assert.equal(typeof context.TaskParameterVariants.prepare,'function');const parent=await task([modes[0]]),selection={version:1,step:0,parameter:'reset',value:'line'},child=await context.TaskParameterVariants.prepare(parent,selection,webcrypto);assert.equal(child.steps[0].reset,'line');assert.deepEqual(await context.TaskParameterVariants.validate(parent,child,selection,webcrypto),child);
 });
 console.log(groups+' closed task-parameter variation groups passed; invented text only, no target execution or I/O.');
})().catch(error=>{console.error(error);process.exitCode=1;});
