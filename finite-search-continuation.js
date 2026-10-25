/* Explicit, cancellable continuation of one reviewed finite domain. Adapters retain all authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,HEX=/^[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 const copy=v=>J.capture(v,{maxBytes:65536,maxDepth:10,maxNodes:6000}),stable=v=>JSON.stringify(v);
 function sleep(ms,signal){return new Promise((resolve,reject)=>{if(signal.aborted)return reject(new DOMException('Paused.','AbortError'));const stop=()=>{clearTimeout(timer);signal.removeEventListener('abort',stop);reject(new DOMException('Paused.','AbortError'));},timer=setTimeout(()=>{signal.removeEventListener('abort',stop);resolve();},ms);signal.addEventListener('abort',stop,{once:true});});}
 function createController(options={}){return controller(options,null);}
 function createOutputController(options={}){return outputController(options,'language-reference-comparison-v1');}
 function createInspectionController(options={}){
  if(!options||typeof options!=='object'||Array.isArray(options))throw Error('Use explicit inspection continuation options.');const descriptors=Object.getOwnPropertyDescriptors(options),captured={};for(const key of Reflect.ownKeys(options)){const descriptor=descriptors[key];if(typeof key!=='string'||!['domain','adapter','clock','onState','maxRetries','maxDelayMs'].includes(key)||!descriptor.enumerable||!Object.hasOwn(descriptor,'value'))throw Error('Use explicit inspection continuation options.');captured[key]=descriptor.value;}return outputController(captured,'transformed-output-inspection-v1');
 }
 function createGroupController(options={}){return groupController(options,'prefix');}
 function createOutputGroupController(options={}){return groupController(options,'language-reference-comparison-v1');}
 function createInspectionGroupController(options={}){return groupController(options,'transformed-output-inspection-v1');}
 function groupController(input,policy){
  if(!input||typeof input!=='object'||Array.isArray(input))throw Error('Use explicit grouped continuation options.');const descriptors=Object.getOwnPropertyDescriptors(input),captured={};for(const key of Reflect.ownKeys(input)){const d=descriptors[key];if(typeof key!=='string'||!['domain','adapter','clock','onState','maxRetries','maxDelayMs'].includes(key)||!d.enumerable||!Object.hasOwn(d,'value'))throw Error('Use explicit grouped continuation options.');captured[key]=d.value;}
  const {domain,...options}=captured,q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion;q?.inspect(domain);if(!q||(policy==='prefix'?domain.schema!=='liberpedia-factored-finite-question-v2':domain.schema!=='liberpedia-factored-finite-output-question-v1'||domain.questionPolicy!==policy))throw Error('Use the matching explicitly bound grouped question.');return controller(options,domain,true);
 }
 function outputController({domain,...options},policy){const q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion;q?.inspect(domain);if(!q||domain.schema!=='liberpedia-factored-finite-output-question-v1'||domain.questionPolicy!==policy)throw Error('Use an explicitly bound maintained output question.');return controller(options,domain);}
 function controller({adapter,clock={sleep},onState,maxRetries=3,maxDelayMs=300000},outputDomain,grouped=false){
  const outputMode=outputDomain?.schema==='liberpedia-factored-finite-output-question-v1',preparedKey=grouped?'preparedGroupIds':'preparedCaseIds',unsavedKey=grouped?'unsavedGroupIds':'unsavedCaseIds';
  for(const name of ['inspectState','refresh','prepareNext','runPrepared','saveLocal','cancel'])if(typeof adapter?.[name]!=='function')throw Error('A checkpoint-safe finite adapter is required.');
  if(typeof clock?.sleep!=='function'||!Number.isInteger(maxRetries)||maxRetries<0||maxRetries>5||!Number.isSafeInteger(maxDelayMs)||maxDelayMs<1000||maxDelayMs>3600000)throw Error('Invalid continuation retry limits.');
  let binding=null,status='idle',action=null,reason=null,error=null,retryDelayMs=null,generation=0,active=null,pausing=null,abort=null,destroyed=false,cancelUnsafe=false;
  const getState=()=>freeze(copy({binding,status,action,reason,error,retryDelayMs}));
  function emit(){try{onState?.(getState());}catch{}}
  function read(){const s=copy(adapter.inspectState());
   if(!exact(s,['proposalId','domainId','inputVersion','phase','decision','lookupComplete',preparedKey,unsavedKey,'lastError'])||s.proposalId!==binding.proposalId||s.domainId!==binding.domainId||s.inputVersion!==binding.inputVersion)throw Error('The reviewed finite question changed.');
   if(typeof s.phase!=='string'||typeof s.lookupComplete!=='boolean'||!s.decision||!['answered','missing-evidence','unavailable'].includes(s.decision.state)||(s.decision.state==='answered'&&!(outputMode?[outputDomain.questionPolicy==='transformed-output-inspection-v1'?'outputs-ready':'comparisons-complete']:['prefix-found','prefix-not-found']).includes(s.decision.answer))||Object.keys(s.decision).some(k=>!['state','answer'].includes(k)))throw Error('The finite adapter returned an invalid decision.');
   for(const ids of [s[preparedKey],s[unsavedKey]])if(!Array.isArray(ids)||ids.length>12||new Set(ids).size!==ids.length||ids.some(id=>!HEX.test(id)))throw Error('The finite adapter returned an invalid batch.');
   if(s[unsavedKey].some(id=>!s[preparedKey].includes(id)))throw Error('Local output lost its reviewed preparation.');
   if(s.lastError!==null&&(!s.lastError||typeof s.lastError.message!=='string'||Object.keys(s.lastError).some(k=>!['message','status','code','retryAfterSeconds','retryAt'].includes(k))))throw Error('The finite adapter returned an invalid error.');
   return s;
  }
  const live=token=>!destroyed&&generation===token;
  function pauseState(why,detail=null){status='paused';reason=why;error=detail;action=null;retryDelayMs=null;emit();}
  function errorData(e){return {message:typeof e?.message==='string'?e.message.slice(0,300):'The action could not be completed.',...(Number.isInteger(e?.status)?{status:e.status}:{}),...(typeof e?.code==='string'?{code:e.code}:{}),...(Number.isSafeInteger(e?.retryAfterSeconds)?{retryAfterSeconds:e.retryAfterSeconds}:{}),...(typeof e?.retryAt==='string'?{retryAt:e.retryAt}:{} )};}
  async function perform(name,token){let attempts=0;const before=read(),payload=stable(name==='saveLocal'?before[unsavedKey]:name==='runPrepared'?before[preparedKey]:null);
   while(live(token)){
    action=name;status='running';retryDelayMs=null;emit();
    try{await adapter[name](...(name==='refresh'?[{preserveLocal:true}]:[]));if(!live(token))return false;const s=read();if(s.lastError)throw s.lastError;error=null;return true;}
    catch(e){if(!live(token))return false;let s;try{s=read();}catch(changed){pauseState('question-changed',errorData(changed));return false;}
     const detail=errorData(e);if(detail.code==='daily-quota'){pauseState('daily-quota',detail);return false;}
     if(detail.status!==429||detail.code!=='rate-limited'){pauseState('action-failed',detail);return false;}
     if(s[unsavedKey].length&&name!=='saveLocal'){pauseState('local-output-retained',detail);return false;}
     if(stable(name==='saveLocal'?s[unsavedKey]:name==='runPrepared'?s[preparedKey]:null)!==payload){pauseState('batch-changed',detail);return false;}
     const seconds=detail.retryAfterSeconds;if(!Number.isSafeInteger(seconds)||seconds<1||attempts>=maxRetries){pauseState('rate-limited',detail);return false;}
     const delay=seconds*1000*Math.pow(2,attempts++);if(delay>maxDelayMs){pauseState('rate-limited',detail);return false;}
     status='waiting';error=detail;retryDelayMs=delay;emit();try{await clock.sleep(delay,abort.signal);}catch(waitError){if(live(token))pauseState('retry-interrupted',errorData(waitError));return false;}if(!live(token))return false;
    }
   }return false;
  }
  async function drive(token){let refreshNeeded=true,steps=0;try{while(live(token)){
   if(++steps>20000){pauseState('action-limit');break;}const s=read();
   if(s[unsavedKey].length){if(!await perform('saveLocal',token))break;if(read()[unsavedKey].length){pauseState('local-output-retained');break;}refreshNeeded=true;continue;}
   if(refreshNeeded){if(!await perform('refresh',token))break;refreshNeeded=false;continue;}
   if(s.decision.state==='answered'){status='stopped';reason=s.decision.answer||'answered';action=null;error=null;emit();break;}
   if(!s.lookupComplete||s.decision.state==='unavailable'){pauseState('lookup-incomplete');break;}
   if(s[preparedKey].length){if(!await perform('runPrepared',token))break;const after=read();if(after[preparedKey].length&&!after[unsavedKey].length&&after.decision.state!=='answered'){pauseState('no-local-output');break;}refreshNeeded=!after[unsavedKey].length;continue;}
   if(!await perform('prepareNext',token))break;const prepared=read();if(!prepared[preparedKey].length&&prepared.decision.state!=='answered'){pauseState('no-prepared-work');break;}
  }}catch(e){if(live(token))pauseState('invalid-state',errorData(e));}return getState();}
  function launch(){const token=++generation;abort=new AbortController();status='running';reason=error=retryDelayMs=null;emit();const operation=drive(token);active=operation;operation.finally(()=>{if(active===operation)active=null;});return operation;}
  function start(value){const saved=copy(value);if(!exact(saved,['proposalId','domainId','inputVersion','allowSave',...(grouped?['executionUnit']:[])])||!/^p_[a-f0-9]{64}$/.test(saved.proposalId)||!HEX.test(saved.domainId)||!['raw','reviewed'].includes(saved.inputVersion)||saved.allowSave!==true||grouped&&saved.executionUnit!=='page-group-v1'||outputDomain&&(saved.domainId!==outputDomain.id||saved.inputVersion!==outputDomain.inputVersion))throw Error('Explicit reviewed run-and-save consent is required.');if(destroyed||binding)throw Error('This continuation has already been started.');binding=freeze({...saved,...(outputMode?{questionPolicy:outputDomain.questionPolicy}:{})});return launch();}
  function pause(){if(pausing)return pausing;if(destroyed||!binding)return Promise.resolve(getState());++generation;abort?.abort();status='paused';reason='user-paused';action=null;retryDelayMs=null;emit();cancelUnsafe=true;const operation=(async()=>{try{await adapter.cancel();if(!destroyed)read();cancelUnsafe=false;}catch(e){if(!destroyed){reason='cancellation-failed';error=errorData(e);emit();}}return getState();})();pausing=operation;operation.finally(()=>{if(pausing===operation)pausing=null;});return operation;}
  async function resume(){if(destroyed||!binding)throw Error('The reviewed continuation is unavailable.');if(pausing)await pausing;if(cancelUnsafe){await pause();if(cancelUnsafe)return getState();}if(active&&status!=='paused')return active;if(status!=='paused')return getState();return launch();}
  async function destroy(){if(destroyed)return getState();const cancellation=pause();destroyed=true;++generation;abort?.abort();await cancellation;status='destroyed';action=null;reason='destroyed';emit();return getState();}
  return {start,pause,resume,destroy,getState};
 }
 const api={createController,createOutputController,createInspectionController,createGroupController,createOutputGroupController,createInspectionGroupController};if(node)module.exports=api;else root.FiniteSearchContinuation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
