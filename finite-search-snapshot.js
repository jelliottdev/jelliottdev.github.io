/* A detached audit snapshot of one verified finite question. No archive, I/O or execution authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,J=node?require('./finite-json.js'):root.FiniteJSON,Q=node?require('./finite-program-question.js'):root.FiniteProgramQuestion,Compiler=node?require('./finite-search-compiler.js'):root.FiniteSearchCompiler;
 const snapshots=new WeakSet(),MAX=8*1024*1024,HEX=/^[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable);
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const copy=v=>J.capture(v,{maxBytes:MAX,maxDepth:24,maxNodes:500000});
 async function hash(v,cryptoAPI,serialize=E.stable){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(serialize(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 const sourceKey=s=>E.stable([s.task.taskId,s.run.id,s.run.createdAt]);
 // Ordinary receipts alone cannot attest a published-record or family-source
 // association. Those destinations need their typed provider proof in a later
 // schema; v1 accepts only the exact computation's own direct location.
 function validLink(link){return exact(link,['taskId','href','label'])&&HEX.test(link.taskId)&&typeof link.label==='string'&&link.label.trim().length>0&&link.label.length<=300&&link.href==='run.html#task='+link.taskId;}
 async function build(options,cryptoAPI=root.crypto){
  const keys=['proposalId','card','bundle','domain','proof','sources',...(options&&Object.hasOwn(options,'sourceLinks')?['sourceLinks']:[])];
  if(!exact(options,keys))throw Error('A snapshot needs the original idea, bound question and actual receipt sources.');
  const domain=Q.inspect(options.domain),proof=Q.inspectEvidence(options.proof);
  if(proof.domainId!==domain.id)throw Error('The evidence belongs to another finite question.');
  // Snapshot caller data before the first asynchronous digest. Branded domain
  // and proof are already deeply immutable; never serialize untrusted hooks.
  const proposalId=J.capture(options.proposalId,{maxBytes:100,maxNodes:1}),card=J.capture(options.card,{maxBytes:H.MAX_BYTES,maxDepth:16,maxNodes:6000}),bundle=J.capture(options.bundle,{maxBytes:Compiler.LIMITS.sourceBytes,maxDepth:16,maxNodes:6000}),sources=copy(options.sources),links=copy(options.sourceLinks||[]);
  if(!/^p_[a-f0-9]{64}$/.test(proposalId)||proposalId!=='p_'+await hash(card,cryptoAPI,C.serialize))throw Error('The original canonical idea identity does not match.');
  const compiled=await Compiler.compile(card,bundle,cryptoAPI);
  if(compiled.domain.id!==domain.id||E.stable(compiled.domain)!==E.stable(domain))throw Error('The finite domain does not implement this original declared idea and pinned inputs.');
  const checked=await Q.summarize(domain,sources,{lookupComplete:proof.lookupComplete},cryptoAPI);
  if(E.stable(checked)!==E.stable(proof))throw Error('The supplied receipts do not reproduce the complete evidence snapshot.');
  if(!Array.isArray(links)||links.length>4096||links.some(link=>!validLink(link)||!sources.some(source=>source.task.taskId===link.taskId)))throw Error('Snapshot v1 links must point directly to the same source task. Published and family locations need their independently verified provider provenance.');
  const available=new Map(sources.map(source=>[sourceKey(source),source])),selected=new Map();
  for(const ref of checked.evidence){const key=E.stable([ref.taskId,ref.resultId,ref.createdAt]),source=available.get(key);if(!source)throw Error('An original evidence receipt is missing.');selected.set(key,source);}
  const tasks=new Map(),results=new Map(),references=[];
  for(const [key,source] of [...selected.entries()].sort((a,b)=>a[0].localeCompare(b[0]))){
   if(tasks.has(source.task.taskId)&&E.stable(tasks.get(source.task.taskId))!==E.stable(source.task))throw Error('One source task identity has conflicting bytes.');
   if(results.has(source.run.id)&&E.stable(results.get(source.run.id))!==E.stable(source.run.result))throw Error('One source result identity has conflicting bytes.');
   tasks.set(source.task.taskId,source.task);results.set(source.run.id,source.run.result);references.push({taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt});
  }
  const sourceLinks=[],seenLinks=new Set();for(const link of links.filter(link=>tasks.has(link.taskId)).sort((a,b)=>E.stable(a).localeCompare(E.stable(b)))){const key=E.stable(link);if(seenLinks.has(key))throw Error('The snapshot repeats a source link.');seenLinks.add(key);sourceLinks.push(link);}
  const shared=domain.programs[0].task,body={schema:'liberpedia-finite-search-snapshot-v1',original:{proposalId,card},question:{domainId:domain.id,engine:shared.engine,inputVersion:domain.inputVersion,alphabet:shared.alphabet,pages:shared.pages,criterion:shared.criterion,programs:domain.programs.map(program=>({id:program.id,steps:program.task.steps})),cases:domain.cases,totalCases:domain.totalCases},evidence:{provenanceMeaning:'Supplied source identities and dates are retained unchanged. Replay verifies the computation, not authorship, publication, public availability or historical timing.',tasks:[...tasks].sort((a,b)=>a[0].localeCompare(b[0])).map(([id,task])=>({id,task})),results:[...results].sort((a,b)=>a[0].localeCompare(b[0])).map(([id,result])=>({id,result})),sources:references,caseSources:checked.evidence,sourceLocations:sourceLinks,coveredCaseIds:checked.coveredCaseIds,matchingCaseIds:checked.matchingCaseIds,missingCaseIds:checked.missingCaseIds,lookup:{recordedComplete:checked.lookupComplete,meaning:'The lookup status recorded when this snapshot was assembled. It is not an offline proof that no other public work exists.'}},finding:{kind:checked.matchingCaseIds.length&&(checked.complete||shared.criterion.kind!=='exact-prefix-set')?'prefix-found':checked.complete?'prefix-not-found':'incomplete',limit:'Only these declared programs, the exact prefix and these pinned texts are covered. Missing cases are not covered by the packaged receipts; they are not established as new work. A matching opening is not a complete reading.'}};
  const detached=copy(body),snapshotId=await hash(detached,cryptoAPI),output=copy({...detached,snapshotId});freeze(output);snapshots.add(output);return output;
 }
 function inspect(snapshot){if(!snapshots.has(snapshot))throw Error('Use an independently verified finite search snapshot.');return snapshot;}
 const api={build,inspect,MAX_BYTES:MAX};if(node)module.exports=api;else root.FiniteSearchSnapshot=api;
})(typeof globalThis!=='undefined'?globalThis:this);
