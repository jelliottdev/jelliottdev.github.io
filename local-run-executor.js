/* Browser CPU execution and cancellation. Never evals source or accepts worker URLs. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 function createExecutor({WorkerClass=root.Worker,schedule=root.setTimeout.bind(root),unschedule=root.clearTimeout.bind(root),deadline=120000}={}){
  let sequence=0;
  function start(task,{onProgress}={}){
   const id=++sequence;let worker=null,timer=null,settled=false,rejectRun;
   const cleanup=()=>{if(timer!==null)unschedule(timer);worker?.terminate();timer=null;worker=null;};
   const finish=(callback,value)=>{if(settled)return;settled=true;cleanup();callback(value);};
   const promise=new Promise((resolve,reject)=>{
    rejectRun=reject;
    try{
     E.validateTask(task);
     const snapshot=JSON.parse(JSON.stringify(task)),total=snapshot.pages.length;let completed=0;
     if(typeof WorkerClass!=='function')throw Error('This browser cannot start the local runner. You can use the reproduction download instead.');
     worker=new WorkerClass('local-run-worker.js?v=20261024-word-pairs');
     worker.onmessage=event=>{
      if(settled||event.data?.id!==id)return;
      const data=event.data;
      if(data.type==='result'){
       if(!data.result||data.result.taskId!==snapshot.taskId)return finish(reject,Error('The runner returned a different experiment.'));
       finish(resolve,data.result);
      }else if(data.type==='error')finish(reject,Error('The experiment could not run. Please try again.'));
      else if(data.type==='progress'){
       const p=data.progress;
       if(!p||!['checking','running'].includes(p.phase)||p.total!==total||!Number.isInteger(p.completed)||p.completed<completed||p.completed>total)return;
       completed=p.completed;try{onProgress?.({phase:p.phase,completed,total});}catch{}
      }
     };
     worker.onerror=event=>{event.preventDefault?.();finish(reject,Error('The local runner stopped. Please try again.'));};
     worker.onmessageerror=()=>finish(reject,Error('The local runner returned an unreadable result.'));
     timer=schedule(()=>finish(reject,Error('The run reached its time limit. Your plan is unchanged.')),deadline);
     worker.postMessage({type:'run',id,task:snapshot});
    }catch(error){finish(reject,error);}
   });
   return {promise,cancel(){finish(rejectRun,new DOMException('Run cancelled.','AbortError'));}};
  }
  return {start};
 }
 const api={createExecutor,start(...args){return defaultExecutor.start(...args);}},defaultExecutor=createExecutor();
 if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunExecutor=api;
})(typeof globalThis!=='undefined'?globalThis:this);
