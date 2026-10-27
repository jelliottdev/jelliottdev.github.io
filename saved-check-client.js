/* Read one authenticated public calculation. No search, task creation or execution admission. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,Summary=node?require('./saved-check-summary.js'):root.SavedCheckSummary;
 const LIMITS=Object.freeze({bytes:2*1024*1024,timeoutMs:8000}),HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/;
 const need=(ok,message)=>{if(!ok)throw Error(message);},own=(value,key)=>Object.hasOwn(value,key),same=(a,b)=>E.stable(a)===E.stable(b),capture=value=>J.capture(value,{maxBytes:LIMITS.bytes,maxDepth:24,maxNodes:500000});
 function fields(value,allowed,required){need(value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).every(key=>typeof key==='string'&&allowed.includes(key)&&Object.getOwnPropertyDescriptor(value,key)?.get===undefined&&Object.getOwnPropertyDescriptor(value,key)?.set===undefined)&&required.every(key=>own(value,key)),'Use exact saved-check options.');return Object.fromEntries(Object.keys(value).map(key=>[key,Object.getOwnPropertyDescriptor(value,key).value]));}
 function abortError(){const error=Error('The saved check was cancelled or timed out.');error.name='AbortError';return error;}
 async function hash(text,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function create(input){
  const options=fields(input,['endpoint','pageURL','fetcher','crypto'],['endpoint']),fetcher=options.fetcher||root.fetch?.bind(root),crypto=options.crypto||root.crypto;need(typeof fetcher==='function'&&crypto?.subtle&&typeof options.endpoint==='string','Saved checks are unavailable.');const endpoint=new URL(options.endpoint);need(!endpoint.username&&!endpoint.password&&!endpoint.search&&!endpoint.hash&&endpoint.pathname==='/tasks','Use the configured task endpoint.');
  if(endpoint.protocol!=='https:'){const page=new URL(options.pageURL||root.location?.href||'');need(endpoint.protocol==='http:'&&['localhost','127.0.0.1','[::1]'].includes(endpoint.hostname)&&page.origin===endpoint.origin,'Use HTTPS or the same local QA origin.');}
  const base=endpoint.href;
  async function read(input){
   const options=fields(input,['taskId','proposalId','card','signal'],['taskId','proposalId','card']),value=capture({taskId:options.taskId,proposalId:options.proposalId,card:options.card}),signal=options.signal;need(typeof value.taskId==='string'&&typeof value.proposalId==='string'&&HEX.test(value.taskId)&&IDEA.test(value.proposalId),'Use one exact saved task and public question.');H.sections(value.card);const cardText=C.serialize(value.card),controller=new AbortController();let rejectAbort,reader;const stop=()=>controller.abort(),live=()=>{if(controller.signal.aborted)throw abortError();};
   if(signal){need(typeof signal.aborted==='boolean'&&typeof signal.addEventListener==='function'&&typeof signal.removeEventListener==='function','Use a cancellation signal.');signal.addEventListener('abort',stop,{once:true});if(signal.aborted)stop();}
   const cancelled=new Promise((_,reject)=>{rejectAbort=()=>reject(abortError());controller.signal.addEventListener('abort',rejectAbort,{once:true});if(controller.signal.aborted)rejectAbort();}),timer=setTimeout(stop,LIMITS.timeoutMs);
   const work=async()=>{
    live();need(value.proposalId==='p_'+await hash(cardText,crypto),'The public card changed its canonical identity.');live();const url=base+'/'+value.taskId+'?idea='+value.proposalId,response=await fetcher(url,{method:'GET',signal:controller.signal,redirect:'error',credentials:'omit',cache:'no-store'});live();
    need(response?.ok&&!response.redirected&&(!response.url||response.url===url),'The saved task response changed location or is unavailable.');need(/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The saved task did not return JSON.');const length=response.headers.get('content-length');need(length===null||/^\d+$/.test(length)&&Number(length)<=LIMITS.bytes,'The saved check exceeds its response bound.');reader=response.body?.getReader();need(reader,'The saved task body is unavailable.');let size=0;const chunks=[];
    for(;;){const part=await reader.read();live();if(part.done)break;size+=part.value.byteLength;need(size<=LIMITS.bytes,'The saved check exceeds its response bound.');chunks.push(part.value);}
    const bytes=new Uint8Array(size);let at=0;for(const part of chunks){bytes.set(part,at);at+=part.byteLength;}const body=capture(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)));live();
    need(body&&body.id===value.taskId&&body.plan?.taskId===value.taskId&&typeof body.proposalId==='string'&&IDEA.test(body.proposalId)&&same(body.card,value.card)&&['raw','reviewed'].includes(body.inputVersion),'The saved calculation or original public card changed.');
    need((own(body,'linkedProposalId')?body.linkedProposalId:body.proposalId)===value.proposalId&&(!own(body,'linkedInputVersion')||body.linkedInputVersion===body.inputVersion),'The saved task is not associated with this question and edition.');
    need((body.parentTaskId===null||typeof body.parentTaskId==='string'&&HEX.test(body.parentTaskId))&&(!own(body,'linkedParentTaskId')||body.linkedParentTaskId===body.parentTaskId),'The saved task association changed.');
    E.validateTask(body.plan);await E.checkIdentity(body.plan,crypto);live();
    if(body.state==='not-run'){need(!own(body,'latestRun'),'An unrun calculation cannot advertise a saved result.');return null;}
    need(body.state==='results-verified'&&own(body,'latestRun'),'Use an actual saved result.');const proof=await Summary.prepare({task:body.plan,run:body.latestRun},crypto);live();if(proof===null)return null;const model=Summary.inspect(proof);need(model.taskId===value.taskId&&model.resultId===body.latestRun.id,'The verified summary changed its saved receipt.');return Object.freeze({proof,inputVersion:body.inputVersion,taskId:value.taskId,proposalId:value.proposalId});
   };
   try{const result=await Promise.race([work(),cancelled]);live();return result;}finally{clearTimeout(timer);signal?.removeEventListener('abort',stop);controller.signal.removeEventListener('abort',rejectAbort);controller.abort();try{void reader?.cancel().catch(()=>{});}catch{}}
  }
  return Object.freeze({read});
 }
 const api=Object.freeze({create,LIMITS});if(node)module.exports=api;else root.SavedCheckClient=api;
})(typeof globalThis!=='undefined'?globalThis:this);
