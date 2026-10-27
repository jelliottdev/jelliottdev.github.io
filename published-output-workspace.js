/* Read-only archived output. Source verification belongs to PublishedOutputClient. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,mounts=new WeakMap();
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function dependencies(){return {Client:node?require('./published-output-client.js'):root.PublishedOutputClient,View:node?require('./local-run-view.js'):root.LocalRunView};}
 function variationDependencies(){return {Variants:node?require('./task-parameter-variants.js'):root.TaskParameterVariants,Context:node?require('./published-variation-context.js'):root.PublishedVariationContext,Mount:node?require('./parameter-variation-mount.js'):root.ParameterVariationMount};}
 function eligible(model,Client){try{const Variants=node?require('./task-parameter-variants.js'):root.TaskParameterVariants;return Client.isVerified?.(model)===true&&model.provenance.schema==='liberpedia-published-program-projection-v1'&&['exact-prefix','exact-prefix-set'].includes(model.task.criterion.kind)&&Variants.suggestions(model.task).length>0;}catch{return false;}}
 function sourceId(value){return typeof value==='string'&&/^[a-z0-9][a-z0-9-]{0,127}$/.test(value)?value:null;}
 function dateNote(provenance){
  const value=provenance?.checkedAt,meaning=provenance?.dateMeaning;
  const parsed=typeof value==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)?new Date(value):null;
  const valid=parsed&&Number.isFinite(parsed.getTime())&&parsed.toISOString()===value;
  if(!valid)return 'The archive date is not the original experiment date.';
  const label=meaning==='Count projection independently checked; not a historical browser submission.'?'Verified ':'Archive date: ';
  const human=parsed.getUTCDate()+' '+['January','February','March','April','May','June','July','August','September','October','November','December'][parsed.getUTCMonth()]+' '+parsed.getUTCFullYear();
  return label+human+'. This is not the original experiment date.';
 }
 function startingKey(task,step,index){
  if(!['keyed-shift','interrupted-keyed-shift','finite-shift'].includes(step.op)||!Array.isArray(step.key)||!step.key.length||step.key.length>256||!Array.isArray(task.alphabet)||task.alphabet.length!==29)return '';
  if(step.key.some(value=>!Number.isInteger(value)||value<0||value>=29||typeof task.alphabet[value]?.latin!=='string'||typeof task.alphabet[value]?.rune!=='string'))return '';
  const name=step.op==='finite-shift'?'Number sequence':'Starting key';
  return '<details class="published-output-details"><summary>'+name+(task.steps.length>1?' · step '+(index+1):'')+' ('+step.key.length+' '+(step.key.length===1?'value':'values')+')</summary><p class="run-text-note">Rune labels, not translated text. Each label corresponds to one rune.</p><p style="overflow-wrap:anywhere">'+step.key.map(value=>esc(task.alphabet[value].latin)).join(' · ')+'</p><p class="small" style="overflow-wrap:anywhere">Exact numbers: '+step.key.map(value=>String(value)).join(', ')+'.</p></details>';
 }
 function programDescription(task){
  if(!Array.isArray(task.steps))return '';
  const description=node?require('./published-program-description.js'):root.PublishedProgramDescription;
  if(!description?.step||!description?.program)return '';
  let descriptions;try{descriptions=task.steps.length?task.steps.map(description.step):[description.program(task.steps)];}catch{return '';}
  if(descriptions.some(value=>!value))return '';
  return '<section class="published-output-method" aria-label="What was tried"><h2>What was tried</h2>'+(descriptions.length===1?'<p>'+esc(descriptions[0])+'</p>'+startingKey(task,task.steps[0]||{},0):'<ol>'+descriptions.map((value,index)=>'<li>'+esc(value)+startingKey(task,task.steps[index],index)+'</li>').join('')+'</ol>')+'</section>';
 }
 function baselineHTML(model){
  const {Client}=dependencies();
  if(Client.isVerified?.(model)!==true||model.provenance?.schema!=='liberpedia-published-program-projection-v1'||!Array.isArray(model.task?.steps)||model.task.steps.length||!['exact-prefix','exact-prefix-set'].includes(model.task.criterion?.kind))return '';
  const owner=sourceId(model.provenance.projection?.ownerRecordId),discovery=node?require('./published-program-discovery.js'):root.PublishedProgramDiscovery;
  return '<p class="small">This keeps the original rune order, so there are no settings to change.</p>'+(owner&&discovery?.hasAlternatives?.(owner)===true?'<p><a href="library.html#/experiment/'+esc(owner)+'?section=record-saved-calculations">Choose another saved calculation</a></p>':'');
 }
 function render(model,View,canVary=false){
  const {task,run,provenance}=model,id=sourceId(provenance?.schema==='liberpedia-published-program-projection-v1'?provenance.projection?.ownerRecordId:provenance?.recordId);if(!id||!task||!run?.result)throw Error('The archived calculation is incomplete.');
  const details=[['Input text',model.inputVersion],['Verification or import date',provenance.checkedAt],['Date meaning',provenance.dateMeaning],['Verification',provenance.verificationMeaning],['Comparison',provenance.expectationMeaning]].filter(([,value])=>typeof value==='string'&&value.length);
  return '<article class="published-output"><header><h1>Archived calculation</h1><p class="published-output-date">'+esc(dateNote(provenance))+'</p><nav aria-label="Archived calculation sources"><a href="library.html#/experiment/'+esc(id)+'">Source experiment</a><a href="research.html">Research map</a></nav></header>'+(provenance.schema==='liberpedia-published-program-projection-v1'?programDescription(task):'')+'<div data-published-output-result>'+View.renderArchived(model,{afterFindingHTML:canVary?'<div class="published-output-variation"><button type="button" data-published-variation>Try another setting</button><div data-published-variation-status></div><div data-published-variation-workspace></div></div>':baselineHTML(model)})+'</div>'+'<details class="published-output-details"><summary>Calculation details</summary><p>'+esc(task.title)+'</p><dl>'+details.map(([label,value])=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>').join('')+'</dl></details></article>';
 }
 function mount(host,options={}){
  if(!host||typeof host.querySelector!=='function')throw Error('Choose an archived-output container.');
  mounts.get(host)?.destroy();
  const {Client,View}=dependencies();if(!Client?.load||!View?.renderArchived||!View?.bindArchived)throw Error('The archived-output inspector is unavailable.');
  let destroyed=false,generation=0,abort=null,cleanup=()=>{},phase='loading',selectedPage=null,verified=null,retryButton=null,retryListener=null;
  let variationGeneration=0,variationAbort=null,variationMount=null,variationButton=null,variationListener=null,variationPhase='idle';
  const alive=token=>!destroyed&&generation===token;
  function unbind(){cleanup();cleanup=()=>{};if(retryButton&&retryListener)retryButton.removeEventListener('click',retryListener);retryButton=null;retryListener=null;variationGeneration++;variationAbort?.abort();variationMount?.destroy();variationMount=null;if(variationButton&&variationListener)variationButton.removeEventListener('click',variationListener);variationButton=null;variationListener=null;variationPhase='idle';}
  async function openVariation(){
   if(destroyed||phase!=='ready'||!verified||variationPhase==='loading'||variationPhase==='ready')return;
   const token=++variationGeneration,outputGeneration=generation,model=verified,status=host.querySelector('[data-published-variation-status]'),workspace=host.querySelector('[data-published-variation-workspace]');
   const current=()=>alive(outputGeneration)&&variationGeneration===token;
   variationAbort?.abort();variationAbort=new AbortController();variationPhase='loading';if(variationButton){variationButton.disabled=true;variationButton.textContent='Loading variation…';}if(status)status.innerHTML='<p role="status" aria-live="polite">Loading the calculation settings…</p>';
   try{
    const {Context,Mount}=variationDependencies();if(!Context?.load||!Mount?.mount)throw Error('Variation review is unavailable.');
    const request={baseURL:options.baseURL,fetcher:options.fetcher,crypto:options.crypto,pageURL:options.pageURL,signal:variationAbort.signal},review=Context.loadReview?await Context.loadReview(model,request):{context:await Context.load(model,request),navigationHints:null};if(!current())return;
    const mounted=Mount.mount(workspace,{...options,context:review.context,navigationHints:review.navigationHints,signal:variationAbort.signal});variationMount=mounted;await mounted.ready;if(!current()){mounted.destroy();return;}variationPhase='ready';if(status)status.innerHTML='';if(variationButton)variationButton.hidden=true;
   }catch{
    if(!current())return;variationMount?.destroy();variationMount=null;variationPhase='error';if(status)status.innerHTML='<p role="alert">The variation settings could not be loaded. The archived output is still available.</p>';if(variationButton){variationButton.disabled=false;variationButton.textContent='Try again';}
   }
  }
  function rememberPage(event){const target=event?.target;if(target?.tagName==='SELECT'&&verified?.task.pages.some(page=>page.id===target.value))selectedPage=target.value;}
  host.addEventListener('change',rememberPage);
  async function load(){
   if(destroyed)return null;const token=++generation;abort?.abort();abort=new AbortController();unbind();phase='loading';host.innerHTML='<section class="published-output"><h1>Archived calculation</h1><p role="status" aria-live="polite">Loading archived output…</p></section>';
   try{
    const model=await Client.load(options.reference,{baseURL:options.baseURL,fetcher:options.fetcher,crypto:options.crypto,pageURL:options.pageURL,signal:abort.signal});
    if(!alive(token))return null;
    host.innerHTML=render(model,View,eligible(model,Client));verified=model;
    if(!model.task.pages.some(page=>page.id===selectedPage))selectedPage=model.task.pages[0]?.id;
    cleanup=View.bindArchived(host.querySelector('[data-published-output-result]'),model,{pageId:selectedPage})||(()=>{});phase='ready';variationButton=host.querySelector('[data-published-variation]');if(variationButton){variationListener=()=>openVariation();variationButton.addEventListener('click',variationListener);}return model;
   }catch{
    if(!alive(token))return null;unbind();phase='error';host.innerHTML='<section class="published-output"><h1>Archived calculation</h1><p role="alert">The archived output could not be verified. Try loading it again.</p><button type="button" data-published-output-retry>Try again</button><p><a href="research.html">Research map</a></p></section>';
    retryButton=host.querySelector('[data-published-output-retry]');retryListener=()=>{load();};retryButton?.addEventListener('click',retryListener);return null;
   }
  }
  function destroy(){if(destroyed)return;destroyed=true;generation++;abort?.abort();unbind();host.removeEventListener('change',rememberPage);options.signal?.removeEventListener('abort',destroy);if(mounts.get(host)===api)mounts.delete(host);}
  const api={ready:null,destroy,getState:()=>({phase:destroyed?'destroyed':phase,pageId:selectedPage,variationPhase})};mounts.set(host,api);
  if(options.signal?.aborted){destroy();api.ready=Promise.resolve(null);}else{options.signal?.addEventListener('abort',destroy,{once:true});api.ready=load();}
  return api;
 }
 const api={mount,render};if(node)module.exports=api;else root.PublishedOutputWorkspace=api;
})(typeof globalThis!=='undefined'?globalThis:this);
