import {checkedOrdinaryOpeningEvidence,discoverOrdinaryOpeningEvidence,checkedOrdinaryOutputAssessment,discoverOrdinaryOutputAssessment,combineOrdinaryOpeningCoverage,strictOpeningMatchingPages} from './ordinary-opening-evidence.mjs';
import {inspectPinnedQuestionRequestContext,assertPinnedQuestionContextDependencies} from './pinned-question-request-context.mjs';
import {assertPinnedQuestionTaskUncovered} from './factored-selected-evidence.mjs';
import {checkedPinnedQuestionMember} from './pinned-question-admission.mjs';
import {checkedPinnedDomainMember} from './pinned-domain-admission.mjs';
import {checkedAuthoredFiniteMember} from './authored-finite-origin.mjs';
import {checkedOrdinaryPrefixEvidence,discoverOrdinaryPrefixEvidence,combineOrdinaryPrefixCoverage} from './ordinary-prefix-evidence.mjs';
/* Immutable server-issued admission proof. No generation, inference or task writes. */
import C from '../../claim-specification.js';
import Share from '../../claim-share.js';
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import Variants from '../../task-variants.js';
import {validateCard} from './idea-relations.mjs';
import Evidence from '../../computation-evidence.js';
import {checkedEvidence,findEvidence} from './task-evidence.mjs';
import Settings from '../../finite-settings.js';
import Policy from '../../finite-question-policy.js';
import Compiler from '../../fixed-plan-compiler.js';
import {storageLimits as checkedStorageLimits} from './storage-limits.mjs';
import {checkedRecordRemainder,strictPrefixMatch} from './authored-prefix-remainder.mjs';

const HEX=/^[a-f0-9]{64}$/,PREP=/^prep_[a-f0-9]{64}$/,PROPOSAL=/^p_[a-f0-9]{64}$/;
const exact=(o,ks)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===ks.length&&ks.every(k=>Object.hasOwn(o,k));
const require=(ok,message)=>{if(!ok)throw Error(message);};
const sha=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
function plain(value,depth=0,budget={nodes:0}){
 require(depth<=20&&++budget.nodes<=30000,'Prepared basis is too complex');
 if(value===null||typeof value==='boolean'||typeof value==='string')return value;
 if(typeof value==='number'&&Number.isFinite(value))return value;
 if(Array.isArray(value)){
  const out=[];for(let n=0;n<value.length;n++){const d=Object.getOwnPropertyDescriptor(value,String(n));require(d&&Object.hasOwn(d,'value'),'Prepared arrays must contain data fields');out.push(plain(d.value,depth+1,budget));}return out;
 }
 require(value&&typeof value==='object'&&[Object.prototype,null].includes(Object.getPrototypeOf(value)),'Prepared basis must be JSON data');
 const out={};for(const key of Object.keys(value)){
  require(!['__proto__','constructor','prototype'].includes(key),'Unsafe prepared basis key');
  const d=Object.getOwnPropertyDescriptor(value,key);require(Object.hasOwn(d,'value'),'Prepared basis must contain data fields');
  out[key]=plain(d.value,depth+1,budget);
 }return out;
}
function json(value,max){const copied=plain(value),text=E.stable(copied);require(new TextEncoder().encode(text).length<=max,'Prepared metadata exceeds its byte limit');return {value:copied,text};}
function query(db,sql,...args){require(typeof db?.prepare==='function','Prepared-plan storage unavailable');return db.prepare(sql).bind(...args).first();}
function projection(row){return {version:1,id:row.id,proposalId:row.proposal_id,cardHash:row.card_hash,
 taskId:row.task_id,taskHash:row.task_hash,inputVersion:row.input_version,parentTaskId:row.parent_task_id,
 authority:row.authority,controlsHash:row.controls_hash};}
