/* Finite exact-opening evidence: real domain, mathematical exclusions, immutable receipts. */
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto,createHash}=require('node:crypto');
const F=require('../research-family.js'),L=require('../local-experiment.js'),Q=require('../family-question-evidence.js');
const crypto=webcrypto,clone=v=>JSON.parse(JSON.stringify(v)),sha=v=>createHash('sha256').update(L.stable(v)).digest('hex'),at='2026-10-25T12:00:00.000Z';
const bundle=JSON.parse(fs.readFileSync(new URL('../data/local-run-inputs.json','file:///'+__filename.replaceAll('\\','/')),'utf8'));
async function direct(preparer,caseId){const task=(await preparer.prepare([caseId])).cases[0].task,result=L.run(task);return {familyId:preparer.snapshot.id,revision:preparer.snapshot.revision,caseId,task,result,resultId:sha(result),verifiedAt:at};}
async function main(){
 let groups=0;
 const preparer=await F.createPreparer(bundle,crypto),snapshot=preparer.snapshot,empty=await Q.summarize({snapshot,bundle,sources:[]},crypto);
 assert.equal(empty.totalCases,990);assert.equal(empty.excludedCaseIds.length,963);assert.equal(empty.missingCaseIds.length,27);assert.equal(empty.complete,false);assert.deepEqual(empty.foundCaseIds,[]);assert.equal(Q.inspect(empty),empty);assert(Object.isFrozen(empty.exclusions[0]));assert.throws(()=>Q.inspect(clone(empty)));groups++;
 assert.deepEqual(empty.excludedCaseIds,F.proveCaseExclusions(snapshot,bundle.alphabet).excluded.map(x=>x.caseId));
 const receipts=[];for(const caseId of empty.missingCaseIds)receipts.push(await direct(preparer,caseId));
 assert(receipts.every(receipt=>receipt.result.matches[0].matched===false));
 const complete=await Q.summarize({snapshot,bundle,sources:receipts},crypto);assert.equal(complete.complete,true);assert.equal(complete.verifiedCaseIds.length,27);assert.deepEqual(complete.missingCaseIds,[]);assert.deepEqual(complete.foundCaseIds,[]);groups++;
 const partial=await Q.summarize({snapshot,bundle,sources:receipts.slice(0,2)},crypto);assert.equal(partial.complete,false);assert.equal(partial.missingCaseIds.length,25);assert.deepEqual(partial.missingCaseIds,empty.missingCaseIds.slice(2));
 const unavailable=await Q.summarize({snapshot,bundle,sources:receipts.slice(0,2),lookupComplete:false},crypto);assert.equal(unavailable.lookupComplete,false);assert.deepEqual(unavailable.missingCaseIds,partial.missingCaseIds);groups++;
 for(const change of [r=>r.revision='0'.repeat(64),r=>r.familyId='another-family',r=>r.caseId='repeat--subtract--page--lp2-50',r=>r.verifiedAt='not a date',r=>r.resultId='0'.repeat(64),r=>r.completed=true]){
  const source=clone(receipts[0]);change(source);await assert.rejects(Q.summarize({snapshot,bundle,sources:[source]},crypto));
 }
 await assert.rejects(Q.summarize({snapshot,bundle,sources:[receipts[0],receipts[0]]},crypto));
 const fakeHit=clone(receipts[0]);fakeHit.result.matches[0].matched=true;fakeHit.resultId=sha(fakeHit.result);await assert.rejects(Q.summarize({snapshot,bundle,sources:[fakeHit]},crypto));groups++;
 const altered=clone(receipts[0]);altered.task=await L.prepare({...altered.task,pages:[{...altered.task.pages[0],text:altered.task.pages[0].text+bundle.alphabet[0].rune}]},crypto);altered.result=L.run(altered.task);altered.resultId=sha(altered.result);
 await assert.rejects(Q.summarize({snapshot,bundle,sources:[altered]},crypto),/exact case and page bytes/);
 const wrongBundle=clone(bundle);wrongBundle.pages.find(p=>p.id==='lp2-00').raw+=bundle.alphabet[0].rune;
 await assert.rejects(Q.summarize({snapshot,bundle:wrongBundle,sources:[]},crypto),/snapshot/);groups++;
 // Shared receipts may have a different title and a larger batch. The exact
 // family case is proved through the same operation/criterion/page byte identity.
 const caseId=receipts[0].caseId,sourceTask=await L.prepare({...receipts[0].task,title:'A separate outcome and category',pages:[receipts[0].task.pages[0],snapshot.pages.find(p=>p.id!==receipts[0].task.pages[0].id)]},crypto),result=L.run(sourceTask),shared={familyId:snapshot.id,revision:snapshot.revision,caseId,source:{task:sourceTask,inputVersion:'raw',run:{id:sha(result),createdAt:at,result}}};
 const reused=await Q.summarize({snapshot,bundle,sources:[shared]},crypto);assert.deepEqual(reused.verifiedCaseIds,[caseId]);assert.equal(reused.evidence[0].taskId,sourceTask.taskId);
 const wire={familyId:snapshot.id,revision:snapshot.revision,sources:[clone(shared.source)],cases:[{caseId,sourceIndex:0}],lookupComplete:true},unpacked=Q.unpack(wire);
 assert.deepEqual(unpacked.sources,[shared]);assert.throws(()=>Q.inspect(unpacked));
 assert.deepEqual((await Q.summarize({snapshot,bundle,sources:unpacked.sources,lookupComplete:unpacked.lookupComplete},crypto)).verifiedCaseIds,[caseId]);
 for(const change of [w=>w.cases[0].sourceIndex=-1,w=>w.cases[0].sourceIndex=1,w=>w.cases[0].sourceIndex=0.5,w=>w.cases.push(clone(w.cases[0])),w=>w.sources.push(clone(w.sources[0])),w=>w.cases=[],w=>w.sources[0].inputVersion='reviewed',w=>w.lookupComplete='yes',w=>w.extra=true,w=>w.sources[0].task.title='x'.repeat(2*1024*1024)]){const bad=clone(wire);change(bad);assert.throws(()=>Q.unpack(bad));}
 const distinctUnused=clone(wire);distinctUnused.sources.push(clone(shared.source));distinctUnused.sources[1].run.createdAt='2026-10-26T12:00:00.000Z';assert.throws(()=>Q.unpack(distinctUnused),/unreferenced/);groups++;
 const reviewed=clone(shared);reviewed.source.inputVersion='reviewed';await assert.rejects(Q.summarize({snapshot,bundle,sources:[reviewed]},crypto));
 const different=clone(shared);different.source.task=await L.prepare({...sourceTask,criterion:{kind:'exact-prefix',values:[0]}},crypto);different.source.run.result=L.run(different.source.task);different.source.run.id=sha(different.source.run.result);await assert.rejects(Q.summarize({snapshot,bundle,sources:[different]},crypto));groups++;
 // Necessary-condition filtering cannot discard a planted real opening under
 // any of the 18 configurations. Generate ciphertext by the inverse recurrence.
 const key=[23,18,3,4],values=[24,7,24,4,9,21,17,18,20,10,18,1];
 for(const config of snapshot.configurations){
  const c=[];for(let i=0;i<values.length;i++){const k=i<4?key[i]:config.mode==='repeat'?key[i%4]:config.mode==='plaintext-autokey'?values[i-4]:c[i-4];c.push((values[i]+(config.direction==='subtract'?k:-k)+29)%29);}
  const planted=clone(bundle);planted.pages.find(p=>p.id==='lp2-00').raw=c.map(v=>planted.alphabet[v].rune).join('');
  const p=await F.createPreparer(planted,crypto),id=config.id+'--lp2-00',receipt=await direct(p,id);assert.equal(receipt.result.matches[0].matched,true);
  const proof=await Q.summarize({snapshot:p.snapshot,bundle:planted,sources:[receipt],lookupComplete:false},crypto);
  assert.deepEqual(proof.foundCaseIds,[id]);assert(proof.missingCaseIds.length>0);assert.equal(proof.complete,false);assert(!proof.excludedCaseIds.includes(id));assert.equal(proof.lookupComplete,false);
 }groups++;
 // Snapshot flags and detached result objects are never authority; callers'
 // inputs also remain mutable and are not frozen or retained by the proof.
 const flagged={...snapshot,completed:empty.missingCaseIds,matched:empty.missingCaseIds};await assert.rejects(Q.summarize({snapshot:flagged,bundle,sources:[]},crypto));
 const captured=clone(receipts[0]),proof=await Q.summarize({snapshot,bundle,sources:[captured]},crypto);captured.result.matches[0].matched=true;assert.deepEqual(proof.foundCaseIds,[]);assert(!Object.isFrozen(captured));groups++;
 console.log('PASS family question evidence ('+groups+' groups): real990-case domain,963 independent exclusions,27 verified nonmatches,18 planted configurations, current revision and exact shared evidence.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
