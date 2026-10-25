'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {execFileSync}=require('node:child_process'),{webcrypto,createHash}=require('node:crypto');
const E=require('../local-experiment.js'),S=require('../language-score.js'),D=require('../output-evaluators.js'),Evidence=require('../computation-evidence.js'),Package=require('../local-run-package.js'),Controls=require('../local-plan-controls.js');
const alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet;
const digest=value=>createHash('sha256').update(E.stable(value)).digest('hex');
const copy=value=>JSON.parse(JSON.stringify(value));
(async()=>{
 assert.deepEqual(D.criterion(),S.criterion());assert(D.identify(S.criterion()));assert.equal(D.describe({kind:'readability'}),null);assert.equal(D.describe({kind:'measurement'}),null);
 for(const altered of [{...D.criterion(),extra:true},{...D.criterion(),modelSha256:'0'.repeat(64)},{...D.criterion(),modelId:'arbitrary-url'}])assert(!D.identify(altered));
 const description=D.describe(D.criterion());description.question='changed';assert.notEqual(D.describe(D.criterion()).question,'changed');
 const task=await E.prepare({title:'Synthetic diagnostic integration',alphabet,pages:[{id:'lp2-15',text:Array.from({length:80},(_,i)=>alphabet[(i*i+7*i)%29].rune).join('')}],steps:[{op:'reverse',unit:'page'}],criterion:D.criterion()},webcrypto);
 const result=E.run(task),source={task,inputVersion:'raw',run:{id:digest(result),createdAt:'2026-10-25T12:00:00.000Z',result}};
 const renamed=await E.prepare({...task,title:'A different aim and category'},webcrypto);
 const oldRun=E.run;E.run=()=>{throw Error('Evidence discovery must not repeat the transformation.');};
 try{const reuse=await Evidence.compare(renamed,'raw',[source],webcrypto);assert.deepEqual(reuse.remainingPages,[]);assert.equal(reuse.exactTaskId,task.taskId);}finally{E.run=oldRun;}
 for(const mutate of [r=>r.languageScore.pages[0].models[0].total++,r=>r.languageScore.pages[0].models.reverse(),r=>r.languageScore.modelSha256='0'.repeat(64),r=>r.languageScore.pages[0].status='passed',r=>r.languageScore.pages[0].models[0].probability=.99]){
  const bad=copy(source);mutate(bad.run.result);bad.run.id=digest(bad.run.result);await assert.rejects(Evidence.compare(renamed,'raw',[bad],webcrypto));
 }
 const runner=fs.readFileSync('tools/research_runner.py','utf8'),model=fs.readFileSync('tools/language-model.json','utf8'),guard=fs.readFileSync('tools/verify_plan_controls.py','utf8'),address='https://jelliottdev.github.io/run.html#task='+task.taskId;
 const controls=await Controls.prepare(task,webcrypto);
 const zip=await Package.build(task,runner,address,[],guard,controls,model);
 assert.deepEqual(await Package.build(task,runner,address,[],guard,controls,model),zip);
 await assert.rejects(Package.build(task,runner,address,[],guard,controls));
 const badModel=JSON.parse(model);badModel.payload.models[0].scores[0]--;await assert.rejects(Package.build(task,runner,address,[],guard,controls,JSON.stringify(badModel)),/changed/);
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'language-package-'));
 try{
  fs.writeFileSync(path.join(folder,'package.zip'),zip);
  const program=String.raw`import json,pathlib,subprocess,sys,zipfile
p=pathlib.Path(sys.argv[1])
with zipfile.ZipFile(p/'package.zip') as z:
 assert 'language-model.json' in z.namelist()
 assert z.testzip() is None
 z.extractall(p)
subprocess.run([sys.executable,'verify_plan_controls.py','--task','task.json','--controls','runner-controls.json','--out','results.json'],cwd=p,check=True,stdout=subprocess.PIPE)
sys.stdout.buffer.write((p/'results.json').read_bytes())
`;
  const actual=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',program,folder],{encoding:'utf8',maxBuffer:3000000}));assert.deepEqual(actual,result);
 }finally{fs.rmSync(folder,{recursive:true,force:true});}
 console.log('PASS diagnostic declaration, cross-card reuse without decoding, forged score rejection, exact model package and independent offline Python controls/result');
})().catch(error=>{console.error(error);process.exitCode=1;});
