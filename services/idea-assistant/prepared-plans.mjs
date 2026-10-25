/* Immutable server-issued admission proof. No generation, inference or task writes. */
import C from '../../claim-specification.js';
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import Variants from '../../task-variants.js';
import {validateCard} from './idea-relations.mjs';
import Evidence from '../../computation-evidence.js';
import {checkedEvidence} from './task-evidence.mjs';
import Settings from '../../finite-settings.js';
import Policy from '../../finite-question-policy.js';
import Compiler from '../../fixed-plan-compiler.js';
import {storageLimits as checkedStorageLimits} from './storage-limits.mjs';

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
async function basisFor(db,value,bound,authority){
 const data=json(value,128000),basis=data.value;
 if(authority==='idea'){
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
    &&bound.card.rules.evaluation.status==='specified'&&(basis.kind==='factored-inspection-settings'?bound.card.rules.evaluation.value==='measurement':basis.kind==='factored-output-settings'?Policy.describe(bound.card.rules.evaluation.value).id==='language-reference-comparison-v1':bound.card.rules.evaluation.value?.kind==='exact-prefix'),'Finite settings do not compile to the explicit maintained evaluation');
   require(E.stable(basis.settings)===E.stable(member.settings)&&plan.inputVersion===bound.base.inputVersion&&plan.inputVersion===bound.card.rules.inputVersion.value
    &&E.stable(plan.criterion)===E.stable(basis.kind==='factored-inspection-settings'?{kind:'measurement'}:bound.card.rules.evaluation.value)&&E.stable(bound.task.criterion)===E.stable(plan.criterion)&&E.stable(bound.task.steps)===E.stable(plan.steps)
    &&E.stable(plan.pages)===E.stable(bound.card.scope.value.pages)&&bound.task.pages.length===1&&plan.pages.includes(bound.task.pages[0].id),'Finite settings changed the declared parameters, pages or common rules');
   const described=await Evidence.describe(bound.task,bound.base.inputVersion);
   require(described.pages.length===1&&described.pages[0].caseId===basis.caseId,'Finite settings case differs from the exact prepared page and program');
   return {text:data.text,hash:await sha(data.text)};
  }
  const original=basis.kind==='evidence-remainder'?basis.originalBasis:basis;
  require(exact(original,['kind','normalizedCard',...(original?.kind==='mapped-card'?['mapping']:[])])
   &&['compiled-card','mapped-card'].includes(original.kind),'Invalid idea preparation basis');
  const normalized=validateCard(original.normalizedCard);
  if(original.kind==='compiled-card')require(C.serialize(normalized)===C.serialize(bound.card),'Compiled basis changed the original card');
  else require(original.mapping&&typeof original.mapping==='object'&&!Array.isArray(original.mapping),'Mapped basis requires reviewed mapping evidence');
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
export async function issue({db,proposalId,card,task,inputVersion,parentTaskId,controls,authority,basis,createdAt=new Date().toISOString(),storageLimits}){
 const limits=checkedStorageLimits(storageLimits);
 const bound=await binding({proposalId,card,task,inputVersion,parentTaskId,controls});
 require(await proposal(db,bound),'Confirmed proposal is unavailable or changed');
 if(parentTaskId!==null)require(await query(db,'SELECT t.id FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id WHERE t.id=? AND links.proposal_id=?',parentTaskId,proposalId),
  'Prepared parent is not associated with this idea');
 require(['idea','remaining-lp2','word-boundaries'].includes(authority),'Invalid prepared authority');
 const source=await basisFor(db,basis,bound,authority),id='prep_'+await sha(E.stable(identity(bound.base,authority,source.hash)));
 let row=await query(db,'SELECT * FROM prepared_plans WHERE id=?',id);
 if(row){const receipt=await checked(row,bound);require(receipt,'Stored preparation differs from its binding');return receipt;}
 require(typeof createdAt==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(createdAt)
  &&Number.isFinite(Date.parse(createdAt))&&new Date(createdAt).toISOString()===createdAt,'Invalid preparation date');
 const b=bound.base,day=createdAt.slice(0,10);
 await query(db,`INSERT INTO prepared_plans(id,binding_hash,proposal_id,card_hash,task_id,task_hash,input_version,parent_task_id,authority,controls_hash,basis_hash,basis_json,created_at,created_day)
  SELECT ?,?,?,?,?,?,?,?,?,?,?,?,?,? WHERE (SELECT COUNT(*) FROM prepared_plans WHERE created_day=?)<?
  ON CONFLICT(id) DO NOTHING RETURNING id`,id,bound.bindingHash,proposalId,b.cardHash,b.taskId,b.taskHash,inputVersion,parentTaskId,authority,b.controlsHash,source.hash,source.text,createdAt,day,day,limits.preparations);
 row=await query(db,'SELECT * FROM prepared_plans WHERE id=?',id);
 if(!row){const error=Error('The daily prepared-plan limit has been reached');error.code='preparation-limit';throw error;}
 const receipt=await checked(row,bound);require(receipt,'Prepared plan could not be verified');return receipt;
}
export async function authorize({db,preparationId,proposalId,card,task,inputVersion,parentTaskId,controls}){
 let bound;
 try{if(preparationId!==undefined)require(typeof preparationId==='string'&&PREP.test(preparationId),'Invalid preparation ID');
  bound=await binding({proposalId,card,task,inputVersion,parentTaskId,controls});}catch{return null;}
 if(!await proposal(db,bound))return null;
 const row=preparationId===undefined?
  await query(db,'SELECT * FROM prepared_plans WHERE binding_hash=? ORDER BY created_at,id LIMIT 1',bound.bindingHash):
  await query(db,'SELECT * FROM prepared_plans WHERE id=? AND binding_hash=?',preparationId,bound.bindingHash);
 return checked(row,bound);
}
