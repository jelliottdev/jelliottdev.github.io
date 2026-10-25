/* Readable next questions, linked only to published comparisons or declared follow-ups. */
(function(root){
 'use strict';
 const slug=value=>typeof value==='string'&&value.length<=100&&/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value);
 const text=(value,max)=>typeof value==='string'&&value.trim().length>0&&Array.from(value).length<=max;
 const prose=(value,max)=>typeof value==='string'&&value.length>0&&value.length<=max&&!/[<>\x00-\x1f\x7f\[\]`*\\\u2028\u2029\ud800-\udfff]/u.test(value)&&!/^[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]|[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]$/u.test(value);
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const followupView=()=>typeof module==='object'&&module.exports?require('./record-followup-view.js'):root.RecordFollowupView;
 function questions(record){
  if(!object(record)||!slug(record.id)||!Array.isArray(record.research_questions)||record.research_questions.length<1||record.research_questions.length>12)return [];
  const seen=new Set(),recipes=followupView()?.recipes(record)||[];
  for(const item of record.research_questions){
   if(!object(item)||Reflect.ownKeys(item).some(key=>!['id','question','state','note','records','followup'].includes(key))||!['id','question','state','note','records'].every(key=>Object.hasOwn(item,key))||Object.values(Object.getOwnPropertyDescriptors(item)).some(field=>!Object.hasOwn(field,'value'))||!slug(item.id)||seen.has(item.id)||!prose(item.question,300)||!prose(item.note,700)||!['tested','open'].includes(item.state)||!Array.isArray(item.records)||item.records.length>12||Array.from(item.records).some(id=>!slug(id)||id===record.id)||new Set(item.records).size!==item.records.length)return [];
   if(item.state==='tested'&&(!item.records.length||Object.hasOwn(item,'followup')))return [];
   if(Object.hasOwn(item,'followup')&&(!slug(item.followup)||!recipes.some(recipe=>recipe.id===item.followup)))return [];
   seen.add(item.id);
  }
  return record.research_questions.slice().sort((a,b)=>(a.state==='open'?0:1)-(b.state==='open'?0:1));
 }
 function coversFollowups(record){const items=questions(record),recipes=followupView()?.recipes(record)||[];return recipes.length>0&&recipes.every(recipe=>items.some(item=>item.state==='open'&&Object.hasOwn(item,'followup')&&item.followup===recipe.id));}
 function render(record,{headingLevel=2,fallback=''}={}){
  const level=[2,3,4].includes(headingLevel)?headingLevel:2;
  if(!object(record)||!Object.hasOwn(record,'research_questions'))return text(fallback,10000)?'<section id="experiment-remaining"><h'+level+'>What remains open</h'+level+'><p>'+esc(fallback)+'</p></section>':'';
  const items=questions(record);if(!items.length)return '';
  return '<section id="experiment-remaining" class="record-questions"><h'+level+'>Questions to explore</h'+level+'><ul>'+items.map(item=>'<li><p class="record-question-title"><strong>'+esc(item.question)+'</strong>'+' <span class="record-question-state">'+(item.state==='tested'?'Tested':'Open')+'</span>'+'</p><p>'+esc(item.note)+'</p>'+(Object.hasOwn(item,'followup')?'<p><a href="run.html#record='+record.id+'&amp;followup='+item.followup+'">Review follow-up</a></p>':'')+(item.records.length?'<ul class="record-question-links">'+item.records.map((id,index)=>'<li><a href="library.html#/experiment/'+id+'">'+(item.records.length===1?'Read completed test':'Read completed test '+(index+1))+'</a></li>').join('')+'</ul>':'')+'</li>').join('')+'</ul></section>';
 }
 const api={questions,coversFollowups,render};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
