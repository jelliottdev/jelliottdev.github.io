/* Bounded immutable pointers to independently audited published computations. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import Matrix from '../../published-numeric-bank-source.js';
const HEX=/^[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/,PAGE=/^(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))$/;
export const LIMITS=Object.freeze({indexBytes:4*1024*1024,entries:1024,receiptBytes:8*1024*1024,cacheBytes:16*1024*1024});
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),require=(v,m)=>{if(!v)throw Error(m);},freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
const caches=new WeakMap();
export function validateProgramCriterion(value){
 const criterion=J.capture(value,{maxBytes:65536,maxDepth:6,maxNodes:12000});
 const vector=values=>Array.isArray(values)&&values.length>=1&&values.length<=256&&values.every(v=>Number.isInteger(v)&&v>=0&&v<29);
 if(exact(criterion,['kind','values'])&&criterion.kind==='exact-prefix'&&vector(criterion.values))return true;
 require(exact(criterion,['kind','openings'])&&criterion.kind==='exact-prefix-set'&&Array.isArray(criterion.openings)&&criterion.openings.length>=1&&criterion.openings.length<=32,'Invalid published program criterion');
 const ids=new Set(),vectors=new Set();
 for(const opening of criterion.openings){require(exact(opening,['id','values'])&&typeof opening.id==='string'&&/^[a-z][a-z0-9-]{0,63}$/.test(opening.id)&&vector(opening.values),'Invalid published program opening');const key=E.stable(opening.values);require(!ids.has(opening.id)&&!vectors.has(key),'Repeated published program opening');ids.add(opening.id);vectors.add(key);}
 return true;
}
export function checkedProgramIndex(value){
 const index=J.capture(value,{maxBytes:LIMITS.indexBytes,maxDepth:20,maxNodes:300000});require(exact(index,['schema','entries'])&&index.schema==='liberpedia-published-program-source-index-v1'&&Array.isArray(index.entries)&&index.entries.length<=LIMITS.entries,'Malformed published program source index');
 const seen=new Set(),shared=new Map(),selectors=new Set();
 for(const item of index.entries){
  const packed=Object.hasOwn(item,'sourceFormat');
  require(exact(item,['recordId','revision','caseId','inputVersion','taskId','resultId','createdAt','steps','criterion','alphabetSha256','pages','path','sha256','bytes',...(packed?['sourceFormat','programId']:[])]),'Malformed published program pointer');
  if(packed)require(item.sourceFormat==='numeric-bank-matrix-v1'&&typeof item.programId==='string'&&item.programId.length<=100&&SLUG.test(item.programId)&&item.caseId===item.programId+'--all-pages','Invalid shared program selector');
  require(typeof item.recordId==='string'&&item.recordId.length<=100&&SLUG.test(item.recordId)&&typeof item.caseId==='string'&&item.caseId.length<=200&&/^[a-z0-9-]+$/.test(item.caseId)&&['revision','taskId','resultId','alphabetSha256','sha256'].every(k=>typeof item[k]==='string'&&HEX.test(item[k]))&&item.inputVersion==='raw'&&typeof item.createdAt==='string'&&Number.isFinite(Date.parse(item.createdAt))&&new Date(item.createdAt).toISOString()===item.createdAt,'Invalid published program identity');
  require(Array.isArray(item.steps)&&item.steps.length<=8&&item.steps.every(s=>s&&typeof s==='object'&&!Array.isArray(s)),'Invalid published program settings');validateProgramCriterion(item.criterion);
  require(Array.isArray(item.pages)&&item.pages.length>=1&&item.pages.length<=75&&item.pages.every((p,i)=>exact(p,['id','textSha256'])&&PAGE.test(p.id)&&HEX.test(p.textSha256)&&(!i||item.pages[i-1].id<p.id)),'Invalid published program page pins');
  require(typeof item.path==='string'&&item.path.length<=350&&item.path.startsWith('published-evidence/programs/')&&item.path.endsWith('.json')&&/^[a-zA-Z0-9_./-]+$/.test(item.path)&&item.path.split('/').every(p=>p&&p!=='.'&&p!=='..')&&Number.isSafeInteger(item.bytes)&&item.bytes>=1&&item.bytes<=LIMITS.receiptBytes,'Invalid published program source path or byte bound');
  const binding=E.stable([item.sourceFormat||'receipt',item.sha256,item.bytes,item.recordId]),prior=shared.get(item.path);require(prior===undefined||prior===binding,'Shared program source binding changed');shared.set(item.path,binding);
  if(packed){const selector=item.path+'|'+item.programId;require(!selectors.has(selector),'Repeated shared program selector');selectors.add(selector);}
  const id=[item.recordId,item.revision,item.caseId].join('|');require(!seen.has(id),'Repeated published program source');seen.add(id);
 }
 return freeze(index);
}
export async function readProgramPointer(item,{fetcher=globalThis.fetch,crypto:cryptoAPI=globalThis.crypto,signal,timeoutMs=20000}={}){
 require(Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=20000,'Invalid published source deadline');
 // Validate even direct internal callers; callers cannot turn this into a URL fetcher.
 item=checkedProgramIndex({schema:'liberpedia-published-program-source-index-v1',entries:[item]}).entries[0];
 if(signal?.aborted)throw Error('Published source loading cancelled');
 let cache=caches.get(cryptoAPI);if(!cache){cache={bytes:0,entries:new Map()};caches.set(cryptoAPI,cache);}
 const packed=item.sourceFormat==='numeric-bank-matrix-v1',key=(packed?item.sourceFormat:'receipt')+'|'+item.sha256+'|'+item.bytes;
 const controller=new AbortController(),combined=signal?AbortSignal.any([signal,controller.signal]):controller.signal;let timer;
 const work=async()=>{
  const cached=cache.entries.get(key);if(cached){cache.entries.delete(key);cache.entries.set(key,cached);const result=packed?await Matrix.hydrate(cached.handle,item.programId,{crypto:cryptoAPI}):JSON.parse(cached.text);require(!combined.aborted,'Published source loading cancelled');return result;}
  const response=await fetcher('https://jelliottdev.github.io/'+item.path,{redirect:'manual',cache:'no-cache',signal:combined});require(response.ok!==false&&/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'Published program source unavailable');const length=response.headers.get('content-length');require(length===null||/^\d+$/.test(length)&&Number(length)===item.bytes,'Published program source length changed');
  const reader=response.body?.getReader();require(reader,'Published program source is unreadable');let size=0;const parts=[];
  try{while(true){if(combined.aborted)throw Error('Published source loading cancelled');const part=await reader.read();if(part.done)break;size+=part.value.byteLength;require(size<=item.bytes,'Published program source exceeds its pinned byte bound');parts.push(part.value);}}catch(error){try{await reader.cancel();}catch{}throw error;}
  require(size===item.bytes,'Published program source length changed');const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.byteLength;}
  const sha=[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');require(sha===item.sha256,'Published program source bytes changed');if(combined.aborted)throw Error('Published source loading cancelled');
  const source=packed?{handle:await Matrix.prepare(bytes,{sha256:item.sha256,crypto:cryptoAPI})}:{text:new TextDecoder('utf-8',{fatal:true}).decode(bytes)};
  const parsed=packed?await Matrix.hydrate(source.handle,item.programId,{crypto:cryptoAPI}):JSON.parse(source.text);require(!combined.aborted,'Published source loading cancelled');if(item.bytes<=LIMITS.cacheBytes){const prior=cache.entries.get(key);if(prior){cache.bytes-=prior.bytes;cache.entries.delete(key);}while(cache.bytes+item.bytes>LIMITS.cacheBytes&&cache.entries.size){const oldest=cache.entries.keys().next().value;cache.bytes-=cache.entries.get(oldest).bytes;cache.entries.delete(oldest);}cache.entries.set(key,{bytes:item.bytes,...source});cache.bytes+=item.bytes;}return parsed;
 };
 try{return await Promise.race([work(),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Published source loading timed out'));},timeoutMs);})]);}finally{clearTimeout(timer);controller.abort();}
}
export function checkProgramPointerReceipt(item,receipt){
 require(receipt&&receipt.publishedSource&&receipt.provenance&&receipt.source,'Published program proof is missing');const {source,publishedSource:p,provenance}=receipt,projection=provenance.projection;
 require(p.recordId===item.recordId&&p.revision===item.revision&&p.caseId===item.caseId&&source.inputVersion===item.inputVersion&&source.task.taskId===item.taskId&&source.run.id===item.resultId&&source.run.createdAt===item.createdAt&&E.stable(source.task.steps)===E.stable(item.steps)&&E.stable(source.task.criterion)===E.stable(item.criterion)&&projection.alphabetSha256===item.alphabetSha256&&E.stable(source.task.pages.map(p=>({id:p.id,textSha256:provenance.sourcePins.find(pin=>pin.path==='text/'+p.id+'.txt')?.sha256})))===E.stable(item.pages),'Published pointer metadata differs from its verified receipt');return receipt;
}
