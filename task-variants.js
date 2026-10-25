/* Closed next-step variants. No inference, source fetching or target execution. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const P=typeof module==='object'&&module.exports?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const D=typeof module==='object'&&module.exports?require('./question-decisions.js'):root.QuestionDecisions;
 function inspect(task){
  try{E.validateTask(task);}catch{return null;}
  if(task.steps.length)return null;
  const variant=P.describe(task.criterion)?.followups.find(v=>v.id==='word-boundaries');
  return variant?{kind:variant.id,from:variant.from,to:variant.to,label:variant.label,description:variant.description}:null;
 }
 async function prepare(parent,cryptoAPI=root.crypto){
  await E.checkIdentity(parent,cryptoAPI);
  const variant=inspect(parent);if(!variant)throw Error('This task has no supported word-boundary comparison.');
  const criterion=P.variant(parent.criterion,variant.kind),title=P.describe(criterion).title;
  return E.prepare({title,
   pages:JSON.parse(E.stable(parent.pages)),alphabet:JSON.parse(E.stable(parent.alphabet)),steps:[],
   criterion},cryptoAPI);
 }
 async function validate(parent,child,cryptoAPI=root.crypto){
  await E.checkIdentity(child,cryptoAPI);
  const expected=await prepare(parent,cryptoAPI);
  if(E.stable(expected)!==E.stable(child))throw Error('The comparison changed more than the fixed word-boundary rule.');
  return child;
 }
 // Compatibility entry points keep their synchronous five-field presentation.
 function decision(parent,before,child,after){const variant=inspect(parent);if(!variant||parent.criterion.kind!=='word-affine-count')return null;return D.boundaryResults(parent,before,child,after);}
 function aggregateDecision(a,b){return D.boundaryAggregates(a,b);}
 const api={inspect,prepare,validate,decision,aggregateDecision};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.TaskVariants=api;
})(typeof globalThis!=='undefined'?globalThis:this);
