'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),{execFileSync}=require('node:child_process'),{webcrypto,createHash}=require('node:crypto'),E=require('../local-experiment.js'),P=require('../local-run-package.js'),Checks=require('../local-plan-controls.js'),Control=require('../local-control.js'),Relation=require('../finite-origin-relation.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const read=n=>fs.readFileSync(path.join(__dirname,'../tools',n),'utf8'),runner=read('research_runner.py'),guard=read('verify_controls.py'),options={subsetGuardText:read('verify_subset_controls.py'),planGuardText:read('verify_plan_controls.py'),finiteGuardText:read('verify_finite_search.py')},hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),known=v=>C.field('specified',v,{kind:'supplied',refs:['software:explicit']});
(async()=>{let groups=0;const test=async(name,fn)=>{await fn();groups++;console.log('PASS '+name);},alphabet=require('../data/local-run-inputs.json').alphabet,card=H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic finite family package.'},aim:known('Measure a pattern'),method:known({operations:[{id:'affine',label:'Affine substitution',a:1}]}),scope:known({pages:['lp2-15','lp2-16']}),rules:{representation:known('GP29'),inputVersion:known('raw'),evaluation:known('measurement'),searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'b',values:[1,2]}]})}}),{id:'software',at:'2026-10-25T12:00:00.000Z'})),task=await E.prepare({title:'Synthetic target member',alphabet,pages:[{id:'lp2-15',text:alphabet.slice(0,3).map(v=>v.rune).join('')}],steps:[{op:'affine',a:1,b:2}],criterion:{kind:'measurement'}},webcrypto),control=await E.prepare({...task,title:'Synthetic authored complete witness',pages:[{id:'lp1-01',text:alphabet[3].rune+alphabet[4].rune}],criterion:{kind:'exact-prefix',values:[5,6]}},webcrypto),origin={origin:{recordId:'synthetic-family',followupId:'compare-settings',recordSha256:'1'.repeat(64),protocolSha256:'2'.repeat(64)},control:{label:'Synthetic complete witness',task:control,expected_result_sha256:hash(E.run(control))},question:'What does this exact family produce?',scopeChange:'Two exact shifts on two pages.',limitation:'No decryption claim.',scopeRelation:{kind:'finite-settings-member',card,settings:[{operation:0,name:'b',value:2}],declaredPages:['lp2-15','lp2-16'],remainingPages:['lp2-15']}},suite=await Checks.prepare(task,webcrypto),url='https://jelliottdev.github.io/run.html#task='+task.taskId,build=(entry=origin,opts=options)=>P.build(task,runner,url,[entry],guard,suite,null,opts);let bytes;
await test('finite package validates its source member and pins optional helper without target execution',async()=>{const run=E.run;E.run=t=>{assert.notEqual(t.taskId,task.taskId);return run(t);};try{bytes=await build();assert.deepEqual(await build(),bytes);}finally{E.run=run;}assert.equal(createHash('sha256').update(options.finiteGuardText).digest('hex'),P.FINITE_AUDIT_SHA256);const context=vm.createContext({LocalExperiment:E,LocalControl:Control,LocalPlanControls:Checks,FiniteOriginRelation:Relation,TextEncoder,URL,crypto:webcrypto});vm.runInContext(fs.readFileSync(path.join(__dirname,'../local-run-package.js'),'utf8'),context);assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(task,runner,url,[origin],guard,suite,null,options)),Buffer.from(bytes));});
await test('missing or changed helper and altered card settings scope criterion reject before packaging targets',async()=>{await assert.rejects(build(origin,{subsetGuardText:options.subsetGuardText,planGuardText:options.planGuardText}));await assert.rejects(build(origin,{...options,finiteGuardText:options.finiteGuardText+'\n'}));for(const change of [v=>v.scopeRelation.settings[0].value=28,v=>v.scopeRelation.card.method.value.operations[0].a=2,v=>v.scopeRelation.remainingPages=['lp2-16'],v=>v.scopeRelation.card.rules.evaluation.value={kind:'exact-prefix',values:[2]},v=>v.scopeRelation.card.scope.value.pages=['lp2-15']]){const bad=structuredClone(origin);change(bad);await assert.rejects(build(bad));}});
await test('Python independently binds member card and both suites; damaged helpers never import or run targets',async()=>{const folder=fs.mkdtempSync(path.join(os.tmpdir(),'finite-origin-package-'));try{fs.writeFileSync(path.join(folder,'run.zip'),bytes);const program=String.raw`import json,pathlib,shutil,subprocess,sys,zipfile
root=pathlib.Path(sys.argv[1]);seed=root/'seed';zipfile.ZipFile(root/'run.zip').extractall(seed)
assert (seed/'verify_finite_search.py').exists()
args=['--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','results.json']
good=root/'good';shutil.copytree(seed,good);subprocess.run([sys.executable,'verify_subset_controls.py',*args],cwd=good,check=True,stdout=subprocess.DEVNULL)
wrapper="""import pathlib,json,sys
import research_runner as runner
import verify_subset_controls as guard
target=json.loads(pathlib.Path('task.json').read_text(encoding='utf-8'))['taskId'];original=runner.run
def run(task):
 assert task['taskId']!=target,'Target must not run'
 return original(task)
runner.run=run
sys.argv=['verify_subset_controls.py','--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','results.json']
try:guard.main()
except SystemExit as e:assert e.code==2
else:raise AssertionError('Invalid package accepted')
assert not pathlib.Path('results.json').exists()
assert not pathlib.Path('imported.txt').exists()
"""
for kind in ['settings','card','scope','criterion','missing-helper','changed-helper','authored-suite','runner-suite']:
 bad=root/kind;shutil.copytree(seed,bad);p=bad/'origins.json';document=json.loads(p.read_text(encoding='utf-8'));relation=document['origins'][0]['scopeRelation']
 if kind=='settings':relation['settings'][0]['value']=28
 elif kind=='card':relation['card']['method']['value']['operations'][0]['a']=2
 elif kind=='scope':relation['remainingPages']=['lp2-16']
 elif kind=='criterion':relation['card']['rules']['evaluation']['value']={'kind':'exact-prefix','values':[2]}
 elif kind=='missing-helper':(bad/'verify_finite_search.py').unlink()
 elif kind=='changed-helper':
  helper=bad/'verify_finite_search.py';helper.write_bytes(helper.read_bytes()+b"\npathlib.Path('imported.txt').touch()\n")
 elif kind=='authored-suite':document['origins'][0]['control']['expected_result_sha256']='0'*64
 elif kind=='runner-suite':
  p2=bad/'runner-controls.json';v=json.loads(p2.read_text(encoding='utf-8'));v['cases'][0]['expectedResultSha256']='0'*64;p2.write_text(json.dumps(v))
 p.write_text(json.dumps(document))
 result=subprocess.run([sys.executable,'-c',wrapper],cwd=bad,capture_output=True)
 assert result.returncode==0,(kind,result.stderr.decode())
sys.stdout.buffer.write((good/'results.json').read_bytes())
`;const result=JSON.parse(execFileSync('python',['-c',program,folder],{encoding:'utf8',maxBuffer:2*1024*1024}));assert.deepEqual(await E.verify(task,result,webcrypto),E.run(task));}finally{fs.rmSync(folder,{recursive:true,force:true});}});
await test('actual 42-key family retains unsorted source axes and a 12-rune target with its complete 184-rune witness',async()=>{
 const recipe=JSON.parse(execFileSync('python',['-c',"import sys,json;sys.path.insert(0,'scripts');from test_authored_finite_followups import fixture;print(json.dumps(fixture(),ensure_ascii=True))"],{encoding:'utf8',maxBuffer:2*1024*1024})),member=recipe.control.members[0],criterion={kind:'exact-prefix',values:member.control.task.criterion.values.slice(0,12)},card=structuredClone(recipe.card);card.rules.evaluation={status:'specified',value:criterion};
 assert.equal(recipe.control.members.length,42);assert.deepEqual(card.rules.searchBounds.value.parameters.map(a=>a.name),['key','direction']);assert.equal(member.control.task.criterion.values.length,184);
 const target=await E.prepare({title:'Synthetic 42-family member target',alphabet,pages:[{id:'lp2-00',text:alphabet.slice(0,16).map(r=>r.rune).join('').repeat(4)}],steps:member.control.task.steps,criterion},webcrypto),entry={origin:{recordId:'synthetic-42-family',followupId:recipe.id,recordSha256:'3'.repeat(64),protocolSha256:hash(recipe)},control:member.control,question:recipe.question,scopeChange:recipe.scope_change,limitation:recipe.limitation,scopeRelation:{kind:'finite-settings-member',card,settings:member.settings,declaredPages:card.scope.value.pages,remainingPages:['lp2-00']}},checks=await Checks.prepare(target,webcrypto),url='https://jelliottdev.github.io/run.html#task='+target.taskId;
 await require('../record-followups.js').validateOrigins([entry],target,webcrypto);
 const run=E.run;let zip;E.run=t=>{assert.notEqual(t.taskId,target.taskId);return run(t);};try{zip=await P.build(target,runner,url,[entry],guard,checks,null,options);}finally{E.run=run;}
 const context=vm.createContext({LocalExperiment:E,LocalControl:Control,LocalPlanControls:Checks,TextEncoder,URL,crypto:webcrypto});vm.runInContext(fs.readFileSync(path.join(__dirname,'../local-run-package.js'),'utf8'),context);context.FiniteOriginRelation=Relation;
 assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(target,runner,url,[entry],guard,checks,null,options)),Buffer.from(zip),'Late browser dependency must resolve when building, not when the early script loads');
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'finite-42-prefix-package-'));try{fs.writeFileSync(path.join(folder,'run.zip'),zip);const program=String.raw`import json,pathlib,subprocess,sys,zipfile
root=pathlib.Path(sys.argv[1]);zipfile.ZipFile(root/'run.zip').extractall(root)
task=json.loads((root/'task.json').read_text(encoding='utf-8'));origin=json.loads((root/'origins.json').read_text(encoding='utf-8'))['origins'][0]
assert len(task['criterion']['values'])==12
assert len(origin['control']['task']['criterion']['values'])==184
assert [axis['name'] for axis in origin['scopeRelation']['card']['rules']['searchBounds']['value']['parameters']]==['key','direction']
subprocess.run([sys.executable,'verify_subset_controls.py','--task','task.json','--origins','origins.json','--controls','runner-controls.json','--out','results.json'],cwd=root,check=True,stdout=subprocess.DEVNULL)
sys.stdout.buffer.write((root/'results.json').read_bytes())
`;const result=JSON.parse(execFileSync('python',['-c',program,folder],{encoding:'utf8',maxBuffer:2*1024*1024}));assert.deepEqual(await E.verify(target,result,webcrypto),E.run(target));}finally{fs.rmSync(folder,{recursive:true,force:true});}
 const fixed={...entry};delete fixed.scopeRelation;await assert.rejects(()=>require('../record-followups.js').validateOrigins([fixed],target,webcrypto));
});
console.log(groups+' finite origin package groups passed.');})().catch(e=>{console.error(e);process.exitCode=1;});
