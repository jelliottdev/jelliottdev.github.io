'use strict';
// Synthetic only: this tests named opening decisions, never manuscript targets.
const assert=require('node:assert/strict'),{webcrypto,createHash}=require('node:crypto'),{execFileSync}=require('node:child_process');
const E=require('../local-experiment.js');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),encode=values=>values.map(value=>runes[value]).join('');
// Literal known-reading prefixes from the historical prime-opening plan; pages below are synthetic planted copies.
const openings=[{"id":"warning","values":[24,7,24,4,9,21,17,18,20,10,18,1]},{"id":"welcome","values":[7,18,20,5,3,19,18,7,18,20,5,3]},{"id":"some-wisdom","values":[15,3,19,18,7,10,15,23,3,19,2,18]},{"id":"first-koan","values":[24,5,3,24,9,24,19,24,9,23,18,5]},{"id":"loss-of-divinity","values":[2,18,20,3,15,15,3,0,23,10,1,10]},{"id":"second-koan","values":[24,5,3,24,9,23,1,4,21,24,20,18]},{"id":"instruction","values":[24,9,10,9,15,16,4,1,5,16,27,9]},{"id":"lp2-56","values":[24,9,18,9,23,7,10,2,10,9,2,18]},{"id":"lp2-57","values":[13,24,4,24,17,20,18,20,10,5,18,2]}];
const accepted=[],rejected=[];let groups=0;
async function task(pages,criterion={kind:'exact-prefix-set',openings}){const t=await E.prepare({title:'Synthetic named opening comparison',alphabet,pages,steps:[],criterion},webcrypto);accepted.push(t);return t;}
async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
const digest=value=>createHash('sha256').update(E.stable(value)).digest('hex');
async function main(){
 await test('all nine planted passages match by complete ordered name',async()=>{
  const t=await task(openings.map((opening,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:encode(opening.values)+'.'+encode([28,0])}))),result=E.run(t);
  assert.deepEqual(result.matches,openings.map((opening,i)=>({page:'lp2-'+String(i).padStart(2,'0'),matched:true,matchingOpenings:[opening.id]})));
  const verified=await E.verify(t,result,webcrypto),summary=E.summary(t,verified);
  assert.match(summary.finding,/9 of 9 pages/);assert.match(summary.finding,/9 named passages/);assert.match(summary.limit,/complete opening sequences/);
 });
 await test('nonmatching, short and empty pages do not create partial hits',async()=>{
  const t=await task([{id:'lp2-00',text:encode([28,28,28])},{id:'lp2-01',text:encode(openings[0].values.slice(0,11))},{id:'lp2-02',text:'-. /\r\n'}]);
  assert.deepEqual(E.run(t).matches,t.pages.map(page=>({page:page.id,matched:false,matchingOpenings:[]})));
 });
 await test('overlapping prefixes retain every matching ID in declared order',async()=>{
  const criterion={kind:'exact-prefix-set',openings:[{id:'long',values:[0,1,2]},{id:'short',values:[0]},{id:'middle',values:[0,1]},{id:'different',values:[1]}]};
  const t=await task([{id:'lp2-00',text:encode([0,1,2,3])},{id:'lp2-01',text:encode([0,1])}],criterion);
  assert.deepEqual(E.run(t).matches,[{page:'lp2-00',matched:true,matchingOpenings:['long','short','middle']},{page:'lp2-01',matched:true,matchingOpenings:['short','middle']}]);
 });
 await test('complete bounds permit 32 named passages and 256 rune prefixes',async()=>{
  const criterion={kind:'exact-prefix-set',openings:Array.from({length:32},(_,i)=>({id:'named-'+i,values:[i%29,...Array.from({length:255},(_,j)=>(j+Math.floor(i/29))%29)]}))};
  const t=await task([{id:'lp2-00',text:encode(criterion.openings[31].values)}],criterion);
  assert.deepEqual(E.run(t).matches,[{page:'lp2-00',matched:true,matchingOpenings:['named-31']}]);
 });
 await test('malformed names, vectors, numbers and unexpected fields reject before work',async()=>{
  const base=await task([{id:'lp2-00',text:encode([0,1])}]);
  const malformed=[[],Array.from({length:33},(_,i)=>({id:'name-'+i,values:[i%29,Math.floor(i/29)]})),null,
   [{id:'Upper',values:[0]}],[{id:'a\n',values:[0]}],[{id:'a'.repeat(65),values:[0]}],[{id:1,values:[0]}],
   [{id:'same',values:[0]},{id:'same',values:[1]}],[{id:'one',values:[0]},{id:'two',values:[0]}],
   ...[[],Array(257).fill(0),[29],[-1],[true],[0.5],[null],['0']].map(values=>[{id:'one',values}]),
   [{id:'one',values:[0],extra:true}]];
  for(const value of malformed){const t=structuredClone(base);t.criterion.openings=value;t.taskId=await E.identity(t,webcrypto);rejected.push(t);let progress=0;assert.throws(()=>E.run(t,{onProgress:()=>progress++}));assert.equal(progress,0);}
  const extra=structuredClone(base);extra.criterion.extra=1;extra.taskId=await E.identity(extra,webcrypto);rejected.push(extra);assert.throws(()=>E.run(extra));
 });
 await test('criterion changes produce distinct task and result identities; legacy shape unchanged',async()=>{
  const pages=[{id:'lp2-00',text:encode([0,1,2])}],single=await task(pages,{kind:'exact-prefix',values:[0]}),set=await task(pages,{kind:'exact-prefix-set',openings:[{id:'one',values:[0]}]}),renamed=await task(pages,{kind:'exact-prefix-set',openings:[{id:'two',values:[0]}]});
  assert.equal(new Set([single.taskId,set.taskId,renamed.taskId]).size,3);
  assert.equal(new Set([single,set,renamed].map(t=>digest(E.run(t)))).size,3);
  assert.deepEqual(E.run(single).matches,[{page:'lp2-00',matched:true}]);
  const reversed=await task(pages,{kind:'exact-prefix-set',openings:[{id:'two',values:[0,1]},{id:'one',values:[0]}]}),ordered=await task(pages,{kind:'exact-prefix-set',openings:[{id:'one',values:[0]},{id:'two',values:[0,1]}]});
  assert.notEqual(reversed.taskId,ordered.taskId);
  const forged=E.run(ordered);forged.matches[0].matchingOpenings.reverse();await assert.rejects(E.verify(ordered,forged,webcrypto));
 });
 await test('independent Python validates and reproduces every full JS decision and identity',async()=>{
  const code="import sys,json,importlib.util; spec=importlib.util.spec_from_file_location('runner','tools/research_runner.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); data=json.load(sys.stdin); output=[]\nfor t in data['accepted']:\n assert m.task_identity(t)==t['taskId']; output.append(m.run(t))\nfor t in data['rejected']:\n try: m.run(t)\n except (ValueError,TypeError): continue\n raise AssertionError('invalid task accepted')\nprint(json.dumps(output,ensure_ascii=False))";
  const output=JSON.parse(execFileSync('python',['-c',code],{cwd:require('node:path').join(__dirname,'..'),input:JSON.stringify({accepted,rejected}),encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'},maxBuffer:4000000}));
  assert.equal(output.length,accepted.length);output.forEach((result,i)=>assert.deepEqual(result,E.run(accepted[i])));
 });
 console.log(groups+' named opening-set groups passed; '+accepted.length+' full JS/Python parity vectors; zero manuscript target runs.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
