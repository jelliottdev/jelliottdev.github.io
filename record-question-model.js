/* Shared authored question states. Tested links permit reproduction, never new-work claims. */
(function(root){
 'use strict';
 const slug=value=>typeof value==='string'&&value.length<=100&&/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value);
 const prose=(value,max)=>typeof value==='string'&&value.length>0&&value.length<=max&&!/[<>\x00-\x1f\x7f\[\]`*\\\u2028\u2029\ud800-\udfff]/u.test(value)&&!/^[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]|[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]$/u.test(value);
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 function questions(record,recipes=[]){
  if(!object(record)||!slug(record.id)||!Array.isArray(record.research_questions)||record.research_questions.length<1||record.research_questions.length>12)return [];
  const seen=new Set(),linked=new Set();
  for(const item of record.research_questions){
   if(!object(item)||Reflect.ownKeys(item).some(key=>!['id','question','state','note','records','followup'].includes(key))||!['id','question','state','note','records'].every(key=>Object.hasOwn(item,key))||Object.values(Object.getOwnPropertyDescriptors(item)).some(field=>!Object.hasOwn(field,'value'))||!slug(item.id)||seen.has(item.id)||!prose(item.question,300)||!prose(item.note,700)||!['tested','open'].includes(item.state)||!Array.isArray(item.records)||item.records.length>12||Array.from(item.records).some(id=>!slug(id)||id===record.id)||new Set(item.records).size!==item.records.length)return [];
   if(item.state==='tested'&&!item.records.length)return [];
   if(Object.hasOwn(item,'followup')&&(!slug(item.followup)||linked.has(item.followup)||!recipes.some(recipe=>recipe.id===item.followup)))return [];
   if(Object.hasOwn(item,'followup'))linked.add(item.followup);
   seen.add(item.id);
  }
  return record.research_questions.slice().sort((a,b)=>(a.state==='open'?0:1)-(b.state==='open'?0:1));
 }
 const api={questions};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
