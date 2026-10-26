/* Private controlled-member admission under its unchanged complete public question.
 * A scheduling selector never authorizes execution or bypasses existing controls. */
import J from '../../finite-json.js';
import E from '../../local-experiment.js';
import C from '../../claim-specification.js';
import {prepare as bindQuestion,inspect as inspectQuestion} from './pinned-domain-question.mjs';
import {preparePinnedDomainMember} from './pinned-domain-admission.mjs';
const prepared=new WeakMap(),HEX=/^[a-f0-9]{64}$/,need=(v,m)=>{if(!v)throw Error(m);},same=(a,b)=>E.stable(a)===E.stable(b),copy=v=>J.capture(v,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x));
async function hash(v,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
export async function preparePinnedQuestionMember({question,selection,loadDomain,loadBundle,fetcher=globalThis.fetch,crypto=globalThis.crypto,signal}={}){
 const original=inspectQuestion(question),chosen=copy(selection),unchanged=()=>need(same(copy(selection),chosen),'The selected parent-question member changed during preparation.');
 const rebound=inspectQuestion(await bindQuestion({card:original.card,proposalId:original.proposalId},{loadDomain,loadBundle,fetcher,crypto}));unchanged();need(rebound.sourceId===original.sourceId&&rebound.parentDomainId===original.parentDomainId,'The complete original question source changed.');
 const member=await preparePinnedDomainMember({sourceId:rebound.sourceId,selection:chosen,loadDomain,loadBundle,fetcher,crypto,signal});unchanged();need(member.basis.parentDomainId===rebound.parentDomainId,'The selected calculation belongs to another complete parent.');
 const source=rebound.source,sourceBindingSha256=await hash({sourceId:source.sourceId,domain:source.domain,template:source.template,manifestSha256:source.manifestSha256},crypto),basis={...member.basis,kind:'pinned-question-member-v1',parentProposalId:rebound.proposalId,parentCardSha256:rebound.proposalId.slice(2),sourceBindingSha256,taskSha256:await hash(member.task,crypto)};unchanged();
 const payload=freeze({...member,proposalId:rebound.proposalId,card:copy(rebound.card),basis,checks:{targetExecution:false,persistence:false}});prepared.set(payload,{loadDomain,loadBundle,fetcher});return payload;
}
export function inspectPinnedQuestionPreparation(value){need(prepared.has(value),'Use a private controlled parent-question preparation.');return value;}
export async function checkedPinnedQuestionMember({basis,card,task,inputVersion,loadDomain,loadBundle,fetcher=globalThis.fetch,crypto=globalThis.crypto,signal}={}){
 const b=copy(basis),original=copy(card),program=copy(task);need(exact(b,['kind','sourceId','parentDomainId','memberId','globalSettingIndex','pageIds','manifestSha256','controlTaskId','controlResultSha256','parentProposalId','parentCardSha256','sourceBindingSha256','taskSha256'])&&b.kind==='pinned-question-member-v1'&&typeof b.parentProposalId==='string'&&/^p_[a-f0-9]{64}$/.test(b.parentProposalId)&&[b.parentCardSha256,b.sourceBindingSha256,b.taskSha256].every(v=>typeof v==='string'&&HEX.test(v))&&b.parentProposalId==='p_'+b.parentCardSha256,'The parent-question admission basis changed.');
 need(await hash(C.serialize(original),crypto)===b.parentCardSha256&&await hash(program,crypto)===b.taskSha256,'The original question or selected task identity changed.');
 const question=await bindQuestion({card:original,proposalId:b.parentProposalId},{loadDomain,loadBundle,fetcher,crypto}),expected=await preparePinnedQuestionMember({question,selection:{globalSettingIndex:b.globalSettingIndex,pageIds:b.pageIds},loadDomain,loadBundle,fetcher,crypto,signal});
 need(same(expected.basis,b)&&same(expected.card,original)&&same(expected.task,program)&&expected.inputVersion===inputVersion,'The complete parent, controlled member or source binding changed.');need(same(copy(basis),b)&&same(copy(card),original)&&same(copy(task),program),'The parent-question admission request changed during checking.');return expected;
}
export async function issuePinnedQuestionPreparation({db,prepared:payload,createdAt,storageLimits,loadDomain,loadBundle,fetcher}={}){
 const value=inspectPinnedQuestionPreparation(payload),access=prepared.get(value),{issue}=await import('./prepared-plans.mjs');return issue({db,proposalId:value.proposalId,card:value.card,task:value.task,inputVersion:value.inputVersion,parentTaskId:null,controls:value.controls,authority:'idea',basis:value.basis,...(createdAt!==undefined?{createdAt}:{}),storageLimits,fetcher:fetcher||access.fetcher,loadPinnedDomain:loadDomain||access.loadDomain,loadPinnedBundle:loadBundle||access.loadBundle});
}
