/* Exact engine routing; control versions are never converted or relabeled. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,V=node?require('./declarative-rune-program.js'):root.DeclarativeRuneProgram,C=node?require('./local-plan-controls.js'):root.LocalPlanControls,D=node?require('./declarative-plan-controls.js'):root.DeclarativePlanControls;
 function select(task){
  const schema=Object.getOwnPropertyDescriptor(task||{},'schema'),engine=Object.getOwnPropertyDescriptor(task||{},'engine');
  if(!schema||!engine||!Object.hasOwn(schema,'value')||!Object.hasOwn(engine,'value'))throw Error('Use an exact task version for its implementation checks.');
  if(schema.value===E.TASK&&engine.value===E.ENGINE)return C;
  if(V&&D&&schema.value===V.TASK&&engine.value===V.ENGINE)return D;
  throw Error('These implementation checks do not support this task version.');
 }
 const api=Object.freeze({prepare:(task,crypto)=>select(task).prepare(task,crypto),validate:(suite,task,crypto)=>select(task).validate(suite,task,crypto),scope:task=>select(task).SCOPE});
 if(node)module.exports=api;else root.LocalPlanControlsDispatch=api;
})(typeof globalThis!=='undefined'?globalThis:this);
