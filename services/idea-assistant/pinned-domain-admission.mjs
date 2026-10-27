/* Maintained-source admission bridge. Synthetic controls only; no target output. */
import Json from '../../finite-json.js';
import E from '../../local-experiment.js';
import Members from '../../pinned-domain-members.js';
import Warning from '../../pinned-warning-controls.js';
import Controls from '../../local-plan-controls.js';
import {preparePinnedParent} from './pinned-parent-loader.mjs';
import {issue} from './prepared-plans.mjs';
import {inspect as inspectQuestion} from './pinned-domain-question.mjs';
import {inspectPinnedQuestionRequestContext as inspectContext,assertPinnedQuestionContextDependencies as contextDependencies} from './pinned-question-request-context.mjs';
const retained=new WeakMap(),HEX=/^[a-f0-9]{64}$/,SOURCE=/^[a-z0-9]+(?:-[a-z0-9]+)*(?![\s\S])/,exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k)),need=(v,m)=>{if(!v)throw Error(m);},same=(a,b)=>E.stable(a)===E.stable(b),capture=v=>Json.capture(v,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},pin=v=>typeof v==='string'&&v.length===64&&HEX.test(v);
async function loaders({loadDomain,loadBundle,fetcher=globalThis.fetch}){return {originalLoadDomain:loadDomain,originalLoadBundle:loadBundle,loadDomain:loadDomain||(await import('./pinned-domain-registry.mjs')).createPinnedDomainSourceLoader(fetcher)};}
function sourceSnapshot(value,sourceId){
 need(value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===5,'Use an exact maintained source descriptor');const fields={};for(const key of ['sourceId','domain','manifestBytes','manifestSha256','template']){const d=Object.getOwnPropertyDescriptor(value,key);need(d&&Object.hasOwn(d,'value')&&d.enumerable,'Maintained source fields must be data');fields[key]=d.value;}
 need(fields.sourceId===sourceId&&pin(fields.manifestSha256)&&fields.manifestBytes instanceof Uint8Array&&fields.manifestBytes.byteLength<=2*1024*1024,'The maintained source or independent manifest identity changed');return {sourceId,domain:capture(fields.domain),template:capture(fields.template),manifestSha256:fields.manifestSha256,manifestBytes:new Uint8Array(fields.manifestBytes)};
}
function cancelled(signal){if(signal?.aborted)throw Object.assign(Error('Pinned member preparation cancelled'),{status:499});}
async function controlledMember({source,parent,chosen,crypto,signal,unchanged,live,access}){
 const check=()=>{unchanged();cancelled(signal);live();};check();
 const member=await Members.derive(parent,chosen);check();
 const manifest=await Warning.read(source.manifestBytes,{sha256:source.manifestSha256,parent,template:source.template,crypto});check();
 const proof=await Warning.verify(member,manifest);check();Warning.inspect(proof,{member,manifest});
 // Fresh independent Warning and ordinary admission controls are required even
 // when the immutable parent/source came from this request's private context.
 const controls=await Controls.prepare(member.task,crypto);check();await Controls.validate(controls,member.task,crypto);check();
 const basis={kind:'pinned-domain-member-v1',sourceId:source.sourceId,parentDomainId:member.parentDomainId,memberId:member.memberId,globalSettingIndex:member.globalSettingIndex,pageIds:chosen.pageIds,manifestSha256:source.manifestSha256,controlTaskId:proof.controlTaskId,controlResultSha256:proof.controlResultSha256};
 const payload=freeze({state:'controls-verified',proposalId:member.cardIdentity,card:member.card,task:member.task,inputVersion:member.inputVersion,parentTaskId:null,authority:'idea',basis,controls,checks:{targetExecution:false,persistence:false}});retained.set(payload,{parent,member,manifest,proof,source,access});return payload;
}
export async function preparePinnedDomainMember({sourceId,selection,bundle,loadDomain,loadBundle,fetcher=globalThis.fetch,crypto=globalThis.crypto,signal,requestContext}={}){
 need(typeof sourceId==='string'&&sourceId.length<=128&&SOURCE.test(sourceId),'Select a maintained pinned domain source');const chosen=capture(selection),unchanged=()=>need(same(capture(selection),chosen),'The selected pinned member changed during preparation');cancelled(signal);
 if(requestContext!==undefined){
  need(loadDomain===undefined&&loadBundle===undefined&&bundle===undefined,'A private request context cannot replace its source loaders or bundle');contextDependencies(requestContext,{fetcher,crypto,signal});const context=inspectContext(requestContext),question=inspectQuestion(context.questionToken);need(context.sourceId===sourceId,'The request context belongs to another pinned source');
  const live=()=>inspectContext(requestContext,{questionToken:context.questionToken});
  return controlledMember({source:question.source,parent:context.parent,chosen,crypto,signal,unchanged,live,access:{}});
 }
 const access=await loaders({loadDomain,loadBundle,fetcher,signal}),source=sourceSnapshot(await access.loadDomain(sourceId),sourceId);unchanged();cancelled(signal);
 const parent=await preparePinnedParent({sourceId,domain:source.domain,template:source.template,manifestSha256:source.manifestSha256,bundle,loadDomain,loadBundle,fetcher,crypto,signal});unchanged();cancelled(signal);
 return controlledMember({source,parent,chosen,crypto,signal,unchanged,live:()=>{},access});
}
export function inspectPinnedDomainPreparation(value){need(retained.has(value),'Use an unchanged independently checked pinned preparation');return value;}
export async function checkedPinnedDomainMember({basis,card,task,inputVersion,loadDomain,loadBundle,fetcher=globalThis.fetch,crypto=globalThis.crypto,signal}={}){
 const b=capture(basis),original=capture(card),program=capture(task);need(exact(b,['kind','sourceId','parentDomainId','memberId','globalSettingIndex','pageIds','manifestSha256','controlTaskId','controlResultSha256'])&&b.kind==='pinned-domain-member-v1'&&pin(b.manifestSha256)&&pin(b.controlTaskId)&&pin(b.controlResultSha256),'The pinned-domain admission basis changed');
 const expected=await preparePinnedDomainMember({sourceId:b.sourceId,selection:{globalSettingIndex:b.globalSettingIndex,pageIds:b.pageIds},loadDomain,loadBundle,fetcher,crypto,signal});need(same(expected.basis,b)&&same(expected.card,original)&&same(expected.task,program)&&expected.inputVersion===inputVersion,'The immutable pinned parent member, source, control or task changed');need(same(capture(basis),b)&&same(capture(card),original)&&same(capture(task),program),'The pinned admission request changed during checking');return expected;
}
export async function issuePinnedDomainPreparation({db,prepared,createdAt,storageLimits,loadDomain,loadBundle,fetcher=globalThis.fetch}={}){
 const p=inspectPinnedDomainPreparation(prepared),access=retained.get(p).access;return issue({db,proposalId:p.proposalId,card:p.card,task:p.task,inputVersion:p.inputVersion,parentTaskId:null,controls:p.controls,authority:'idea',basis:p.basis,...(createdAt!==undefined?{createdAt}:{}),storageLimits,fetcher,loadPinnedDomain:loadDomain||access.originalLoadDomain,loadPinnedBundle:loadBundle||access.originalLoadBundle});
}
