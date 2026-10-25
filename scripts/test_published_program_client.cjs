/* Browser proof loading of compiled programs always replays the complete receipt. */
'use strict';
const assert=require('node:assert/strict'),{createHash}=require('node:crypto'),E=require('../local-experiment.js'),Evidence=require('../computation-evidence.js'),Client=require('../verified-evidence-client.js'),Registry=require('../published-opening-evidence-data.js'),Count=require('../published-count-evidence-data.js');
const clone=v=>JSON.parse(JSON.stringify(v)),sha=v=>createHash('sha256').update(E.stable(v)).digest('hex'),entry=Registry.entries[0],record=Registry.records[0],endpoint='https://worker.example/tasks';
function apiFor(item=entry,sourceRecord=record){return {task:clone(item.task),inputVersion:item.inputVersion,run:clone(item.run),publishedSource:{taskId:item.task.taskId,resultId:item.run.id,recordId:item.recordId,revision:item.revision,caseId:item.caseId},provenance:clone(sourceRecord.provenance)};}
async function coverage(task,wire){return {...await Evidence.compare(task,'raw',[{task:wire.task,inputVersion:'raw',run:wire.run}]),requestedTask:task,inputVersion:'raw',truncated:false,publishedSources:[wire.publishedSource]};}
function clientFor(wire){const calls=[],client=Client.create({endpoint,validEndpoint:(url,kind)=>url===endpoint&&kind==='tasks',request:async url=>{calls.push(url);assert(url.startsWith('https://worker.example/published-evidence/'),'A published receipt must never fall through to /tasks');return Response.json(wire);}});return {client,calls};}
function repin(wire){wire.run.id=sha(wire.run.result);wire.provenance.projection.resultId=wire.run.id;wire.provenance.projection.taskId=wire.task.taskId;wire.publishedSource={...wire.publishedSource,taskId:wire.task.taskId,resultId:wire.run.id,revision:sha(wire.provenance)};return wire;}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('actual 55-page program proof loads one published source and exposes independently branded negative results',async()=>{
  const wire=apiFor(),value=await coverage(entry.task,wire),{client,calls}=clientFor(wire),checked=await client.checkCoverage(value);assert.equal(checked.coveredPages.length,55);assert.deepEqual(checked.remainingPages,[]);assert.equal(calls.length,1);assert.equal(calls[0],'https://worker.example/published-evidence/'+entry.recordId+'/'+entry.caseId+'?revision='+entry.revision);assert.match(checked.titles[entry.task.taskId],/^Published opening check/);assert.equal(checked.links[entry.task.taskId],'library.html#/experiment/prepared-opening-evidence-gates');const sources=client.getSources(checked);assert.equal(sources.length,1);assert.equal(sources[0].run.result.matches.length,55);assert(sources[0].run.result.matches.every(row=>row.matched===false));assert(E.summary(sources[0].task,sources[0].run.result));assert.throws(()=>client.getSources(clone(checked)));
 });
 await test('another title and reordered page subset reuses the exact transformed-prefix program only',async()=>{
  const task=await E.prepare({...entry.task,title:'Different category for the same program',pages:[entry.task.pages[31],entry.task.pages[0]]}),wire=apiFor(),value=await coverage(task,wire),{client,calls}=clientFor(wire),checked=await client.checkCoverage(value);assert.deepEqual(checked.coveredPages,task.pages.map(p=>p.id));assert.equal(checked.exactTaskId,null);assert.equal(calls.length,1);
  for(const mutation of [{steps:[{op:'reverse',unit:'word'},{op:'affine',a:28,b:28}]},{criterion:{kind:'exact-prefix',values:entry.task.criterion.values.slice(0,12)}}]){const changed=await E.prepare({...task,...mutation}),forged={...value,requestedTask:changed};await assert.rejects(()=>client.checkCoverage(forged));}
 });
 await test('provenance, declared steps, prefix values and exact source bytes are checked even with updated revision hashes',async()=>{
  for(const mutate of [wire=>{wire.provenance.dateMeaning+=' tampered';},wire=>{wire.provenance.projection.steps[0].unit='word';wire.publishedSource.revision=sha(wire.provenance);},wire=>{wire.provenance.projection.criterion.values[0]=0;wire.publishedSource.revision=sha(wire.provenance);},wire=>{wire.provenance.sourcePins.find(p=>p.path==='text/lp2-00.txt').sha256='0'.repeat(64);wire.publishedSource.revision=sha(wire.provenance);}]){
   const wire=apiFor();mutate(wire);const value=await coverage(entry.task,wire),{client,calls}=clientFor(wire);await assert.rejects(()=>client.checkCoverage(value));assert.equal(calls.length,1);
  }
 });
 await test('a fully rehashed self-consistent wrong-transform receipt cannot bypass independent browser replay',async()=>{
  const wire=apiFor(),wrongTask=await E.prepare({...entry.task,steps:[{op:'reverse',unit:'word'},{op:'affine',a:28,b:28}]});wire.run.result=E.run(wrongTask);wire.run.result.taskId=entry.task.taskId;repin(wire);
  const value=await coverage(entry.task,wire);assert.equal(value.coveredPages.length,55,'Structural/hash consistency alone can describe the forged stored result');const {client}=clientFor(wire);await assert.rejects(()=>client.checkCoverage(value),/result|match|computation|reproduce/i);
 });
 await test('count-v1 remains unchanged and public target-run entry is never invoked while loading either proof',async()=>{
  const countWire=apiFor(Count.entries[0],Count.records[0]),countValue=await coverage(Count.entries[0].task,countWire),programWire=apiFor(),programValue=await coverage(entry.task,programWire),original=E.run;E.run=()=>{throw Error('No public target-run call during receipt loading');};try{for(const [wire,value,kind] of [[countWire,countValue,'count'],[programWire,programValue,'opening']]){const {client,calls}=clientFor(wire),checked=await client.checkCoverage(value);assert.equal(calls.length,1);assert.match(checked.titles[wire.task.taskId],new RegExp('Published '+kind+' check'));if(kind==='count')assert.equal(client.getSources(checked)[0].run.result.wordPairs.matches,77);}}finally{E.run=original;}
 });
 console.log(groups+' published program client groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
