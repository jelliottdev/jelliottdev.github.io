/* Factored complete finite questions. Ordinary tasks exist only for selected cases.
 * Accumulators retain original receipt references, not a second copy of their outputs.
 * Original receipt bodies must remain available from the caller for an offline audit. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,R=node?require('./computation-evidence.js'):root.ComputationEvidence,J=node?require('./finite-json.js'):root.FiniteJSON;
 const domains=new WeakSet(),accumulators=new WeakMap(),proofs=new WeakSet(),preparedAccepts=new WeakMap(),HEX=/^[a-f0-9]{64}$/,LIMITS=Object.freeze({programs:1024,pages:75,cases:76800,domainBytes:4*1024*1024,chunkBytes:8*1024*1024,chunkSources:12,memoBytes:8*1024*1024});
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const capture=(v,maxBytes=LIMITS.domainBytes)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000});
 const hash=async(v,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
 async function bitmapHash(positions,total,crypto){const bits=new Uint8Array(Math.ceil(total/8));for(const position of positions)bits[position>>3]|=1<<(position&7);return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bits))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 const protocol=(d,steps)=>({schema:'liberpedia-computation-protocol-v1',engine:d.engine,inputVersion:d.inputVersion,alphabet:d.alphabet,steps,criterion:d.criterion});
 function inspect(domain){if(!domains.has(domain))throw Error('Use a bound factored finite question.');return domain;}
 async function bind(options,crypto=root.crypto){
  const v=capture(options);if(!exact(v,['engine','inputVersion','alphabet','pages','criterion','programs'])||v.engine!==E.ENGINE||!['raw','reviewed'].includes(v.inputVersion)||!Array.isArray(v.pages)||!v.pages.length||v.pages.length>LIMITS.pages||!Array.isArray(v.programs)||!v.programs.length||v.programs.length>LIMITS.programs||v.criterion?.kind!=='exact-prefix')throw Error('Declare exact common inputs, an opening and bounded programs.');
  const pages=v.pages.slice().sort((a,b)=>a.id.localeCompare(b.id));
  // Validate shared geometry once and each program through the maintained engine.
  const shared=await E.prepare({title:'Validate shared finite inputs',pages,alphabet:v.alphabet,steps:[],criterion:v.criterion},crypto),programs=[],seen=new Set();
  for(const input of v.programs){if(!exact(input,Object.hasOwn(input||{},'id')?['id','steps']:['steps']))throw Error('A program needs only its exact ordered steps and optional identity.');
   const task=await E.prepare({title:'Validate finite program',pages:[pages[0]],alphabet:shared.alphabet,steps:input.steps,criterion:shared.criterion},crypto);
   // Finite key lengths and reset segments depend on every declared page. Reuse
   // the maintained validator with shared references, without retaining or
   // hashing a repeated full-input task for each program.
   E.validateTask({...task,pages:shared.pages});const id=await hash(protocol(v,task.steps),crypto);
   if(Object.hasOwn(input,'id')&&input.id!==id||seen.has(id))throw Error('Duplicate or changed computation protocol.');seen.add(id);programs.push({id,steps:task.steps});
  }
  programs.sort((a,b)=>a.id.localeCompare(b.id));const body={schema:'liberpedia-factored-finite-question-v2',engine:v.engine,inputVersion:v.inputVersion,alphabet:shared.alphabet,pages:shared.pages,criterion:shared.criterion,programs,totalCases:programs.length*pages.length};
  if(new TextEncoder().encode(E.stable({...body,id:'0'.repeat(64)})).byteLength>LIMITS.domainBytes)throw Error('The complete factored domain exceeds its metadata byte bound.');
  const domain=freeze({...body,id:await hash(body,crypto)});domains.add(domain);return domain;
 }
 function paging(options,total){const v=capture(options,256);if(!exact(v,['cursor','limit'])||!Number.isSafeInteger(v.cursor)||v.cursor<0||v.cursor>total||!Number.isSafeInteger(v.limit)||v.limit<1||v.limit>12)throw Error('Use a bounded case cursor and limit.');return v;}
 async function refAt(domain,position,crypto){const p=domain.programs[Math.floor(position/domain.pages.length)],page=domain.pages[position%domain.pages.length];return {id:await hash({protocolId:p.id,page},crypto),programId:p.id,pageId:page.id};}
 async function cases(domain,options={cursor:0,limit:12},crypto=root.crypto){inspect(domain);const {cursor,limit}=paging(options,domain.totalCases),out=[];for(let n=cursor;n<Math.min(cursor+limit,domain.totalCases);n++)out.push(await refAt(domain,n,crypto));return freeze({cases:out,nextCursor:cursor+out.length<domain.totalCases?cursor+out.length:null});}
 async function select(domain,refs,crypto=root.crypto){
  inspect(domain);refs=capture(refs,8192);if(!Array.isArray(refs)||!refs.length||refs.length>12)throw Error('Select one to twelve declared cases.');const selected=[],seen=new Set();
  for(const ref of refs){if(!exact(ref,Object.hasOwn(ref||{},'id')?['id','programId','pageId']:['programId','pageId']))throw Error('Give the exact program and page address.');const pi=domain.programs.findIndex(p=>p.id===ref.programId),page=domain.pages.find(p=>p.id===ref.pageId);if(pi<0||!page)throw Error('Selected case is outside the declared domain.');const id=await hash({protocolId:ref.programId,page},crypto);if(Object.hasOwn(ref,'id')&&ref.id!==id||seen.has(id))throw Error('Duplicate or changed case identity.');seen.add(id);selected.push({id,programId:ref.programId,pageId:page.id,task:await E.prepare({title:'Finite program '+ref.programId,pages:[page],alphabet:domain.alphabet,steps:domain.programs[pi].steps,criterion:domain.criterion},crypto)});}
  selected.sort((a,b)=>a.programId.localeCompare(b.programId)||a.pageId.localeCompare(b.pageId));return freeze({domainId:domain.id,cases:selected});
 }
 function createAccumulator(domain,crypto=root.crypto){inspect(domain);const token=Object.freeze({});accumulators.set(token,{domain,crypto,owners:new Map(),matches:new Set(),receipts:new Map(),receiptKeys:null,memo:new Map(),memoBytes:0});return token;}
 function state(token){const s=accumulators.get(token);if(!s)throw Error('Use a private factored evidence accumulator.');return s;}
 async function prepareAccept(token,sources){
  const s=state(token),d=s.domain,inputs=capture(sources,LIMITS.chunkBytes);if(!Array.isArray(inputs)||inputs.length>LIMITS.chunkSources)throw Error('Supply at most twelve bounded original receipts.');
  const programs=new Map(d.programs.map((p,i)=>[p.id,i])),pages=new Map(d.pages.map((p,i)=>[p.id,{page:p,index:i}])),staged=[],memo=[];
  for(const source of inputs){if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result']))throw Error('Use complete original computation receipts.');const descriptor=await R.describe(source.task,source.inputVersion,s.crypto),pi=programs.get(descriptor.protocolId);
   if(pi===undefined||source.inputVersion!==d.inputVersion)continue;
   // Envelope, full task/result hashes and original page geometry are checked on every chunk.
   await R.compare(source.task,source.inputVersion,[source],s.crypto);
   const positions=[];for(const page of source.task.pages){const target=pages.get(page.id);if(target&&target.page.text===page.text)positions.push({position:pi*d.pages.length+target.index,pageId:page.id});}if(!positions.length)continue;
   const memoKey=source.task.taskId+'--'+source.run.id,signature=E.stable([source.task,source.run.result]),cached=s.memo.get(memoKey);
   if(cached!==undefined&&cached!==signature)throw Error('Conflicting bytes for one computation identity.');
   const result=cached===signature?source.run.result:await E.verify(source.task,source.run.result,s.crypto);
   if(cached!==signature)memo.push({key:memoKey,signature});
   const reference={taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt},key=E.stable(reference);
   staged.push({key,reference,programId:descriptor.protocolId,positions:positions.map(p=>({...p,matched:result.matches.find(m=>m.page===p.pageId).matched}))});
  }
  // Preparing never changes coverage, provenance or the replay cache. The caller
  // can stage these original receipts before committing any visible evidence.
  const pending=Object.freeze({});preparedAccepts.set(pending,{token,staged,memo});return pending;
 }
 function inspectPrepared(pending){const saved=preparedAccepts.get(pending);if(!saved)throw Error('Use an uncommitted independently prepared evidence chunk.');return freeze({domainId:state(saved.token).domain.id,acceptedSources:saved.staged.length});}
 function commitAccept(token,pending){
  const s=state(token),saved=preparedAccepts.get(pending);if(!saved||saved.token!==token)throw Error('The prepared evidence belongs to another accumulator or was already committed.');
  const {staged,memo}=saved;
  for(const item of memo){const existing=s.memo.get(item.key);if(existing!==undefined&&existing!==item.signature)throw Error('Conflicting bytes for one computation identity.');}
  preparedAccepts.delete(pending);
  for(const item of memo)if(!s.memo.has(item.key)){const size=new TextEncoder().encode(item.signature).byteLength+item.key.length+128;if(s.memoBytes+size<=LIMITS.memoBytes){s.memo.set(item.key,item.signature);s.memoBytes+=size;}}
  for(const item of staged)for(const p of item.positions){const old=s.owners.get(p.position);if(old&&old.localeCompare(item.key)<=0)continue;
   if(old){const receipt=s.receipts.get(old);receipt.positions.delete(p.position);if(!receipt.positions.size){s.receipts.delete(old);s.receiptKeys=null;}}
   if(!s.receipts.has(item.key)){s.receipts.set(item.key,{reference:item.reference,programId:item.programId,positions:new Set()});s.receiptKeys=null;}s.receipts.get(item.key).positions.add(p.position);s.owners.set(p.position,item.key);if(p.matched)s.matches.add(p.position);
  }
  return freeze({acceptedSources:staged.length,coveredCases:s.owners.size,matchingCases:s.matches.size});
 }
 async function accept(token,sources){return commitAccept(token,await prepareAccept(token,sources));}
 async function summarize(token,options={lookupComplete:false}){
  const s=state(token),d=s.domain,v=capture(options,100);if(!exact(v,['lookupComplete'])||typeof v.lookupComplete!=='boolean')throw Error('Declare whether the complete source lookup finished.');
  const covered=new Set(s.owners.keys()),matched=new Set(s.matches),matching=matched.size,nextCases=[];if(!matching&&covered.size<d.totalCases&&v.lookupComplete)for(let n=0;n<d.totalCases&&nextCases.length<12;n++)if(!covered.has(n))nextCases.push(await refAt(d,n,s.crypto));
  const complete=covered.size===d.totalCases,decision=matching?{state:'answered',answer:'prefix-found'}:complete?{state:'answered',answer:'prefix-not-found'}:v.lookupComplete?{state:'missing-evidence'}:{state:'unavailable'};
  const coverageSha256=await bitmapHash(covered,d.totalCases,s.crypto),matchingSha256=await bitmapHash(matched,d.totalCases,s.crypto);
  const proof=freeze({schema:'liberpedia-factored-finite-evidence-v2',domainId:d.id,totalCases:d.totalCases,coveredCases:covered.size,matchingCases:matching,remainingCases:d.totalCases-covered.size,coverageSha256,matchingSha256,lookupComplete:v.lookupComplete,complete,nextCases,decision});proofs.add(proof);return proof;
 }
 function inspectEvidence(proof){if(!proofs.has(proof))throw Error('Use independently verified factored evidence.');return proof;}
 async function coverage(token,refs){
  const s=state(token),selected=await select(s.domain,refs,s.crypto),coveredCaseIds=[],missingCaseIds=[],matchingCaseIds=[];
  for(const item of selected.cases){const pi=s.domain.programs.findIndex(p=>p.id===item.programId),pageIndex=s.domain.pages.findIndex(p=>p.id===item.pageId),position=pi*s.domain.pages.length+pageIndex;
   (s.owners.has(position)?coveredCaseIds:missingCaseIds).push(item.id);if(s.matches.has(position))matchingCaseIds.push(item.id);
  }
  return freeze({domainId:s.domain.id,coveredCaseIds,missingCaseIds,matchingCaseIds});
 }
 function evidence(token,options={cursor:0,limit:12}){const s=state(token),keys=s.receiptKeys||(s.receiptKeys=[...s.receipts.keys()].sort()),{cursor,limit}=paging(options,keys.length),out=keys.slice(cursor,cursor+limit).map(key=>{const r=s.receipts.get(key);return {...r.reference,programId:r.programId,pageIds:[...r.positions].sort((a,b)=>a-b).map(n=>s.domain.pages[n%s.domain.pages.length].id)};});return freeze({sources:out,nextCursor:cursor+out.length<keys.length?cursor+out.length:null});}
 const api={bind,inspect,cases,select,createAccumulator,prepareAccept,inspectPrepared,commitAccept,accept,summarize,inspectEvidence,coverage,evidence,LIMITS};if(node)module.exports=api;else root.FactoredFiniteQuestion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
