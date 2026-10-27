/* Fresh official bytes bind a bundled, build-verified parent plan. No evidence or admission. */
import M from '../../pinned-domain-members.js';
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import {parseInputBundle} from './official-inputs.mjs';
const URL='https://jelliottdev.github.io/data/local-run-inputs.json',MAX=2*1024*1024;
const need=(v,m)=>{if(!v)throw Error(m);};
async function abortable(promise,signal){
 let abort;try{return await Promise.race([Promise.resolve(promise),new Promise((_,reject)=>{abort=()=>reject(Error('Official source loading cancelled.'));signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();})]);}finally{signal.removeEventListener('abort',abort);}
}
async function bytes(fetcher,signal){
 need(!signal.aborted,'Official source loading cancelled.');
 const response=await abortable(Promise.resolve().then(()=>fetcher(URL,{redirect:'manual',signal})),signal);
 need(response.ok&&response.body,'Official source bytes unavailable.');
 const length=response.headers.get('content-length');if(!(length===null||/^\d+$/.test(length)&&Number(length)<=MAX)){response.body.cancel().catch(()=>{});throw Error('Official input bytes exceed their bound.');}
 const reader=response.body.getReader(),parts=[];let count=0;const abort=()=>{reader.cancel().catch(()=>{});};signal.addEventListener('abort',abort,{once:true});
 try{for(;;){need(!signal.aborted,'Official source loading cancelled.');const {done,value}=await abortable(reader.read(),signal);if(done)break;count+=value.byteLength;need(count<=MAX,'Official input bytes exceed their bound.');parts.push(value);}need(!signal.aborted,'Official source loading cancelled.');const raw=new Uint8Array(count);let offset=0;for(const part of parts){raw.set(part,offset);offset+=part.byteLength;}return raw;
 }catch(error){reader.cancel().catch(()=>{});throw error;}finally{signal.removeEventListener('abort',abort);}
}
async function bundle(fetcher,signal){const raw=await bytes(fetcher,signal),source=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));parseInputBundle(source);return source;}
export async function preparePinnedParent({sourceId,domain,template,manifestSha256,bundle:provided,loadDomain,loadBundle,fetcher=globalThis.fetch,crypto=globalThis.crypto,signal}={}){
 const active=signal?AbortSignal.any([signal,AbortSignal.timeout(15000)]):AbortSignal.timeout(15000);
 need(!active.aborted,'Official source loading cancelled.');
 const capturedDomain=J.capture(domain,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000});
 let parent;
 if(provided===undefined&&loadDomain===undefined&&loadBundle===undefined&&crypto===globalThis.crypto){
  const descriptor=M.registeredDescriptor(sourceId),binding=E.stable(J.capture({sourceId,domain:capturedDomain,template,manifestSha256},{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000}));
  const digest=[...new Uint8Array(await abortable(crypto.subtle.digest('SHA-256',new TextEncoder().encode(binding)),active))].map(n=>n.toString(16).padStart(2,'0')).join('');
  need(digest===descriptor.sourceBindingSha256,'The compiled parent source commitments changed.');
  const raw=await bytes(fetcher,active);parent=await abortable(M.prepareRegistered(sourceId,{officialBytes:raw,crypto}),active);
 }else{
  const source=provided===undefined?await abortable(Promise.resolve().then(()=>loadBundle?loadBundle():bundle(fetcher,active)),active):provided;
  parent=await abortable(M.prepare(capturedDomain,{bundle:source,crypto}),active);
 }
 need(!active.aborted,'Official source loading cancelled.');
 need(E.stable(J.capture(domain,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000}))===E.stable(capturedDomain),'The parent source changed during binding.');
 need(E.stable(M.inspect(parent).domain)===E.stable(capturedDomain),'The compiled parent changed its maintained domain.');
 return parent;
}
