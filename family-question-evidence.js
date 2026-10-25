/* Verified evidence for one finite exact-prefix question; no lookup or verdict by flags. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,F=node?require('./research-family.js'):root.ResearchFamily,Evidence=node?require('./computation-evidence.js'):root.ComputationEvidence;
 const proofs=new WeakSet(),HEX=/^[a-f0-9]{64}$/,clone=v=>JSON.parse(E.stable(v));
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 function freeze(v){if(v&&typeof v==='object'){for(const child of Object.values(v))freeze(child);Object.freeze(v);}return v;}
 function unpack(wire){
  if(!exact(wire,['familyId','revision','sources','cases','lookupComplete'])||wire.familyId!=='deor-feedback-v1'||!HEX.test(wire.revision)||typeof wire.lookupComplete!=='boolean'||!Array.isArray(wire.sources)||wire.sources.length>990||!Array.isArray(wire.cases)||wire.cases.length>990||new TextEncoder().encode(E.stable(wire)).length>2*1024*1024)throw Error('The finite question wire evidence is malformed or exceeds its bound.');
  const value=clone(wire),identities=new Set(),referenced=new Set(),caseIds=new Set();
  for(const source of value.sources){
   if(!exact(source,['task','inputVersion','run'])||source.inputVersion!=='raw'||!HEX.test(source.task?.taskId)||!exact(source.run,['id','createdAt','result'])||!HEX.test(source.run.id)||typeof source.run.createdAt!=='string'||!Number.isFinite(Date.parse(source.run.createdAt)))throw Error('The finite question wire source is malformed.');
   const identity=E.stable([source.task.taskId,source.run.id,source.run.createdAt]);if(identities.has(identity))throw Error('The finite question wire repeats an original source.');identities.add(identity);
  }
  const sources=value.cases.map(ref=>{
   if(!exact(ref,['caseId','sourceIndex'])||typeof ref.caseId!=='string'||ref.caseId.length>200||!/^[a-z0-9][a-z0-9-]*$/.test(ref.caseId)||caseIds.has(ref.caseId)||!Number.isInteger(ref.sourceIndex)||ref.sourceIndex<0||ref.sourceIndex>=value.sources.length)throw Error('The finite question wire case reference is malformed.');
   caseIds.add(ref.caseId);referenced.add(ref.sourceIndex);return {familyId:value.familyId,revision:value.revision,caseId:ref.caseId,source:value.sources[ref.sourceIndex]};
  });
  if(referenced.size!==value.sources.length)throw Error('The finite question wire has an unreferenced source.');
  return {familyId:value.familyId,revision:value.revision,sources,lookupComplete:value.lookupComplete};
 }
 async function hash(v,cryptoAPI,raw=false){return Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(raw?v:E.stable(v)))),b=>b.toString(16).padStart(2,'0')).join('');}
 async function summarize(options,cryptoAPI=root.crypto){
  if(!options||typeof options!=='object'||Array.isArray(options)||Object.keys(options).some(k=>!['snapshot','bundle','sources','lookupComplete'].includes(k))||!['snapshot','bundle','sources'].every(k=>Object.hasOwn(options,k))||Object.hasOwn(options,'lookupComplete')&&typeof options.lookupComplete!=='boolean')throw Error('Finite question evidence needs exact inputs and a lookup status.');
  const {snapshot,bundle,sources,lookupComplete=true}=clone(options);
  if(!Array.isArray(sources)||sources.length>990||E.stable(sources).length>16000000)throw Error('Finite question evidence exceeds its bound.');
  const preparer=await F.createPreparer(bundle,cryptoAPI),view=preparer.snapshot;
  if(E.stable(snapshot)!==E.stable(view))throw Error('The finite question snapshot differs from the exact current family inputs.');
  const all=F.caseIds(view),allowed=new Set(all),index=new Map(bundle.alphabet.map((entry,i)=>[entry.rune,i])),templates=new Map(),exclusions=[];
  // Prepare one representative per configuration, not 990 target executions.
  // Invert its first equation independently of the family exclusion routine.
  // All modes/resets consume the same seed at the first rune of a page.
  for(const config of view.configurations){
   const task=(await preparer.prepare([config.id+'--'+view.pages[0].id])).cases[0].task;
   templates.set(config.id,task);
   const step=task.steps[0],expectedIndex=task.criterion.values[0],keyIndex=step.key[0];
   const requiredInput=((expectedIndex+(step.direction==='subtract'?keyIndex:-keyIndex))%29+29)%29;
   for(const page of view.pages){
    const observedInput=index.get(Array.from(page.text).find(ch=>index.has(ch)));
    if(observedInput!==requiredInput)exclusions.push({caseId:config.id+'--'+page.id,rule:'first-rune',requiredInput,observedInput,keyIndex,expectedIndex,direction:step.direction});
   }
  }
  exclusions.sort((a,b)=>a.caseId.localeCompare(b.caseId));
  const excluded=new Set(exclusions.map(e=>e.caseId)),seen=new Set(),sourceCache=new Map(),evidence=[],found=[],verified=[];
  const sourceCaseIds=sources.map(source=>source?.caseId);
  if(sourceCaseIds.some(id=>typeof id!=='string'||!allowed.has(id))||new Set(sourceCaseIds).size!==sourceCaseIds.length)throw Error('Finite evidence cases must be distinct members of this question.');
  const expected=new Map();
  for(let i=0;i<sourceCaseIds.length;i+=12){const plan=await preparer.prepare(sourceCaseIds.slice(i,i+12));for(const item of plan.cases)expected.set(item.id,item.task);}
  for(const receipt of sources){
   const direct=exact(receipt,['familyId','revision','caseId','task','result','resultId','verifiedAt']),shared=exact(receipt,['familyId','revision','caseId','source']);
   if(!direct&&!shared||receipt.familyId!==view.id||receipt.revision!==view.revision)throw Error('The finite receipt belongs to another family revision or has unsupported proof fields.');
   let source;
   if(direct){
    if(E.stable(receipt.task)!==E.stable(expected.get(receipt.caseId)))throw Error('The saved family task differs from this exact case and page bytes.');
    source={task:receipt.task,inputVersion:'raw',run:{id:receipt.resultId,createdAt:receipt.verifiedAt,result:receipt.result}};
   }else source=receipt.source;
   if(!exact(source,['task','inputVersion','run'])||source.inputVersion!=='raw'||!exact(source.run,['id','createdAt','result'])||!HEX.test(source.run.id)||typeof source.run.createdAt!=='string'||!Number.isFinite(Date.parse(source.run.createdAt)))throw Error('The finite source receipt is malformed.');
   const signature=E.stable(source),prior=sourceCache.get(source.task?.taskId);
   if(prior&&prior.signature!==signature)throw Error('Conflicting source receipts name the same task.');
   let result=prior?.result;
   if(!result){
    await E.checkIdentity(source.task,cryptoAPI);
    if(await hash(source.run.result,cryptoAPI)!==source.run.id)throw Error('The finite result hash changed.');
    result=await E.verify(source.task,source.run.result,cryptoAPI);
    sourceCache.set(source.task.taskId,{signature,result});
   }
   const task=expected.get(receipt.caseId),comparison=await Evidence.compare(task,'raw',[source],cryptoAPI);
   if(comparison.remainingPages.length||comparison.coveredPages.length!==1)throw Error('The source does not prove this exact finite case.');
   const match=result.matches.find(item=>item.page===task.pages[0].id);
   if(!match||typeof match.matched!=='boolean')throw Error('The finite source has no exact opening result.');
   if(match.matched&&excluded.has(receipt.caseId))throw Error('The full-prefix result contradicts a necessary first-rune condition.');
   seen.add(receipt.caseId);verified.push(receipt.caseId);if(match.matched)found.push(receipt.caseId);
   evidence.push({caseId:receipt.caseId,taskId:source.task.taskId,resultId:source.run.id,createdAt:source.run.createdAt});
  }
  const template=templates.values().next().value,criterion=clone(template.criterion),key=template.steps[0].key.slice(),missing=all.filter(id=>!excluded.has(id)&&!seen.has(id));
  const pages=[];for(const page of view.pages)pages.push({id:page.id,sha256:await hash(page.text,cryptoAPI,true)});
  const proof=freeze({familyId:view.id,revision:view.revision,inputVersion:'raw',engine:template.engine,criterion,parameters:{key,values:criterion.values.slice(),modes:[...new Set(view.configurations.map(c=>c.mode))],directions:[...new Set(view.configurations.map(c=>c.direction))],resets:[...new Set(view.configurations.map(c=>c.reset))]},alphabetSha256:await hash(bundle.alphabet,cryptoAPI),pages,totalCases:all.length,excludedCaseIds:all.filter(id=>excluded.has(id)),verifiedCaseIds:verified.sort(),foundCaseIds:found.sort(),missingCaseIds:missing,complete:missing.length===0,lookupComplete,evidence:evidence.sort((a,b)=>a.caseId.localeCompare(b.caseId)),exclusions});
  proofs.add(proof);return proof;
 }
 function inspect(proof){if(!proof||!proofs.has(proof))throw Error('Finite question evidence must be independently verified before use.');return proof;}
 const api={summarize,inspect,unpack};if(node)module.exports=api;else root.FamilyQuestionEvidence=api;
})(typeof globalThis!=='undefined'?globalThis:this);
