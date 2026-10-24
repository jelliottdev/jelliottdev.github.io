/* Fixed site-owned worker. Task data can select reviewed operations, never code. */
importScripts('local-experiment.js?v=20261024-word-sums');
self.onmessage=async function(event){
 const message=event.data;
 if(!message||message.type!=='run'||!Number.isSafeInteger(message.id))return;
 const id=message.id;
 try{
  await LocalExperiment.checkIdentity(message.task);
  self.postMessage({id,type:'progress',progress:{phase:'checking',completed:0,total:message.task.pages.length}});
  const result=LocalExperiment.run(message.task,{onProgress:progress=>self.postMessage({id,type:'progress',progress})});
  self.postMessage({id,type:'result',result});
 }catch{
  self.postMessage({id,type:'error',message:'The experiment could not run. Its plan may have changed or needs a newer runner.'});
 }
};
