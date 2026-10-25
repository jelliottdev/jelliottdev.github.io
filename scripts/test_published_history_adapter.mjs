/* Exact retained reads do not turn history into current candidate discovery. */
import assert from 'node:assert/strict';
import HistoryData from '../published-evidence-history-data.js';
import Count from '../published-count-evidence-data.js';
import E from '../local-experiment.js';
import Hydration from '../published-evidence-history.js';
import Evidence from '../computation-evidence.js';
import Client from '../verified-evidence-client.js';
import http from 'node:http';
import {readPublishedEvidence,resolvePublishedEvidence,findPublishedEvidence,createPublishedEvidenceHandler} from '../services/idea-assistant/published-evidence.mjs';
const clone=v=>JSON.parse(JSON.stringify(v)),empty={schema:Count.schema,records:[],entries:[]},old=HistoryData.receipts.find(r=>r.registrySchema===Count.schema&&r.revision!==Count.entries[0].revision),reference={recordId:old.recordId,revision:old.revision,caseId:old.caseId},identity={taskId:old.taskId,resultId:old.resultId,inputVersion:old.inputVersion,createdAt:old.createdAt},expected=Hydration.create(HistoryData).find(reference),origin='https://jelliottdev.github.io';
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
const original=E.run;E.run=()=>{throw Error('Runtime retained reads must not execute a target');};
try{
 await test('default historical read returns original exact bytes and provenance rather than a current redirect',async()=>{
  const read=await readPublishedEvidence(reference);assert(read);assert.equal(read.publishedSource.revision,old.revision);assert.notEqual(read.publishedSource.revision,Count.entries[0].revision);assert.deepEqual(read.task,expected.entries[0].task);assert.deepEqual(read.run,expected.entries[0].run);assert.deepEqual(read.provenance,expected.records[0].provenance);assert.equal(read.inputVersion,old.inputVersion);read.task.pages[0].text='changed';assert.notEqual((await readPublishedEvidence(reference)).task.pages[0].text,'changed');
 });
 await test('current discovery and source resolution prefer one current proof over retained aliases',async()=>{
  const task=Count.entries[0].task,found=await findPublishedEvidence({task,inputVersion:'raw'});assert.equal(found.sources.length,1);assert.equal(found.publishedSources.length,1);assert.equal(found.publishedSources[0].revision,Count.entries[0].revision);const resolved=await resolvePublishedEvidence(identity);assert.equal(resolved.publishedSource.revision,Count.entries[0].revision);
 });
 await test('explicit registries stay isolated unless exact history is supplied; null disables default retention',async()=>{
  assert.equal(await readPublishedEvidence({...reference,registry:Count}),null);assert.equal(await resolvePublishedEvidence({...identity,registry:empty}),null);assert.equal(await readPublishedEvidence({...reference,history:null}),null);assert(await readPublishedEvidence({...reference,registry:empty,history:HistoryData}));
  const resolved=await resolvePublishedEvidence({...identity,registry:empty,history:HistoryData});assert.equal(resolved.source.task.taskId,old.taskId);assert.equal(resolved.source.run.id,old.resultId);assert.equal(resolved.source.run.createdAt,old.createdAt);assert.equal(await resolvePublishedEvidence({...identity,registry:empty,history:HistoryData,inputVersion:'reviewed'}),null);assert.equal(await resolvePublishedEvidence({...identity,registry:empty,history:HistoryData,createdAt:'2000-01-01T00:00:00.000Z'}),null);assert.equal(await readPublishedEvidence({...reference,revision:'0'.repeat(64)}),null);
 });
 await test('HTTP historical URLs stay stable and unknown revisions remain 404',async()=>{
  const handler=createPublishedEvidenceHandler(),url='https://worker.example/published-evidence/'+old.recordId+'/'+old.caseId+'?revision='+old.revision,request=value=>new Request(value,{headers:{origin}}),response=await handler(request(url),{SITE_ORIGIN:origin});assert.equal(response.status,200);assert.equal(response.headers.get('location'),null);const value=await response.json();assert.equal(value.publishedSource.revision,old.revision);assert.deepEqual(value.provenance,old.provenance);assert.deepEqual(value.run,expected.entries[0].run);assert.equal((await handler(request(url.replace(old.revision,'0'.repeat(64))),{SITE_ORIGIN:origin})).status,404);assert.equal((await createPublishedEvidenceHandler({history:null})(request(url),{SITE_ORIGIN:origin})).status,404);
 });
 await test('selected historical corruption and conflicting aliases fail closed before any result is returned',async()=>{
  for(const mutate of [history=>{history.receipts.find(r=>r.revision===old.revision).provenance.dateMeaning+=' forged';},history=>{history.results.find(r=>r.id===old.resultId).result.wordPairs.matches++;},history=>{const duplicate=clone(history.receipts.find(r=>r.revision===old.revision));duplicate.createdAt='2000-01-01T00:00:00.000Z';history.receipts.push(duplicate);},history=>{history.tasks.find(t=>t.id===old.taskId).task.engine='unsupported-old-engine-v99';}]){
   const history=clone(HistoryData);mutate(history);await assert.rejects(()=>readPublishedEvidence({...reference,registry:empty,history}));const handler=createPublishedEvidenceHandler({registry:empty,history}),response=await handler(new Request('https://worker.example/published-evidence/'+old.recordId+'/'+old.caseId+'?revision='+old.revision,{headers:{origin}}),{SITE_ORIGIN:origin});assert.equal(response.status,503);
  }
 });
 await test('fallback resolves a single selected body without enumerating historical manifests',async()=>{
  const create=Hydration.create;let scans=0;Hydration.create=data=>{const archive=create(data);return {...archive,manifests(){throw Error('Never enumerate all proof bodies during source resolution');},findSource(ref){scans++;return archive.findSource(ref);}};};try{const result=await resolvePublishedEvidence({...identity,registry:empty,history:HistoryData});assert(result);assert.equal(scans,1);}finally{Hydration.create=create;}
 });
 await test('real local HTTP historical response replays in the browser proof client with no task fallback',async()=>{
  const handler=createPublishedEvidenceHandler(),paths=[];let base;
  const server=http.createServer(async(req,res)=>{try{paths.push(req.url);assert(req.url.startsWith('/published-evidence/'));const response=await handler(new Request(base+req.url,{headers:req.headers}),{SITE_ORIGIN:base});res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));}catch(error){res.writeHead(500);res.end(error.message);}});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base='http://127.0.0.1:'+server.address().port;
  try{const source=await readPublishedEvidence(reference),ref={taskId:old.taskId,resultId:old.resultId,...reference},coverage={...await Evidence.compare(source.task,'raw',[{task:source.task,inputVersion:'raw',run:source.run}]),requestedTask:source.task,inputVersion:'raw',truncated:false,publishedSources:[ref]},client=Client.create({endpoint:base+'/tasks',validEndpoint:(url,kind)=>url===base+'/tasks'&&kind==='tasks',request:url=>fetch(url,{headers:{origin:base}})}),checked=await client.checkCoverage(coverage);assert.equal(checked.coveredPages.length,56);assert.deepEqual(checked.remainingPages,[]);const replayed=client.getSources(checked)[0];assert.equal(replayed.run.result.wordPairs.matches,77);assert(E.summary(replayed.task,replayed.run.result));assert.equal(paths.length,1);assert(paths[0].endsWith('?revision='+old.revision));assert.equal(checked.publishedSources[0].revision,old.revision);assert.equal(checked.links[old.taskId],'library.html#/experiment/'+old.recordId);}finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
 });
 console.log(groups+' published history adapter groups passed');
}finally{E.run=original;}
