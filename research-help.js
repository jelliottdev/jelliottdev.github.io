/* Discover maintained browser checks without treating a recipe as unfinished evidence. */
(function(root){
 'use strict';
 const F=typeof module==='object'&&module.exports?require('./record-followup-view.js'):root.RecordFollowupView;
 const Discovery=typeof module==='object'&&module.exports?require('./research-discovery.js'):root.ResearchDiscovery;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function choices(records){return Object.values(records||{}).filter(r=>r&&r.community!==true).map(record=>({record,checks:Discovery?.isRecord(record)?Discovery.available(record):F.available(record)})).filter(group=>group.checks.length).sort((a,b)=>rank(a.checks[0])-rank(b.checks[0]));}
 const href=(record,check)=>'run.html#record='+encodeURIComponent(record.id)+'&followup='+encodeURIComponent(check.id);
 function criterion(check){if(check.evaluation_kind)return {kind:check.evaluation_kind};const value=check.card.rules.evaluation.value;return typeof value==='string'?{kind:value}:value;}
 function rank(check){return {'word-affine-count':0,'word-prime-sums':1,measurement:2,'exact-prefix':3}[criterion(check).kind]??4;}
 function purpose(check){if(check.motivation)return check.motivation;const kind=criterion(check).kind;return {'exact-prefix':'Try a decoding rule and look for a fixed passage we already know.','word-affine-count':'Count a particular rune pattern to see whether it depends on how the text is divided.','word-prime-sums':'Assign numbers to runes and add them within each word.','measurement':'Apply a rule and inspect the resulting runes.','language-score':'Compare the output with fixed language samples and rearranged versions of itself. A high score does not establish a reading.'}[kind]||'Inspect the declared calculation before running it.';}
 function render(records){const groups=choices(records);return '<div class="research-help-intro"><p>No theory or coding needed. Choose a prepared check and review what it will do before running it.</p></div>'+(groups.length?'<section class="research-help-start" data-help-start><h3 class="research-help-start-label">A place to start</h3><p data-help-start-status role="status" aria-live="polite">Finding a check with work remaining…</p><button type="button" data-help-more hidden>Look for another check</button><div data-help-start-choice hidden><h4 data-help-start-title></h4><p data-help-start-purpose></p><p data-help-start-count role="status" aria-live="polite"></p><a class="research-help-start-action" data-help-start-link>Review remaining check</a></div></section><details class="research-help-all" data-help-browse><summary>Browse all prepared checks<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m6 9 6 6 6-6"/></svg></summary><ul class="research-help-choices">'+groups.map(({record,checks},index)=>'<li data-help-check="'+index+'"><h3 data-help-title>'+esc(checks[0].title)+'</h3><p data-help-purpose>'+esc(purpose(checks[0]))+'</p>'+(checks.length>1?'<label for="help-check-'+index+'">Choose a check</label><select id="help-check-'+index+'">'+checks.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.title)+'</option>').join('')+'</select>':'')+'<p class="research-help-question" data-help-question'+(checks[0].motivation?' hidden':'')+'>'+esc(checks[0].question)+'</p><p class="research-help-status" data-help-status role="status" aria-live="polite" hidden></p><div class="research-help-actions"><a data-help-review href="'+esc(href(record,checks[0]))+'">Review check <span aria-hidden="true">→</span></a><button type="button" data-help-retry hidden>Retry</button><a href="library.html#/experiment/'+esc(record.id)+'">Read the research: '+esc(record.title)+'</a></div></li>').join('')+'</ul></details>':'<p>No maintained browser checks are listed in this research snapshot. You can still browse the research map.</p>');}
 function bind(host,records,{createReadiness}={}){
  const groups=choices(records),rows=[...host.querySelectorAll('[data-help-check]')],entries=new Map(),cleanups=[],initial=[],alternatives=[];
  const browse=host.querySelector?.('[data-help-browse]'),startStatus=host.querySelector?.('[data-help-start-status]'),startChoice=host.querySelector?.('[data-help-start-choice]'),startTitle=host.querySelector?.('[data-help-start-title]'),startPurpose=host.querySelector?.('[data-help-start-purpose]'),startLink=host.querySelector?.('[data-help-start-link]'),startCount=host.querySelector?.('[data-help-start-count]'),more=host.querySelector?.('[data-help-more]');
  let destroyed=false,recommendation=null,browsing=false,scheduled=false,autoStarted=false,batchActive=false,budget=0,cursor=0,current=null;
  const key=(record,check)=>record.id+'|'+check.id,terminal=e=>e.state&&e.state.state!=='loading';
  function stateView(value){
   let state=value?.state,label='Review check',message;
   if(state==='remaining'&&(!Number.isSafeInteger(value.remainingCount)||value.remainingCount<1))state='unavailable';
   if(state==='loading')message='Checking saved results…';
   else if(state==='remaining'){message=value.unit==='cases'?value.remainingCount+' '+(value.remainingCount===1?'check remains.':'checks remain.'):value.remainingCount+' '+(value.remainingCount===1?'page remains':'pages remain')+' to check.';label='Review remaining check';}
   else if(state==='results'){message=value.unit==='cases'?'Results are saved for every declared page and setting.':'Results are saved for every declared page.';label='View results';}
   else if(state==='answered'){message='This question already has an answer.';label='View answer';}
   else{state='unavailable';message='Saved results could not be checked.';}
   return {state,message,label,...(state==='remaining'?{remainingCount:value.remainingCount}:{})};
  }
  function entryFor(record,check){
   const id=key(record,check);if(!entries.has(id))entries.set(id,{id,record,check,state:null,controller:null,started:false,listeners:new Set()});return entries.get(id);
  }
  function stopForBrowse(){
   if(destroyed)return;browsing=true;batchActive=false;if(more)more.hidden=true;
   if(!recommendation&&startStatus)startStatus.textContent='Choose a check with work remaining below.';
  }
  function updateStart(entry){
   if(!startStatus)return;const state=entry.state;
   if(recommendation){if(recommendation.id===entry.id){startCount.textContent=state.message;startLink.textContent=state.label;if(startCount.dataset)startCount.dataset.state=state.state;}return;}
   if(browse?.open)stopForBrowse();if(browsing||state.state!=='remaining')return;
   recommendation=Object.freeze({id:entry.id,recordId:entry.record.id,checkId:entry.check.id,title:entry.check.title,purpose:purpose(entry.check),question:entry.check.question,href:href(entry.record,entry.check)});
   startTitle.textContent=recommendation.title;startPurpose.textContent=recommendation.purpose;startLink.href=recommendation.href;startLink.textContent=state.label;startCount.textContent=state.message;if(startCount.dataset)startCount.dataset.state=state.state;startStatus.hidden=true;startChoice.hidden=false;batchActive=false;if(more)more.hidden=true;
  }
  function schedule(){if(scheduled||destroyed)return;scheduled=true;Promise.resolve().then(()=>{scheduled=false;discover();});}
  function publish(entry,value){
   if(destroyed)return;entry.state=stateView(value);for(const listener of entry.listeners)listener(entry.state);updateStart(entry);schedule();
  }
  function activate(entry,retry=false){
   if(destroyed||typeof createReadiness!=='function')return;
   if(entry.started&&!retry)return;
   entry.started=true;publish(entry,{state:'loading'});
   try{
    if(!entry.controller){
     const controller=createReadiness({record:entry.record,check:entry.check,onState:value=>publish(entry,value)});
     if(!controller||!['activate','retry','destroy'].every(k=>typeof controller[k]==='function')){controller?.destroy?.();throw Error('Readiness controller unavailable');}
     entry.controller=controller;
    }
    Promise.resolve(retry?entry.controller.retry():entry.controller.activate()).catch(()=>publish(entry,{state:'unavailable'}));
   }catch{publish(entry,{state:'unavailable'});}
  }
  function fallback(){
   if(!startStatus||recommendation||browsing||destroyed)return;
   const unknown=[...entries.values()].some(e=>e.started&&e.state?.state==='unavailable');
   startStatus.textContent=unknown?'No starting check was confirmed yet. Some saved results could not be checked.':cursor<alternatives.length?'The checks reviewed so far have saved results or answers.':'These prepared checks have saved results or answers. Browse the full list to view them.';
   if(more){more.hidden=cursor>=alternatives.length;more.disabled=false;}
  }
  function discover(){
   if(destroyed||recommendation||browsing||!startStatus||typeof createReadiness!=='function'||!initial.length)return;
   if(browse?.open){stopForBrowse();return;}
   if(!initial.every(terminal))return;
   if(!autoStarted){autoStarted=true;batchActive=true;budget=4;}
   if(!batchActive){fallback();return;}
   if(current&&!terminal(current))return;current=null;
   if(!budget||cursor>=alternatives.length){batchActive=false;fallback();return;}
   current=alternatives[cursor++];budget--;startStatus.textContent='Looking through other prepared checks…';if(more)more.hidden=true;
   if(current.started){updateStart(current);schedule();}else activate(current);
  }
  if(startStatus&&typeof createReadiness!=='function')startStatus.textContent='Browse the prepared checks below.';
  if(browse){browse.ontoggle=()=>{if(browse.open)stopForBrowse();};cleanups.push(()=>{browse.ontoggle=null;});}
  if(more){more.onclick=()=>{if(destroyed||recommendation||browsing||batchActive||cursor>=alternatives.length)return;batchActive=true;budget=4;more.disabled=true;schedule();};cleanups.push(()=>{more.onclick=null;});}
  // Capture the catalogue before any synchronous controller can report a state.
  const boundRows=[];
  for(const element of rows){const group=groups[Number(element.dataset.helpCheck)];if(!group)continue;initial.push(entryFor(group.record,group.checks[0]));for(const check of group.checks.slice(1))alternatives.push(entryFor(group.record,check));boundRows.push({element,group});}
  for(const {element,group} of boundRows){
   const select=element.querySelector('select'),status=element.querySelector('[data-help-status]'),retry=element.querySelector('[data-help-retry]'),link=element.querySelector('[data-help-review]');let selected=null;
   function clear(){if(status){status.textContent='';status.hidden=true;if(status.dataset)delete status.dataset.state;}if(retry){retry.hidden=true;retry.onclick=null;}link.textContent='Review check';}
   function show(state){if(status){status.textContent=state.message;status.hidden=false;if(status.dataset)status.dataset.state=state.state;}link.textContent=state.label;if(retry)retry.hidden=state.state!=='unavailable';}
   function choose(check){
    if(selected)selected.listeners.delete(show);clear();selected=entryFor(group.record,check);selected.listeners.add(show);
    const heading=element.querySelector('[data-help-title]');if(heading)heading.textContent=check.title;
    if(retry)retry.onclick=()=>{if(!destroyed)activate(selected,true);};
    if(selected.state)show(selected.state);activate(selected);
   }
   if(select)select.onchange=()=>{
    const check=group.checks.find(c=>c.id===select.value);if(!check){select.value=selected.check.id;return;}if(check.id===selected.check.id)return;
    stopForBrowse();element.querySelector('[data-help-purpose]').textContent=purpose(check);element.querySelector('[data-help-question]').textContent=check.question;element.querySelector('[data-help-question]').hidden=Boolean(check.motivation);link.href=href(group.record,check);choose(check);
   };
   cleanups.push(()=>{selected?.listeners.delete(show);clear();if(select)select.onchange=null;});choose(group.checks[0]);
  }
  return function destroy(){if(destroyed)return;destroyed=true;for(const cleanup of cleanups)cleanup();for(const entry of entries.values()){entry.listeners.clear();entry.controller?.destroy();}};
 }

 const api={choices,render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchHelp=api;
})(typeof globalThis!=='undefined'?globalThis:this);
