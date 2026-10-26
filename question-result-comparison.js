/* Compare only retained, independently replayed outputs on shared saved pages.
 * No missing baseline is calculated; neither difference nor sameness is readability. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,F=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,S=node?require('./finite-settings.js'):root.FiniteSettings,RP=node?require('./reviewed-program.js'):root.ReviewedProgram,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle,Context=node?require('./task-question-context.js'):root.TaskQuestionContext,Links=node?require('./question-variation-links.js'):root.QuestionVariationLinks;
 const tokens=new WeakMap(),HEX=/^[a-f0-9]{64}$/,same=(a,b)=>E.stable(a)===E.stable(b),ensure=(v,m)=>{if(!v)throw Error(m);},exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k)),capture=v=>J.capture(v,{maxBytes:16*1024*1024,maxDepth:28,maxNodes:1000000}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},iso=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
 async function hash(v,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 async function saved(projection,proposalId,card,crypto){
  ensure(projection&&projection.state==='results-verified'&&projection.id===projection.plan?.taskId&&projection.proposalId===proposalId&&projection.linkedProposalId===proposalId&&same(projection.card,card)&&['raw','reviewed'].includes(projection.inputVersion)&&projection.linkedInputVersion===projection.inputVersion&&(projection.parentTaskId===null||typeof projection.parentTaskId==='string'&&HEX.test(projection.parentTaskId))&&projection.parentTaskId===projection.linkedParentTaskId,'The saved output has no exact original question association.');
  await E.checkIdentity(projection.plan,crypto);
  const run=projection.latestRun;ensure(exact(run,['id','createdAt','result'])&&typeof run.id==='string'&&HEX.test(run.id)&&iso(run.createdAt)&&run.result?.taskId===projection.id&&await hash(run.result,crypto)===run.id,'The saved output receipt changed.');
  ensure(await E.verify(projection.plan,run.result,crypto),'The saved output does not reproduce its declared calculation.');
 }
 async function prepare(input,crypto=root.crypto){
  const value=capture(input),unchanged=()=>ensure(same(capture(input),value),'The result comparison changed during verification.');
  ensure(exact(value,['entry','childProposalId','childCard','childProjection','parentProjection','bundle'])&&crypto?.subtle,'Use one retained variation and both exact saved projections.');
  const {entry,childProposalId,childCard,childProjection:child,parentProjection:parent}=value,o=entry?.origin;
  const relation=await Links.validate(entry,{ideaId:childProposalId,direction:'parents',crypto});unchanged();
  ensure(same(childCard,entry.childCard),'The selected child question changed.');
  const source=o.source,ref=source.reference,pin=source.receipt;
  ensure(['saved-task','saved-question-program'].includes(ref.kind),'Comparison currently requires a saved parent calculation; published sources are not supported.');
  await saved(parent,o.parentProposalId,entry.parentCard,crypto);unchanged();
  ensure(parent.id===ref.taskId&&parent.id===pin.taskId&&await hash(parent.plan,crypto)===pin.taskSha256&&parent.latestRun.id===pin.resultId&&parent.latestRun.createdAt===pin.createdAt&&parent.inputVersion===pin.inputVersion,'The parent output is not the exact calculation retained by this variation.');unchanged();
  const official=Inputs.parse(value.bundle),reviewed=source.reviewedProgram;
  ensure(!Object.hasOwn(parent,'reviewedProgram')||reviewed&&same(parent.reviewedProgram,reviewed),'The parent mapping differs from its retained variation.');
  let before;
  if(reviewed){const bound=await RP.verifyProof({proof:reviewed,originalCard:entry.parentCard,task:parent.plan,inputVersion:pin.inputVersion},crypto);before=F.compile(bound.proof.normalizedCard);}else before=F.compile(Object.hasOwn(o,'parentSettings')?S.factored.member(entry.parentCard,o.parentSettings).card:entry.parentCard);
  unchanged();ensure(!before.reason&&!before.state&&before.inputVersion===pin.inputVersion&&same(before.steps,parent.plan.steps)&&same(before.criterion,parent.plan.criterion)&&same(parent.plan.alphabet,official.alphabet),'The parent calculation changed its declared program.');
  const parentIds=parent.plan.pages.map(p=>p.id);ensure(same(parentIds,before.pages.filter(id=>parentIds.includes(id))),'The parent saved scope changed.');
  for(const page of parent.plan.pages)ensure(page.text===official.pages.get(page.id)?.[pin.inputVersion==='raw'?'raw':'reviewed_text'],'The parent calculation changed its official source bytes.');
  const fullPages=before.pages.map(id=>{const text=official.pages.get(id)?.[pin.inputVersion==='raw'?'raw':'reviewed_text'];ensure(typeof text==='string','The original question has no official text in this edition.');return {id,text};});
  const full=await E.prepare({title:'Complete declared question',pages:fullPages,alphabet:official.alphabet,steps:before.steps,criterion:before.criterion},crypto);unchanged();
  if(o.schema===Links.QUESTION_SCHEMA)ensure(source.questionProgram.taskId===full.taskId&&source.questionProgram.taskSha256===await hash(full,crypto)&&source.questionProgram.inputVersion===pin.inputVersion,'The complete original question program changed.');unchanged();
  const token=await Context.verify({taskId:child.id,proposalId:childProposalId,projection:child,bundle:value.bundle},crypto);unchanged();ensure(Context.inspect(token).comparable,'The child output is not the declared variation program.');
  await saved(child,childProposalId,childCard,crypto);unchanged();ensure(child.inputVersion===pin.inputVersion,'The compared outputs use different source editions.');
  const childIds=child.plan.pages.map(p=>p.id),sharedPages=parentIds.filter(id=>childIds.includes(id)),alphabet=new Set(official.alphabet.map(r=>r.rune)),pages=[];
  let runeCount=0,changedRunes=0;
  for(const id of sharedPages){const a=parent.latestRun.result.transformed.find(p=>p.page===id).text,b=child.latestRun.result.transformed.find(p=>p.page===id).text,left=Array.from(a),right=Array.from(b),changes=[];let position=0;
   ensure(left.length===right.length,'The compared outputs changed their source geometry.');for(let i=0;i<left.length;i++){if(alphabet.has(left[i])){position++;ensure(alphabet.has(right[i]),'The compared output contains a different rune alphabet.');if(left[i]!==right[i])changes.push({position,before:left[i],after:right[i]});}else ensure(left[i]===right[i],'The compared outputs changed separators.');}
   runeCount+=position;changedRunes+=changes.length;pages.push({id,parentText:a,childText:b,runeCount:position,changedRunes:changes.length,changes});
  }
  const summary=(projection,proposalId)=>({proposalId,href:'run.html#idea='+proposalId,taskHref:'run.html#task='+projection.id+'&idea='+proposalId,taskId:projection.id,resultId:projection.latestRun.id,createdAt:projection.latestRun.createdAt,pages:projection.plan.pages.map(p=>p.id)});
  unchanged();const model=freeze({schema:'liberpedia-question-result-comparison-v1',variationId:entry.id,alphabet:official.alphabet.map(({rune,latin})=>({rune,latin})),label:relation.label,description:relation.description,parent:summary(parent,o.parentProposalId),child:summary(child,childProposalId),declaredParentPages:[...entry.parentCard.scope.value.pages],declaredChildPages:[...childCard.scope.value.pages],sharedPages,parentOnlyPages:parentIds.filter(id=>!childIds.includes(id)),childOnlyPages:childIds.filter(id=>!parentIds.includes(id)),runeCount,changedRunes,pages});const result=Object.freeze({});tokens.set(result,model);return result;
 }
 function inspect(token){const model=tokens.get(token);ensure(model,'Use an independently verified result comparison.');return model;}
 const api={prepare,inspect};if(node)module.exports=api;else root.QuestionResultComparison=api;
})(typeof globalThis!=='undefined'?globalThis:this);
