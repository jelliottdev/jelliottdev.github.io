'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),{execFileSync}=require('node:child_process'),{createHash,webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),P=require('../local-run-package.js'),Checks=require('../local-plan-controls.js'),Control=require('../local-control.js');
const text=name=>fs.readFileSync(path.join(__dirname,'../tools',name),'utf8'),runner=text('research_runner.py'),guard=text('verify_controls.py'),planGuardText=text('verify_plan_controls.py'),subsetGuardText=text('verify_subset_controls.py'),hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),copy=structuredClone;
async function main(){let n=0;const test=async(name,fn)=>{await fn();n++;console.log('PASS '+name);};
 const alphabet=require('../data/local-run-inputs.json').alphabet,task=await E.prepare({title:'Synthetic remaining-page package',alphabet,pages:[{id:'lp2-17',text:alphabet[0].rune+'-'+alphabet[1].rune}],steps:[{op:'reverse',unit:'word'}],criterion:{kind:'exact-prefix',values:[28]}},webcrypto),controlTask=await E.prepare({...task,title:'Synthetic authored opening reference',pages:[{id:'lp2-00',text:alphabet[28].rune}]},webcrypto),origin={origin:{recordId:'synthetic-record',followupId:'known-opening',recordSha256:'1'.repeat(64),protocolSha256:'2'.repeat(64)},control:{label:'Synthetic known answer',task:controlTask,expected_result_sha256:hash(E.run(controlTask))},question:'Does this specified opening appear?',scopeChange:'The complete two-page declaration.',limitation:'Only the exact opening is checked.',scopeRelation:{kind:'remaining-pages',declaredPages:['lp2-15','lp2-17'],remainingPages:['lp2-17']}},suite=await Checks.prepare(task,webcrypto),address='https://jelliottdev.github.io/run.html#task='+task.taskId+'&idea=p_'+'a'.repeat(64),options={subsetGuardText,planGuardText};
 const build=(origins=[origin],controls=suite,extra=options,url=address)=>P.build(task,runner,url,origins,guard,controls,null,extra);
 let bytes;
 await test('subset archive pins both guards and suites without running or fabricating target output',async()=>{const original=E.run;E.run=(input,...args)=>{assert.notEqual(input.taskId,task.taskId,'Packaging must never execute target');return original(input,...args);};try{bytes=await build();assert.deepEqual(await build(),bytes);}finally{E.run=original;}assert.equal(createHash('sha256').update(subsetGuardText).digest('hex'),P.SUBSET_GUARD_SHA256);});
 await test('browser UMD produces identical subset archive with the maintained controls and selected context',async()=>{const context=vm.createContext({LocalExperiment:E,LocalControl:Control,LocalPlanControls:Checks,TextEncoder,URL,crypto:webcrypto});vm.runInContext(fs.readFileSync(path.join(__dirname,'../local-run-package.js'),'utf8'),context);assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(task,runner,address,[origin],guard,suite,null,options)),Buffer.from(bytes));});
 await test('generic archive stays byte-identical; each authored archive retains its exact pinned guard',async()=>{const oldSource=execFileSync('git',['show','HEAD:local-run-package.js'],{encoding:'utf8'}),oldGuard=execFileSync('git',['show','HEAD:tools/verify_controls.py'],{encoding:'utf8'}),context=vm.createContext({LocalExperiment:E,LocalControl:Control,LocalPlanControls:Checks,TextEncoder,URL,crypto:webcrypto});vm.runInContext(oldSource,context);const old=context.LocalRunPackage,plain='https://jelliottdev.github.io/run.html#task='+task.taskId,full=copy(origin);delete full.scopeRelation;for(const args of [[task,runner,plain],[task,runner,plain,[],planGuardText,suite]])assert.deepEqual(Buffer.from(await P.build(...args)),Buffer.from(await old.build(...args)));const current=await P.build(task,runner,plain,[full],guard),previous=await old.build(task,runner,plain,[full],oldGuard);function members(bytes){const out=new Map();let offset=0;const b=Buffer.from(bytes);while(b.readUInt32LE(offset)===0x04034b50){const size=b.readUInt32LE(offset+18),length=b.readUInt16LE(offset+26),extra=b.readUInt16LE(offset+28),name=b.subarray(offset+30,offset+30+length).toString('utf8'),start=offset+30+length+extra;out.set(name,b.subarray(start,start+size));offset=start+size;}return out;}const now=members(current),before=members(previous);assert.deepEqual([...now.keys()],[...before.keys()]);for(const [name,bytes]of now)if(name!=='verify_controls.py')assert.deepEqual(bytes,before.get(name),name);assert.deepEqual(now.get('verify_controls.py'),Buffer.from(guard));assert.deepEqual(before.get('verify_controls.py'),Buffer.from(oldGuard));assert.equal(createHash('sha256').update(now.get('verify_controls.py')).digest('hex'),P.GUARD_SHA256);assert.equal(createHash('sha256').update(before.get('verify_controls.py')).digest('hex'),old.GUARD_SHA256);});
 await test('closed scope guard options hashes and selected return addresses reject tampering',async()=>{for(const change of [v=>v.scopeRelation.kind='full',v=>v.scopeRelation.declaredPages=['lp2-17'],v=>v.scopeRelation.remainingPages=['lp2-15'],v=>v.scopeRelation.extra=true,v=>v.scopeRelation.declaredPages.reverse(),v=>v.scopeRelation.declaredPages.push('lp2-99')]){const bad=copy(origin);change(bad);await assert.rejects(build([bad]));}await assert.rejects(build([origin],null));await assert.rejects(build([origin],suite,null));await assert.rejects(build([origin],suite,{...options,subsetGuardText:subsetGuardText+'\n'}));await assert.rejects(build([origin],suite,{...options,planGuardText:planGuardText+'\n'}));for(const bad of [address+'&extra=1',address.replace('&idea=','&idea=%70_'),address.replace(/p_a+$/,'bad'),address+'&idea=p_'+'b'.repeat(64)])await assert.rejects(build([origin],suite,options,bad));});
 await test('detached ZIP runs both suites before target; malformed or missing suites never execute target',async()=>{const folder=fs.mkdtempSync(path.join(os.tmpdir(),'subset-controls-package-'));try{fs.writeFileSync(path.join(folder,'run.zip'),bytes);const code=String.raw`import json,pathlib,subprocess,sys,tempfile,zipfile,shutil
root=pathlib.Path(sys.argv[1]);archive=zipfile.ZipFile(root/'run.zip')
assert archive.testzip() is None
for name in ['verify_subset_controls.py','verify_controls.py','verify_plan_controls.py','runner-controls.json','origins.json']:
 assert name in archive.namelist()
assert '--controls runner-controls.json' in archive.read('START.txt').decode('utf-8')
seed=root/'seed';archive.extractall(seed)
valid=root/'valid';shutil.copytree(seed,valid)
args=['--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','result.json']
subprocess.run([sys.executable,'verify_subset_controls.py',*args],cwd=valid,check=True,stdout=subprocess.DEVNULL)
before=(valid/'result.json').read_bytes()
again=subprocess.run([sys.executable,'verify_subset_controls.py',*args],cwd=valid,capture_output=True)
assert again.returncode!=0 and (valid/'result.json').read_bytes()==before
wrapper="""import json,sys,pathlib
import research_runner as runner
import verify_subset_controls as guard
target=json.loads(pathlib.Path('task.json').read_text(encoding='utf-8'))['taskId'];calls=[];original=runner.run
def run(task):
 calls.append(task['taskId'])
 assert task['taskId']!=target,'Target executed before failed controls'
 return original(task)
runner.run=run
sys.argv=['verify_subset_controls.py','--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','result.json']
try:guard.main()
except SystemExit as error:
 assert error.code==2 and target not in calls and not pathlib.Path('result.json').exists()
else:raise AssertionError('Corrupt package accepted')
"""
for kind in ['generic-hash','authored-hash','relation','no-relation','missing-generic','missing-authored-control','collision']:
 bad=root/kind;shutil.copytree(seed,bad)
 if kind=='generic-hash':
  p=bad/'runner-controls.json';v=json.loads(p.read_text(encoding='utf-8'));v['cases'][0]['expectedResultSha256']='0'*64;p.write_text(json.dumps(v),encoding='utf-8')
 elif kind=='authored-hash':
  p=bad/'origins.json';v=json.loads(p.read_text(encoding='utf-8'));v['origins'][0]['control']['expected_result_sha256']='0'*64;p.write_text(json.dumps(v),encoding='utf-8')
 elif kind in ('relation','no-relation'):
  p=bad/'origins.json';v=json.loads(p.read_text(encoding='utf-8'))
  if kind=='relation':v['origins'][0]['scopeRelation']['remainingPages']=['lp2-15']
  else:del v['origins'][0]['scopeRelation']
  p.write_text(json.dumps(v),encoding='utf-8')
 elif kind=='missing-generic':(bad/'runner-controls.json').unlink()
 elif kind=='missing-authored-control':next((bad/'controls').glob('*.json')).unlink()
 elif kind=='collision':
  trial=subprocess.run([sys.executable,'verify_subset_controls.py',*args[:-1],'task.json'],cwd=bad,capture_output=True)
  assert trial.returncode!=0;continue
 outcome=subprocess.run([sys.executable,'-c',wrapper],cwd=bad,capture_output=True)
 assert outcome.returncode==0,(kind,outcome.stderr.decode())
sys.stdout.buffer.write(before)
`;const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',code,folder],{encoding:'utf8',maxBuffer:3000000}));assert.deepEqual(await E.verify(task,result,webcrypto),E.run(task));}finally{fs.rmSync(folder,{recursive:true,force:true});}});
 console.log(n+' remaining-page control package groups passed; no hosted calls');}
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1;});
