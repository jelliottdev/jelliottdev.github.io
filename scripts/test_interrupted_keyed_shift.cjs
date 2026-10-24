'use strict';
// Explicit synthetic vectors only. No manuscript execution or hosted calls.
const assert=require('node:assert/strict'),{webcrypto}=require('node:crypto'),{execFileSync}=require('node:child_process'),path=require('node:path');
const E=require('../local-experiment.js');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),encode=values=>values.map(v=>runes[v]).join(''),values=text=>Array.from(text).filter(ch=>runes.includes(ch)).map(ch=>runes.indexOf(ch));
const op=(key=[1,2],interrupts=[0],direction='subtract',reset='page')=>({op:'interrupted-keyed-shift',key,interrupts,direction,reset});
const accepted=[],rejected=[];let groups=0;
async function task(text,steps=[op()],pages){const t=await E.prepare({title:'Synthetic interrupted-key test',alphabet,pages:pages||[{id:'lp2-15',text}],steps,criterion:{kind:'measurement'}},webcrypto);accepted.push(t);return t;}
async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
async function invalid(base,steps){const t={...base,steps};t.taskId=await E.identity(t,webcrypto);rejected.push(t);let progress=0;assert.throws(()=>E.run(t,{onProgress:()=>progress++}));assert.equal(progress,0);}
function encodeKnown(plaintext,key,interrupts,direction){
 const sign=direction==='subtract'?-1:1;let position=0;
 return plaintext.map(p=>{if(interrupts.includes(p))return p;const c=(p-sign*key[position%key.length]+29)%29;if(interrupts.includes(c))throw Error('Unreachable under this declared copy convention');position++;return c;});
}
async function main(){
 await test('interrupt runes copy literally and following noninterrupt uses the held key',async()=>{
  const input=[0,0,3,0,5,6,0];
  const expected={subtract:[0,0,2,0,3,5,0],add:[0,0,4,0,7,7,0]};
  for(const direction of ['subtract','add'])assert.deepEqual(values(E.run(await task(encode(input),[op([1,2],[0],direction)])).transformed[0].text),expected[direction]);
 });
 await test('copying is chosen by this step input, never decoded output or original program input',async()=>{
  // Input1 decodes to interrupt0 but still advances, so input3 uses key2.
  assert.deepEqual(values(E.run(await task(encode([1,3]),[op()])).transformed[0].text),[0,1]);
  // Earlier affine changes input0 to1; new step must consume it, while changed input28 becomes0 and holds.
  const t=await task(encode([0,28,2]),[{op:'affine',a:1,b:1},op()]);
  assert.deepEqual(values(E.run(t).transformed[0].text),[0,0,1]);
  // A second interrupted step consumes its own input; zero emitted by first is copied.
  const chained=await task(encode([1,3,5]),[op(),op([4,5],[0])]);
  assert.deepEqual(values(E.run(chained).transformed[0].text),[0,26,28]);
 });
 await test('separators preserve bytes and reset only at the explicit page line or word boundary',async()=>{
  const text=encode([3,0])+' /💡'+encode([5,0])+'\r\n'+encode([7,0])+'\r'+encode([9])+'\n'+encode([11]);
  const expected={page:[2,0,3,0,6,0,7,10],line:[2,0,3,0,6,0,8,10],word:[2,0,4,0,6,0,8,10]};
  for(const reset of ['page','line','word']){
   const t=await task('',[op([1,2],[0],'subtract',reset)],[{id:'lp2-15',text},{id:'lp2-16',text:encode([3,0,5])}]),r=E.run(t);
   assert.deepEqual(values(r.transformed[0].text),expected[reset]);assert.deepEqual(values(r.transformed[1].text),[2,0,3]);
   assert.equal(Array.from(r.transformed[0].text).filter(ch=>!runes.includes(ch)).join(''),Array.from(text).filter(ch=>!runes.includes(ch)).join(''));
  }
 });
 await test('multiple interrupts, all interrupts, zero key and empty pages behave literally',async()=>{
  const t=await task(encode([0,1,2,3,28,4]),[op([2,3],[0,2,28])]);assert.deepEqual(values(E.run(t).transformed[0].text),[0,28,2,0,28,2]);
  const input=encode(Array.from({length:29},(_,i)=>i));assert.equal(E.run(await task(input,[op([28],Array.from({length:29},(_,i)=>i))])).transformed[0].text,input);
  assert.equal(E.run(await task(input,[op([0],[0])])).transformed[0].text,input);
  assert.equal(E.run(await task(' /\r\n💡',[op()])).transformed[0].text,' /\r\n💡');
 });
 await test('independent reachable-plaintext encoding recovers interrupt and following alignment',async()=>{
  const plaintext=[0,4,6,0,8,0,10,12,0,14],key=[1,2];
  for(const direction of ['subtract','add']){
   const ciphertext=encodeKnown(plaintext,key,[0],direction),t=await task(encode(ciphertext),[op(key,[0],direction)]);
   assert.deepEqual(values(E.run(t).transformed[0].text),plaintext);
   assert(ciphertext.includes(0));
  }
  assert.throws(()=>encodeKnown([28],[1],[0],'subtract'),/Unreachable/);
 });
 await test('complete 256-index key repeats and maximum rune count is not truncated',async()=>{
  const key=Array.from({length:256},(_,i)=>i%29),input=Array.from({length:20000},(_,i)=>i%7===0?0:1+(i%28));let clock=0;
  const expected=input.map(c=>c===0?0:(c-key[clock++%key.length]+29)%29);
  assert.deepEqual(values(E.run(await task(encode(input),[op(key)])).transformed[0].text),expected);
 });
 await test('strict shapes indices sorted uniqueness lengths and no hidden modes reject before execution',async()=>{
  const base=await task(encode([0,1]));
  for(const patch of [{interrupts:[]},{interrupts:[1,0]},{interrupts:[0,0]},{interrupts:[true]},{interrupts:[null]},{interrupts:[1.5]},{interrupts:[-1]},{interrupts:[29]},{interrupts:'0'},{interrupts:Array(30).fill(0)},
   {key:[]},{key:[true]},{key:[29]},{key:[-1]},{key:[0.5]},{key:Array(257).fill(0)},{key:new Uint8Array([1,2])},{interrupts:new Uint8Array([0])},{mode:'repeat'},{pause:[0]},{literal:false},{direction:'decode'},{reset:'none'}])await invalid(base,[{...op(),...patch}]);
  for(const field of ['op','key','direction','reset','interrupts']){const step=op();delete step[field];await invalid(base,[step]);}
 });
 await test('full replay identity and legacy result structure remain strict',async()=>{
  const t=await task(encode([0,1,3])),r=E.run(t);assert.deepEqual(await E.verify(t,r,webcrypto),r);
  const forged=structuredClone(r);forged.transformed[0].text=encode([28,0,1]);await assert.rejects(E.verify(t,forged,webcrypto));
  const changed={...t,steps:[op([1,2],[1])]};await assert.rejects(E.checkIdentity(changed,webcrypto));
  assert.deepEqual(Object.keys(r).sort(),['schema','taskId','engine','runnerVersion','metrics','matches','transformed'].sort());
 });
 await test('independent Python reproduces every synthetic full result and strict invalid rejection',async()=>{
  const code="import sys,json,importlib.util; spec=importlib.util.spec_from_file_location('runner','tools/research_runner.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); data=json.load(sys.stdin); output=[]\nfor t in data['accepted']: output.append(m.run(t))\nfor t in data['rejected']:\n try: m.run(t)\n except (ValueError,TypeError): continue\n raise AssertionError('invalid task accepted')\nprint(json.dumps(output,ensure_ascii=False))";
  const output=JSON.parse(execFileSync('python',['-c',code],{cwd:path.join(__dirname,'..'),input:JSON.stringify({accepted,rejected}),encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'},maxBuffer:20000000}));
  assert.equal(output.length,accepted.length);for(let i=0;i<output.length;i++)assert.deepEqual(output[i],E.run(accepted[i]));
 });
 console.log(groups+' interrupted-key groups passed; '+accepted.length+' accepted and '+rejected.length+' rejected JS/Python parity vectors.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
