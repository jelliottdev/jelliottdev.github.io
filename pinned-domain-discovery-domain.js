/* Bounded source-bound discovery programs only. No outputs, controls or admission. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,M=node?require('./pinned-domain-members.js'):root.PinnedDomainMembers,Q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion,R=node?require('./computation-evidence.js'):root.ComputationEvidence,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON;
 const tokens=new WeakMap(),LIMIT=16,need=(v,m)=>{if(!v)throw Error(m);},same=(a,b)=>E.stable(a)===E.stable(b),capture=v=>J.capture(v,{maxBytes:1024,maxDepth:4,maxNodes:32}),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 async function hash(v,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 async function prepare(parent,options={},crypto=root.crypto){
  const bound=M.inspect(parent),v=capture(options),total=bound.domain.bank.count;
  need(v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).every(k=>['start','count'].includes(k)),'Declare only a bounded discovery range.');
  const start=Object.hasOwn(v,'start')?v.start:0,count=Object.hasOwn(v,'count')?v.count:Math.min(LIMIT,total-start);need(Number.isSafeInteger(start)&&start>=0&&start<total&&Number.isSafeInteger(count)&&count>=1&&count<=LIMIT&&start+count<=total,'Discovery ranges contain one to16 exact named settings.');need(crypto?.subtle,'Hash verification is unavailable.');
  need(['exact-prefix','exact-prefix-set'].includes(bound.domain.criterion.kind),'Discovery requires an exact opening or opening set; no evaluation fallback is permitted.');
  const unchanged=()=>need(same(capture(options),v),'The discovery range changed during compilation.'),pageIds=bound.domain.pages.map(p=>p.id),programs=[],aliases=new Map();let common=null;need(same(pageIds,[...pageIds].sort((a,b)=>a.localeCompare(b))),'Discovery requires unchanged canonical ordered pages.');
  // Scheduling never narrows the parent page scope. Members independently bind
  // oversized periodic representations against that same complete scope.
  for(let index=start;index<start+count;index++){
   const member=await M.derive(parent,{globalSettingIndex:index,pageIds});M.inspectMember(member,{parent});unchanged();const task=member.task,descriptor=await R.describe(task,member.inputVersion,crypto);unchanged();
   need(member.globalSettingIndex===index&&member.parentDomainId===bound.plan.domainId&&same(task.pages.map(p=>p.id),pageIds)&&same(task.criterion,bound.domain.criterion)&&member.inputVersion===bound.domain.inputVersion,'Discovery changed the complete parent scope or criterion.');
   if(!common)common={engine:task.engine,inputVersion:member.inputVersion,alphabet:task.alphabet,pages:task.pages,criterion:task.criterion};else need(same(task.alphabet,common.alphabet)&&same(task.pages,common.pages)&&same(task.criterion,common.criterion)&&task.engine===common.engine,'Discovery programs must share exact complete inputs.');
   if(!aliases.has(descriptor.protocolId)){aliases.set(descriptor.protocolId,[]);programs.push({id:descriptor.protocolId,steps:task.steps});}aliases.get(descriptor.protocolId).push(index);
  }
  const domain=await Q.bind({...common,programs},crypto);unchanged();const checked=Q.inspect(domain);need(same(checked.pages,common.pages)&&checked.programs.length===programs.length&&checked.programs.every(p=>aliases.has(p.id)),'The strict discovery binder changed ordered page geometry or programs.');const parentPlanSha256=await hash(bound.plan,crypto);unchanged();
  const model=freeze({state:'bound-discovery-programs-only',parentDomainId:bound.plan.domainId,parentPlanSha256,start,count,nextStart:start+count<total?start+count:null,domain,programMap:[...aliases].map(([programId,globalSettingIndices])=>({programId,globalSettingIndices})).sort((a,b)=>a.programId.localeCompare(b.programId)),checks:{execution:false,controls:false,admission:false,evidence:false}}),token=Object.freeze({});tokens.set(token,{parent,model});return token;
 }
 function inspect(token,options={}){const value=tokens.get(token);need(value&&options&&typeof options==='object'&&!Array.isArray(options),'Use a private discovery binding.');const descriptors=Object.getOwnPropertyDescriptors(options);need(Reflect.ownKeys(descriptors).every(k=>k==='parent'&&Object.hasOwn(descriptors[k],'value')&&descriptors[k].enumerable)&&(!descriptors.parent||descriptors.parent.value===value.parent),'Use the exact optional source-bound parent.');return value.model;}
 const api=Object.freeze({prepare,inspect,LIMITS:Object.freeze({settings:LIMIT})});if(node)module.exports=api;else root.PinnedDomainDiscoveryDomain=api;
})(typeof globalThis!=='undefined'?globalThis:this);
