/* Historical URLs retain exact envelopes, while discovery remains current-only. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import History from '../published-evidence-history-data.js';
import Count from '../published-count-evidence-data.js';
import Program from '../published-opening-evidence-data.js';
import E from '../local-experiment.js';
import Hydration from '../published-evidence-history.js';
import {validateHistory,manifestFor,BUDGET} from './check_published_evidence_history.mjs';
import {readPublishedEvidence,findPublishedEvidence} from '../services/idea-assistant/published-evidence.mjs';
const clone=v=>JSON.parse(JSON.stringify(v)),hash=v=>createHash('sha256').update(E.stable(v)).digest('hex');
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('all seeded envelopes replay with deduplicated immutable task/result bodies',async()=>{
 const stats=await validateHistory(History);assert.equal(stats.receipts,History.receipts.length);assert(stats.receipts>=4);assert.equal(stats.tasks,2);assert.equal(stats.results,2);assert.equal(stats.replayed,2);assert(History.seedSources.length>=4);assert(Object.isFrozen(History.tasks[0].task.pages[0]));assert.equal(E.stable(History),E.stable(JSON.parse(readFileSync('data/published-evidence-history.json','utf8'))));
 const count=History.receipts.filter(r=>r.registrySchema===Count.schema);assert(count.length>=3);assert.equal(new Set(count.map(r=>r.revision)).size,count.length);assert.equal(new Set(count.map(r=>r.taskId)).size,1);assert.equal(new Set(count.map(r=>r.resultId)).size,1);
});
await test('every prior tuple reconstructs exact response fields without rewriting its provenance or dates',async()=>{
 for(const receipt of History.receipts){const registry=manifestFor(History,receipt),source=await readPublishedEvidence({recordId:receipt.recordId,revision:receipt.revision,caseId:receipt.caseId,registry});assert(source);assert.deepEqual(source.provenance,receipt.provenance);assert.equal(source.run.createdAt,receipt.createdAt);assert.equal(source.run.id,receipt.resultId);assert.equal(source.task.taskId,receipt.taskId);assert.equal(hash(source.provenance),receipt.revision);assert.equal(hash(source.run.result),receipt.resultId);assert.deepEqual(source.publishedSource,{taskId:receipt.taskId,resultId:receipt.resultId,recordId:receipt.recordId,revision:receipt.revision,caseId:receipt.caseId});assert.equal(await readPublishedEvidence({recordId:receipt.recordId,revision:'0'.repeat(64),caseId:receipt.caseId,registry}),null);}
});
await test('current discovery is not poisoned by historical aliases for the same mathematical task',async()=>{
 for(const registry of [Count,Program]){const entry=registry.entries[0],found=await findPublishedEvidence({task:entry.task,inputVersion:'raw'});assert.equal(found.sources.length,1);assert.equal(found.publishedSources.length,1);assert.equal(found.publishedSources[0].revision,entry.revision);}const old=History.receipts.find(r=>r.registrySchema===Count.schema&&r.revision!==Count.entries[0].revision);assert.equal(await readPublishedEvidence({...old,registry:Count}),null,'An explicitly current-only registry does not redirect a historical tuple');
});
await test('duplicates, missing bodies, changed envelopes and unreferenced retained data fail closed',async()=>{
 const mutations=[h=>h.receipts.push(clone(h.receipts[0])),h=>{h.receipts[0].provenance.dateMeaning+=' forged';},h=>{h.results[0].result.matches.push({page:'lp2-00',matched:true});},h=>h.tasks.pop(),h=>h.results.push(clone(h.results[0]))];
 for(const mutate of mutations){const bad=clone(History);mutate(bad);await assert.rejects(()=>validateHistory(bad));}
 const unused=clone(History),task=await E.prepare({...unused.tasks[0].task,title:'An unreferenced task body'});unused.tasks.push({id:task.taskId,task});unused.tasks.sort((a,b)=>a.id.localeCompare(b.id));await assert.rejects(()=>validateHistory(unused),/unreferenced/);
});
await test('pure hydration snapshots private data and returns only exact independently checkable envelopes',async()=>{
 const input=clone(History),archive=Hydration.create(input),receipt=History.receipts[0],reference={recordId:receipt.recordId,revision:receipt.revision,caseId:receipt.caseId};input.receipts[0].provenance.dateMeaning='mutated';const a=archive.find(reference);assert.deepEqual(a.records[0].provenance,receipt.provenance);a.entries[0].task.pages[0].text='changed';assert.notEqual(archive.find(reference).entries[0].task.pages[0].text,'changed');assert.equal(archive.find({...reference,revision:'0'.repeat(64)}),null);assert.throws(()=>archive.find({...reference,resultId:receipt.resultId}));assert.equal([...archive.manifests()].length,History.receipts.length);
});
await test('source aliases hydrate only the selected body and full enumeration stays lazy',async()=>{
 const archive=Hydration.create(History),receipt=History.receipts[0],stable=E.stable;let hydrated=0;E.stable=value=>{hydrated++;return stable(value);};
 try{const iterator=archive.manifests();assert.equal(hydrated,0);assert.equal(iterator.next().done,false);assert.equal(hydrated,1);const manifest=archive.findSource({taskId:receipt.taskId,resultId:receipt.resultId,inputVersion:receipt.inputVersion,createdAt:receipt.createdAt});assert.equal(hydrated,2);assert.equal(manifest.entries[0].run.id,receipt.resultId);assert.equal(archive.findSource({taskId:receipt.taskId,resultId:receipt.resultId,inputVersion:'reviewed'}),null);assert.equal(hydrated,2);assert.equal(archive.findSource({taskId:receipt.taskId,resultId:receipt.resultId,inputVersion:receipt.inputVersion,createdAt:'2000-01-01T00:00:00.000Z'}),null);assert.equal(hydrated,2);assert.throws(()=>archive.findSource({taskId:receipt.taskId,resultId:receipt.resultId,inputVersion:'raw',revision:receipt.revision}));}finally{E.stable=stable;}
});
await test('unsupported old engines and hard limits fail instead of dropping or rewriting old evidence',async()=>{
 const bad=clone(History);bad.tasks[0].task.engine='unknown-old-engine-v99';await assert.rejects(()=>validateHistory(bad),/engine|runner|unsupported/i);const over=clone(History);over.receipts=Array.from({length:BUDGET.receipts+1},()=>clone(History.receipts[0]));await assert.rejects(()=>validateHistory(over),/budget/);const reversed=clone(History);reversed.receipts.reverse();await assert.rejects(()=>validateHistory(reversed),/deterministic ordering/);
});
console.log(groups+' immutable published history groups passed');
