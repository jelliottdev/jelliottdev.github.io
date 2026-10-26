/* Factored complete finite questions. Ordinary tasks exist only for selected cases.
 * Accumulators retain original receipt references, not a second copy of their outputs.
 * Original receipt bodies must remain available from the caller for an offline audit. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,R=node?require('./computation-evidence.js'):root.ComputationEvidence,J=node?require('./finite-json.js'):root.FiniteJSON;
 const domains=new WeakSet(),outputDomains=new WeakSet(),accumulators=new WeakMap(),proofs=new WeakSet(),preparedAccepts=new WeakMap(),HEX=/^[a-f0-9]{64}$/,LIMITS=Object.freeze({programs:1024,pages:75,cases:76800,domainBytes:4*1024*1024,chunkBytes:8*1024*1024,chunkSources:12,memoBytes:8*1024*1024});
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const capture=(v,maxBytes=LIMITS.domainBytes)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000});
 const hash=async(v,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
 async function bitmapHash(positions,total,crypto){const bits=new Uint8Array(Math.ceil(total/8));for(const position of positions)bits[position>>3]|=1<<(position&7);return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bits))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 const protocol=(d,steps)=>({schema:'liberpedia-computation-protocol-v1',engine:d.engine,inputVersion:d.inputVersion,alphabet:d.alphabet,steps,criterion:d.criterion});
 function inspect(domain){if(!domains.has(domain))throw Error('Use a bound factored finite question.');return domain;}
 const outputPolicy=()=>node?require('./finite-question-policy.js'):root.FiniteQuestionPolicy;
 async function bind(options,crypto=root.crypto){return bindDomain(options,crypto,false);}
 async function bindLanguageComparison(options,crypto=root.crypto){return bindDomain(options,crypto,'language-reference-comparison-v1');}
 async function bindOutputInspection(options,crypto=root.crypto){return bindDomain(options,crypto,'transformed-output-inspection-v1');}
 const profile=d=>d.questionPolicy==='transformed-output-inspection-v1'?{statuses:['rune-output','no-runes'],secondary:'no-runes',derivedKind:'derived-inspection',evidenceMode:'verified-output-inspection-v1',answer:'outputs-ready'}:{statuses:['compared','insufficient'],secondary:'insufficient',derivedKind:'derived-language',evidenceMode:'verified-output-language-v1',answer:'comparisons-complete'};
 async function bindDomain(options,crypto,output){
  const v=capture(options);if(!exact(v,['engine','inputVersion','alphabet','pages','criterion','programs'])||v.engine!==E.ENGINE||!['raw','reviewed'].includes(v.inputVersion)||!Array.isArray(v.pages)||!v.pages.length||v.pages.length>LIMITS.pages||!Array.isArray(v.programs)||!v.programs.length||v.programs.length>LIMITS.programs||(!output&&!['exact-prefix','exact-prefix-set'].includes(v.criterion?.kind)))throw Error('Declare exact common inputs, an opening and bounded programs.');
  if(output&&outputPolicy()?.describe(v.criterion).id!==output)throw Error('Declare the maintained pinned language comparison.');
  const pages=v.pages.slice().sort((a,b)=>a.id.localeCompare(b.id));
  // Validate shared geometry once and each program through the maintained engine.
  const shared=await E.prepare({title:'Validate shared finite inputs',pages,alphabet:v.alphabet,steps:[],criterion:v.criterion},crypto),programs=[],seen=new Set();
  const base={...shared,title:'Validate finite program',taskId:'0'.repeat(64)},baseBytes=new TextEncoder().encode(E.stable(base)).byteLength;
  for(const input of v.programs){if(!exact(input,Object.hasOwn(input||{},'id')?['id','steps']:['steps']))throw Error('A program needs only its exact ordered steps and optional identity.');
   // Every maintained transform preserves rune/separator geometry. Validate
   // ordinary program grammar on an empty page; only finite key sufficiency
   // depends on the complete real reset segments and needs that full geometry.
   const task={...base,steps:input.steps,pages:Array.isArray(input.steps)&&input.steps.some(step=>step?.op==='finite-shift')?shared.pages:[{id:pages[0].id,text:''}]};
   E.validateTask(task);
   // Restore the exact full-task byte bound without repeatedly serializing all
   // shared text. Only the steps array differs from the already checked base.
   if(baseBytes+new TextEncoder().encode(E.stable(task.steps)).byteLength-2>2000000)throw Error('The task exceeds the local runner file limit.');
   const id=await hash(protocol(v,task.steps),crypto);
   if(Object.hasOwn(input,'id')&&input.id!==id||seen.has(id))throw Error('Duplicate or changed computation protocol.');seen.add(id);programs.push({id,steps:task.steps});
  }
  programs.sort((a,b)=>a.id.localeCompare(b.id));const body={schema:output?'liberpedia-factored-finite-output-question-v1':'liberpedia-factored-finite-question-v2',...(output?{questionPolicy:output}:{}),engine:v.engine,inputVersion:v.inputVersion,alphabet:shared.alphabet,pages:shared.pages,criterion:shared.criterion,programs,totalCases:programs.length*pages.length};
  if(new TextEncoder().encode(E.stable({...body,id:'0'.repeat(64)})).byteLength>LIMITS.domainBytes)throw Error('The complete factored domain exceeds its metadata byte bound.');
  const domain=freeze({...body,id:await hash(body,crypto)});domains.add(domain);if(output)outputDomains.add(domain);return domain;
 }
 function paging(options,total){const v=capture(options,256);if(!exact(v,['cursor','limit'])||!Number.isSafeInteger(v.cursor)||v.cursor<0||v.cursor>total||!Number.isSafeInteger(v.limit)||v.limit<1||v.limit>12)throw Error('Use a bounded case cursor and limit.');return v;}
 async function refAt(domain,position,crypto){const p=domain.programs[Math.floor(position/domain.pages.length)],page=domain.pages[position%domain.pages.length];return {id:await hash({protocolId:p.id,page},crypto),programId:p.id,pageId:page.id};}
 async function cases(domain,options={cursor:0,limit:12},crypto=root.crypto){inspect(domain);const {cursor,limit}=paging(options,domain.totalCases),out=[];for(let n=cursor;n<Math.min(cursor+limit,domain.totalCases);n++)out.push(await refAt(domain,n,crypto));return freeze({cases:out,nextCursor:cursor+out.length<domain.totalCases?cursor+out.length:null});}
 async function resolveRefs(domain,refs,crypto){
  inspect(domain);refs=capture(refs,8192);if(!Array.isArray(refs)||!refs.length||refs.length>12)throw Error('Select one to twelve declared cases.');const selected=[],seen=new Set();
  for(const ref of refs){if(!exact(ref,Object.hasOwn(ref||{},'id')?['id','programId','pageId']:['programId','pageId']))throw Error('Give the exact program and page address.');const pi=domain.programs.findIndex(p=>p.id===ref.programId),page=domain.pages.find(p=>p.id===ref.pageId);if(pi<0||!page)throw Error('Selected case is outside the declared domain.');const id=await hash({protocolId:ref.programId,page},crypto);if(Object.hasOwn(ref,'id')&&ref.id!==id||seen.has(id))throw Error('Duplicate or changed case identity.');seen.add(id);selected.push({id,programId:ref.programId,pageId:page.id});}
  return freeze({domainId:domain.id,cases:selected});
 }
 async function select(domain,refs,crypto=root.crypto){
  const resolved=await resolveRefs(domain,refs,crypto),selected=[];
  for(const ref of resolved.cases){const page=domain.pages.find(p=>p.id===ref.pageId),program=domain.programs.find(p=>p.id===ref.programId);selected.push({...ref,task:await E.prepare({title:'Finite program '+ref.programId,pages:[page],alphabet:domain.alphabet,steps:program.steps,criterion:domain.criterion},crypto)});}
  selected.sort((a,b)=>a.programId.localeCompare(b.programId)||a.pageId.localeCompare(b.pageId));return freeze({domainId:domain.id,cases:selected});
 }
 function accumulator(domain,crypto,prefixMode,outputMode=false){inspect(domain);const token=Object.freeze({});accumulators.set(token,{domain,crypto,prefixMode,outputMode,owners:new Map(),matches:new Set(),insufficient:new Set(),receipts:new Map(),receiptKeys:null,memo:new Map(),memoBytes:0});return token;}
 function createAccumulator(domain,crypto=root.crypto){if(outputDomains.has(domain))throw Error('Use the explicit output-question accumulator.');return accumulator(domain,crypto,false);}
 function createPrefixAccumulator(domain,crypto=root.crypto){if(domain?.criterion?.kind==='exact-prefix-set')throw Error('Opening sets require exact direct results; single-prefix evidence reuse is unavailable.');if(outputDomains.has(domain))throw Error('Use the explicit output-question accumulator.');return accumulator(domain,crypto,true);}
 function createOutputAccumulator(domain,crypto=root.crypto){inspect(domain);if(!outputDomains.has(domain))throw Error('Use an explicitly bound output question.');return accumulator(domain,crypto,false,true);}
 const sourceKey=(reference,kind)=>E.stable([kind==='direct-result'?0:1,reference.taskId,reference.resultId,reference.createdAt,reference.inputVersion]);
 function state(token){const s=accumulators.get(token);if(!s)throw Error('Use a private factored evidence accumulator.');return s;}
 async function prepareAccept(token,sources){
  const s=state(token),d=s.domain,inputs=capture(sources,LIMITS.chunkBytes);if(!Array.isArray(inputs)||inputs.length>LIMITS.chunkSources)throw Error('Supply at most twelve bounded original receipts.');
  const direct=[],derived=[];for(const source of inputs){if((s.prefixMode||s.outputMode)&&E.stable(source?.task?.criterion)!==E.stable(d.criterion))derived.push(source);else direct.push(source);}
  const programs=new Map(d.programs.map((p,i)=>[p.id,i])),pages=new Map(d.pages.map((p,i)=>[p.id,{page:p,index:i}])),staged=[],memo=[];
  for(const source of direct){if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result']))throw Error('Use complete original computation receipts.');const descriptor=await R.describe(source.task,source.inputVersion,s.crypto),pi=programs.get(descriptor.protocolId);
   if(pi===undefined||source.inputVersion!==d.inputVersion){if(s.prefixMode||s.outputMode)throw Error('An original source is outside this exact question.');continue;}
   if(s.outputMode){
    const positions=[];for(const page of source.task.pages){const target=pages.get(page.id);if(target&&target.page.text===page.text)positions.push({position:pi*d.pages.length+target.index,pageId:page.id,page});}
    if(!positions.length)throw Error('An original source has no exact declared page intersection.');
    const policy=outputPolicy(),assessment=policy.inspect(await policy.prepare(source,s.crypto)),reference={taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt};
    if(assessment.policy.id!==d.questionPolicy||E.stable(assessment.criterion)!==E.stable(d.criterion)||E.stable(assessment.source)!==E.stable(reference))throw Error('An output assessment changed its exact original source or criterion.');
    const evaluated=[];for(const p of positions){const value=assessment.pages.find(value=>value.pageId===p.pageId);if(!value||value.inputSha256!==await hash(p.page,s.crypto)||!profile(d).statuses.includes(value.status))throw Error('An output assessment changed a declared page.');evaluated.push({position:p.position,pageId:p.pageId,insufficient:value.status===profile(d).secondary});}
    staged.push({key:sourceKey(reference,'direct-result'),reference,programId:descriptor.protocolId,evidenceKind:'direct-result',sourceProtocolId:descriptor.protocolId,positions:evaluated});continue;
   }
   // Envelope, full task/result hashes and original page geometry are checked on every chunk.
   await R.compare(source.task,source.inputVersion,[source],s.crypto);
   const positions=[];for(const page of source.task.pages){const target=pages.get(page.id);if(target&&target.page.text===page.text)positions.push({position:pi*d.pages.length+target.index,pageId:page.id});}if(!positions.length){if(s.prefixMode)throw Error('An original source has no exact declared page intersection.');continue;}
   const memoKey=source.task.taskId+'--'+source.run.id,signature=E.stable([source.task,source.run.result]),cached=s.memo.get(memoKey);
   if(cached!==undefined&&cached!==signature)throw Error('Conflicting bytes for one computation identity.');
   const result=cached===signature?source.run.result:await E.verify(source.task,source.run.result,s.crypto);
   if(cached!==signature)memo.push({key:memoKey,signature});
   const reference={taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt},key=s.prefixMode?sourceKey(reference,'direct-result'):E.stable(reference);
   staged.push({key,reference,programId:descriptor.protocolId,...(s.prefixMode?{evidenceKind:'direct-result',sourceProtocolId:descriptor.protocolId}:{}),positions:positions.map(p=>({...p,matched:result.matches.find(m=>m.page===p.pageId).matched}))});
  }
  let acceptedSources=staged.length;
  if(derived.length&&s.outputMode){
   const reuse=node?require('./factored-language-reuse.js'):root.FactoredLanguageReuse;if(!reuse)throw Error('Original-output language comparison is unavailable.');const metadata=reuse.inspect(await (d.questionPolicy==='transformed-output-inspection-v1'?reuse.prepareInspection:reuse.prepare)(d,derived,s.crypto));if(metadata.domainId!==d.id||metadata.sourceCount!==derived.length)throw Error('Derived comparisons changed their original question.');acceptedSources+=metadata.sourceCount;const receipts=new Map();
   for(const claim of metadata.claims){const source=metadata.sources[claim.sourceIndex],pi=programs.get(claim.programId),target=pages.get(claim.pageId);if(!source||pi===undefined||!target||!profile(d).statuses.includes(claim.status)||claim.targetCaseId!==await hash({protocolId:claim.programId,page:target.page},s.crypto))throw Error('A derived comparison is outside its exact declared case.');const key=sourceKey(source.reference,profile(d).derivedKind);let item=receipts.get(key);if(!item){item={key,reference:source.reference,programId:claim.programId,evidenceKind:profile(d).derivedKind,sourceProtocolId:source.sourceProtocolId,positions:[]};receipts.set(key,item);}if(item.programId!==claim.programId||item.sourceProtocolId!==source.sourceProtocolId)throw Error('One original source changed its transformation.');item.positions.push({position:pi*d.pages.length+target.index,pageId:claim.pageId,insufficient:claim.status===profile(d).secondary});}staged.push(...receipts.values());
  }else if(derived.length){
   // Lazy dependency avoids a Q/primitive UMD cycle and leaves legacy loading
   // independent of the optional prefix-reuse implementation.
   const reuse=node?require('./factored-prefix-reuse.js'):root.FactoredPrefixReuse;if(!reuse)throw Error('Derived opening verification is unavailable.');
   const metadata=reuse.inspect(await reuse.prepare(d,derived,s.crypto));if(metadata.domainId!==d.id||metadata.sourceCount!==derived.length)throw Error('Derived opening claims changed their bound question.');acceptedSources+=metadata.sourceCount;
   const receipts=new Map();for(const claim of metadata.claims){const pi=programs.get(claim.programId),target=pages.get(claim.pageId);if(pi===undefined||!target)throw Error('A derived opening claim is outside the declared domain.');const key=sourceKey(claim.source,'derived-prefix');let item=receipts.get(key);if(!item){const sourceProtocolId=await hash({...protocol(d,d.programs[pi].steps),criterion:claim.sourceCriterion},s.crypto);item={key,reference:claim.source,programId:claim.programId,evidenceKind:'derived-prefix',sourceProtocolId,positions:[]};receipts.set(key,item);}if(item.programId!==claim.programId)throw Error('One original source changed its transformation.');item.positions.push({position:pi*d.pages.length+target.index,pageId:claim.pageId,matched:claim.matched});}staged.push(...receipts.values());
  }
  // Preparing never changes coverage, provenance or the replay cache. The caller
  // can stage these original receipts before committing any visible evidence.
  const pending=Object.freeze({});preparedAccepts.set(pending,{token,staged,memo,acceptedSources});return pending;
 }
 function inspectPrepared(pending){const saved=preparedAccepts.get(pending);if(!saved)throw Error('Use an uncommitted independently prepared evidence chunk.');return freeze({domainId:state(saved.token).domain.id,acceptedSources:saved.acceptedSources});}
 function commitAccept(token,pending){
  const s=state(token),saved=preparedAccepts.get(pending);if(!saved||saved.token!==token)throw Error('The prepared evidence belongs to another accumulator or was already committed.');
  const {staged,memo}=saved;
  for(const item of memo){const existing=s.memo.get(item.key);if(existing!==undefined&&existing!==item.signature)throw Error('Conflicting bytes for one computation identity.');}
  if(s.prefixMode){const matches=new Map();for(const item of staged)for(const p of item.positions){if(s.owners.has(p.position)&&s.matches.has(p.position)!==p.matched||matches.has(p.position)&&matches.get(p.position)!==p.matched)throw Error('Verified sources conflict on the same requested opening.');matches.set(p.position,p.matched);}}
  if(s.outputMode){const statuses=new Map();for(const item of staged)for(const p of item.positions){if(s.owners.has(p.position)&&s.insufficient.has(p.position)!==p.insufficient||statuses.has(p.position)&&statuses.get(p.position)!==p.insufficient)throw Error('Verified sources conflict on the same output assessment.');statuses.set(p.position,p.insufficient);}}
  preparedAccepts.delete(pending);
  for(const item of memo)if(!s.memo.has(item.key)){const size=new TextEncoder().encode(item.signature).byteLength+item.key.length+128;if(s.memoBytes+size<=LIMITS.memoBytes){s.memo.set(item.key,item.signature);s.memoBytes+=size;}}
  for(const item of staged)for(const p of item.positions){const old=s.owners.get(p.position);if(old&&old.localeCompare(item.key)<=0)continue;
   if(old){const receipt=s.receipts.get(old);receipt.positions.delete(p.position);if(!receipt.positions.size){s.receipts.delete(old);s.receiptKeys=null;}}
   if(!s.receipts.has(item.key)){s.receipts.set(item.key,{reference:item.reference,programId:item.programId,...(s.prefixMode||s.outputMode?{evidenceKind:item.evidenceKind,sourceProtocolId:item.sourceProtocolId}:{}),positions:new Set()});s.receiptKeys=null;}s.receipts.get(item.key).positions.add(p.position);s.owners.set(p.position,item.key);if(p.matched)s.matches.add(p.position);if(s.outputMode&&p.insufficient)s.insufficient.add(p.position);
  }
  return freeze({acceptedSources:saved.acceptedSources,coveredCases:s.owners.size,...(s.outputMode?(s.domain.questionPolicy==='transformed-output-inspection-v1'?{runeOutputCases:s.owners.size-s.insufficient.size,noRuneCases:s.insufficient.size}:{usableCases:s.owners.size-s.insufficient.size,insufficientCases:s.insufficient.size}):{matchingCases:s.matches.size})});
 }
 async function accept(token,sources){return commitAccept(token,await prepareAccept(token,sources));}
 async function summarize(token,options={lookupComplete:false}){
  const s=state(token),d=s.domain,v=capture(options,100);if(!exact(v,['lookupComplete'])||typeof v.lookupComplete!=='boolean')throw Error('Declare whether the complete source lookup finished.');
  if(s.outputMode){
   // Capture every category before awaiting identities or hashes so a concurrent
   // commit cannot mix old coverage with newly committed status metadata.
   const covered=new Set(s.owners.keys()),insufficient=new Set(s.insufficient),derived=new Set([...s.owners].filter(([,key])=>s.receipts.get(key).evidenceKind===profile(d).derivedKind).map(([position])=>position)),nextCases=[],complete=covered.size===d.totalCases;
   if(!complete&&v.lookupComplete)for(let n=0;n<d.totalCases&&nextCases.length<12;n++)if(!covered.has(n))nextCases.push(await refAt(d,n,s.crypto));
   const decision=complete?{state:'answered',answer:profile(d).answer}:v.lookupComplete?{state:'missing-evidence'}:{state:'unavailable'},proof=freeze({schema:'liberpedia-factored-finite-output-evidence-v1',questionPolicy:d.questionPolicy,evidenceMode:profile(d).evidenceMode,domainId:d.id,totalCases:d.totalCases,coveredCases:covered.size,...(d.questionPolicy==='transformed-output-inspection-v1'?{runeOutputCases:covered.size-insufficient.size,noRuneCases:insufficient.size}:{usableCases:covered.size-insufficient.size,insufficientCases:insufficient.size}),directCases:covered.size-derived.size,derivedCases:derived.size,derivedCoverageSha256:await bitmapHash(derived,d.totalCases,s.crypto),remainingCases:d.totalCases-covered.size,coverageSha256:await bitmapHash(covered,d.totalCases,s.crypto),...(d.questionPolicy==='transformed-output-inspection-v1'?{noRuneSha256:await bitmapHash(insufficient,d.totalCases,s.crypto)}:{insufficientSha256:await bitmapHash(insufficient,d.totalCases,s.crypto)}),lookupComplete:v.lookupComplete,complete,nextCases,decision});proofs.add(proof);return proof;
  }
  const derived=new Set();if(s.prefixMode)for(const [position,key]of s.owners)if(s.receipts.get(key).evidenceKind==='derived-prefix')derived.add(position);
  const covered=new Set(s.owners.keys()),matched=new Set(s.matches),matching=matched.size,nextCases=[];if((!matching||d.criterion.kind==='exact-prefix-set')&&covered.size<d.totalCases&&v.lookupComplete)for(let n=0;n<d.totalCases&&nextCases.length<12;n++)if(!covered.has(n))nextCases.push(await refAt(d,n,s.crypto));
  const complete=covered.size===d.totalCases,decision=matching&&(complete||d.criterion.kind!=='exact-prefix-set')?{state:'answered',answer:'prefix-found'}:complete?{state:'answered',answer:'prefix-not-found'}:v.lookupComplete?{state:'missing-evidence'}:{state:'unavailable'};
  const coverageSha256=await bitmapHash(covered,d.totalCases,s.crypto),matchingSha256=await bitmapHash(matched,d.totalCases,s.crypto);
  const proof=freeze({schema:s.prefixMode?'liberpedia-factored-finite-evidence-v3':'liberpedia-factored-finite-evidence-v2',...(s.prefixMode?{evidenceMode:'verified-output-prefix-v1',directCases:covered.size-derived.size,derivedCases:derived.size,derivedCoverageSha256:await bitmapHash(derived,d.totalCases,s.crypto)}:{}),domainId:d.id,totalCases:d.totalCases,coveredCases:covered.size,matchingCases:matching,remainingCases:d.totalCases-covered.size,coverageSha256,matchingSha256,lookupComplete:v.lookupComplete,complete,nextCases,decision});proofs.add(proof);return proof;
 }
 function inspectEvidence(proof){if(!proofs.has(proof))throw Error('Use independently verified factored evidence.');return proof;}
 async function coverage(token,refs){
  const s=state(token),resolved=await resolveRefs(s.domain,refs,s.crypto),selected={cases:[...resolved.cases].sort((a,b)=>a.programId.localeCompare(b.programId)||a.pageId.localeCompare(b.pageId))},coveredCaseIds=[],missingCaseIds=[],matchingCaseIds=[],directCaseIds=[],derivedCaseIds=[];
  if(s.outputMode){const usableCaseIds=[],insufficientCaseIds=[];for(const item of selected.cases){const pi=s.domain.programs.findIndex(p=>p.id===item.programId),pageIndex=s.domain.pages.findIndex(p=>p.id===item.pageId),position=pi*s.domain.pages.length+pageIndex;if(!s.owners.has(position))missingCaseIds.push(item.id);else{coveredCaseIds.push(item.id);(s.insufficient.has(position)?insufficientCaseIds:usableCaseIds).push(item.id);(s.receipts.get(s.owners.get(position)).evidenceKind===profile(s.domain).derivedKind?derivedCaseIds:directCaseIds).push(item.id);}}return freeze({domainId:s.domain.id,coveredCaseIds,missingCaseIds,...(s.domain.questionPolicy==='transformed-output-inspection-v1'?{runeOutputCaseIds:usableCaseIds,noRuneCaseIds:insufficientCaseIds}:{usableCaseIds,insufficientCaseIds}),directCaseIds,derivedCaseIds});}
  for(const item of selected.cases){const pi=s.domain.programs.findIndex(p=>p.id===item.programId),pageIndex=s.domain.pages.findIndex(p=>p.id===item.pageId),position=pi*s.domain.pages.length+pageIndex;
   (s.owners.has(position)?coveredCaseIds:missingCaseIds).push(item.id);if(s.matches.has(position))matchingCaseIds.push(item.id);if(s.prefixMode&&s.owners.has(position))(s.receipts.get(s.owners.get(position)).evidenceKind==='derived-prefix'?derivedCaseIds:directCaseIds).push(item.id);
  }
  return freeze({domainId:s.domain.id,coveredCaseIds,missingCaseIds,matchingCaseIds,...(s.prefixMode?{directCaseIds,derivedCaseIds}:{})});
 }
 function evidence(token,options={cursor:0,limit:12}){const s=state(token),keys=s.receiptKeys||(s.receiptKeys=[...s.receipts.keys()].sort()),{cursor,limit}=paging(options,keys.length),out=keys.slice(cursor,cursor+limit).map(key=>{const r=s.receipts.get(key);return {...r.reference,programId:r.programId,...(s.prefixMode?{evidenceKind:r.evidenceKind,sourceProtocolId:r.sourceProtocolId,matchingPageIds:[...r.positions].filter(n=>s.matches.has(n)).sort((a,b)=>a-b).map(n=>s.domain.pages[n%s.domain.pages.length].id)}:{}),...(s.outputMode?{evidenceKind:r.evidenceKind,sourceProtocolId:r.sourceProtocolId,...(s.domain.questionPolicy==='transformed-output-inspection-v1'?{noRunePageIds:[...r.positions].filter(n=>s.insufficient.has(n)).sort((a,b)=>a-b).map(n=>s.domain.pages[n%s.domain.pages.length].id)}:{insufficientPageIds:[...r.positions].filter(n=>s.insufficient.has(n)).sort((a,b)=>a-b).map(n=>s.domain.pages[n%s.domain.pages.length].id)})}:{}),pageIds:[...r.positions].sort((a,b)=>a-b).map(n=>s.domain.pages[n%s.domain.pages.length].id)};});return freeze({sources:out,nextCursor:cursor+out.length<keys.length?cursor+out.length:null});}
 const api={bind,bindLanguageComparison,bindOutputInspection,inspect,cases,select,createAccumulator,createPrefixAccumulator,createOutputAccumulator,prepareAccept,inspectPrepared,commitAccept,accept,summarize,inspectEvidence,coverage,evidence,LIMITS};if(node)module.exports=api;else root.FactoredFiniteQuestion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
