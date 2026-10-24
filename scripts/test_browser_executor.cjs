'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js'),{createExecutor}=require('../local-run-executor.js');
const root=path.resolve(__dirname,'..'),engine=fs.readFileSync(path.join(root,'local-experiment.js'),'utf8'),workerSource=fs.readFileSync(path.join(root,'local-run-worker.js'),'utf8');
const workers=[];
class WorkerFixture{
 constructor(url){assert.equal(url,'local-run-worker.js?v=20261024-word-sums');this.stopped=false;workers.push(this);
  const self={postMessage:data=>{if(!this.stopped)this.onmessage?.({data:structuredClone(data)});}};
  const context=vm.createContext({self,crypto:webcrypto,TextEncoder,structuredClone});
  context.importScripts=url=>{assert.equal(url,'local-experiment.js?v=20261024-word-sums');vm.runInContext(engine,context);};
  vm.runInContext(workerSource,context);this.receive=self.onmessage;
 }
 postMessage(data){this.message=structuredClone(data);queueMicrotask(()=>{if(!this.stopped)Promise.resolve(this.receive({data:this.message})).catch(()=>this.onerror?.({preventDefault(){}}));});}
 terminate(){this.stopped=true;}
}
function deferred(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
async function task(){return E.prepare({title:'Browser fixture',pages:[{id:'lp2-15',text:'ABC A'},{id:'lp2-16',text:'BAC\r\nABC'}],alphabet:Array.from({length:29},(_,i)=>({rune:String.fromCharCode(65+i),latin:'R'+i,prime:i+2})),steps:[{op:'reverse',unit:'line'}],criterion:{kind:'measurement'}},webcrypto);}
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
(async()=>{
 await test('actual worker script runs fixed engine and reports real page progress',async()=>{
  const input=await task(),progress=[],executor=createExecutor({WorkerClass:WorkerFixture});
  const result=await executor.start(input,{onProgress:p=>progress.push(p)}).promise;
  await E.verify(input,result,webcrypto);assert.deepEqual(progress.map(p=>[p.phase,p.completed,p.total]),[['checking',0,2],['running',1,2],['running',2,2]]);
  assert(workers.at(-1).stopped);assert.equal(input.pages[0].text,'ABC A');
 });
 await test('fixed worker accepts all keyed modes and returns the exact declared computation',async()=>{
  for(const mode of ['repeat','plaintext-autokey','ciphertext-autokey'])for(const direction of ['subtract','add']){
   const input=await E.prepare({...await task(),steps:[{op:'keyed-shift',key:[1,2],mode,direction,reset:'page'}]},webcrypto);
   const output=await createExecutor({WorkerClass:WorkerFixture}).start(input).promise;
   assert.deepEqual(await E.verify(input,output,webcrypto),E.run(input));assert(workers.at(-1).stopped);
  }
 });
 await test('actual worker executes a finite stream without repetition and rejects an underrun before worker creation',async()=>{
  const input=await E.prepare({...await task(),steps:[{op:'finite-shift',key:[1,2,3,4,5,6],direction:'subtract',reset:'page'}]},webcrypto);
  const output=await createExecutor({WorkerClass:WorkerFixture}).start(input).promise;assert.deepEqual(await E.verify(input,output,webcrypto),E.run(input));
  const short=structuredClone(input);short.steps[0].key=[1];short.taskId=await E.identity(short,webcrypto);const before=workers.length;await assert.rejects(createExecutor({WorkerClass:WorkerFixture}).start(short).promise,/shorter/);assert.equal(workers.length,before);
 });
 await test('actual worker preserves literal interrupt runes and the held key clock',async()=>{
  for(const direction of ['subtract','add'])for(const reset of ['page','line','word']){
   const input=await E.prepare({...await task(),steps:[{op:'interrupted-keyed-shift',key:[1,3],direction,reset,interrupts:[0]}]},webcrypto);
   const output=await createExecutor({WorkerClass:WorkerFixture}).start(input).promise;
   assert.deepEqual(await E.verify(input,output,webcrypto),E.run(input));assert.equal(output.transformed[0].text[0],'A');assert(workers.at(-1).stopped);
  }
  const invalid=await task();invalid.steps=[{op:'interrupted-keyed-shift',key:[1],direction:'subtract',reset:'page',interrupts:[0,0]}];invalid.taskId=await E.identity(invalid,webcrypto);
  const before=workers.length;await assert.rejects(createExecutor({WorkerClass:WorkerFixture}).start(invalid).promise);assert.equal(workers.length,before);
 });
 await test('actual worker measures word prime values using the declared table and boundaries',async()=>{
  const input=await E.prepare({...await task(),steps:[],criterion:{kind:'word-prime-sums',table:'reversed',boundaries:'non-rune'}},webcrypto);
  const output=await createExecutor({WorkerClass:WorkerFixture}).start(input).promise;
  assert.deepEqual(await E.verify(input,output,webcrypto),E.run(input));assert.equal(output.wordSums.words,4);assert.equal(output.wordSums.total,291);assert.deepEqual(output.wordSums.pages[0].words[0],{runes:'ABC',sum:87});assert(workers.at(-1).stopped);
 });
 await test('stop terminates the worker and rejects without accepting late output',async()=>{
  const executor=createExecutor({WorkerClass:WorkerFixture}),run=executor.start(await task());
  const worker=workers.at(-1);run.cancel();await assert.rejects(run.promise,{name:'AbortError'});assert(worker.stopped);
  worker.onmessage({data:{id:worker.message.id,type:'result',result:{taskId:worker.message.task.taskId}}});
 });
 await test('input snapshot, result binding and malformed progress are enforced',async()=>{
  const gate=deferred();class ManualWorker{constructor(){gate.resolve(this);}postMessage(m){this.message=m;}terminate(){this.stopped=true;}}
  const input=await task(),progress=[],run=createExecutor({WorkerClass:ManualWorker}).start(input,{onProgress:p=>progress.push(p)}),w=await gate.promise;
  input.pages[0].text='changed';assert.equal(w.message.task.pages[0].text,'ABC A');
  for(const p of [{phase:'running',completed:3,total:2},{phase:'running',completed:1,total:3},{phase:'anything',completed:1,total:2}])w.onmessage({data:{id:w.message.id,type:'progress',progress:p}});
  assert.deepEqual(progress,[]);w.onmessage({data:{id:w.message.id,type:'result',result:{taskId:'a'.repeat(64)}}});await assert.rejects(run.promise,/different experiment/);assert(w.stopped);
 });
 await test('deadline, unavailable worker, identity mismatch and load errors recover cleanly',async()=>{
  let fire;class HungWorker{postMessage(){}terminate(){this.stopped=true;}}
  const run=createExecutor({WorkerClass:HungWorker,schedule:fn=>{fire=fn;return 1;},unschedule(){}}).start(await task());fire();await assert.rejects(run.promise,/time limit/);
  await assert.rejects(createExecutor({WorkerClass:null}).start(await task()).promise,/cannot start/);
  const invalid=await task();invalid.taskId='a'.repeat(64);await assert.rejects(createExecutor({WorkerClass:WorkerFixture}).start(invalid).promise,/could not run/);
  class BrokenWorker{constructor(){throw Error('Worker blocked');}}
  await assert.rejects(createExecutor({WorkerClass:BrokenWorker}).start(await task()).promise,/Worker blocked/);
 });
 console.log('PASS '+groups+' browser execution groups; fixed worker/engine, no network or generated-code execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
