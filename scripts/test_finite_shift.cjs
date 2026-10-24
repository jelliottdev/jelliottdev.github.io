'use strict';
// Synthetic vectors only: no manuscript targets are decoded by this suite.
const assert=require('node:assert/strict'),path=require('node:path');
const {execFileSync}=require('node:child_process'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
const encode=values=>values.map(v=>runes[v]).join('');
const values=text=>Array.from(text).filter(ch=>runes.includes(ch)).map(ch=>runes.indexOf(ch));
const finite=(key,reset='page',direction='subtract')=>({op:'finite-shift',key,reset,direction});
const body=(steps,text=encode([1,2,3,4,5,6]),pages)=>({title:'Synthetic finite stream',pages:pages||[{id:'lp2-15',text}],alphabet,steps,criterion:{kind:'measurement'}});
let groups=0;const accepted=[],rejected=[];
async function task(steps,text,pages){const t=await E.prepare(body(steps,text,pages),webcrypto);accepted.push(t);return t;}
async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
async function invalid(candidate){candidate={...candidate,schema:E.TASK,engine:E.ENGINE,taskId:'0'.repeat(64)};candidate.taskId=await E.identity(candidate,webcrypto);rejected.push(candidate);assert.throws(()=>E.validateTask(candidate));return candidate;}
async function main(){
 await test('finite arithmetic is nonrepeating, modulo29, and hand checked in both directions',async()=>{
  const key=[1,2,4,8,16,28];
  for(const [direction,expected]of [['subtract',[0,0,28,25,18,7]],['add',[2,4,7,12,21,5]]]){
   const t=await task([finite(key,'page',direction)]),r=E.run(t);
   assert.deepEqual(values(r.transformed[0].text),expected);
   assert.deepEqual(await E.verify(t,r,webcrypto),r);
  }
 });
 await test('separators do not consume values, every page starts fresh, and CR/LF are line boundaries',async()=>{
  const text=encode([1,2])+' /💡'+encode([3,4,5])+'\r\n'+encode([6,7])+'\r'+encode([8])+'\n'+encode([9]);
  const expected={page:[0,0,28,25,18,7,27,6,5],line:[0,0,28,25,18,5,5,7,8],word:[0,0,2,2,1,5,5,7,8]};
  const key=[1,2,4,8,16,28,9,2,4];
  for(const reset of ['page','line','word']){
   const t=await task([finite(key,reset)],text,[{id:'lp2-15',text},{id:'lp2-16',text:encode([1,2])}]);
   const r=E.run(t);assert.deepEqual(values(r.transformed[0].text),expected[reset]);
   assert.equal(r.transformed[1].text,encode([0,0]));
   assert.deepEqual(Array.from(r.transformed[0].text).map((ch,i)=>[ch,i]).filter(([ch])=>!runes.includes(ch)),Array.from(text).map((ch,i)=>[ch,i]).filter(([ch])=>!runes.includes(ch)));
  }
 });
 await test('277-value and maximum20000-value streams use their full supplied length',async()=>{
  for(const n of [277,20000]){
   const key=Array.from({length:n},(_,i)=>(i*7+Math.floor(i/29))%29);
   const t=await task([finite(key)],runes[0].repeat(n));
   assert.deepEqual(values(E.run(t).transformed[0].text),key.map(k=>(29-k)%29));
  }
 });
 await test('all segment underruns fail validation before any progress, including later pages and later steps',async()=>{
  const cases=[body([finite([1])]),body([finite([1,2],'line')],encode([1])+'\n'+encode([2,3,4])),
   body([finite([1,2],'word')],encode([1])+' '+encode([2,3,4])),
   body([finite([1,2])],null,[{id:'lp2-15',text:encode([1,2])},{id:'lp2-16',text:encode([1,2,3])}]),
   body([{op:'reverse',unit:'page'},{op:'affine',a:0,b:0},finite([1,2],'word')],encode([1])+' '+encode([2,3,4]))];
  for(const candidate of cases){const t=await invalid(candidate);let progress=0;assert.throws(()=>E.run(t,{onProgress:()=>progress++}));assert.equal(progress,0);}
  // Matching the longest segment exactly is valid; empty reset segments need no key.
  const t=await task([finite([1,2],'word')],' /\r\n'+encode([1,2])+'.. '+encode([1])+'\n');
  assert.deepEqual(values(E.run(t).transformed[0].text),[0,0,0]);
 });
 await test('strict shape, integer, size and mode constraints reject invented stream behavior',async()=>{
  const base=finite([1,2]);
  for(const patch of [{key:[]},{key:'12'},{key:[true]},{key:[null]},{key:[1.5]},{key:[-1]},{key:[29]},{key:Array(20001).fill(0)},
   {direction:'decode'},{reset:'none'},{mode:'repeat'},{phase:0},{skip:[]}])await invalid(body([{...base,...patch}]));
 });
 await test('ordered multistep control recovers a planted sequence and cannot reorder methods',async()=>{
  // Plain [0,1,2,3] -> add finite [1,2,4,8] -> [1,3,6,11]
  // -> affine2x+1 -> [3,7,13,23] -> reversepage -> [23,13,7,3].
  const ciphertext=encode([23,13])+'-'+encode([7,3]);
  const steps=[{op:'reverse',unit:'page'},{op:'affine',a:15,b:14},finite([1,2,4,8])];
  const t=await task(steps,ciphertext);t.criterion={kind:'exact-prefix',values:[0,1,2,3]};t.taskId=await E.identity(t,webcrypto);
  const r=E.run(t);assert.equal(r.transformed[0].text,encode([0,1])+'-'+encode([2,3]));assert.equal(r.matches[0].matched,true);
  const wrong=await task([steps[2],steps[1],steps[0]],ciphertext);assert.notDeepEqual(values(E.run(wrong).transformed[0].text),[0,1,2,3]);
 });
 await test('finite stream composes with feedback and reversal for all resets and directions',async()=>{
  const text=encode([28,0,1])+'-'+encode([2,3])+'\r\n'+encode([4,5]);
  for(const reset of ['page','line','word'])for(const direction of ['add','subtract']){
   await task([{op:'reverse',unit:'line'},finite([28,0,1,2,3,4,5],reset,direction),{op:'cumulative-difference',reset},
    {op:'keyed-shift',key:[1,2],mode:'plaintext-autokey',direction,reset},finite([1,3,5,7,9,11,13],reset,direction)],text);
  }
 });
 await test('Python independently validates and reproduces every synthetic accepted and rejected task',async()=>{
  const bridge=`import json,sys\nfrom tools import research_runner as R\nb=json.load(sys.stdin)\nout={'accepted':[],'rejected':[]}\nfor task in b['accepted']: out['accepted'].append(R.run(task))\nfor task in b['rejected']:\n try: R.run(task)\n except ValueError: out['rejected'].append(True)\n else: out['rejected'].append(False)\njson.dump(out,sys.stdout,ensure_ascii=False,allow_nan=False)`;
  const output=JSON.parse(execFileSync('python',['-c',bridge],{cwd:path.resolve(__dirname,'..'),input:JSON.stringify({accepted,rejected}),encoding:'utf8',maxBuffer:8*1024*1024,env:{...process.env,PYTHONIOENCODING:'utf-8'}}));
  assert.deepEqual(output.accepted,accepted.map(t=>E.run(t)));assert(output.rejected.every(Boolean));
 });
 console.log(groups+' finite-stream groups passed; '+accepted.length+' accepted and '+rejected.length+' rejected JS/Python vectors.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
