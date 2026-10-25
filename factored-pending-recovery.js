/* Recover original local outputs, never a historical or current question proof.
 * Public saving still requires the server's immutable task association/replay. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,R=node?require('./computation-evidence.js'):root.ComputationEvidence,J=node?require('./finite-json.js'):root.FiniteJSON;
 const records=new WeakMap(),HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/,MAX=8*1024*1024,enc=new TextEncoder();
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const capture=(v,maxBytes=MAX)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000});
 const live=signal=>{if(signal?.aborted)throw new DOMException('Local output recovery cancelled.','AbortError');};
 const hash=async(v,c)=>[...new Uint8Array(await c.subtle.digest('SHA-256',enc.encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
 function checkedDescriptor(input){const d=capture(input,4096);if(!exact(d,['domainId','inputVersion','caseCount','pageIds','bytes','sha256'])||typeof d.domainId!=='string'||!HEX.test(d.domainId)||typeof d.sha256!=='string'||!HEX.test(d.sha256)||!['raw','reviewed'].includes(d.inputVersion)||!Number.isSafeInteger(d.caseCount)||d.caseCount<1||d.caseCount>12||!Number.isSafeInteger(d.bytes)||d.bytes<1||d.bytes>MAX||!Array.isArray(d.pageIds)||!d.pageIds.length||d.pageIds.length>d.caseCount||d.pageIds.some((id,i)=>typeof id!=='string'||!/^lp[12]-\d{2}$/.test(id)||i&&d.pageIds[i-1]>=id))throw Error('Select one exact retained-output descriptor.');return freeze(d);}
 async function readPinned(store,namespace,descriptor,crypto,signal){
  live(signal);const data=capture(await store.getPinnedPending(namespace,descriptor));live(signal);
  if(!exact(data,['inputVersion','cases'])||data.inputVersion!==descriptor.inputVersion||!Array.isArray(data.cases)||data.cases.length!==descriptor.caseCount||enc.encode(E.stable(data)).byteLength!==descriptor.bytes||await hash(data,crypto)!==descriptor.sha256)throw Error('Retained output no longer matches the selected original bytes.');live(signal);return data;
 }
 async function load({store,proposalId,descriptor,signal},crypto=root.crypto){
  const selected=checkedDescriptor(descriptor);if(typeof proposalId!=='string'||!IDEA.test(proposalId)||typeof store?.getPinnedPending!=='function'||typeof store?.removePending!=='function'||!crypto?.subtle)throw Error('Use the original saved idea and pinned local-output storage.');
  const namespace=freeze({proposalId,domainId:selected.domainId}),data=await readPinned(store,namespace,selected,crypto,signal),seen=new Set(),tasks=new Set(),cases=[];
  for(const item of data.cases){if(!exact(item,['caseId','programId','pageId','task','result'])||typeof item.caseId!=='string'||!HEX.test(item.caseId)||typeof item.programId!=='string'||!HEX.test(item.programId)||seen.has(item.caseId)||tasks.has(item.task?.taskId)||item.task?.engine!==E.ENGINE||item.task?.criterion?.kind!=='exact-prefix'||!Array.isArray(item.task?.pages)||item.task.pages.length!==1||item.task.pages[0].id!==item.pageId)throw Error('A retained case changed its original task descriptor.');
   await E.checkIdentity(item.task,crypto);live(signal);const described=await R.describe(item.task,data.inputVersion,crypto);live(signal);if(described.protocolId!==item.programId||described.pages[0].caseId!==item.caseId)throw Error('A retained output names another exact computation.');
   const result=await E.verify(item.task,item.result,crypto);live(signal);cases.push({...item,result,resultId:await hash(result,crypto)});live(signal);seen.add(item.caseId);tasks.add(item.task.taskId);
  }
  const pageIds=[...new Set(cases.map(item=>item.pageId))].sort();if(E.stable(pageIds)!==E.stable(selected.pageIds))throw Error('Retained pages changed after selection.');
  const proof=freeze({schema:'liberpedia-retained-output-recovery-v1',proposalId,domainId:selected.domainId,inputVersion:data.inputVersion,caseCount:cases.length,pageIds,cases,meaning:'Verified local outputs only. Saving requires their original server task associations. These outputs do not establish coverage of the current question.'});
  records.set(proof,{store,namespace,descriptor:selected,data,crypto});return proof;
 }
 function inspect(proof){if(!records.has(proof))throw Error('Use independently verified pinned retained outputs.');return proof;}
 async function save(proof,{transport,store,signal}={}){
  inspect(proof);const saved=records.get(proof);if(typeof transport!=='function'||store!==undefined&&store!==saved.store)throw Error('Save through the original result endpoint and retained-output store.');
  await readPinned(saved.store,saved.namespace,saved.descriptor,saved.crypto,signal);
  const body=freeze({domainId:proof.domainId,results:proof.cases.map(item=>({taskId:item.task.taskId,result:item.result}))});live(signal);const value=capture(await transport(body,{signal}));live(signal);
  if(!exact(value,['schema','proposalId','receipts'])||value.schema!=='liberpedia-finite-search-results-v1'||value.proposalId!==proof.proposalId||!Array.isArray(value.receipts)||value.receipts.length!==proof.cases.length)throw Error('The saved output receipts do not match the recovered originals.');
  const seen=new Set();for(const receipt of value.receipts){const item=proof.cases.find(item=>item.task.taskId===receipt?.taskId);if(!item||seen.has(receipt.taskId)||!exact(receipt,['taskId','state','latestRun'])||receipt.state!=='results-verified'||!exact(receipt.latestRun,['id','createdAt','result'])||receipt.latestRun.id!==item.resultId||typeof receipt.latestRun.createdAt!=='string'||!Number.isFinite(Date.parse(receipt.latestRun.createdAt))||new Date(receipt.latestRun.createdAt).toISOString()!==receipt.latestRun.createdAt||E.stable(receipt.latestRun.result)!==E.stable(item.result))throw Error('A saved receipt changed an original recovered calculation.');
   const verified=await E.verify(item.task,receipt.latestRun.result,saved.crypto);live(signal);if(await hash(verified,saved.crypto)!==receipt.latestRun.id)throw Error('A recovered output receipt digest changed.');live(signal);receipt.latestRun.result=verified;seen.add(receipt.taskId);
  }
  let cleanup='unavailable';try{live(signal);const result=await saved.store.removePending(saved.namespace,proof.cases.map(item=>({caseId:item.caseId,result:item.result})));cleanup=['removed','absent','stale'].includes(result?.state)?result.state:'unavailable';}catch(error){if(error.name==='AbortError')throw error;}
  return freeze({state:'results-verified',proposalId:proof.proposalId,domainId:proof.domainId,receipts:value.receipts,cleanup,meaning:'Original task results saved. Current question coverage must be checked independently against its current inputs.'});
 }
 const api={load,inspect,save};if(node)module.exports=api;else root.FactoredPendingRecovery=api;
})(typeof globalThis!=='undefined'?globalThis:this);
