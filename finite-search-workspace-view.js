/* Shared finite-search controls and results. No task or evidence authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,View=node?require('./finite-search-view.js'):root.FiniteSearchView,Output=node?require('./local-run-view.js'):root.LocalRunView,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function domainLabel(name,values){
  if(values.length>=3&&values.every((v,i)=>Number.isInteger(v)&&(!i||v===values[i-1]+1)))return values[0]+'–'+values.at(-1);
  const literal=values.map(v=>typeof v==='string'?v:JSON.stringify(v)).join(', ');
  if(values.length<=6&&literal.length<=80)return literal;
  if(values.every(Array.isArray)){const lengths=values.map(v=>v.length),min=Math.min(...lengths),max=Math.max(...lengths);return values.length+' '+(name==='key'?'keys':'rune sets')+' ('+(min===max?min:min+'–'+max)+' indices each; exact values in Confirmed idea)';}
  return values.length+' '+(values.every(v=>typeof v==='number')?'values':'choices')+' (exact values in Confirmed idea)';
 }
 function operationLabel(op){const parameters=H.operationParameters(op).map(p=>({label:p.label,value:p.label==='Key'&&Array.isArray(op.key)&&op.key.length>6?op.key.length+' indices (exact key in Confirmed idea)':p.value}));return (op.label||op.id.replace(/_/g,' '))+(parameters.length?' ('+parameters.map(p=>p.label+': '+p.value).join(', ')+')':'');}
 function settingsLabel(settings,parameters=[]){
  const operations=new Map();for(const setting of settings){if(!operations.has(setting.name))operations.set(setting.name,new Set());operations.get(setting.name).add(setting.operation);}
  return settings.map(setting=>{
   const name=(operations.get(setting.name).size>1?'step '+(setting.operation+1)+' ':'')+setting.name,value=setting.value;
   if(setting.name==='key'&&Array.isArray(value)&&value.length>6){
    const axis=parameters.find(p=>p.operation===setting.operation&&p.name===setting.name),ordinal=axis?.values.findIndex(v=>JSON.stringify(v)===JSON.stringify(value))??-1;
    return name+(ordinal>=0?' '+(ordinal+1)+' of '+axis.values.length:'')+' · '+value.length+' indices · starts ['+value.slice(0,6).join(', ')+', …]';
   }
   return name+' = '+(Array.isArray(value)?'['+value.join(', ')+']':typeof value==='object'?JSON.stringify(value):String(value));
  }).join('; ');
 }
 function openingLabel(task){const known=C.evaluationText(task.criterion);if(known)return known;const values=task.criterion.values;return 'Exact opening: '+values.slice(0,24).map(value=>task.alphabet[value].rune).join('')+(values.length>24?'… ('+values.length+' runes; complete opening in Confirmed idea)':'');}
  function continuationMessage(state,local){
   if(state.status==='waiting')return 'The service is busy. Retrying in '+Math.ceil(state.retryDelayMs/1000)+' seconds.';
   if(state.status==='running')return 'Verified results are saved after each small batch.';
   if(state.status==='stopped')return state.reason==='prefix-found'?'Stopped after finding the specified opening. Verified results are shown above.':'The remaining search is finished. Verified results are shown above.';
   if(state.reason==='lookup-incomplete')return 'Saved evidence could not be checked completely. Resume to retry before running more settings.';
   if(state.reason==='daily-quota')return 'The daily saving limit has been reached.'+(state.error?.retryAt?' Try again after '+new Date(state.error.retryAt).toLocaleString()+'.':'')+(local?' Keep this page open while results remain unsaved.':' Saved checks are kept.');
   return state.error?.message||(local?'Resume saves the completed outputs before continuing. Keep this page open while results remain unsaved.':'Saved checks are kept. You can resume this same search.');
  }
 function render(model,{phase,reuseNote='',busy=false,notice='',progress=null,error='',storageNotice='',continuationState=null,fullReview=null,prepared=null,local=null,pending=null,inspected=null,unsupported=false,coveredCases=0,retry=false}={}){
   const disabled=busy?' disabled':'';
   let html=model?View.render(model,{checkLabel:'Review remaining search'}):'<h2 data-finite-focus tabindex="-1">Check these settings</h2><p role="status">'+(phase==='loading'?'Checking the declared settings and saved work…':'The settings could not be checked.')+'</p>';
   if(reuseNote)html+='<p class="finite-search-reuse">'+esc(reuseNote)+'</p>';
   const statusNotice=continuationState&&['running','waiting','paused'].includes(continuationState.status)?'':notice;html+='<p data-finite-focus tabindex="-1" role="status">'+esc(statusNotice||progress&&(progress.phase==='controls'?'Checking the calculation':'Checking your pages')+': '+progress.completed+' of '+progress.total||'')+'</p>';
   if(storageNotice)html+='<p role="status">'+esc(storageNotice)+'</p>';
   if(pending&&!local)html+='<section class="finite-local"><h3>Unsaved checks on this device</h3><p>'+pending.count+' completed '+(pending.count===1?'check was':'checks were')+' retained. Restore to inspect or save '+(pending.count===1?'it':'them')+'. Nothing runs automatically.</p><div class="run-actions"><button type="button" class="primary" data-finite-work="restore-local"'+disabled+'>Restore unsaved checks</button><button type="button" data-finite-work="discard-local"'+disabled+'>Discard</button></div></section>';
   if(error&&continuationState?.error?.message!==error)html+='<p class="error" role="alert">'+esc(error)+'</p>'+(!model&&!unsupported?'<button type="button" data-finite-work="retry">Try again</button>':'')+(unsupported?'<p>Review the declared settings before preparing this idea again. No settings or pages were omitted.</p>':'');
   if(error&&model&&retry)html+='<button type="button" data-finite-work="retry"'+disabled+'>Refresh saved evidence</button>';
   const continuing=continuationState&&['running','waiting'].includes(continuationState.status);
   if(fullReview)html+='<section class="finite-batch"><h3>Run the remaining search</h3><p>'+fullReview.remainingCases.toLocaleString('en-US')+' checks remain in the search shown above. Uses '+(fullReview.inputVersion==='raw'?'the archived rune text':'the reviewed text')+'.</p><p>Runs on this device and saves verified results as it goes. Stops if the specified opening is found. You can pause at any time. Saving may also pause at a service limit; completed checks are kept.</p><div class="run-actions"><button type="button" class="primary" data-finite-work="start-remaining">Run and save remaining checks</button><button type="button" data-finite-work="small-batch">Review a small batch</button><button type="button" data-finite-work="close-review">Cancel</button></div></section>';
   if(continuationState&&continuationState.status!=='idle'&&continuationState.status!=='destroyed'){const state=continuationState,paused=state.status==='paused',active=['running','waiting'].includes(state.status),waiting=state.status==='waiting';html+='<section class="finite-batch" aria-label="Search progress"><h3>'+(active?'Checking the remaining search':paused?'Search paused':'Search stopped')+'</h3><p role="status">'+esc(continuationMessage(state,local))+'</p>'+(active?'<button type="button" data-finite-work="pause-remaining">Pause search</button>':paused?'<button type="button" class="primary" data-finite-work="resume-remaining">Resume search</button>':'')+'</section>'; }
   if(prepared&&!local&&!continuing){html+='<section class="finite-batch"><h3>Review the next checks</h3><p>'+prepared.cases.length+' page-and-setting '+(prepared.cases.length===1?'check':'checks')+'. The original idea and opening check stay the same.</p><ul>'+prepared.cases.map(item=>'<li>'+esc(item.pageId.toUpperCase())+' · '+esc(settingsLabel(item.settings,prepared.parameters))+'</li>').join('')+'</ul>'+(prepared.cases.some(item=>item.settings.some(s=>s.name==='key'&&Array.isArray(s.value)&&s.value.length>6))?'<p class="small">Full key values are in Confirmed idea.</p>':'')+'<p class="small">Known-answer checks run first. They check the calculation, not a decryption.</p><button type="button" class="primary" data-finite-work="run"'+disabled+'>'+(prepared.retryEvidence?'Retry saved evidence':'Run in browser')+'</button></section>';}
   if(local&&!continuing)html+='<section class="finite-local"><h3>Checked on this device</h3><p>'+local.count+' '+(local.count===1?'check is':'checks are')+' verified locally and not yet saved.'+(local.matching?' An output starts with the specified opening.':'')+'</p><button type="button" data-finite-work="inspect-local">Inspect local output</button> <button type="button" class="primary" data-finite-work="save"'+disabled+'>Save results</button></section>';
   if(busy&&!continuing&&phase!=='loading'&&phase!=='checkpoint')html+='<button type="button" data-finite-work="cancel">Cancel</button>';
   if(inspected){const derived=inspected.evidenceKind==='derived-prefix';html+='<section class="finite-inspected"><h3 tabindex="-1" data-finite-output-heading>'+esc(derived?'Opening checked from earlier output':inspected.label)+'</h3>'+(derived?'<p>This opening was checked now against the earlier output. The original calculation below used a different check.</p>'+Output.renderPrefixComparison(inspected.task,inspected.result,inspected.requestedCriterion,inspected.pageId)+'<h3>Original saved result</h3>':'')+Output.render(inspected.task,inspected.result)+'</section>'; }
   if(coveredCases)html+='<details class="experiment-details"><summary>Reproduce saved checks</summary><p>Download the original question, pinned inputs and saved results, with an offline audit. It checks these receipts without running missing settings.</p><button type="button" data-finite-work="download"'+disabled+'>Download search audit</button></details>';
   return html;
 }
 const api={render,domainLabel,operationLabel,openingLabel,settingsLabel};if(node)module.exports=api;else root.FiniteSearchWorkspaceView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
