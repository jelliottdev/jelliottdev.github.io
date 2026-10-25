/* Fixed same-origin question dependencies, loaded only when a question is activated. */
(function(root){
 'use strict';
 const stages=[
  [['finite-json.js','FiniteJSON','capture'],['local-experiment.js','LocalExperiment','checkIdentity']],
  [['computation-evidence.js','ComputationEvidence','compare'],['experiment-protocols.js','ExperimentProtocols','describe'],['research-family.js','ResearchFamily','snapshot'],['question-protocols.js','QuestionProtocols','definition'],['claim-specification.js','ClaimSpecification','createDraft'],['local-control.js','LocalControl','compatible']],
  [['question-evidence.js','QuestionEvidence','summarize'],['family-question-evidence.js','FamilyQuestionEvidence','summarize'],['verified-evidence-client.js','VerifiedEvidenceClient','create'],['claim-share.js','ClaimShare','cardData']],
  [['question-decisions.js','QuestionDecisions','finite'],['record-followups.js','RecordFollowups','describeCard']],
  [['task-variants.js','TaskVariants','validate']],
  [['record-question-live.js','RecordQuestionLive','createController']]
 ];
 const version='20261025-evidence-reuse',scripts=new Map();let pending=null;
 const ready=([,name,method])=>root[name]&&typeof root[name][method]==='function';
 function ensure(definition){
  const [file,name]=definition;if(ready(definition))return Promise.resolve(root[name]);
  if(scripts.has(file))return scripts.get(file);
  const promise=new Promise((resolve,reject)=>{
   if(!root.document?.createElement||!root.document.head||!root.location?.href){reject(Error('Current evidence tools are unavailable.'));return;}
   const script=root.document.createElement('script'),url=new URL(file,root.location.href);url.search='v='+version;url.hash='';
   let settled=false;const finish=error=>{if(settled)return;settled=true;root.clearTimeout(timer);script.onload=script.onerror=null;if(error){script.remove?.();scripts.delete(file);reject(error);}else resolve(root[name]);};
   const timer=root.setTimeout(()=>finish(Error('Current evidence tools took too long to load.')),10000);
   script.src=url.href;script.async=true;script.onload=()=>finish(ready(definition)?null:Error('A current evidence tool did not load correctly.'));script.onerror=()=>finish(Error('Current evidence tools could not be loaded.'));
   try{root.document.head.appendChild(script);}catch{finish(Error('Current evidence tools could not be loaded.'));}
  });
  scripts.set(file,promise);promise.catch(()=>{if(scripts.get(file)===promise)scripts.delete(file);});return promise;
 }
 function load(){
  if(ready(stages.at(-1)[0]))return Promise.resolve(root.RecordQuestionLive);
  if(pending)return pending;
  pending=(async()=>{for(const stage of stages)await Promise.all(stage.map(ensure));return root.RecordQuestionLive;})().catch(error=>{pending=null;throw error;});return pending;
 }
 const api={load};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionRuntime=api;
})(typeof globalThis!=='undefined'?globalThis:this);
