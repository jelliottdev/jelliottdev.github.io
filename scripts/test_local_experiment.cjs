'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {execFileSync}=require('node:child_process'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js');
const V=require('../local-run-view.js');
const root=path.resolve(__dirname,'..');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
let groups=0;
async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
function body(patch={}){return {title:'Synthetic local experiment',pages:[{id:'lp2-15',text:'ᚠᚢ-ᚦᚩ/\r\nᚱᚳ.ᚷ'}],alphabet,steps:[],criterion:{kind:'measurement'},...patch};}
async function prepared(patch){return E.prepare(body(patch),webcrypto);}
async function main(){
 await test('identity covers inputs, ordered steps and criterion; no text is executed',async()=>{
  const task=await prepared();assert.equal((await E.checkIdentity(task,webcrypto)).taskId,task.taskId);
  for(const change of [t=>t.pages[0].text+='ᚠ',t=>t.alphabet.reverse(),t=>t.steps.push({op:'affine',a:1,b:1}),t=>t.criterion={kind:'exact-prefix',values:[0]}]){
   const t=structuredClone(task);change(t);await assert.rejects(E.checkIdentity(t,webcrypto),/changed/);
  }
  const t=await prepared({pages:[{id:'lp2-15',text:'__import__("os").system("not executable")'}]});
  assert.equal(E.run(t).transformed[0].text,t.pages[0].text);
 });
 await test('declared reversal units preserve punctuation and exact line endings',async()=>{
  const cases={word:'ᚢᚠ-ᚩᚦ/\r\nᚳᚱ.ᚷ',line:'ᚩᚦ-ᚢᚠ/\r\nᚷᚳ.ᚱ',page:'ᚷᚳ-ᚱᚩ/\r\nᚦᚢ.ᚠ'};
  for(const [unit,expected]of Object.entries(cases))assert.equal(E.run(await prepared({steps:[{op:'reverse',unit}]})).transformed[0].text,expected);
 });
 await test('prefix checks are exact; measurement has no invented pass/fail',async()=>{
  const measurement=await prepared(),result=await E.verify(measurement,E.run(measurement),webcrypto);assert.deepEqual(result.matches,[]);
  assert.match(E.summary(measurement,result).finding,/left neighbouring rune repeats unchanged/);
  assert.match(E.summary(measurement,result).limit,/does not test readability/);
  const task=await prepared({criterion:{kind:'exact-prefix',values:[0,1,2]}});
  assert.deepEqual(E.run(task).matches,[{page:'lp2-15',matched:true}]);
  assert.match(E.summary(task,await E.verify(task,E.run(task),webcrypto)).finding,/does not establish a decryption/);
  const tooLong=await prepared({criterion:{kind:'exact-prefix',values:Array(8).fill(0)}});assert.equal(E.run(tooLong).matches[0].matched,false);
 });
 await test('replay rejects forged totals, wrong text, missing rows and extra claims',async()=>{
  const task=await prepared({steps:[{op:'cumulative-difference',reset:'line'}]}),result=E.run(task);
  assert.deepEqual(await E.verify(task,result,webcrypto),result);
  for(const change of [r=>r.metrics.runes++,r=>r.metrics.runes+=1e-13,r=>r.transformed[0].text+='ᚠ',r=>r.transformed=[],r=>r.solved=true,r=>r.taskId='a'.repeat(64),r=>r.metrics.ioc=NaN]){
   const forged=structuredClone(result);change(forged);await assert.rejects(E.verify(task,forged,webcrypto),/do not match/);
   assert.throws(()=>E.summary(task,forged));
  }
 });
 await test('bounds reject unsupported steps, false indices, duplicate and impossible pages',async()=>{
  for(const patch of [{steps:[{op:'exec',code:'print(1)'}]},{steps:[{op:'affine',a:true,b:0}]},{steps:Array(9).fill({op:'reverse',unit:'line'})},
   {pages:[{id:'lp2-58',text:'ᚠ'}]},{pages:[{id:'lp2-15',text:'ᚠ'},{id:'lp2-15',text:'ᚢ'}]},
   {pages:[{id:'lp1-17',text:'ᚠ'}]},{pages:[{id:'lp2-15',text:'ᚠ'.repeat(20001)}]},
   {title:'\ud800'},{criterion:{kind:'exact-prefix',values:Array(257).fill(0)}}])await assert.rejects(prepared(patch));
 });
 await test('dynamic result view derives numbers from verified data and rejects arbitrary output',async()=>{
  const task=await prepared({title:'<script>not markup</script>',steps:[{op:'affine',a:0,b:0}]}),result=await E.verify(task,E.run(task),webcrypto),html=V.render(task,result);
  assert(html.includes('After the method: 6 of 6 pairs'));assert(html.includes('Original text: 0 of 6 pairs'));
  assert(html.includes('Computation verified'));assert(html.includes('does not test readability'));
  assert(html.includes('changed neighbouring rune repeats from 0 to 6'));
  assert(!html.includes('<script>'));assert(!html.includes('NaN'));assert(!html.includes('Infinity'));
  assert.throws(()=>V.render(task,{...result,solved:true}));
  assert.throws(()=>V.render(task,E.run(task)),/verified/);
  const changed=structuredClone(task);changed.taskId='a'.repeat(64);assert.throws(()=>V.render(changed,result),/verified/);
  const baseline=await prepared();assert.notEqual(V.render(baseline,await E.verify(baseline,E.run(baseline),webcrypto)),html);
 });
 await test('independent Python execution agrees on ordered methods, resets and real manuscript data',async()=>{
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),'liberpedia-local-parity-'));
  try{
   const steps=[[],...['page','line','word'].map(unit=>[{op:'reverse',unit}]),...['page','line','word'].map(reset=>[{op:'cumulative-difference',reset}]),
    [{op:'reverse',unit:'word'},{op:'affine',a:27,b:24},{op:'cumulative-difference',reset:'page'}]];
   const source=JSON.parse(fs.readFileSync(path.join(root,'data/pages/lp2-15.json'),'utf8'));
   for(const [i,program]of steps.entries()){
    const task=await prepared({steps:program,pages:[...body().pages,{id:'lp2-16',text:source.raw}],criterion:i%2?{kind:'exact-prefix',values:[0,1]}:{kind:'measurement'}});
    const input=path.join(folder,'task.json'),output=path.join(folder,'results-'+i+'.json');fs.writeFileSync(input,JSON.stringify(task));
    execFileSync(process.env.PYTHON||'python',[path.join(root,'tools/research_runner.py'),'--task',input,'--out',output],{stdio:'pipe'});
    const result=JSON.parse(fs.readFileSync(output,'utf8'));
    assert.deepEqual(await E.verify(task,result,webcrypto),E.run(task));
   }
  }finally{
   const actual=fs.realpathSync(folder),parent=fs.realpathSync(os.tmpdir());assert(actual.startsWith(parent+path.sep)&&path.basename(actual).startsWith('liberpedia-local-parity-'));
   fs.rmSync(actual,{recursive:true,force:true});
  }
 });
 console.log('PASS '+groups+' local execution groups; no hosted calls');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
