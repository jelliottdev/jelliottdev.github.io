/* Fixed same-origin question dependencies, loaded only when a question is activated. */
(function(root){
 'use strict';
 const stages=[
  [['finite-sequence-banks.js','FiniteSequenceBanks','resolve']],
  [['finite-json.js','FiniteJSON','capture'],['local-experiment.js','LocalExperiment','checkIdentity'],['output-evaluators.js','OutputEvaluators','identify']],
  [['computation-evidence.js','ComputationEvidence','compare'],['experiment-protocols.js','ExperimentProtocols','describe'],['research-family.js','ResearchFamily','snapshot'],['question-protocols.js','QuestionProtocols','definition'],['claim-specification.js','ClaimSpecification','createDraft'],['local-control.js','LocalControl','compatible']],
  [['question-evidence.js','QuestionEvidence','summarize'],['family-question-evidence.js','FamilyQuestionEvidence','summarize'],['verified-evidence-client.js','VerifiedEvidenceClient','create'],['claim-share.js','ClaimShare','cardData']],
  [['question-decisions.js','QuestionDecisions','finite'],['record-followups.js','RecordFollowups','describeCard']],
  [['task-variants.js','TaskVariants','validate']],
  [['record-question-live.js','RecordQuestionLive','createController']]
 ];
 const readinessStages=[
  [['finite-sequence-banks.js','FiniteSequenceBanks','resolve']],
  [['finite-json.js','FiniteJSON','capture'],['local-experiment.js','LocalExperiment','checkIdentity'],['output-evaluators.js','OutputEvaluators','identify']],
  [['computation-evidence.js','ComputationEvidence','compare'],['experiment-protocols.js','ExperimentProtocols','describe'],['claim-specification.js','ClaimSpecification','createDraft'],['local-control.js','LocalControl','compatible'],['output-evaluators.js','OutputEvaluators','identify'],['local-input-bundle.js','LocalInputBundle','parse']],
  [['claim-share.js','ClaimShare','cardData'],['verified-evidence-client.js','VerifiedEvidenceClient','create'],['verified-prefix-evaluation.js','VerifiedPrefixEvaluation','evaluate']],
  [['record-followups.js','RecordFollowups','describeCard'],['fixed-plan-compiler.js','FixedPlanCompiler','compile']],
  [['ordinary-prefix-evidence-client.js','OrdinaryPrefixEvidenceClient','verify']],
  [['followup-readiness.js','FollowupReadiness','createController']]
 ];
 // Only authored finite checks need this read-only compiler/evidence path.
 // Execution, admission, storage and the run-page UI are deliberately absent.
 const finiteReadinessStages=[
  [['finite-sequence-banks.js','FiniteSequenceBanks','resolve'],['repeating-key-banks.js','RepeatingKeyBanks','resolve']],
  [['finite-json.js','FiniteJSON','capture'],['local-experiment.js','LocalExperiment','checkIdentity'],['output-evaluators.js','OutputEvaluators','identify'],['claim-specification.js','ClaimSpecification','createDraft'],['local-control.js','LocalControl','compatible'],['local-input-bundle.js','LocalInputBundle','parse'],['followup-context.js','FollowupContext','valid'],['experiment-protocols.js','ExperimentProtocols','describe']],
  [['finite-control-storage.js','FiniteControlStorage','expand'],['claim-share.js','ClaimShare','cardData'],['fixed-plan-compiler.js','FixedPlanCompiler','compile'],['computation-evidence.js','ComputationEvidence','compare']],
  [['finite-settings.js','FiniteSettings','expand'],['finite-question-policy.js','FiniteQuestionPolicy','describe'],['verified-prefix-evaluation.js','VerifiedPrefixEvaluation','evaluate'],['record-question-model.js','RecordQuestionModel','finiteRecipe'],['local-run-view.js','LocalRunView','render']],
  [['factored-language-reuse.js','FactoredLanguageReuse','prepare'],['finite-search-view.js','FiniteSearchView','render']],
  [['factored-finite-question.js','FactoredFiniteQuestion','createOutputAccumulator'],['finite-search-workspace-view.js','FiniteSearchWorkspaceView','workDescription']],
  [['factored-finite-search-compiler.js','FactoredFiniteSearchCompiler','compileLanguageComparison'],['factored-prefix-reuse.js','FactoredPrefixReuse','prepare']],
  [['factored-evidence-client.js','FactoredEvidenceClient','createScan'],['authored-finite-followup.js','AuthoredFiniteFollowup','validatePlan']]
 ];
 const version='20261026-folded-key-cycles',scripts=new Map();let pending=null,readinessPending=null;
 const ready=([,name,method])=>root[name]&&(method==='payload'?typeof root[name][method]==='object':typeof root[name][method]==='function');
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
 function load({finite=false,language=false}={}){
  if(finite)return loadReadiness({finite:true,language}).then(()=>load());
  if(ready(stages.at(-1)[0]))return Promise.resolve(root.RecordQuestionLive);
  if(pending)return pending;
  pending=(async()=>{for(const stage of stages)await Promise.all(stage.map(ensure));return root.RecordQuestionLive;})().catch(error=>{pending=null;throw error;});return pending;
 }
 async function loadReadiness({language=false,finite=false}={}){
  if(language){try{await ensure(['language-model-data.js','RuneLanguageModelData','payload']);await ensure(['language-score.js','RuneLanguageScore','evaluate']);}catch(error){if(!root.RuneLanguageScore){scripts.delete('language-model-data.js');delete root.RuneLanguageModelData;}throw error;}}
  if(finite)for(const stage of finiteReadinessStages)await Promise.all(stage.map(ensure));
  if(ready(readinessStages.at(-1)[0]))return Promise.resolve(root.FollowupReadiness);
  if(readinessPending)return readinessPending;
  readinessPending=(async()=>{for(const stage of readinessStages)await Promise.all(stage.map(ensure));return root.FollowupReadiness;})().catch(error=>{readinessPending=null;throw error;});return readinessPending;
 }
 const api={load,loadReadiness};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionRuntime=api;
})(typeof globalThis!=='undefined'?globalThis:this);
