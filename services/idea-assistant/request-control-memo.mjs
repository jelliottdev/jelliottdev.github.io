/* One invocation's duplicate control work only. This is not admission authority.
 * Independent preparation authorization must still validate the returned suite. */
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import J from '../../finite-json.js';
export function createRequestControlMemo({prepare=Controls.prepare,crypto=globalThis.crypto,maxEntries=4,maxBytes=2*1024*1024}={}){
 if(typeof prepare!=='function'||!Number.isSafeInteger(maxEntries)||maxEntries<1||maxEntries>32||!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>8*1024*1024)throw Error('Invalid request control memo bounds');
 const entries=new Map(),pending=new Map(),encoder=new TextEncoder();let bytes=0,pendingBytes=0;
 const capture=value=>J.capture(value,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:300000}),text=value=>E.stable(capture(value)),size=value=>encoder.encode(value).length;
 function remember(key,value){const cost=size(key)+size(value);if(cost>maxBytes)return;const prior=entries.get(key);if(prior){bytes-=prior.cost;entries.delete(key);}entries.set(key,{value,cost});bytes+=cost;while(entries.size>maxEntries||bytes>maxBytes){const oldest=entries.keys().next().value;bytes-=entries.get(oldest).cost;entries.delete(oldest);}}
 async function read(task,cryptoAPI=crypto){
  if(cryptoAPI!==crypto)throw Error('Request control memo belongs to another crypto identity');
  const key=text(task),check=()=>{if(text(task)!==key)throw Error('The original task changed during request control preparation');};
  const hit=entries.get(key);if(hit){entries.delete(key);entries.set(key,hit);check();return JSON.parse(hit.value);}
  let work=pending.get(key)?.work;
  if(!work){
   const build=async()=>{const detached=JSON.parse(key),suite=await prepare(detached,crypto);if(text(detached)!==key)throw Error('The detached control target changed during preparation');return text(suite);};
   work=build();const cost=size(key);
   if(pending.size<maxEntries&&pendingBytes+cost<=maxBytes){const item={work,cost};pending.set(key,item);pendingBytes+=cost;work.finally(()=>{if(pending.get(key)===item){pending.delete(key);pendingBytes-=cost;}}).catch(()=>{});}
  }
  const result=await work;check();remember(key,result);return JSON.parse(result);
 }
 return Object.freeze({read,inspect:()=>Object.freeze({entries:entries.size,bytes,pending:pending.size,pendingBytes})});
}
