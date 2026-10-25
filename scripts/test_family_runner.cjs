'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js'),C=require('../local-plan-controls.js'),F=require('../research-family.js'),R=require('../family-runner.js');
const clone=v=>JSON.parse(JSON.stringify(v)),tick=()=>new Promise(resolve=>setImmediate(resolve));
const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8'));
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
function mock(transform=x=>x){const calls=[];return {calls,start(task){calls.push(task);return {promise:Promise.resolve().then(()=>transform(E.run(task),task,calls.length)),cancel(){}};}};}
async function fixture(count=2){const view=await F.snapshot(bundle,webcrypto),ids=F.caseIds(view).slice(0,count),plan=await F.prepare(bundle,ids,webcrypto),controls=[];for(const item of plan.cases)controls.push({caseId:item.id,suite:await C.prepare(item.task,webcrypto)});return {plan,controls};}
(async()=>{
 const base=await fixture();
 await test('all synthetic checks precede manuscript cases; output is the complete submission envelope',async()=>{
  const executor=mock(),events=[],run=R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls,{onProgress:p=>events.push(p)}),value=await run.promise;
  assert.deepEqual(value.plan,base.plan);assert.equal(executor.calls.length,6);
  assert(executor.calls.slice(0,4).every(t=>t.title.startsWith('Synthetic local reference')));
  assert.deepEqual(executor.calls.slice(4).map(t=>t.taskId),base.plan.cases.map(c=>c.task.taskId));
  assert.deepEqual(value.results,base.plan.cases.map(c=>({caseId:c.id,result:E.run(c.task)})));
  assert.deepEqual(value.controls,base.controls.map(c=>({caseId:c.caseId,results:c.suite.cases.map(f=>({id:f.id,result:E.run(f.task)}))})));
  assert.deepEqual(events,[{phase:'controls',completed:0,total:4},...[1,2,3,4].map(completed=>({phase:'controls',completed,total:4})),...[0,1,2].map(completed=>({phase:'cases',completed,total:2}))]);
  run.cancel();assert.equal(executor.calls.length,6);
 });
 await test('inputs are captured before asynchronous admission and cannot change execution',async()=>{
  const local=clone(base),executor=mock(),run=R.createRunner({executor,crypto:webcrypto}).start(local.plan,local.controls);
  local.plan.cases[0].task.pages[0].text='changed';local.controls[0].suite.cases[0].expectedResultSha256='0'.repeat(64);
  assert.deepEqual((await run.promise).plan,base.plan);
 });
 await test('tampered plan or any later suite rejects before the first worker',async()=>{
  const mutations=[v=>v.plan.planId='0'.repeat(64),v=>v.plan.cases[1].task.title+=' changed',v=>v.controls.reverse(),v=>v.controls.pop(),v=>v.controls.push(v.controls[0]),v=>v.controls[0].extra=true,v=>v.controls[1].suite.cases[1].expectedResultSha256='0'.repeat(64),v=>v.controls[1].suite.cases[1].task.pages[0].text+='x'];
  for(const alter of mutations){const value=clone(base);alter(value);const executor=mock();await assert.rejects(R.createRunner({executor,crypto:webcrypto}).start(value.plan,value.controls).promise);assert.equal(executor.calls.length,0);}
 });
 await test('a corrupted control or executor rejection aborts without manuscript work',async()=>{
  for(const failure of ['wrong','throw']){const executor=mock((result,task,n)=>{if(n===2){if(failure==='throw')throw Error('worker failed');result.metrics.runes++;}return result;});await assert.rejects(R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls).promise);assert.equal(executor.calls.length,2);assert(executor.calls.every(t=>t.title.startsWith('Synthetic')));}
 });
 await test('manuscript outputs also require complete verification',async()=>{
  const executor=mock((r,t,n)=>{if(n===5)r.transformed[0].text+='x';return r;});await assert.rejects(R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls).promise);assert.equal(executor.calls.length,5);
 });
 await test('immediate cancellation stops admission before worker creation',async()=>{
  const executor=mock(),run=R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls);run.cancel();run.cancel();await assert.rejects(run.promise,{name:'AbortError'});await tick();assert.equal(executor.calls.length,0);
 });
 await test('cancellation terminates current work even if its stale promise later resolves',async()=>{
  let resolveCurrent,cancelled=0;const calls=[],executor={start(task){calls.push(task);return {promise:new Promise(resolve=>resolveCurrent=()=>resolve(E.run(task))),cancel(){cancelled++;}};}};
  const run=R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls);while(!resolveCurrent)await tick();run.cancel();await assert.rejects(run.promise,{name:'AbortError'});assert.equal(cancelled,1);resolveCurrent();await tick();await tick();assert.equal(calls.length,1);
 });
 await test('cancelling from the last control progress event never starts a manuscript',async()=>{
  const executor=mock();let run;run=R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls,{onProgress:p=>{if(p.phase==='controls'&&p.completed===p.total)run.cancel();}});await assert.rejects(run.promise,{name:'AbortError'});assert.equal(executor.calls.length,4);
 });
 await test('cancelling after one manuscript case prevents every remaining case',async()=>{
  const executor=mock();let run;run=R.createRunner({executor,crypto:webcrypto}).start(base.plan,base.controls,{onProgress:p=>{if(p.phase==='cases'&&p.completed===1)run.cancel();}});await assert.rejects(run.promise,{name:'AbortError'});assert.equal(executor.calls.length,5);
 });
 await test('the full twelve-case batch remains bounded and preserves case order',async()=>{
  const value=await fixture(12),executor=mock(),result=await R.createRunner({executor,crypto:webcrypto}).start(value.plan,value.controls).promise;assert.equal(executor.calls.length,36);assert.equal(result.results.length,12);assert.equal(result.controls.length,12);assert(executor.calls.slice(0,24).every(t=>t.title.startsWith('Synthetic')));assert.deepEqual(result.results.map(v=>v.caseId),value.plan.cases.map(v=>v.id));
 });
 await test('each run is isolated, including cancellation and throwing progress observers',async()=>{
  const executor=mock(),runner=R.createRunner({executor,crypto:webcrypto}),a=runner.start(base.plan,base.controls),b=runner.start(base.plan,base.controls,{onProgress(){throw Error('view failed');}});a.cancel();await assert.rejects(a.promise,{name:'AbortError'});assert.equal((await b.promise).results.length,2);assert.equal(executor.calls.length,6);
 });
 await test('browser UMD exports use injected fixed executor dependencies',async()=>{
  const context={LocalExperiment:E,LocalPlanControls:C,ResearchFamily:F,LocalRunExecutor:{createExecutor:()=>mock()},TextEncoder,DOMException,crypto:webcrypto};vm.createContext(context);vm.runInContext(fs.readFileSync('family-runner.js','utf8'),context);const value=await context.FamilyRunner.createRunner().start(base.plan,base.controls).promise;assert.equal(E.stable(value.plan),E.stable(base.plan));assert.equal(value.results.length,2);
 });
 console.log('PASS '+groups+' family runner groups');
})().catch(error=>{console.error(error);process.exitCode=1;});
