'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{execFileSync}=require('node:child_process'),{createHash,webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),P=require('../local-run-package.js'),Checks=require('../local-plan-controls.js'),S=require('../language-score.js');
const read=n=>fs.readFileSync(path.join(__dirname,'../tools',n),'utf8'),hash=v=>createHash('sha256').update(E.stable(v)).digest('hex');
(async()=>{
const alphabet=require('../data/local-run-inputs.json').alphabet,steps=[{op:'keyed-shift',mode:'repeat',direction:'subtract',reset:'word',key:[3,1,4]}],text=Array.from({length:75},(_,i)=>alphabet[i%29].rune).join(''),task=await E.prepare({title:'Synthetic authored language package target',alphabet,steps,pages:[{id:'lp2-15',text}],criterion:S.criterion()},webcrypto),witness=await E.prepare({title:'Synthetic complete transform witness',alphabet,steps,pages:[{id:'lp1-00',text:alphabet[5].rune+alphabet[7].rune}],criterion:{kind:'exact-prefix',values:[2,6]}},webcrypto),origin={origin:{recordId:'synthetic-record',followupId:'language-check',recordSha256:'1'.repeat(64),protocolSha256:'2'.repeat(64)},control:{label:'Synthetic exact transform witness',task:witness,expected_result_sha256:hash(E.run(witness))},question:'Compare this exact output with maintained samples.',scopeChange:'One declared synthetic test page.',limitation:'Scores do not establish a decryption.'},suite=await Checks.prepare(task,webcrypto),options={authoredLanguageGuardText:read('verify_authored_language.py'),planGuardText:read('verify_plan_controls.py')},address='https://jelliottdev.github.io/run.html#task='+task.taskId;
const build=(controls=suite,model=read('language-model.json'),extra=options,origins=[origin],subset=null)=>P.build(task,read('research_runner.py'),address,origins,read('verify_controls.py'),controls,model,subset,extra);
let bytes;const original=E.run;E.run=(t,...a)=>{assert.notEqual(t.taskId,task.taskId,'Packaging must not execute manuscript target');return original(t,...a);};try{bytes=await build();assert.deepEqual(await build(),bytes);}finally{E.run=original;}
for(const args of [[null],[suite,null],[suite,read('language-model.json'),null],[suite,read('language-model.json'),{...options,authoredLanguageGuardText:options.authoredLanguageGuardText+'\n'}]])await assert.rejects(build(...args));
const short=await E.prepare({...witness,criterion:{kind:'exact-prefix',values:[2]}},webcrypto),bad=structuredClone(origin);bad.control={...bad.control,task:short,expected_result_sha256:hash(E.run(short))};await assert.rejects(build(suite,read('language-model.json'),options,[bad]));
console.log('PASS deterministic package requires full transform witness, scorer suite and exact fixed guards/model without target execution');
const folder=fs.mkdtempSync(path.join(os.tmpdir(),'authored-language-package-'));try{fs.writeFileSync(path.join(folder,'run.zip'),bytes);const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',String.raw`import json,pathlib,subprocess,sys,zipfile,shutil
root=pathlib.Path(sys.argv[1]);archive=zipfile.ZipFile(root/'run.zip');seed=root/'seed';archive.extractall(seed)
assert 'language-model.json' in archive.namelist()
args=['--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','result.json']
valid=root/'valid';shutil.copytree(seed,valid);subprocess.run([sys.executable,'verify_authored_language.py',*args],cwd=valid,check=True,stdout=subprocess.DEVNULL)
before=(valid/'result.json').read_bytes();direct=subprocess.run([sys.executable,'verify_controls.py','--task','task.json','--origins','origins.json','--out','bypassed.json'],cwd=valid,capture_output=True);assert direct.returncode!=0 and not (valid/'bypassed.json').exists()
again=subprocess.run([sys.executable,'verify_authored_language.py',*args],cwd=valid,capture_output=True);assert again.returncode!=0 and (valid/'result.json').read_bytes()==before
wrapper="""import json,pathlib,sys
import research_runner as runner
import verify_authored_language as guard
target=json.loads(pathlib.Path('task.json').read_text(encoding='utf-8'))['taskId'];original=runner.run
runner.run=lambda task: (_ for _ in ()).throw(AssertionError('Target ran before failed guards')) if task['taskId']==target else original(task)
sys.argv=['guard','--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','result.json']
try:guard.main()
except SystemExit as error:assert error.code==2 and not pathlib.Path('result.json').exists()
else:raise AssertionError('Malformed package accepted')
"""
for kind in ['scorer-hash','authored-hash','missing-suite','missing-model','model-tamper','missing-witness']:
 bad=root/kind;shutil.copytree(seed,bad)
 if kind=='scorer-hash':
  p=bad/'runner-controls.json';v=json.loads(p.read_text(encoding='utf-8'));v['cases'][0]['expectedResultSha256']='0'*64;p.write_text(json.dumps(v),encoding='utf-8')
 elif kind=='authored-hash':
  p=bad/'origins.json';v=json.loads(p.read_text(encoding='utf-8'));v['origins'][0]['control']['expected_result_sha256']='0'*64;p.write_text(json.dumps(v),encoding='utf-8')
 elif kind=='missing-suite':(bad/'runner-controls.json').unlink()
 elif kind=='missing-model':(bad/'language-model.json').unlink()
 elif kind=='missing-witness':next((bad/'controls').glob('*.json')).unlink()
 else:
  p=bad/'language-model.json';v=json.loads(p.read_text(encoding='utf-8'));v['sha256']='0'*64;p.write_text(json.dumps(v),encoding='utf-8')
 outcome=subprocess.run([sys.executable,'-c',wrapper],cwd=bad,capture_output=True);assert outcome.returncode==0,(kind,outcome.stderr.decode())
sys.stdout.buffer.write(before)
`,folder],{encoding:'utf8',maxBuffer:3000000}));assert.deepEqual(await E.verify(task,result,webcrypto),E.run(task));console.log('PASS offline Python parity; both suites before target; missing or corrupt suites, witness and model fail closed; overwrite refused');}finally{fs.rmSync(folder,{recursive:true,force:true});}
const subset=structuredClone(origin);subset.scopeRelation={kind:'remaining-pages',declaredPages:['lp2-15','lp2-16'],remainingPages:['lp2-15']};const subsetBytes=await build(suite,read('language-model.json'),null,[subset],{subsetGuardText:read('verify_subset_controls.py'),planGuardText:read('verify_plan_controls.py')});const subsetFolder=fs.mkdtempSync(path.join(os.tmpdir(),'authored-language-subset-'));try{fs.writeFileSync(path.join(subsetFolder,'run.zip'),subsetBytes);const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',String.raw`import pathlib,subprocess,sys,zipfile
folder=pathlib.Path(sys.argv[1]);zipfile.ZipFile(folder/'run.zip').extractall(folder)
subprocess.run([sys.executable,'verify_subset_controls.py','--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','result.json'],cwd=folder,check=True,stdout=subprocess.DEVNULL)
sys.stdout.buffer.write((folder/'result.json').read_bytes())
`,subsetFolder],{encoding:'utf8',maxBuffer:3000000}));assert.deepEqual(result,E.run(task));}finally{fs.rmSync(subsetFolder,{recursive:true,force:true});}console.log('PASS detached remaining-page authored language archive replays both suites and model with Python/JS parity');
})().catch(e=>{console.error(e);process.exitCode=1;});
