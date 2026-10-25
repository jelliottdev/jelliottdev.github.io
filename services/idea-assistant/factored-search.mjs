/* Authoritative HTTP adapter for factored questions. Original cards and official
 * inputs are loaded fresh by the shared handler on every discovery/admission.
 * The memo caches compilation only; it never supplies DB or input authority. */
import {readFactoredOutputEvidencePage,verifyFactoredOutputSnapshot} from './factored-output-evidence.mjs';
import {readFactoredInspectionEvidencePage,verifyFactoredInspectionSnapshot} from './factored-inspection-evidence.mjs';
import Settings from '../../finite-settings.js';
import {createFiniteSearchHandler} from './finite-search.mjs';
import {createFactoredCompiler,createFactoredOutputCompiler,createFactoredInspectionCompiler} from './factored-compiler-cache.mjs';
import {readFactoredEvidencePage,verifyFactoredSnapshot} from './factored-search-evidence.mjs';
import {readFactoredPrefixEvidencePage,verifyFactoredPrefixSnapshot} from './factored-prefix-evidence.mjs';
import {selectFactoredCases,findSelectedFactoredEvidence,findSelectedFactoredPrefixEvidence,findSelectedFactoredOutputEvidence,findSelectedFactoredInspectionEvidence} from './factored-selected-evidence.mjs';
import {prepareFiniteCases} from './finite-search-admission.mjs';
function createHandler({fetcher=globalThis.fetch,now=()=>new Date(),taskHandler}={},prefix=false,output=false,inspection=false){
 const compiler=(inspection?createFactoredInspectionCompiler:output?createFactoredOutputCompiler:createFactoredCompiler)();
 const questionPolicy=inspection?'transformed-output-inspection-v1':output?'language-reference-comparison-v1':undefined;
 const readPage=inspection?readFactoredInspectionEvidencePage:output?readFactoredOutputEvidencePage:prefix?readFactoredPrefixEvidencePage:readFactoredEvidencePage;
 const verify=inspection?verifyFactoredInspectionSnapshot:output?verifyFactoredOutputSnapshot:prefix?verifyFactoredPrefixSnapshot:verifyFactoredSnapshot;
 const findSelected=inspection?findSelectedFactoredInspectionEvidence:output?findSelectedFactoredOutputEvidence:prefix?findSelectedFactoredPrefixEvidence:findSelectedFactoredEvidence;
 const clock=()=>now().getTime();
 const gate=({db,proposalId,currentDomain,body,env})=>verify({db,proposalId,domain:currentDomain.domain,inputVersion:currentDomain.domain.inputVersion,snapshotToken:body.snapshotToken,cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:clock()});
 const prefixReuse=async context=>{const {db,proposalId,currentDomain,cases,env,request}=context,reuse=await findSelected({db,proposalId,domain:currentDomain.domain,cases,cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:clock(),fetcher,signal:request.signal});await gate(context);if(request.signal.aborted)throw Object.assign(Error('The request was cancelled.'),{status:499});return reuse;};
 return createFiniteSearchHandler({fetcher,now,verifyGroupSnapshot:gate,...(taskHandler?{taskHandler}:{}),settingsAPI:Settings.factored,...((prefix||output||inspection)?{routePrefix:inspection?'factored-inspection-search':output?'factored-output-search':'factored-prefix-search',reuseCasesBeforeCreate:prefixReuse}:{}),
  async authorizeDomain(context){
   const {card,bundle,body,action}=context;
   const compiled=await compiler.compile({card,bundle:{schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]}});
   if(compiled.domain.id!==body.domainId)throw Object.assign(Error('The original question or official inputs changed. Review a fresh lookup.'),{status:409,code:'stale-scan'});
   if(action!=='evidence')await gate({...context,currentDomain:compiled});
   return compiled;
  },
  async discoverEvidence({db,proposalId,currentDomain,body,env,request}){
   return readPage({db,proposalId,domain:currentDomain.domain,inputVersion:body.inputVersion,cursor:body.cursor,cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:clock(),fetcher,signal:request.signal});
  },
  async prepareCases(context){
   const {currentDomain,db,cases,request,proposalId,env}=context,selected=await selectFactoredCases({compiled:currentDomain,cases}),reuse=await findSelected({db,domain:currentDomain.domain,cases:selected,fetcher,signal:request.signal,...((prefix||output||inspection)?{proposalId,cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:clock()}:{} )});
   await gate(context);
   if(request.signal.aborted)throw Object.assign(Error('The request was cancelled.'),{status:499});
   const prepared=reuse.missing.length?await prepareFiniteCases({...context,cases:reuse.missing,settingsAPI:Settings.factored,...(questionPolicy?{questionPolicy}:{}),signal:request.signal}):{inputVersion:currentDomain.domain.inputVersion,cases:[]};
   return {...prepared,sources:reuse.sources,sourceLinks:reuse.sourceLinks};
  }
 });
}
export const createFactoredSearchHandler=options=>createHandler(options,false);
export const createFactoredPrefixSearchHandler=options=>createHandler(options,true);

export const createFactoredOutputSearchHandler=options=>createHandler(options,false,true);
export const createFactoredInspectionSearchHandler=options=>createHandler(options,false,false,true);
