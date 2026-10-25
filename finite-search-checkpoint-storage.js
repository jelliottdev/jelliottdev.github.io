/* Pending local output only. Stored bytes are rechecked, never treated as public evidence. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,Q=node?require('./finite-program-question.js'):root.FiniteProgramQuestion,J=node?require('./finite-json.js'):root.FiniteJSON;
 const PREFIX='liberpedia.finite-pending.v1.',SCHEMA='liberpedia-finite-pending-v1',MAX_BYTES=2*1024*1024,MAX_TOTAL_BYTES=8*1024*1024,MAX_ENTRIES=4,HEX=/^[a-f0-9]{64}$/,PID=/^p_[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 const capture=v=>J.capture(v,{maxBytes:MAX_BYTES,maxDepth:24,maxNodes:100000}),bytes=v=>new TextEncoder().encode(v).byteLength;
 function binding(proposalId,domain){if(!PID.test(proposalId))throw Error('Use the original saved idea identity.');Q.inspect(domain);return {proposalId,domainId:domain.id,inputVersion:domain.inputVersion};}
 function parse(text){if(typeof text!=='string'||text.length>MAX_BYTES||bytes(text)>MAX_BYTES)throw Error('Pending output exceeds its storage bound.');const value=capture(JSON.parse(text));if(!exact(value,['schema','proposalId','domainId','inputVersion','cases'])||value.schema!==SCHEMA||!PID.test(value.proposalId)||!HEX.test(value.domainId)||!['raw','reviewed'].includes(value.inputVersion)||!Array.isArray(value.cases)||!value.cases.length||value.cases.length>12||value.cases.some(c=>!exact(c,['caseId','task','result'])||!HEX.test(c.caseId))||new Set(value.cases.map(c=>c.caseId)).size!==value.cases.length)throw Error('Pending output has an invalid shape.');return value;}
 function storageFailure(error){return {state:['QuotaExceededError','NS_ERROR_DOM_QUOTA_REACHED'].includes(error?.name)?'quota':'unsupported'};}
 function createStore({storage,crypto:cryptoAPI=root.crypto}={}){
  const available=()=>{try{return storage&&['getItem','setItem','removeItem','key'].every(name=>typeof storage[name]==='function');}catch{return false;}};
  async function checkedCases(domain,results){
   const saved=capture(results);if(!Array.isArray(saved)||!saved.length||saved.length>12||saved.some(r=>!exact(r,['caseId','result'])||!HEX.test(r.caseId))||new Set(saved.map(r=>r.caseId)).size!==saved.length)throw Error('Use one to twelve exact completed outputs.');
   const selected=await Q.select(domain,saved.map(r=>r.caseId),cryptoAPI),byId=new Map(saved.map(r=>[r.caseId,r.result])),cases=[];
   for(const item of selected.cases)cases.push({caseId:item.id,task:item.task,result:await E.verify(item.task,byId.get(item.id),cryptoAPI)});
   return cases;
  }
  async function save({proposalId,domain,results}){
   const identity=binding(proposalId,domain),cases=await checkedCases(domain,results),value={schema:SCHEMA,...identity,cases},text=E.stable(value),key=PREFIX+proposalId;
   if(bytes(text)>MAX_BYTES)return {state:'limit'};if(!available())return {state:'unsupported'};
   try{
    const previous=storage.getItem(key);if(previous!==null){let old;try{old=parse(previous);}catch{return {state:'invalid'};}if(old.proposalId!==proposalId||old.domainId!==domain.id||old.inputVersion!==domain.inputVersion)return {state:'conflict'};if(old.cases.some(item=>!cases.some(next=>next.caseId===item.caseId&&E.stable(next)===E.stable(item))))return {state:'conflict'};}
    let count=0,total=bytes(key)+bytes(text);const length=storage.length;if(!Number.isSafeInteger(length)||length<0||length>10000)return {state:'limit'};
    for(let i=0;i<length;i++){const other=storage.key(i);if(typeof other!=='string'||!other.startsWith(PREFIX)||other===key)continue;count++;const body=storage.getItem(other);if(typeof body!=='string'||body.length>MAX_BYTES)return {state:'limit'};total+=bytes(other)+bytes(body);if(count>=MAX_ENTRIES||total>MAX_TOTAL_BYTES)return {state:'limit'};}
    storage.setItem(key,text);return {state:'stored',caseIds:cases.map(c=>c.caseId)};
   }catch(error){return storageFailure(error);}
  }
  async function restore({proposalId,domain}){
   binding(proposalId,domain);if(!available())return {state:'unsupported'};let text;try{text=storage.getItem(PREFIX+proposalId);}catch(error){return storageFailure(error);}if(text===null)return {state:'absent'};
   let value;try{value=parse(text);}catch{return {state:'invalid'};}if(value.proposalId!==proposalId||value.domainId!==domain.id||value.inputVersion!==domain.inputVersion)return {state:'stale'};
   try{
    const cases=await checkedCases(domain,value.cases.map(c=>({caseId:c.caseId,result:c.result})));
    if(E.stable(cases)!==E.stable(value.cases))return {state:'invalid'};
    const results=cases.map(c=>({caseId:c.caseId,result:c.result}));return freeze({state:'restored',checkpoint:{domainId:domain.id,results,completedCaseIds:results.map(c=>c.caseId),matchingCaseIds:results.filter(c=>c.result.matches.some(m=>m.matched)).map(c=>c.caseId)}});
   }catch{return {state:'invalid'};}
  }
  function remove(input){
   let captured;try{captured=capture(input);}catch{return {state:'invalid'};}
   const guarded=Object.hasOwn(captured||{},'results');if(!exact(captured,['proposalId','domainId',...(guarded?['results']:[])]))return {state:'invalid'};
   const {proposalId,domainId,results}=captured;if(!PID.test(proposalId)||!HEX.test(domainId))return {state:'invalid'};
   if(guarded&&(!Array.isArray(results)||!results.length||results.length>12||results.some(r=>!exact(r,['caseId','result'])||!HEX.test(r.caseId))||new Set(results.map(r=>r.caseId)).size!==results.length))return {state:'invalid'};
   if(!available())return {state:'unsupported'};
   try{const key=PREFIX+proposalId,text=storage.getItem(key);if(text===null)return {state:'absent'};let value;try{value=parse(text);}catch{return {state:'invalid'};}if(value.proposalId!==proposalId||value.domainId!==domainId)return {state:'stale'};
    if(guarded){const ordered=items=>items.map(r=>({caseId:r.caseId,result:r.result})).sort((a,b)=>a.caseId.localeCompare(b.caseId));if(E.stable(ordered(results))!==E.stable(ordered(value.cases)))return {state:'stale'};}
    storage.removeItem(key);return {state:'removed'};
   }catch(error){return storageFailure(error);}
  }
  return {save,restore,remove};
 }
 const api={createStore,LIMITS:Object.freeze({entryBytes:MAX_BYTES,totalBytes:MAX_TOTAL_BYTES,entries:MAX_ENTRIES}),PREFIX};if(node)module.exports=api;else root.FiniteSearchCheckpointStorage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
