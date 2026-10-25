/* Whole ordinary grouped outputs. Validation grants storage/recovery, never execution or coverage. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,R=node?require('./computation-evidence.js'):root.ComputationEvidence,J=node?require('./finite-json.js'):root.FiniteJSON;
 const SCHEMA='liberpedia-factored-group-pending-v1',KINDS=Object.freeze(['exact-prefix','measurement','word-affine-count','word-prime-sums','language-score']),HEX=/^[a-f0-9]{64}$/,MAX=8*1024*1024;
 const exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===k.length&&k.every(n=>Object.hasOwn(v,n)),capture=v=>J.capture(v,{maxBytes:MAX,maxDepth:24,maxNodes:500000}),size=v=>new TextEncoder().encode(E.stable(v)).byteLength;
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 async function id(domainId,programId,caseIds,crypto=root.crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable({schema:'liberpedia-page-group-v1',domainId,programId,caseIds}))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 async function validate({domainId,payload},crypto=root.crypto){
  if(typeof domainId!=='string'||!HEX.test(domainId))throw Error('Use the original grouped search identity.');
  const data=capture(payload);if(!exact(data,['schema','inputVersion','groups'])||data.schema!==SCHEMA||!['raw','reviewed'].includes(data.inputVersion)||!Array.isArray(data.groups)||!data.groups.length||data.groups.length>12)throw Error('Use bounded completed page-group outputs.');
  const seen=new Set(),tasks=new Set(),cases=new Set();let runes=0,chars=0,taskBytes=0;
  for(const group of data.groups){
   if(!exact(group,['id','programId','pageIds','caseIds','task','result'])||typeof group.id!=='string'||!HEX.test(group.id)||typeof group.programId!=='string'||!HEX.test(group.programId)||seen.has(group.id)||tasks.has(group.task?.taskId)||!Array.isArray(group.pageIds)||!group.pageIds.length||group.pageIds.length>75||!Array.isArray(group.caseIds)||group.caseIds.length!==group.pageIds.length||!KINDS.includes(group.task?.criterion?.kind))throw Error('A completed group descriptor changed.');
   if(group.pageIds.some((p,i)=>typeof p!=='string'||!/^lp[12]-\d{2}$/.test(p)||i&&group.pageIds[i-1]>=p)||group.caseIds.some(c=>typeof c!=='string'||!HEX.test(c)||cases.has(c)))throw Error('A completed group repeats or changes its pages.');
   const described=await R.describe(group.task,data.inputVersion,crypto);
   if(described.protocolId!==group.programId||E.stable(described.pages.map(p=>p.id))!==E.stable(group.pageIds)||E.stable(described.pages.map(p=>p.caseId))!==E.stable(group.caseIds)||await id(domainId,group.programId,group.caseIds,crypto)!==group.id)throw Error('A completed group names another exact computation.');
   if(size(group.task)>800000||size({task:group.task,inputVersion:data.inputVersion,run:{id:'0'.repeat(64),createdAt:'1970-01-01T00:00:00.000Z',result:group.result}})>2*1024*1024)throw Error('A whole grouped output exceeds its retained byte bound.');
   const alphabet=new Set(group.task.alphabet.map(v=>v.rune));for(const page of group.task.pages){for(const ch of page.text){chars++;if(alphabet.has(ch))runes++;}}taskBytes+=size(group.task);
   if(runes>20000||chars>300000||taskBytes>2*1024*1024)throw Error('The completed groups exceed their reviewed work bound.');
   group.result=await E.verify(group.task,group.result,crypto);seen.add(group.id);tasks.add(group.task.taskId);for(const c of group.caseIds){if(cases.has(c))throw Error('A completed scientific case is repeated.');cases.add(c);}
  }
  data.groups.sort((a,b)=>a.id.localeCompare(b.id));return freeze(data);
 }
 const api={SCHEMA,KINDS,id,validate};if(node)module.exports=api;else root.FactoredGroupOutput=api;
})(typeof globalThis!=='undefined'?globalThis:this);
