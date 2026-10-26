/* Retained question lineage, not execution or coverage evidence. No I/O. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,F=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,S=node?require('./finite-settings.js'):root.FiniteSettings,V=node?require('./task-parameter-variants.js'):root.TaskParameterVariants,Reviewed=node?require('./reviewed-program.js'):root.ReviewedProgram;
 const SCHEMA='liberpedia-question-derivation-v1',MAPPED_SCHEMA='liberpedia-question-derivation-v2',QUESTION_SCHEMA='liberpedia-question-derivation-v3',EVALUATION_SCHEMA='liberpedia-question-derivation-v4',HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),same=(a,b)=>E.stable(a)===E.stable(b),ensure=(v,m)=>{if(!v)throw Error(m);},freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},capture=v=>J.capture(v,{maxBytes:131072,maxDepth:24,maxNodes:20000}),iso=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
 async function hash(v,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function canonical(card){
  const text=E.stable(card);ensure(new TextEncoder().encode(text).length<=H.MAX_BYTES,'The question exceeds its card limit.');let binary='';for(const b of new TextEncoder().encode(text))binary+=String.fromCharCode(b);
  const draft=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft,checked=H.cardData(C.confirm(draft,{id:'lineage-card-validation',at:'2000-01-01T00:00:00.000Z'}));ensure(same(checked,card),'The retained question is not canonical.');return checked;
 }
 function source(origin){
  const value=origin.source,mapped=origin.schema===MAPPED_SCHEMA,question=[QUESTION_SCHEMA,EVALUATION_SCHEMA].includes(origin.schema),reviewed=mapped||question&&Object.hasOwn(value||{},'reviewedProgram');
  ensure(exact(value,['reference','receipt',...(Object.hasOwn(value||{},'publishedSource')?['publishedSource']:[]),...(reviewed?['reviewedProgram']:[]),...(question?['questionProgram']:[])]),'The variation source fields changed.');
  ensure(!(mapped||question)||!Object.hasOwn(origin,'parentSettings')&&!Object.hasOwn(value,'publishedSource'),'A saved program cannot use archived references or family settings.');
  const r=value.reference,p=value.receipt;ensure(r&&r.proposalId===origin.parentProposalId&&(question?r.kind==='saved-question-program':['saved-task','published-program','archived-program'].includes(r.kind)),'The source identifies another parent.');
  ensure(!mapped||r.kind==='saved-task','A reviewed mapping needs an exact saved-task source.');
  ensure(exact(p,['taskId','taskSha256','resultId','createdAt','inputVersion'])&&[p.taskId,p.taskSha256,p.resultId].every(v=>typeof v==='string'&&HEX.test(v))&&iso(p.createdAt)&&['raw','reviewed'].includes(p.inputVersion),'The retained source receipt changed.');
  if(question){const program=value.questionProgram;ensure(exact(program,['taskId','taskSha256','inputVersion'])&&[program.taskId,program.taskSha256].every(v=>typeof v==='string'&&HEX.test(v))&&program.inputVersion===p.inputVersion,'The complete question program changed.');}
  if(r.kind==='saved-task'||r.kind==='saved-question-program'){ensure(exact(r,['kind','proposalId','taskId'])&&r.taskId===p.taskId&&!Object.hasOwn(value,'publishedSource'),'The saved source reference changed.');return null;}
  ensure(exact(r,['kind','proposalId','recordId','revision','caseId'])&&typeof r.recordId==='string'&&r.recordId.length<=100&&SLUG.test(r.recordId)&&typeof r.revision==='string'&&HEX.test(r.revision)&&typeof r.caseId==='string'&&r.caseId.length<=200&&/^[a-z0-9-]+$/.test(r.caseId),'The archived source reference changed.');
  const published=value.publishedSource;ensure(exact(published,['taskId','resultId','recordId','revision','caseId'])&&published.taskId===p.taskId&&published.resultId===p.resultId&&['recordId','revision','caseId'].every(k=>published[k]===r[k]),'The archived source pins disagree.');
  ensure(r.kind!=='archived-program'||!Object.hasOwn(origin,'parentSettings'),'A fixed archived source cannot select family settings.');
  return 'run.html#published='+encodeURIComponent(r.recordId)+'&case='+encodeURIComponent(r.caseId)+'&revision='+r.revision;
 }

 function evaluationSelection(value){ensure(exact(value,['parameter','value'])&&value.parameter==='evaluation'&&['language-samples','warning-opening'].includes(value.value),'Choose a maintained output check.');return value;}
 function change(steps,selection){
  const s=steps[selection.step],p=selection.parameter;ensure(s&&(p==='mode'?s.op==='keyed-shift':p==='unit'?s.op==='reverse':p==='direction'?['keyed-shift','interrupted-keyed-shift','finite-shift'].includes(s.op):['keyed-shift','interrupted-keyed-shift','finite-shift','cumulative-difference'].includes(s.op)),'The selected operation does not support that change.');ensure(s[p]!==selection.value,'The variation must change its selected parameter.');
  const copy=JSON.parse(E.stable(steps));copy[selection.step][p]=selection.value;return copy;
 }
 function wording(step,selection){
  const p=selection.parameter,to=selection.value,from=step[p],number=selection.step+1;let label,description;
  if(p==='mode'){
   const names={repeat:'repeat the starting key','plaintext-autokey':'use decoded runes for later key numbers','ciphertext-autokey':'use input runes for later key numbers'};
   label=to==='repeat'?'Repeat the starting key':to==='plaintext-autokey'?'Continue the key with decoded runes':'Continue the key with input runes';description='Step '+number+': '+names[from]+' → '+names[to]+'.'+([from,to].includes('plaintext-autokey')?' Decoded runes are calculated output, not confirmed readable text.':'');
  }else if(p==='unit'){label='Reverse rune order within each '+to;description='Step '+number+': reverse runes within each '+from+' → each '+to+'. Spaces, punctuation and line breaks stay in place.';}
  else if(p==='direction'){label=to==='add'?'Add the key numbers':'Subtract the key numbers';description='Step '+number+': '+(from==='add'?'add':'subtract')+' → '+to+' the same key numbers. The key and restart boundaries stay the same.';}
  else {label='Restart '+(step.op==='cumulative-difference'?'the running total':step.op==='finite-shift'?'the number sequence':'the key')+' at each '+to;description='Step '+number+': restart at each '+from+' → each '+to+'. The other calculation steps stay the same.';}
  return {label,description};
 }
 async function validate(entry,{ideaId,direction,crypto=root.crypto}={}){
  ensure(typeof ideaId==='string'&&IDEA.test(ideaId)&&['parents','children'].includes(direction)&&crypto?.subtle,'Choose an exact question and relationship direction.');
  const value=capture(entry),unchanged=()=>ensure(same(capture(entry),value),'The retained variation changed during validation.');
  ensure(exact(value,['id','createdAt','origin','parentCard','childCard'])&&typeof value.id==='string'&&HEX.test(value.id)&&iso(value.createdAt),'The retained variation envelope changed.');
  const o=value.origin,settings=Object.hasOwn(o||{},'parentSettings');ensure(new TextEncoder().encode(E.stable(o)).length<=65536,'The retained origin exceeds its byte bound.');ensure(exact(o,['schema','parentProposalId','childProposalId','previewHash','source','selection',...(settings?['parentSettings']:[]),'childTaskId'])&&[SCHEMA,MAPPED_SCHEMA,QUESTION_SCHEMA,EVALUATION_SCHEMA].includes(o.schema)&&[o.parentProposalId,o.childProposalId].every(v=>typeof v==='string'&&IDEA.test(v))&&o.parentProposalId!==o.childProposalId&&[o.previewHash,o.childTaskId].every(v=>typeof v==='string'&&HEX.test(v)),'The retained origin fields changed.');
  ensure((direction==='parents'?o.childProposalId:o.parentProposalId)===ideaId,'The variation belongs to another question.');
  const evaluation=o.schema===EVALUATION_SCHEMA;
  const sourceHref=source(o),selection=evaluation?evaluationSelection(o.selection):V.selection(o.selection),parent=canonical(value.parentCard),child=canonical(value.childCard);
  ensure(await hash(o,crypto)===value.id,'The retained origin identity changed.');unchanged();
  ensure('p_'+await hash(C.serialize(parent),crypto)===o.parentProposalId&&'p_'+await hash(C.serialize(child),crypto)===o.childProposalId,'The retained question identity changed.');unchanged();
  const member=settings?S.factored.member(parent,o.parentSettings):null;ensure(!member||same(member.settings,o.parentSettings),'The finite member assignments changed.');
  const reviewed=(o.schema===MAPPED_SCHEMA||[QUESTION_SCHEMA,EVALUATION_SCHEMA].includes(o.schema)&&Object.hasOwn(o.source,'reviewedProgram'))?await Reviewed.verifyMappingProof({proof:o.source.reviewedProgram,originalCard:parent,inputVersion:o.source.receipt.inputVersion},crypto):null;unchanged();ensure(!reviewed||reviewed.originalProposalId===o.parentProposalId,'The reviewed mapping identifies another parent.');
  const before=reviewed?reviewed.mapped.plan:F.compile(member?member.card:parent),after=F.compile(child);ensure(!before.reason&&!after.reason&&!before.state&&!after.state&&same(parent.outcome,child.outcome)&&before.inputVersion===after.inputVersion&&before.inputVersion===o.source.receipt.inputVersion&&(evaluation||same(before.criterion,after.criterion)),'The variation changed its aim, edition or evaluation.');
  const validPages=pages=>Array.isArray(pages)&&pages.length>0&&pages.length<=75&&new Set(pages).size===pages.length&&pages.every(p=>typeof p==='string'&&/^lp[12]-\d{2}$/.test(p)&&Number(p.slice(4))<=(p[2]==='1'?16:57));
  ensure(validPages(before.pages)&&validPages(after.pages)&&before.steps.length<=8&&after.steps.length<=8,'The retained calculation exceeds its supported scope.');
  ensure(Array.isArray(after.pages)&&after.pages.length>0&&new Set(after.pages).size===after.pages.length&&after.pages.every(p=>before.pages.includes(p)),'The variation extends beyond its parent scope.');
  ensure(![QUESTION_SCHEMA,EVALUATION_SCHEMA].includes(o.schema)||same(after.pages,before.pages),'A complete-question variation must keep every originally declared page.');
  let text;
  if(evaluation){
   ensure(parent.outcome.status==='specified'&&parent.outcome.value.outcomeId==='decipher'&&before.criterion.kind==='measurement'&&before.steps.length>0&&same(before.steps,after.steps),'An evaluation follow-up needs unchanged output-producing steps and a deciphering question.');
   const expected=JSON.parse(E.stable(reviewed?reviewed.mapped.card:parent)),choice=C.EVALUATION_CHOICES.find(item=>item.id===selection.value);expected.rules.evaluation={status:'specified',value:choice.value};ensure(same(expected,child),'The evaluation follow-up changed more than its maintained check.');
   text=selection.value==='language-samples'?{label:'Compare the output with language samples',description:'Keep the same calculation and pages; compare rune patterns with eight fixed language samples. Similarity does not establish a decryption.'}:{label:'Check for the decoded Warning opening',description:'Keep the same calculation and pages; compare the first 12 runes with the decoded Warning opening. This checks page starts only.'};
  }else {ensure(same(change(before.steps,selection),after.steps),'The variation changed more than the selected step parameter.');text=wording(before.steps[selection.step],selection);}
  const proposalId=direction==='parents'?o.parentProposalId:o.childProposalId;unchanged();
  return freeze({id:value.id,createdAt:value.createdAt,direction,proposalId,href:'run.html#idea='+proposalId,...text,sourceHref});
 }
 const api={SCHEMA,MAPPED_SCHEMA,QUESTION_SCHEMA,EVALUATION_SCHEMA,validate};if(node)module.exports=api;else root.QuestionVariationLinks=api;
})(typeof globalThis!=='undefined'?globalThis:this);
