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
     worker=new WorkerClass('local-run-worker.js?v=20261025-language');
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
 // A private reviewed batch may reuse this fixed worker sequentially. The
 // owner must close it when the batch ends; cancellation/error is terminal.
 function createBatchExecutor({WorkerClass=root.Worker,schedule=root.setTimeout.bind(root),unschedule=root.clearTimeout.bind(root),deadline=120000}={}){
  let worker=null,active=null,sequence=0,closed=false;
  const aborted=()=>new DOMException('Run cancelled.','AbortError');
  function settle(job,fn,value){if(job.settled)return;job.settled=true;if(job.timer!==null)unschedule(job.timer);job.timer=null;if(active===job)active=null;fn(value);}
  function close(error=aborted()){if(closed)return;closed=true;const current=worker;worker=null;current?.terminate();if(active){const job=active;settle(job,job.reject,error);}}
  function ensureWorker(){if(worker)return;if(typeof WorkerClass!=='function')throw Error('This browser cannot start the local runner. You can use the reproduction download instead.');const current=new WorkerClass('local-run-worker.js?v=20261025-language');worker=current;
   current.onmessage=event=>{if(closed||worker!==current)return;const job=active,data=event.data;if(!job||job.settled||data?.id!==job.id)return;
    if(data.type==='result'){if(!data.result||data.result.taskId!==job.task.taskId){close(Error('The runner returned a different experiment.'));return;}settle(job,job.resolve,data.result);}
    else if(data.type==='error')close(Error('The experiment could not run. Please try again.'));
    else if(data.type==='progress'){const p=data.progress;if(!p||!['checking','running'].includes(p.phase)||p.total!==job.task.pages.length||!Number.isInteger(p.completed)||p.completed<job.completed||p.completed>p.total)return;job.completed=p.completed;try{job.onProgress?.({phase:p.phase,completed:p.completed,total:p.total});}catch{}}
   };
   current.onerror=event=>{event.preventDefault?.();if(worker===current)close(Error('The local runner stopped. Please try again.'));};
   current.onmessageerror=()=>{if(worker===current)close(Error('The local runner returned an unreadable result.'));};
  }
  function start(task,{onProgress}={}){let job;const promise=new Promise((resolve,reject)=>{job={id:++sequence,resolve,reject,timer:null,settled:false,completed:0,onProgress,task:null};try{if(closed)throw Error('This reviewed batch has ended.');if(active)throw Error('Wait for the current batch computation to finish.');E.validateTask(task);job.task=JSON.parse(JSON.stringify(task));active=job;ensureWorker();job.timer=schedule(()=>{if(active===job)close(Error('The run reached its time limit. Your plan is unchanged.'));},deadline);worker.postMessage({type:'run',id:job.id,task:job.task});}catch(error){if(active===job)close(error);else settle(job,reject,error);}});return {promise,cancel(){if(job?.settled)return;close();}};}
  return {start,close};
 }
 const api={createExecutor,createBatchExecutor,start(...args){return defaultExecutor.start(...args);}},defaultExecutor=createExecutor();
 if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunExecutor=api;
})(typeof globalThis!=='undefined'?globalThis:this);
