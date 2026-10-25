/* Read-only current answers for maintained questions. Nothing runs until activated. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const E=node?require('./local-experiment.js'):root.LocalExperiment,Model=node?require('./record-question-model.js'):root.RecordQuestionModel,Client=node?require('./verified-evidence-client.js'):root.VerifiedEvidenceClient,Q=node?require('./question-evidence.js'):root.QuestionEvidence,D=node?require('./question-decisions.js'):root.QuestionDecisions,F=node?require('./research-family.js'):root.ResearchFamily,FQ=node?require('./family-question-evidence.js'):root.FamilyQuestionEvidence,V=node?require('./task-variants.js'):root.TaskVariants;
 const Followups=node?require('./record-followups.js'):root.RecordFollowups;
 const clone=v=>JSON.parse(E.stable(v));
 async function digest(value,cryptoAPI,raw=false){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(raw?value:E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 function validEndpoint(value,path,pageURL,anchor){
  try{const url=new URL(value),base=new URL(anchor||value),local=['localhost','127.0.0.1'];return url.origin===base.origin&&!url.username&&!url.password&&!url.search&&!url.hash&&url.pathname==='/'+path&&(url.protocol==='https:'||url.protocol==='http:'&&local.includes(url.hostname)&&local.includes(new URL(pageURL).hostname));}catch{return false;}
 }
 function createController({record,questionId,fetcher=root.fetch?.bind(root),config,loadConfig,loadInputs,crypto:cryptoAPI=root.crypto,onState=()=>{},pageURL=root.location?.href||'https://jelliottdev.github.io/library.html'}={}){
  const captured=clone(record),reference=Model.protocolReference(captured,questionId);let generation=0,destroyed=false,active=false,abort=null,pending=null;
  const live=token=>!destroyed&&generation===token;
  function emit(token,value){if(live(token))onState(value);}
  async function perform(){
   const token=++generation;abort?.abort();abort=new AbortController();const signal=abort.signal;
   emit(token,{state:'loading'});
   async function request(url,init={}){
    if(!live(token))throw new DOMException('Question detached.','AbortError');
    const response=await fetcher(url,{...init,signal:AbortSignal.any([signal,init.signal,AbortSignal.timeout(20000)].filter(Boolean)),cache:'no-store'});
    if(!response.ok)throw Error('Current evidence could not be checked. Please retry.');return response;
   }
   async function json(url,init){const response=await request(url,init),text=await response.text();if(new TextEncoder().encode(text).length>2*1024*1024)throw Error('The current evidence exceeds its bound.');return JSON.parse(text);}
   try{
    if(!reference)throw Error('This question has no maintained live evidence protocol.');
    const settings=clone(config||(loadConfig?await loadConfig({signal}):await json('data/assistant.json')));
    if(!live(token))return;
    const endpoint=settings.localTaskEndpoint,allowed=(value,path)=>validEndpoint(value,path,pageURL,settings.endpoint||endpoint);
    if(!allowed(endpoint,'tasks'))throw Error('Current evidence is not available here.');
    const bundle=clone(loadInputs?await loadInputs({signal}):await json('data/local-run-inputs.json'));
    if(!live(token))return;
    let decision;
    if(reference.id==='deor-warning-opening'){
     const snapshot=await F.snapshot(bundle,cryptoAPI),wire=await json(new URL(endpoint).origin+'/families/'+reference.familyId+'/question'),unpacked=FQ.unpack(wire);
     if(unpacked.familyId!==snapshot.id||unpacked.revision!==snapshot.revision)throw Error('Current evidence uses different manuscript inputs.');
     const proof=await FQ.summarize({snapshot,bundle,sources:unpacked.sources,lookupComplete:unpacked.lookupComplete},cryptoAPI);decision=await D.finite(proof,cryptoAPI);
    }else{
     if(!allowed(settings.recordPlanEndpoint,'record-plans'))throw Error('Current question plans are not available here.');
     const recipe=captured.browser_followups.find(item=>item.id===reference.followupId),pins=reference.inputs;
     if(bundle.schema!=='liberpedia-local-inputs-v1'||!Array.isArray(bundle.alphabet)||!Array.isArray(bundle.pages)||await digest(bundle.alphabet,cryptoAPI)!==pins.alphabet_sha256)throw Error('The question alphabet changed.');
     const pages=[];for(const pin of pins.pages){const found=bundle.pages.filter(page=>page.id===pin.id);if(found.length!==1)throw Error('The question page is unavailable.');const text=pins.version==='raw'?found[0].raw:found[0].reviewed_text;if(typeof text!=='string'||await digest(text,cryptoAPI,true)!==pin.text_sha256)throw Error('The question page changed.');pages.push({id:pin.id,text});}
     let steps=[];
     if(reference.id==='fixed-program-prefix'){
      const program=Followups.describeCard(recipe.card);
      if(program.inputVersion!==pins.version||program.criterion.kind!=='exact-prefix'||E.stable(program.pages)!==E.stable(pins.pages.map(page=>page.id))||E.stable(program.criterion)!==E.stable(recipe.card.rules.evaluation.value))throw Error('The compiled question changed its declared scope or prefix.');
      steps=program.steps;
     }
     const task=await E.prepare({title:recipe.title,pages,alphabet:bundle.alphabet,steps,criterion:recipe.card.rules.evaluation.value},cryptoAPI),plan=await json(settings.recordPlanEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({recordId:captured.id,followupId:reference.followupId,includeExisting:true,...(reference.id==='word-boundary-sensitivity'?{includeBoundaryComparison:true}:{})})});
     if(plan.state!=='plan-ready'||plan.origin?.recordId!==captured.id||plan.origin?.followupId!==reference.followupId||plan.origin?.protocolSha256!==await digest(recipe,cryptoAPI)||plan.inputVersion!==pins.version||E.stable(plan.task)!==E.stable(task))throw Error('The current question plan changed its definition or inputs.');
     if(reference.id==='fixed-program-prefix'){
      if(!plan.coverage||plan.coverageUnavailable===true||Object.hasOwn(plan,'boundaryComparison'))throw Error('The current opening evidence could not be checked.');
      const client=Client.create({request,endpoint,validEndpoint:allowed,crypto:cryptoAPI}),coverage=await client.checkCoverage(plan.coverage,{inputVersion:pins.version,isLive:()=>live(token)});
      if(E.stable(coverage.requestedTask)!==E.stable(task))throw Error('The current evidence changed the opening scope.');
      const proof=await Q.summarize(task,pins.version,client.getSources(coverage),cryptoAPI);decision=await D.prefix({task,inputVersion:pins.version,proof,lookupComplete:!coverage.truncated},cryptoAPI);
     }else{
     const companion=plan.boundaryComparison;if(!companion?.task||!plan.coverage||!companion.coverage||companion.coverageUnavailable===true)throw Error('Both sides of the current comparison could not be checked.');
     await V.validate(task,companion.task,cryptoAPI);
     const client=Client.create({request,endpoint,validEndpoint:allowed,crypto:cryptoAPI}),left=await client.checkCoverage(plan.coverage,{inputVersion:pins.version,isLive:()=>live(token)}),right=await client.checkCoverage(companion.coverage,{inputVersion:pins.version,isLive:()=>live(token)});
     if(E.stable(left.requestedTask)!==E.stable(task)||E.stable(right.requestedTask)!==E.stable(companion.task))throw Error('The current evidence changed the question scope.');
     const a=await Q.summarize(task,pins.version,client.getSources(left),cryptoAPI),b=await Q.summarize(companion.task,pins.version,client.getSources(right),cryptoAPI);
     decision=await D.boundary({task,otherTask:companion.task,inputVersion:pins.version,left:a,right:b,lookupComplete:!left.truncated&&!right.truncated},cryptoAPI);
     }
    }
    emit(token,{state:decision.state,decision});return decision;
   }catch(error){if(live(token))emit(token,{state:'unavailable',error:'Current evidence could not be verified. Retry to check it again.'});return null;}
  }
  function activate(){if(destroyed)return Promise.resolve(null);if(active)return pending;active=true;pending=perform();return pending;}
  function retry(){if(destroyed)return Promise.resolve(null);active=true;pending=perform();return pending;}
  function destroy(){destroyed=true;generation++;abort?.abort();}
  return {activate,retry,destroy};
 }
 const api={createController};if(node)module.exports=api;else root.RecordQuestionLive=api;
})(typeof globalThis!=='undefined'?globalThis:this);
