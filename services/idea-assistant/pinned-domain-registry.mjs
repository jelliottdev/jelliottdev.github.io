/* Maintained server authority for complete domains. No request can replace pins. */
import sources from './pinned-domain-sources.mjs';
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
const BASE='https://jelliottdev.github.io/',MAX=2*1024*1024;
const capture=v=>J.capture(v,{maxBytes:MAX,maxDepth:24,maxNodes:100000});
const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
const maintained=new Map(sources.map(source=>[source.sourceId,freeze(capture(source))]));
const instances=new WeakMap();
async function bytes(response){
 if(!response.ok||!response.body)throw Error('Independent control commitments are unavailable.');
 const declared=response.headers.get('content-length');
 if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>MAX))throw Error('Independent control commitments exceed their bound.');
 const reader=response.body.getReader(),chunks=[];let size=0;
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX)throw Error('Independent control commitments exceed their bound.');chunks.push(value);}}
 catch(error){try{await reader.cancel();}catch{}throw error;}
 const raw=new Uint8Array(size);let offset=0;for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.byteLength;}return raw;
}
async function digest(raw){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(v=>v.toString(16).padStart(2,'0')).join('');}
export function listPinnedDomains(){return [...maintained.values()].map(source=>({sourceId:source.sourceId,bankId:source.domain.bank.bankId,settings:source.domain.bank.count,pages:source.domain.pages.length}));}
export function createPinnedDomainSourceLoader(fetcher=globalThis.fetch){
 if(typeof fetcher!=='function')throw Error('A maintained source fetcher is required.');
 if(instances.has(fetcher))return instances.get(fetcher);
 const cached=new Map(),pending=new Map();
 const loadDomain=async function(sourceId){
  const source=maintained.get(sourceId);if(!source)throw Error('Choose a maintained complete search.');
  const result=raw=>({sourceId,domain:capture(source.domain),template:capture(source.template),manifestSha256:source.manifestSha256,manifestBytes:new Uint8Array(raw)});
  if(cached.has(sourceId))return result(cached.get(sourceId));
  if(!pending.has(sourceId)){
   const work=(async()=>{const raw=await bytes(await fetcher(BASE+source.manifestPath,{redirect:'manual',signal:AbortSignal.timeout(15000)}));if(await digest(raw)!==source.manifestSha256)throw Error('Independent control commitments changed.');
    // Validate the exact committed envelope before retaining immutable raw bytes.
    const manifest=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
    if(manifest.schema!=='liberpedia-pinned-control-commitments-v1'||manifest.entries?.length!==source.domain.bank.count||E.stable(manifest)!==new TextDecoder().decode(raw).trim())throw Error('Independent control commitment envelope changed.');
    cached.set(sourceId,new Uint8Array(raw));return raw;})();
   pending.set(sourceId,work);work.finally(()=>pending.delete(sourceId)).catch(()=>{});
  }
  return result(await pending.get(sourceId));
 };
 instances.set(fetcher,loadDomain);return loadDomain;
}
