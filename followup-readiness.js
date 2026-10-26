/* Read-only discovery of saved work for one source-pinned authored recipe. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const E=node?require('./local-experiment.js'):root.LocalExperiment,F=node?require('./record-followups.js'):root.RecordFollowups,Client=node?require('./verified-evidence-client.js'):root.VerifiedEvidenceClient,Ordinary=node?require('./ordinary-prefix-evidence-client.js'):root.OrdinaryPrefixEvidenceClient,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle,C=node?require('./claim-specification.js'):root.ClaimSpecification,J=node?require('./finite-json.js'):root.FiniteJSON;
 const HEX=/^[a-f0-9]{64}$/,ID=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
 const capture=(v,maxBytes=2*1024*1024)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:500000}),same=(a,b)=>E.stable(a)===E.stable(b);
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 async function digest(value,cryptoAPI,raw=false){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(raw?value:E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 function validEndpoint(value,path,pageURL,anchor){try{const u=new URL(value),base=new URL(anchor||value),local=['localhost','127.0.0.1'];return u.origin===base.origin&&!u.username&&!u.password&&!u.search&&!u.hash&&u.pathname==='/'+path&&(u.protocol==='https:'||u.protocol==='http:'&&local.includes(u.hostname)&&local.includes(new URL(pageURL).hostname));}catch{return false;}}
 function createController({record,check,followupId=check?.id,fetcher=root.fetch?.bind(root),config,loadConfig,loadInputs,crypto:cryptoAPI=root.crypto,onState=()=>{},pageURL=root.location?.href||'https://jelliottdev.github.io/research.html'}={}){
  const recordId=record?.id,selected=record?.browser_followups?.filter(item=>item?.id===followupId)||[],recipe=selected.length===1?capture(selected[0],selected[0]?.kind==='finite-settings'?2*1024*1024:512*1024):null;
  let generation=0,destroyed=false,active=false,pending=null,abort=null;
  const live=token=>!destroyed&&generation===token,emit=(token,state)=>{if(live(token))onState(state);};
  async function perform(){
   const token=++generation;abort?.abort();abort=new AbortController();const signal=abort.signal;
   emit(token,{state:'loading'});
   const assertLive=()=>{if(!live(token)||signal.aborted)throw new DOMException('Readiness detached.','AbortError');};
   async function request(url,init={}){assertLive();const response=await fetcher(url,{...init,cache:'no-store',signal:AbortSignal.any([signal,init.signal,AbortSignal.timeout(20000)].filter(Boolean))});assertLive();if(!response.ok)throw Error('Saved work is unavailable.');return response;}
   async function json(url,init,max=2*1024*1024){const value=await Ordinary.read(await request(url,init),{signal});assertLive();return capture(value,max);}
   try{
    if(!recipe||!ID.test(recordId)||recordId.length>100||!ID.test(followupId)||followupId.length>100)throw Error('Invalid authored reference.');
    const settings=capture(config||(loadConfig?await loadConfig({signal}):await json('data/assistant.json')));assertLive();
    const endpoint=settings.localTaskEndpoint,allowed=(value,path)=>validEndpoint(value,path,pageURL,settings.endpoint||endpoint);
    if(!allowed(endpoint,'tasks')||!allowed(settings.recordPlanEndpoint,'record-plans'))throw Error('Saved work is not configured.');
    const bundle=capture(loadInputs?await loadInputs({signal}):await json('data/local-run-inputs.json'));assertLive();
    if(recipe.kind==='finite-settings'){
     const Authored=node?require('./authored-finite-followup.js'):root.AuthoredFiniteFollowup,Finite=node?require('./factored-evidence-client.js'):root.FactoredEvidenceClient;
     if(!Authored||!Finite)throw Error('The source search reader is unavailable.');
     const wire=await json(settings.recordPlanEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({recordId,followupId,includeExisting:true,includeMotivation:true})});assertLive();
     const response=await request('experiments/records/'+recordId+'/record.json',{redirect:'error'}),reader=response.body?.getReader();if(!reader)throw Error('The official source is unavailable.');
     const parts=[];let size=0;try{for(;;){const part=await reader.read();assertLive();if(part.done)break;size+=part.value.byteLength;if(size>2*1024*1024)throw Error('The official source exceeds its bound.');parts.push(part.value);}}catch(error){await reader.cancel().catch(()=>{});throw error;}
     const sourceBytes=new Uint8Array(size);let offset=0;for(const part of parts){sourceBytes.set(part,offset);offset+=part.byteLength;}
     const plan=await Authored.validatePlan(wire,{recordId,followupId},{bundle,sourceBytes,crypto:cryptoAPI,isLive:()=>live(token)&&!signal.aborted});assertLive();
     if(!same(plan.snapshot,recipe))throw Error('The catalogue source changed.');
     const domain=plan.compiled.domain,criterion=domain.criterion,inspection=domain.questionPolicy==='transformed-output-inspection-v1',output=domain.questionPolicy==='language-reference-comparison-v1',prefix=!inspection&&!output&&criterion?.kind==='exact-prefix'&&typeof settings.factoredPrefixSearchEndpoint==='string',route=inspection?'factored-inspection-search':output?'factored-output-search':prefix?'factored-prefix-search':'factored-search',searchEndpoint=settings[{ 'factored-inspection-search':'factoredInspectionSearchEndpoint','factored-output-search':'factoredOutputSearchEndpoint','factored-prefix-search':'factoredPrefixSearchEndpoint','factored-search':'factoredSearchEndpoint'}[route]];
     if(!allowed(searchEndpoint,route))throw Error('Saved search evidence is not configured.');
     const proposalId='p_'+await digest(C.serialize(recipe.card),cryptoAPI,true),scan=(inspection?Finite.createInspectionScan:output?Finite.createOutputScan:Finite.createScan)({proposalId,domain,crypto:cryptoAPI,signal,...(prefix?{evidenceMode:'verified-output-prefix-v1'}:{}),fetchPage:(body,{signal:scanSignal})=>json(searchEndpoint+'/'+proposalId+'/evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,authoredOrigin:plan.origin}),signal:scanSignal},8*1024*1024)});
     let result;do{result=await scan.step();assertLive();}while(result.status!=='complete');
     const proof=result.proof;if(!proof.lookupComplete)throw Error('The saved search lookup is incomplete.');
     const state={state:proof.decision.state==='answered'?(output||inspection?'results':'answered'):'remaining',unit:'cases',remainingCount:proof.remainingCases,totalCases:proof.totalCases,coveredCases:proof.coveredCases,totalPages:domain.pages.length,programCount:domain.programs.length,criterion,domainId:domain.id,origin:plan.origin,lookupComplete:true,...(domain.questionPolicy?{questionPolicy:domain.questionPolicy}:{}),...Object.fromEntries(['matchingCases','usableCases','insufficientCases','runeOutputCases','noRuneCases'].filter(k=>Object.hasOwn(proof,k)).map(k=>[k,proof[k]]))};
     emit(token,state);return live(token)?state:null;
    }
    const official=Inputs.parse(bundle),pins=recipe.inputs,program=F.describeCard(recipe.card);
    if(!exact(pins,['version','alphabet_sha256','pages'])||pins.version!==program.inputVersion||!HEX.test(pins.alphabet_sha256)||!Array.isArray(pins.pages)||!pins.pages.length||pins.pages.length>75||!same(pins.pages.map(p=>p?.id),program.pages)||await digest(official.alphabet,cryptoAPI)!==pins.alphabet_sha256)throw Error('Authored input pins changed.');
    const pages=[];for(const pin of pins.pages){const page=official.pages.get(pin?.id),text=pins.version==='raw'?page?.raw:page?.reviewed_text;if(!exact(pin,['id','text_sha256'])||!HEX.test(pin.text_sha256)||typeof text!=='string'||await digest(text,cryptoAPI,true)!==pin.text_sha256)throw Error('Authored page changed.');pages.push({id:pin.id,text});}assertLive();
    const task=await E.prepare({title:recipe.title,pages,alphabet:official.alphabet,steps:program.steps,criterion:program.criterion},cryptoAPI);assertLive();
    const plan=await json(settings.recordPlanEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({recordId,followupId,includeExisting:true,includeExistingContext:true,includeDerivedPrefixEvidence:true})},8*1024*1024);
    const keys=['state','origin','card','task','inputVersion','control','question','scopeChange','limitation','coverage'],optional=['existingTask','motivation','boundaryComparison','derivedCoverage'];
    if(!exact(plan,[...keys,...optional.filter(k=>Object.hasOwn(plan,k))])||plan.state!=='plan-ready'||!exact(plan.origin,['recordId','followupId','recordSha256','protocolSha256'])||plan.origin.recordId!==recordId||plan.origin.followupId!==followupId||!HEX.test(plan.origin.recordSha256)||plan.origin.protocolSha256!==await digest(recipe,cryptoAPI)||plan.inputVersion!==pins.version||!same(plan.card,recipe.card)||!same(plan.task,task)||!same(plan.control,recipe.control)||plan.question!==recipe.question||plan.scopeChange!==recipe.scope_change||plan.limitation!==recipe.limitation||Object.hasOwn(plan,'boundaryComparison'))throw Error('The current plan differs from its source.');
    const client=Client.create({request,endpoint,validEndpoint:allowed,crypto:cryptoAPI}),coverage=await client.checkCoverage(plan.coverage,{inputVersion:pins.version,isLive:()=>live(token)});assertLive();
    if(!same(coverage.requestedTask,task))throw Error('Coverage changed the requested task.');
    const covered=new Set(coverage.coveredPages),matching=new Set();let complete=!coverage.truncated;
    if(task.criterion.kind==='exact-prefix'){
     const wanted=new Map(task.pages.map(page=>[page.id,page.text]));
     for(const source of client.getSources(coverage))for(const match of source.run.result.matches)if(match.matched&&covered.has(match.page)&&source.task.pages.some(page=>page.id===match.page&&wanted.get(page.id)===page.text))matching.add(match.page);
     if(Object.hasOwn(plan,'derivedCoverage')){
      const canonical='p_'+await digest(C.serialize(recipe.card),cryptoAPI,true);
      const proof=Ordinary.inspect(await Ordinary.verify({proposalId:canonical,card:recipe.card,bundle,requestedTask:task,value:plan.derivedCoverage,isLive:()=>live(token)},cryptoAPI));assertLive();
      proof.proof.coveredPages.forEach(id=>covered.add(id));proof.proof.matchingPages.forEach(id=>matching.add(id));complete=complete&&proof.lookupComplete;
     }else if(coverage.remainingPages.length)throw Error('Earlier-output discovery is missing.');
    }else if(Object.hasOwn(plan,'derivedCoverage'))throw Error('Measurements cannot use a different calculation.');
    const remaining=task.pages.filter(page=>!covered.has(page.id)).length,totalPages=task.pages.length;
    let state;if(task.criterion.kind==='exact-prefix'&&matching.size)state={state:'answered',totalPages};
    else if(!remaining)state={state:task.criterion.kind==='exact-prefix'?'answered':'results',totalPages};
    else if(complete)state={state:'remaining',remainingCount:remaining,totalPages};
    else throw Error('Saved-work discovery is incomplete.');
    emit(token,state);return live(token)?state:null;
   }catch{const state={state:'unavailable'};emit(token,state);return live(token)?state:null;}
  }
  return {activate(){if(destroyed)return Promise.resolve(null);if(active)return pending;active=true;pending=perform();return pending;},retry(){if(destroyed)return Promise.resolve(null);active=true;pending=perform();return pending;},destroy(){destroyed=true;generation++;abort?.abort();}};
 }
 const api={createController};if(node)module.exports=api;else root.FollowupReadiness=api;
})(typeof globalThis!=='undefined'?globalThis:this);
