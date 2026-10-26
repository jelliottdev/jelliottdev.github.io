/* Internal scheduling only: missing coordinates are not admitted tasks, results,
 * reservations or new questions. Only externally verified ledger receipts advance work. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,M=node?require('./pinned-domain-members.js'):root.PinnedDomainMembers,L=node?require('./pinned-domain-case-ledger.js'):root.PinnedDomainCaseLedger,J=node?require('./finite-json.js'):root.FiniteJSON;
 const SCHEMA='liberpedia-pinned-domain-next-work-v1',LIMITS=Object.freeze({jobs:1024,pagesPerJob:75,pageCases:76800}),need=(v,m)=>{if(!v)throw Error(m);},freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function select(parent,ledger,options={}){
  const bound=M.inspect(parent),v=J.capture(options,{maxBytes:4096,maxDepth:4,maxNodes:32});
  need(v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).every(k=>['cursor','maxJobs','pagesPerJob'].includes(k)),'Declare only a scheduling cursor and bounded job/page counts.');
  const cursor=v.cursor??0,maxJobs=v.maxJobs??1,pagesPerJob=v.pagesPerJob??12,total=bound.plan.counters.pageCases;
  need(Number.isSafeInteger(cursor)&&cursor>=0&&cursor<=total&&Number.isSafeInteger(maxJobs)&&maxJobs>=1&&maxJobs<=LIMITS.jobs&&Number.isSafeInteger(pagesPerJob)&&pagesPerJob>=1&&pagesPerJob<=LIMITS.pagesPerJob&&maxJobs*pagesPerJob<=LIMITS.pageCases,'Use existing bounded job and page limits.');
  // The private ledger verifies the exact parent identity even for empty work.
  const status=L.inspect(ledger),jobs=[];let position=cursor,nextCursor=null,pageCases=0;
  need(status.parentDomainId===bound.plan.domainId,'The ledger belongs to another complete parent.');
  while(jobs.length<maxJobs){
   const batch=L.missing(ledger,{parent,cursor:position,limit:Math.min(pagesPerJob,bound.domain.pages.length)});
   need(batch.parentDomainId===status.parentDomainId&&batch.parentPlanSha256===status.parentPlanSha256,'The complete parent changed during scheduling.');
   if(!batch.entries.length){nextCursor=null;break;}
   const first=batch.entries[0].globalSettingIndex,entries=batch.entries.filter(entry=>entry.globalSettingIndex===first),last=entries.at(-1);
   jobs.push({selector:{globalSettingIndex:first,pageIds:entries.map(entry=>entry.pageId)},pageCases:entries.length});pageCases+=entries.length;
   position=last.coordinate+1;
   // A batch may include the next setting; leave those coordinates for the next job.
   nextCursor=entries.length<batch.entries.length?position:batch.nextCursor;
   if(nextCursor===null)break;
   position=nextCursor;
  }
  return freeze({schema:SCHEMA,state:'scheduling-only',parentDomainId:status.parentDomainId,parentPlanSha256:status.parentPlanSha256,inputVersion:bound.domain.inputVersion,cursor,jobs,pageCases,nextCursor,restartCursor:nextCursor===null&&!status.complete?0:null,remainingNamedCases:status.remainingNamedCases,complete:status.complete,checks:{admission:false,controls:false,execution:false,persistence:false,reservation:false,outcomeInference:false}});
 }
 const api=Object.freeze({SCHEMA,LIMITS,select});if(node)module.exports=api;else root.PinnedDomainNextWork=api;
})(typeof globalThis!=='undefined'?globalThis:this);
