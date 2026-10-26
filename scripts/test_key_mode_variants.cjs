'use strict';
// Invented scope; mode eligibility and no-op proofs must not decode any target.
const assert=require('node:assert/strict'),{webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),V=require('../task-parameter-variants.js');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'),alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),modes=['repeat','plaintext-autokey','ciphertext-autokey'],resets=['page','line','word'],copy=x=>JSON.parse(JSON.stringify(x));
const selection=(value,step=0)=>({version:1,step,parameter:'mode',value}),step=(mode='repeat',reset='page',key=[1,7])=>({op:'keyed-shift',mode,reset,key,direction:'subtract'}),modeItems=(task,method='list')=>V[method](task).filter(item=>item.selection.parameter==='mode');
async function task(steps,patch={}){return E.prepare({title:'Invented key continuation',pages:[{id:'lp2-00',text:runes.slice(0,4).join('')+' '+runes.slice(4,8).join('')+'\r\n'+runes.slice(8,12).join('')},{id:'lp2-01',text:runes.slice(12,16).join('')}],alphabet,steps,criterion:{kind:'exact-prefix',values:[1,2,3]},...patch},webcrypto);}
let groups=0;async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
async function mutation(start,change){let release;const blocked=new Promise(resolve=>{release=resolve;}),crypto={subtle:{digest:async(...args)=>{await blocked;return webcrypto.subtle.digest(...args);}}},pending=start(crypto);change();release();await assert.rejects(pending,/changed|identity|outside|Unexpected|Missing/);}
(async()=>{
 const run=E.run,verify=E.verify;E.run=()=>assert.fail('Mode variations must not execute a target');E.verify=()=>assert.fail('Mode variations must not replay a result');
 try{
await test('shared HTTP selection parser returns immutable detached exact descriptors',async()=>{const input={version:1,step:0,parameter:'mode',value:'plaintext-autokey'},out=V.selection(input);assert.deepEqual(out,input);assert(Object.isFrozen(out));input.value='repeat';assert.equal(out.value,'plaintext-autokey');for(const value of [{...input,value:'unknown'},{...input,extra:true},{...input,step:0.5}])assert.throws(()=>V.selection(value));let reads=0;const hostile={version:1,step:0,parameter:'mode'};Object.defineProperty(hostile,'value',{enumerable:true,get(){reads++;return 'repeat';}});assert.throws(()=>V.selection(hostile));assert.equal(reads,0);});
 await test('all six directed key modes and all three resets preserve the exact fixed calculation',async()=>{
  for(const reset of resets)for(const mode of modes){const parent=await task([step(mode,reset)]),before=E.stable(parent),items=modeItems(parent);assert.equal(items.length,2);assert.deepEqual(items.map(x=>x.selection.value),modes.filter(x=>x!==mode));assert(Object.isFrozen(items[0].selection));
   for(const item of items){assert.equal(item.from,mode);const child=await V.prepare(parent,item.selection,webcrypto),expected=copy(parent.steps);expected[0].mode=item.selection.value;assert.deepEqual(child.steps,expected);assert.deepEqual(child.pages,parent.pages);assert.deepEqual(child.alphabet,parent.alphabet);assert.deepEqual(child.criterion,parent.criterion);assert(Object.isFrozen(child));assert(Object.isFrozen(child.steps[0].key));assert.notEqual(child.taskId,parent.taskId);assert.deepEqual(await V.validate(parent,child,item.selection,webcrypto),child);assert.deepEqual(await V.prepare(parent,item.selection,webcrypto),child);assert.equal(E.stable(parent),before);}
  }
 });
 await test('suggestions suppress only seed-unexhausted modes at the selected reset boundary',async()=>{
  const pages=[{id:'lp2-00',text:runes.slice(0,2).join('')+' '+runes.slice(2,4).join('')+'\n'+runes.slice(4,6).join('')+' '+runes.slice(6,8).join('')}];
  for(const mode of modes)for(const reset of resets){const parent=await task([step(mode,reset,[1,7])],{pages});assert.equal(modeItems(parent,'suggestions').length,reset==='word'?0:2);assert.equal(modeItems(parent).length,2);}
  for(const reset of resets){const max=reset==='page'?8:reset==='line'?4:2;
   for(const length of [max-1,max,max+1]){const parent=await task([step('repeat',reset,Array(length).fill(0))],{pages});assert.equal(modeItems(parent,'suggestions').length,length<max?2:0);}
  }
  const empty=await task([step()],{pages:[{id:'lp2-00',text:' ---\n'}]});assert.equal(modeItems(empty,'suggestions').length,0);
 });
 await test('prior transformations preserve clocks and downstream constants alone erase mode differences',async()=>{
  const prior=[{op:'reverse',unit:'page'},{op:'affine',a:0,b:0},{op:'cumulative-difference',reset:'line'}],parent=await task([...prior,step('repeat','word',[0])]);assert.equal(modeItems(parent,'suggestions').length,2);
  for(const item of modeItems(parent)){assert.equal(item.selection.step,3);const child=await V.prepare(parent,item.selection,webcrypto);assert.deepEqual(child.steps.slice(0,3),prior);}
  const wiped=await task([...prior,step(),{op:'affine',a:0,b:9}]);assert.equal(modeItems(wiped,'suggestions').length,0);assert.equal(modeItems(wiped).length,2);
  const kept=await task([...prior,step(),{op:'affine',a:1,b:0}]);assert.equal(modeItems(kept,'suggestions').length,2);
 });
 await test('finite and interrupted streams reject modes and exact selection schema rejects ambiguity',async()=>{
  for(const op of ['finite-shift','interrupted-keyed-shift']){const operation={op,key:Array(30).fill(1),direction:'add',reset:'page',...(op==='interrupted-keyed-shift'?{interrupts:[0]}:{})},parent=await task([operation]);assert.equal(modeItems(parent).length,0);await assert.rejects(V.prepare(parent,selection('repeat'),webcrypto),/does not support/);}
  const parent=await task([step()]);for(const patch of [{value:'page'},{value:'Repeat'},{value:'repeat'},{value:0},{version:2},{step:1},{step:-1},{step:0.5},{extra:true},{parameter:'key-mode'}])await assert.rejects(V.prepare(parent,{...selection('plaintext-autokey'),...patch},webcrypto));
  let getterCalls=0;const bad=selection('plaintext-autokey');Object.defineProperty(bad,'value',{enumerable:true,get(){getterCalls++;return 'plaintext-autokey';}});await assert.rejects(V.prepare(parent,bad,webcrypto));assert.equal(getterCalls,0);
 });
 await test('rehashing cannot hide changed source, literal seed, boundary, direction, evaluation or title',async()=>{
  const parent=await task([{op:'reverse',unit:'word'},step()]),choice=selection('ciphertext-autokey',1),child=await V.prepare(parent,choice,webcrypto);
  for(const change of [x=>{x.title='Different';},x=>{x.pages[0].text+=runes[0];},x=>{x.criterion.values[0]=9;},x=>{x.steps[0].unit='page';},x=>{x.steps[1].key[0]=9;},x=>{x.steps[1].reset='word';},x=>{x.steps[1].direction='add';},x=>{x.steps[1].mode='plaintext-autokey';}]){const bad=copy(child);change(bad);bad.taskId=await E.identity(bad,webcrypto);await assert.rejects(V.validate(parent,bad,choice,webcrypto),/more than/);}
  const bad=copy(parent);bad.taskId='0'.repeat(64);await assert.rejects(V.prepare(bad,choice,webcrypto));
 });
 await test('asynchronous preparation and validation reject parent child and selection mutations',async()=>{
  const parent=await task([step()]),choice=selection('plaintext-autokey');await mutation(crypto=>V.prepare(parent,choice,crypto),()=>{parent.steps[0].key[0]=2;});
  const p2=await task([step()]),c2=selection('ciphertext-autokey');await mutation(crypto=>V.prepare(p2,c2,crypto),()=>{c2.value='plaintext-autokey';});
  const c3=selection('plaintext-autokey'),child=copy(await V.prepare(p2,c3,webcrypto));await mutation(crypto=>V.validate(p2,child,c3,crypto),()=>{child.steps[0].reset='line';});
 });
 }finally{E.run=run;E.verify=verify;}
 console.log(groups+' key-mode variation groups passed; invented pages, no target execution or I/O.');
})().catch(error=>{console.error(error);process.exitCode=1;});
