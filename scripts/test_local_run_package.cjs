'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process'),{webcrypto,createHash}=require('node:crypto');
const E=require('../local-experiment.js'),P=require('../local-run-package.js');
const root=path.resolve(__dirname,'..'),runner=fs.readFileSync(path.join(root,'tools/research_runner.py'),'utf8');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
async function main(){
 const task=await E.prepare({title:'Synthetic package control 🧪',alphabet:runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),
  pages:[{id:'lp2-15',text:'ᚠᚢ-ᚦᚩ\r\nᚱᚳ'}],steps:[{op:'reverse',unit:'line'},{op:'affine',a:2,b:1},{op:'cumulative-difference',reset:'line'}],criterion:{kind:'measurement'}},webcrypto);
 const address='https://jelliottdev.github.io/run.html#task='+task.taskId,before=structuredClone(task);
 const bytes=await P.build(task,runner,address);assert(bytes instanceof Uint8Array);assert.deepEqual(task,before);
 assert.deepEqual(await P.build(task,runner,address),bytes,'Identical inputs produce byte-identical ZIPs');
 const changing=structuredClone(task),pending=P.build(changing,runner,address);changing.pages[0].text='Changed during identity verification';assert.deepEqual(await pending,bytes,'Caller changes during hashing cannot alter the packaged task');
 const reordered=Object.fromEntries(Object.entries(task).reverse());assert.deepEqual(await P.build(reordered,runner,address),bytes,'Task key order cannot change archive bytes');
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'local-run-package-'));
 try{
  const archive=path.join(folder,'package.zip');fs.writeFileSync(archive,bytes);fs.writeFileSync(path.join(folder,'expected-task.json'),E.stable(task)+'\n');fs.writeFileSync(path.join(folder,'expected-runner.py'),runner);
  const inspect=String.raw`import json,pathlib,sys,tempfile,zipfile
p=pathlib.Path(sys.argv[1]);z=zipfile.ZipFile(p/'package.zip')
assert z.namelist()==['task.json','research_runner.py','START.txt']
assert z.testzip() is None
for m in z.infolist():
 assert m.compress_type==zipfile.ZIP_STORED and m.date_time==(1980,1,1,0,0,0)
 assert m.flag_bits & 0x800 and not m.is_dir()
 assert pathlib.PurePosixPath(m.filename).name==m.filename
assert z.read('task.json')==(p/'expected-task.json').read_bytes()
assert z.read('research_runner.py')==(p/'expected-runner.py').read_bytes()
assert sys.argv[2] in z.read('START.txt').decode('utf-8')
with tempfile.TemporaryDirectory(prefix='extracted-rune-run-') as directory:
 output=pathlib.Path(directory);z.extractall(output)
 import subprocess
 subprocess.run([sys.executable,'research_runner.py','--task','task.json','--out','results.json'],cwd=output,check=True)
 sys.stdout.buffer.write((output/'results.json').read_bytes())
`;
  const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',inspect,folder,address],{encoding:'utf8',maxBuffer:3000000}));
  assert.deepEqual(await E.verify(task,result,webcrypto),E.run(task));
 }finally{fs.rmSync(folder,{recursive:true,force:true});}
 for(const bad of ['https://evil.example/run.html#task='+task.taskId,'https://jelliottdev.github.io.evil.example/run.html#task='+task.taskId,
  'https://user:password@jelliottdev.github.io/run.html#task='+task.taskId,'https://jelliottdev.github.io:444/run.html#task='+task.taskId,
  'https://jelliottdev.github.io/run.html?text=private#task='+task.taskId,'https://jelliottdev.github.io/../run.html#task='+task.taskId,
  'https://jelliottdev.github.io/run.html#task='+'0'.repeat(64),'http://192.168.1.2/run.html#task='+task.taskId,'javascript:alert(1)',null])await assert.rejects(P.build(task,runner,bad));
 for(const origin of ['http://localhost:8765','http://127.0.0.1:8765'])assert(await P.build(task,runner,origin+'/run.html#task='+task.taskId));
 const tampered=structuredClone(task);tampered.pages[0].text+='ᚠ';await assert.rejects(P.build(tampered,runner,address),/changed/);
 await assert.rejects(P.build({...task,unknown:undefined},runner,address),'Unknown fields cannot disappear during JSON snapshotting');
 for(const invalid of ['',null,'x'.repeat(100001),'🧪'.repeat(25001),'\ud800'])await assert.rejects(P.build(task,invalid,address));
 const context={LocalControl:require('../local-control.js'),LocalExperiment:E,TextEncoder,URL,crypto:webcrypto};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'local-run-package.js'),'utf8'),context);
 assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(task,runner,address)),Buffer.from(bytes),'Browser UMD and CommonJS produce identical archives');
 await controlsPackage(context);
 await wordPairPackage(context);
 console.log('PASS local run package: deterministic STORE/CRC/date/UTF8; exact source/task; safe return addresses; Python extraction/run and shared verification; browser parity.');
}
async function controlsPackage(context){
 const guard=fs.readFileSync(path.join(root,'tools/verify_controls.py'),'utf8'),hash=value=>createHash('sha256').update(E.stable(value)).digest('hex');
 assert.equal(createHash('sha256').update(guard).digest('hex'),P.GUARD_SHA256,'Only the fixed reviewed guard is packaged');
 const alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),steps=[{op:'keyed-shift',key:[1,2],mode:'repeat',direction:'subtract',reset:'word'}],criterion={kind:'exact-prefix',values:[0,1]};
 const controlTask=await E.prepare({title:'Synthetic independent known-answer control',alphabet,steps,criterion,pages:[{id:'lp1-01',text:'ᚢᚩ-ᚩᚳ\r\nᚢᚩ'}]},webcrypto);
 const controlResult=E.run(controlTask);assert(controlResult.matches.every(m=>m.matched));
 const task=await E.prepare({title:'Synthetic optional package target',alphabet,steps,criterion,pages:[{id:'lp2-15',text:'ᚢᚩ-ᚢᚩ'}]},webcrypto),address='https://jelliottdev.github.io/run.html#task='+task.taskId;
 const entry={origin:{recordId:'synthetic-record',followupId:'fixed-variant',recordSha256:'a'.repeat(64),protocolSha256:'b'.repeat(64)},control:{label:'Synthetic known-answer control',task:controlTask,expected_result_sha256:hash(controlResult)},question:'Does this fixed beginning match?',scopeChange:'One explicit synthetic variant.',limitation:'A short match is not a reading.'};
 const origins=[entry],before=structuredClone(origins),zip=await P.build(task,runner,address,origins,guard);
 assert.deepEqual(origins,before);assert.deepEqual(await P.build(task,runner,address,origins,guard),zip);
 const changing=structuredClone(origins),pending=P.build(task,runner,address,changing,guard);changing[0].control.task.pages[0].text='edited';changing[0].question='changed';assert.deepEqual(await pending,zip,'Origin and control snapshots precede awaits');
 assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(task,runner,address,origins,guard)),Buffer.from(zip));
 await assert.rejects(P.build(task,runner,address,origins),/guard source/);
 await assert.rejects(P.build(task,runner,address,origins,guard+'\n#changed'),/guard source changed/);
 const different=structuredClone(origins);different[0].control.task.steps[0].reset='page';different[0].control.task.taskId=await E.identity(different[0].control.task);await assert.rejects(P.build(task,runner,address,different,guard),/different steps/);
 const badHash=structuredClone(origins);badHash[0].control.expected_result_sha256='0'.repeat(64);await assert.rejects(P.build(task,runner,address,badHash,guard),/result changed/);
 const failed=structuredClone(origins);failed[0].control.task.pages[0].text='ᚦ'+failed[0].control.task.pages[0].text.slice(1);failed[0].control.task.taskId=await E.identity(failed[0].control.task);failed[0].control.expected_result_sha256=hash(E.run(failed[0].control.task));await assert.rejects(P.build(task,runner,address,failed,guard),/control failed/);
 const extra=structuredClone(origins);extra[0].privateSource=undefined;await assert.rejects(P.build(task,runner,address,extra,guard),/origin fields/);
 await assert.rejects(P.build(task,runner,address,Array(11).fill(entry),guard),/origins/);
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'controlled-package-'));
 try{
  fs.writeFileSync(path.join(directory,'package.zip'),zip);
  // The extracted command verifies controls and then produces the exact target
  // result. Four damaged-package cases must stop before any target invocation.
  const check=String.raw`import copy,hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
p=pathlib.Path(sys.argv[1]);z=zipfile.ZipFile(p/'package.zip')
assert z.namelist()==['task.json','research_runner.py','START.txt','origins.json','verify_controls.py','controls/'+sys.argv[2]+'.json']
assert 'python verify_controls.py --task task.json --origins origins.json --out results.json' in z.read('START.txt').decode()
for mode in ['pass','prefix','digest','program','file']:
 with tempfile.TemporaryDirectory(prefix='extracted-guard-') as folder:
  folder=pathlib.Path(folder);z.extractall(folder)
  sys.path.insert(0,str(folder));import research_runner as r
  document=json.loads((folder/'origins.json').read_text(encoding='utf-8'));c=document['origins'][0]['control'];t=c['task']
  if mode=='prefix':
   t['pages'][0]['text']='ᚦ'+t['pages'][0]['text'][1:];t['taskId']=r.task_identity(t)
  elif mode=='digest':c['expected_result_sha256']='0'*64
  elif mode=='program':t['steps'][0]['reset']='page';t['taskId']=r.task_identity(t)
  if mode in ['prefix','program']:
   (folder/'controls'/ (t['taskId']+'.json')).write_text(json.dumps(t,ensure_ascii=False),encoding='utf-8')
  if mode=='file':
   altered=copy.deepcopy(t);altered['pages'][0]['text']+='ᚠ'
   (folder/'controls'/ (t['taskId']+'.json')).write_text(json.dumps(altered,ensure_ascii=False),encoding='utf-8')
  (folder/'origins.json').write_text(json.dumps(document,ensure_ascii=False),encoding='utf-8')
  # Observe execution order without changing any transformation or result.
  target=json.loads((folder/'task.json').read_text(encoding='utf-8'))
  with (folder/'research_runner.py').open('a',encoding='utf-8') as handle:
   handle.write('\n_original_run = run\ndef run(task):\n if task["taskId"] == '+repr(target['taskId'])+':\n  Path("TARGET_CALLED").write_text("yes")\n return _original_run(task)\n')
  done=subprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','results.json'],cwd=folder,capture_output=True,text=True)
  if mode=='pass':
   assert done.returncode==0,done.stderr
   assert (folder/'TARGET_CALLED').exists()
   assert json.loads((folder/'results.json').read_text(encoding='utf-8'))==r.run(target)
   retry=subprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','results.json'],cwd=folder,capture_output=True)
   assert retry.returncode==2
  else:
   assert done.returncode==2,(mode,done.stdout,done.stderr)
   assert not (folder/'TARGET_CALLED').exists(),mode
   assert not (folder/'results.json').exists(),mode
  sys.path.pop(0);del sys.modules['research_runner']
print('PASS extracted Python guard: complete controls before target; prefix/hash/program/file failures stop target; no overwrite')
`;
  console.log(execFileSync(process.env.PYTHON||'python',['-c',check,directory,controlTask.taskId],{encoding:'utf8',maxBuffer:3000000}).trim());
 }finally{fs.rmSync(directory,{recursive:true,force:true});}
 const second={...structuredClone(entry),origin:{...entry.origin,followupId:'same-computation'}};
 const deduplicated=await P.build(task,runner,address,[entry,second],guard);assert(deduplicated.length>zip.length,'Both public origins survive, even when the control task is shared');
 console.log('PASS authored-origin package: full JS/Python synthetic controls, immutable snapshots, fixed guard, exact protocol/digest, browser parity and bounded origins.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});

async function wordPairPackage(context){
 const recipe=JSON.parse(fs.readFileSync(path.join(root,'experiments/records/word-internal-affine-lags/record.json'),'utf8')).browser_followups[0],control=recipe.control;
 const task=await E.prepare({...control.task,title:'Synthetic word-pair package target',pages:[{id:'lp2-15',text:control.task.pages[0].text+'-'+control.task.pages[0].text}]});
 const entry={origin:{recordId:'synthetic-pairs',followupId:'fixed-boundary',recordSha256:'a'.repeat(64),protocolSha256:'b'.repeat(64)},control,question:'Synthetic fixed-pair count',scopeChange:'Synthetic words only',limitation:'No manuscript result or significance claim'};
 const guard=fs.readFileSync(path.join(root,'tools/verify_controls.py'),'utf8'),address='https://jelliottdev.github.io/run.html#task='+task.taskId,zip=await P.build(task,runner,address,[entry],guard);
 assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(task,runner,address,[entry],guard)),Buffer.from(zip));
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'word-pair-guard-'));fs.writeFileSync(path.join(dir,'run.zip'),zip);
 const code=String.raw`import pathlib,subprocess,sys,tempfile,zipfile
with tempfile.TemporaryDirectory() as d:
 zipfile.ZipFile(pathlib.Path(sys.argv[1])/'run.zip').extractall(d)
 subprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','result.json'],cwd=d,check=True,stdout=subprocess.DEVNULL)
 sys.stdout.buffer.write((pathlib.Path(d)/'result.json').read_bytes())`;
 const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',code,dir],{encoding:'utf8'}));await E.verify(task,result);assert.deepEqual(result.wordPairs,E.run(task).wordPairs);
 const failed=structuredClone(entry);failed.control.task.pages[0].text=task.alphabet[0].rune;failed.control.task.taskId=await E.identity(failed.control.task);failed.control.expected_result_sha256=createHash('sha256').update(E.stable(E.run(failed.control.task))).digest('hex');await assert.rejects(P.build(task,runner,address,[failed],guard),/control failed/);
 console.log('PASS word-pair package: independent Python guard/control and exact fractions reproduce JS; failed or empty control cannot prepare a package');
}
