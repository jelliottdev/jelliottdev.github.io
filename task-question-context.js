/* Selected original-question context only. No evidence counts or execution authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle,Authored=node?require('./followup-context.js'):root.FollowupContext,Reviewed=node?require('./reviewed-program.js'):root.ReviewedProgram;
 const HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/,tokens=new WeakMap(),capture=(v,maxBytes=8*1024*1024)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(key=>Object.hasOwn(v,key))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable);
 function route(hash){if(typeof hash!=='string')return null;const match=/^#task=([a-f0-9]{64})(?:&(idea|fromIdea)=(p_[a-f0-9]{64}))?$/.exec(hash);return match?Object.freeze({kind:'task',id:match[1],...(match[2]==='idea'?{proposalId:match[3]}:match[2]==='fromIdea'?{fromIdea:match[3]}:{})}):null;}
 function href(taskId,proposalId){if(!HEX.test(taskId)||proposalId!==undefined&&!IDEA.test(proposalId))throw Error('Use an exact task and optional original idea identity.');return '#task='+taskId+(proposalId===undefined?'':'&idea='+proposalId);}
 // Presentation-only context hint. Stored evidence links and explicit associations stay unchanged.
 function inspectionHref(sourceHref,proposalId){
  if(typeof sourceHref!=='string'||!IDEA.test(proposalId))throw Error('Use an inspection link and exact current idea identity.');
  return /^(?:run\.html)?#task=[a-f0-9]{64}$/.test(sourceHref)?sourceHref+'&fromIdea='+proposalId:sourceHref;
 }
 async function verify(options,crypto=root.crypto){
  if(!exact(options,['taskId','proposalId','projection','bundle']))throw Error('Use the selected task, original idea and official input bundle.');const input=capture(options),{taskId,proposalId,projection,bundle}=input;
  if(!HEX.test(taskId)||!IDEA.test(proposalId)||!projection||projection.id!==taskId||projection.plan?.taskId!==taskId||projection.proposalId!==proposalId||projection.linkedProposalId!==proposalId||!['raw','reviewed'].includes(projection.inputVersion)||projection.linkedInputVersion!==projection.inputVersion||!(projection.parentTaskId===null||typeof projection.parentTaskId==='string'&&HEX.test(projection.parentTaskId))||projection.linkedParentTaskId!==projection.parentTaskId)throw Error('The task does not identify this selected original idea association.');
  const card=capture(projection.card,H.MAX_BYTES);H.sections(card);const cardHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(card))))].map(v=>v.toString(16).padStart(2,'0')).join('');if(proposalId!=='p_'+cardHash)throw Error('The selected original idea changed its canonical card identity.');
  const task=projection.plan;await E.checkIdentity(task,crypto);const source=Inputs.parse(capture(bundle,2*1024*1024));if(E.stable(task.alphabet)!==E.stable(source.alphabet))throw Error('The selected task changed the official alphabet.');
  for(const page of task.pages){const official=source.pages.get(page.id),text=projection.inputVersion==='raw'?official?.raw:official?.reviewed_text;if(typeof text!=='string'||page.text!==text)throw Error('The selected task changed its official page bytes or input edition.');}
  const reviewedProgram=Object.hasOwn(projection,'reviewedProgram')?(await Reviewed.verifyProof({proof:projection.reviewedProgram,originalCard:card,task,inputVersion:projection.inputVersion},crypto)).proof:null;
  const declaredPages=card.scope.status==='specified'&&Array.isArray(card.scope.value?.pages)?[...card.scope.value.pages]:[],plan=Compiler.compile(reviewedProgram?reviewedProgram.normalizedCard:card),comparable=!plan.reason&&!plan.state&&Array.isArray(plan.pages)&&Array.isArray(plan.steps)&&!!plan.criterion;
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
  const token=Object.freeze({});tokens.set(token,freeze({proposalId,card,taskPages:task.pages.map(page=>page.id),declaredPages,comparable,...(reviewedProgram?{reviewedProgram}:{})}));return token;
 }
 // JSON.parse alone silently accepts duplicate keys and lone surrogate escapes.
 function authoredJSON(text){
  const parsed=JSON.parse(text),stack=[],tokens=text.match(/"(?:\\[\s\S]|[^"\\])*"|[{}\[\]:,]/g)||[];
  for(const token of tokens){
   if(token[0]==='"'){
    const value=JSON.parse(token);if(/[\ud800-\udfff]/u.test(value))throw Error('The authored source contains malformed Unicode.');
    const top=stack[stack.length-1];if(top?.keys&&top.key){if(top.keys.has(value))throw Error('The authored source contains duplicate fields.');top.keys.add(value);top.key=false;}
   }else if(token==='{')stack.push({keys:new Set(),key:true});else if(token==='[')stack.push({});else if(token==='}'||token===']')stack.pop();else if(token===','&&stack[stack.length-1]?.keys)stack[stack.length-1].key=true;
  }
  return capture(parsed,2*1024*1024);
 }
 async function readAuthoredContext(options,crypto=root.crypto){
  if(!exact(options,['origin','bytes'])||!exact(options.origin,['recordId','followupId','recordSha256','protocolSha256']))throw Error('Use an exact published source identity and its raw bytes.');
  const origin=capture(options.origin,1024),bytes=options.bytes,slug=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  if(![origin.recordId,origin.followupId].every(id=>typeof id==='string'&&id.length<=100&&slug.test(id))||![origin.recordSha256,origin.protocolSha256].every(id=>typeof id==='string'&&HEX.test(id))||!ArrayBuffer.isView(bytes)||Object.prototype.toString.call(bytes)!=='[object Uint8Array]'||!bytes.byteLength||bytes.byteLength>2*1024*1024)throw Error('The authored source identity or byte bound is invalid.');
  const raw=new Uint8Array(bytes),hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',value))].map(v=>v.toString(16).padStart(2,'0')).join('');
  if(await hash(raw)!==origin.recordSha256)throw Error('The authored source bytes changed.');
  const record=authoredJSON(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(raw));
  if(record.id!==origin.recordId||record.status!=='published'||!Array.isArray(record.browser_followups))throw Error('The authored source is not this published record.');
  const matches=record.browser_followups.filter(recipe=>recipe?.id===origin.followupId);if(matches.length!==1)throw Error('The authored source does not identify one matching check.');
  const recipe=matches[0];if(recipe.kind!=='finite-settings'&&raw.byteLength>512*1024)throw Error('The fixed authored source exceeds its byte bound.');if(await hash(new TextEncoder().encode(E.stable(recipe)))!==origin.protocolSha256)throw Error('The authored check changed.');
  if(typeof recipe.question!=='string'||!recipe.question.trim()||Array.from(recipe.question).length>1200||Object.hasOwn(recipe,'motivation')&&!Authored?.valid(recipe.motivation))throw Error('The authored explanation is invalid.');
  if(Object.hasOwn(recipe,'title')&&(typeof recipe.title!=='string'||recipe.title!==recipe.title.trim()||!recipe.title||Array.from(recipe.title).length>300||/[\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u.test(recipe.title)))throw Error('The authored title is invalid.');
  return Object.freeze({question:recipe.question,...(Object.hasOwn(recipe,'title')?{title:recipe.title}:{}),...(Object.hasOwn(recipe,'motivation')?{motivation:recipe.motivation}:{})});
 }
 function inspect(token){const value=tokens.get(token);if(!value)throw Error('Use independently bound original-question context.');return value;}
 const api={route,href,inspectionHref,verify,inspect,readAuthoredContext};if(node)module.exports=api;else root.TaskQuestionContext=api;
})(typeof globalThis!=='undefined'?globalThis:this);
