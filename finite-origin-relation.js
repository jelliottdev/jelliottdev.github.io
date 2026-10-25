/* Validate a saved authored family member; no execution or evidence authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,Settings=node?require('./finite-settings.js'):root.FiniteSettings,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler;
 const same=(a,b)=>E.stable(a)===E.stable(b),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 function validate(value,task,{inputVersion}={}){
  const relation=J.capture(value,{maxBytes:64*1024,maxDepth:24,maxNodes:30000});
  if(!exact(relation,['kind','card','settings','declaredPages','remainingPages'])||relation.kind!=='finite-settings-member')throw Error('Invalid authored finite-member relation.');
  E.validateTask(task);
  const member=Settings.factored.member(relation.card,relation.settings),plan=Compiler.compile(member.card),declared=relation.card.scope?.value?.pages,current=task.pages.map(p=>p.id);
  if(plan.reason||plan.state||!same(member.settings,relation.settings)||!same(declared,relation.declaredPages)||!same(plan.pages,declared)||!same(current,relation.remainingPages)||!same(current,declared.filter(id=>current.includes(id)))||!same(plan.steps,task.steps)||!same(plan.criterion,task.criterion)||inputVersion!==undefined&&inputVersion!==plan.inputVersion)throw Error('The saved calculation changed its authored family member.');
  return Object.freeze({inputVersion:plan.inputVersion,settings:member.settings,declaredPages:relation.declaredPages,remainingPages:relation.remainingPages});
 }
 const api={validate};if(node)module.exports=api;else root.FiniteOriginRelation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
