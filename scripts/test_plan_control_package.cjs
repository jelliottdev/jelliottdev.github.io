'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process'),{webcrypto,createHash}=require('node:crypto');
const E=require('../local-experiment.js'),Checks=require('../local-plan-controls.js'),P=require('../local-run-package.js');
const root=path.resolve(__dirname,'..'),runner=fs.readFileSync(path.join(root,'tools/research_runner.py'),'utf8'),guard=fs.readFileSync(path.join(root,'tools/verify_plan_controls.py'),'utf8');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'),alphabet=runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
const python=String.raw`
import copy,importlib.util,json,pathlib,subprocess,sys,tempfile,zipfile
p=pathlib.Path(sys.argv[1]);z=zipfile.ZipFile(p/'package.zip')
assert z.namelist()==['task.json','research_runner.py','START.txt','runner-controls.json','verify_plan_controls.py']
assert z.testzip() is None
assert b'verify_plan_controls.py --task task.json --controls runner-controls.json --out results.json' in z.read('START.txt')
with tempfile.TemporaryDirectory(prefix='extracted-plan-controls-') as directory:
 folder=pathlib.Path(directory);z.extractall(folder)
 subprocess.run([sys.executable,'verify_plan_controls.py','--task','task.json','--controls','runner-controls.json','--out','results.json'],cwd=folder,check=True,stdout=subprocess.PIPE)
 actual=json.loads((folder/'results.json').read_text(encoding='utf-8'))
 assert actual==json.loads((p/'expected.json').read_text(encoding='utf-8'))
 repeat=subprocess.run([sys.executable,'verify_plan_controls.py','--task','task.json','--controls','runner-controls.json','--out','results.json'],cwd=folder,capture_output=True)
 assert repeat.returncode!=0 and b'Output already exists' in repeat.stderr
 sys.path.insert(0,str(folder));import verify_plan_controls as g
 task=json.loads((folder/'task.json').read_text(encoding='utf-8'));suite=json.loads((folder/'runner-controls.json').read_text(encoding='utf-8'))
 assert g.verified_controls(task,suite)==2
 bads=[]
 for key,value in [('targetId','0'*64),('version',2),('cases',suite['cases'][:1])]:
  bad=copy.deepcopy(suite);bad[key]=value;bads.append(bad)
 bad=copy.deepcopy(suite);bad['cases'][0]['expectedResultSha256']='0'*64;bads.append(bad)
 bad=copy.deepcopy(suite);bad['cases'][1]=bad['cases'][0];bads.append(bad)
 bad=copy.deepcopy(suite);bad['cases'][0]['task']['steps'].append({'op':'affine','a':1,'b':1});bad['cases'][0]['task']['taskId']=g.runner.task_identity(bad['cases'][0]['task']);bads.append(bad)
 bad=copy.deepcopy(suite);bad['cases'][0]['unexpected']=True;bads.append(bad)
 for bad in bads:
  (folder/'runner-controls.json').write_text(json.dumps(bad,ensure_ascii=False),encoding='utf-8')
  result=subprocess.run([sys.executable,'verify_plan_controls.py','--task','task.json','--controls','runner-controls.json','--out','failed.json'],cwd=folder,capture_output=True)
  assert result.returncode!=0 and not (folder/'failed.json').exists(),result.stdout
 # Failures must stop before the target evaluator is called, not only suppress its file.
 calls=[];original=g.runner.run
 def tracking(value):
  calls.append(value['taskId']);return original(value)
 g.runner.run=tracking
 bad=copy.deepcopy(suite);bad['cases'][1]['expectedResultSha256']='0'*64
 try:g.verified_controls(task,bad);raise AssertionError('Corrupted check accepted')
 except ValueError:pass
 assert task['taskId'] not in calls
print('PASS independent Python control replay, target parity, failure-before-target, metadata tampering and no overwrite')
`;
async function main(){
 assert.equal(createHash('sha256').update(guard).digest('hex'),P.PLAN_GUARD_SHA256);
 const cases=[
  {steps:[{op:'reverse',unit:'word'},{op:'affine',a:0,b:7},{op:'cumulative-difference',reset:'line'}],criterion:{kind:'measurement'}},
  {steps:[{op:'keyed-shift',key:[1,2,3],direction:'subtract',mode:'plaintext-autokey',reset:'word'}],criterion:{kind:'exact-prefix',values:[0,1]}},
  {steps:[{op:'finite-shift',key:[4],direction:'add',reset:'page'}],criterion:{kind:'measurement'},text:runes[0]},
  {steps:[],criterion:{kind:'word-affine-count',lag:12,a:27,b:24,boundaries:'non-rune'}},
  {steps:[],criterion:{kind:'word-prime-sums',table:'reversed',boundaries:'hyphen-period'}},
  {steps:[{op:'keyed-shift',key:Array.from({length:256},(_,i)=>i%29),direction:'add',mode:'ciphertext-autokey',reset:'page'}],criterion:{kind:'measurement'}}
 ];
 const browser={LocalExperiment:E,LocalControl:require('../local-control.js'),LocalPlanControls:Checks,crypto:webcrypto,TextEncoder,URL};vm.createContext(browser);vm.runInContext(fs.readFileSync(path.join(root,'local-run-package.js'),'utf8'),browser);
 for(const [i,entry] of cases.entries()){
  const task=await E.prepare({title:'Synthetic package target '+i,alphabet,pages:[{id:'lp2-15',text:entry.text||runes.slice(0,8).join('')+'-ᚠ\nᚢ'}],steps:entry.steps,criterion:entry.criterion},webcrypto);
  const suite=await Checks.prepare(task,webcrypto),address='https://jelliottdev.github.io/run.html#task='+task.taskId;
  const bytes=await P.build(task,runner,address,[],guard,suite);assert.deepEqual(await P.build(task,runner,address,[],guard,suite),bytes);
  assert.deepEqual(Buffer.from(await browser.LocalRunPackage.build(task,runner,address,[],guard,suite)),Buffer.from(bytes));
  const mutable=structuredClone(suite),pending=P.build(task,runner,address,[],guard,mutable);mutable.cases[0].task.pages[0].text='later edit';assert.deepEqual(await pending,bytes,'Controls are snapshotted before awaiting');
  for(const alter of [v=>v.targetId='0'.repeat(64),v=>v.cases[0].expectedResultSha256='0'.repeat(64),v=>v.cases[0].task.unknown=undefined]){const bad=structuredClone(suite);alter(bad);await assert.rejects(P.build(task,runner,address,[],guard,bad));}
  await assert.rejects(P.build(task,runner,address,[],guard+'\n#changed',suite),/guard source changed/);
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),'plan-control-package-'));
  try{fs.writeFileSync(path.join(folder,'package.zip'),bytes);fs.writeFileSync(path.join(folder,'expected.json'),JSON.stringify(E.run(task)));process.stdout.write(execFileSync(process.env.PYTHON||'python',['-c',python,folder],{encoding:'utf8',maxBuffer:3000000}));}
  finally{fs.rmSync(folder,{recursive:true,force:true});}
 }
 console.log('PASS six generic packages: exact checks and browser/Python outputs; old three-file packages remain covered separately.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
