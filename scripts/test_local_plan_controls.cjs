'use strict';
// Only fixed synthetic pages are run. No manuscript target execution or network.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto,createHash}=require('node:crypto');
const E=require('../local-experiment.js'),P=require('../local-plan-controls.js');
const alphabet=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ').map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
const digest=value=>createHash('sha256').update(E.stable(value)).digest('hex');
async function target(steps=[],criterion={kind:'measurement'},a=alphabet){return E.prepare({title:'Synthetic target descriptor; never execute this page',pages:[{id:'lp2-15',text:a[0].rune}],alphabet:a,steps,criterion},webcrypto);}
let groups=0;async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
async function checked(t){
 const original=structuredClone(t),oldRun=E.run,executed=[];
 E.run=task=>{assert.notEqual(task.taskId,t.taskId,'Preparation must never execute its target');assert(task.title.startsWith('Synthetic local reference'));executed.push(task);return oldRun(task);};
 let suite;try{suite=await P.prepare(t,webcrypto);}finally{E.run=oldRun;}
 assert.deepEqual(t,original);assert.equal(executed.length,2);assert.equal(suite.version,1);assert.equal(suite.targetId,t.taskId);assert.equal(suite.cases.length,2);
 for(const item of suite.cases){assert.deepEqual(item.task.steps,t.steps);assert.deepEqual(item.task.alphabet,t.alphabet);assert.equal(item.task.pages.length,2);assert(item.task.pages.every(p=>Array.from(p.text).some(ch=>t.alphabet.some(a=>a.rune===ch))));assert.equal(item.expectedResultSha256,digest(oldRun(item.task)));await E.checkIdentity(item.task,webcrypto);}
 assert.deepEqual(await P.validate(suite,t,webcrypto),suite);assert.deepEqual(await P.prepare(t,webcrypto),suite);return suite;
}
(async()=>{
 await test('versioned suite is deterministic and bound to the exact target, never target execution',async()=>{assert.equal(P.REFERENCE_VERSION,1);assert.match(P.SCOPE,/independent reference/);await checked(await target());});
 await test('all supported ordered operators, reset rules and arithmetic directions have independent checks',async()=>{
  const programs=[[{op:'affine',a:0,b:28}],[{op:'affine',a:7,b:7}]];
  for(const unit of ['page','line','word'])programs.push([{op:'reverse',unit}]);
  for(const reset of ['page','line','word']){
   programs.push([{op:'cumulative-difference',reset}]);
   for(const direction of ['add','subtract']){
    for(const mode of ['repeat','plaintext-autokey','ciphertext-autokey'])programs.push([{op:'keyed-shift',key:[0,1,28],mode,direction,reset}]);
    programs.push([{op:'interrupted-keyed-shift',key:[1,28],interrupts:[0,4,16,28],direction,reset}]);
    programs.push([{op:'finite-shift',key:[0,1,28],direction,reset}]);
   }
  }
  programs.push([{op:'reverse',unit:'line'},{op:'affine',a:2,b:1},{op:'cumulative-difference',reset:'word'},
   {op:'keyed-shift',key:[1,2],mode:'plaintext-autokey',direction:'subtract',reset:'page'},
   {op:'interrupted-keyed-shift',key:[0,2],interrupts:[0,28],direction:'add',reset:'line'},
   {op:'finite-shift',key:Array(16).fill(2),direction:'subtract',reset:'word'}]);
  for(const program of programs)await checked(await target(program));
 });
 await test('exact-prefix controls explicitly test a derived positive and changed negative, not target plaintext',async()=>{
  const t=await target([{op:'affine',a:0,b:12}],{kind:'exact-prefix',values:[28,28,28]}),suite=await checked(t);
  const first=E.run(suite.cases[0].task),second=E.run(suite.cases[1].task);assert(first.matches[0].matched);assert.equal(second.matches[0].matched,false);
  assert.notDeepEqual(suite.cases[0].task.criterion,t.criterion);assert.equal(suite.cases[0].task.criterion.values[0],12);assert.equal(suite.cases[1].task.criterion.values[0],13);assert.deepEqual(t.criterion.values,[28,28,28]);
 });
 await test('finite-key minimum keeps both fixtures nonempty without expanding or wrapping the key',async()=>{
  for(const reset of ['page','line','word']){
   const t=await target([{op:'finite-shift',key:[1],direction:'subtract',reset}],{kind:'exact-prefix',values:[0]});
   const suite=await checked(t);for(const item of suite.cases){assert.deepEqual(item.task.steps,t.steps);if(reset==='page')for(const page of item.task.pages)assert.equal(Array.from(page.text).filter(ch=>alphabet.some(a=>a.rune===ch)).length,1);}
  }
 });
 await test('long autokey fixtures reach feedback after the complete seed where finite bounds permit',async()=>{
  const key=Array.from({length:256},(_,i)=>i%29),suite=await checked(await target([{op:'keyed-shift',key,mode:'plaintext-autokey',direction:'add',reset:'word'}]));
  for(const item of suite.cases)assert(Array.from(item.task.pages[0].text.split(' ')[0]).length>256);
 });
 await test('word pair expectations and sum ledgers retain their exact criterion under both boundary rules',async()=>{
  for(const boundaries of ['non-rune','hyphen-period']){
   for(const [a,b,lag]of [[1,0,1],[0,28,3],[27,24,6],[28,1,12]]){
    const t=await target([{op:'affine',a:7,b:7}],{kind:'word-affine-count',a,b,lag,boundaries}),suite=await checked(t);for(const c of suite.cases){assert.deepEqual(c.task.criterion,t.criterion);assert(E.run(c.task).wordPairs);}
   }
   for(const table of ['canonical','reversed']){
    const t=await target([{op:'reverse',unit:'word'}],{kind:'word-prime-sums',table,boundaries}),suite=await checked(t);for(const c of suite.cases){assert.deepEqual(c.task.criterion,t.criterion);assert(E.run(c.task).wordSums.words>0);}
   }
  }
 });
 await test('untransformed word-affine controls include real matching and nonmatching opportunities through lag12',async()=>{
  for(const boundaries of ['non-rune','hyphen-period'])for(const lag of [1,6,12])for(const [a,b]of [[0,0],[0,28],[1,0],[27,24],[28,28]]){
   const suite=await checked(await target([],{kind:'word-affine-count',lag,a,b,boundaries}));
   for(const c of suite.cases){const pairs=E.run(c.task).wordPairs;assert(pairs.opportunities>0);assert(pairs.matches>=2,'Each of the two synthetic pages contains a planted match');assert(pairs.matches<pairs.opportunities,'Each page also contains a planted mismatch');assert(BigInt(pairs.expected.numerator)>0n,'An always-zero expectation must fail this control');}
  }
  // The largest adaptive seed fixture remains below the reproduction guard cap.
  const longest=await P.prepare(await target([{op:'keyed-shift',key:Array(256).fill(1),mode:'plaintext-autokey',direction:'subtract',reset:'word'}],{kind:'word-affine-count',lag:12,a:27,b:24,boundaries:'non-rune'}),webcrypto);
  const counts=longest.cases.flatMap(c=>c.task.pages.map(p=>Array.from(p.text).filter(ch=>alphabet.some(a=>a.rune===ch)).length));assert.equal(Math.max(...counts),274);assert(counts.every(n=>n<=320));
 });
 await test('astral rune alphabets and actual assigned prime values stay intact',async()=>{
  const a=structuredClone(alphabet);a[0].rune='🌀';a[28].prime=1000000;await checked(await target([{op:'interrupted-keyed-shift',key:[1],interrupts:Array.from({length:29},(_,i)=>i),direction:'add',reset:'word'}],{kind:'word-prime-sums',table:'reversed',boundaries:'hyphen-period'},a));
 });
 await test('suite shape, identity, program, criteria and digests cannot be substituted',async()=>{
  const t=await target(),suite=await P.prepare(t,webcrypto);
  for(const change of [s=>s.version=2,s=>s.targetId='0'.repeat(64),s=>s.extra=true,s=>s.cases.pop(),s=>s.cases[0].id='other',s=>s.cases[0].extra=true,s=>s.cases[0].task.extra=undefined,s=>s.cases.reverse(),s=>s.cases[0].expectedResultSha256='0'.repeat(64),s=>s.cases[0].task.pages[0].text+='ᚠ',s=>s.cases[0].task.criterion={kind:'exact-prefix',values:[1]}]){const forged=structuredClone(suite);change(forged);await assert.rejects(P.validate(forged,t,webcrypto));}
  const other=await target([{op:'affine',a:1,b:1}]);await assert.rejects(P.validate(suite,other,webcrypto));
  const bad={...t,taskId:'0'.repeat(64)};await assert.rejects(P.prepare(bad,webcrypto));await assert.rejects(P.prepare({...t,extra:undefined},webcrypto));
 });
 await test('engine text, metrics and prefix-scoring defects fail independent comparison before a suite is returned',async()=>{
  const original=E.run;
  for(const mode of ['text','metrics','prefix']){
   E.run=t=>{const r=original(t);if(mode==='text')r.transformed[0].text+='ᚠ';if(mode==='metrics')r.metrics.runes++;if(mode==='prefix')r.matches.forEach(m=>m.matched=false);return r;};
   try{await assert.rejects(P.prepare(await target([],{kind:'exact-prefix',values:[0]}),webcrypto),/independent synthetic reference/);}finally{E.run=original;}
  }
 });
 await test('browser module produces the identical suite and verifies its exact signature',async()=>{
  const browser={LocalExperiment:E,TextEncoder,crypto:webcrypto};vm.runInNewContext(fs.readFileSync(require.resolve('../local-plan-controls.js'),'utf8'),browser);
  const t=await target([{op:'cumulative-difference',reset:'line'}],{kind:'word-affine-count',lag:6,a:27,b:24,boundaries:'hyphen-period'}),suite=await P.prepare(t,webcrypto);
  assert.equal(JSON.stringify(await browser.LocalPlanControls.prepare(t,webcrypto)),JSON.stringify(suite));assert.equal(JSON.stringify(await browser.LocalPlanControls.validate(suite,t,webcrypto)),JSON.stringify(suite));
 });
 console.log('PASS '+groups+' independent local-plan control groups; all runner calls use synthetic inputs only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
