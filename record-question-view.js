/* Readable next questions, linked only to published comparisons or declared follow-ups. */
(function(root){
 'use strict';
 const text=(value,max)=>typeof value==='string'&&value.trim().length>0&&Array.from(value).length<=max;
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const followupView=()=>typeof module==='object'&&module.exports?require('./record-followup-view.js'):root.RecordFollowupView;
 const model=typeof module==='object'&&module.exports?require('./record-question-model.js'):root.RecordQuestionModel;
 const mounts=new WeakMap();
 function questions(record){return model?.questions(record,followupView()?.recipes(record)||[])||[];}
 function coversFollowups(record){const items=questions(record),recipes=followupView()?.recipes(record)||[];return recipes.length>0&&recipes.every(recipe=>items.some(item=>Object.hasOwn(item,'followup')&&item.followup===recipe.id));}
 function workspace(record,item,reference){return reference.id==='deor-warning-opening'?'run.html#family=deor-feedback-v1':'run.html#record='+record.id+'&followup='+item.followup;}
 function publishedLinks(item){return item.records.length?'<ul class="record-question-links">'+item.records.map((id,index)=>'<li><a href="library.html#/experiment/'+id+'">'+(item.records.length===1?'Read completed test':'Read completed test '+(index+1))+'</a></li>').join('')+'</ul>':'';}
 function liveQuestion(record,item,reference,level){
  const href=workspace(record,item,reference);
  return '<li><p class="record-question-title"><strong>'+esc(item.question)+'</strong></p><div class="record-live-question" data-live-question="'+esc(item.id)+'" data-question-heading="'+Math.min(level+1,4)+'" aria-live="polite"><p class="record-question-live-status">Current evidence has not been checked.</p><button type="button" data-question-activate>Check current evidence</button><p class="record-question-workspace"><a href="'+esc(href)+'">Open question workspace</a></p></div><details class="record-published-assessment"><summary>Published assessment</summary><p class="record-question-state">Published as '+(item.state==='tested'?'tested':'open')+'</p><p>'+esc(item.note)+'</p>'+publishedLinks(item)+'</details></li>';
 }
 function render(record,{headingLevel=2,fallback=''}={}){
  const level=[2,3,4].includes(headingLevel)?headingLevel:2;
  if(!object(record)||!Object.hasOwn(record,'research_questions'))return text(fallback,10000)?'<section id="experiment-remaining"><h'+level+'>What remains open</h'+level+'><p>'+esc(fallback)+'</p></section>':'';
  const items=questions(record);if(!items.length)return '';
  return '<section id="experiment-remaining" class="record-questions"><h'+level+'>Questions to explore</h'+level+'><ul>'+items.map(item=>{const reference=model.protocolReference(record,item.id,followupView()?.recipes(record)||[]);return reference?liveQuestion(record,item,reference,level):'<li><p class="record-question-title"><strong>'+esc(item.question)+'</strong>'+' <span class="record-question-state">'+(item.state==='tested'?'Tested':'Open')+'</span>'+'</p><p>'+esc(item.note)+'</p>'+publishedLinks(item)+(Object.hasOwn(item,'followup')?'<p><a href="run.html#record='+record.id+'&amp;followup='+item.followup+'">'+(item.state==='tested'?'Review reproduction':'Review follow-up')+'</a></p>':'')+'</li>';}).join('')+'</ul></section>';
 }
 function mount(host,record,options={}){
  mounts.get(host)?.destroy();let dead=false,observer=null;
  const captured=JSON.parse(JSON.stringify(record)),items=new Map(questions(captured).map(item=>[item.id,item])),entries=[],loadLive=options.loadLive||(()=>root.RecordQuestionRuntime?.load?root.RecordQuestionRuntime.load():Promise.reject(Error('Current evidence tools are unavailable.')));
  function display(entry,value){
   if(dead)return;const {element,href,reference}=entry,level=entry.level;
   if(value?.state==='loading'){element.innerHTML='<p class="record-question-live-status" role="status">Checking current evidence…</p>';return;}
   const decision=value?.decision,valid=decision&&decision.schema==='liberpedia-question-decision-v1'&&decision.state===value.state&&decision.question?.id===reference.id&&['heading','finding','limit'].every(key=>typeof decision[key]==='string'&&decision[key].trim());
   if(!valid||value.state==='unavailable'){
    element.innerHTML='<p class="record-question-live-status">Current evidence could not be checked.</p><button type="button" data-question-retry>Retry current evidence</button><p class="record-question-workspace"><a href="'+esc(href)+'">Open question workspace</a></p>';return;
   }
   if(!['answered','missing-evidence'].includes(value.state)){display(entry,{state:'unavailable'});return;}
   let next='';
   if(value.state==='missing-evidence'&&decision.next?.kind==='run-missing-evidence')next='<p class="record-question-next"><a href="'+esc(href)+'">Review remaining checks</a></p>';
   if(value.state==='answered'&&decision.next?.kind==='inspect-evidence'&&reference.id==='deor-warning-opening'){
    const caseId=decision.next.caseIds?.[0],revision=decision.evidence?.revision;if(typeof caseId==='string'&&/^[a-z0-9-]{1,200}$/.test(caseId)&&typeof revision==='string'&&/^[a-f0-9]{64}$/.test(revision))next='<p class="record-question-next"><a href="run.html#family=deor-feedback-v1&amp;case='+esc(caseId)+'&amp;revision='+revision+'">Inspect matching output</a></p>';
   }
   if(value.state==='answered'&&decision.next?.kind==='inspect-evidence'&&reference.id==='fixed-program-prefix')next='<p class="record-question-next"><a href="'+esc(href)+'">Inspect matching output</a></p>';
   element.innerHTML='<h'+level+' class="record-question-answer">'+esc(decision.heading)+'</h'+level+'><p>'+esc(decision.finding)+'</p><p class="record-question-live-limit">'+esc(decision.limit)+'</p>'+next+(next?'':'<p class="record-question-workspace"><a href="'+esc(href)+'">Inspect source calculations</a></p>');
  }
  async function activate(entry,retry=false){
   if(dead||entry.pending||entry.activated&&!retry)return;entry.activated=true;const token=++entry.generation;display(entry,{state:'loading'});
   entry.pending=(async()=>{try{if(!entry.controller){const api=await loadLive();if(dead||entry.generation!==token)return;if(typeof api?.createController!=='function')throw Error('Current evidence tools did not load.');const {fetcher,config,loadConfig,loadInputs,crypto,pageURL}=options;entry.controller=api.createController({record:captured,questionId:entry.id,fetcher,config,loadConfig,loadInputs,crypto,pageURL,onState:value=>{if(!dead)display(entry,value);}});}if(dead||entry.generation!==token)return;await (retry?entry.controller.retry():entry.controller.activate());}catch{if(!dead&&entry.generation===token)display(entry,{state:'unavailable'});}finally{if(entry.generation===token)entry.pending=null;}})();return entry.pending;
  }
  for(const element of host?.querySelectorAll?.('[data-live-question]')||[]){
   const id=element.getAttribute('data-live-question'),item=items.get(id),reference=item&&model.protocolReference(captured,id,followupView()?.recipes(captured)||[]);if(!reference)continue;
   const heading=Number(element.getAttribute('data-question-heading')),entry={element,id,reference,href:workspace(captured,item,reference),level:[2,3,4].includes(heading)?heading:3,generation:0,activated:false,pending:null,controller:null};
   entry.click=event=>{const target=event.target?.closest?.('[data-question-activate],[data-question-retry]');if(target&&element.contains(target)){observer?.unobserve(element);void activate(entry,target.hasAttribute('data-question-retry'));}};element.addEventListener('click',entry.click);entries.push(entry);
  }
  const Observer=Object.hasOwn(options,'IntersectionObserver')?options.IntersectionObserver:root.IntersectionObserver;
  if(typeof Observer==='function'&&entries.length){observer=new Observer(changes=>{if(dead)return;for(const change of changes)if(change.isIntersecting){const entry=entries.find(entry=>entry.element===change.target);if(entry){observer.unobserve(change.target);void activate(entry);}}});entries.forEach(entry=>observer.observe(entry.element));}
  const handle={destroy(){if(dead)return;dead=true;observer?.disconnect();for(const entry of entries){entry.generation++;entry.controller?.destroy();entry.element.removeEventListener('click',entry.click);}if(mounts.get(host)===handle)mounts.delete(host);}};if(host&&typeof host==='object')mounts.set(host,handle);return handle;
 }
 const api={questions,coversFollowups,render,mount};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
