/* Reviewed published follow-ups: inspect first, explicitly create, never run at load. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,E=node?require('./local-experiment.js'):root.LocalExperiment,Control=node?require('./local-control.js'):root.LocalControl;
 const Protocols=node?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const HEX=/^[a-f0-9]{64}$/,SLUG='[a-z0-9]+(?:-[a-z0-9]+)*',ID=new RegExp('^'+SLUG+'$');
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const clone=v=>JSON.parse(JSON.stringify(v)),same=(a,b)=>E.stable(a)===E.stable(b);
 const text=(v,max=1200)=>typeof v==='string'&&v.trim()&&Array.from(v).length<=max;
 function reference(hash){if(typeof hash!=='string')return null;const m=new RegExp('^#record=('+SLUG+')&followup=('+SLUG+')$').exec(hash||'');return m&&m[1].length<=100&&m[2].length<=100?{kind:'record',recordId:m[1],followupId:m[2],id:m[1]+'/'+m[2]}:null;}
 function validOrigin(v){return exact(v,['recordId','followupId','recordSha256','protocolSha256'])&&[v.recordId,v.followupId].every(id=>typeof id==='string'&&id.length<=100&&ID.test(id))&&HEX.test(v.recordSha256)&&HEX.test(v.protocolSha256);}
 async function digest(value,cryptoAPI){return Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(value))),b=>b.toString(16).padStart(2,'0')).join('');}
 async function validateOrigins(origins=[],plan,cryptoAPI=root.crypto){
  if(!Array.isArray(origins)||origins.length>10)throw Error('The published origin metadata is invalid.');
  await E.checkIdentity(plan,cryptoAPI);const seen=new Set(),runes=new Set(plan.alphabet.map(v=>v.rune));
  for(const item of origins){
   if(!exact(item,['origin','control','question','scopeChange','limitation',...(Object.hasOwn(item||{},'scopeRelation')?['scopeRelation']:[])])||!validOrigin(item.origin)||!['question','scopeChange','limitation'].every(k=>text(item[k])))throw Error('The published origin metadata is invalid.');
   if(Object.hasOwn(item,'scopeRelation')){const relation=item.scopeRelation,ids=/^(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))$/;if(!exact(relation,['kind','declaredPages','remainingPages'])||relation.kind!=='remaining-pages'||!Array.isArray(relation.declaredPages)||!Array.isArray(relation.remainingPages)||!relation.remainingPages.length||relation.declaredPages.length>75||relation.declaredPages.length<=relation.remainingPages.length||[relation.declaredPages,relation.remainingPages].some(values=>values.some(id=>typeof id!=='string'||!ids.test(id))||new Set(values).size!==values.length||!same(values,[...values].sort()))||!same(relation.remainingPages,plan.pages.map(page=>page.id))||relation.remainingPages.some(id=>!relation.declaredPages.includes(id)))throw Error('The published remaining-page relation is invalid.');}
   const key=E.stable(item.origin);if(seen.has(key))throw Error('A published origin is repeated.');seen.add(key);
   const control=item.control;if(!exact(control,['label','task','expected_result_sha256'])||!text(control.label,300)||!HEX.test(control.expected_result_sha256))throw Error('The synthetic control metadata is invalid.');
   await E.checkIdentity(control.task,cryptoAPI);
   if(control.task.pages.length!==1||Array.from(control.task.pages[0].text).filter(ch=>runes.has(ch)).length>4096||!Control.compatible(control.task,plan))throw Error('The synthetic control does not match this bounded experiment.');
  }
  return clone(origins);
 }
 function cardSnapshot(card){
  let binary='';for(const byte of new TextEncoder().encode(JSON.stringify(card)))binary+=String.fromCharCode(byte);
  const imported=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''));
  const confirmed=C.confirm(imported.draft,{id:'reviewed-followup',at:'2000-01-01T00:00:00.000Z'});
  if(!same(H.cardData(confirmed),card))throw Error('The published idea card is not canonical.');return confirmed;
 }
 function cardProgram(card){
  const snapshot=cardSnapshot(card),draft=snapshot,rules=draft.rules,known=k=>rules[k].status==='specified';
  if(draft.unresolved.length||draft.method.status!=='specified'||draft.scope.status!=='specified'||!exact(draft.scope.value,['pages'])||!Array.isArray(draft.scope.value.pages)||!draft.scope.value.pages.length||Object.values(rules).some(v=>v.status==='unrestricted'))throw Error('The published idea is not a fixed complete-page experiment.');
  if(!known('inputVersion')||!['raw','reviewed'].includes(rules.inputVersion.value)||!known('representation')||rules.representation.value!=='GP29'||!known('evaluation')||!(rules.evaluation.value==='measurement'||rules.evaluation.value?.kind==='exact-prefix'||Protocols.identify(rules.evaluation.value)))throw Error('The published input and evaluation must be explicit.');
  for(const k of ['searchBounds','searchProtocol','exceptionalCases'])if(known(k))throw Error('The published conditions need an execution adapter.');
  if(known('unmapped')&&rules.unmapped.value!=='preserve'||known('wordBoundaries')&&rules.wordBoundaries.value!=='preserve')throw Error('The published separator rule needs an adapter.');
  const measurementIds=new Set(Protocols.list().map(d=>d.operation.id));
  if(draft.method.value.operations.some(op=>measurementIds.has(op.id))){
   const operations=draft.method.value.operations,op=operations[0],evaluation=rules.evaluation.value,withoutFamily={...op};delete withoutFamily.declaredFamilyId;
   if(Object.hasOwn(op,'declaredFamilyId')&&(typeof op.declaredFamilyId!=='string'||!Object.hasOwn(C.METHOD_FAMILIES,op.declaredFamilyId)))throw Error('The published method family is not in the maintained vocabulary.');
   const expected=Protocols.fromOperation(withoutFamily);
   if(operations.length!==1||!expected||!Protocols.identify(evaluation)||!same(evaluation,expected)||['boundaryMode','reset','initialState'].some(known)||rules.wordBoundaries.status==='not_applicable')throw Error('The published measurement settings and evaluation must agree.');
   return {snapshot,steps:[],pages:draft.scope.value.pages,inputVersion:rules.inputVersion.value,criterion:evaluation};
  }
  if(rules.evaluation.value!=='measurement'&&(rules.evaluation.value.kind!=='exact-prefix'||!exact(rules.evaluation.value,['kind','values'])))throw Error('The published transformation needs an explicit evaluation.');
  const modes={vigenere:'repeat',repeating_key:'repeat',plaintext_autokey:'plaintext-autokey',ciphertext_autokey:'ciphertext-autokey'};let reversed=false,cumulative=false,resetUsed=false;
  const steps=draft.method.value.operations.map(op=>{
   const allowed=['id','label','declaredFamilyId',...(op.id==='affine'?['a','b']:op.id==='reverse_runes'?['unit']:op.id==='cumulative_difference'?['reset']:op.id==='interrupted_repeating_key'?['key','direction','reset','interrupts']:(op.id==='finite_key'||Object.hasOwn(modes,op.id))?['key','direction','reset']:[])];
   if(Object.keys(op).some(k=>!allowed.includes(k)))throw Error('The published operation has unsupported parameters.');
   if(op.id==='reverse_row_runes'||op.id==='reverse_runes'){
    reversed=true;let unit=op.id==='reverse_row_runes'?(known('boundaryMode')&&rules.boundaryMode.value==='within_words'?'word':'line'):op.unit;
    if(known('boundaryMode')&&(unit==='page'||rules.boundaryMode.value!==(unit==='word'?'within_words':'fixed_spaces'))||op.id==='reverse_row_runes'&&known('wordBoundaries')&&!known('boundaryMode'))throw Error('The published reversal boundary conflicts.');
    const labels=op.id==='reverse_row_runes'?['Reverse rune order within rows','Reverse rune order within each row']:['Reverse rune order within each '+unit];if(op.label!==undefined&&!labels.includes(op.label))throw Error('The published reversal wording is unsupported.');return {op:'reverse',unit};
   }
   if(op.id==='affine'){if(op.label!==undefined&&!['Affine','Affine substitution'].includes(op.label))throw Error('The published affine wording is unsupported.');return {op:'affine',a:op.a,b:op.b};}
   if(op.id==='cumulative_difference'||op.id==='finite_key'||op.id==='interrupted_repeating_key'||Object.hasOwn(modes,op.id)){
    resetUsed=true;if(rules.reset.status==='not_applicable'||known('reset')&&rules.reset.value!==op.reset)throw Error('The published reset conflicts.');
    if(op.id==='cumulative_difference'){cumulative=true;if(op.label!==undefined&&op.label!=='Cumulative difference'||rules.initialState.status==='not_applicable'||known('initialState')&&rules.initialState.value!==0)throw Error('The published initial state conflicts.');return {op:'cumulative-difference',reset:op.reset};}
    if(op.id==='interrupted_repeating_key'){if(op.label!=='Interrupted repeating key')throw Error('The published interrupted-key wording is unsupported.');return {op:'interrupted-keyed-shift',key:op.key,direction:op.direction,reset:op.reset,interrupts:op.interrupts};}
    if(op.id==='finite_key'){if(op.label!==undefined&&op.label!=='Finite key stream')throw Error('The published finite stream wording is unsupported.');return {op:'finite-shift',key:op.key,direction:op.direction,reset:op.reset};}
    const labels={vigenere:['Vigenere','Vigenère'],repeating_key:['Repeating key','Repeating-key','Vigenere','Vigenère'],plaintext_autokey:['Plaintext autokey','Plaintext-autokey'],ciphertext_autokey:['Ciphertext autokey','Ciphertext-autokey']};if(op.label!==undefined&&!labels[op.id].includes(op.label))throw Error('The published keyed wording is unsupported.');return {op:'keyed-shift',key:op.key,mode:modes[op.id],direction:op.direction,reset:op.reset};
   }
   throw Error('The published method needs a supported adapter.');
  });
  if(known('boundaryMode')&&!reversed||known('reset')&&!resetUsed||known('initialState')&&!cumulative)throw Error('A published condition is not represented by the plan.');
  return {snapshot,steps,pages:draft.scope.value.pages,inputVersion:rules.inputVersion.value,criterion:rules.evaluation.value==='measurement'?{kind:'measurement'}:rules.evaluation.value};
 }
 async function validatePlan(value,ref,cryptoAPI){
  if(!exact(value,['state','origin','card','task','inputVersion','control','question','scopeChange','limitation',...(value&&Object.hasOwn(value,'existingTask')?['existingTask']:[]),...(value&&Object.hasOwn(value,'coverage')?['coverage']:[]),...(value&&Object.hasOwn(value,'boundaryComparison')?['boundaryComparison']:[]),...(value&&Object.hasOwn(value,'derivedCoverage')?['derivedCoverage']:[])])||value.state!=='plan-ready'||value.origin?.recordId!==ref.recordId||value.origin?.followupId!==ref.followupId)throw Error('The reviewed plan belongs to another published follow-up.');
  if(Object.hasOwn(value,'existingTask')&&(!exact(value.existingTask,['id','state','proposalId'])||typeof value.existingTask.proposalId!=='string'||!/^p_[a-f0-9]{64}$/.test(value.existingTask.proposalId)||!HEX.test(value.existingTask.id)||value.existingTask.id!==value.task?.taskId||!['not-run','results-verified'].includes(value.existingTask.state)))throw Error('The existing experiment reference is invalid.');
  if(value.existingTask&&value.existingTask.proposalId!=='p_'+await digest(C.serialize(value.card),cryptoAPI))throw Error('The existing check does not belong to this exact original question.');
  const program=cardProgram(value.card);await E.checkIdentity(value.task,cryptoAPI);
  if(!same(program.steps,value.task.steps)||!same(program.pages,value.task.pages.map(p=>p.id))||program.inputVersion!==value.inputVersion||!same(program.criterion,value.task.criterion))throw Error('The reviewed plan does not match its idea card.');
  await validateOrigins([{origin:value.origin,control:value.control,question:value.question,scopeChange:value.scopeChange,limitation:value.limitation}],value.task,cryptoAPI);return clone(value);
 }
 function createWorkspace(doc,host,options){
  const {reference:ref,config,request,validEndpoint,crypto:cryptoAPI=root.crypto,planHTML,isLive=()=>true,onCreated,onRemaining,onCancel,reviewHTML=planHTML,projection,checkedCoverage,coverageHTML,checkBoundaryComparison,bindAuthoredReuse,checkAuthoredReuse,checkAuthoredPrefixReuse,runAuthoredRemainder}=options;
  let dead=false,version=0,plan=null,busy=false,intent=null,reuseCleanup=null;const controller=new AbortController(),live=token=>!dead&&version===token&&isLive(),get=id=>doc.getElementById(id),set=(id,value)=>{const el=get(id);if(el)el.textContent=value;};
  const endpoint=(value,path)=>typeof value==='string'&&validEndpoint(value,path);
  async function json(url,body,timeout=25000){const response=await request(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal},timeout),reader=node?require('./ordinary-prefix-evidence-client.js'):root.OrdinaryPrefixEvidenceClient,value=reader?await reader.read(response,{signal:controller.signal}):await response.json();if(!response.ok)throw Error(text(value?.error,1200)?value.error:text(value?.reason,1200)?value.reason:'The request could not be completed. Please retry.');return value;}
  const actionLabel=()=>plan?.verifiedAuthoredReuse?(plan.verifiedAuthoredReuse.coveredPages.length?'Run remaining '+plan.verifiedAuthoredReuse.remainingPages.length+' '+(plan.verifiedAuthoredReuse.remainingPages.length===1?'page':'pages'):'Run check'):plan?.verifiedCoverage?'Review '+plan.verifiedCoverage.remainingPages.length+' unchecked '+(plan.verifiedCoverage.remainingPages.length===1?'page':'pages'):'Run check';
  function status(message='',error=''){set('followup-status',message);set('followup-error',error);const button=get('create-followup');if(button){button.disabled=busy;button.textContent=busy?(plan?.verifiedCoverage?'Opening remaining work…':'Starting your check…'):actionLabel();}const companion=get('review-companion');if(companion){companion.disabled=busy;companion.textContent=busy?'Opening remaining comparison…':'Review remaining comparison';}const retry=get('retry-companion');if(retry){retry.disabled=busy;retry.textContent=busy?'Checking comparison…':'Retry comparison';}const cancel=get('cancel-followup');if(cancel)cancel.hidden=!busy;}
  function cleanupReuse(){if(reuseCleanup){const cleanup=reuseCleanup;reuseCleanup=null;cleanup();}}
  function draw(){
   cleanupReuse();
   const reused=plan.verifiedCoverage,prefix=plan.verifiedAuthoredReuse,comparison=plan.verifiedBoundaryComparison,complete=!!prefix?.answered||!!comparison?.complete||reused&&!reused.remainingPages.length,existing=reused||prefix?null:plan.existingTask;
   const header='<nav class="run-links"><a href="research.html?v=record-panel-20261024">Back to research map</a><a href="library.html?v=record-panel-20261024#/experiment/'+esc(ref.recordId)+'">Source experiment</a></nav><h1>'+esc(plan.task.title)+'</h1><p>'+esc(plan.question)+'</p>';
   let body;
   if(prefix){
    body=prefix.html+(!prefix.answered&&prefix.lookupComplete?'<section class="reviewed-check">'+reviewHTML(plan.remainingTask,plan.inputVersion)+'<div class="run-actions"><button id="create-followup" class="primary">'+actionLabel()+'</button><button id="cancel-followup" hidden>Cancel</button></div><p class="small">Runs on this device. Results are saved only when you choose to save them.</p></section>':!prefix.answered?'<p class="notice">Saved output could not be checked completely. Retry before starting more work.</p><button id="retry-prefix-reuse">Retry saved output</button>':'')+(prefix.afterReviewHTML||'')+'<details class="experiment-details"><summary>Original published plan</summary>'+planHTML(plan.task,plan.inputVersion)+'<p>'+esc(plan.scopeChange)+'</p><p>Known-answer check: '+esc(plan.control.label)+'. A failed check stops the run.</p><p>'+esc(plan.limitation)+'</p></details>';
   }else if(reused){
    body=(comparison?'<details class="experiment-details"><summary>Source calculations</summary>'+coverageHTML(reused)+'</details>':coverageHTML(reused))+(complete?(comparison?'':'<p class="small">'+esc(plan.limitation)+'</p>'):'<button id="create-followup" class="primary">'+actionLabel()+'</button><p class="small">Keep this question and review a new plan covering only unchecked pages.</p><details class="experiment-details"><summary>Original published plan</summary><p>'+esc(plan.scopeChange)+'</p>'+planHTML(plan.task,plan.inputVersion)+'<p class="small">'+esc(plan.limitation)+'</p></details>');
   }else{
    const selectedHref=existing?((node?require('./task-question-context.js'):root.TaskQuestionContext)?.href?.(existing.id,existing.proposalId)||'#task='+existing.id+'&idea='+existing.proposalId):null;
    const open=existing?'<p class="notice">'+(existing.state==='results-verified'?'A verified computation is already saved.':'This experiment already exists. No saved computation yet.')+'</p><div class="run-actions"><a class="button primary" id="open-followup" href="run.html'+selectedHref+'">'+(existing.state==='results-verified'?'View saved result':'Continue check')+'</a></div>':'';
    body=open+'<section class="reviewed-check">'+reviewHTML(plan.task,plan.inputVersion)+(existing?'':'<div class="run-actions"><button id="create-followup" class="primary">Run check</button><button id="cancel-followup" hidden>Cancel</button></div><p class="small">Runs on this device. Results are saved only when you choose to save them.</p>')+'</section><details class="experiment-details"><summary>Settings and known-answer check</summary>'+planHTML(plan.task,plan.inputVersion)+'<p>'+esc(plan.scopeChange)+'</p><p>Known-answer check: '+esc(plan.control.label)+'. A failed check stops the run.</p><p>'+esc(plan.limitation)+'</p></details>';
   }
   const comparisonHTML=comparison?comparison.html+(comparison.nextCard?'<button id="review-companion" class="primary">Review remaining comparison</button>':''):plan.boundaryComparisonError?'<p class="notice">The boundary comparison could not be checked. The original experiment is still available.</p><button id="retry-companion">Retry comparison</button>':'',deferComparison=!!comparison&&!comparison.complete&&!!prefix&&!prefix.answered;
   host.innerHTML=header+(deferComparison?'':comparisonHTML)+body+(deferComparison?comparisonHTML:'')+'<p id="followup-status" class="notice" role="status"></p><p id="followup-error" class="error" role="alert"></p>';const button=get('create-followup');if(button)button.onclick=create;const cancel=get('cancel-followup');if(cancel)cancel.onclick=()=>{if(typeof onCancel==='function')onCancel();};const companion=get('review-companion');if(companion)companion.onclick=reviewCompanion;const retry=get('retry-companion');if(retry)retry.onclick=()=>{if(!busy) return load(true);};const retryPrefix=get('retry-prefix-reuse');if(retryPrefix)retryPrefix.onclick=()=>{if(!busy)return load();};if(plan.verifiedAuthoredReuse&&typeof bindAuthoredReuse==='function'){const cleanup=bindAuthoredReuse(plan.verifiedAuthoredReuse,host);if(typeof cleanup==='function')reuseCleanup=cleanup;}
  }
  async function load(preserve=false){cleanupReuse();const previous=preserve===true?plan:null,token=++version;if(previous){busy=true;status('Checking the saved comparison…');}else host.innerHTML='<h1>Published follow-up</h1><p role="status">Loading the reviewed plan…</p>';try{
   if(!ref||!endpoint(config?.recordPlanEndpoint,'record-plans'))throw Error('Published follow-up plans are not available here yet.');
   const checked=await validatePlan(await json(config.recordPlanEndpoint,{recordId:ref.recordId,followupId:ref.followupId,includeExisting:true,includeExistingContext:true,includeBoundaryComparison:true,...((typeof checkAuthoredReuse==='function'||typeof checkAuthoredPrefixReuse==='function')?{includeDerivedPrefixEvidence:true}:{})}),ref,cryptoAPI);if(!live(token))return;
   const reuseChecker=['measurement','word-affine-count','word-prime-sums','exact-prefix'].includes(checked.task.criterion.kind)&&typeof checkAuthoredReuse==='function'?checkAuthoredReuse:checked.task.criterion.kind==='exact-prefix'&&typeof checkAuthoredPrefixReuse==='function'?checkAuthoredPrefixReuse:null;
   if(Object.hasOwn(checked,'coverage')){
    if(typeof checkedCoverage!=='function'||typeof coverageHTML!=='function')throw Error('Saved evidence could not be checked. Reload before starting new work.');
    const reused=await checkedCoverage(checked.coverage,checked.inputVersion);if(!live(token))return;
    if(!Array.isArray(reused?.coveredPages)||reused.inputVersion!==checked.inputVersion||!same(reused.requestedTask,checked.task))throw Error('The saved evidence does not describe this exact published follow-up.');
    if(!reuseChecker&&reused.truncated===true&&reused.remainingPages.length)throw Error('Saved evidence is incomplete. Reload before preparing remaining work.');
    checked.originalVerifiedCoverage=reused;
    if(reused.coveredPages.length){if(!reuseChecker&&reused.remainingPages.length&&typeof onRemaining!=='function')throw Error('The remaining-page review could not be opened. Please reload.');checked.verifiedCoverage=reused;}
   }
   if(Object.hasOwn(checked,'derivedCoverage')&&(checked.task.criterion.kind!=='exact-prefix'||!reuseChecker))throw Error('The earlier published output verifier is unavailable.');
   if(reuseChecker){
    const reused=await reuseChecker(checked);if(!live(token))return;const ids=checked.task.pages.map(page=>page.id),validList=values=>Array.isArray(values)&&new Set(values).size===values.length&&same(values,ids.filter(id=>values.includes(id)));
    if(!reused||!same(reused.requestedTask,checked.task)||reused.inputVersion!==checked.inputVersion||typeof reused.html!=='string'||!reused.html.trim()||Object.hasOwn(reused,'afterReviewHTML')&&typeof reused.afterReviewHTML!=='string'||typeof reused.lookupComplete!=='boolean'||!validList(reused.coveredPages)||!validList(reused.remainingPages)||!validList(reused.matchingPages)||reused.coveredPages.some(id=>reused.remainingPages.includes(id))||!same(ids,ids.filter(id=>reused.coveredPages.includes(id)||reused.remainingPages.includes(id)))||reused.matchingPages.some(id=>!reused.coveredPages.includes(id))||(checked.task.criterion.kind!=='exact-prefix'&&reused.matchingPages.length>0)||reused.answered!==((checked.task.criterion.kind==='exact-prefix'&&reused.matchingPages.length>0)||reused.remainingPages.length===0))throw Error('The published output proof changed the exact declared question.');
    checked.verifiedAuthoredReuse=reused;if(checked.task.criterion.kind==='exact-prefix')checked.verifiedPrefixReuse=reused;
    if(!reused.answered&&reused.lookupComplete){if(typeof runAuthoredRemainder!=='function')throw Error('The remaining published check could not be started. Reload before running.');checked.remainingTask=await E.prepare({...checked.task,pages:checked.task.pages.filter(page=>reused.remainingPages.includes(page.id))},cryptoAPI);if(!live(token))return;}
   }
   if(Object.hasOwn(checked,'boundaryComparison'))try{
    if(typeof checkBoundaryComparison!=='function')throw Error('The boundary comparison verifier is unavailable.');
    const compared=await checkBoundaryComparison(checked.task,checked.inputVersion,checked.originalVerifiedCoverage||null,checked.boundaryComparison);if(!live(token))return;
    if(!exact(compared,['html','complete',...(compared&&Object.hasOwn(compared,'nextCard')?['nextCard']:[])])||typeof compared.html!=='string'||!compared.html.trim()||typeof compared.complete!=='boolean')throw Error('The boundary comparison view is invalid.');
    if(Object.hasOwn(compared,'nextCard')){
     const original=checked.originalVerifiedCoverage,companion=checked.boundaryComparison,program=cardProgram(compared.nextCard);
     if(compared.complete||!original?.coveredPages.length||original.remainingPages.length||!companion.coverage?.remainingPages?.length||companion.coverage.truncated!==false||companion.coverageUnavailable===true||typeof onRemaining!=='function'||program.inputVersion!==checked.inputVersion||!same(program.pages,companion.task.pages.map(p=>p.id))||!same(program.steps,companion.task.steps)||!same(program.criterion,companion.task.criterion))throw Error('The next comparison card does not match the exact remaining comparison.');
    }
    checked.verifiedBoundaryComparison=clone(compared);
   }catch{if(!live(token))return;checked.boundaryComparisonError=true;}
   plan=checked;draw();
  }catch(error){if(!live(token))return;if(previous){plan=previous;plan.boundaryComparisonError=true;delete plan.verifiedBoundaryComparison;draw();status('',error.message);}else{host.innerHTML='<h1>Follow-up unavailable</h1><p class="error" role="alert">'+esc(error.message)+'</p><button id="retry-followup">Retry</button><p><a href="library.html?v=record-panel-20261024#/experiment/'+esc(ref.recordId)+'">Read the source experiment</a></p>';get('retry-followup').onclick=()=>load();}}finally{if(previous&&live(token)){busy=false;status(get('followup-status')?.textContent||'',get('followup-error')?.textContent||'');}}}
  async function saveIdeaCard(card,key,token){
   for(const [name,path]of [['proposalEndpoint','proposals'],['researchIdeaEndpoint','ideas']])if(!endpoint(config?.[name],path))throw Error('Saving reviewed comparisons is not available here yet.');
   if(!intent||intent.key!==key){const snapshot=C.confirm(cardSnapshot(card),{id:cryptoAPI.randomUUID(),at:new Date().toISOString()});intent={key,requestId:cryptoAPI.randomUUID(),fragment:H.encode(snapshot),proposalId:'p_'+await digest(C.serialize(H.cardData(snapshot)),cryptoAPI)};}
   if(!live(token))return null;const created=await json(config.proposalEndpoint,{requestId:intent.requestId,fragment:intent.fragment});if(!live(token))return null;
   if(created.id!==intent.proposalId||!['received','already_received'].includes(created.status)||!Number.isFinite(Date.parse(created.receivedAt)))throw Error('The saved idea receipt does not match this card.');
   const idea=await json(config.researchIdeaEndpoint,{proposalId:intent.proposalId});if(!live(token))return null;if(idea.id!==intent.proposalId||!same(idea.card,card))throw Error('The shared research entry does not match this card.');
   return intent.proposalId;
  }
  async function reviewCompanion(){
   const card=plan?.verifiedBoundaryComparison?.nextCard;if(!card||busy||typeof onRemaining!=='function')return;const token=version;busy=true;status('Saving the comparison question…');
   try{const id=await saveIdeaCard(card,'boundary:'+E.stable(card),token);if(!id||!live(token))return;status('Comparison question saved. Opening the unchecked pages for review.');onRemaining(id);}
   catch(error){if(live(token))status('',error.message);}finally{if(live(token)){busy=false;const button=get('review-companion');if(button){button.disabled=false;button.textContent='Review remaining comparison';}}}
  }
  async function create(){if(plan?.verifiedAuthoredReuse&&(plan.verifiedAuthoredReuse.answered||!plan.verifiedAuthoredReuse.lookupComplete))return;if(!plan||plan.verifiedBoundaryComparison?.complete||plan.verifiedCoverage&&!plan.verifiedCoverage.remainingPages.length||plan.existingTask&&!plan.verifiedCoverage&&!plan.verifiedAuthoredReuse||busy)return;const token=version;busy=true;status('Starting your check…');try{
   for(const [key,path]of [['proposalEndpoint','proposals'],['researchIdeaEndpoint','ideas'],['localTaskEndpoint','tasks']])if(!endpoint(config?.[key],path))throw Error('Creating published follow-ups is not available here yet.');
   if(!await saveIdeaCard(plan.card,E.stable(plan),token)||!live(token))return;
   if(plan.verifiedAuthoredReuse){
    const reused=plan.verifiedAuthoredReuse,checked=await runAuthoredRemainder({proposalId:intent.proposalId,plan,remainingPages:[...reused.remainingPages]},{signal:controller.signal,isLive:()=>live(token)});if(!live(token))return;
    const assoc=(name,fallback)=>Object.hasOwn(checked,name)?checked[name]:checked[fallback],expected=await E.prepare({...plan.task,title:checked.plan.title,pages:plan.task.pages.filter(page=>reused.remainingPages.includes(page.id))},cryptoAPI);if(!live(token))return;
    if(assoc('linkedProposalId','proposalId')!==intent.proposalId||assoc('linkedInputVersion','inputVersion')!==plan.inputVersion||assoc('linkedParentTaskId','parentTaskId')!==null||!same(checked.card,plan.card)||!same(checked.plan,expected))throw Error('The remaining check differs from the exact reviewed pages or original idea.');
    const origins=await validateOrigins(checked.origins,checked.plan,cryptoAPI);if(!live(token))return;const subset=reused.remainingPages.length<plan.task.pages.length,relation={kind:'remaining-pages',declaredPages:plan.task.pages.map(page=>page.id),remainingPages:reused.remainingPages};
    if(!origins.some(item=>same(item.origin,plan.origin)&&same(item.control,plan.control)&&item.question===plan.question&&item.scopeChange===plan.scopeChange&&item.limitation===plan.limitation&&(subset?same(item.scopeRelation,relation):!Object.hasOwn(item,'scopeRelation'))))throw Error('The remaining check lost its reviewed published source or control.');
    if(subset){const controls=node?require('./local-plan-controls.js'):root.LocalPlanControls;if(!controls)throw Error('The remaining check controls are unavailable.');await controls.validate(checked.controls,checked.plan,cryptoAPI);if(!live(token))return;}
    await onCreated(checked,true,{declaredPages:plan.task.pages.map(page=>page.id),coveredPages:[...reused.coveredPages],remainingPages:[...reused.remainingPages]});return;
   }
   if(plan.verifiedCoverage){status('Original idea saved. Opening the unchecked pages for review.');onRemaining(intent.proposalId);return;}
   const response=await json(config.localTaskEndpoint,{proposalId:intent.proposalId,task:plan.task,inputVersion:plan.inputVersion,parentTaskId:null,origin:plan.origin}),checked=await projection(response,plan.task.taskId,cryptoAPI);if(!live(token))return;
   const assoc=(name,fallback)=>Object.hasOwn(checked,name)?checked[name]:checked[fallback];
   if(assoc('linkedProposalId','proposalId')!==intent.proposalId||assoc('linkedInputVersion','inputVersion')!==plan.inputVersion||assoc('linkedParentTaskId','parentTaskId')!==null||!same(checked.plan,plan.task)||!same(checked.card,plan.card))throw Error('The created experiment differs from the reviewed plan.');
   const origins=await validateOrigins(checked.origins,checked.plan,cryptoAPI);if(!live(token))return;if(!origins.some(item=>same(item.origin,plan.origin)&&same(item.control,plan.control)&&item.question===plan.question&&item.scopeChange===plan.scopeChange&&item.limitation===plan.limitation))throw Error('The created experiment has no matching published origin.');
   status('Starting your check…');await onCreated(checked,true);
  }catch(error){if(live(token)){if(error.reviewAgain){busy=false;const refreshing=load(),refreshedVersion=version;await refreshing;if(live(refreshedVersion))status('Saved output changed. Review the current remaining pages before running.');}else status('',error.message);}}finally{if(live(token)){busy=false;const button=get('create-followup');if(button){button.disabled=false;button.textContent=actionLabel();}}}}
  const ready=load();return {ready,destroy(){dead=true;version++;controller.abort();cleanupReuse();},getState:()=>({plan,busy})};
 }
 const api={reference,validateOrigins,createWorkspace};api.describeCard=cardProgram;if(node)module.exports=api;else root.RecordFollowups=api;
})(typeof globalThis!=='undefined'?globalThis:this);
