/* Offline reproduction with invented inputs only. No server, packages or manuscript execution. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),{execFileSync,spawnSync}=require('node:child_process'),{webcrypto,createHash}=require('node:crypto');
const P=require('../declarative-run-package.js'),V=require('../declarative-rune-program.js'),C=require('../declarative-plan-controls.js'),J=require('../finite-json.js'),Zip=require('../local-run-package.js'),E=require('../local-experiment.js'),Language=require('../language-score.js');
const root=path.resolve(__dirname,'..'),sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const rawSources=new Map(P.SOURCES.map(pin=>[pin.path,fs.readFileSync(path.join(root,pin.path),'utf8').replace(/\r\n/g,'\n')]));
function fetcher(log=[],change){return async(url,options)=>{const name=url.slice('https://jelliottdev.github.io/'.length);assert.equal(url,'https://jelliottdev.github.io/'+name);assert(rawSources.has(name));assert.equal(options.redirect,'error');assert(options.signal);log.push(name);return new Response(change?change(name,rawSources.get(name)):rawSources.get(name));};}
async function fixture(criterion={kind:'measurement'}){const alphabet=require('../data/local-run-inputs.json').alphabet,text=criterion.kind==='language-score'?alphabet.map(r=>r.rune).join('').repeat(2):alphabet[0].rune.repeat(3)+'! '+alphabet[1].rune.repeat(2)+'\n'+alphabet[2].rune;const task=await V.prepare({title:'Invented downloadable target only',alphabet,pages:[{id:'lp2-00',text}],steps:[{op:'collapse-adjacent-repeats',unit:'word',policy:'all-but-first'},{op:'affine',a:2,b:1}],criterion},webcrypto);return {task,inputVersion:'raw',controls:await C.prepare(task,webcrypto),crypto:webcrypto,fetcher:fetcher()};}
function unpack(bytes){const out=new Map();let offset=0;while(bytes.readUInt32LE(offset)===0x04034b50){const length=bytes.readUInt32LE(offset+18),names=bytes.readUInt16LE(offset+26),extra=bytes.readUInt16LE(offset+28),name=bytes.subarray(offset+30,offset+30+names).toString('utf8'),start=offset+30+names+extra;out.set(name,bytes.subarray(start,start+length));offset=start+length;}return out;}
function folder(files){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'declarative-package-'));for(const [name,data] of files)fs.writeFileSync(path.join(dir,name),data);return dir;}
function run(dir){return spawnSync(process.execPath,['reproduce.cjs'],{cwd:dir,encoding:'utf8',timeout:20000});}
function rehash(dir,name){const m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),entry=m.files.find(x=>x.path===name),bytes=fs.readFileSync(path.join(dir,name));entry.bytes=bytes.length;entry.sha256=sha(bytes);fs.writeFileSync(path.join(dir,'manifest.json'),JSON.stringify(m));}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('fixed LF source pins and bounded deterministic ZIP preserve full task controls and optional receipt',async()=>{
  for(const pin of P.SOURCES){assert.equal(Buffer.byteLength(rawSources.get(pin.path)),pin.bytes);assert.equal(sha(rawSources.get(pin.path)),pin.sha256);}
  const args=await fixture(),result=V.run(args.task),log=[],before=E.stable({task:args.task,controls:args.controls,result});const built=await P.build({...args,result,fetcher:fetcher(log)}),bytes=Buffer.from(await built.blob.arrayBuffer());assert.equal(built.blob.type,'application/zip');assert.equal(built.filename,'rune-program-v2-'+args.task.taskId+'.zip');assert.deepEqual(log,P.SOURCES.map(x=>x.path));assert(bytes.length<P.MAX_ZIP);assert.equal(E.stable({task:args.task,controls:args.controls,result}),before);
  assert.deepEqual(Buffer.from(await (await P.build({...args,result})).blob.arrayBuffer()),bytes);
  const files=unpack(bytes);assert.equal(JSON.parse(files.get('package.json')).type,'commonjs');assert.deepEqual(JSON.parse(files.get('task.json')),args.task);assert.deepEqual(JSON.parse(files.get('result.json')),result);const dir=folder(files);
  try{const proc=run(dir);assert.equal(proc.status,0,proc.stderr);const row=JSON.parse(proc.stdout.split('\n')[0]);assert.equal(row.resultSha256,sha(E.stable(result)));assert.equal(row.savedResultVerified,true);
   fs.writeFileSync(path.join(dir,'package.zip'),bytes);execFileSync('python',['-c','import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None; assert len(z.namelist())==13',path.join(dir,'package.zip')]);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
 });
 await test('building never executes a target; result-free offline CLI computes the exact invented program',async()=>{
  const args=await fixture(),expected=V.run(args.task),ctx={DeclarativeRuneProgram:{...V,run(){assert.fail('Export cannot run the target');},verify(){assert.fail('Export cannot replay the target');}},DeclarativePlanControls:C,FiniteJSON:J,LocalRunPackage:Zip,TextEncoder,Uint8Array,Blob,AbortController,setTimeout,clearTimeout,crypto:webcrypto};
  vm.runInNewContext(fs.readFileSync(path.join(root,'declarative-run-package.js'),'utf8'),ctx);const built=await ctx.DeclarativeRunPackage.build(args);
  const dir=folder(unpack(Buffer.from(await built.blob.arrayBuffer())));try{const proc=run(dir);assert.equal(proc.status,0,proc.stderr);const row=JSON.parse(proc.stdout.split('\n')[0]);assert.equal(row.savedResultVerified,false);assert.equal(row.resultSha256,sha(E.stable(expected)));assert.equal(fs.existsSync(path.join(dir,'result.json')),false);}finally{fs.rmSync(dir,{recursive:true,force:true});}
 });
 await test('every executable and data file hash is checked before modules load; rehashed bad saved math still fails replay',async()=>{
  const args=await fixture(),result=V.run(args.task),files=unpack(Buffer.from(await (await P.build({...args,result})).blob.arrayBuffer()));
  for(const name of ['declarative-rune-program.js','reproduce.cjs','task.json','controls.json','result.json']){const dir=folder(files);try{const changed=fs.readFileSync(path.join(dir,name));changed[changed.length-1]=32;fs.writeFileSync(path.join(dir,name),changed);const proc=run(dir);assert.notEqual(proc.status,0);assert.match(proc.stderr,/hash mismatch/);}finally{fs.rmSync(dir,{recursive:true,force:true});}}
  for(const name of ['result.json','controls.json']){const dir=folder(files);try{const data=JSON.parse(fs.readFileSync(path.join(dir,name)));if(name==='result.json')data.alignment.pages[0].outputToInput[0]=1;else data.cases[0].expectedResultSha256='0'.repeat(64);fs.writeFileSync(path.join(dir,name),JSON.stringify(data));rehash(dir,name);const proc=run(dir);assert.notEqual(proc.status,0);assert.doesNotMatch(proc.stderr,/hash mismatch/);}finally{fs.rmSync(dir,{recursive:true,force:true});}}
 });
 await test('invalid tasks controls edition source bytes and getter payloads fail export without arbitrary transport',async()=>{
  const args=await fixture();for(const bad of [{...args,inputVersion:'other'},{...args,task:{...args.task,taskId:'0'.repeat(64)}},{...args,controls:{...args.controls,version:1}},{...args,extra:true},{...args,result:{}}])await assert.rejects(()=>P.build(bad));
  await assert.rejects(()=>P.build({...args,fetcher:fetcher([],(_,text)=>text+' ')}),/pin|size/);
  await assert.rejects(()=>P.build({...args,fetcher:fetcher([],(_,text)=>text.replace(/\n/g,'\r\n'))}),/pin|size/);
  await assert.rejects(()=>P.build({...args,fetcher:async()=>new Response('no',{status:503})}),/unavailable/);
  let reads=0;const bad={...args};Object.defineProperty(bad,'task',{enumerable:true,get(){reads++;return args.task;}});await assert.rejects(()=>P.build(bad));assert.equal(reads,0);
 });
 await test('detached snapshots survive caller mutation and UMD builds with the same offline language closure',async()=>{
  const args=await fixture(Language.criterion());args.task=structuredClone(args.task);args.controls=structuredClone(args.controls);const original=structuredClone(args.task),result=structuredClone(V.run(args.task));assert.equal(result.languageScore.pages[0].status,'compared');let mutated=false;
  const built=await P.build({...args,result,fetcher:fetcher([],(_,text)=>{if(!mutated){mutated=true;args.task.pages[0].text='Changed';args.controls.cases[0].expectedResultSha256='0'.repeat(64);result.transformed[0].text='Changed';}return text;})});const files=unpack(Buffer.from(await built.blob.arrayBuffer()));assert.deepEqual(JSON.parse(files.get('task.json')),original);
  const dir=folder(files);try{const proc=run(dir);assert.equal(proc.status,0,proc.stderr);}finally{fs.rmSync(dir,{recursive:true,force:true});}
  const ctx={DeclarativeRuneProgram:V,DeclarativePlanControls:C,FiniteJSON:J,LocalRunPackage:Zip,TextEncoder,Uint8Array,Blob,AbortController,setTimeout,clearTimeout,crypto:webcrypto};vm.runInNewContext(fs.readFileSync(path.join(root,'declarative-run-package.js'),'utf8'),ctx);const next=await fixture();const output=await ctx.DeclarativeRunPackage.build(next);assert(output.blob instanceof Blob);
 });
 console.log(groups+' declarative package groups passed; invented targets only, offline Node replay.');
})().catch(error=>{console.error(error);process.exitCode=1;});
