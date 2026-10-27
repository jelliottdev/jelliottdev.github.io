/* Bind an authenticated archived output to its exact canonical variation question. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,Client=node?require('./published-output-client.js'):root.PublishedOutputClient,Q=node?require('./task-parameter-question.js'):root.TaskParameterQuestion,V=node?require('./task-parameter-variants.js'):root.TaskParameterVariants;
 const MAX=8*1024*1024,ensure=(v,m)=>{if(!v)throw Error(m);},exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),same=(a,b)=>E.stable(a)===E.stable(b),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function options(value){ensure(value&&typeof value==='object'&&!Array.isArray(value),'Use explicit archived question options.');const out={};for(const key of Reflect.ownKeys(value)){const d=Object.getOwnPropertyDescriptor(value,key);ensure(typeof key==='string'&&['baseURL','fetcher','crypto','pageURL','signal','timeoutMs'].includes(key)&&d.enumerable&&Object.hasOwn(d,'value'),'Use explicit archived question options.');out[key]=d.value;}return out;}
 function service(baseURL,pageURL){ensure(typeof baseURL==='string','Use a published-evidence service origin.');const url=new URL(baseURL);ensure(!url.username&&!url.password&&!url.search&&!url.hash&&url.pathname==='/','Use a service origin without a path.');if(url.protocol!=='https:'){const page=new URL(pageURL);ensure(url.protocol==='http:'&&['localhost','127.0.0.1','[::1]'].includes(url.hostname)&&url.origin===page.origin,'Use HTTPS or the same local testing origin.');}return url.origin;}
 // These pointers only help navigation. They never establish result coverage,
 // authorize creation, or replace the ordinary fresh preview and proof checks.
 async function checkNavigationHints(input,context,crypto=root.crypto){
  try{
   if(input==null)return null;
   const value=J.capture(input,{maxBytes:2*1024*1024,maxDepth:8,maxNodes:40000}),c=J.capture(context,{maxBytes:MAX,maxDepth:24,maxNodes:500000}),hex=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),slug=v=>typeof v==='string'&&v.length<=100&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(v);
   ensure(exact(value,['schema','parentTaskHash','inputVersion','catalogGeneration','choices'])&&value.schema==='liberpedia-archived-variation-navigation-v1'&&hex(value.parentTaskHash)&&hex(value.catalogGeneration)&&['raw','reviewed'].includes(value.inputVersion)&&value.inputVersion===c.inputVersion&&Array.isArray(value.choices)&&value.choices.length<=2080&&crypto?.subtle,'Invalid archived navigation hints');
   await E.checkIdentity(c.task,crypto);
   const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(c.task)));
   ensure(Array.from(new Uint8Array(hash),v=>v.toString(16).padStart(2,'0')).join('')===value.parentTaskHash,'Navigation hints belong to another calculation');
   const allowed=new Set(V.suggestions(c.task).map(item=>E.stable(item.selection))),seen=new Set();
   for(const item of value.choices){
    ensure(exact(item,['selection','reference','matchingPageCount']),'Invalid archived navigation choice');
    const key=E.stable(V.selection(item.selection)),r=item.reference;
    ensure(allowed.has(key)&&!seen.has(key)&&exact(r,['recordId','revision','caseId'])&&slug(r.recordId)&&hex(r.revision)&&typeof r.caseId==='string'&&r.caseId.length<=200&&/^[a-z0-9][a-z0-9-]*$/.test(r.caseId)&&Number.isSafeInteger(item.matchingPageCount)&&item.matchingPageCount>=1&&item.matchingPageCount<=c.task.pages.length,'Invalid archived navigation reference');seen.add(key);
   }
   return freeze(value);
  }catch{return null;}
 }
 async function loadContext(model,supplied={},includeHints=false){
  ensure(Client?.isVerified(model),'Use the original authenticated archived output.');
  const o=options(supplied),crypto=o.crypto||root.crypto,fetcher=o.fetcher||root.fetch?.bind(root),timeoutMs=o.timeoutMs??25000,pageURL=o.pageURL??root.location?.href??'';
  ensure(crypto?.subtle&&typeof fetcher==='function'&&Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=45000,'Archived question inspection is unavailable.');
  const url=service(o.baseURL,pageURL)+'/parameter-questions/archive-context',ref={recordId:model.publishedSource.recordId,revision:model.publishedSource.revision,caseId:model.publishedSource.caseId},controller=new AbortController(),cancel=()=>controller.abort();
  o.signal?.addEventListener('abort',cancel,{once:true});if(o.signal?.aborted)cancel();
  let reader,rejectAbort;const aborted=new Promise((_,reject)=>{rejectAbort=()=>{try{void reader?.cancel().catch(()=>{});}catch{}const error=Error('Archived question loading was cancelled.');error.name='AbortError';reject(error);};controller.signal.addEventListener('abort',rejectAbort,{once:true});}),timer=setTimeout(cancel,timeoutMs),live=()=>{if(controller.signal.aborted){const error=Error('Archived question loading was cancelled.');error.name='AbortError';throw error;}};
  const work=async()=>{
   live();const expected=await Q.archived({task:model.task,inputVersion:model.inputVersion},crypto);live();
   const response=await fetcher(url,{method:'POST',headers:{Accept:'application/json','Content-Type':'application/json'},body:JSON.stringify({...ref,...(includeHints?{includeNavigationHints:true}:{})}),redirect:'error',credentials:'omit',cache:'no-store',signal:controller.signal});
   if(controller.signal.aborted){try{void response?.body?.cancel().catch(()=>{});}catch{}live();}
   ensure(response?.ok&&!response.redirected&&(!response.url||response.url===url)&&/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The archived question could not be loaded.');
   const declared=response.headers.get('content-length');ensure(declared===null||/^\d+$/.test(declared)&&Number(declared)<=MAX,'The archived question exceeds its byte bound.');reader=response.body?.getReader();ensure(reader,'The archived question body is missing.');const chunks=[];let size=0;
   for(;;){live();const part=await Promise.race([reader.read(),aborted]);if(part.done)break;ensure(part.value instanceof Uint8Array,'The archived question body is invalid.');size+=part.value.byteLength;ensure(size<=MAX,'The archived question exceeds its byte bound.');chunks.push(part.value);}
   const bytes=new Uint8Array(size);let offset=0;for(const part of chunks){bytes.set(part,offset);offset+=part.byteLength;}
   const body=J.capture(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)),{maxBytes:MAX,maxDepth:24,maxNodes:500000});live();
   ensure(exact(body,['schema','context',...(includeHints&&Object.hasOwn(body,'navigationHints')?['navigationHints']:[])])&&body.schema==='liberpedia-archived-parameter-context-v1','The archived question changed its envelope.');
   const context=body.context,source={kind:'archived-program',proposalId:expected.proposalId,...ref};
   ensure(exact(context,['task','card','source','inputVersion','run'])&&same(context.task,model.task)&&same(context.card,expected.card)&&same(context.source,source)&&context.inputVersion===model.inputVersion&&same(context.run,model.run),'The archived question differs from the displayed calculation.');
   live();return includeHints?freeze({context,navigationHints:body.navigationHints??null}):freeze(context);
  };
  try{return await Promise.race([work(),aborted]);}catch(error){try{void reader?.cancel().catch(()=>{});}catch{}throw error;}finally{clearTimeout(timer);o.signal?.removeEventListener('abort',cancel);controller.signal.removeEventListener('abort',rejectAbort);}
 }
 const load=(model,supplied)=>loadContext(model,supplied,false),loadReview=(model,supplied)=>loadContext(model,supplied,true);
 const api={load,loadReview,checkNavigationHints};if(node)module.exports=api;else root.PublishedVariationContext=api;
})(typeof globalThis!=='undefined'?globalThis:this);
