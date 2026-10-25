/* Explicit finite alternatives of ordinary programs. No inference, lookup or admission. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,Relations=node?require('./computation-evidence.js'):root.ComputationEvidence,JSONData=node?require('./finite-json.js'):root.FiniteJSON;
 const domains=new WeakSet(),proofs=new WeakMap(),verificationMemos=new WeakMap(),MAX_PROGRAMS=1024,MAX_CASES=4096,MAX_BYTES=8*1024*1024,MAX_RUNE_WORK=2000000;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 async function hash(v,cryptoAPI){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function inspect(domain){if(!domains.has(domain))throw Error('Use a bound finite question domain.');return domain;}
 function createVerificationMemo(){const token=Object.freeze({});verificationMemos.set(token,{entries:new Map(),bytes:0,active:true});return token;}
 function clearVerificationMemo(token){const memo=verificationMemos.get(token);if(!memo)throw Error('Use an opaque finite verification memo.');memo.entries.clear();memo.bytes=0;memo.active=false;}
 function evidenceOptions(options){
  const keys=['lookupComplete','verificationMemo'].filter(key=>Object.hasOwn(options||{},key));
  if(!exact(options,keys))throw Error('Invalid finite evidence options.');
  const raw=Object.hasOwn(options,'verificationMemo')?Object.getOwnPropertyDescriptor(options,'verificationMemo').value:null,memo=raw===null?null:verificationMemos.get(raw);
  if(Object.hasOwn(options,'verificationMemo')&&(!memo||!memo.active))throw Error('Use an active opaque finite verification memo.');
  const descriptors=Object.getOwnPropertyDescriptors(options);delete descriptors.verificationMemo;
  const clean=JSONData.capture(Object.create(Object.getPrototypeOf(options),descriptors),{maxBytes:100,maxDepth:2,maxNodes:2});
  const lookupComplete=Object.hasOwn(clean,'lookupComplete')?clean.lookupComplete:true;
  if(typeof lookupComplete!=='boolean')throw Error('Invalid finite lookup status.');return {lookupComplete,memo};
 }
 async function bind(options,cryptoAPI=root.crypto){
  options=JSONData.capture(options,{maxBytes:MAX_BYTES,maxDepth:20,maxNodes:500000});
  if(!exact(options,['programs','inputVersion'])||!['raw','reviewed'].includes(options.inputVersion)||!Array.isArray(options.programs)||!options.programs.length||options.programs.length>MAX_PROGRAMS)throw Error('A finite question needs explicit programs and an input version.');
  const captured=options,programs=[],ids=new Set();let common=null;
  for(const input of captured.programs){
   await E.checkIdentity(input,cryptoAPI);
   if(input.criterion.kind!=='exact-prefix')throw Error('Finite questions currently require an exact prefix.');
   const pages=input.pages.slice().sort((a,b)=>a.id.localeCompare(b.id)),scope=E.stable({engine:input.engine,alphabet:input.alphabet,criterion:input.criterion,pages});
   if(common!==null&&scope!==common)throw Error('Every alternative must retain the same exact inputs and criterion.');common=scope;
   if(pages.length*captured.programs.length>MAX_CASES)throw Error('The finite question exceeds its case bound.');
   if(!programs.length){const names=new Set(input.alphabet.map(r=>r.rune)),runes=pages.reduce((n,p)=>n+Array.from(p.text).filter(ch=>names.has(ch)).length,0);if(runes*captured.programs.length>MAX_RUNE_WORK)throw Error('The finite question exceeds its rune-work bound.');}
   const described=await Relations.describe(input,captured.inputVersion,cryptoAPI);
   if(ids.has(described.protocolId))throw Error('Duplicate compiled alternatives are not separate programs.');ids.add(described.protocolId);
   const task=await E.prepare({title:'Finite program '+described.protocolId,pages,alphabet:input.alphabet,steps:input.steps,criterion:input.criterion},cryptoAPI);
   programs.push({id:described.protocolId,task});
  }
  programs.sort((a,b)=>a.id.localeCompare(b.id));const cases=[];
  for(const program of programs){const described=await Relations.describe(program.task,captured.inputVersion,cryptoAPI);for(const page of described.pages)cases.push({id:page.caseId,programId:program.id,pageId:page.id});}
  cases.sort((a,b)=>a.id.localeCompare(b.id));
  const id=await hash({schema:'liberpedia-finite-program-question-v1',inputVersion:captured.inputVersion,programIds:programs.map(p=>p.id),caseIds:cases.map(c=>c.id)},cryptoAPI);
  const domain=freeze({schema:'liberpedia-finite-program-question-v1',id,inputVersion:captured.inputVersion,programs,cases,totalCases:cases.length});domains.add(domain);return domain;
 }
 async function select(domain,caseIds,cryptoAPI=root.crypto){
  inspect(domain);caseIds=JSONData.capture(caseIds,{maxBytes:4096,maxDepth:2,maxNodes:13});if(!Array.isArray(caseIds)||!caseIds.length||caseIds.length>12||new Set(caseIds).size!==caseIds.length||caseIds.some(id=>typeof id!=='string'))throw Error('Select one to twelve distinct declared cases.');
  const wanted=new Set(caseIds),chosen=domain.cases.filter(item=>wanted.has(item.id));if(chosen.length!==caseIds.length)throw Error('The selected case is outside this domain.');
  const byProgram=new Map(domain.programs.map(p=>[p.id,p.task])),cases=[];
  for(const item of chosen){const original=byProgram.get(item.programId),task=await E.prepare({...original,pages:original.pages.filter(p=>p.id===item.pageId)},cryptoAPI);cases.push({...item,task});}
  return freeze({domainId:domain.id,cases});
 }
 async function summarize(domain,sources,options={},cryptoAPI=root.crypto){
  const {lookupComplete,memo}=evidenceOptions(options);
  inspect(domain);if(typeof lookupComplete!=='boolean'||!Array.isArray(sources)||sources.length>MAX_CASES)throw Error('Finite evidence needs bounded sources and a lookup status.');
  const captured=JSONData.capture(sources,{maxBytes:MAX_BYTES,maxDepth:20,maxNodes:500000}),programs=new Map(domain.programs.map(p=>[p.id,p.task])),caseIndex=new Map(domain.cases.map(c=>[c.programId+'--'+c.pageId,c])),claims=new Map(),receipts=new Set();
  for(const source of captured){
   if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result']))throw Error('Use ordinary immutable computation receipts.');
   const described=await Relations.describe(source.task,source.inputVersion,cryptoAPI),requested=programs.get(described.protocolId);if(!requested)continue;
   const comparison=await Relations.compare(requested,domain.inputVersion,[source],cryptoAPI);if(!comparison.coveredPages.length)continue;
   const receiptKey=source.task.taskId+'--'+source.run.id+'--'+source.run.createdAt;
   if(receipts.has(receiptKey))continue;receipts.add(receiptKey);
   // Relations validates full hashes/envelopes; execution independently checks
   // the actual transformation. A metadata flag alone never covers a case.
   // The lookup, original envelope/hash/criterion and exact page intersection
   // above remain fresh. Memoize only a successful independent replay of these
   // exact captured task/result bytes, never coverage or receipt provenance.
   const memoKey=source.task.taskId+'--'+source.run.id,signature=memo?E.stable([source.task,source.run.result]):null,cached=memo?.active?memo.entries.get(memoKey):null;
   if(cached!==undefined&&cached!==null&&cached!==signature)throw Error('Conflicting exact bytes for a memoized computation.');
   const verified=memo?.active&&typeof cached==='string'&&cached===signature?source.run.result:await E.verify(source.task,source.run.result,cryptoAPI);
   if(memo?.active&&cached!==signature){const size=new TextEncoder().encode(signature).byteLength+memoKey.length+128;if(memo.bytes+size<=MAX_BYTES){memo.entries.set(memoKey,signature);memo.bytes+=size;}}
   for(const pageId of comparison.coveredPages){
    const entry=caseIndex.get(described.protocolId+'--'+pageId),matched=verified.matches.find(m=>m.page===pageId).matched,text=verified.transformed.find(p=>p.page===pageId).text,value=E.stable({matched,text});
    const prior=claims.get(entry.id);if(prior&&prior.value!==value)throw Error('Conflicting verified evidence for the same finite case.');
    const provenance={caseId:entry.id,taskId:source.task.taskId,resultId:source.run.id,createdAt:source.run.createdAt,pageId},order=E.stable([provenance.taskId,provenance.resultId,provenance.createdAt]);
    if(!prior||order<prior.order)claims.set(entry.id,{matched,value,order,provenance});
   }
  }
  const coveredCaseIds=domain.cases.filter(c=>claims.has(c.id)).map(c=>c.id),missingCaseIds=domain.cases.filter(c=>!claims.has(c.id)).map(c=>c.id),matchingCaseIds=coveredCaseIds.filter(id=>claims.get(id).matched),evidence=coveredCaseIds.map(id=>claims.get(id).provenance);
  const proof=freeze({schema:'liberpedia-finite-program-evidence-v1',domainId:domain.id,totalCases:domain.totalCases,coveredCaseIds,missingCaseIds,matchingCaseIds,complete:!missingCaseIds.length,lookupComplete,evidence});proofs.set(proof,domain);return proof;
 }
 function inspectEvidence(proof){if(!proofs.has(proof))throw Error('Finite question evidence must be independently verified.');return proof;}
 function decision(proof){
  inspectEvidence(proof);const base={schema:'liberpedia-finite-program-decision-v1',domainId:proof.domainId,evidence:proof,limit:'Only these declared programs, this exact prefix and these pinned page texts are covered. A matching opening is not a complete reading; a failure does not reject the broader deciphering aim.'};
  if(proof.matchingCaseIds.length)return freeze({...base,state:'answered',answer:'prefix-found',next:{kind:'inspect-evidence',caseIds:proof.matchingCaseIds}});
  if(proof.complete)return freeze({...base,state:'answered',answer:'prefix-not-found',next:null});
  if(!proof.lookupComplete)return freeze({...base,state:'unavailable',answer:null,next:{kind:'retry-evidence'}});
  return freeze({...base,state:'missing-evidence',answer:null,next:{kind:'run-missing-evidence',caseIds:proof.missingCaseIds.slice(0,12)}});
 }
 const api={bind,inspect,select,summarize,inspectEvidence,decision,createVerificationMemo,clearVerificationMemo};if(node)module.exports=api;else root.FiniteProgramQuestion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
