/* Bind an authenticated archived output to its exact canonical variation question. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,Client=node?require('./published-output-client.js'):root.PublishedOutputClient,Q=node?require('./task-parameter-question.js'):root.TaskParameterQuestion;
 const MAX=8*1024*1024,ensure=(v,m)=>{if(!v)throw Error(m);},exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),same=(a,b)=>E.stable(a)===E.stable(b),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function options(value){ensure(value&&typeof value==='object'&&!Array.isArray(value),'Use explicit archived question options.');const out={};for(const key of Reflect.ownKeys(value)){const d=Object.getOwnPropertyDescriptor(value,key);ensure(typeof key==='string'&&['baseURL','fetcher','crypto','pageURL','signal','timeoutMs'].includes(key)&&d.enumerable&&Object.hasOwn(d,'value'),'Use explicit archived question options.');out[key]=d.value;}return out;}
 function service(baseURL,pageURL){ensure(typeof baseURL==='string','Use a published-evidence service origin.');const url=new URL(baseURL);ensure(!url.username&&!url.password&&!url.search&&!url.hash&&url.pathname==='/','Use a service origin without a path.');if(url.protocol!=='https:'){const page=new URL(pageURL);ensure(url.protocol==='http:'&&['localhost','127.0.0.1','[::1]'].includes(url.hostname)&&url.origin===page.origin,'Use HTTPS or the same local testing origin.');}return url.origin;}
 async function load(model,supplied={}){
  ensure(Client?.isVerified(model),'Use the original authenticated archived output.');
  const o=options(supplied),crypto=o.crypto||root.crypto,fetcher=o.fetcher||root.fetch?.bind(root),timeoutMs=o.timeoutMs??25000,pageURL=o.pageURL??root.location?.href??'';
  ensure(crypto?.subtle&&typeof fetcher==='function'&&Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=45000,'Archived question inspection is unavailable.');
  const url=service(o.baseURL,pageURL)+'/parameter-questions/archive-context',ref={recordId:model.publishedSource.recordId,revision:model.publishedSource.revision,caseId:model.publishedSource.caseId},controller=new AbortController(),cancel=()=>controller.abort();
  o.signal?.addEventListener('abort',cancel,{once:true});if(o.signal?.aborted)cancel();
  let reader,rejectAbort;const aborted=new Promise((_,reject)=>{rejectAbort=()=>{try{void reader?.cancel().catch(()=>{});}catch{}const error=Error('Archived question loading was cancelled.');error.name='AbortError';reject(error);};controller.signal.addEventListener('abort',rejectAbort,{once:true});}),timer=setTimeout(cancel,timeoutMs),live=()=>{if(controller.signal.aborted){const error=Error('Archived question loading was cancelled.');error.name='AbortError';throw error;}};
  const work=async()=>{
   live();const expected=await Q.archived({task:model.task,inputVersion:model.inputVersion},crypto);live();
   const response=await fetcher(url,{method:'POST',headers:{Accept:'application/json','Content-Type':'application/json'},body:JSON.stringify(ref),redirect:'error',credentials:'omit',cache:'no-store',signal:controller.signal});
   if(controller.signal.aborted){try{void response?.body?.cancel().catch(()=>{});}catch{}live();}
   ensure(response?.ok&&!response.redirected&&(!response.url||response.url===url)&&/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The archived question could not be loaded.');
   const declared=response.headers.get('content-length');ensure(declared===null||/^\d+$/.test(declared)&&Number(declared)<=MAX,'The archived question exceeds its byte bound.');reader=response.body?.getReader();ensure(reader,'The archived question body is missing.');const chunks=[];let size=0;
   for(;;){live();const part=await Promise.race([reader.read(),aborted]);if(part.done)break;ensure(part.value instanceof Uint8Array,'The archived question body is invalid.');size+=part.value.byteLength;ensure(size<=MAX,'The archived question exceeds its byte bound.');chunks.push(part.value);}
   const bytes=new Uint8Array(size);let offset=0;for(const part of chunks){bytes.set(part,offset);offset+=part.byteLength;}
   const body=J.capture(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)),{maxBytes:MAX,maxDepth:24,maxNodes:500000});live();
   ensure(exact(body,['schema','context'])&&body.schema==='liberpedia-archived-parameter-context-v1','The archived question changed its envelope.');
   const context=body.context,source={kind:'archived-program',proposalId:expected.proposalId,...ref};
   ensure(exact(context,['task','card','source','inputVersion','run'])&&same(context.task,model.task)&&same(context.card,expected.card)&&same(context.source,source)&&context.inputVersion===model.inputVersion&&same(context.run,model.run),'The archived question differs from the displayed calculation.');
   live();return freeze(context);
  };
  try{return await Promise.race([work(),aborted]);}catch(error){try{void reader?.cancel().catch(()=>{});}catch{}throw error;}finally{clearTimeout(timer);o.signal?.removeEventListener('abort',cancel);controller.signal.removeEventListener('abort',rejectAbort);}
 }
 const api={load};if(node)module.exports=api;else root.PublishedVariationContext=api;
})(typeof globalThis!=='undefined'?globalThis:this);
