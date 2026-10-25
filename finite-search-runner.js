/* Controls-first local execution for a bound finite question. No saved receipts or writes. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,F=node?require('./finite-program-question.js'):root.FiniteProgramQuestion,Factored=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion,C=node?require('./local-plan-controls.js'):root.LocalPlanControls,X=node?require('./local-run-executor.js'):root.LocalRunExecutor,JSONData=node?require('./finite-json.js'):root.FiniteJSON;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const copy=v=>JSON.parse(E.stable(v));
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 async function digest(v,cryptoAPI){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function createRunner(options={}){return runner(options,'prefix');}
 function createOutputRunner(options={}){return runner(options,'language');}
 function createInspectionRunner(options={}){
  if(!options||typeof options!=='object'||Array.isArray(options))throw Error('Use explicit inspection runner options.');const descriptors=Object.getOwnPropertyDescriptors(options),captured={};for(const key of Reflect.ownKeys(options)){const descriptor=descriptors[key];if(typeof key!=='string'||!['executor','crypto','reuseWorker'].includes(key)||!descriptor.enumerable||!Object.hasOwn(descriptor,'value'))throw Error('Use explicit inspection runner options.');captured[key]=descriptor.value;}return runner(captured,'inspection');
 }
 function runner({executor:suppliedExecutor,crypto:cryptoAPI=root.crypto,reuseWorker=false},mode){
  const outputMode=mode!=='prefix',inspectionMode=mode==='inspection';
  function start(domain,suppliedIds,suppliedControls,{onProgress}={}){
   let current=null,aborted=false,settled=false,resolve,reject,domainId=null;
   const batchExecutor=!suppliedExecutor&&reuseWorker===true?X.createBatchExecutor():null,executor=suppliedExecutor||batchExecutor||X.createExecutor();
   const checkpointResults=[],checkpointMatches=[],checkpointUsable=[],checkpointInsufficient=[];
   // Local verified output only: this is neither a saved receipt nor a public
   // question decision. Each read is detached from runner and caller state.
   const getCheckpoint=()=>freeze(copy({schema:inspectionMode?'liberpedia-finite-inspection-checkpoint-v1':outputMode?'liberpedia-finite-output-checkpoint-v1':'liberpedia-finite-local-checkpoint-v1',domainId,results:checkpointResults,completedCaseIds:checkpointResults.map(item=>item.caseId),...(inspectionMode?{runeOutputCaseIds:checkpointUsable,noRuneCaseIds:checkpointInsufficient}:outputMode?{usableCaseIds:checkpointUsable,insufficientCaseIds:checkpointInsufficient}:{matchingCaseIds:checkpointMatches})}));
   const promise=new Promise((yes,no)=>{resolve=yes;reject=no;}),finish=(fn,value)=>{if(settled)return;settled=true;batchExecutor?.close();fn(value);};
   const live=()=>{if(aborted)throw new DOMException('Run cancelled.','AbortError');};
   const progress=(phase,completed,total)=>{live();try{onProgress?.({phase,completed,total});}catch{}live();};
   let ids,controls,question=F;
   try{try{F.inspect(domain);}catch(legacyError){if(!Factored)throw legacyError;Factored.inspect(domain);question=Factored;}const outputDomain=question===Factored&&domain.schema==='liberpedia-factored-finite-output-question-v1',policy=inspectionMode?'transformed-output-inspection-v1':'language-reference-comparison-v1';if(outputMode?(!outputDomain||domain.questionPolicy!==policy):outputDomain)throw Error('Use the explicit runner for this maintained finite question.');domainId=domain.id;ids=JSONData.capture(suppliedIds,question===F?{maxBytes:4096,maxDepth:2,maxNodes:13}:{maxBytes:8192,maxDepth:3,maxNodes:60});controls=JSONData.capture(suppliedControls);}catch(error){finish(reject,error);return {promise,cancel(){},getCheckpoint};}
   async function execute(task){
    live();current=executor.start(copy(task));if(!current||typeof current.cancel!=='function'||!current.promise)throw Error('The local executor is unavailable.');
    const output=await current.promise;live();current=null;const checked=await E.verify(task,output,cryptoAPI);live();return checked;
   }
   (async()=>{
    const selection=await question.select(domain,ids,cryptoAPI);live();
    if(!Array.isArray(controls)||controls.length!==selection.cases.length||controls.some((item,i)=>!exact(item,['caseId','suite'])||item.caseId!==selection.cases[i].id))throw Error('Controls must match every selected case in canonical order.');
    // Finish admission for the entire batch before starting its first worker.
    for(let i=0;i<selection.cases.length;i++){await E.checkIdentity(selection.cases[i].task,cryptoAPI);live();await C.validate(controls[i].suite,selection.cases[i].task,cryptoAPI);live();}
    const controlResults=[],results=[],matchingCaseIds=[],total=controls.reduce((n,item)=>n+item.suite.cases.length,0);let completed=0;
    progress('controls',0,total);
    for(const item of controls){const checked=[];for(const fixture of item.suite.cases){const result=await execute(fixture.task);if(await digest(result,cryptoAPI)!==fixture.expectedResultSha256)throw Error('An independent known-answer control failed. No target cases will run.');live();checked.push({id:fixture.id,result});progress('controls',++completed,total);}controlResults.push({caseId:item.caseId,results:checked});}
    progress('cases',0,selection.cases.length);
    for(const item of selection.cases){const result=await execute(item.task);live();results.push({caseId:item.id,result});checkpointResults.push({caseId:item.id,result});if(inspectionMode){const page=result.transformed.find(p=>p.page===item.pageId);if(!page)throw Error('The verified output page is missing.');const runes=new Set(item.task.alphabet.map(v=>v.rune));(Array.from(page.text).some(ch=>runes.has(ch))?checkpointUsable:checkpointInsufficient).push(item.id);}else if(outputMode){const page=result.languageScore.pages.find(p=>p.page===item.pageId);if(!page||!['compared','insufficient'].includes(page.status))throw Error('The verified output lost its page comparison.');(page.status==='compared'?checkpointUsable:checkpointInsufficient).push(item.id);}else if(result.matches.some(match=>match.matched)){matchingCaseIds.push(item.id);checkpointMatches.push(item.id);}progress('cases',results.length,selection.cases.length);if(!outputMode&&matchingCaseIds.length)break;}
    live();const completedCaseIds=results.map(item=>item.caseId),done=new Set(completedCaseIds);
    // These are local outputs, not public evidence. The caller must save real
    // verified receipts before constructing a shared question decision.
    return {domainId:domain.id,selection,results,controls:controlResults,selectedCaseIds:selection.cases.map(item=>item.id),completedCaseIds,missingCaseIds:selection.cases.filter(item=>!done.has(item.id)).map(item=>item.id),...(inspectionMode?{runeOutputCaseIds:checkpointUsable.slice(),noRuneCaseIds:checkpointInsufficient.slice()}:outputMode?{usableCaseIds:checkpointUsable.slice(),insufficientCaseIds:checkpointInsufficient.slice()}:{matchingCaseIds}),stopped:!outputMode&&matchingCaseIds.length?'prefix-found':'batch-complete'};
   })().then(value=>finish(resolve,value),error=>{try{current?.cancel();}catch{}current=null;finish(reject,error);});
   return {promise,getCheckpoint,cancel(){if(settled)return;aborted=true;try{current?.cancel();}catch{}current=null;finish(reject,new DOMException('Run cancelled.','AbortError'));}};
  }
  return {start};
 }
 const api={createRunner,createOutputRunner,createInspectionRunner};if(node)module.exports=api;else root.FiniteSearchRunner=api;
})(typeof globalThis!=='undefined'?globalThis:this);
