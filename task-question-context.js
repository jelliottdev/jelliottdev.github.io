/* Selected original-question context only. No evidence counts or execution authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle;
 const HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/,tokens=new WeakMap(),capture=(v,maxBytes=8*1024*1024)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(key=>Object.hasOwn(v,key))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable);
 function route(hash){if(typeof hash!=='string')return null;const match=/^#task=([a-f0-9]{64})(?:&idea=(p_[a-f0-9]{64}))?$/.exec(hash);return match?Object.freeze({kind:'task',id:match[1],...(match[2]?{proposalId:match[2]}:{})}):null;}
 function href(taskId,proposalId){if(!HEX.test(taskId)||proposalId!==undefined&&!IDEA.test(proposalId))throw Error('Use an exact task and optional original idea identity.');return '#task='+taskId+(proposalId===undefined?'':'&idea='+proposalId);}
 async function verify(options,crypto=root.crypto){
  if(!exact(options,['taskId','proposalId','projection','bundle']))throw Error('Use the selected task, original idea and official input bundle.');const input=capture(options),{taskId,proposalId,projection,bundle}=input;
  if(!HEX.test(taskId)||!IDEA.test(proposalId)||!projection||projection.id!==taskId||projection.plan?.taskId!==taskId||projection.proposalId!==proposalId||projection.linkedProposalId!==proposalId||!['raw','reviewed'].includes(projection.inputVersion)||projection.linkedInputVersion!==projection.inputVersion||!(projection.parentTaskId===null||typeof projection.parentTaskId==='string'&&HEX.test(projection.parentTaskId))||projection.linkedParentTaskId!==projection.parentTaskId)throw Error('The task does not identify this selected original idea association.');
  const card=capture(projection.card,H.MAX_BYTES);H.sections(card);const cardHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(card))))].map(v=>v.toString(16).padStart(2,'0')).join('');if(proposalId!=='p_'+cardHash)throw Error('The selected original idea changed its canonical card identity.');
  const task=projection.plan;await E.checkIdentity(task,crypto);const source=Inputs.parse(capture(bundle,2*1024*1024));if(E.stable(task.alphabet)!==E.stable(source.alphabet))throw Error('The selected task changed the official alphabet.');
  for(const page of task.pages){const official=source.pages.get(page.id),text=projection.inputVersion==='raw'?official?.raw:official?.reviewed_text;if(typeof text!=='string'||page.text!==text)throw Error('The selected task changed its official page bytes or input edition.');}
  const declaredPages=card.scope.status==='specified'&&Array.isArray(card.scope.value?.pages)?[...card.scope.value.pages]:[],plan=Compiler.compile(card),comparable=!plan.reason&&!plan.state&&Array.isArray(plan.pages)&&Array.isArray(plan.steps)&&!!plan.criterion;
  if(comparable){
   if(plan.inputVersion!==projection.inputVersion||E.stable(plan.pages)!==E.stable(declaredPages)||E.stable(plan.steps)!==E.stable(task.steps)||E.stable(plan.criterion)!==E.stable(task.criterion)||task.pages.some(page=>!declaredPages.includes(page.id)))throw Error('The selected calculation is not an exact subset of the original question.');
   const fullPages=declaredPages.map(id=>{const page=source.pages.get(id),text=plan.inputVersion==='raw'?page?.raw:page?.reviewed_text;if(typeof text!=='string')throw Error('The complete original scope has no official text in this edition.');return {id,text};});
   // A later page can invalidate a finite key even when this subset is valid.
   // Validate the whole original input program without executing any target.
   await E.prepare({title:task.title,pages:fullPages,alphabet:source.alphabet,steps:plan.steps,criterion:plan.criterion},crypto);
   // Task validation establishes canonical page order; subset equality also
   // prevents dropping/reordering an original page under the same subset label.
   if(E.stable(task.pages.map(page=>page.id))!==E.stable(declaredPages.filter(id=>task.pages.some(page=>page.id===id))))throw Error('The selected task changed the original page order.');
  }
  const token=Object.freeze({});tokens.set(token,freeze({proposalId,card,taskPages:task.pages.map(page=>page.id),declaredPages,comparable}));return token;
 }
 function inspect(token){const value=tokens.get(token);if(!value)throw Error('Use independently bound original-question context.');return value;}
 const api={route,href,verify,inspect};if(node)module.exports=api;else root.TaskQuestionContext=api;
})(typeof globalThis!=='undefined'?globalThis:this);
