/* Actual saved-search archive extracted and audited with Python's standard library. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{execFileSync}=require('node:child_process'),{createHash}=require('node:crypto');
const C=require('../claim-specification.js'),H=require('../claim-share.js'),E=require('../local-experiment.js'),F=require('../finite-search-compiler.js'),Q=require('../finite-program-question.js'),S=require('../finite-search-snapshot.js'),P=require('../local-run-package.js');
const hash=(v,serialize=E.stable)=>createHash('sha256').update(serialize(v)).digest('hex'),known=v=>C.field('specified',v),at='2026-10-25T12:00:00.000Z';
(async()=>{
 const card=H.cardData(C.confirm(C.createDraft({source:{text:'Explicit saved-search reproduction fixture'},aim:known('Solve LP2'),method:known({operations:[{id:'affine',b:0}]}),scope:known({pages:['lp2-15']}),rules:{inputVersion:known('raw'),evaluation:known({kind:'exact-prefix',values:[28,28]}),searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'a',values:[1,2]}]})}}),{id:'fixture',at})),bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8'));bundle.pages.find(p=>p.id==='lp2-15').raw='ᚠᚢᚦᚩ';
 const {domain}=await F.compile(card,bundle),task=domain.programs[0].task,result=E.run(task),sources=[{task,inputVersion:'raw',run:{id:hash(result),createdAt:at,result}}],proof=await Q.summarize(domain,sources,{lookupComplete:false}),snapshot=await S.build({proposalId:'p_'+hash(card,C.serialize),card,bundle,domain,proof,sources}),runner=fs.readFileSync('tools/research_runner.py','utf8'),audit=fs.readFileSync('tools/verify_finite_search.py','utf8');
 assert.equal(createHash('sha256').update(runner).digest('hex'),P.FINITE_RUNNER_SHA256);assert.equal(createHash('sha256').update(audit).digest('hex'),P.FINITE_AUDIT_SHA256);
 const archive=await P.buildSnapshot(snapshot,runner,audit);assert.deepEqual(archive,await P.buildSnapshot(snapshot,runner,audit));
 await assert.rejects(()=>P.buildSnapshot(JSON.parse(JSON.stringify(snapshot)),runner,audit),/verified.*snapshot/);await assert.rejects(()=>P.buildSnapshot(snapshot,runner,audit+'\n'),/audit source changed/);await assert.rejects(()=>P.buildSnapshot(snapshot,runner+'\n',audit),/runner source changed/);
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'liberpedia-search-package-'));
 try{
  const filename=path.join(folder,'search.zip');fs.writeFileSync(filename,archive);
  const code=`import json, pathlib, subprocess, sys, zipfile
root=pathlib.Path(sys.argv[1]); archive=root/'search.zip'
with zipfile.ZipFile(archive) as z:
 assert z.namelist()==['snapshot.json','research_runner.py','verify_finite_search.py','START.txt']
 assert z.testzip() is None
 z.extractall(root/'extracted')
folder=root/'extracted'
assert 'python verify_finite_search.py snapshot.json' in (folder/'START.txt').read_text()
p=subprocess.run([sys.executable,'verify_finite_search.py','snapshot.json'],cwd=folder,capture_output=True,text=True,encoding='utf-8')
assert p.returncode==0,p.stderr
out=json.loads(p.stdout)
assert out['finding']=='incomplete' and out['coveredCases']==1 and out['missingCases']==1 and out['replayedSources']==1
assert out['recordedLookupComplete'] is False
assert sorted(f.name for f in folder.iterdir() if f.is_file())==['START.txt','research_runner.py','snapshot.json','verify_finite_search.py']
print(json.dumps(out))`;
  const output=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',code,folder],{encoding:'utf8'}));assert.equal(output.snapshotId,snapshot.snapshotId);assert.equal(output.domainId,domain.id);
 }finally{const resolved=path.resolve(folder);assert.equal(path.dirname(resolved),path.resolve(os.tmpdir()));assert(path.basename(resolved).startsWith('liberpedia-search-package-'));fs.rmSync(resolved,{recursive:true,force:true});}
 console.log('PASS deterministic saved-search ZIP: branded proof, pinned sources, exact four members, independent Python audit, partial coverage and no missing-case execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
