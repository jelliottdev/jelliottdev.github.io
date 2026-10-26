/* Separate immutable provider catalogs; actual browser verifiers, private read-only SQLite. */
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {webcrypto,createHash} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import E from '../local-experiment.js';
import Q from '../factored-finite-question.js';
import Client from '../factored-evidence-client.js';
import Evaluation from '../output-evaluators.js';
import {publishedProgramIndex,readPublishedEvidence,resolvePublishedEvidence} from '../services/idea-assistant/published-evidence.mjs';
import {readFactoredOutputEvidencePage,verifyFactoredOutputSnapshot} from '../services/idea-assistant/factored-output-evidence.mjs';
import {readFactoredInspectionEvidencePage,verifyFactoredInspectionSnapshot} from '../services/idea-assistant/factored-inspection-evidence.mjs';
const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8')),hash=v=>createHash('sha256').update(typeof v==='string'||v instanceof Uint8Array?v:E.stable(v)).digest('hex');
const old=read('data/published-program-source-index.json'),panel=read('data/published-panel-program-source-index.json'),catalog=read('data/published-program-source-catalog.json'),bundle=read('data/local-run-inputs.json'),plan=read('experiments/records/lp2-panel-prime-openings/plan.json'),historical=read('experiments/records/lp2-panel-prime-openings/results.json'),audit=read('published-evidence/programs/panel-prime-historical-audit.json'),lookup=new Map(bundle.alphabet.map((r,i)=>[r.rune,i])),requests=[];
const fetcher=async(url,options)=>{assert(url.startsWith('https://jelliottdev.github.io/published-evidence/programs/'));assert.equal(options.redirect,'manual');requests.push(url);const bytes=readFileSync(new URL('../'+url.slice('https://jelliottdev.github.io/'.length),import.meta.url));return new Response(bytes,{headers:{'content-type':'application/json','content-length':String(bytes.length)}});};
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('default catalog preserves all42 immutable known-key pointers and adds exactly32 separate panel pointers',async()=>{
 assert.equal(old.entries.length,42);assert.equal(panel.entries.length,32);assert.equal(catalog.entries.length,74);assert.deepEqual(await publishedProgramIndex(),catalog);
 for(const index of [old,panel])for(const item of index.entries)assert.deepEqual(catalog.entries.find(c=>c.recordId===item.recordId&&c.revision===item.revision&&c.caseId===item.caseId),item);
 const before=requests.length,run=E.run;E.run=()=>assert.fail('Catalog lookup cannot execute source programs');try{
  const original=old.entries[0],receipt=await readPublishedEvidence({...original,fetcher});assert.equal(receipt.task.taskId,original.taskId);assert.equal(receipt.run.id,original.resultId);assert.equal(requests.length,before+1);
  const item=panel.entries[0],found=await readPublishedEvidence({...item,fetcher});assert.equal(found.task.taskId,item.taskId);assert.equal(requests.length,before+2,'Only the selected providers\' receipts are fetched');assert.equal((await resolvePublishedEvidence({...item,fetcher})).source.run.id,item.resultId);assert.equal(requests.length,before+2,'Pinned receipt cache is reused');
 }finally{E.run=run;}
});
await test('all32 complete panel receipts retain1760 archived arrays,32 explicitly structural empty outputs, and all9 historical checks',async()=>{
 assert.equal(hash(readFileSync(new URL('../experiments/records/lp2-panel-prime-openings/results.json',import.meta.url))),'d78bc73a0fabe0a70937ae3ab787b6160c9481935b1627a8281e5e6147787d50');assert.deepEqual(audit.openings,plan.openings);assert.equal(audit.caseCount,1760);assert.equal(audit.comparisonCount,15840);assert.equal(audit.projectedCaseCount,1792);assert.equal(audit.structuralEmptyInputCaseCount,32);assert.match(audit.emptyInputMeaning,/not historical runs/);assert.equal(audit.projectedCriterion,'warning');assert.match(audit.otherOpeningEvaluations,/other eight.*Warning only/);
 const cases=new Map(historical.cases.map(c=>[[c.page,c.offset,c.sign].join('|'),c])),seen=new Set();let nonempty=0,empty=0,comparisons=0;
 const run=E.run;E.run=()=>assert.fail('Auditing imported outputs cannot construct target calculations');try{for(const item of panel.entries){
  const bytes=readFileSync(new URL('../'+item.path,import.meta.url));assert.equal(bytes.length,item.bytes);assert.equal(hash(bytes),item.sha256);const file=JSON.parse(bytes),raw=file.entries[0],provenance=file.records[0].provenance,receipt=await readPublishedEvidence({...item,fetcher});assert.equal(hash(provenance),item.revision);assert.equal(hash(raw.run.result),item.resultId);assert.equal(provenance.projection.sourceProgramId,provenance.projection.id);assert(!Object.hasOwn(provenance.projection,'followupId'));assert(provenance.sourcePins.some(p=>p.path==='published-evidence/programs/panel-prime-historical-audit.json'&&p.sha256===hash(readFileSync(new URL('../'+p.path,import.meta.url)))));
  assert.deepEqual(receipt.task.criterion,{kind:'exact-prefix',values:plan.openings.find(o=>o.id==='warning').indices});assert.equal(receipt.task.pages.length,56);const step=receipt.task.steps[0],sign=step.direction==='subtract'?-1:1,key=plan.key.map(n=>n%29),offset=plan.offsets.find(n=>E.stable(key.slice(n).concat(key.slice(0,n)))===E.stable(step.key));assert(Number.isInteger(offset));assert(!seen.has(offset+'|'+sign));seen.add(offset+'|'+sign);assert.equal(step.reset,'page');
  for(const page of receipt.task.pages){assert.equal(page.text,bundle.pages.find(p=>p.id===page.id).raw);const out=receipt.run.result.transformed.find(o=>o.page===page.id),values=Array.from(out.text).filter(c=>lookup.has(c)).map(c=>lookup.get(c));assert.equal(Array.from(out.text).filter(c=>!lookup.has(c)).join(''),Array.from(page.text).filter(c=>!lookup.has(c)).join(''));
   if(page.id==='lp2-50'){assert.deepEqual(values,[]);assert.equal(out.text,page.text);assert(!cases.has([page.id,offset,sign].join('|')));empty++;continue;}
   const prior=cases.get([page.id,offset,sign].join('|'));assert.deepEqual(values,prior.output_indices);const input=Array.from(page.text).filter(c=>lookup.has(c)).map(c=>lookup.get(c));assert(values.every((v,i)=>((v-sign*plan.key[(i+offset)%16])%29+29)%29===input[i]));assert.deepEqual(prior.matching_openings,plan.openings.filter(o=>o.indices.every((v,i)=>values[i]===v)).map(o=>o.id));nonempty++;comparisons+=9;
  }
 }}finally{E.run=run;}
 assert.equal(seen.size,32);assert.equal(nonempty,1760);assert.equal(empty,32);assert.equal(comparisons,15840);
});
await test('actual browser inspection and pinned language scans reuse all1792 cases with SELECT-only storage and no target engine runs',async()=>{
 const sql=new DatabaseSync(':memory:'),dir=new URL('../services/idea-assistant/migrations/',import.meta.url);for(const name of readdirSync(dir).filter(n=>/^\d{4}_.*\.sql$/.test(n)).sort())sql.exec(readFileSync(new URL(name,dir),'utf8'));
 const db={prepare(text){assert(/^\s*SELECT\b/i.test(text),'Evidence discovery cannot write');return{bind(...args){return{first:async()=>sql.prepare(text).get(...args)||null,all:async()=>({results:sql.prepare(text).all(...args)})};}};}},programs=panel.entries.map(item=>({steps:item.steps})),pages=panel.entries[0].pages.map(p=>({id:p.id,text:bundle.pages.find(q=>q.id===p.id).raw})),run=E.run;E.run=()=>assert.fail('Read-only reuse cannot execute target transformations');
 try{for(const language of [false,true]){
  const criterion=language?Evaluation.criterion():{kind:'measurement'},domain=await(language?Q.bindLanguageComparison:Q.bindOutputInspection)({engine:E.ENGINE,inputVersion:'raw',alphabet:bundle.alphabet,pages,criterion,programs}),options={db,proposalId:'p_'+'d'.repeat(64),domain,inputVersion:'raw',cursorKey:'Private panel catalog test snapshot signing key',now:Date.parse('2026-10-25T12:00:00.000Z'),fetcher},wire=[],scan=(language?Client.createOutputScan:Client.createInspectionScan)({proposalId:options.proposalId,domain,crypto:webcrypto,fetchPage:async body=>{const value=await(language?readFactoredOutputEvidencePage:readFactoredInspectionEvidencePage)({...options,...body});wire.push(value);return value;}});
  let state;do{state=await scan.step();}while(state.status!=='complete');assert.equal(state.proof.totalCases,1792);assert.equal(state.proof.coveredCases,1792);assert.equal(state.proof.remainingCases,0);assert.equal(state.proof.directCases,0);assert.equal(state.proof.derivedCases,1792);assert.equal(state.proof.decision.answer,language?'comparisons-complete':'outputs-ready');assert.equal(state.proof[language?'usableCases':'runeOutputCases'],1760);assert.equal(state.proof[language?'insufficientCases':'noRuneCases'],32);assert.equal(wire.flatMap(p=>p.sources).length,32);assert(wire.every(p=>p.sources.length<=12));assert(wire.flatMap(p=>p.sources).every(s=>s.task.criterion.kind==='exact-prefix'));assert(!wire.some(p=>Object.hasOwn(p,'usableCases')),'Browser independently evaluates language comparisons');await(language?verifyFactoredOutputSnapshot:verifyFactoredInspectionSnapshot)({...options,snapshotToken:wire.at(-1).snapshotToken});
 }
 for(const table of ['local_tasks','local_task_results','proposals'])assert.equal(sql.prepare('SELECT count(*) n FROM '+table).get().n,0);
 }finally{E.run=run;sql.close();}
});
console.log(groups+' panel catalog integration groups passed; historical outcomes retained, no public writes or new target calculations.');
