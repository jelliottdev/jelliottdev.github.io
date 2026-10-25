/* Finite family execution through the fixed local worker. No generated code. */
(function(root){
 'use strict';
 const common=typeof module==='object'&&module.exports;
 const E=common?require('./local-experiment.js'):root.LocalExperiment;
 const C=common?require('./local-plan-controls.js'):root.LocalPlanControls;
 const F=common?require('./research-family.js'):root.ResearchFamily;
 const X=common?require('./local-run-executor.js'):root.LocalRunExecutor;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const copy=v=>JSON.parse(E.stable(v));
 async function digest(v,cryptoAPI){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(b=>b.toString(16).padStart(2,'0')).join('');}
 function createRunner({executor=X.createExecutor(),crypto:cryptoAPI=root.crypto}={}){
  function start(suppliedPlan,suppliedControls,{onProgress}={}){
   let current=null,settled=false,aborted=false,resolveRun,rejectRun;
   const promise=new Promise((resolve,reject)=>{resolveRun=resolve;rejectRun=reject;});
   const finish=(callback,value)=>{if(settled)return;settled=true;callback(value);};
   const live=()=>{if(aborted)throw new DOMException('Run cancelled.','AbortError');};
   const progress=(phase,completed,total)=>{live();try{onProgress?.({phase,completed,total});}catch{}live();};
   async function execute(task){
    live();current=executor.start(copy(task));
    if(!current||typeof current.cancel!=='function'||!current.promise)throw Error('The family executor is unavailable.');
    const result=await current.promise;live();current=null;
    const verified=await E.verify(task,result,cryptoAPI);live();return verified;
   }
   // Capture before the first await: edits to a caller's objects cannot change a run.
   let plan,controls;
   try{plan=copy(suppliedPlan);controls=copy(suppliedControls);}catch(error){finish(rejectRun,error);return {promise,cancel(){}};}
   (async()=>{
    await F.validateExecutionPlan(plan,cryptoAPI);live();
    if(!Array.isArray(controls)||controls.length!==plan.cases.length||controls.some((item,i)=>!exact(item,['caseId','suite'])||item.caseId!==plan.cases[i].id))throw Error('The family controls do not match its ordered cases.');
    // Every case and suite must pass admission before any worker starts.
    for(let i=0;i<plan.cases.length;i++){
     await E.checkIdentity(plan.cases[i].task,cryptoAPI);live();
     await C.validate(controls[i].suite,plan.cases[i].task,cryptoAPI);live();
    }
    const controlResults=[],results=[],totalControls=controls.reduce((n,item)=>n+item.suite.cases.length,0);let completed=0;
    progress('controls',0,totalControls);
    for(const item of controls){
     const checked=[];
     for(const fixture of item.suite.cases){
      const result=await execute(fixture.task);
      if(await digest(result,cryptoAPI)!==fixture.expectedResultSha256)throw Error('A known-answer check failed. No manuscript cases will run.');
      live();checked.push({id:fixture.id,result});progress('controls',++completed,totalControls);
     }
     controlResults.push({caseId:item.caseId,results:checked});
    }
    progress('cases',0,plan.cases.length);
    for(const item of plan.cases){const result=await execute(item.task);live();results.push({caseId:item.id,result});progress('cases',results.length,plan.cases.length);}
    live();return {plan,results,controls:controlResults};
   })().then(value=>finish(resolveRun,value),error=>{try{current?.cancel();}catch{}current=null;finish(rejectRun,error);});
   return {promise,cancel(){if(settled)return;aborted=true;try{current?.cancel();}catch{}current=null;finish(rejectRun,new DOMException('Run cancelled.','AbortError'));}};
  }
  return {start};
 }
 const api={createRunner};if(common)module.exports=api;else root.FamilyRunner=api;
})(typeof globalThis!=='undefined'?globalThis:this);
