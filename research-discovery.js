/* Browse summaries; hydrate one pinned record before inspecting executable declarations. */
(function(root){
 'use strict';
 const SCHEMA='liberpedia-experiment-discovery-v1',FOLLOWUPS='liberpedia-followup-discovery-v1',HEX=/^[a-f0-9]{64}$/,ID=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
 const object=v=>v&&typeof v==='object'&&!Array.isArray(v),text=(v,max)=>typeof v==='string'&&v.trim().length>0&&Array.from(v).length<=max;
 const exact=(v,keys)=>object(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const stable=v=>JSON.stringify(v,(_,value)=>object(value)?Object.fromEntries(Object.keys(value).sort().map(k=>[k,value[k]])):value);
 const source=record=>ID.test(record?.id||'')&&exact(record.record_source,['path','sha256'])&&record.record_source.path==='reference/experiments/'+record.id+'.json'&&HEX.test(record.record_source.sha256);
 const isRecord=record=>record?.discovery_only===true&&source(record);
 function items(record){
  if(!isRecord(record))return [];
  const envelope=record.followup_discovery;if(!exact(envelope,['schema','items'])||envelope.schema!==FOLLOWUPS||!Array.isArray(envelope.items)||envelope.items.length>8)return [];
  const seen=new Set();
  for(const item of envelope.items){
   const keys=['id','kind','title','question','scope_change','limitation','evaluation_kind','available','protocol_sha256',...(Object.hasOwn(item||{},'motivation')?['motivation']:[])];
   if(!exact(item,keys)||!ID.test(item.id)||item.id.length>100||seen.has(item.id)||!['fixed','finite-settings'].includes(item.kind)||!text(item.title,300)||!['question','scope_change','limitation'].every(k=>text(item[k],1200))||Object.hasOwn(item,'motivation')&&!text(item.motivation,1200)||!['measurement','exact-prefix','word-affine-count','word-prime-sums','language-score'].includes(item.evaluation_kind)||typeof item.available!=='boolean'||!HEX.test(item.protocol_sha256))return [];
   seen.add(item.id);
  }
  return envelope.items.slice();
 }
 const available=record=>items(record).filter(item=>item.available);
 function normalize(index){
  if(!object(index)||index.schema!==SCHEMA||!Array.isArray(index.records)||index.records.length>10000)throw Error('Research summaries could not be read.');
  const seen=new Set();
  return {records:index.records.map(row=>{
   if(!object(row)||!source(row)||seen.has(row.id)||row.status!=='published'||!Array.isArray(row.scope?.pages)||typeof row.source_finding!=='string')throw Error('Research summaries could not be read.');
   seen.add(row.id);
   const record={...row,finding:row.source_finding,review:{retested_on:row.retested_on},discovery_only:true};
   if(record.family===null)delete record.family;if(record.record_type===null)delete record.record_type;
   // A malformed descriptor is an unavailable action, never permission to run.
   if(Object.hasOwn(row,'browser_followups'))throw Error('Execution details do not belong in research summaries.');
   return record;
  })};
 }
 async function digest(bytes,crypto){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');}
 function createStore({fetcher=root.fetch?.bind(root),crypto=root.crypto,limit=2,maxBytes=2*1024*1024}={}){
  if(typeof fetcher!=='function'||!crypto?.subtle||!Number.isInteger(limit)||limit<1||limit>2)throw Error('Research records are unavailable.');
  const pending=new Map(),cache=new Map(),queue=[],abort=new AbortController();let active=0,closed=false;
  function drain(){while(!closed&&active<limit&&queue.length){const job=queue.shift();active++;job().finally(()=>{active--;drain();});}}
  async function read(record){
   const response=await fetcher(record.record_source.path,{cache:'no-cache',redirect:'error',signal:AbortSignal.any([abort.signal,AbortSignal.timeout(20000)])});
   if(!response.ok||response.redirected)throw Error('The research record could not be loaded.');
   const reader=response.body?.getReader();if(!reader)throw Error('The research record could not be read.');
   const parts=[];let size=0;try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>maxBytes)throw Error('The research record exceeds its size limit.');parts.push(value);}}catch(error){await reader.cancel().catch(()=>{});throw error;}
   const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
   if(closed||await digest(bytes,crypto)!==record.record_source.sha256)throw Error('The research record has changed. Reload the map to get the latest version.');
   const full=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
   if(full.id!==record.id||full.status!=='published'||!Array.isArray(full.scope?.pages))throw Error('The research record does not match its summary.');
   return {...full,pages:full.scope.pages,...(record.href?{href:record.href}:{})};
  }
  function load(record){
   if(closed)return Promise.reject(Error('Research lookup was closed.'));
   if(!isRecord(record))return Promise.resolve(record);
   const key=record.id+':'+record.record_source.sha256;
   if(cache.has(key))return Promise.resolve(cache.get(key));if(pending.has(key))return pending.get(key);
   const promise=new Promise((resolve,reject)=>{queue.push(async()=>{try{if(closed)throw Error('Research lookup was closed.');const full=await read(record);cache.set(key,full);resolve(full);}catch(error){reject(error);}finally{pending.delete(key);}});});
   pending.set(key,promise);drain();return promise;
  }
  async function hydrate({record,check}){
   if(!isRecord(record))return {record,check};
   const descriptor=items(record).find(item=>item.id===check?.id);
   if(!descriptor||stable(descriptor)!==stable(check))throw Error('The prepared check does not match its summary.');
   const full=await load(record),matches=full.browser_followups?.filter(item=>item.id===check.id)||[];
   if(matches.length!==1||await digest(new TextEncoder().encode(stable(matches[0])),crypto)!==descriptor.protocol_sha256)throw Error('The prepared check has changed. Reload the map.');
   return {record:full,check:matches[0]};
  }
  return {load,hydrate,destroy(){if(closed)return;closed=true;abort.abort();cache.clear();for(const job of queue.splice(0))void job();}};
 }
 const api={normalize,isRecord,items,available,createStore};if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchDiscovery=api;
})(typeof globalThis!=='undefined'?globalThis:this);
