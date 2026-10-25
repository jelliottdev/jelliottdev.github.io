/* Isolated derived-opening preparation. It creates neither target receipts nor
 * public coverage. Original task/result bodies remain owned by the caller. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,Q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion,P=node?require('./verified-prefix-evaluation.js'):root.VerifiedPrefixEvaluation,J=node?require('./finite-json.js'):root.FiniteJSON;
 const prepared=new WeakMap(),LIMITS=Object.freeze({sources:12,sourceBytes:8*1024*1024,metadataBytes:2*1024*1024,claims:900});
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},capture=(v,maxBytes)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000});
 const programKey=(engine,alphabet,steps)=>E.stable({engine,alphabet,steps}),referenceKey=v=>E.stable([v.taskId,v.resultId,v.createdAt,v.inputVersion]);
 function inspect(token){const value=prepared.get(token);if(!value)throw Error('Use independently prepared derived-opening claims.');return value;}
 async function prepare(domain,suppliedSources,crypto=root.crypto){
  const d=Q.inspect(domain),sources=capture(suppliedSources,LIMITS.sourceBytes);if(!Array.isArray(sources)||sources.length>LIMITS.sources)throw Error('Use at most twelve bounded original computation receipts.');
  const programs=new Map(d.programs.map(p=>[programKey(d.engine,d.alphabet,p.steps),p])),pages=new Map(d.pages.map(p=>[p.id,p.text])),groups=new Map();
  // Admission is strict for this already-selected candidate primitive. An
  // unrelated source cannot be silently dropped from an otherwise valid chunk.
  for(const source of sources){if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result'])||source.inputVersion!==d.inputVersion)throw Error('An original source has a different envelope or text edition.');E.validateTask(source.task);if(!['measurement','exact-prefix'].includes(source.task.criterion.kind))throw Error('Only original measurement and exact-prefix outputs support this derivation.');const program=programs.get(programKey(source.task.engine,source.task.alphabet,source.task.steps));const intersections=source.task.pages.filter(p=>pages.get(p.id)===p.text);if(!program||!intersections.length)throw Error('An original source is outside the exact declared transformations and page bytes.');if(!groups.has(program.id))groups.set(program.id,{program,sources:[],pageIds:new Set()});const group=groups.get(program.id);group.sources.push(source);for(const page of intersections)group.pageIds.add(page.id);}
  const claims=new Map();
  for(const group of [...groups.values()].sort((a,b)=>a.program.id.localeCompare(b.program.id))){
   // The branded domain has already validated every declared page. This
   // transient evaluator target contains only this program's exact source
   // intersections, in domain order; its completeness is never domain coverage.
   const targetPages=d.pages.filter(page=>group.pageIds.has(page.id));
   const target=await E.prepare({title:'Derived opening check for program '+group.program.id,alphabet:d.alphabet,pages:targetPages,steps:group.program.steps,criterion:d.criterion},crypto);
   // Keep whole originals in packets bounded by the maintained evaluator's
   // total input limit. The exact intersection target is shared by each packet.
   // In particular, identical dated originals can use its local replay memo.
   const emptyBytes=new TextEncoder().encode(E.stable({task:target,inputVersion:d.inputVersion,sources:[]})).byteLength;let packet=[],packetBytes=emptyBytes;
   async function flush(){if(!packet.length)return;const proof=P.inspect(await P.evaluate({task:target,inputVersion:d.inputVersion,sources:packet},crypto)),expected=d.pages.filter(p=>packet.some(source=>source.task.pages.some(s=>s.id===p.id&&s.text===p.text))).map(p=>p.id);if(E.stable(proof.coveredPages)!==E.stable(expected))throw Error('The derived check changed its exact page intersection.');
    for(const page of proof.pages){const claim={programId:group.program.id,pageId:page.pageId,targetCaseId:page.targetCaseId,sourceCaseId:page.sourceCaseId,matched:page.matched,sourceCriterion:page.sourceCriterion,source:page.source},prior=claims.get(page.targetCaseId);if(prior&&prior.matched!==claim.matched)throw Error('Verified original outputs conflict on the same requested opening.');if(!prior||referenceKey(claim.source)<referenceKey(prior.source))claims.set(page.targetCaseId,claim);}packet=[];packetBytes=emptyBytes;
   }
   for(const source of group.sources){const bytes=new TextEncoder().encode(E.stable(source)).byteLength;if(emptyBytes+bytes>P.MAX_BYTES)throw Error('One whole original exceeds the bounded derived-evaluation input.');if(packet.length&&packetBytes+bytes+1>P.MAX_BYTES)await flush();packetBytes+=bytes+(packet.length?1:0);packet.push(source);}await flush();
  }
  const ordered=[...claims.values()].sort((a,b)=>a.programId.localeCompare(b.programId)||a.pageId.localeCompare(b.pageId));if(ordered.length>LIMITS.claims)throw Error('Derived claim metadata exceeds its bound.');const metadata=freeze(capture({schema:'liberpedia-factored-prefix-reuse-v1',domainId:d.id,sourceCount:sources.length,claims:ordered},LIMITS.metadataBytes)),token=Object.freeze({});prepared.set(token,metadata);return token;
 }
 const api={prepare,inspect,LIMITS};if(node)module.exports=api;else root.FactoredPrefixReuse=api;
})(typeof globalThis!=='undefined'?globalThis:this);
