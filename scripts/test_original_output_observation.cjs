/* Invented data only. Observations never execute a transformation or create a baseline result. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto}=require('node:crypto'),V=require('../declarative-rune-program.js'),D=require('../local-experiment-dispatch.js'),E=require('../local-experiment.js'),O=require('../original-output-observation.js');
const alphabet=require('../data/local-run-inputs.json').alphabet,chars=values=>values.map(i=>alphabet[i].rune).join('');
async function certificate(texts,steps=[],criterion={kind:'measurement'}){const task=await V.prepare({title:'Invented original/output observation only',alphabet,pages:texts.map((text,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text})),steps,criterion},webcrypto),result=V.run(task);return {task,result,certificate:await D.verify(task,result,webcrypto)};}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('private observation binds exact dispatcher certificate and exposes immutable same-scope metrics',async()=>{
  const x=await certificate([chars([0,0,0]),chars([1,2])],[{op:'collapse-adjacent-repeats',unit:'word',policy:'all-but-first'}]),token=O.derive(x.certificate),view=O.inspect(token);
  assert.equal(view.taskId,x.task.taskId);assert.strictEqual(view.certificate,x.certificate);assert.deepEqual(view.pageIds,['lp2-00','lp2-01']);assert.deepEqual(view.original,{pages:2,runes:5,adjacentPairs:3,equalAdjacentPairs:2,equalPairRate:{numerator:2,denominator:3,value:2/3},ioc:0.3});assert.deepEqual(view.output,{pages:2,runes:3,adjacentPairs:1,equalAdjacentPairs:0,equalPairRate:{numerator:0,denominator:1,value:0},ioc:0});assert.equal(view.removedRunes,2);assert.deepEqual(view.pages.map(p=>p.removedRunes),[2,0]);assert(Object.isFrozen(view.pages[0].original.equalPairRate));assert(!Object.hasOwn(view,'baselineReceipt'));assert(!Object.hasOwn(view,'coverage'));assert(!Object.hasOwn(view,'matched'));
  assert.equal(view.pages[0].original.ioc,1);assert.equal(view.pages[1].original.ioc,0);assert.notEqual(view.original.ioc,(view.pages[0].original.ioc+view.pages[1].original.ioc)/2);
 });
 await test('rune-only adjacent pairs ignore punctuation and newlines but never cross a page boundary',async()=>{
  const a=alphabet[0].rune,b=alphabet[1].rune,x=await certificate([a+'!🧩\n'+a,b]),view=O.inspect(O.derive(x.certificate));assert.equal(view.original.adjacentPairs,1);assert.equal(view.original.equalAdjacentPairs,1);assert.equal(view.original.runes,3);assert.equal(view.pages[1].original.adjacentPairs,0);assert.equal(view.pages[1].original.equalPairRate.value,null);assert.deepEqual(view.original,view.output);assert.equal(view.removedRunes,0);
 });
 await test('filtering and reversal retain exact input/output counts without claiming a causal or scientific null comparison',async()=>{
  const x=await certificate([chars([0,1,0,2,2])+'!'],[{op:'reverse',unit:'page'},{op:'remove-rune-types',values:[0]}]),view=O.inspect(O.derive(x.certificate));assert.equal(view.original.runes,5);assert.equal(view.output.runes,3);assert.equal(view.output.adjacentPairs,2);assert.equal(view.output.equalAdjacentPairs,1);assert.equal(view.removedRunes,2);assert.match(view.limit,/not.*scientific null/);assert.match(view.limit,/not a mean/);
 });
 await test('empty and one-rune outputs distinguish missing pair opportunities from an observed zero rate',async()=>{
  for(const text of ['',chars([0]),chars([0,0])]){const x=await certificate([text],[{op:'remove-rune-types',values:[0]}]),view=O.inspect(O.derive(x.certificate));assert.equal(view.output.runes,0);assert.equal(view.output.ioc,0);assert.equal(view.output.equalPairRate.value,null);assert.equal(view.output.equalPairRate.denominator,0);assert.equal(view.pages[0].output.pages,1);}
  const x=await certificate([chars([0,1])]),view=O.inspect(O.derive(x.certificate));assert.equal(view.output.equalPairRate.value,0);assert.equal(view.output.equalPairRate.denominator,1);
 });
 await test('raw cloned forged V1 and opaque engine tokens cannot act as dispatcher certificates',async()=>{
  const x=await certificate([chars([0,0])]);for(const value of [x.result,structuredClone(x.certificate),{task:x.task,result:x.certificate},await V.verify(x.task,x.result,webcrypto),null])assert.throws(()=>O.derive(value));
  const legacy=await E.prepare({title:'Invented V1 observation rejection',alphabet,pages:[{id:'lp2-00',text:chars([0])}],steps:[],criterion:{kind:'measurement'}},webcrypto);const legacyVerified=await D.verify(legacy,E.run(legacy),webcrypto);assert.throws(()=>O.derive(legacyVerified));
 });
 await test('UMD derives from verified values without runner scorer verification or filesystem calls',async()=>{
  const x=await certificate([chars([0,0,1])],[{op:'collapse-adjacent-repeats',unit:'page',policy:'all-but-first'}],{kind:'exact-prefix',values:[0,1]}),before=JSON.stringify(x.certificate),context={LocalExperimentDispatch:{inspect:value=>D.inspect(value),run(){assert.fail('No execution');},verify(){assert.fail('No replay');},checkIdentity(){assert.fail('No redundant validation');}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../original-output-observation.js'),'utf8'),context);const browser=context.OriginalOutputObservation,token=browser.derive(x.certificate),view=browser.inspect(token);assert.equal(view.output.runes,2);assert.equal(JSON.stringify(x.certificate),before);assert.strictEqual(view.certificate,x.certificate);assert.throws(()=>browser.inspect({...token}));assert.throws(()=>browser.inspect(view));assert.throws(()=>O.inspect(token));
 });
 console.log(groups+' original/output observation groups passed; invented verified outputs only, no baseline execution or receipt.');
})().catch(error=>{console.error(error);process.exitCode=1;});
