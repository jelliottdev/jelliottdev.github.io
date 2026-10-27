/* Ordinary opening checks from unchanged originals. No admission, execution or writes. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,H=node?require('./claim-share.js'):root.ClaimShare,C=node?require('./claim-specification.js'):root.ClaimSpecification,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle,P=node?require('./verified-prefix-evaluation.js'):root.VerifiedPrefixEvaluation,A=node?require('./verified-output-assessment.js'):root.VerifiedOutputAssessment,Published=node?require('./published-output-client.js'):root.PublishedOutputClient;
 const MAX_BYTES=8*1024*1024,VERIFICATION_TIMEOUT=45000,tokens=new WeakMap(),IDEA=/^p_[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable),capture=(v,maxBytes=MAX_BYTES)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000});
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},abort=()=>new DOMException('Navigation changed.','AbortError');
 function publishedTransport(o){
  const descriptors=o&&Object.getOwnPropertyDescriptors(o);if(!o||typeof o!=='object'||Array.isArray(o)||Reflect.ownKeys(o).some(k=>typeof k!=='string'||!['baseURL','fetcher','pageURL','signal'].includes(k)||!descriptors[k].enumerable||!Object.hasOwn(descriptors[k],'value'))||!Object.hasOwn(o,'baseURL')||!Object.hasOwn(o,'fetcher')||typeof o.baseURL!=='string'||typeof o.fetcher!=='function'||Object.hasOwn(o,'pageURL')&&typeof o.pageURL!=='string')throw Error('Use bound published-output transport options without authority overrides.');return {...o};
 }
 async function verificationDeadline(work,signal){
  const controller=new AbortController();let closed=false,failure=null,rejectStop;
  const stopped=new Promise((_,reject)=>{rejectStop=reject;});
  const stop=error=>{if(closed||failure)return;failure=error;controller.abort();rejectStop(error);},cancel=()=>stop(abort());
  signal?.addEventListener?.('abort',cancel,{once:true});
  const timer=setTimeout(()=>stop(Error('Earlier-output verification timed out. Please retry.')),VERIFICATION_TIMEOUT);
  const live=()=>{if(failure||closed)throw failure||abort();};
  try{if(signal?.aborted)cancel();return await Promise.race([failure?Promise.reject(failure):work({signal:controller.signal,live}),stopped]);}
  finally{closed=true;clearTimeout(timer);signal?.removeEventListener?.('abort',cancel);controller.abort();}
 }
 async function read(response,{signal}={}){
  const live=()=>{if(signal?.aborted)throw abort();};live();
  if(!response)throw Error('The earlier-output evidence response is unavailable.');
  const length=response.headers?.get?.('content-length');if(length!==undefined&&length!==null&&(!/^\d+$/.test(length)||Number(length)>MAX_BYTES))throw Error('Earlier-output evidence exceeds its byte bound.');
  const reader=response.body?.getReader?.();
  if(reader){const chunks=[];let size=0;const stop=()=>{try{Promise.resolve(reader.cancel()).catch(()=>{});}catch{}};signal?.addEventListener?.('abort',stop,{once:true});
   try{while(true){live();const {done,value}=await reader.read();live();if(done)break;if(!ArrayBuffer.isView(value)||value.BYTES_PER_ELEMENT!==1)throw Error('Earlier-output evidence is unreadable.');size+=value.byteLength;if(size>MAX_BYTES)throw Error('Earlier-output evidence exceeds its byte bound.');chunks.push(new Uint8Array(value));}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return capture(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)));}
   catch(error){try{await reader.cancel();}catch{}throw error;}
   finally{signal?.removeEventListener?.('abort',stop);reader.releaseLock?.();}
  }
  // A text-only injectable transport is supported; native readable bodies above
  // never fall through to an unbounded Response.json() call.
  if(typeof response.text!=='function')throw Error('Earlier-output evidence needs a readable response.');const text=await response.text();live();if(typeof text!=='string'||new TextEncoder().encode(text).byteLength>MAX_BYTES)throw Error('Earlier-output evidence exceeds its byte bound.');return capture(JSON.parse(text));
 }
 async function verifyDerivedOutput(options,crypto=root.crypto,assessment=false){
  const keys=['requestedTask','inputVersion','value',...(Object.hasOwn(options||{},'isLive')?['isLive']:[]),...(Object.hasOwn(options||{},'publishedOptions')?['publishedOptions']:[])];if(!exact(options,keys))throw Error('Use the exact requested computation and complete original opening evidence.');
  const isLive=Object.hasOwn(options,'isLive')?options.isLive:(()=>true);if(typeof isLive!=='function')throw Error('Invalid evidence lifecycle guard.');let budgetCheck=()=>{};const live=()=>{budgetCheck();if(!isLive())throw abort();};live();
  const {requestedTask,inputVersion,value}=capture({requestedTask:options.requestedTask,inputVersion:options.inputVersion,value:options.value},12*1024*1024);
  capture(value,MAX_BYTES);
  if(!['raw','reviewed'].includes(inputVersion)||!exact(value,['schema','provider','requestedTaskId','inputVersion','originals','lookupComplete','summary'])||value.schema!==(assessment?'liberpedia-ordinary-derived-output-assessment-v1':'liberpedia-ordinary-derived-openings-coverage-v1')||value.provider!==(assessment?'public-output-originals-v1':'public-opening-originals-v1')||value.requestedTaskId!==requestedTask.taskId||value.inputVersion!==inputVersion||typeof value.lookupComplete!=='boolean'||!Array.isArray(value.originals)||value.originals.length>75||!exact(value.summary,assessment?['coveredPages','remainingPages','insufficientPages']:['coveredPages','matchingPages','remainingPages']))throw Error('The derived opening evidence envelope is invalid.');
  const publishedOptions=Object.hasOwn(options,'publishedOptions')?{...publishedTransport(options.publishedOptions),crypto}:null;
  return verificationDeadline(async budget=>{
  budgetCheck=budget.live;
  await E.checkIdentity(requestedTask,crypto);live();if(!(assessment?['language-score']:['exact-prefix','exact-prefix-set']).includes(requestedTask.criterion.kind))throw Error('Use an explicit literal opening check.');
  const wanted=new Map(requestedTask.pages.map(p=>[p.id,p.text])),program=E.stable({engine:requestedTask.engine,alphabet:requestedTask.alphabet,steps:requestedTask.steps}),seen=new Set(),sources=[],sourceLinks=[],reloads=[],assessmentOriginals=new Map();let assessmentReplayRunes=0;
  for(const original of value.originals){
   if(!exact(original,['origin','source']))throw Error('Use an exact retained original and its typed origin.');const o=original.origin,s=original.source,published=o?.kind==='published';
   if(!exact(o,['kind','taskId','resultId','inputVersion','createdAt',...(published?['recordId','revision','caseId']:[])])||!['local','published'].includes(o.kind)||!['taskId','resultId'].every(k=>typeof o[k]==='string'&&/^[a-f0-9]{64}$/.test(o[k]))||o.inputVersion!==inputVersion||typeof o.createdAt!=='string'||!Number.isFinite(Date.parse(o.createdAt))||new Date(o.createdAt).toISOString()!==o.createdAt||!exact(s,['task','inputVersion','run',...(published?['publishedSource','provenance']:[])])||s.inputVersion!==inputVersion||s.task?.taskId!==o.taskId||s.run?.id!==o.resultId||s.run?.createdAt!==o.createdAt||seen.has(E.stable(o)))throw Error('The original output identity or origin changed.');seen.add(E.stable(o));
   if(E.stable({engine:s.task.engine,alphabet:s.task.alphabet,steps:s.task.steps})!==program||!s.task.pages.some(p=>wanted.get(p.id)===p.text))throw Error('The retained output belongs to another transformation or page input.');
   if(assessment){
    if(!A)throw Error('Saved-output assessments are unavailable.');
    E.validateTask(s.task);
    const runes=new Set(s.task.alphabet.map(entry=>entry.rune)),count=s.task.pages.reduce((total,page)=>total+[...page.text].filter(ch=>runes.has(ch)).length,0),key=E.stable([s.task.taskId,s.run.id]),taskBytes=E.stable(s.task),resultBytes=E.stable(s.run.result),prior=assessmentOriginals.get(key);
    if(prior&&(prior.taskBytes!==taskBytes||prior.resultBytes!==resultBytes))throw Error('Conflicting original computation bytes.');
    // Core verification reuses only exact task/result bytes. Each published
    // reload independently verifies again, even for another archived pointer
    // to the same original. Bound their combined work before starting I/O.
    if(!prior){assessmentOriginals.set(key,{taskBytes,resultBytes});assessmentReplayRunes+=count;}
    if(published)assessmentReplayRunes+=count;
    if(assessmentReplayRunes>A.MAX_RUNES)throw Error('Saved-output assessment replay exceeds its 200,000-rune bound.');
   }
   let href='run.html#task='+o.taskId,label='Original computation';
   if(published){
    if(!publishedOptions||!Published)throw Error('Archived output needs an authenticated published source transport.');
    const ref={recordId:o.recordId,revision:o.revision,caseId:o.caseId};href='run.html'+Published.href(ref);label='Archived original output';
    reloads.push(async()=>{const loaded=await Published.load(ref,{...publishedOptions,signal:budget.signal});live();if(!Published.isVerified(loaded)||E.stable(loaded)!==E.stable(s))throw Error('The archived original differs from its independently authenticated source.');});
   }
   sources.push({task:s.task,inputVersion:s.inputVersion,run:s.run});sourceLinks.push({taskId:o.taskId,href,label});
  }
  let next=0;const worker=async()=>{while(next<reloads.length){live();const at=next++;await reloads[at]();}};
  await Promise.all(Array.from({length:Math.min(4,reloads.length)},worker));live();
  const evaluator=assessment?A:P;if(!evaluator)throw Error('Saved-output assessments are unavailable.');const proof=await(assessment?evaluator.evaluate:evaluator.evaluateOpenings)({task:requestedTask,inputVersion,sources},crypto);live();evaluator.inspect(proof);for(const name of (assessment?['coveredPages','remainingPages','insufficientPages']:['coveredPages','matchingPages','remainingPages']))if(E.stable(value.summary[name])!==E.stable(proof[name]))throw Error('The advertised opening page partition is incorrect.');
  const token=Object.freeze({});tokens.set(token,freeze({requestedTask,inputVersion,proof,sourceLinks,lookupComplete:value.lookupComplete}));return token;
  },publishedOptions?.signal);
 }
 const verifyDerivedOpenings=(options,crypto=root.crypto)=>verifyDerivedOutput(options,crypto,false),verifyDerivedAssessment=(options,crypto=root.crypto)=>verifyDerivedOutput(options,crypto,true);
 async function verify(options,crypto=root.crypto){
  const keys=['proposalId','card','bundle','requestedTask','value',...(Object.hasOwn(options||{},'isLive')?['isLive']:[]),...(Object.hasOwn(options||{},'publishedOptions')?['publishedOptions']:[])];if(!exact(options,keys))throw Error('Use the original idea, official inputs and complete earlier-output evidence.');
  const transport=Object.hasOwn(options,'publishedOptions')?publishedTransport(options.publishedOptions):null;
  const isLive=Object.hasOwn(options,'isLive')?options.isLive:(()=>true);if(typeof isLive!=='function')throw Error('Invalid evidence lifecycle guard.');
  const input=capture({proposalId:options.proposalId,card:options.card,bundle:options.bundle,requestedTask:options.requestedTask,value:options.value},14*1024*1024),live=()=>{if(!isLive())throw abort();};live();
  const {proposalId,card,bundle,requestedTask,value}=input,assessment=value?.schema==='liberpedia-ordinary-derived-output-assessment-v1',v2=assessment||value?.schema==='liberpedia-ordinary-derived-openings-coverage-v1';if(!IDEA.test(proposalId))throw Error('The saved idea identity is invalid.');capture(card,H.MAX_BYTES);H.sections(card);const cardHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(card))))].map(n=>n.toString(16).padStart(2,'0')).join('');live();if(proposalId!=='p_'+cardHash)throw Error('The saved idea does not match its canonical card identity.');const plan=Compiler.compile(card);if(plan.reason||plan.state||!(assessment?['language-score']:v2?['exact-prefix','exact-prefix-set']:['exact-prefix']).includes(plan.criterion?.kind))throw Error('This original idea does not compile to an explicit ordinary opening check.');
  const source=Inputs.parse(capture(bundle,2*1024*1024)),pages=plan.pages.map(id=>{const page=source.pages.get(id),text=plan.inputVersion==='raw'?page?.raw:page?.reviewed_text;if(typeof text!=='string')throw Error('A requested page has no official text in this edition.');return {id,text};});
  capture(requestedTask,2*1024*1024);await E.checkIdentity(requestedTask,crypto);live();const expected=await E.prepare({title:requestedTask.title,pages,alphabet:source.alphabet,steps:plan.steps,criterion:plan.criterion},crypto);live();if(E.stable(expected)!==E.stable(requestedTask))throw Error('The requested computation changed the original idea or official input bytes.');
  if(v2){const checked=inspect(await (assessment?verifyDerivedAssessment:verifyDerivedOpenings)({requestedTask,inputVersion:plan.inputVersion,value,isLive,...(transport?{publishedOptions:transport}:{})},crypto));live();const token=Object.freeze({});tokens.set(token,freeze({proposalId,...checked}));return token;}
  if(Object.hasOwn(options,'publishedOptions'))throw Error('Published transport is only supported by versioned opening evidence.');
  capture(value,MAX_BYTES);if(!exact(value,['schema','provider','requestedTaskId','inputVersion','sources','sourceLocations','lookupComplete','summary'])||value.schema!=='liberpedia-ordinary-derived-prefix-coverage-v1'||value.provider!=='public-local-tasks-v1'||value.requestedTaskId!==requestedTask.taskId||value.inputVersion!==plan.inputVersion||typeof value.lookupComplete!=='boolean'||!Array.isArray(value.sources)||value.sources.length>75||!Array.isArray(value.sourceLocations)||value.sourceLocations.length!==value.sources.length||!exact(value.summary,['coveredPages','matchingPages','remainingPages']))throw Error('The earlier-output evidence envelope is invalid.');
  const wanted=new Map(requestedTask.pages.map(page=>[page.id,page.text])),program=E.stable({engine:requestedTask.engine,alphabet:requestedTask.alphabet,steps:requestedTask.steps}),ids=new Set();
  for(const original of value.sources){capture(original.task,2*1024*1024);capture(original.run?.result,2*1024*1024);if(!exact(original,['task','inputVersion','run'])||original.inputVersion!==plan.inputVersion||!exact(original.run,['id','createdAt','result'])||typeof original.run.createdAt!=='string'||!Number.isFinite(Date.parse(original.run.createdAt))||new Date(original.run.createdAt).toISOString()!==original.run.createdAt||!['measurement','exact-prefix'].includes(original.task?.criterion?.kind)||ids.has(original.task.taskId)||E.stable({engine:original.task.engine,alphabet:original.task.alphabet,steps:original.task.steps})!==program||!Array.isArray(original.task.pages)||!original.task.pages.some(page=>wanted.get(page.id)===page.text))throw Error('An earlier output is not an unchanged relevant original.');ids.add(original.task.taskId);}
  const sourceLinks=[],located=new Set();for(const location of value.sourceLocations){if(!exact(location,['taskId','href','label'])||!ids.has(location.taskId)||located.has(location.taskId)||location.href!=='run.html#task='+location.taskId||location.label!=='Original computation')throw Error('An earlier-output source location changed its original computation.');located.add(location.taskId);sourceLinks.push(location);}
  const proof=await P.evaluate({task:requestedTask,inputVersion:plan.inputVersion,sources:value.sources},crypto);live();P.inspect(proof);for(const name of ['coveredPages','matchingPages','remainingPages'])if(E.stable(value.summary[name])!==E.stable(proof[name]))throw Error('The advertised earlier-output page partition is incorrect.');
  const metadata=freeze({proposalId,requestedTask,inputVersion:plan.inputVersion,proof,sourceLinks,lookupComplete:value.lookupComplete}),token=Object.freeze({});tokens.set(token,metadata);return token;
 }
 function inspect(token){const value=tokens.get(token);if(!value)throw Error('Use independently checked ordinary opening evidence.');return value;}
 const api={read,verify,verifyDerivedOpenings,verifyDerivedAssessment,inspect,MAX_BYTES};if(node)module.exports=api;else root.OrdinaryPrefixEvidenceClient=api;
})(typeof globalThis!=='undefined'?globalThis:this);
