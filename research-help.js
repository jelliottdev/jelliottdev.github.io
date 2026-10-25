/* Discover maintained browser checks without treating a recipe as unfinished evidence. */
(function(root){
 'use strict';
 const F=typeof module==='object'&&module.exports?require('./record-followup-view.js'):root.RecordFollowupView;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function choices(records){return Object.values(records||{}).filter(r=>r&&r.community!==true).map(record=>({record,checks:F.available(record)})).filter(group=>group.checks.length).sort((a,b)=>rank(a.checks[0])-rank(b.checks[0]));}
 const href=(record,check)=>'run.html#record='+encodeURIComponent(record.id)+'&followup='+encodeURIComponent(check.id);
 function criterion(check){const value=check.card.rules.evaluation.value;return typeof value==='string'?{kind:value}:value;}
 function rank(check){return {'word-affine-count':0,'word-prime-sums':1,measurement:2,'exact-prefix':3}[criterion(check).kind]??4;}
 function title(check){const c=criterion(check);return c.kind==='word-affine-count'?(c.a===1&&c.b===0?'Check repeats ':'Check a pattern ')+c.lag+' runes apart':c.kind==='word-prime-sums'?'Add numbers within each word':c.kind==='measurement'?'See what a decoding rule produces':'Look for a known passage';}
 function purpose(check){if(check.motivation)return check.motivation;const kind=criterion(check).kind;return {'exact-prefix':'Try a decoding rule and look for a fixed passage we already know.','word-affine-count':'Count a particular rune pattern to see whether it depends on how the text is divided.','word-prime-sums':'Assign numbers to runes and add them within each word.','measurement':'Apply a rule and inspect the resulting runes.'}[kind]||'Inspect the declared calculation before running it.';}
 function render(records){const groups=choices(records);return '<div class="research-help-intro"><p>No theory or coding needed. Review a prepared check, run it here, then choose whether to save the result.</p></div>'+(groups.length?'<section class="research-help-start" data-help-start><h3 class="research-help-start-label">A place to start</h3><p data-help-start-status role="status" aria-live="polite">Finding a check with work remaining…</p><div data-help-start-choice hidden><h4 data-help-start-title></h4><p data-help-start-purpose></p><p data-help-start-count role="status" aria-live="polite"></p><a class="research-help-start-action" data-help-start-link>Review remaining check</a></div></section><details class="research-help-all" data-help-browse><summary>Browse all prepared checks<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m6 9 6 6 6-6"/></svg></summary><ul class="research-help-choices">'+groups.map(({record,checks},index)=>'<li data-help-check="'+index+'"><h3>'+esc(title(checks[0]))+'</h3><p data-help-purpose>'+esc(purpose(checks[0]))+'</p>'+(checks.length>1?'<label for="help-check-'+index+'">Choose a rule</label><select id="help-check-'+index+'">'+checks.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.title)+'</option>').join('')+'</select>':'')+'<p class="research-help-question" data-help-question>'+esc(checks[0].question)+'</p><p class="research-help-status" data-help-status role="status" aria-live="polite" hidden></p><div class="research-help-actions"><a data-help-review href="'+esc(href(record,checks[0]))+'">Review check <span aria-hidden="true">→</span></a><button type="button" data-help-retry hidden>Retry</button><a href="library.html#/experiment/'+esc(record.id)+'">Read the research: '+esc(record.title)+'</a></div></li>').join('')+'</ul></details>':'<p>No maintained browser checks are listed in this research snapshot. You can still browse the research map.</p>');}
 function bind(host,records,{createReadiness}={}){
  const groups=choices(records),cleanups=[],rows=[...host.querySelectorAll('[data-help-check]')],initialStates=new Map(rows.map(row=>[row,null])),browse=host.querySelector?.('[data-help-browse]'),startStatus=host.querySelector?.('[data-help-start-status]'),startChoice=host.querySelector?.('[data-help-start-choice]'),startTitle=host.querySelector?.('[data-help-start-title]'),startPurpose=host.querySelector?.('[data-help-start-purpose]'),startLink=host.querySelector?.('[data-help-start-link]'),startCount=host.querySelector?.('[data-help-start-count]');let destroyed=false,recommendation=null,browsing=false;
  const remainingText=count=>count+' '+(count===1?'page remains':'pages remain')+' to check.';
  function recommend(element,record,check,state,value,message,label){
   initialStates.set(element,state);if(destroyed)return;
   if(recommendation){if(recommendation.recordId===record.id&&recommendation.checkId===check.id){startCount.textContent=message;startLink.textContent=label;if(startCount.dataset)startCount.dataset.state=state;}return;}
   if(browse?.open)stopForBrowse();if(browsing||!startStatus)return;
   if(state==='remaining'){
    recommendation=Object.freeze({recordId:record.id,checkId:check.id,title:check.title,purpose:purpose(check),question:check.question,remainingCount:value.remainingCount,href:href(record,check)});
    startTitle.textContent=recommendation.title;startPurpose.textContent=recommendation.purpose;startLink.href=recommendation.href;startLink.textContent=label;startCount.textContent=message;if(startCount.dataset)startCount.dataset.state=state;startStatus.hidden=true;startChoice.hidden=false;
   }else if([...initialStates.values()].every(item=>item&&item!=='loading'))startStatus.textContent=[...initialStates.values()].every(item=>item==='results'||item==='answered')?'These checks have saved results. Browse the full list to view them or choose another rule.':'We couldn’t confirm a check with work remaining. Browse the prepared checks below.';
  }
  if(startStatus&&typeof createReadiness!=='function')startStatus.textContent='Browse the prepared checks below.';
  function stopForBrowse(){if(destroyed)return;browsing=true;if(!recommendation&&startStatus)startStatus.textContent='Choose any check with pages remaining below.';}
  if(browse){browse.ontoggle=()=>{if(browse.open)stopForBrowse();};cleanups.push(()=>{browse.ontoggle=null;});}
  for(const element of rows){
   const group=groups[Number(element.dataset.helpCheck)];if(!group)continue;
   const select=element.querySelector('select'),status=element.querySelector('[data-help-status]'),retry=element.querySelector('[data-help-retry]'),link=element.querySelector('[data-help-review]');
   let current=group.checks[0].id,controller=null,version=0;
   function clear(){if(status){status.textContent='';status.hidden=true;if(status.dataset)delete status.dataset.state;}if(retry){retry.hidden=true;retry.onclick=null;}link.textContent='Review check';}
   function stop(){version++;const previous=controller;controller=null;if(previous)try{previous.destroy();}catch{}clear();}
   function start(check){
    stop();if(destroyed||typeof createReadiness!=='function')return;
    const token=version,live=()=>!destroyed&&version===token;
    function onState(value){
     if(!live())return;
     let state=value?.state,message,label='Review check';
     if(state==='remaining'&&(!Number.isSafeInteger(value.remainingCount)||value.remainingCount<1))state='unavailable';
     if(state==='loading')message='Checking saved results…';
     else if(state==='remaining'){message=remainingText(value.remainingCount);label='Review remaining check';}
     else if(state==='results'){message='Results are saved for every declared page.';label='View results';}
     else if(state==='answered'){message='This question already has an answer.';label='View answer';}
     else{state='unavailable';message='Saved results could not be checked.';}
     if(status){status.textContent=message;status.hidden=false;if(status.dataset)status.dataset.state=state;}link.textContent=label;if(retry)retry.hidden=state!=='unavailable';
     if(check.id===group.checks[0].id)recommend(element,group.record,check,state,value,message,label);
    }
    function invoke(method){try{Promise.resolve(method()).catch(()=>onState({state:'unavailable'}));}catch{onState({state:'unavailable'});}}
    onState({state:'loading'});
    if(retry)retry.onclick=()=>{if(!live())return;if(typeof controller?.retry!=='function'){start(check);return;}onState({state:'loading'});invoke(()=>controller.retry());};
    try{
     controller=createReadiness({record:group.record,check,onState});
     if(!controller||!['activate','retry','destroy'].every(key=>typeof controller[key]==='function'))throw Error('Readiness controller unavailable');
     invoke(()=>controller.activate());
    }catch{onState({state:'unavailable'});}
   }
   if(select)select.onchange=()=>{
    const check=group.checks.find(c=>c.id===select.value);if(!check){select.value=current;return;}if(check.id===current)return;
    current=check.id;element.querySelector('[data-help-purpose]').textContent=purpose(check);element.querySelector('[data-help-question]').textContent=check.question;link.href=href(group.record,check);start(check);
   };
   cleanups.push(()=>{stop();if(select)select.onchange=null;});start(group.checks[0]);
  }
  return function destroy(){if(destroyed)return;destroyed=true;for(const cleanup of cleanups)cleanup();};
 }

 const api={choices,render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchHelp=api;
})(typeof globalThis!=='undefined'?globalThis:this);
