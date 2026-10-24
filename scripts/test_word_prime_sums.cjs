'use strict';
// Synthetic exact-word ledgers only; no manuscript target execution.
const assert=require('node:assert/strict'),{webcrypto}=require('node:crypto'),{execFileSync}=require('node:child_process'),path=require('node:path');
const E=require('../local-experiment.js'),runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
const primes=[2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109];
const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:primes[i]})),encode=v=>v.map(i=>runes[i]).join('');
const criterion=(table='canonical',boundaries='non-rune')=>({kind:'word-prime-sums',table,boundaries});
const accepted=[],rejected=[];let groups=0;
async function task(text,c=criterion(),steps=[],pages,a=alphabet){const t=await E.prepare({title:'Synthetic word prime ledger',alphabet:a,pages:pages||[{id:'lp2-15',text}],steps,criterion:c},webcrypto);accepted.push(t);return t;}
async function test(label,fn){await fn();groups++;console.log('PASS '+label);}
async function invalid(t){t={...t};t.taskId=await E.identity(t,webcrypto);rejected.push(t);let progress=0;assert.throws(()=>E.run(t,{onProgress:()=>progress++}));assert.equal(progress,0);}
async function main(){
 await test('canonical and reversed tables are actual ordered lookups, not an arithmetic complement',async()=>{
  const text=encode([0])+'-'+encode([1])+'-'+encode([28]);
  const canonical=E.run(await task(text)).wordSums,reversed=E.run(await task(text,criterion('reversed'))).wordSums;
  assert.deepEqual(canonical.pages[0].words.map(w=>w.sum),[2,3,109]);assert.equal(canonical.words,3);assert.equal(canonical.total,114);
  assert.deepEqual(reversed.pages[0].words.map(w=>w.sum),[109,107,2]);assert.equal(reversed.total,218);assert.notEqual(reversed.pages[0].words[1].sum,111-3);
 });
 await test('shared boundaries preserve word order and join layout only when explicitly selected',async()=>{
  const text='-/.'+encode([0])+' /💡\r\n'+encode([1])+'‐'+encode([2])+'--'+encode([28])+'.';
  const split=E.run(await task(text)).wordSums,joined=E.run(await task(text,criterion('canonical','hyphen-period'))).wordSums;
  assert.deepEqual(split.pages[0].words.map(w=>w.sum),[2,3,5,109]);
  assert.deepEqual(joined.pages[0].words,[{runes:encode([0,1,2]),sum:10},{runes:encode([28]),sum:109}]);
  assert.equal(split.total,joined.total);assert.equal(joined.words,2);
 });
 await test('each page has separate ordered groups and empty pages never fabricate words',async()=>{
  const pages=[{id:'lp2-15',text:encode([0])},{id:'lp2-16',text:'- . /\r\n💡'},{id:'lp2-17',text:encode([1])}];
  const p=E.run(await task('',criterion('reversed','hyphen-period'),[],pages)).wordSums;
  assert.deepEqual(p,{words:2,total:216,pages:[{page:'lp2-15',words:[{runes:encode([0]),sum:109}]},{page:'lp2-16',words:[]},{page:'lp2-17',words:[{runes:encode([1]),sum:107}]}]});
  const empty=E.run(await task('',criterion(),[],[{id:'lp2-15',text:''},{id:'lp2-16',text:' /\n'}])).wordSums;
  assert.deepEqual(empty,{words:0,total:0,pages:[{page:'lp2-15',words:[]},{page:'lp2-16',words:[]}]});
 });
 await test('word reversal leaves each sum unchanged while output rune order is accurately recorded',async()=>{
  const text=encode([0,1,28])+'-'+encode([2,5]);
  for(const table of ['canonical','reversed']){
   const original=E.run(await task(text,criterion(table))).wordSums,reversed=E.run(await task(text,criterion(table),[{op:'reverse',unit:'word'}])).wordSums;
   assert.deepEqual(original.pages[0].words.map(w=>w.sum),reversed.pages[0].words.map(w=>w.sum));
   assert.deepEqual(reversed.pages[0].words.map(w=>w.runes),[encode([28,1,0]),encode([5,2])]);
  }
 });
 await test('all supported transformations can precede measurement with current output values',async()=>{
  const text=encode([0,1])+'-'+encode([2,3,4]),steps=[{op:'affine',a:2,b:1},{op:'reverse',unit:'line'},{op:'cumulative-difference',reset:'word'},
   {op:'keyed-shift',key:[1,2],mode:'plaintext-autokey',direction:'subtract',reset:'page'},
   {op:'finite-shift',key:[0,1,2,3,4],direction:'add',reset:'page'},
   {op:'interrupted-keyed-shift',key:[2,3],interrupts:[0,2],direction:'add',reset:'word'}];
  for(const table of ['canonical','reversed']){
   const t=await task(text,criterion(table),steps),r=E.run(t),expected=r.transformed[0].text.split('-').map(word=>({runes:word,sum:Array.from(word).reduce((s,ch)=>s+primes[table==='reversed'?28-runes.indexOf(ch):runes.indexOf(ch)],0)}));
   assert.deepEqual(r.wordSums.pages[0].words,expected);assert.equal(r.wordSums.total,expected.reduce((s,w)=>s+w.sum,0));
  }
 });
 await test('custom rune Unicode and maximum safe total remain exact without truncation',async()=>{
  const special=structuredClone(alphabet);special[0].rune='🌀';
  const unicode=E.run(await task('🌀 /'+encode([1]),criterion(),[],undefined,special)).wordSums;
  assert.deepEqual(unicode.pages[0].words,[{runes:'🌀',sum:2},{runes:encode([1]),sum:3}]);
  const huge=alphabet.map(v=>({...v,prime:1000000})),large=E.run(await task(runes[0].repeat(20000),criterion(),[],undefined,huge)).wordSums;
  assert.equal(large.words,1);assert.equal(large.total,20000000000);assert.equal(large.pages[0].words[0].sum,20000000000);assert(Number.isSafeInteger(large.total));
 });
 await test('strict criteria reject unknown fields table guesses and resource overflow before progress',async()=>{
  const base=await task(encode([0,1]));
  for(const patch of [{table:'atbash'},{table:0},{boundaries:'words'},{boundaries:null},{seed:3301},{lag:6},{table:['canonical']}])await invalid({...base,criterion:{...base.criterion,...patch}});
  for(const field of ['table','boundaries']){const c={...base.criterion};delete c[field];await invalid({...base,criterion:c});}
  await invalid({...base,pages:[{id:'lp2-15',text:runes[0].repeat(20001)}]});
 });
 await test('verification rejects forged ledgers, word order, totals, added fields and different identities',async()=>{
  const t=await task(encode([0,1])+'-'+encode([28])),r=E.run(t);assert.deepEqual(r.matches,[]);assert.throws(()=>E.summary(t,r));
  const verified=await E.verify(t,r,webcrypto),summary=E.summary(t,verified);assert.equal(summary.finding,'2 words measured with the canonical prime table.');assert.match(summary.limit,/not a decoding or a statistical test/);assert.deepEqual(summary.comparison,[]);
  for(const change of [x=>x.wordSums.total++,x=>x.wordSums.words++,x=>x.wordSums.pages[0].words.reverse(),x=>x.wordSums.pages[0].words[0].sum++,x=>x.wordSums.pages[0].words[0].runes=encode([28]),x=>delete x.wordSums,x=>x.wordSums.claim='decoded']){const forged=structuredClone(r);change(forged);await assert.rejects(E.verify(t,forged,webcrypto));}
  const changed={...t,criterion:criterion('reversed')};await assert.rejects(E.verify(changed,r,webcrypto));
  for(const c of [{kind:'measurement'},{kind:'exact-prefix',values:[0]}]){const old=await task(encode([0]),c);const result=E.run(old);assert.equal('wordSums'in result,false);await assert.rejects(E.verify(old,{...result,wordSums:{}},webcrypto));}
 });
 await test('independent Python reproduces every complete result and strict invalid rejection',async()=>{
  const code="import sys,json,importlib.util; spec=importlib.util.spec_from_file_location('runner','tools/research_runner.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); data=json.load(sys.stdin); output=[]\nfor t in data['accepted']: output.append(m.run(t))\nfor t in data['rejected']:\n try: m.run(t)\n except (ValueError,TypeError): continue\n raise AssertionError('invalid task accepted')\nprint(json.dumps(output,ensure_ascii=False))";
  const output=JSON.parse(execFileSync('python',['-c',code],{cwd:path.join(__dirname,'..'),input:JSON.stringify({accepted,rejected}),encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'},maxBuffer:20000000}));
  assert.equal(output.length,accepted.length);for(let i=0;i<output.length;i++)assert.deepEqual(output[i],E.run(accepted[i]));
 });
 console.log(groups+' word-prime sums groups passed; '+accepted.length+' accepted and '+rejected.length+' rejected JS/Python parity vectors.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