function identity(base,authority,basisHash){return {...base,authority,basisHash};}
async function binding({proposalId,card,task,inputVersion,parentTaskId,controls}){
 require(typeof proposalId==='string'&&PROPOSAL.test(proposalId)&&['raw','reviewed'].includes(inputVersion)
  &&(parentTaskId===null||typeof parentTaskId==='string'&&HEX.test(parentTaskId)),'Invalid prepared plan binding');
 const canonical=validateCard(card),cardHash=await sha(C.serialize(canonical));
 // Structural reading deliberately accepts legacy incomplete cards. Issuance
 // and authorization retain their separate explicit meaning-review gate.
 let binary='';for(const byte of new TextEncoder().encode(C.serialize(canonical)))binary+=String.fromCharCode(byte);
 const review=Share.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft;
 require(C.questions(review).length===0,'Review consequential questions before preparing an experiment');
 require(proposalId==='p_'+cardHash,'Prepared proposal does not match the canonical card');
 E.validateTask(task);const frozen=JSON.parse(E.stable(task));await E.checkIdentity(frozen);
 const suite=json(controls,2000000).value;await Controls.validate(suite,frozen);
 const base={version:1,proposalId,cardHash,taskId:frozen.taskId,taskHash:await sha(E.stable(frozen)),
  inputVersion,parentTaskId,controlsHash:await sha(E.stable(suite))};
 return {base,bindingHash:await sha(E.stable(base)),card:canonical,task:frozen};
}
async function proposal(db,bound){
 const row=await query(db,'SELECT card_hash,card_json FROM proposals WHERE id=?',bound.base.proposalId);
 if(!row)return false;
 try{return row.card_hash===bound.base.cardHash&&C.serialize(validateCard(row.card_json))===C.serialize(bound.card);}catch{return false;}
}
async function basisFor(db,value,bound,authority,fresh=false,fetcher=globalThis.fetch,loadAuthoredSource,loadPinnedDomain,loadPinnedBundle,pinnedQuestionContext,signal){
 const data=json(value,128000),basis=data.value;
 const contextDeps=pinnedQuestionContext===undefined?null:assertPinnedQuestionContextDependencies(pinnedQuestionContext,{db,fetcher,crypto:globalThis.crypto});
 if(contextDeps)require(authority==='idea'&&basis.kind==='pinned-question-member-v1'&&!loadPinnedDomain&&!loadPinnedBundle,'A request context only admits its original pinned question.');
 if(authority==='idea'){
  if(basis.kind==='pinned-question-member-v1'){require(bound.base.parentTaskId===null,'Pinned question members preserve their complete original question');await checkedPinnedQuestionMember({basis,card:bound.card,task:bound.task,inputVersion:bound.base.inputVersion,loadDomain:loadPinnedDomain,loadBundle:loadPinnedBundle,fetcher,...(contextDeps?{requestContext:pinnedQuestionContext,signal:contextDeps.signal}:{})});require(basis.parentProposalId===bound.base.proposalId,'The complete parent question identity changed');if(fresh)await assertPinnedQuestionTaskUncovered({db,task:bound.task,inputVersion:bound.base.inputVersion,fetcher,...(contextDeps?{signal:contextDeps.signal}:{})});return {text:data.text,hash:await sha(data.text)};}
  if(basis.kind==='pinned-domain-member-v1'){require(bound.base.parentTaskId===null,'Pinned members preserve an independent parent-domain identity');await checkedPinnedDomainMember({basis,card:bound.card,task:bound.task,inputVersion:bound.base.inputVersion,loadDomain:loadPinnedDomain,loadBundle:loadPinnedBundle,fetcher});return {text:data.text,hash:await sha(data.text)};}
  if(basis.kind==='authored-finite-member-v1'){await checkedAuthoredFiniteMember({basis,card:bound.card,task:bound.task,inputVersion:bound.base.inputVersion,fetcher,loadAuthoredSource});await basisFor(db,basis.memberBasis,bound,authority,fresh,fetcher,loadAuthoredSource);return {text:data.text,hash:await sha(data.text)};}
  if(['record-derived-prefix-remainder-v1','record-strict-evidence-remainder-v1'].includes(basis.kind)){
   const reviewed=await checkedRecordRemainder({basis,card:bound.card,task:bound.task,inputVersion:bound.base.inputVersion,fetcher});
   if(basis.kind==='record-strict-evidence-remainder-v1'){
    require(bound.base.parentTaskId===null&&typeof basis.requestedTaskId==='string'&&HEX.test(basis.requestedTaskId)&&Array.isArray(basis.strictEvidence)&&basis.strictEvidence.length<=75,'Invalid strict authored remainder binding');
    const row=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
    require(row&&row.input_version===bound.base.inputVersion,'Requested authored scope is unavailable');const requested=JSON.parse(row.requested_task_json);await E.checkIdentity(requested);
    require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===row.requested_task_hash&&['engine','alphabet','steps','criterion','pages'].every(key=>E.stable(requested[key])===E.stable(reviewed.task[key])),'Requested authored scope changed');
    const pinned=await checkedEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.strictEvidence});
    require(pinned.remainingPages.length>0&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(page=>pinned.remainingPages.includes(page.id))),'Authored strict remainder changed the exact unchecked pages');
    if(fresh){const current=await findEvidence({db,task:requested,inputVersion:row.input_version});require(!current.truncated&&E.stable(current.remainingPages)===E.stable(pinned.remainingPages),'Saved work changed; review the authored remaining pages again');}
    return {text:data.text,hash:await sha(data.text)};
   }
   await basisFor(db,basis.remainderBasis,bound,authority,fresh,fetcher);
   const requestedRow=await query(db,'SELECT requested_task_json FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.remainderBasis.requestedTaskId);
   require(!await strictPrefixMatch({db,task:JSON.parse(requestedRow.requested_task_json),inputVersion:bound.base.inputVersion,evidence:basis.remainderBasis.strictEvidence}),'The authored opening is already found');
   return {text:data.text,hash:await sha(data.text)};
  }
  if(basis.kind==='factored-page-group-v1'){
   require(exact(basis,['kind','domainId','settings','caseIds'])&&typeof basis.domainId==='string'&&HEX.test(basis.domainId)&&Array.isArray(basis.caseIds)&&basis.caseIds.length>=1&&basis.caseIds.length<=75&&basis.caseIds.every(id=>typeof id==='string'&&HEX.test(id))&&new Set(basis.caseIds).size===basis.caseIds.length&&bound.base.parentTaskId===null,'Invalid reviewed page-group basis');
   const member=Settings.factored.member(bound.card,basis.settings),plan=Compiler.compile(member.card),evaluation=bound.card.rules.evaluation.value==='measurement'?{kind:'measurement'}:bound.card.rules.evaluation.value;
   require(!plan.reason&&Array.isArray(plan.steps)&&bound.card.rules.inputVersion.status==='specified'&&bound.card.rules.evaluation.status==='specified','Page groups need the unchanged explicit source and evaluation');Policy.describe(evaluation);
   require(E.stable(basis.settings)===E.stable(member.settings)&&plan.inputVersion===bound.base.inputVersion&&plan.inputVersion===bound.card.rules.inputVersion.value&&E.stable(plan.criterion)===E.stable(evaluation)&&E.stable(bound.task.criterion)===E.stable(plan.criterion)&&E.stable(bound.task.steps)===E.stable(plan.steps)&&E.stable(plan.pages)===E.stable(bound.card.scope.value.pages)&&bound.task.pages.length>=1&&bound.task.pages.length<=75&&bound.task.pages.every(page=>plan.pages.includes(page.id))&&E.stable(bound.task.pages.map(p=>p.id))===E.stable(bound.task.pages.map(p=>p.id).sort())&&new TextEncoder().encode(E.stable(bound.task)).length<=800000,'Page groups changed the declared method, evaluation or exact reviewed pages');
   const described=await Evidence.describe(bound.task,bound.base.inputVersion);require(E.stable(described.pages.map(page=>page.caseId))===E.stable(basis.caseIds),'Page-group cases differ from the whole prepared ordinary task');return {text:data.text,hash:await sha(data.text)};
  }
  if(basis.kind==='finite-settings'||basis.kind==='factored-finite-settings'||basis.kind==='factored-output-settings'||basis.kind==='factored-inspection-settings'){
   require(exact(basis,['kind','settings','caseId'])&&HEX.test(basis.caseId)&&bound.base.parentTaskId===null,'Invalid finite-settings preparation basis');
   const settingsAPI=basis.kind!=='finite-settings'?Settings.factored:Settings;
   const member=settingsAPI.member(bound.card,basis.settings),plan=Compiler.compile(member.card);
   require(!plan.reason&&Array.isArray(plan.steps)&&bound.card.rules.inputVersion.status==='specified'&&['raw','reviewed'].includes(bound.card.rules.inputVersion.value)
    &&bound.card.rules.evaluation.status==='specified'&&(basis.kind==='factored-inspection-settings'?bound.card.rules.evaluation.value==='measurement':basis.kind==='factored-output-settings'?Policy.describe(bound.card.rules.evaluation.value).id==='language-reference-comparison-v1':['exact-prefix','exact-prefix-set'].includes(bound.card.rules.evaluation.value?.kind)),'Finite settings do not compile to the explicit maintained evaluation');
   require(E.stable(basis.settings)===E.stable(member.settings)&&plan.inputVersion===bound.base.inputVersion&&plan.inputVersion===bound.card.rules.inputVersion.value
    &&E.stable(plan.criterion)===E.stable(basis.kind==='factored-inspection-settings'?{kind:'measurement'}:bound.card.rules.evaluation.value)&&E.stable(bound.task.criterion)===E.stable(plan.criterion)&&E.stable(bound.task.steps)===E.stable(plan.steps)
    &&E.stable(plan.pages)===E.stable(bound.card.scope.value.pages)&&bound.task.pages.length===1&&plan.pages.includes(bound.task.pages[0].id),'Finite settings changed the declared parameters, pages or common rules');
   const described=await Evidence.describe(bound.task,bound.base.inputVersion);
   require(described.pages.length===1&&described.pages[0].caseId===basis.caseId,'Finite settings case differs from the exact prepared page and program');
   return {text:data.text,hash:await sha(data.text)};
  }
  const original=['evidence-remainder','ordinary-derived-prefix-remainder-v1','ordinary-derived-openings-remainder-v1','ordinary-derived-assessment-remainder-v1'].includes(basis.kind)?basis.originalBasis:basis;
  require(exact(original,['kind','normalizedCard',...(original?.kind==='mapped-card'?['mapping']:[])])
   &&['compiled-card','mapped-card'].includes(original.kind),'Invalid idea preparation basis');
  const normalized=validateCard(original.normalizedCard);
  if(original.kind==='compiled-card')require(C.serialize(normalized)===C.serialize(bound.card),'Compiled basis changed the original card');
  else require(original.mapping&&typeof original.mapping==='object'&&!Array.isArray(original.mapping),'Mapped basis requires reviewed mapping evidence');
  if(basis.kind==='ordinary-derived-assessment-remainder-v1'){
   require(exact(basis,['kind','originalBasis','requestedTaskId','strictEvidence','derivedEvidence'])&&HEX.test(basis.requestedTaskId)&&original.kind==='compiled-card'&&bound.base.parentTaskId===null&&Array.isArray(basis.strictEvidence)&&Array.isArray(basis.derivedEvidence)&&basis.strictEvidence.length<=75&&basis.derivedEvidence.length<=75&&new Set([...basis.strictEvidence.map(r=>E.stable([r?.taskId,r?.resultId,r?.createdAt])),...basis.derivedEvidence.map(r=>E.stable([r?.origin?.taskId,r?.origin?.resultId,r?.origin?.createdAt]))]).size<=75,'Invalid derived-assessment remainder basis');
   const row=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
   require(row&&row.input_version===bound.base.inputVersion,'Derived assessment request is not associated with this idea');const requested=JSON.parse(row.requested_task_json);await E.checkIdentity(requested);
   require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===row.requested_task_hash,'Derived assessment request changed');
   const plan=Compiler.compile(normalized);require(!plan.reason&&requested.criterion.kind==='language-score'&&plan.inputVersion===row.input_version&&E.stable(plan.pages)===E.stable(requested.pages.map(p=>p.id))&&E.stable(plan.steps)===E.stable(requested.steps)&&E.stable(plan.criterion)===E.stable(requested.criterion),'Derived assessment differs from the original question');
   const strict=await checkedEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.strictEvidence,fetcher,signal}),derived=await checkedOrdinaryOutputAssessment({db,task:requested,inputVersion:row.input_version,evidence:basis.derivedEvidence,fetcher,signal}),covered=new Set([...strict.coveredPages,...derived.coveredPages]),remainingPages=requested.pages.filter(p=>!covered.has(p.id)).map(p=>p.id);
   require(remainingPages.length>0,'An assessment remainder needs unassessed pages');const full=await Evidence.describe(requested,row.input_version),remaining=await Evidence.describe(bound.task,row.input_version);require(full.protocolId===remaining.protocolId&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(p=>remainingPages.includes(p.id))),'Assessment remainder changed its exact pages or criterion');
   if(fresh){const currentStrict=await findEvidence({db,task:requested,inputVersion:row.input_version,fetcher,signal}),currentDerived=await discoverOrdinaryOutputAssessment({db,task:requested,inputVersion:row.input_version,fetcher,signal}),currentCovered=new Set([...currentStrict.coveredPages,...currentDerived.wire.summary.coveredPages]),currentRemaining=requested.pages.filter(p=>!currentCovered.has(p.id)).map(p=>p.id);require(!(currentStrict.truncated||!currentDerived.wire.lookupComplete)&&E.stable(currentRemaining)===E.stable(remainingPages),'Saved original output changed; review the unassessed pages again');}
  }
  if(basis.kind==='ordinary-derived-openings-remainder-v1'){
   require(exact(basis,['kind','originalBasis','requestedTaskId','strictEvidence','derivedEvidence'])&&HEX.test(basis.requestedTaskId)&&original.kind==='compiled-card'&&bound.base.parentTaskId===null&&Array.isArray(basis.strictEvidence)&&Array.isArray(basis.derivedEvidence)&&basis.strictEvidence.length<=75&&basis.derivedEvidence.length<=75&&new Set([...basis.strictEvidence.map(r=>E.stable([r?.taskId,r?.resultId,r?.createdAt])),...basis.derivedEvidence.map(r=>E.stable([r?.origin?.taskId,r?.origin?.resultId,r?.origin?.createdAt]))]).size<=75,'Invalid derived-opening remainder basis');
   const row=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
   require(row&&row.input_version===bound.base.inputVersion,'Derived opening request is not associated with this idea');const requested=JSON.parse(row.requested_task_json);await E.checkIdentity(requested);
   require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===row.requested_task_hash,'Derived opening request changed');
   const plan=Compiler.compile(normalized);require(!plan.reason&&['exact-prefix','exact-prefix-set'].includes(requested.criterion.kind)&&plan.inputVersion===row.input_version&&E.stable(plan.pages)===E.stable(requested.pages.map(p=>p.id))&&E.stable(plan.steps)===E.stable(requested.steps)&&E.stable(plan.criterion)===E.stable(requested.criterion),'Derived opening differs from the original question');
   const strictOpenings=await strictOpeningMatchingPages({db,task:requested,inputVersion:row.input_version,evidence:basis.strictEvidence,fetcher}),strict=strictOpenings.comparison,derived=await checkedOrdinaryOpeningEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.derivedEvidence,fetcher}),union=combineOrdinaryOpeningCoverage(requested,strict,derived);
   require(union.remainingPages.length>0&&!union.matchingPages.length&&!strictOpenings.matchingPages.length,'An opening remainder needs unanswered pages');const full=await Evidence.describe(requested,row.input_version),remaining=await Evidence.describe(bound.task,row.input_version);require(full.protocolId===remaining.protocolId&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(p=>union.remainingPages.includes(p.id))),'Opening remainder changed its exact pages or evaluation');
   if(fresh){const currentStrict=await findEvidence({db,task:requested,inputVersion:row.input_version,fetcher}),currentDecisions=await strictOpeningMatchingPages({db,task:requested,inputVersion:row.input_version,evidence:currentStrict.evidence,fetcher}),currentDerived=await discoverOrdinaryOpeningEvidence({db,task:requested,inputVersion:row.input_version,fetcher}),current=combineOrdinaryOpeningCoverage(requested,currentStrict,currentDerived.wire.summary);require(!(currentStrict.truncated||!currentDerived.wire.lookupComplete)&&!current.matchingPages.length&&!currentDecisions.matchingPages.length&&E.stable(current.remainingPages)===E.stable(union.remainingPages),'Saved original output changed; review the open pages again');}
  }
  if(basis.kind==='ordinary-derived-prefix-remainder-v1'){
   require(exact(basis,['kind','originalBasis','requestedTaskId','strictEvidence','derivedEvidence'])&&HEX.test(basis.requestedTaskId)&&original.kind==='compiled-card'&&bound.base.parentTaskId===null&&Array.isArray(basis.strictEvidence)&&Array.isArray(basis.derivedEvidence)&&basis.strictEvidence.length<=75&&basis.derivedEvidence.length<=75&&new Set([...basis.strictEvidence,...basis.derivedEvidence].map(ref=>E.stable([ref?.taskId,ref?.resultId,ref?.createdAt]))).size<=75,'Invalid derived-prefix remainder basis');
   const row=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
   require(row&&row.input_version===bound.base.inputVersion,'Derived prefix request is not associated with this idea');const requested=JSON.parse(row.requested_task_json);await E.checkIdentity(requested);
   require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===row.requested_task_hash,'Derived prefix request changed');
   const plan=Compiler.compile(normalized);require(!plan.reason&&requested.criterion.kind==='exact-prefix'&&plan.inputVersion===row.input_version&&E.stable(plan.pages)===E.stable(requested.pages.map(p=>p.id))&&E.stable(plan.steps)===E.stable(requested.steps)&&E.stable(plan.criterion)===E.stable(requested.criterion),'Derived request differs from the original declared question');
   const strict=await checkedEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.strictEvidence}),derived=await checkedOrdinaryPrefixEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.derivedEvidence}),union=combineOrdinaryPrefixCoverage(requested,strict,derived);
   require(union.remainingPages.length>0&&!union.matchingPages.length,'Derived remainder must retain unanswered pages');
   const full=await Evidence.describe(requested,row.input_version),remaining=await Evidence.describe(bound.task,row.input_version);require(full.protocolId===remaining.protocolId&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(p=>union.remainingPages.includes(p.id))),'Derived remainder changed its exact open pages or evaluation');
   if(fresh){const currentStrict=await findEvidence({db,task:requested,inputVersion:row.input_version}),currentDerived=await discoverOrdinaryPrefixEvidence({db,task:requested,inputVersion:row.input_version}),current=combineOrdinaryPrefixCoverage(requested,currentStrict,currentDerived.wire.summary);require(!(currentStrict.truncated||!currentDerived.wire.lookupComplete)&&!current.matchingPages.length&&E.stable(current.remainingPages)===E.stable(union.remainingPages),'Saved evidence changed; review the remaining pages again');}
  }
  if(basis.kind==='evidence-remainder'){
   require(exact(basis,['kind','originalBasis','requestedTaskId','evidence'])&&HEX.test(basis.requestedTaskId),'Invalid evidence remainder basis');
   const row=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
   require(row&&row.input_version===bound.base.inputVersion,'Requested scope is not associated with this idea');
   const requested=JSON.parse(row.requested_task_json);await E.checkIdentity(requested);
   require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===row.requested_task_hash,'Requested scope differs from its immutable inputs');
   const comparison=await checkedEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.evidence});
   require(comparison.coveredPages.length>0&&comparison.remainingPages.length>0,'A remainder needs both covered and open pages');
   const full=await Evidence.describe(requested,row.input_version),remaining=await Evidence.describe(bound.task,row.input_version);
   require(full.protocolId===remaining.protocolId&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(page=>comparison.remainingPages.includes(page.id))),'Remainder changed the method, criterion or exact open pages');
  }
 }else if(authority==='word-boundaries'){
  require(exact(basis,['kind','parentTaskId','parentTaskHash','from','to',...(Object.hasOwn(basis,'requestedTaskId')||Object.hasOwn(basis,'evidence')?['requestedTaskId','evidence']:[])])&&basis.kind==='word-boundaries'
   &&basis.parentTaskId===bound.base.parentTaskId&&typeof basis.parentTaskHash==='string'&&HEX.test(basis.parentTaskHash),
   'Invalid word-boundary preparation basis');
  const row=await query(db,'SELECT t.task_hash,t.task_json FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id WHERE t.id=? AND links.proposal_id=?',basis.parentTaskId,bound.base.proposalId);
  require(row?.task_hash===basis.parentTaskHash,'Word-boundary parent is not associated with this idea');
  const parent=JSON.parse(row.task_json);await E.checkIdentity(parent);
  require(parent.taskId===basis.parentTaskId&&await sha(E.stable(parent))===row.task_hash,'Stored word-boundary parent differs from its hash');
  const variant=Variants.inspect(parent);
  require(variant&&variant.from===basis.from&&variant.to===basis.to,'Word-boundary basis differs from the fixed comparison');
  if(Object.hasOwn(basis,'requestedTaskId')){
   require(HEX.test(basis.requestedTaskId),'Invalid word-boundary evidence request');
   const saved=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
   require(saved&&saved.input_version===bound.base.inputVersion,'Word-boundary request is not associated with this idea');
   const requested=JSON.parse(saved.requested_task_json);await E.checkIdentity(requested);
   require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===saved.requested_task_hash,'Word-boundary request differs from its immutable inputs');
   await Variants.validate(parent,requested);
   const comparison=await checkedEvidence({db,task:requested,inputVersion:bound.base.inputVersion,evidence:basis.evidence});
   require(comparison.coveredPages.length>0&&comparison.remainingPages.length>0,'A boundary remainder needs both covered and open pages');
   const full=await Evidence.describe(requested,bound.base.inputVersion),remaining=await Evidence.describe(bound.task,bound.base.inputVersion);
   require(full.protocolId===remaining.protocolId&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(page=>comparison.remainingPages.includes(page.id))),'Word-boundary evidence changed the method, grouping or exact remaining pages');
  }else await Variants.validate(parent,bound.task);
 }else{
  require(authority==='remaining-lp2'&&exact(basis,['kind','parentTaskId','parentTaskHash','protocolHash','coveredPages','remainingPages',...(Object.hasOwn(basis,'requestedTaskId')||Object.hasOwn(basis,'evidence')?['requestedTaskId','evidence']:[])])
   &&basis.kind==='remaining-lp2'&&basis.parentTaskId===bound.base.parentTaskId&&typeof basis.parentTaskHash==='string'&&HEX.test(basis.parentTaskHash),
   'Invalid remaining-scope preparation basis');
  require(typeof basis.protocolHash==='string'&&basis.protocolHash===await sha(E.stable({steps:bound.task.steps,criterion:bound.task.criterion,alphabet:bound.task.alphabet})),
   'Extension protocol differs from its preparation basis');
  const covered=C.pages(basis.coveredPages),remaining=C.pages(basis.remainingPages);
  require(E.stable(covered)===E.stable(basis.coveredPages)&&E.stable(remaining)===E.stable(basis.remainingPages)
   &&remaining.length>0&&remaining.every(p=>/^lp2-(?:[0-4][0-9]|5[0-5])$/.test(p)&&!covered.includes(p))
   &&E.stable(remaining)===E.stable(bound.task.pages.map(p=>p.id)),'Invalid exact remaining-page scope');
  const parent=await query(db,'SELECT t.task_hash FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id WHERE t.id=? AND links.proposal_id=?',basis.parentTaskId,bound.base.proposalId);
  require(parent?.task_hash===basis.parentTaskHash,'Extension parent is not associated with this idea');
  if(Object.hasOwn(basis,'requestedTaskId')){
   require(HEX.test(basis.requestedTaskId),'Invalid extension evidence request');
   const row=await query(db,'SELECT requested_task_json,requested_task_hash,input_version FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?',bound.base.proposalId,basis.requestedTaskId);
   require(row&&row.input_version===bound.base.inputVersion,'Extension request is not associated with this idea');
   const requested=JSON.parse(row.requested_task_json);await E.checkIdentity(requested);
   require(requested.taskId===basis.requestedTaskId&&await sha(E.stable(requested))===row.requested_task_hash,'Extension request differs from its immutable inputs');
   const comparison=await checkedEvidence({db,task:requested,inputVersion:row.input_version,evidence:basis.evidence});
   require(comparison.coveredPages.length>0&&comparison.remainingPages.length>0&&comparison.coveredPages.every(id=>covered.includes(id)),'Extension evidence does not support its covered pages');
   const full=await Evidence.describe(requested,row.input_version),open=await Evidence.describe(bound.task,row.input_version);
   require(full.protocolId===open.protocolId&&E.stable(bound.task.pages)===E.stable(requested.pages.filter(page=>comparison.remainingPages.includes(page.id))),'Extension evidence changed the method, criterion or exact open pages');
  }

 }
 return {text:data.text,hash:await sha(data.text)};
}
async function checked(row,bound){
 if(!row||row.binding_hash!==bound.bindingHash)return null;
 const p=projection(row);
 if(!['idea','remaining-lp2','word-boundaries'].includes(row.authority)||!PREP.test(row.id)||typeof row.basis_json!=='string'||row.basis_json.length>128000)return null;
 for(const key of Object.keys(bound.base))if(p[key]!==bound.base[key])return null;
 try{
  const basis=JSON.parse(row.basis_json);if(E.stable(basis)!==row.basis_json||await sha(row.basis_json)!==row.basis_hash)return null;
  if(row.id!=='prep_'+await sha(E.stable(identity(bound.base,row.authority,row.basis_hash))))return null;
 }catch{return null;}
 return p;
}
export async function issue({db,proposalId,card,task,inputVersion,parentTaskId,controls,authority,basis,createdAt=new Date().toISOString(),storageLimits,fetcher=globalThis.fetch,loadAuthoredSource,loadPinnedDomain,loadPinnedBundle,pinnedQuestionContext,signal}){
 const liveContext=()=>{require(!signal?.aborted,'Preparation cancelled');if(pinnedQuestionContext!==undefined){inspectPinnedQuestionRequestContext(pinnedQuestionContext);assertPinnedQuestionContextDependencies(pinnedQuestionContext,{db,fetcher,crypto:globalThis.crypto});require(authority==='idea'&&basis?.kind==='pinned-question-member-v1'&&!loadPinnedDomain&&!loadPinnedBundle,'A request context only admits its original pinned question.');}};liveContext();
 const limits=checkedStorageLimits(storageLimits);
 const bound=await binding({proposalId,card,task,inputVersion,parentTaskId,controls});
 require(await proposal(db,bound),'Confirmed proposal is unavailable or changed');
 if(parentTaskId!==null)require(await query(db,'SELECT t.id FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id WHERE t.id=? AND links.proposal_id=?',parentTaskId,proposalId),
  'Prepared parent is not associated with this idea');
 require(['idea','remaining-lp2','word-boundaries'].includes(authority),'Invalid prepared authority');
 const source=await basisFor(db,basis,bound,authority,false,fetcher,loadAuthoredSource,loadPinnedDomain,loadPinnedBundle,pinnedQuestionContext,signal),id='prep_'+await sha(E.stable(identity(bound.base,authority,source.hash)));
 let row=await query(db,'SELECT * FROM prepared_plans WHERE id=?',id);
 if(row){const receipt=await checked(row,bound);require(receipt,'Stored preparation differs from its binding');liveContext();return receipt;}
 require(typeof createdAt==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(createdAt)
  &&Number.isFinite(Date.parse(createdAt))&&new Date(createdAt).toISOString()===createdAt,'Invalid preparation date');
 const b=bound.base,day=createdAt.slice(0,10);
 liveContext();
 await query(db,`INSERT INTO prepared_plans(id,binding_hash,proposal_id,card_hash,task_id,task_hash,input_version,parent_task_id,authority,controls_hash,basis_hash,basis_json,created_at,created_day)
  SELECT ?,?,?,?,?,?,?,?,?,?,?,?,?,? WHERE (SELECT COUNT(*) FROM prepared_plans WHERE created_day=?)<?
  ON CONFLICT(id) DO NOTHING RETURNING id`,id,bound.bindingHash,proposalId,b.cardHash,b.taskId,b.taskHash,inputVersion,parentTaskId,authority,b.controlsHash,source.hash,source.text,createdAt,day,day,limits.preparations);
 row=await query(db,'SELECT * FROM prepared_plans WHERE id=?',id);
 if(!row){const error=Error('The daily prepared-plan limit has been reached');error.code='preparation-limit';throw error;}
 const receipt=await checked(row,bound);require(receipt,'Prepared plan could not be verified');liveContext();return receipt;
}
export async function authorize({db,preparationId,proposalId,card,task,inputVersion,parentTaskId,controls,fetcher=globalThis.fetch,loadAuthoredSource,loadPinnedDomain,loadPinnedBundle,pinnedQuestionContext,signal}){
 let bound;
 if(signal?.aborted)return null;
 try{if(preparationId!==undefined)require(typeof preparationId==='string'&&PREP.test(preparationId),'Invalid preparation ID');
  bound=await binding({proposalId,card,task,inputVersion,parentTaskId,controls});}catch{return null;}
 if(!await proposal(db,bound))return null;
 const row=preparationId===undefined?
  await query(db,'SELECT * FROM prepared_plans WHERE binding_hash=? ORDER BY created_at,id LIMIT 1',bound.bindingHash):
  await query(db,'SELECT * FROM prepared_plans WHERE id=? AND binding_hash=?',preparationId,bound.bindingHash);
 const receipt=await checked(row,bound);if(!receipt)return null;
 try{const basis=JSON.parse(row.basis_json);if(pinnedQuestionContext!==undefined){assertPinnedQuestionContextDependencies(pinnedQuestionContext,{db,fetcher,crypto:globalThis.crypto});require(row.authority==='idea'&&basis.kind==='pinned-question-member-v1'&&!loadPinnedDomain&&!loadPinnedBundle,'A request context only authorizes its original pinned question.');}if(['pinned-domain-member-v1','pinned-question-member-v1'].includes(basis.kind)){await basisFor(db,basis,bound,row.authority,true,fetcher,loadAuthoredSource,loadPinnedDomain,loadPinnedBundle,pinnedQuestionContext);if(pinnedQuestionContext!==undefined)inspectPinnedQuestionRequestContext(pinnedQuestionContext);return receipt;}if(basis.kind==='authored-finite-member-v1'){await basisFor(db,basis,bound,row.authority,true,fetcher,loadAuthoredSource);return {...receipt,reviewed:await checkedAuthoredFiniteMember({basis,card:bound.card,task:bound.task,inputVersion,fetcher,loadAuthoredSource})};}if(['ordinary-derived-prefix-remainder-v1','ordinary-derived-openings-remainder-v1','ordinary-derived-assessment-remainder-v1','record-derived-prefix-remainder-v1','record-strict-evidence-remainder-v1'].includes(basis.kind))await basisFor(db,basis,bound,row.authority,true,fetcher,undefined,undefined,undefined,undefined,signal);if(['record-derived-prefix-remainder-v1','record-strict-evidence-remainder-v1'].includes(basis.kind))return {...receipt,reviewed:await checkedRecordRemainder({basis,card:bound.card,task:bound.task,inputVersion,fetcher})};}catch{return null;}
 if(signal?.aborted)return null;return receipt;
}
