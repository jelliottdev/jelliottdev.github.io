/* Exact diagnostic scoring, independent controls and offline Python parity. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),E=require('../local-experiment.js'),Controls=require('../local-plan-controls.js');
const alphabet=JSON.parse(fs.readFileSync(path.join(root,'data/local-run-inputs.json'),'utf8')).alphabet;
const hash=value=>crypto.createHash('sha256').update(E.stable(value)).digest('hex');
const criterion={kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'};
const text=n=>Array.from({length:n},(_,i)=>alphabet[(i*i+7*i+3)%29].rune+(i%9===0?'-':i%11===0?'\n':'')).join('');
async function make(n=100,steps=[],pages){return E.prepare({title:'Language-order diagnostic fixture',pages:pages||[{id:'lp2-00',text:text(n)}],alphabet,steps,criterion});}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('old criteria remain lazy and retain pinned pre-change task and result identities',async()=>{
  assert(!require.cache[require.resolve('../language-score.js')]);assert(!require.cache[require.resolve('../language-model-data.js')]);
  const task=await E.prepare({title:'Legacy compatibility fixture',pages:[{id:'lp2-00',text:'ᚠᚢ-ᚦᚩ\nᚱ'}],alphabet,steps:[{op:'reverse',unit:'word'}],criterion:{kind:'measurement'}});
  assert.equal(task.taskId,'49dcb3990e33bdd5b41d7addb39e78cd12c944aa0a367008a4f07a0368073fe2');assert.equal(hash(E.run(task)),'d7224474ad021e34cae754823c077b2ad6f9684e80d86a698af019f1ce817dd2');
  await Controls.prepare(task);assert(!require.cache[require.resolve('../language-score.js')]);
 });
 const scorer=require('../language-score.js'),cases=[];
 await test('short streams are explicit insufficient comparisons, including empty and trigram boundaries',async()=>{
  for(const n of [0,1,2,3,39,40,41]){const task=await make(n),result=await E.verify(task,E.run(task)),page=result.languageScore.pages[0];cases.push(task);assert.equal(page.runes,n);assert.equal(page.windows,Math.max(0,n-2));assert.equal(page.status,n<40?'insufficient':'compared');assert.equal(page.models.length,n<40?0:8);assert.deepEqual(result.matches,[]);assert.equal(result.runnerVersion,'1');assert.equal(result.engine,'rune-program-v1');assert(!Object.hasOwn(result,'accepted'));assert(!Object.hasOwn(result,'winner'));assert(!Object.hasOwn(result,'readable'));assert.match(E.summary(task,result).limit,/do not identify a language/);}
 });
 await test('complete transformed outputs are scored per page under pinned model, without joining short pages',async()=>{
  const methods=[[{op:'reverse',unit:'line'}],[{op:'affine',a:7,b:7}],[{op:'cumulative-difference',reset:'word'}],[{op:'keyed-shift',key:[23,18,3,4],mode:'plaintext-autokey',direction:'subtract',reset:'line'}],[{op:'interrupted-keyed-shift',key:[1,2,3],direction:'add',reset:'word',interrupts:[0,19]}]];
  for(const steps of methods){const task=await make(127,steps),result=E.run(task);cases.push(task);const values=Array.from(result.transformed[0].text).filter(ch=>alphabet.some(a=>a.rune===ch)).map(ch=>alphabet.findIndex(a=>a.rune===ch));assert.deepEqual(result.languageScore.pages[0],{page:'lp2-00',...scorer.evaluate(values)});assert.equal(result.languageScore.modelSha256,criterion.modelSha256);}
  const task=await make(0,[],[{id:'lp2-00',text:text(30)},{id:'lp2-01',text:text(30)}]);cases.push(task);assert(E.run(task).languageScore.pages.every(page=>page.status==='insufficient'));
 });
 await test('unknown model pins, fields and changed alphabet order fail closed',async()=>{
  for(const bad of [{...criterion,modelSha256:'0'.repeat(64)},{...criterion,modelId:'another-model'},{...criterion,threshold:1}])await assert.rejects(()=>E.prepare({title:'Invalid model',pages:[{id:'lp2-00',text:text(50)}],alphabet,steps:[],criterion:bad}));
  const changed=alphabet.map(v=>({...v}));[changed[0],changed[1]]=[changed[1],changed[0]];await assert.rejects(()=>E.prepare({title:'Changed order',pages:[{id:'lp2-00',text:text(50)}],alphabet:changed,steps:[],criterion}));
  const task=await make(),result=E.run(task);result.languageScore.pages[0].models[0].total++;await assert.rejects(()=>E.verify(task,result));
 });
 let suite;
 await test('independent implementation controls cover numeric scores and catch a corrupted production scorer',async()=>{
  const target=await make(110,[{op:'affine',a:7,b:7}]);suite=await Controls.prepare(target);assert.equal(suite.cases.length,2);await Controls.validate(suite,target);
  for(const item of suite.cases){const result=E.run(item.task);assert(result.languageScore.pages.every(page=>page.status==='compared'));assert.equal(hash(result),item.expectedResultSha256);cases.push(item.task);}
  const original=scorer.evaluate;scorer.evaluate=values=>{const result=original(values);if(result.models.length)result.models[0].total++;return result;};
  try{await assert.rejects(()=>Controls.prepare(target),/independent synthetic reference/);}finally{scorer.evaluate=original;}
 });
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'liberpedia-language-execution-'));
 try{
  await test('independent Python reproduces complete JavaScript results and control digests exactly',async()=>{
   const input=path.join(temp,'tasks.json');fs.writeFileSync(input,JSON.stringify(cases));
   const program="import sys,json,importlib.util; s=importlib.util.spec_from_file_location('runner',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); tasks=json.load(open(sys.argv[2],encoding='utf-8')); print(json.dumps([m.run(task) for task in tasks],ensure_ascii=True,allow_nan=False))";
   const output=JSON.parse(cp.execFileSync('python',['-c',program,path.join(root,'tools/research_runner.py'),input],{encoding:'utf8',maxBuffer:8*1024*1024}));assert.equal(output.length,cases.length);output.forEach((result,i)=>assert.deepEqual(result,E.run(cases[i])));
   for(const item of suite.cases){const index=cases.findIndex(task=>task.taskId===item.task.taskId);assert.equal(hash(output[index]),item.expectedResultSha256);}
  });
  await test('offline runner loads no model for old tasks and rejects missing or tampered optional model assets',async()=>{
   const runner=path.join(temp,'research_runner.py');fs.copyFileSync(path.join(root,'tools/research_runner.py'),runner);
   const task=await make(),file=path.join(temp,'language-task.json');fs.writeFileSync(file,JSON.stringify(task));
   const run=(taskFile,out)=>cp.spawnSync('python',[runner,'--task',taskFile,'--out',path.join(temp,out)],{encoding:'utf8'});
   assert.notEqual(run(file,'missing.json').status,0);
   const legacy=await E.prepare({...task,criterion:{kind:'measurement'}}),legacyFile=path.join(temp,'legacy-task.json');fs.writeFileSync(legacyFile,JSON.stringify(legacy));assert.equal(run(legacyFile,'legacy-result.json').status,0);
   const model=JSON.parse(fs.readFileSync(path.join(root,'tools/language-model.json'),'utf8'));model.payload.models[0].scores[0]--;fs.writeFileSync(path.join(temp,'language-model.json'),JSON.stringify(model));const denied=run(file,'tampered.json');assert.notEqual(denied.status,0);assert.match(denied.stderr,/pinned rune-language model changed/);assert(!fs.existsSync(path.join(temp,'tampered.json')));
   fs.copyFileSync(path.join(root,'tools/language-model.json'),path.join(temp,'language-model.json'));const valid=run(file,'language-result.json');assert.equal(valid.status,0,valid.stderr);assert.deepEqual(JSON.parse(fs.readFileSync(path.join(temp,'language-result.json'),'utf8')),E.run(task));
  });
 }finally{assert(path.resolve(temp).startsWith(path.resolve(os.tmpdir())+path.sep+'liberpedia-language-execution-'));fs.rmSync(temp,{recursive:true,force:true});}
 console.log('Language diagnostic execution: '+groups+' groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
