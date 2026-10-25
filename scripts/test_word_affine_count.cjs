'use strict';
// Synthetic words and exhaustive small-word permutations only; no manuscript target runs.
const assert=require('node:assert/strict'),{webcrypto}=require('node:crypto'),{execFileSync}=require('node:child_process');
const E=require('../local-experiment.js');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),encode=v=>v.map(i=>runes[i]).join('');
const criterion=(lag=1,a=1,b=0,boundaries='non-rune')=>({kind:'word-affine-count',lag,a,b,boundaries});
const accepted=[],rejected=[];let groups=0;
async function task(text,c=criterion(),steps=[],pages){const t=await E.prepare({title:'Synthetic exact word-pair count',alphabet,pages:pages||[{id:'lp2-00',text}],steps,criterion:c},webcrypto);accepted.push(t);return t;}
async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
function* permutations(v){if(!v.length){yield [];return;}for(let i=0;i<v.length;i++)for(const suffix of permutations(v.filter((_,j)=>j!==i)))yield [v[i],...suffix];}
function gcd(a,b){return b?gcd(b,a%b):a;}
function rational(n,d){const g=gcd(n,d);return {numerator:String(n/g),denominator:String(d/g)};}
async function main(){
 await test('hand count and exact expectation including constant maps',async()=>{
  let t=await task(encode([0,0,1]),criterion()),p=E.run(t).wordPairs;
  assert.equal(p.matches,1);assert.equal(p.opportunities,2);assert.deepEqual(p.expected,{numerator:'2',denominator:'3'});
  t=await task(encode([0,0,1]),criterion(1,0,0));p=E.run(t).wordPairs;
  assert.equal(p.matches,1);assert.deepEqual(p.expected,{numerator:'4',denominator:'3'});
 });
 await test('conditional expectation matches exhaustive permutations at every legal lag',async()=>{
  for(const word of [[0,0,1],[0,1,2,1],[0,0,0,1,2],[28,0,1,28]])for(let lag=1;lag<=word.length;lag++)for(const [a,b]of [[0,0],[1,0],[1,1],[27,24],[28,28]]){
   let total=0,trials=0;
   for(const permutation of permutations(word)){trials++;for(let i=0;i<word.length-lag;i++)total+=Number(permutation[i+lag]===(a*permutation[i]+b)%29);}
   const p=E.run(await task(encode(word),criterion(lag,a,b))).wordPairs;
   assert.deepEqual(p.expected,rational(total,trials));
  }
 });
 await test('word boundary rules differ deliberately for spaces, slash, CR and LF',async()=>{
  const text=encode([0,0])+' /\r\n💡'+encode([0,0])+'-'+encode([0,0])+'.'+encode([0,0]);
  const split=E.run(await task(text)).wordPairs,joined=E.run(await task(text,criterion(1,1,0,'hyphen-period'))).wordPairs;
  assert.equal(split.opportunities,4);assert.equal(split.matches,4);
  assert.equal(joined.opportunities,5);assert.equal(joined.matches,5);
  assert.deepEqual(joined.expected,{numerator:'5',denominator:'1'});
 });
 await test('page boundaries never join; empty and short words give zero over one',async()=>{
  const pages=[{id:'lp2-00',text:encode([0])},{id:'lp2-01',text:encode([0])},{id:'lp2-02',text:'-/\r\n.'}];
  const p=E.run(await task('',criterion(1,1,0,'hyphen-period'),[],pages)).wordPairs;
  assert.equal(p.opportunities,0);assert.equal(p.matches,0);assert.deepEqual(p.expected,{numerator:'0',denominator:'1'});
  assert.equal(p.pages.length,3);for(const page of p.pages)assert.deepEqual(page.expected,p.expected);
 });
 await test('aggregation adds reduced fractions exactly and transforms precede counting',async()=>{
  const pages=[{id:'lp2-00',text:encode([0,0,1])},{id:'lp2-01',text:encode([0,0,0,1])}];
  let p=E.run(await task('',criterion(),[],pages)).wordPairs;
  assert.deepEqual(p.expected,{numerator:'13',denominator:'6'});
  const t=await task(encode([0,1,2]),criterion(1,1,0),[{op:'affine',a:0,b:7}]);
  p=E.run(t).wordPairs;assert.equal(p.matches,2);assert.deepEqual(p.expected,{numerator:'2',denominator:'1'});
 });
 await test('maximum legal lag and rune count remain exact without truncation',async()=>{
  const text=encode(Array.from({length:20000},(_,i)=>i%29));
  const p=E.run(await task(text,criterion(12,1,12))).wordPairs;
  assert.equal(p.opportunities,19988);assert.equal(p.matches,19988);
  assert.equal(p.pages[0].opportunities,19988);
 });
 await test('strict criterion and task work limits reject before progress',async()=>{
  const base=await task(encode([0,1]));
  for(const patch of [{lag:0},{lag:13},{lag:1.5},{a:-1},{a:29},{b:true},{boundaries:'word'},{seed:1}]){
   const t={...base,criterion:{...base.criterion,...patch}};t.taskId=await E.identity(t,webcrypto);rejected.push(t);let progress=0;
   assert.throws(()=>E.run(t,{onProgress:()=>progress++}));assert.equal(progress,0);
  }
  const t={...base,pages:[{id:'lp2-00',text:runes[0].repeat(20001)}]};t.taskId=await E.identity(t,webcrypto);rejected.push(t);assert.throws(()=>E.run(t));
 });
 await test('complete result verification rejects forged counts, fractions, pages and extra fields',async()=>{
  const t=await task(encode([0,0,1])),r=E.run(t);assert.deepEqual(r.matches,[]);
  assert.throws(()=>E.summary(t,r));
  const verified=await E.verify(t,r,webcrypto),s=E.summary(t,verified);
  assert.match(s.finding,/1 matches among 2 rune pairs/);assert.match(s.limit,/does not tell us how unlikely/);assert.match(s.limit,/does not account for choosing/);
  for(const change of [x=>x.wordPairs.matches++,x=>x.wordPairs.expected.numerator='3',x=>x.wordPairs.expected.denominator='6',x=>x.wordPairs.pages.reverse().push(x.wordPairs.pages[0]),x=>x.wordPairs.extra=1,x=>delete x.wordPairs]){
   const forged=structuredClone(r);change(forged);await assert.rejects(E.verify(t,forged,webcrypto));
  }
  assert.throws(()=>{verified.wordPairs.matches++;},TypeError);assert.deepEqual(E.summary(t,verified),s);
 });
 await test('legacy result fields stay exact and absent measurement field cannot be forged',async()=>{
  const t=await task(encode([0,0,1]));t.criterion={kind:'measurement'};t.taskId=await E.identity(t,webcrypto);accepted.push(t);
  const r=E.run(t);assert.equal('wordPairs'in r,false);assert.deepEqual(Object.keys(r).sort(),['schema','taskId','engine','runnerVersion','metrics','matches','transformed'].sort());
  await assert.rejects(E.verify(t,{...r,wordPairs:{}},webcrypto));
 });
 await test('independent Python runner matches every complete JS result and rejects invalid tasks',async()=>{
  const code="import sys,json,importlib.util; spec=importlib.util.spec_from_file_location('runner','tools/research_runner.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); data=json.load(sys.stdin); output=[]\nfor t in data['accepted']: output.append(m.run(t))\nfor t in data['rejected']:\n try: m.run(t)\n except (ValueError,TypeError): continue\n raise AssertionError('invalid task accepted')\nprint(json.dumps(output,ensure_ascii=False))";
  const output=JSON.parse(execFileSync('python',['-c',code],{cwd:require('node:path').join(__dirname,'..'),input:JSON.stringify({accepted,rejected}),encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'},maxBuffer:20000000}));
  assert.equal(output.length,accepted.length);for(let i=0;i<output.length;i++)assert.deepEqual(output[i],E.run(accepted[i]));
 });
 console.log(groups+' word-affine count groups passed; '+accepted.length+' full JS/Python parity vectors.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
