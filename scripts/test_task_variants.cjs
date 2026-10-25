'use strict';
const assert=require('node:assert/strict'),{webcrypto}=require('node:crypto'),fs=require('node:fs'),vm=require('node:vm');
const E=require('../local-experiment.js'),V=require('../task-variants.js');
const alphabet=JSON.parse(fs.readFileSync('data/index.json','utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
async function task(criterion,steps=[]){return E.prepare({title:'Synthetic boundary measurement',pages:[{id:'lp2-15',text:'ᚠᚢ /\r\nᛠ-ᚠᚢ.ᛠ'}],alphabet,steps,criterion},webcrypto);}
(async()=>{
 let checked=0;
 for(const kind of ['word-prime-sums','word-affine-count'])for(const from of ['non-rune','hyphen-period']){
  const criterion=kind==='word-prime-sums'?{kind,table:'reversed',boundaries:from}:{kind,lag:1,a:27,b:24,boundaries:from};
  const parent=await task(criterion),original=E.stable(parent),oldRun=E.run;
  E.run=()=>{throw Error('Variant preparation must not execute target');};let child;
  try{child=await V.prepare(parent,webcrypto);assert.deepEqual(await V.validate(parent,child,webcrypto),child);}finally{E.run=oldRun;}
  assert.equal(E.stable(parent),original);assert.equal(child.criterion.boundaries,from==='non-rune'?'hyphen-period':'non-rune');
  assert.deepEqual({...child.criterion,boundaries:from},criterion);assert.deepEqual(child.pages,parent.pages);assert.deepEqual(child.alphabet,parent.alphabet);assert.deepEqual(child.steps,[]);assert.notEqual(child.taskId,parent.taskId);
  const back=await V.prepare(child,webcrypto),again=await V.prepare(back,webcrypto),backAgain=await V.prepare(again,webcrypto);
  assert.deepEqual(again,child);assert.deepEqual(backAgain,back);assert(!again.title.includes(parent.title));
  assert.notDeepEqual(oldRun(parent)[kind==='word-prime-sums'?'wordSums':'wordPairs'],oldRun(child)[kind==='word-prime-sums'?'wordSums':'wordPairs']);
  for(const change of [{title:'Other title'},{pages:[{id:'lp2-16',text:parent.pages[0].text}]},{pages:[{id:'lp2-15',text:'ᚠᚢ'}]},{criterion:parent.criterion},{steps:[{op:'affine',a:1,b:0}]},
   {criterion:kind==='word-prime-sums'?{...child.criterion,table:'canonical'}:{...child.criterion,lag:2}}])await assert.rejects(V.validate(parent,await E.prepare({...child,...change},webcrypto),webcrypto));
  await assert.rejects(V.validate(parent,{...child,taskId:'0'.repeat(64)},webcrypto));checked++;
 }
 for(const criterion of [{kind:'measurement'},{kind:'exact-prefix',values:[0]}])assert.equal(V.inspect(await task(criterion)),null);
 const transformed=await task({kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'},[{op:'affine',a:1,b:0}]);assert.equal(V.inspect(transformed),null);await assert.rejects(V.prepare(transformed,webcrypto));assert.equal(V.inspect({}),null);
 // Decisions use real independently verified outputs, including a non-monotone null.
 const examples={
  'neither-above':'ᚦᚦᚦ ᚠᚠᚢ ᚩᚦᚦ ᚦᚢᚦ',
  'excess-in-both':'ᚠᚦᚠ ᚦᚩᚦ ᚦᚩᚠ ᚠᚠᚠ',
  'excess-joined-only':'ᚠᚩᚦ ᚦᚦᚦ ᚠᚦᚩ ᚠᚠᚢ',
  'excess-separate-only':'ᚦᚠᚠ ᚩᚢᚩ ᚩᚠᚩ ᚩᚠᚠ',
  'insufficient-pairs':'ᚠ ᚢ ᚦ'
 };
 for(const [expected,text] of Object.entries(examples)){
  const parent=await E.prepare({title:'Boundary decision control',pages:[{id:'lp2-15',text}],alphabet,steps:[],criterion:{kind:'word-affine-count',lag:2,a:1,b:0,boundaries:'non-rune'}},webcrypto);
  const child=await V.prepare(parent,webcrypto),raw=E.run(parent),before=await E.verify(parent,raw,webcrypto),after=await E.verify(child,E.run(child),webcrypto);
  const decision=V.decision(parent,before,child,after);
  assert.equal(decision.id,expected);assert.deepEqual(V.decision(child,after,parent,before),decision);
  assert.match(decision.limit,/not a significance test/);assert.match(decision.limit,/not a significance test or independent confirmation/);
  assert.throws(()=>V.decision(parent,raw,child,after),/verified/);
  const different=await E.prepare({...child,pages:[{id:'lp2-15',text:text+'ᚠ'}]},webcrypto),differentResult=await E.verify(different,E.run(different),webcrypto);
  assert.throws(()=>V.decision(parent,before,different,differentResult),/same text and rule/);
 }
 const context={LocalExperiment:E,ExperimentProtocols:require('../experiment-protocols.js')};vm.createContext(context);vm.runInContext(fs.readFileSync('task-variants.js','utf8'),context);assert.equal(typeof context.TaskVariants.prepare,'function');
 console.log('PASS '+checked+' fixed boundary variants, exact invariants, unsupported exclusions, browser export and no target preparation execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
