/* Streaming local audit staging. No network, admission or missing-case execution.
 * A failed build may leave staging chunks; callers must discard that staging.
 * Only a completed branded manifest describes a checked export. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,J=node?require('./finite-json.js'):root.FiniteJSON,Q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion,Compiler=node?require('./factored-finite-search-compiler.js'):root.FactoredFiniteSearchCompiler;
 const manifests=new WeakSet(),LIMITS=Object.freeze({manifestBytes:8*1024*1024,chunkBytes:8*1024*1024,totalBytes:512*1024*1024,sources:76800,chunkSources:12}),PROVENANCE='Supplied source identities and dates are retained unchanged. Replay verifies the computation, not authorship, publication, public availability or historical timing.',LOOKUP='The lookup status recorded when this snapshot was assembled. It is not an offline proof that no other public work exists.',LIMIT='Only these declared programs, the exact prefix and these pinned texts are covered. Missing cases are not covered by the packaged receipts; they are not established as new work. A matching opening is not a complete reading.';
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},capture=(v,maxBytes=LIMITS.manifestBytes)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000}),encode=v=>new TextEncoder().encode(E.stable(v));
 const digest=async(bytes,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
 async function build(options,crypto=root.crypto){
  if(!exact(options,['proposalId','card','bundle','domain','proof','sources','writeChunk']))throw Error('Provide the complete original question, verified proof and local chunk writer.');
  const domain=Q.inspect(options.domain),proof=Q.inspectEvidence(options.proof),proposalId=capture(options.proposalId,100),card=capture(options.card,H.MAX_BYTES),bundle=capture(options.bundle,2*1024*1024),sources=options.sources,writeChunk=options.writeChunk;
  if(proof.domainId!==domain.id||typeof proposalId!=='string'||!/^p_[a-f0-9]{64}$/.test(proposalId)||proposalId!=='p_'+await digest(new TextEncoder().encode(C.serialize(card)),crypto))throw Error('The original idea or evidence identity changed.');
  if(typeof writeChunk!=='function'||!sources||typeof sources[Symbol.asyncIterator]!=='function')throw Error('Use an asynchronous original-receipt stream and explicit local staging writer.');
  const compiled=await Compiler.compile(card,bundle,crypto);if(E.stable(compiled.domain)!==E.stable(domain))throw Error('The complete domain does not implement the original idea and pinned inputs.');
  const accumulator=Q.createAccumulator(domain,crypto),chunks=[],seen=new Set();let pending=[],pendingBytes=0,totalBytes=0,sourceCount=0;
  const emptyBytes=encode({schema:'liberpedia-original-receipt-chunk-v1',sources:[]}).byteLength;
  async function flush(){
   if(!pending.length)return;const chunk={schema:'liberpedia-original-receipt-chunk-v1',sources:pending},bytes=encode(chunk);if(bytes.byteLength>LIMITS.chunkBytes||totalBytes+bytes.byteLength>LIMITS.totalBytes)throw Error('The complete receipt export exceeds its byte bound.');
   const checked=await Q.accept(accumulator,pending);if(checked.acceptedSources!==pending.length)throw Error('An original receipt is outside the exact declared question.');
   const path='chunks/'+String(chunks.length+1).padStart(6,'0')+'.json',reference={path,sha256:await digest(bytes,crypto),bytes:bytes.byteLength,entries:pending.length};
   await writeChunk(path,bytes);chunks.push(reference);totalBytes+=bytes.byteLength;pending=[];pendingBytes=0;
  }
  for await(const supplied of sources){
   if(++sourceCount>LIMITS.sources)throw Error('The complete export exceeds its original-receipt count bound.');
   const source=capture(supplied,LIMITS.chunkBytes);if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result']))throw Error('Preserve complete original computation receipts.');
   const date=source.run.createdAt;if(typeof date!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(date)||!Number.isFinite(Date.parse(date))||new Date(date).toISOString()!==date)throw Error('Preserve a canonical original receipt date.');
   if(encode(source.task).byteLength>2000000||encode(source.run.result).byteLength>2000000)throw Error('An original task or result exceeds its maintained byte bound.');
   const key=E.stable([source.task.taskId,source.run.id,source.inputVersion,date]);if(seen.has(key))throw Error('The export repeats an original receipt.');seen.add(key);
   const size=encode(source).byteLength;if(emptyBytes+size>LIMITS.chunkBytes)throw Error('One whole original receipt exceeds its chunk bound.');
   if(pending.length&&(pending.length===LIMITS.chunkSources||emptyBytes+pendingBytes+size+pending.length>LIMITS.chunkBytes))await flush();
   pending.push(source);pendingBytes+=size;
  }
  await flush();
  const checked=await Q.summarize(accumulator,{lookupComplete:proof.lookupComplete});if(E.stable(checked)!==E.stable(proof))throw Error('The complete original receipt stream does not reproduce the supplied evidence.');
  const body={schema:'liberpedia-factored-finite-search-snapshot-v2',original:{proposalId,card},question:domain,evidence:{chunks,lookup:{recordedComplete:proof.lookupComplete,meaning:LOOKUP},provenanceMeaning:PROVENANCE},proof:{coveredCases:checked.coveredCases,matchingCases:checked.matchingCases,remainingCases:checked.remainingCases,complete:checked.complete,coverageSha256:checked.coverageSha256,matchingSha256:checked.matchingSha256},finding:{kind:checked.matchingCases?'prefix-found':checked.complete?'prefix-not-found':'incomplete',limit:LIMIT}};
  const output=capture({...body,snapshotId:await digest(encode(body),crypto)});freeze(output);manifests.add(output);return output;
 }
 function inspect(manifest){if(!manifests.has(manifest))throw Error('Use a completed independently checked factored snapshot.');return manifest;}
 const api={build,inspect,LIMITS,PROVENANCE,LOOKUP,LIMIT};if(node)module.exports=api;else root.FactoredFiniteSearchSnapshot=api;
})(typeof globalThis!=='undefined'?globalThis:this);
