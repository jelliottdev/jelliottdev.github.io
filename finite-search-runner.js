/* Controls-first local execution for a bound finite question. No saved receipts or writes. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,F=node?require('./finite-program-question.js'):root.FiniteProgramQuestion,C=node?require('./local-plan-controls.js'):root.LocalPlanControls,X=node?require('./local-run-executor.js'):root.LocalRunExecutor,JSONData=node?require('./finite-json.js'):root.FiniteJSON;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const copy=v=>JSON.parse(E.stable(v));
 async function digest(v,cryptoAPI){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function createRunner({executor=X.createExecutor(),crypto:cryptoAPI=root.crypto}={}){
  function start(domain,suppliedIds,suppliedControls,{onProgress}={}){
   let current=null,aborted=false,settled=false,resolve,reject;
   const promise=new Promise((yes,no)=>{resolve=yes;reject=no;}),finish=(fn,value)=>{if(settled)return;settled=true;fn(value);};
   const live=()=>{if(aborted)throw new DOMException('Run cancelled.','AbortError');};
   const progress=(phase,completed,total)=>{live();try{onProgress?.({phase,completed,total});}catch{}live();};
   let ids,controls;
   try{F.inspect(domain);ids=JSONData.capture(suppliedIds,{maxBytes:4096,maxDepth:2,maxNodes:13});controls=JSONData.capture(suppliedControls);}catch(error){finish(reject,error);return {promise,cancel(){}};}
   async function execute(task){
    live();current=executor.start(copy(task));if(!current||typeof current.cancel!=='function'||!current.promise)throw Error('The local executor is unavailable.');
    const output=await current.promise;live();current=null;const checked=await E.verify(task,output,cryptoAPI);live();return checked;
   }
   (async()=>{
    const selection=await F.select(domain,ids,cryptoAPI);live();
    if(!Array.isArray(controls)||controls.length!==selection.cases.length||controls.some((item,i)=>!exact(item,['caseId','suite'])||item.caseId!==selection.cases[i].id))throw Error('Controls must match every selected case in canonical order.');
    // Finish admission for the entire batch before starting its first worker.
    for(let i=0;i<selection.cases.length;i++){await E.checkIdentity(selection.cases[i].task,cryptoAPI);live();await C.validate(controls[i].suite,selection.cases[i].task,cryptoAPI);live();}
    const controlResults=[],results=[],matchingCaseIds=[],total=controls.reduce((n,item)=>n+item.suite.cases.length,0);let completed=0;
    progress('controls',0,total);
    for(const item of controls){const checked=[];for(const fixture of item.suite.cases){const result=await execute(fixture.task);if(await digest(result,cryptoAPI)!==fixture.expectedResultSha256)throw Error('An independent known-answer control failed. No target cases will run.');live();checked.push({id:fixture.id,result});progress('controls',++completed,total);}controlResults.push({caseId:item.caseId,results:checked});}
    progress('cases',0,selection.cases.length);
    for(const item of selection.cases){const result=await execute(item.task);live();results.push({caseId:item.id,result});if(result.matches.some(match=>match.matched))matchingCaseIds.push(item.id);progress('cases',results.length,selection.cases.length);if(matchingCaseIds.length)break;}
    live();const completedCaseIds=results.map(item=>item.caseId),done=new Set(completedCaseIds);
    // These are local outputs, not public evidence. The caller must save real
    // verified receipts before constructing a shared question decision.
    return {domainId:domain.id,selection,results,controls:controlResults,selectedCaseIds:selection.cases.map(item=>item.id),completedCaseIds,missingCaseIds:selection.cases.filter(item=>!done.has(item.id)).map(item=>item.id),matchingCaseIds,stopped:matchingCaseIds.length?'prefix-found':'batch-complete'};
   })().then(value=>finish(resolve,value),error=>{try{current?.cancel();}catch{}current=null;finish(reject,error);});
   return {promise,cancel(){if(settled)return;aborted=true;try{current?.cancel();}catch{}current=null;finish(reject,new DOMException('Run cancelled.','AbortError'));}};
  }
  return {start};
 }
 const api={createRunner};if(node)module.exports=api;else root.FiniteSearchRunner=api;
})(typeof globalThis!=='undefined'?globalThis:this);
