/* Fixed V2 worker. Inputs select bounded operations, never executable source. */
importScripts('local-experiment.js?v=20261026-opening-sets','finite-json.js?v=20261027-declarative','declarative-rune-program.js?v=20261027-declarative');
self.onmessage=async function(event){
 const message=event.data;
 if(!message||message.type!=='run'||!Number.isSafeInteger(message.id))return;
 const id=message.id;
 try{
  if(message.task?.criterion?.kind==='language-score'&&!self.RuneLanguageScore)importScripts('language-model-data.js?v=20261025-language','language-score.js?v=20261025-language');
  const task=await DeclarativeRuneProgram.checkIdentity(message.task);
  self.postMessage({id,type:'progress',progress:{phase:'checking',completed:0,total:task.pages.length}});
  const result=DeclarativeRuneProgram.run(task);
  self.postMessage({id,type:'progress',progress:{phase:'running',completed:task.pages.length,total:task.pages.length}});
  self.postMessage({id,type:'result',result});
 }catch{
  self.postMessage({id,type:'error',message:'The experiment could not run. Its exact rule or finite key may be invalid.'});
 }
};
