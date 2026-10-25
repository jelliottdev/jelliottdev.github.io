/* Structural hydration only. Validate each selected manifest with the published adapter. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const BUDGET=Object.freeze({bytes:8*1024*1024,receipts:256,tasks:128,results:128,seedSources:1024}),HEX=/^[a-f0-9]{64}$/,COMMIT=/^[a-f0-9]{40}$/;
 const SCHEMAS=['liberpedia-published-count-evidence-v1','liberpedia-published-program-evidence-v1'],PATHS=['data/published-count-evidence.json','data/published-opening-evidence.json'];
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const clone=v=>JSON.parse(E.stable(v)),key=r=>[r.recordId,r.revision,r.caseId].join('|');
 function create(data){
  if(!exact(data,['schema','tasks','results','receipts','seedSources'])||data.schema!=='liberpedia-published-evidence-history-v1')throw Error('Published proof history has an unsupported schema.');
  const serialized=E.stable(data);if(new TextEncoder().encode(serialized).byteLength>BUDGET.bytes)throw Error('Published proof history exceeds its byte budget; no receipts may be evicted.');
  const history=JSON.parse(serialized);for(const field of ['tasks','results','receipts','seedSources'])if(!Array.isArray(history[field])||history[field].length>BUDGET[field])throw Error('Published proof history exceeds its '+field+' budget; no receipts may be evicted.');
  const tasks=new Map(),results=new Map(),receipts=new Map(),seeds=new Set(),usedTasks=new Set(),usedResults=new Set();
  for(const row of history.tasks){if(!exact(row,['id','task'])||!HEX.test(row.id)||row.task?.taskId!==row.id||tasks.has(row.id))throw Error('A retained task body is duplicated or changed.');tasks.set(row.id,row.task);}
  for(const row of history.results){if(!exact(row,['id','result'])||!HEX.test(row.id)||!row.result||results.has(row.id))throw Error('A retained result body is duplicated or changed.');results.set(row.id,row.result);}
  for(const row of history.seedSources){const identity=row?.commit+'|'+row?.path;if(!exact(row,['commit','path','sha256'])||!COMMIT.test(row.commit)||!PATHS.includes(row.path)||!HEX.test(row.sha256)||seeds.has(identity))throw Error('Public-history seed metadata is invalid or duplicated.');seeds.add(identity);}
  for(const row of history.receipts){
   if(!exact(row,['recordId','revision','caseId','registrySchema','taskId','resultId','inputVersion','createdAt','provenance'])||!SCHEMAS.includes(row.registrySchema)||!tasks.has(row.taskId)||!results.has(row.resultId)||receipts.has(key(row)))throw Error('A historical receipt identity is missing or duplicated.');
   if(typeof row.recordId!=='string'||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(row.recordId)||!HEX.test(row.revision)||typeof row.caseId!=='string'||!/^[a-z0-9-]{1,200}$/.test(row.caseId)||row.inputVersion!=='raw'||typeof row.createdAt!=='string'||!Number.isFinite(Date.parse(row.createdAt))||results.get(row.resultId).taskId!==row.taskId)throw Error('A historical receipt reference is malformed.');
   receipts.set(key(row),row);usedTasks.add(row.taskId);usedResults.add(row.resultId);
  }
  if(tasks.size!==usedTasks.size||results.size!==usedResults.size)throw Error('Published proof history contains unreferenced bodies.');
  function hydrate(row){return clone({schema:row.registrySchema,records:[{recordId:row.recordId,revision:row.revision,provenance:row.provenance}],entries:[{recordId:row.recordId,revision:row.revision,caseId:row.caseId,task:tasks.get(row.taskId),inputVersion:row.inputVersion,run:{id:row.resultId,createdAt:row.createdAt,result:results.get(row.resultId)}}]});}
  return {
   find(reference){if(!exact(reference,['recordId','revision','caseId']))throw Error('Historical lookup needs one exact source tuple.');const row=receipts.get(key(reference));return row?hydrate(row):null;},
   findSource(reference){const date=Object.hasOwn(reference||{},'createdAt');if(!exact(reference,['taskId','resultId','inputVersion',...(date?['createdAt']:[])])||!HEX.test(reference.taskId)||!HEX.test(reference.resultId)||!['raw','reviewed'].includes(reference.inputVersion)||date&&(typeof reference.createdAt!=='string'||!Number.isFinite(Date.parse(reference.createdAt))))throw Error('Historical source lookup needs an exact result identity.');for(const row of receipts.values())if(row.taskId===reference.taskId&&row.resultId===reference.resultId&&row.inputVersion===reference.inputVersion&&(!date||row.createdAt===reference.createdAt))return hydrate(row);return null;},
   *manifests(){for(const row of receipts.values())yield hydrate(row);}
  };
 }
 const api={create,BUDGET};if(typeof module==='object'&&module.exports)module.exports=api;else root.PublishedEvidenceHistory=api;
})(typeof globalThis!=='undefined'?globalThis:this);
