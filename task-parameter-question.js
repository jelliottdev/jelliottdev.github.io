/* Exact task variations become new canonical questions, never edits to a parent.
 * The caller must authenticate the task/card association and saved evidence;
 * this pure derivation neither grants admission nor asserts prior coverage. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,V=node?require('./task-parameter-variants.js'):root.TaskParameterVariants,F=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,S=node?require('./finite-settings.js'):root.FiniteSettings,Reviewed=node?require('./reviewed-program.js'):root.ReviewedProgram;
 // Full canonical GP29 table: rune order, transliterations and prime assignments.
 const ALPHABET_SHA256='06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f';
 const SCHEMA='liberpedia-task-parameter-question-v1',same=(a,b)=>E.stable(a)===E.stable(b),ensure=(v,m)=>{if(!v)throw Error(m);},freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const field=value=>C.field('specified',value),copy=v=>JSON.parse(E.stable(v));
 const EVALUATIONS=['language-samples','warning-opening'];
 function selection(input){const value=J.capture(input,{maxBytes:1024,maxDepth:3,maxNodes:16});if(value?.parameter!=='evaluation')return V.selection(value);ensure(value&&Object.keys(value).length===2&&Object.hasOwn(value,'value')&&EVALUATIONS.includes(value.value),'Choose one maintained output check.');return freeze(value);}
 function evaluationChoices(task){E.validateTask(task);if(!same(task.criterion,{kind:'measurement'})||task.steps.length===0)return Object.freeze([]);return freeze(EVALUATIONS.map(id=>{const choice=C.EVALUATION_CHOICES.find(item=>item.id===id);return {selection:{parameter:'evaluation',value:id},label:choice.label,description:choice.example,criterion:copy(choice.value)};}));}
 async function hash(value,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function canonical(card){
  const text=E.stable(card),bytes=new TextEncoder().encode(text);ensure(bytes.length<=H.MAX_BYTES,'The original question exceeds the card limit.');let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);
  const imported=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')),confirmed=C.confirm(imported.draft,{id:'parameter-question-validation',at:'2000-01-01T00:00:00.000Z'}),checked=H.cardData(confirmed);ensure(same(card,checked),'Use an unchanged canonical parent question.');return checked;
 }
 function operation(step){
  if(step.op==='affine')return {id:'affine',label:'Affine substitution',a:step.a,b:step.b};
  if(step.op==='reverse')return {id:'reverse_runes',label:'Reverse rune order within each '+step.unit,unit:step.unit};
  if(step.op==='cumulative-difference')return {id:'cumulative_difference',label:'Cumulative difference',reset:step.reset};
  ensure(['finite-shift','interrupted-keyed-shift','keyed-shift'].includes(step.op),'An unchanged step needs a canonical question adapter.');
  const common={key:copy(step.key),direction:step.direction,reset:step.reset};
  if(step.op==='finite-shift')return {id:'finite_key',label:'Finite key stream',...common};
  if(step.op==='interrupted-keyed-shift')return {id:'interrupted_repeating_key',label:'Interrupted repeating key',...common,interrupts:copy(step.interrupts)};
  if(step.op==='keyed-shift'){
   const mode={repeat:['repeating_key','Repeating key'],'plaintext-autokey':['plaintext_autokey','Plaintext autokey'],'ciphertext-autokey':['ciphertext_autokey','Ciphertext autokey']}[step.mode];ensure(mode,'This key mode cannot be represented as a canonical question.');return {id:mode[0],label:mode[1],...common};
  }
  throw Error('An unchanged step needs a canonical question adapter.');
 }
 async function prepare(input,crypto=root.crypto){
  const value=J.capture(input,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),hasSettings=!!value&&Object.hasOwn(value,'parentSettings'),hasReviewed=!!value&&Object.hasOwn(value,'reviewedProgram');ensure(value&&Object.keys(value).length===4+Number(hasSettings)+Number(hasReviewed)&&['parentTask','parentCard','inputVersion','selection'].every(k=>Object.hasOwn(value,k))&&['raw','reviewed'].includes(value.inputVersion)&&!(hasSettings&&hasReviewed),'Use the exact parent task, question, input version and selected change.');
  ensure(await hash(value.parentTask.alphabet,crypto)===ALPHABET_SHA256,'The parent calculation must use the canonical GP29 alphabet.');
  const original=canonical(value.parentCard),reviewedProgram=hasReviewed?(await Reviewed.verifyProof({proof:value.reviewedProgram,originalCard:original,task:value.parentTask,inputVersion:value.inputVersion},crypto)).proof:null,member=hasSettings?S.factored.member(original,value.parentSettings):null,parentPlan=F.compile(reviewedProgram?reviewedProgram.normalizedCard:member?member.card:original);
  ensure(!parentPlan.reason&&same(parentPlan.steps,value.parentTask.steps)&&same(parentPlan.criterion,value.parentTask.criterion)&&parentPlan.inputVersion===value.inputVersion&&value.parentTask.pages.every(p=>parentPlan.pages.includes(p.id)),'The parent question does not describe this exact calculation; finite questions require their explicit member settings.');
  const chosen=selection(value.selection),evaluation=chosen.parameter==='evaluation';
  if(evaluation){
   await E.checkIdentity(value.parentTask,crypto);
   ensure(!hasSettings&&original.outcome.status==='specified'&&original.outcome.value.outcomeId==='decipher'&&same(value.parentTask.pages.map(p=>p.id),parentPlan.pages),'An output-check follow-up needs the complete fixed decipher question.');
   const choice=evaluationChoices(value.parentTask).find(item=>same(item.selection,chosen));ensure(choice,'The parent must show transformed output and counts without a readability verdict.');
   const task=await E.prepare({title:'Check output: '+choice.label,pages:copy(value.parentTask.pages),alphabet:copy(value.parentTask.alphabet),steps:copy(value.parentTask.steps),criterion:copy(choice.criterion)},crypto),card=copy(reviewedProgram?reviewedProgram.normalizedCard:original);card.rules.evaluation={status:'specified',value:copy(choice.criterion)};canonical(card);
   const compiled=F.compile(card);ensure(!compiled.reason&&!compiled.state&&same(card.outcome,original.outcome)&&same(compiled.steps,value.parentTask.steps)&&same(compiled.pages,parentPlan.pages)&&same(compiled.criterion,task.criterion)&&compiled.inputVersion===value.inputVersion,'The output-check follow-up changed its declared calculation.');
   const parent={taskId:value.parentTask.taskId,taskSha256:await hash(value.parentTask,crypto),cardSha256:await hash(original,crypto),inputVersion:value.inputVersion};ensure(same(J.capture(input,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),value),'The parent question changed during preparation.');
   return freeze({schema:SCHEMA,parent,selection:chosen,card,task});
  }
  const task=await V.prepare(value.parentTask,chosen,crypto),operations=task.steps.map(operation);
  const draft=C.createDraft({source:{text:'A direct parameter variation of a saved calculation.'},aim:copy(original.outcome),method:field({operations}),scope:field({pages:task.pages.map(p=>p.id)}),rules:{inputVersion:field(value.inputVersion),representation:field('GP29'),unmapped:field('preserve'),wordBoundaries:field('preserve'),...(task.steps.some(s=>s.op==='cumulative-difference')?{initialState:field(0)}:{}),evaluation:field(task.criterion.kind==='measurement'?'measurement':copy(task.criterion))}}),card=H.cardData(C.confirm(draft,{id:'parameter-variation',at:'2000-01-01T00:00:00.000Z'}));
  canonical(card);ensure(same(card.outcome,original.outcome),'The variation changed the research aim.');
  const compiled=F.compile(card);ensure(!compiled.reason&&same(compiled.steps,task.steps)&&same(compiled.criterion,task.criterion)&&same(compiled.pages,task.pages.map(p=>p.id))&&compiled.inputVersion===value.inputVersion,'The new question does not describe the exact varied calculation.');
  return freeze({schema:SCHEMA,parent:{taskId:value.parentTask.taskId,taskSha256:await hash(value.parentTask,crypto),cardSha256:await hash(original,crypto),inputVersion:value.inputVersion,...(member?{settings:copy(member.settings)}:{})},selection:copy(value.selection),card,task});
 }
 async function validate(input,derived,crypto=root.crypto){const snapshot=J.capture(derived,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),expected=await prepare(input,crypto);ensure(same(snapshot,expected),'The varied question or parent relationship changed.');return expected;}
 // Reconstruct the literal archived opening check, not its author's intent or
 // membership in a present-day recipe. The receipt is authenticated by caller.
 async function archived(input,crypto=root.crypto){
  const capture=value=>J.capture(value,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:250000}),value=capture(input);
  ensure(value&&Object.keys(value).length===2&&['task','inputVersion'].every(k=>Object.hasOwn(value,k))&&['raw','reviewed'].includes(value.inputVersion),'Use an exact archived task and input version.');
  const unchanged=()=>ensure(same(capture(input),value),'The archived calculation changed during question preparation.');
  await E.checkIdentity(value.task,crypto);unchanged();
  ensure(['exact-prefix','exact-prefix-set'].includes(value.task.criterion.kind),'Only literal archived opening checks can become this question.');
  ensure(await hash(value.task.alphabet,crypto)===ALPHABET_SHA256,'The archived calculation must use the canonical GP29 alphabet.');unchanged();
  const operations=value.task.steps.map(operation),draft=C.createDraft({source:{text:'An exact supplied-opening check reconstructed from an archived calculation.'},aim:field({outcomeId:'decipher',wording:'Check the supplied opening after the declared transformations.',detail:'Check the supplied opening after the declared transformations.'}),method:field({operations}),scope:field({pages:value.task.pages.map(p=>p.id)}),rules:{inputVersion:field(value.inputVersion),representation:field('GP29'),unmapped:field('preserve'),wordBoundaries:field('preserve'),...(value.task.steps.some(s=>s.op==='cumulative-difference')?{initialState:field(0)}:{}),evaluation:field(copy(value.task.criterion))}}),card=H.cardData(C.confirm(draft,{id:'archived-opening-question',at:'2000-01-01T00:00:00.000Z'}));
  canonical(card);const compiled=F.compile(card);
  ensure(!compiled.reason&&!compiled.state&&same(compiled.steps,value.task.steps)&&same(compiled.criterion,value.task.criterion)&&same(compiled.pages,value.task.pages.map(p=>p.id))&&compiled.inputVersion===value.inputVersion,'The reconstructed question does not describe the exact archived calculation.');
  const cardSha256=await hash(card,crypto);unchanged();const taskSha256=await hash(value.task,crypto);unchanged();
  return freeze({card,proposalId:'p_'+cardSha256,cardSha256,taskSha256});
 }
 const api={SCHEMA,ALPHABET_SHA256,selection,evaluationChoices,prepare,validate,archived};if(node)module.exports=api;else root.TaskParameterQuestion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
