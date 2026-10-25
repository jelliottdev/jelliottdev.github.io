/* Shared authored question states. Tested links permit reproduction, never new-work claims. */
(function(root){
 'use strict';
 const slug=value=>typeof value==='string'&&value.length<=100&&/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value);
 const prose=(value,max)=>typeof value==='string'&&value.length>0&&value.length<=max&&!/[<>\x00-\x1f\x7f\[\]`*\\\u2028\u2029\ud800-\udfff]/u.test(value)&&!/^[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]|[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]$/u.test(value);
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const exact=(value,keys)=>object(value)&&Reflect.ownKeys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
 const clone=value=>JSON.parse(JSON.stringify(value)),hex=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 function pinnedScope(inputs,scope){return exact(inputs,['version','alphabet_sha256','pages'])&&['raw','reviewed'].includes(inputs.version)&&hex(inputs.alphabet_sha256)&&Array.isArray(inputs.pages)&&inputs.pages.length>0&&inputs.pages.length<=75&&!inputs.pages.some(page=>!exact(page,['id','text_sha256'])||!/^lp[12]-\d{2}$/.test(page.id)||!hex(page.text_sha256))&&new Set(inputs.pages.map(page=>page.id)).size===inputs.pages.length&&scope?.status==='specified'&&exact(scope.value,['pages'])&&JSON.stringify(scope.value.pages)===JSON.stringify(inputs.pages.map(page=>page.id));}
 function resolveProtocol(item,recipes){
  const p=item.protocol;if(!exact(p,['id','version'])||p.version!==1)return null;
  if(p.id==='deor-warning-opening')return Object.hasOwn(item,'followup')?null:{id:p.id,version:1,familyId:'deor-feedback-v1'};
  if(!['word-boundary-sensitivity','fixed-program-prefix'].includes(p.id)||!Object.hasOwn(item,'followup'))return null;
  const owned=recipes.filter(recipe=>recipe?.id===item.followup);if(owned.length!==1)return null;
  const recipe=owned[0],card=recipe.card,inputs=recipe.inputs,method=card?.method,rules=card?.rules,c=rules?.evaluation?.value,scope=card?.scope;
  if(p.id==='fixed-program-prefix'){
   // Metadata permits lazy activation, not an answer. The maintained compiler
   // and exact source pins are checked by the live controller before evidence.
   if(card?.version!==1||!Array.isArray(card.unresolved)||card.unresolved.length||method?.status!=='specified'||!exact(method.value,['operations'])||!Array.isArray(method.value.operations)||!method.value.operations.length||method.value.operations.length>8||method.value.operations.some(op=>!object(op)||typeof op.id!=='string'||!/^[a-z][a-z0-9_]{0,99}$/.test(op.id))||rules?.evaluation?.status!=='specified'||!exact(c,['kind','values'])||c.kind!=='exact-prefix'||!Array.isArray(c.values)||!c.values.length||c.values.length>256||c.values.some(n=>!Number.isInteger(n)||n<0||n>28)||!pinnedScope(inputs,scope)||rules.inputVersion?.status!=='specified'||rules.inputVersion.value!==inputs.version)return null;
   return {id:p.id,version:1,followupId:recipe.id,inputs:clone(inputs)};
  }
  if(card?.version!==1||!Array.isArray(card.unresolved)||card.unresolved.length||method?.status!=='specified'||!exact(method.value,['operations'])||!Array.isArray(method.value.operations)||method.value.operations.length!==1||rules?.evaluation?.status!=='specified'||!exact(c,['kind','lag','a','b','boundaries'])||c.kind!=='word-affine-count'||!Number.isInteger(c.lag)||c.lag<1||c.lag>12||!Number.isInteger(c.a)||c.a<0||c.a>28||!Number.isInteger(c.b)||c.b<0||c.b>28||!['non-rune','hyphen-period'].includes(c.boundaries))return null;
  const operation=method.value.operations[0],fields=['id','lag','a','b','boundaries',...(Object.hasOwn(operation||{},'label')?['label']:[])];
  if(!exact(operation,fields)||operation.id!=='word_affine_count'||Object.hasOwn(operation,'label')&&operation.label!=='Within-word affine pair count'||['lag','a','b','boundaries'].some(k=>operation[k]!==c[k]))return null;
  if(!pinnedScope(inputs,scope))return null;
  const specified={representation:'GP29',wordBoundaries:'preserve',unmapped:'preserve',inputVersion:inputs.version};
  if(Object.entries(specified).some(([k,v])=>!exact(rules[k],['status','value'])||rules[k].status!=='specified'||rules[k].value!==v)||['boundaryMode','reset','initialState','searchBounds','searchProtocol','exceptionalCases'].some(k=>!exact(rules[k],['status'])||rules[k].status!=='not_applicable'))return null;
  return {id:p.id,version:1,followupId:recipe.id,parameters:{lag:c.lag,a:c.a,b:c.b},inputs:clone(inputs)};
 }
 function questions(record,recipes=[]){
  if(!object(record)||!slug(record.id)||!Array.isArray(record.research_questions)||record.research_questions.length<1||record.research_questions.length>12)return [];
  const seen=new Set(),linked=new Set();
  for(const item of record.research_questions){
   if(!object(item)||Reflect.ownKeys(item).some(key=>!['id','question','state','note','records','followup','protocol'].includes(key))||!['id','question','state','note','records'].every(key=>Object.hasOwn(item,key))||Object.values(Object.getOwnPropertyDescriptors(item)).some(field=>!Object.hasOwn(field,'value'))||!slug(item.id)||seen.has(item.id)||!prose(item.question,300)||!prose(item.note,700)||!['tested','open'].includes(item.state)||!Array.isArray(item.records)||item.records.length>12||Array.from(item.records).some(id=>!slug(id)||id===record.id)||new Set(item.records).size!==item.records.length)return [];
   if(item.state==='tested'&&!item.records.length)return [];
   if(Object.hasOwn(item,'followup')&&(!slug(item.followup)||linked.has(item.followup)||!recipes.some(recipe=>recipe.id===item.followup)))return [];
   if(Object.hasOwn(item,'followup'))linked.add(item.followup);
   if(Object.hasOwn(item,'protocol')&&!resolveProtocol(item,recipes))return [];
   seen.add(item.id);
  }
  return record.research_questions.slice().sort((a,b)=>(a.state==='open'?0:1)-(b.state==='open'?0:1));
 }
 function protocolReference(record,questionId,recipes=record?.browser_followups||[]){const item=questions(record,recipes).find(item=>item.id===questionId);return item&&Object.hasOwn(item,'protocol')?resolveProtocol(item,recipes):null;}
 const api={questions,protocolReference};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
