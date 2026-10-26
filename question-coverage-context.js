/* Bind a saved-work request to its original question. No result authority or I/O. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,Context=node?require('./task-question-context.js'):root.TaskQuestionContext;
 const IDEA=/^p_[a-f0-9]{64}$/,ALPHABET_SHA256='06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f',same=(a,b)=>E.stable(a)===E.stable(b),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),ensure=(v,m)=>{if(!v)throw Error(m);},capture=v=>J.capture(v,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 async function hash(v,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function canonical(card){
  const text=E.stable(card),bytes=new TextEncoder().encode(text);ensure(bytes.length<=H.MAX_BYTES,'The original question exceeds its card limit.');let binary='';for(const b of bytes)binary+=String.fromCharCode(b);
  const draft=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft,checked=H.cardData(C.confirm(draft,{id:'question-coverage-context',at:'2000-01-01T00:00:00.000Z'}));ensure(same(checked,card),'Use the unchanged canonical original question.');return checked;
 }
 async function verify(input,crypto=root.crypto){
  const value=capture(input),mapped=!!value&&Object.hasOwn(value,'reviewedProgram'),unchanged=()=>ensure(same(capture(input),value),'The question coverage request changed during verification.');
  ensure(exact(value,['proposalId','card','coverage','bundle',...(mapped?['reviewedProgram']:[])])&&typeof value.proposalId==='string'&&IDEA.test(value.proposalId)&&crypto?.subtle,'Use an exact original question, coverage request and official input bundle.');
  const card=canonical(value.card),coverage=value.coverage,task=coverage?.requestedTask;
  ensure(coverage&&typeof coverage==='object'&&!Array.isArray(coverage)&&task&&['raw','reviewed'].includes(coverage.inputVersion),'The saved-work request has no exact task or input edition.');
  ensure('p_'+await hash(C.serialize(card),crypto)===value.proposalId,'The saved-work request identifies another original question.');unchanged();
  ensure(await hash(task.alphabet,crypto)===ALPHABET_SHA256,'The request must use the canonical GP29 alphabet.');unchanged();
  const projection={id:task.taskId,plan:task,proposalId:value.proposalId,card,inputVersion:coverage.inputVersion,parentTaskId:null,linkedProposalId:value.proposalId,linkedInputVersion:coverage.inputVersion,linkedParentTaskId:null,...(mapped?{reviewedProgram:value.reviewedProgram}:{})};
  const token=await Context.verify({taskId:task.taskId,proposalId:value.proposalId,projection,bundle:value.bundle},crypto);unchanged();const bound=Context.inspect(token);
  ensure(bound.comparable,'The saved-work request is not an exact supported program of this original question.');
  // Task context deliberately permits subsets. A question overview must retain
  // every declared page, even if one saved receipt covers only a smaller scope.
  ensure(same(task.pages.map(page=>page.id),bound.declaredPages),'The saved-work request must cover the complete original scope in its declared order.');
  return freeze({proposalId:value.proposalId,card,requestedTask:task,inputVersion:coverage.inputVersion,declaredPages:bound.declaredPages,...(mapped?{reviewedProgram:bound.reviewedProgram}:{})});
 }
 const api={verify};if(node)module.exports=api;else root.QuestionCoverageContext=api;
})(typeof globalThis!=='undefined'?globalThis:this);
