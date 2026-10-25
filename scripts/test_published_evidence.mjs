/* Published count receipts retain provenance and share only exact computations. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import Registry from '../published-count-evidence-data.js';
import ProgramRegistry from '../published-opening-evidence-data.js';
import L from '../local-experiment.js';
import {findPublishedEvidence,resolvePublishedEvidence,readPublishedEvidence,createPublishedEvidenceHandler} from '../services/idea-assistant/published-evidence.mjs';
import {findEvidence,checkedEvidence} from '../services/idea-assistant/task-evidence.mjs';
const clone=v=>JSON.parse(JSON.stringify(v)),sha=v=>createHash('sha256').update(L.stable(v)).digest('hex');
const entry=Registry.entries[0],task=entry.task,sourceRef={taskId:task.taskId,resultId:entry.run.id,recordId:entry.recordId,revision:entry.revision,caseId:entry.caseId};
const db={prepare(){return{bind(){return{all:async()=>({results:[]}),first:async()=>null,run:async()=>{throw Error('Evidence lookup must never write.');}};}};}};
const originalRun=L.run;L.run=()=>{throw Error('Lookup must never decode or execute a target.');};
let groups=0;
try{
 const found=await findEvidence({db,task,inputVersion:'raw'});
 assert.equal(found.coveredPages.length,56);assert.deepEqual(found.remainingPages,[]);assert.equal(found.evidence.length,1);assert.deepEqual(found.publishedSources,[sourceRef]);assert.equal(found.exactTaskId,task.taskId);groups++;
 const replay=await checkedEvidence({db,task,inputVersion:'raw',evidence:found.evidence});assert.deepEqual(replay.coveredPages,found.coveredPages);groups++;
 const subset=await L.prepare({...task,title:'Another category and a different title',pages:[task.pages[4],task.pages[0]]});
 const partial=await findEvidence({db,task:subset,inputVersion:'raw'});assert.deepEqual(partial.coveredPages,subset.pages.map(p=>p.id));assert.equal(partial.exactTaskId,null);assert.deepEqual(partial.publishedSources,[sourceRef]);groups++;
 const changed=await L.prepare({...task,pages:[task.pages[0],{...task.pages[1],text:task.pages[1].text+' '+task.alphabet[0].rune}]});
 const mixed=await findEvidence({db,task:changed,inputVersion:'raw'});assert.deepEqual(mixed.coveredPages,[task.pages[0].id]);assert.deepEqual(mixed.remainingPages,[task.pages[1].id]);assert.deepEqual((await checkedEvidence({db,task:changed,inputVersion:'raw',evidence:mixed.evidence})).remainingPages,mixed.remainingPages);groups++;
 for(const mutation of [{inputVersion:'reviewed'},{criterion:{...task.criterion,boundaries:'non-rune'}},{criterion:{...task.criterion,lag:5}},{criterion:{...task.criterion,a:26}},{steps:[{op:'reverse',unit:'page'}]}]){
  const {inputVersion='raw',...updates}=mutation;
  const other=await L.prepare({...task,...updates});assert.deepEqual((await findPublishedEvidence({task:other,inputVersion})).sources,[]);
 }groups++;
 const read=await readPublishedEvidence(sourceRef);assert.deepEqual(read.publishedSource,sourceRef);assert.equal(read.run.result.wordPairs.matches,77);assert.equal(read.run.result.wordPairs.opportunities,1267);assert.match(read.provenance.dateMeaning,/not a historical browser/i);assert.equal(read.provenance.checkedAt,read.run.createdAt);
 assert.equal(await readPublishedEvidence({...sourceRef,revision:'a'.repeat(64)}),null);
 assert.equal(await resolvePublishedEvidence({...sourceRef,inputVersion:'raw',createdAt:'2000-01-01T00:00:00.000Z'}),null);
 read.task.pages[0].text='mutated';assert.notEqual((await readPublishedEvidence(sourceRef)).task.pages[0].text,'mutated');groups++;
 const badResult=clone(Registry);badResult.entries[0].run.result.wordPairs.matches++;
 await assert.rejects(findPublishedEvidence({task,inputVersion:'raw',registry:badResult}));
 const badInput=clone(Registry);badInput.entries[0].task.pages[0].text+='x';badInput.entries[0].task=await L.prepare(badInput.entries[0].task);
 await assert.rejects(findPublishedEvidence({task,inputVersion:'raw',registry:badInput}));
 const badPin=clone(Registry);badPin.records[0].provenance.sourcePins[0].sha256='0'.repeat(64);
 await assert.rejects(findPublishedEvidence({task,inputVersion:'raw',registry:badPin}),/provenance/);
 const badCriterion=clone(Registry);badCriterion.entries[0].task=await L.prepare({...task,criterion:{...task.criterion,b:23}});
 await assert.rejects(findPublishedEvidence({task,inputVersion:'raw',registry:badCriterion}));
 const badAlphabet=clone(Registry);const alphabet=clone(task.alphabet);[alphabet[0],alphabet[1]]=[alphabet[1],alphabet[0]];badAlphabet.entries[0].task=await L.prepare({...task,alphabet});
 await assert.rejects(findPublishedEvidence({task,inputVersion:'raw',registry:badAlphabet}));
 const badTask=clone(Registry);badTask.entries[0].task.title+=' tampered';await assert.rejects(findPublishedEvidence({task,inputVersion:'raw',registry:badTask}));groups++;
 const env={SITE_ORIGIN:'https://jelliottdev.github.io'},handler=createPublishedEvidenceHandler(),url='https://worker.example/published-evidence/'+entry.recordId+'/'+entry.caseId+'?revision='+entry.revision;
 const request=(suffix='',options={})=>new Request(url+suffix,{headers:{Origin:env.SITE_ORIGIN},...options});
 const response=await handler(request(),env);assert.equal(response.status,200);const api=await response.json();assert.deepEqual(api.publishedSource,sourceRef);assert.equal(sha(api.run.result),api.run.id);
 assert.equal((await handler(request('&other=1'),env)).status,404);assert.equal((await handler(request('',{method:'POST'}),env)).status,405);assert.equal((await handler(new Request(url),env)).status,403);
 assert.equal((await handler(new Request(url,{method:'OPTIONS',headers:{Origin:env.SITE_ORIGIN,'access-control-request-method':'GET'}}),env)).status,204);groups++;
 const corruptProof=clone(found.evidence);corruptProof[0].resultId='0'.repeat(64);await assert.rejects(checkedEvidence({db,task,inputVersion:'raw',evidence:corruptProof}));groups++;
 const programEntry=ProgramRegistry.entries[0],programTask=programEntry.task,programRef={taskId:programTask.taskId,resultId:programEntry.run.id,recordId:programEntry.recordId,revision:programEntry.revision,caseId:programEntry.caseId};
 const programFound=await findEvidence({db,task:programTask,inputVersion:'raw'});assert.equal(programFound.coveredPages.length,55);assert.deepEqual(programFound.remainingPages,[]);assert.equal(programFound.exactTaskId,programTask.taskId);assert.deepEqual(programFound.publishedSources,[programRef]);assert.equal(programFound.evidence.length,1);
 const programRead=await readPublishedEvidence(programRef);assert.deepEqual(programRead.publishedSource,programRef);assert.equal(programRead.provenance.schema,'liberpedia-published-program-projection-v1');assert.equal(programRead.provenance.projection.ownerRecordId,'lp2-row-column-routes');assert.deepEqual(programRead.task.steps,[{op:'reverse',unit:'line'},{op:'affine',a:28,b:28}]);assert.equal(programRead.run.result.matches.length,55);assert(programRead.run.result.matches.every(row=>row.matched===false));assert.match(programRead.provenance.verificationMeaning,/freshly reproduced/);assert.deepEqual((await checkedEvidence({db,task:programTask,inputVersion:'raw',evidence:programFound.evidence})).remainingPages,[]);groups++;
 const programSubset=await L.prepare({...programTask,title:'A differently classified question about this exact program',pages:[programTask.pages[31],programTask.pages[0]]}),subsetProof=await findEvidence({db,task:programSubset,inputVersion:'raw'});assert.deepEqual(subsetProof.coveredPages,programSubset.pages.map(p=>p.id));assert.equal(subsetProof.exactTaskId,null);assert.deepEqual(subsetProof.publishedSources,[programRef]);
 for(const mutation of [{steps:[{op:'reverse',unit:'word'},{op:'affine',a:28,b:28}]},{criterion:{kind:'exact-prefix',values:programTask.criterion.values.slice(0,12)}},{pages:[{...programTask.pages[0],text:programTask.pages[0].text+'x'}]}]){const changed=await L.prepare({...programTask,...mutation});assert.deepEqual((await findPublishedEvidence({task:changed,inputVersion:'raw'})).sources,[]);}assert.deepEqual((await findPublishedEvidence({task:programTask,inputVersion:'reviewed'})).sources,[]);groups++;
 const repin=value=>{const record=value.records[0],item=value.entries[0];record.revision=sha(record.provenance);item.revision=record.revision;return value;};
 for(const mutate of [value=>{value.records[0].provenance.projection.steps[0].unit='word';},value=>{value.records[0].provenance.projection.criterion.values[0]=0;}]){const bad=clone(ProgramRegistry);mutate(bad);repin(bad);await assert.rejects(findPublishedEvidence({task:programTask,inputVersion:'raw',registry:bad}),/scope or rules/);}
 const badProgramProvenance=clone(ProgramRegistry);badProgramProvenance.records[0].provenance.verificationMeaning+=' tampered';await assert.rejects(findPublishedEvidence({task:programTask,inputVersion:'raw',registry:badProgramProvenance}),/provenance/);
 const badProgramPage=clone(ProgramRegistry);badProgramPage.entries[0].task=await L.prepare({...programTask,pages:programTask.pages.map((p,i)=>i===0?{...p,text:p.text+'x'}:p)});badProgramPage.records[0].provenance.projection.taskId=badProgramPage.entries[0].task.taskId;repin(badProgramPage);await assert.rejects(findPublishedEvidence({task:programTask,inputVersion:'raw',registry:badProgramPage}),/source bytes/);
 const falseOpening=clone(ProgramRegistry);falseOpening.entries[0].run.result.matches[0].matched=true;falseOpening.entries[0].run.id=sha(falseOpening.entries[0].run.result);falseOpening.records[0].provenance.projection.resultId=falseOpening.entries[0].run.id;repin(falseOpening);await assert.rejects(findPublishedEvidence({task:programTask,inputVersion:'raw',registry:falseOpening}),/opening result is inconsistent/);groups++;
 const programUrl='https://worker.example/published-evidence/'+programEntry.recordId+'/'+programEntry.caseId+'?revision='+programEntry.revision,programResponse=await handler(new Request(programUrl,{headers:{Origin:env.SITE_ORIGIN}}),env);assert.equal(programResponse.status,200);const programAPI=await programResponse.json();assert.deepEqual(programAPI.publishedSource,programRef);assert.equal(programAPI.provenance.schema,'liberpedia-published-program-projection-v1');assert.equal(programAPI.run.result.matches.filter(r=>r.matched).length,0);assert.equal(sha(programAPI.run.result),programAPI.run.id);assert.equal((await readPublishedEvidence(sourceRef)).run.result.wordPairs.matches,77,'Count-v1 continues alongside program-v1');groups++;
 console.log('PASS published evidence ('+groups+' groups): count-v1 unchanged, program-v1 55 archived exclusions, default union, exact partial reuse, immutable provenance/settings/input pins, no lookup target execution.');
}finally{L.run=originalRun;}
