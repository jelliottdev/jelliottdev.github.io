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
 await test('keyed shifts match hand-computed repeat/plaintext/ciphertext histories in both directions',async()=>{
  const vectors={subtract:{repeat:[0,0,2,2,4,4],'plaintext-autokey':[0,0,3,4,2,2],'ciphertext-autokey':[0,0,2,2,2,2]},
   add:{repeat:[2,4,4,6,6,8],'plaintext-autokey':[2,4,5,8,10,14],'ciphertext-autokey':[2,4,4,6,8,10]}};
  for(const [direction,modes]of Object.entries(vectors))for(const [mode,expected]of Object.entries(modes)){
   const task=await prepared({pages:[{id:'lp2-15',text:[1,2,3,4,5,6].map(i=>runes[i]).join('')}],steps:[{op:'keyed-shift',key:[1,2],mode,direction,reset:'page'}]});
   const result=E.run(task);assert.deepEqual(Array.from(result.transformed[0].text,c=>runes.indexOf(c)),expected,direction+'/'+mode);await E.verify(task,result,webcrypto);
   const forged=structuredClone(result);forged.transformed[0].text=runes[28]+forged.transformed[0].text.slice(1);await assert.rejects(E.verify(task,forged,webcrypto));
  }
 });
 await test('key history skips separators, respects every reset and never carries across pages',async()=>{
  const text=runes[1]+runes[2]+' / '+runes[3]+runes[4]+runes[5]+'\r\n'+runes[6]+runes[7];
  const vectors={subtract:{
   page:{repeat:[0,0,2,2,4,4,6],'plaintext-autokey':[0,0,3,4,2,2,5],'ciphertext-autokey':[0,0,2,2,2,2,2]},
   line:{repeat:[0,0,2,2,4,5,5],'plaintext-autokey':[0,0,3,4,2,5,5],'ciphertext-autokey':[0,0,2,2,2,5,5]},
   word:{repeat:[0,0,2,2,4,5,5],'plaintext-autokey':[0,0,2,2,3,5,5],'ciphertext-autokey':[0,0,2,2,2,5,5]}},add:{
   page:{repeat:[2,4,4,6,6,8,8],'plaintext-autokey':[2,4,5,8,10,14,17],'ciphertext-autokey':[2,4,4,6,8,10,12]},
   line:{repeat:[2,4,4,6,6,7,9],'plaintext-autokey':[2,4,5,8,10,7,9],'ciphertext-autokey':[2,4,4,6,8,7,9]},
   word:{repeat:[2,4,4,6,6,7,9],'plaintext-autokey':[2,4,4,6,9,7,9],'ciphertext-autokey':[2,4,4,6,8,7,9]}}};
  for(const [direction,resets]of Object.entries(vectors))for(const [reset,modes]of Object.entries(resets))for(const [mode,expected]of Object.entries(modes)){
   const task=await prepared({pages:[{id:'lp2-15',text},{id:'lp2-16',text:runes[1]+runes[2]}],steps:[{op:'keyed-shift',key:[1,2],mode,direction,reset}]});
   const result=E.run(task),actual=result.transformed[0].text;
   assert.deepEqual(Array.from(actual).filter(c=>runes.includes(c)).map(c=>runes.indexOf(c)),expected,direction+'/'+reset+'/'+mode);
   assert.deepEqual(Array.from(actual).map((c,i)=>[c,i]).filter(([c])=>!runes.includes(c)),Array.from(text).map((c,i)=>[c,i]).filter(([c])=>!runes.includes(c)));
   assert.equal(result.transformed[1].text,(direction==='subtract'?[0,0]:[2,4]).map(i=>runes[i]).join(''));
  }
 });
 await test('key bounds, modulo edges, long seeds and step-local ciphertext history are exact',async()=>{
  const base={op:'keyed-shift',key:[0,28],mode:'repeat',direction:'subtract',reset:'page'};
  for(const mode of ['repeat','plaintext-autokey','ciphertext-autokey']){
   const task=await prepared({pages:[{id:'lp2-15',text:runes[0]+runes[28]}],steps:[{...base,mode,key:Array(256).fill(28)}]});
   assert.equal(E.run(task).transformed[0].text,runes[1]+runes[0]);
  }
  const edges=await prepared({pages:[{id:'lp2-15',text:runes[0]+runes[28]+runes[0]+runes[28]}],steps:[base]});assert.equal(E.run(edges).transformed[0].text,runes[0].repeat(4));
  const pipeline=await prepared({pages:[{id:'lp2-15',text:[1,2,3,4].map(i=>runes[i]).join('')}],steps:[{op:'affine',a:2,b:1},{...base,key:[1],mode:'ciphertext-autokey'}]});
  assert.equal(E.run(pipeline).transformed[0].text,[2,2,2,2].map(i=>runes[i]).join(''),'Ciphertext history reads input after earlier steps, not whole-program original text');
  for(const patch of [{key:[]},{key:[true]},{key:[-1]},{key:[29]},{key:[1.5]},{key:Array(257).fill(0)},{key:'KEY'},{mode:'unknown'},{direction:'decode'},{reset:'none'},{phase:0},{skip:[]}])await assert.rejects(prepared({steps:[{...base,...patch}]}));
 });
 await test('Welcome known-reading control is exactly the first48 runes before its first interruption',async()=>{
  const methods=JSON.parse(fs.readFileSync(path.join(root,'data/evidence/reading-methods.json'),'utf8')).controls;
  const control=methods.find(c=>c.id==='welcome'),page=JSON.parse(fs.readFileSync(path.join(root,'data/pages/lp1-03.json'),'utf8'));
  const index=JSON.parse(fs.readFileSync(path.join(root,'data/index.json'),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
  const known=JSON.parse(fs.readFileSync(path.join(root,'data/evidence/known-readings.json'),'utf8')).controls.find(c=>c.id==='welcome').decoded_pages.find(p=>p.page==='lp1-03');
  assert.equal(control.skip[0],48);assert.equal(control.start,0);assert.equal(control.shift,0);
  const symbols=new Set(index.map(r=>r.rune));let count=0,prefix='';for(const ch of page.raw){if(symbols.has(ch)&&count===48)break;prefix+=ch;if(symbols.has(ch))count++;}
  assert.equal(count,48);const expected=known.rune_indices.slice(0,48);
  const task=await prepared({title:'Welcome prefix before first interruption',alphabet:index,pages:[{id:page.id,text:prefix}],steps:[{op:'keyed-shift',key:control.key,mode:'repeat',direction:'subtract',reset:'page'}],criterion:{kind:'exact-prefix',values:expected}});
  const result=await E.verify(task,E.run(task),webcrypto),positions=new Map(index.map((r,i)=>[r.rune,i]));
  assert.deepEqual(Array.from(result.transformed[0].text).filter(c=>positions.has(c)).map(c=>positions.get(c)),expected);assert.deepEqual(result.matches,[{page:'lp1-03',matched:true}]);
  const latin=Array.from(result.transformed[0].text,c=>positions.has(c)?index[positions.get(c)].latin:c).join('');assert(page.reading.literal.startsWith(latin),'Preserved separators and multi-letter GP labels match archived literal reading before skip48');
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
