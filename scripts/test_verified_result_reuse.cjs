/* Verified display receipts remain immutable; rendering never reruns a target. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{webcrypto}=require('node:crypto'),{performance}=require('node:perf_hooks');
const E=require('../local-experiment.js'),Score=require('../language-score.js'),Evaluators=require('../output-evaluators.js');
const root=path.resolve(__dirname,'..'),alphabet=JSON.parse(fs.readFileSync(path.join(root,'data/local-run-inputs.json'),'utf8')).alphabet;
const body=(criterion={kind:'measurement'},n=50)=>({title:'Immutable display fixture',alphabet,pages:[{id:'lp2-15',text:Array.from({length:n},(_,i)=>alphabet[(i*i+3*i)%29].rune).join('')}],steps:[{op:'reverse',unit:'word'}],criterion});
const clone=value=>JSON.parse(JSON.stringify(value));
function measuredEngine(){
 const counts={transforms:0,scores:0},module={exports:{}};
 const context=vm.createContext({module,crypto:webcrypto,TextEncoder,TextDecoder,counts,require(name){assert.equal(name,'./language-score.js');return {...Score,evaluate(values){counts.scores++;return Score.evaluate(values);}};}});
 const source=fs.readFileSync(path.join(root,'local-experiment.js'),'utf8');assert(source.includes('function transform(text,steps,alphabet){'));
 vm.runInContext(source.replace('function transform(text,steps,alphabet){','function transform(text,steps,alphabet){ root.counts.transforms++;'),context);
 return {engine:module.exports,counts};
}
function frozenTree(value){if(value&&typeof value==='object'){assert(Object.isFrozen(value));for(const child of Object.values(value))frozenTree(child);}}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('only independently computed receipts become deeply immutable; submitted data stays caller owned',async()=>{
  const task=await E.prepare(body()),raw=E.run(task),verified=await E.verify(task,raw);assert.notEqual(verified,raw);assert.deepEqual(verified,raw);frozenTree(verified);
  assert(!Object.isFrozen(task));assert(!Object.isFrozen(task.pages));assert(!Object.isFrozen(raw));assert(!Object.isFrozen(raw.metrics));
  for(const mutate of [()=>verified.metrics.runes++,()=>verified.transformed[0].text+='ᚠ',()=>verified.transformed.push({}),()=>{verified.matches=[];},()=>Object.setPrototypeOf(verified,{}),()=>Object.defineProperty(verified.metrics,'runes',{get:()=>0}),()=>{verified.accepted=true;}])assert.throws(mutate,TypeError);
  raw.metrics.runes++;assert.doesNotThrow(()=>E.summary(task,verified));assert.throws(()=>E.summary(task,raw));assert.throws(()=>E.summary(task,clone(verified)));assert.throws(()=>E.summary(task,Object.create(verified)));
 });
 await test('task changes, forged clones, prototypes and accessors cannot inherit verified status',async()=>{
  const task=await E.prepare(body()),verified=await E.verify(task,E.run(task));
  for(const mutate of [t=>{t.title+=' changed';},t=>{t.pages[0].text+='ᚠ';},t=>{t.criterion={kind:'exact-prefix',values:[0]};},t=>{t.steps.reverse();t.steps.push({op:'affine',a:1,b:1});},t=>Object.setPrototypeOf(t,{}),t=>Object.setPrototypeOf(t.pages[0],null),t=>Object.defineProperty(t.pages[0],'text',{get:()=>task.pages[0].text,enumerable:true}),t=>{t[Symbol('hidden')]=true;}]){const changed=clone(task);mutate(changed);assert.throws(()=>E.summary(changed,verified));}
  assert.deepEqual(E.summary(clone(task),verified),E.summary(task,verified),'Equivalent plain JSON retains the exact original computation signature');
  const original=task.pages[0].text;task.pages[0].text+='ᚠ';assert.throws(()=>E.summary(task,verified));task.pages[0].text=original;assert.doesNotThrow(()=>E.summary(task,verified));
  const accessor=clone(task);Object.defineProperty(accessor,'pages',{enumerable:true,get:()=>task.pages});await assert.rejects(()=>E.verify(accessor,E.run(task)));
 });
 await test('plain JSON from another realm verifies and displays without granting result-clone trust',async()=>{
  const task=await E.prepare(body(Evaluators.criterion())),foreign=vm.runInNewContext('JSON.parse(payload)',{payload:JSON.stringify(task)});
  assert.notEqual(Object.getPrototypeOf(foreign),Object.prototype);assert.notEqual(Object.getPrototypeOf(foreign.pages),Array.prototype);
  const raw=E.run(foreign),verified=await E.verify(foreign,raw);assert.doesNotThrow(()=>E.summary(foreign,verified));assert.deepEqual(E.summary(task,verified),E.summary(foreign,verified));
  const resultClone=vm.runInNewContext('JSON.parse(payload)',{payload:JSON.stringify(verified)});assert.throws(()=>E.summary(foreign,resultClone));
  for(const code of ['Object.setPrototypeOf(value,{})','Object.setPrototypeOf(value.pages,[])',"Object.defineProperty(value.pages[0],'text',{get(){return 'ᚠ';},enumerable:true})"]){const altered=vm.runInNewContext('const value=JSON.parse(payload);'+code+';value',{payload:JSON.stringify(task)});assert.throws(()=>E.summary(altered,verified));await assert.rejects(()=>E.verify(altered,raw));}
 });
 await test('task mutation across asynchronous identity verification cannot acquire a display receipt',async()=>{
  const task=await E.prepare(body()),raw=E.run(task);let resume,started;
  const waiting=new Promise(resolve=>{started=resolve;}),gate=new Promise(resolve=>{resume=resolve;});
  const cryptoAPI={subtle:{digest:async(...args)=>{const answer=await webcrypto.subtle.digest(...args);started();await gate;return answer;}}};
  const verification=E.verify(task,raw,cryptoAPI);await waiting;task.title+=' changed while hashing';resume();await assert.rejects(verification,/changed during verification/);assert.throws(()=>E.summary(task,raw));
 });
 await test('every verification replays independently; repeated language summaries never transform or rescore',async()=>{
  const {engine,counts}=measuredEngine(),task=await engine.prepare(body(Evaluators.criterion())),raw=engine.run(task);assert.equal(counts.scores,1);
  const verified=await engine.verify(task,raw);assert.equal(counts.scores,2);assert.equal(counts.transforms,2);
  const first=engine.summary(task,verified);for(let i=0;i<12;i++)assert.equal(engine.summary(task,verified).finding,first.finding);assert.equal(counts.scores,2);assert.equal(counts.transforms,2);
  await engine.verify(task,raw);assert.equal(counts.scores,3);assert.equal(counts.transforms,3);
 });
 await test('measurement and exact-prefix summaries cache only the baseline, with unchanged findings',async()=>{
  for(const criterion of [{kind:'measurement'},{kind:'exact-prefix',values:[0]}]){
   const {engine,counts}=measuredEngine(),task=await engine.prepare(body(criterion)),verified=await engine.verify(task,engine.run(task));
   const first=engine.summary(task,verified);assert.equal(counts.transforms,3);for(let i=0;i<10;i++)assert.equal(engine.summary(task,verified).finding,first.finding);assert.equal(counts.transforms,3);assert.equal(counts.scores,0);
   const originalTask=await E.prepare(body(criterion)),expected=E.summary(originalTask,await E.verify(originalTask,E.run(originalTask)));assert.deepEqual(clone(first),expected);
  }
 });
 await test('actual Welcome still reproduces and its prefix summary does not change across renders',async()=>{
  const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8')),control=read('data/evidence/reading-methods.json').controls.find(c=>c.id==='welcome'),page=read('data/pages/lp1-03.json'),known=read('data/evidence/known-readings.json').controls.find(c=>c.id==='welcome').decoded_pages.find(p=>p.page==='lp1-03'),symbols=new Set(alphabet.map(r=>r.rune));
  let runeCount=0,source='';for(const ch of page.raw){if(symbols.has(ch)&&runeCount===48)break;source+=ch;if(symbols.has(ch))runeCount++;}assert.equal(control.skip[0],48);
  const task=await E.prepare({title:'Welcome exact prefix regression',alphabet,pages:[{id:page.id,text:source}],steps:[{op:'keyed-shift',key:control.key,mode:'repeat',direction:'subtract',reset:'page'}],criterion:{kind:'exact-prefix',values:known.rune_indices.slice(0,48)}}),raw=E.run(task),verified=await E.verify(task,raw);assert.equal(verified.matches[0].matched,true);
  assert.deepEqual(clone(verified),raw);const first=E.summary(task,verified);assert.deepEqual(E.summary(task,verified),first);assert.match(first.finding,/exact rune sequence/);assert.match(first.finding,/does not establish a decryption/);
 });
 await test('20,000-rune display benchmark avoids repeated scoring while retaining task checks',async()=>{
  const {engine,counts}=measuredEngine(),task=await engine.prepare(body(Evaluators.criterion(),20000)),raw=engine.run(task),verified=await engine.verify(task,raw),start=performance.now();
  for(let i=0;i<20;i++)engine.summary(task,verified);const cachedMs=performance.now()-start;assert.equal(counts.scores,2);assert.equal(counts.transforms,2);
  const before=performance.now();for(let i=0;i<20;i++)engine.run(task);const priorReplayMs=performance.now()-before;
  console.log(JSON.stringify({benchmark:'20k runes,20 renders',cachedSummaryMs:+cachedMs.toFixed(2),priorTargetReplayMs:+priorReplayMs.toFixed(2),avoidedTargetReplays:20}));
 });
 console.log('Verified display reuse: '+groups+' groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
