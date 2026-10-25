/* Readable next questions, linked only to published comparisons or declared follow-ups. */
(function(root){
 'use strict';
 const text=(value,max)=>typeof value==='string'&&value.trim().length>0&&Array.from(value).length<=max;
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const followupView=()=>typeof module==='object'&&module.exports?require('./record-followup-view.js'):root.RecordFollowupView;
 const model=typeof module==='object'&&module.exports?require('./record-question-model.js'):root.RecordQuestionModel;
 function questions(record){return model?.questions(record,followupView()?.recipes(record)||[])||[];}
 function coversFollowups(record){const items=questions(record),recipes=followupView()?.recipes(record)||[];return recipes.length>0&&recipes.every(recipe=>items.some(item=>Object.hasOwn(item,'followup')&&item.followup===recipe.id));}
 function render(record,{headingLevel=2,fallback=''}={}){
  const level=[2,3,4].includes(headingLevel)?headingLevel:2;
  if(!object(record)||!Object.hasOwn(record,'research_questions'))return text(fallback,10000)?'<section id="experiment-remaining"><h'+level+'>What remains open</h'+level+'><p>'+esc(fallback)+'</p></section>':'';
  const items=questions(record);if(!items.length)return '';
  return '<section id="experiment-remaining" class="record-questions"><h'+level+'>Questions to explore</h'+level+'><ul>'+items.map(item=>'<li><p class="record-question-title"><strong>'+esc(item.question)+'</strong>'+' <span class="record-question-state">'+(item.state==='tested'?'Tested':'Open')+'</span>'+'</p><p>'+esc(item.note)+'</p>'+(item.records.length?'<ul class="record-question-links">'+item.records.map((id,index)=>'<li><a href="library.html#/experiment/'+id+'">'+(item.records.length===1?'Read completed test':'Read completed test '+(index+1))+'</a></li>').join('')+'</ul>':'')+(Object.hasOwn(item,'followup')?'<p><a href="run.html#record='+record.id+'&amp;followup='+item.followup+'">'+(item.state==='tested'?'Review reproduction':'Review follow-up')+'</a></p>':'')+'</li>').join('')+'</ul></section>';
 }
 const api={questions,coversFollowups,render};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
