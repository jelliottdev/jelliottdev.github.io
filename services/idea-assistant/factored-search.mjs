/* Authoritative HTTP adapter for factored questions. Original cards and official
 * inputs are loaded fresh by the shared handler on every discovery/admission.
 * The memo caches compilation only; it never supplies DB or input authority. */
import Settings from '../../finite-settings.js';
import {createFiniteSearchHandler} from './finite-search.mjs';
import {createFactoredCompiler} from './factored-compiler-cache.mjs';
import {readFactoredEvidencePage,verifyFactoredSnapshot} from './factored-search-evidence.mjs';
import {selectFactoredCases,findSelectedFactoredEvidence} from './factored-selected-evidence.mjs';
import {prepareFiniteCases} from './finite-search-admission.mjs';
export function createFactoredSearchHandler({fetcher=globalThis.fetch,now=()=>new Date(),taskHandler}={}){
 const compiler=createFactoredCompiler();
 const clock=()=>now().getTime();
 const gate=({db,proposalId,currentDomain,body,env})=>verifyFactoredSnapshot({db,proposalId,domain:currentDomain.domain,inputVersion:currentDomain.domain.inputVersion,snapshotToken:body.snapshotToken,cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:clock()});
 return createFiniteSearchHandler({fetcher,now,...(taskHandler?{taskHandler}:{}),settingsAPI:Settings.factored,
  async authorizeDomain(context){
   const {card,bundle,body,action}=context;
   const compiled=await compiler.compile({card,bundle:{schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]}});
   if(compiled.domain.id!==body.domainId)throw Object.assign(Error('The original question or official inputs changed. Review a fresh lookup.'),{status:409,code:'stale-scan'});
   if(action!=='evidence')await gate({...context,currentDomain:compiled});
   return compiled;
  },
  async discoverEvidence({db,proposalId,currentDomain,body,env}){
   return readFactoredEvidencePage({db,proposalId,domain:currentDomain.domain,inputVersion:body.inputVersion,cursor:body.cursor,cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:clock()});
  },
  async prepareCases(context){
   const {currentDomain,db,cases,request}=context,selected=await selectFactoredCases({compiled:currentDomain,cases}),reuse=await findSelectedFactoredEvidence({db,domain:currentDomain.domain,cases:selected});
   await gate(context);
   if(request.signal.aborted)throw Object.assign(Error('The request was cancelled.'),{status:499});
   const prepared=reuse.missing.length?await prepareFiniteCases({...context,cases:reuse.missing,settingsAPI:Settings.factored,signal:request.signal}):{inputVersion:currentDomain.domain.inputVersion,cases:[]};
   return {...prepared,sources:reuse.sources,sourceLinks:reuse.sourceLinks};
  }
 });
}
