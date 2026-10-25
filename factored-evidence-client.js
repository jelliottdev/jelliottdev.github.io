/* Ordered, independently replayed evidence discovery. No execution or writes. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,Q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion,J=node?require('./finite-json.js'):root.FiniteJSON,E=node?require('./local-experiment.js'):root.LocalExperiment;
 const HEX=/^[a-f0-9]{64}$/,MAX=8*1024*1024,keys=['schema','proposalId','domainId','inputVersion','scanId','sequence','previousPageSha256','sources','sourceLinks','continuation','snapshotToken','pageSha256'];
 const exact=(v,names)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===names.length&&names.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const capture=v=>J.capture(v,{maxBytes:MAX,maxDepth:24,maxNodes:500000});
 const aborted=()=>new DOMException('Evidence lookup cancelled.','AbortError');
 async function hash(value,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 function validLink(link,source){return exact(link,['taskId','href','label'])&&link.taskId===source.task.taskId&&typeof link.label==='string'&&link.label.trim().length>0&&link.label.length<=300&&typeof link.href==='string'&&(link.href==='run.html#task='+link.taskId||/^library\.html#\/experiment\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(link.href)||/^run\.html#family=deor-feedback-v1&case=[a-z0-9-]+&revision=[a-f0-9]{64}$/.test(link.href));}
 function createScan({proposalId,domain,fetchPage,crypto=root.crypto,signal,onSources,onProgress}){
  Q.inspect(domain);if(!/^p_[a-f0-9]{64}$/.test(proposalId)||typeof fetchPage!=='function'||!crypto?.subtle||onSources!==undefined&&typeof onSources!=='function'||onProgress!==undefined&&typeof onProgress!=='function')throw Error('Use a bound original question and a page reader.');
  const accumulator=Q.createAccumulator(domain,crypto),controller=new AbortController(),seenCursorHashes=new Set();let dead=false,generation=0,tail=Promise.resolve(),cursor=null,scanId=null,previous=null,sequence=0,baselineComplete=false;
  let state=freeze({status:'idle',proposalId,domainId:domain.id,pagesAccepted:0,proof:null,snapshotToken:null,error:null});
  const live=token=>{if(dead||generation!==token)throw aborted();};
  function cancel(){if(dead)return;dead=true;generation++;controller.abort();signal?.removeEventListener?.('abort',cancel);state=freeze({...state,status:'cancelled',error:null});}
  if(signal){if(signal.aborted)cancel();else signal.addEventListener('abort',cancel,{once:true});}
  async function advance(){
   const token=generation;live(token);if(state.status==='complete')return state;state=freeze({...state,status:'loading',error:null});
   try{
    const page=capture(await fetchPage(freeze({inputVersion:domain.inputVersion,domainId:domain.id,cursor}),{signal:controller.signal}));live(token);
    if(!exact(page,keys)||page.schema!=='liberpedia-factored-evidence-page-v1'||page.proposalId!==proposalId||page.domainId!==domain.id||page.inputVersion!==domain.inputVersion||typeof page.scanId!=='string'||!/^[a-zA-Z0-9_-]{24}$/.test(page.scanId)||scanId!==null&&page.scanId!==scanId||page.sequence!==sequence||page.previousPageSha256!==previous||!HEX.test(page.pageSha256)||!Array.isArray(page.sources)||page.sources.length>12||!Array.isArray(page.sourceLinks)||page.sourceLinks.length!==page.sources.length||!exact(page.continuation,['nextCursor','complete'])||typeof page.continuation.complete!=='boolean')throw Error('The evidence page changed its question or ordered scan.');
    if(page.continuation.complete?typeof page.snapshotToken!=='string'||!page.snapshotToken.length||page.snapshotToken.length>32768:page.snapshotToken!==null)throw Error('The completed evidence snapshot token is missing or premature.');
    const next=page.continuation.nextCursor;if(page.continuation.complete?next!==null:typeof next!=='string'||!next.length||next.length>32768||next===cursor)throw Error('The evidence scan is missing or repeating its continuation.');
    const nextHash=next===null?null:await hash(next,crypto);live(token);if(nextHash!==null&&seenCursorHashes.has(nextHash))throw Error('The evidence scan is repeating its continuation.');
    const body={...page,continuation:{complete:page.continuation.complete}};delete body.pageSha256;if(await hash(body,crypto)!==page.pageSha256)throw Error('The evidence page digest changed.');live(token);
    if(page.sourceLinks.some((link,i)=>!validLink(link,page.sources[i])))throw Error('An evidence source location does not identify its original computation.');
    // Prepare all receipts transactionally. Neither a rejected mixed page nor
    // failed/cancelled local staging may publish any of its coverage.
    const prepared=await Q.prepareAccept(accumulator,page.sources);live(token);if(Q.inspectPrepared(prepared).acceptedSources!==page.sources.length)throw Error('An evidence receipt is outside this exact question.');
    if(onSources){await onSources(freeze(page.sources),freeze(page.sourceLinks));live(token);}
    Q.commitAccept(accumulator,prepared);
    const pendingProof=await Q.summarize(accumulator,{lookupComplete:page.continuation.complete});live(token);
    scanId=page.scanId;previous=page.pageSha256;sequence++;cursor=next;if(nextHash!==null)seenCursorHashes.add(nextHash);
    baselineComplete=page.continuation.complete;state=freeze({status:baselineComplete?'complete':'ready',proposalId,domainId:domain.id,pagesAccepted:sequence,proof:pendingProof,snapshotToken:page.snapshotToken,error:null});
    // Progress is an observer, not a staging transaction. Observer failures
    // cannot make a committed page retry and duplicate its retained originals.
    if(onProgress)try{const observed=onProgress(freeze({pagesAccepted:sequence,coveredCases:pendingProof.coveredCases,totalCases:pendingProof.totalCases}));if(observed&&typeof observed.catch==='function')observed.catch(()=>{});}catch{}
    return state;
   }catch(error){if(dead||generation!==token||error.name==='AbortError'){if(!dead)cancel();throw aborted();}const proof=await Q.summarize(accumulator,{lookupComplete:false});live(token);state=freeze({...state,status:'error',proof,error:{message:String(error.message||'Evidence could not be checked.'),...(typeof error.code==='string'?{code:error.code}:{})}});throw error;}
  }
  async function append(suppliedSources,suppliedLinks){
   const token=generation;live(token);if(!baselineComplete)throw Error('Finish the baseline evidence lookup before appending saved receipts.');
   const prior=state;state=freeze({...state,status:'loading',error:null});
   try{const value=capture({sources:suppliedSources,sourceLinks:suppliedLinks});if(!Array.isArray(value.sources)||value.sources.length>12||!Array.isArray(value.sourceLinks)||value.sourceLinks.length!==value.sources.length||value.sourceLinks.some((link,i)=>!validLink(link,value.sources[i])))throw Error('Use bounded original saved receipts and exact source links.');
    const prepared=await Q.prepareAccept(accumulator,value.sources);live(token);if(Q.inspectPrepared(prepared).acceptedSources!==value.sources.length)throw Error('A saved receipt is outside this exact question.');
    if(onSources){await onSources(freeze(value.sources),freeze(value.sourceLinks));live(token);}Q.commitAccept(accumulator,prepared);const proof=await Q.summarize(accumulator,{lookupComplete:true});live(token);state=freeze({...prior,status:'complete',proof,error:null});return state;
   }catch(error){if(dead||generation!==token){throw aborted();}state=freeze({...prior,status:'error',error:{message:String(error.message||'Saved receipts could not be retained.')}});throw error;}
  }
  function queue(action){const result=tail.then(action,action);tail=result.catch(()=>{});return result;}
  function step(){return queue(advance);}
  return {step,acceptSources:(sources,links)=>{const value=capture({sources,sourceLinks:links});return queue(()=>append(value.sources,value.sourceLinks));},evidence:(options={cursor:0,limit:12})=>Q.evidence(accumulator,options),coverage:refs=>{const value=capture(refs);return queue(()=>Q.coverage(accumulator,value));},getState:()=>state,cancel};
 }
 const api={createScan};if(node)module.exports=api;else root.FactoredEvidenceClient=api;
})(typeof globalThis!=='undefined'?globalThis:this);
