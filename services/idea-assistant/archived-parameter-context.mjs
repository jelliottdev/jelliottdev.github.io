/* Read-only archived calculation -> exact canonical source question. */
import J from '../../finite-json.js';
import Q from '../../task-parameter-question.js';
import V from '../../task-parameter-variants.js';
import {archivedVariationNavigation} from './archived-variation-navigation.mjs';
import {readPublishedEvidence} from './published-evidence.mjs';
const HEX=/^[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
// Navigation is optional. Its bytes must never displace a usable context.
export function boundedContextBody(value){
 const fits=body=>new TextEncoder().encode(JSON.stringify(body)).byteLength<=8*1024*1024;
 if(fits(value))return value;
 if(Object.hasOwn(value,'navigationHints')&&value.navigationHints!==null){const fallback={...value,navigationHints:null};if(fits(fallback))return fallback;}
 throw Error('The archived context exceeds its response bound');
}
async function readBody(request,signal){
 const length=request.headers.get('content-length');if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||'')||length!==null&&(!/^\d+$/.test(length)||Number(length)>1024))throw Error();
 const reader=request.body?.getReader();if(!reader||signal.aborted)throw Error();let size=0,stop;const chunks=[],cancelled=new Promise((_,reject)=>{stop=()=>{void reader.cancel().catch(()=>{});reject(Error('Cancelled'));};signal.addEventListener('abort',stop,{once:true});});
 try{while(true){const part=await Promise.race([reader.read(),cancelled]);if(part.done)break;size+=part.value.byteLength;if(size>1024)throw Error();chunks.push(part.value);}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return J.capture(JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(bytes)),{maxBytes:1024,maxDepth:3,maxNodes:8});}
 catch(error){try{void reader.cancel().catch(()=>{});}catch{}throw error;}finally{signal.removeEventListener('abort',stop);}
}
export function createArchivedParameterContextHandler({crypto=globalThis.crypto,fetcher=globalThis.fetch,registry,history,programIndex}={}){
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers}),allowed=env?.SITE_ORIGIN;
  try{if(typeof allowed!=='string'||new URL(allowed).origin!==allowed||!['https:','http:'].includes(new URL(allowed).protocol))throw Error();}catch{return reply({error:'Archived variations are unavailable.'},503);}
  if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url);if(url.pathname!=='/parameter-questions/archive-context'||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){const hs=(request.headers.get('access-control-request-headers')||'').split(',').map(value=>value.trim().toLowerCase()).filter(Boolean);return request.headers.get('access-control-request-method')==='POST'&&hs.every(value=>value==='content-type')?new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}}):reply({error:'Request is not allowed.'},403);}
  if(request.method!=='POST'){headers.Allow='POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;if(!rate?.limit||!crypto?.subtle)return reply({error:'Archived variations are unavailable.'},503);
  const controller=new AbortController(),abort=()=>controller.abort();request.signal.addEventListener('abort',abort,{once:true});if(request.signal.aborted)abort();const timer=setTimeout(abort,45000);let checked=false;
  try{
   const body=await readBody(request,controller.signal),opted=body&&Object.hasOwn(body,'includeNavigationHints');
   if(opted&&body.includeNavigationHints!==true)throw Error();
   const ref=opted?Object.fromEntries(Object.entries(body).filter(([key])=>key!=='includeNavigationHints')):body;
   if(!ref||typeof ref!=='object'||Array.isArray(ref)||Object.keys(ref).length!==3||!['recordId','revision','caseId'].every(key=>Object.hasOwn(ref,key))||typeof ref.recordId!=='string'||ref.recordId.length>100||!SLUG.test(ref.recordId)||typeof ref.revision!=='string'||!HEX.test(ref.revision)||typeof ref.caseId!=='string'||ref.caseId.length>200||!/^[a-z0-9][a-z0-9-]*$/.test(ref.caseId))throw Error();checked=true;
   if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   const source=await readPublishedEvidence({...ref,crypto,fetcher,registry,history,programIndex,signal:controller.signal});
   if(controller.signal.aborted)throw Error();if(!source)return reply({error:'The archived calculation is unavailable.'},404);
   if(source.provenance.schema!=='liberpedia-published-program-projection-v1'||!V.suggestions(source.task).length)return reply({error:'This archived calculation has no supported variations.'},422);
   const parent=await Q.archived({task:source.task,inputVersion:source.inputVersion},crypto);if(controller.signal.aborted)throw Error();
   let navigationHints;
   if(opted){try{navigationHints=await archivedVariationNavigation({task:source.task,inputVersion:source.inputVersion},{crypto,registry,programIndex,signal:controller.signal});}catch{if(controller.signal.aborted)throw Error();navigationHints=null;}}
   const value={schema:'liberpedia-archived-parameter-context-v1',context:{task:source.task,card:parent.card,source:{kind:'archived-program',proposalId:parent.proposalId,...ref},inputVersion:source.inputVersion,run:source.run},...(opted?{navigationHints}:{})};
   return reply(boundedContextBody(value));
  }catch{return reply({error:controller.signal.aborted?'Loading variations was cancelled. Please retry.':'The archived calculation could not be prepared for variations.'},checked||controller.signal.aborted?503:400);}
  finally{clearTimeout(timer);request.signal.removeEventListener('abort',abort);}
 };
}
