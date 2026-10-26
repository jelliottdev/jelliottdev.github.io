/* Bounded isolate-local cache of complete independent implementation controls.
 * Call only after validating a stored task. Admission still prepares controls
 * afresh; cached wire data carries no permission to run or admit a result. */
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
export function createReadControlCache({prepare=Controls.prepare,maxEntries=32,maxBytes=2*1024*1024}={}){
 if(!Number.isSafeInteger(maxEntries)||maxEntries<1||maxEntries>128||!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>8*1024*1024)throw Error('Invalid control cache bounds');
 const entries=new Map(),pending=new Map(),encoder=new TextEncoder();let bytes=0;
 const key=task=>E.stable(task);
 function prime(task,suite){const k=key(task),text=E.stable(suite),size=encoder.encode(k).length+encoder.encode(text).length;if(size>maxBytes)return;const previous=entries.get(k);if(previous){bytes-=previous.size;entries.delete(k);}entries.set(k,{text,size});bytes+=size;while(entries.size>maxEntries||bytes>maxBytes){const oldest=entries.keys().next().value;bytes-=entries.get(oldest).size;entries.delete(oldest);}}
 async function read(task,crypto=globalThis.crypto){const k=key(task),hit=entries.get(k);if(hit){entries.delete(k);entries.set(k,hit);return JSON.parse(hit.text);}if(pending.has(k))return JSON.parse(await pending.get(k));
  // In-flight entries are bounded separately; excess concurrent reads compute
  // normally rather than growing retained promises without a bound.
  const build=async()=>{const captured=JSON.parse(k),suite=await prepare(captured,crypto);if(E.stable(captured)!==k)throw Error('The stored task changed while preparing controls');prime(captured,suite);return E.stable(suite);};
  const work=build();if(pending.size>=maxEntries)return JSON.parse(await work);pending.set(k,work);try{return JSON.parse(await work);}finally{if(pending.get(k)===work)pending.delete(k);}
 }
 return Object.freeze({read,prime,inspect:()=>Object.freeze({entries:entries.size,bytes,pending:pending.size})});
}
