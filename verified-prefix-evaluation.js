/* Read-only prefix evaluation from fully verified original outputs. No target receipt is created. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,Relations=node?require('./computation-evidence.js'):root.ComputationEvidence,J=node?require('./finite-json.js'):root.FiniteJSON;
 const proofs=new WeakSet(),MAX_BYTES=8*1024*1024,MAX_SOURCES=75,HEX=/^[a-f0-9]{64}$/;
 const exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable);
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 const capture=v=>J.capture(v,{maxBytes:MAX_BYTES,maxDepth:24,maxNodes:500000});
 async function hash(value,cryptoAPI){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 const sourceKey=s=>E.stable([s.task.taskId,s.run.id,s.run.createdAt]);
 function inspect(proof){if(!proofs.has(proof))throw Error('Prefix evidence must be independently verified before use.');return proof;}
 async function evaluate(options,cryptoAPI=root.crypto){
  const input=capture(options);if(!exact(input,['task','inputVersion','sources'])||!['raw','reviewed'].includes(input.inputVersion)||!Array.isArray(input.sources)||input.sources.length>MAX_SOURCES)throw Error('A derived prefix check needs one explicit task and at most 75 original receipts.');
  const {task,inputVersion,sources}=input;await E.checkIdentity(task,cryptoAPI);
  if(task.criterion.kind!=='exact-prefix')throw Error('The requested evaluation must be an exact prefix.');
  const targetDescription=await Relations.describe(task,inputVersion,cryptoAPI),targetCases=new Map(targetDescription.pages.map(p=>[p.id,p.caseId])),targetPages=new Map(task.pages.map(p=>[p.id,p.text])),program=E.stable({engine:task.engine,alphabet:task.alphabet,steps:task.steps}),runes=new Map(task.alphabet.map((r,i)=>[r.rune,i])),claims=new Map(),verifiedSources=new Map(),replayed=new Map();
  for(const source of sources){
   if(!exact(source,['task','inputVersion','run'])||!['raw','reviewed'].includes(source.inputVersion)||!exact(source.run,['id','createdAt','result'])||!HEX.test(source.run.id)||typeof source.run.createdAt!=='string'||!Number.isFinite(Date.parse(source.run.createdAt)))throw Error('Use a complete original computation receipt.');
   if(!['measurement','exact-prefix'].includes(source.task?.criterion?.kind))throw Error('Only measurement and exact-prefix source evaluations are supported in this derivation.');
   await E.checkIdentity(source.task,cryptoAPI);
   const key=sourceKey(source),prior=verifiedSources.get(key),replayKey=E.stable([source.task.taskId,source.run.id]),taskBytes=E.stable(source.task),resultBytes=E.stable(source.run.result),cached=replayed.get(replayKey);
   if(cached&&(cached.taskBytes!==taskBytes||cached.resultBytes!==resultBytes))throw Error('Conflicting bytes for the same original computation identity.');
   // Validate each dated original envelope, including duplicates. Reuse only a
   // full replay of identical captured task/result bytes within this call.
   await Relations.compare(source.task,source.inputVersion,[source],cryptoAPI);
   let result=cached?.result;
   if(!cached){result=await E.verify(source.task,source.run.result,cryptoAPI);if(await hash(result,cryptoAPI)!==source.run.id)throw Error('The original result digest changed.');replayed.set(replayKey,{taskBytes,resultBytes,result});}
   if(prior){if(E.stable(prior)!==E.stable(source))throw Error('Conflicting bytes for the same original receipt.');continue;}
   verifiedSources.set(key,{task:source.task,inputVersion:source.inputVersion,run:{...source.run,result}});
   if(source.inputVersion!==inputVersion||E.stable({engine:source.task.engine,alphabet:source.task.alphabet,steps:source.task.steps})!==program)continue;
   const description=await Relations.describe(source.task,source.inputVersion,cryptoAPI),sourceCases=new Map(description.pages.map(p=>[p.id,p.caseId]));
   for(const page of source.task.pages){
    if(targetPages.get(page.id)!==page.text)continue;
    const text=result.transformed.find(p=>p.page===page.id).text,values=Array.from(text).filter(ch=>runes.has(ch)).map(ch=>runes.get(ch)),matched=task.criterion.values.every((value,i)=>values[i]===value),signature=E.stable({text,matched}),old=claims.get(page.id);
    if(old&&old.signature!==signature)throw Error('Conflicting original outputs for the same exact transformation and page.');
    if(!old||key<old.key)claims.set(page.id,{key,signature,derived:{pageId:page.id,targetCaseId:targetCases.get(page.id),matched,sourceCriterion:source.task.criterion,sourceCaseId:sourceCases.get(page.id),source:{taskId:source.task.taskId,resultId:source.run.id,createdAt:source.run.createdAt,inputVersion:source.inputVersion}}});
   }
  }
  const pages=task.pages.filter(p=>claims.has(p.id)).map(p=>claims.get(p.id).derived),used=new Set(task.pages.filter(p=>claims.has(p.id)).map(p=>claims.get(p.id).key)),originalSources=[...verifiedSources].filter(([key])=>used.has(key)).sort((a,b)=>a[0].localeCompare(b[0])).map(([,source])=>source),coveredPages=pages.map(p=>p.pageId),matchingPages=pages.filter(p=>p.matched).map(p=>p.pageId),remainingPages=task.pages.filter(p=>!claims.has(p.id)).map(p=>p.id);
  const body={schema:'liberpedia-derived-prefix-evidence-v1',kind:'exact-prefix-from-verified-output-v1',requested:{taskId:task.taskId,inputVersion,criterion:task.criterion},coveredPages,remainingPages,matchingPages,complete:!remainingPages.length,pages,originalSources,limit:'The requested prefix is evaluated now from independently replayed original output. The original experiment is not claimed to have tested this prefix. No requested-task result receipt, public availability, historical attribution or current search completeness is established.'};
  const detached=capture(body),proof=freeze(capture({...detached,proofId:await hash(detached,cryptoAPI)}));proofs.add(proof);return proof;
 }
 const api={evaluate,inspect,MAX_BYTES,MAX_SOURCES};if(node)module.exports=api;else root.VerifiedPrefixEvaluation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
