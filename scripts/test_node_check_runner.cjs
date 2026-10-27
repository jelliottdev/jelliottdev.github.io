'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {validateManifest,runChecks}=require('./run_node_checks.cjs');
const root=path.resolve(__dirname,'..');let count=0;
// Frozen migration snapshot, not a cap on future checks appended to the manifest.
const MIGRATION={count:277,sha256:'f12844a7c83c9a0e005c4365806df38c50af1483c40f2a517be805a35bcf8d40'};
async function test(name,fn){await fn();count++;console.log('PASS '+name);}
(async()=>{
 await test('migration retains every exact original command and flag; runner tests occur exactly once',()=>{
  const manifest=validateManifest(JSON.parse(fs.readFileSync(path.join(__dirname,'node-checks.json'),'utf8')));
  assert.deepEqual(manifest.migration,MIGRATION);
  const original=manifest.checks.slice(0,manifest.migration.count).map(c=>c.args);
  assert.equal(crypto.createHash('sha256').update(JSON.stringify(original)).digest('hex'),manifest.migration.sha256);
  assert.equal(manifest.checks.filter(c=>c.args.includes('scripts/test_node_check_runner.cjs')).length,1);
  assert(original.some(args=>args.includes('scripts/test_protocol_example_view.cjs')));
  assert(original.some(args=>args[0]==='--experimental-sqlite'));
  const workflow=fs.readFileSync(path.join(root,'.github/workflows/validate-experiments.yml'),'utf8').replace(/\r\n/g,'\n');
  const blocks=workflow.split(/(?=^      - )/m),batch=blocks.filter(b=>b.includes('run: node scripts/run_node_checks.cjs'));
  assert.equal(batch.length,1);assert(!/^        if:/m.test(batch[0]));
  assert(workflow.indexOf('run: node scripts/run_node_checks.cjs')<workflow.indexOf('run: python scripts/test_finite_search_audit.py'));
  assert(workflow.indexOf('name: Check current and retained authored source revisions')<workflow.indexOf('run: node scripts/run_node_checks.cjs'));
  assert(workflow.includes('id: scope\n        run: node scripts/ci_validation_scope.cjs'));
 });
 await test('manifest rejects duplicate malformed commands flags timeouts and resource declarations',()=>{
  const first=['scripts/test_example.cjs'],digest=crypto.createHash('sha256').update(JSON.stringify([first])).digest('hex');
  const good={schema:'liberpedia-node-checks-v1',migration:{count:1,sha256:digest},checks:[{args:first}]};validateManifest(good);
  for(const change of [v=>v.checks.push(v.checks[0]),v=>v.checks=[],v=>v.checks[0].args=['--eval','bad'],v=>v.checks[0].args=['scripts/../bad.cjs'],v=>v.checks[0].args=['scripts/x.cjs','--extra'],v=>v.checks[0].timeoutMs=0,v=>v.checks[0].timeoutMs=600001,v=>v.checks[0].resources=['same','same'],v=>v.checks[0].unknown=true,v=>v.schema='other',v=>v.migration.count=2]){const bad=structuredClone(good);change(bad);assert.throws(()=>validateManifest(bad));}
 });
 await test('migration drift fails before scheduling while appended checks preserve the frozen prefix',()=>{
  const first=['scripts/test_example.cjs'],sha256=crypto.createHash('sha256').update(JSON.stringify([first])).digest('hex');
  const fixture={schema:'liberpedia-node-checks-v1',migration:{count:1,sha256},checks:[{args:first}]};
  const appended=structuredClone(fixture);appended.checks.push({args:['scripts/test_new_example.cjs']});assert.equal(validateManifest(appended),appended);
  for(const edit of [v=>v.checks.unshift({args:['scripts/test_new_example.cjs']}),v=>v.checks[0].args=['scripts/test_replacement.cjs'],v=>v.migration.sha256='0'.repeat(64)]){
   const changed=structuredClone(fixture);edit(changed);assert.throws(()=>validateManifest(changed),/Original Node checks changed/);
  }
 });
 const tempRoot=fs.realpathSync(os.tmpdir()),folder=fs.mkdtempSync(path.join(tempRoot,'liberpedia-runner-test-'));
 try{
  const script=path.join(folder,'child.cjs');fs.writeFileSync(script,`const fs=require('node:fs'),os=require('node:os');const start=Date.now();globalThis.privateState=process.pid;setTimeout(()=>{console.log(JSON.stringify({start,end:Date.now(),pid:process.pid,tmp:os.tmpdir(),state:globalThis.privateState,label:process.argv[2]}));console.error('stderr '+process.argv[2]);process.exitCode=Number(process.argv[4]||0);},Number(process.argv[3]||120));`);
  const check=(label,delay=120,exit=0,resources=[])=>({args:[script,label,String(delay),String(exit)],resources});
  const data=r=>JSON.parse(r.output.split('\n').find(line=>line.startsWith('{')));
  await test('four separate processes bound parallelism and isolate logs temporary files and globals',async()=>{
   const checks=Array.from({length:9},(_,i)=>check('job-'+i)),seen=[];
   const results=await runChecks(checks,{workers:4,onResult:r=>seen.push(r.index)});assert.equal(seen.length,9);assert(results.every(r=>r.passed));
   const rows=results.map(data);assert.equal(new Set(rows.map(r=>r.pid)).size,9);assert.equal(new Set(rows.map(r=>r.tmp)).size,9);
   for(const [i,row]of rows.entries()){assert.equal(row.state,row.pid);assert.equal(row.label,'job-'+i);assert(results[i].output.includes('stderr job-'+i));assert(!fs.existsSync(row.tmp));}
   const events=rows.flatMap(r=>[[r.start,1],[r.end,-1]]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);let active=0,maximum=0;for(const [,change]of events){active+=change;maximum=Math.max(maximum,active);}assert(maximum>1);assert(maximum<=4);
  });
  await test('failed command and timeout do not prevent remaining commands; errors remain attributable',async()=>{
   const hanging=path.join(folder,'hang.cjs');fs.writeFileSync(hanging,'setInterval(()=>{},1000);');
   const results=await runChecks([check('fails',20,7),{args:[hanging],timeoutMs:80},check('after-failure',20)],{workers:1});
   assert.equal(results[0].code,7);assert.equal(results[0].passed,false);assert.equal(results[1].timedOut,true);assert.equal(results[1].passed,false);assert(results[1].elapsedMs<5000);assert.equal(results[2].passed,true);assert(data(results[2]).label==='after-failure');
  });
  await test('spawn errors complete every check and do not report success',async()=>{
   const results=await runChecks([check('one'),check('two')],{executable:path.join(folder,'missing-node-executable'),workers:2});assert.equal(results.length,2);assert(results.every(r=>!r.passed&&r.error));
  });
  await test('shared resource locks serialize conflicting checks while unrelated work overlaps',async()=>{
   const rows=(await runChecks([check('locked-a',200,0,['fixture']),check('locked-b',40,0,['fixture']),check('free',100)],{workers:3})).map(data);
   assert(rows[1].start>=rows[0].end);assert(rows[2].start<rows[0].end);assert(rows[2].end>rows[0].start);
   await assert.rejects(runChecks([],{workers:0}));await assert.rejects(runChecks([],{timeoutMs:0}));
  });
 }finally{
  const target=fs.realpathSync(folder),relative=path.relative(tempRoot,target);
  assert(relative&&!path.isAbsolute(relative)&&!relative.split(path.sep).includes('..'));
  assert.equal(path.dirname(target),tempRoot);assert(path.basename(target).startsWith('liberpedia-runner-test-'));
  fs.rmSync(target,{recursive:true,force:true,maxRetries:3,retryDelay:100});
 }
 console.log('PASS '+count+' Node batch runner groups');
})().catch(error=>{console.error(error);process.exitCode=1;});
