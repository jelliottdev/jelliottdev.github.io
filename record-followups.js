/* Reviewed published follow-ups: inspect first, explicitly create, never run at load. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,E=node?require('./local-experiment.js'):root.LocalExperiment;
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
   if(!exact(item,['origin','control','question','scopeChange','limitation'])||!validOrigin(item.origin)||!['question','scopeChange','limitation'].every(k=>text(item[k])))throw Error('The published origin metadata is invalid.');
   const key=E.stable(item.origin);if(seen.has(key))throw Error('A published origin is repeated.');seen.add(key);
   const control=item.control;if(!exact(control,['label','task','expected_result_sha256'])||!text(control.label,300)||!HEX.test(control.expected_result_sha256))throw Error('The synthetic control metadata is invalid.');
   await E.checkIdentity(control.task,cryptoAPI);
   if(control.task.pages.length!==1||Array.from(control.task.pages[0].text).filter(ch=>runes.has(ch)).length>4096||plan.criterion.kind!=='exact-prefix'||!['alphabet','steps','criterion'].every(k=>same(control.task[k],plan[k])))throw Error('The synthetic control does not match this bounded experiment.');
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
  if(!known('inputVersion')||!['raw','reviewed'].includes(rules.inputVersion.value)||!known('representation')||rules.representation.value!=='GP29'||!known('evaluation')||rules.evaluation.value?.kind!=='exact-prefix'||!exact(rules.evaluation.value,['kind','values']))throw Error('The published input and prefix criterion must be explicit.');
  for(const k of ['searchBounds','searchProtocol','exceptionalCases'])if(known(k))throw Error('The published conditions need an execution adapter.');
  if(known('unmapped')&&rules.unmapped.value!=='preserve'||known('wordBoundaries')&&rules.wordBoundaries.value!=='preserve')throw Error('The published separator rule needs an adapter.');
  const modes={vigenere:'repeat',repeating_key:'repeat',plaintext_autokey:'plaintext-autokey',ciphertext_autokey:'ciphertext-autokey'};let reversed=false,cumulative=false,resetUsed=false;
  const steps=draft.method.value.operations.map(op=>{
   const allowed=['id','label','declaredFamilyId',...(op.id==='affine'?['a','b']:op.id==='reverse_runes'?['unit']:op.id==='cumulative_difference'?['reset']:Object.hasOwn(modes,op.id)?['key','direction','reset']:[])];
   if(Object.keys(op).some(k=>!allowed.includes(k)))throw Error('The published operation has unsupported parameters.');
   if(op.id==='reverse_row_runes'||op.id==='reverse_runes'){
    reversed=true;let unit=op.id==='reverse_row_runes'?(known('boundaryMode')&&rules.boundaryMode.value==='within_words'?'word':'line'):op.unit;
    if(known('boundaryMode')&&(unit==='page'||rules.boundaryMode.value!==(unit==='word'?'within_words':'fixed_spaces'))||op.id==='reverse_row_runes'&&known('wordBoundaries')&&!known('boundaryMode'))throw Error('The published reversal boundary conflicts.');
    const labels=op.id==='reverse_row_runes'?['Reverse rune order within rows','Reverse rune order within each row']:['Reverse rune order within each '+unit];if(op.label!==undefined&&!labels.includes(op.label))throw Error('The published reversal wording is unsupported.');return {op:'reverse',unit};
   }
   if(op.id==='affine'){if(op.label!==undefined&&!['Affine','Affine substitution'].includes(op.label))throw Error('The published affine wording is unsupported.');return {op:'affine',a:op.a,b:op.b};}
   if(op.id==='cumulative_difference'||Object.hasOwn(modes,op.id)){
    resetUsed=true;if(rules.reset.status==='not_applicable'||known('reset')&&rules.reset.value!==op.reset)throw Error('The published reset conflicts.');
    if(op.id==='cumulative_difference'){cumulative=true;if(op.label!==undefined&&op.label!=='Cumulative difference'||rules.initialState.status==='not_applicable'||known('initialState')&&rules.initialState.value!==0)throw Error('The published initial state conflicts.');return {op:'cumulative-difference',reset:op.reset};}
    const labels={vigenere:['Vigenere','Vigenère'],repeating_key:['Repeating key','Repeating-key','Vigenere','Vigenère'],plaintext_autokey:['Plaintext autokey','Plaintext-autokey'],ciphertext_autokey:['Ciphertext autokey','Ciphertext-autokey']};if(op.label!==undefined&&!labels[op.id].includes(op.label))throw Error('The published keyed wording is unsupported.');return {op:'keyed-shift',key:op.key,mode:modes[op.id],direction:op.direction,reset:op.reset};
   }
   throw Error('The published method needs a supported adapter.');
  });
  if(known('boundaryMode')&&!reversed||known('reset')&&!resetUsed||known('initialState')&&!cumulative)throw Error('A published condition is not represented by the plan.');
  return {snapshot,steps,pages:draft.scope.value.pages,inputVersion:rules.inputVersion.value,criterion:rules.evaluation.value};
 }
 async function validatePlan(value,ref,cryptoAPI){
  if(!exact(value,['state','origin','card','task','inputVersion','control','question','scopeChange','limitation'])||value.state!=='plan-ready'||value.origin?.recordId!==ref.recordId||value.origin?.followupId!==ref.followupId)throw Error('The reviewed plan belongs to another published follow-up.');
  const program=cardProgram(value.card);await E.checkIdentity(value.task,cryptoAPI);
  if(!same(program.steps,value.task.steps)||!same(program.pages,value.task.pages.map(p=>p.id))||program.inputVersion!==value.inputVersion||!same(program.criterion,value.task.criterion))throw Error('The reviewed plan does not match its idea card.');
  await validateOrigins([{origin:value.origin,control:value.control,question:value.question,scopeChange:value.scopeChange,limitation:value.limitation}],value.task,cryptoAPI);return clone(value);
 }
 function createWorkspace(doc,host,options){
  const {reference:ref,config,request,validEndpoint,crypto:cryptoAPI=root.crypto,planHTML,isLive=()=>true,onCreated,projection}=options;
  let dead=false,version=0,plan=null,busy=false,intent=null;const controller=new AbortController(),live=token=>!dead&&version===token&&isLive(),get=id=>doc.getElementById(id),set=(id,value)=>{const el=get(id);if(el)el.textContent=value;};
  const endpoint=(value,path)=>typeof value==='string'&&validEndpoint(value,path);
  async function json(url,body,timeout=25000){const response=await request(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal},timeout),value=await response.json();if(!response.ok)throw Error(text(value?.error,1200)?value.error:text(value?.reason,1200)?value.reason:'The request could not be completed. Please retry.');return value;}
  function status(message='',error=''){set('followup-status',message);set('followup-error',error);const button=get('create-followup');if(button){button.disabled=busy;button.textContent=busy?'Creating experiment…':'Create experiment';}}
  function draw(){host.innerHTML='<nav class="run-links"><a href="research.html?v=record-panel-20261024">Back to research map</a><a href="library.html?v=record-panel-20261024#/experiment/'+esc(ref.recordId)+'">Source experiment</a></nav><h1>'+esc(plan.task.title)+'</h1><p>'+esc(plan.question)+'</p><p class="small">'+esc(plan.scopeChange)+'</p>'+planHTML(plan.task,plan.inputVersion)+'<p><strong>Synthetic control:</strong> '+esc(plan.control.label)+'. It will run first; a failed control stops the manuscript run.</p><p class="small">'+esc(plan.limitation)+'</p><p class="small">Creating this experiment shares the confirmed idea as a research entry. Results stay on your device until you submit them.</p><button id="create-followup" class="primary">Create experiment</button><p id="followup-status" class="notice" role="status"></p><p id="followup-error" class="error" role="alert"></p>';get('create-followup').onclick=create;}
  async function load(){const token=++version;host.innerHTML='<h1>Published follow-up</h1><p role="status">Loading the reviewed plan…</p>';try{
   if(!ref||!endpoint(config?.recordPlanEndpoint,'record-plans'))throw Error('Published follow-up plans are not available here yet.');
   const checked=await validatePlan(await json(config.recordPlanEndpoint,{recordId:ref.recordId,followupId:ref.followupId}),ref,cryptoAPI);if(!live(token))return;plan=checked;draw();
  }catch(error){if(!live(token))return;host.innerHTML='<h1>Follow-up unavailable</h1><p class="error" role="alert">'+esc(error.message)+'</p><button id="retry-followup">Retry</button><p><a href="library.html?v=record-panel-20261024#/experiment/'+esc(ref.recordId)+'">Read the source experiment</a></p>';get('retry-followup').onclick=load;}}
  async function create(){if(!plan||busy)return;const token=version;busy=true;status('Saving the reviewed experiment…');try{
   for(const [key,path]of [['proposalEndpoint','proposals'],['researchIdeaEndpoint','ideas'],['localTaskEndpoint','tasks']])if(!endpoint(config?.[key],path))throw Error('Creating published follow-ups is not available here yet.');
   const key=E.stable(plan);if(!intent||intent.key!==key){const snapshot=C.confirm(cardSnapshot(plan.card),{id:cryptoAPI.randomUUID(),at:new Date().toISOString()});intent={key,requestId:cryptoAPI.randomUUID(),fragment:H.encode(snapshot),proposalId:'p_'+await digest(C.serialize(H.cardData(snapshot)),cryptoAPI)};}
   if(!live(token))return;const created=await json(config.proposalEndpoint,{requestId:intent.requestId,fragment:intent.fragment});if(!live(token))return;
   if(created.id!==intent.proposalId||!['received','already_received'].includes(created.status)||!Number.isFinite(Date.parse(created.receivedAt)))throw Error('The saved idea receipt does not match this card.');
   const idea=await json(config.researchIdeaEndpoint,{proposalId:intent.proposalId});if(!live(token))return;if(idea.id!==intent.proposalId||!same(idea.card,plan.card))throw Error('The shared research entry does not match this card.');
   const response=await json(config.localTaskEndpoint,{proposalId:intent.proposalId,task:plan.task,inputVersion:plan.inputVersion,parentTaskId:null,origin:plan.origin}),checked=await projection(response,plan.task.taskId,cryptoAPI);if(!live(token))return;
   const assoc=(name,fallback)=>Object.hasOwn(checked,name)?checked[name]:checked[fallback];
   if(assoc('linkedProposalId','proposalId')!==intent.proposalId||assoc('linkedInputVersion','inputVersion')!==plan.inputVersion||assoc('linkedParentTaskId','parentTaskId')!==null||!same(checked.plan,plan.task)||!same(checked.card,plan.card))throw Error('The created experiment differs from the reviewed plan.');
   const origins=await validateOrigins(checked.origins,checked.plan,cryptoAPI);if(!live(token))return;if(!origins.some(item=>same(item.origin,plan.origin)&&same(item.control,plan.control)&&item.question===plan.question&&item.scopeChange===plan.scopeChange&&item.limitation===plan.limitation))throw Error('The created experiment has no matching published origin.');
   status('Experiment created. It has not been run.');onCreated(checked);
  }catch(error){if(live(token))status('',error.message);}finally{if(live(token)){busy=false;const button=get('create-followup');if(button){button.disabled=false;button.textContent='Create experiment';}}}}
  const ready=load();return {ready,destroy(){dead=true;version++;controller.abort();},getState:()=>({plan,busy})};
 }
 const api={reference,validateOrigins,createWorkspace};if(node)module.exports=api;else root.RecordFollowups=api;
})(typeof globalThis!=='undefined'?globalThis:this);
