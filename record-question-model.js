/* Shared authored question states. Tested links permit reproduction, never new-work claims. */
(function(root){
 'use strict';
 const slug=value=>typeof value==='string'&&value.length<=100&&/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value);
 const prose=(value,max)=>typeof value==='string'&&value.length>0&&value.length<=max&&!/[<>\x00-\x1f\x7f\[\]`*\\\u2028\u2029\ud800-\udfff]/u.test(value)&&!/^[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]|[ \x85\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]$/u.test(value);
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const exact=(value,keys)=>object(value)&&Reflect.ownKeys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
 const clone=value=>JSON.parse(JSON.stringify(value)),hex=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 function pinnedScope(inputs,scope){return exact(inputs,['version','alphabet_sha256','pages'])&&['raw','reviewed'].includes(inputs.version)&&hex(inputs.alphabet_sha256)&&Array.isArray(inputs.pages)&&inputs.pages.length>0&&inputs.pages.length<=75&&!inputs.pages.some(page=>!exact(page,['id','text_sha256'])||!/^lp[12]-\d{2}$/.test(page.id)||!hex(page.text_sha256))&&new Set(inputs.pages.map(page=>page.id)).size===inputs.pages.length&&scope?.status==='specified'&&exact(scope.value,['pages'])&&JSON.stringify(scope.value.pages)===JSON.stringify(inputs.pages.map(page=>page.id));}
 // Cache only bounded, plain, already validated discovery metadata. Every lookup
 // still traverses descriptors so mutations and accessors cannot reuse a result.
 const finiteMetadata=new Map(),CACHE_ENTRIES=64,CACHE_BYTES=16*1024*1024,CACHE_KEY_BYTES=2*1024*1024;let finiteMetadataBytes=0;
 function metadataKey(recipe,cacheable){if(!cacheable)return null;const key=JSON.stringify(recipe);if(key.length>CACHE_KEY_BYTES)return null;const bytes=new TextEncoder().encode(key).byteLength;return bytes<=CACHE_KEY_BYTES?{key,bytes}:null;}
 function rememberMetadata(identity,value){const result=Object.freeze(value);if(identity){while(finiteMetadata.size&&(finiteMetadata.size>=CACHE_ENTRIES||finiteMetadataBytes+identity.bytes>CACHE_BYTES)){const oldest=finiteMetadata.keys().next().value;finiteMetadataBytes-=finiteMetadata.get(oldest).bytes;finiteMetadata.delete(oldest);}finiteMetadata.set(identity.key,{value:result,bytes:identity.bytes});finiteMetadataBytes+=identity.bytes;}return result;}
 const settingsAPI=()=>typeof module==='object'&&module.exports?require('./finite-settings.js'):root.FiniteSettings;
 // Discovery metadata only: canonical settings and source-shaped controls permit
 // a review link. The maintained loader still verifies every executable member.
 function finiteRecipe(recipe){
  try{
   let nodes=0,characters=0,cacheable=true;const plain=(value,depth=0)=>{
    if(depth>24||++nodes>1000000)return false;
    if(value===null||typeof value==='boolean')return true;
    if(typeof value==='number')return Number.isFinite(value);
    if(typeof value==='string'){characters+=value.length;return characters<=8*1024*1024;}
    if(!object(value)&&!Array.isArray(value))return false;
    if(Object.getPrototypeOf(value)!==(Array.isArray(value)?Array.prototype:Object.prototype)&&Object.getPrototypeOf(value)!==null)cacheable=false;
    const keys=Reflect.ownKeys(value),descriptors=Object.getOwnPropertyDescriptors(value);
    if(Array.isArray(value)&&keys.length!==value.length+1)return false;
    return keys.every(key=>key==='length'&&Array.isArray(value)||typeof key==='string'&&!['__proto__','constructor','prototype'].includes(key)&&Object.hasOwn(descriptors[key],'value')&&descriptors[key].enumerable&&plain(descriptors[key].value,depth+1));
   };
   if(!plain(recipe)||recipe.kind!=='finite-settings')return null;
   const Settings=settingsAPI();if(!Settings?.factored?.inspect||!Settings.factored.member)return null;
   const identity=metadataKey(recipe,cacheable),cached=identity&&finiteMetadata.get(identity.key);if(cached){finiteMetadata.delete(identity.key);finiteMetadata.set(identity.key,cached);return cached.value;}
   const card=recipe.card,inputs=recipe.inputs,criterion=card?.rules?.evaluation;
   if(card?.version!==1||card.unresolved.length||criterion?.status!=='specified'||!pinnedScope(inputs,card.scope)||card.rules.inputVersion?.status!=='specified'||card.rules.inputVersion.value!==inputs.version)return null;
   const c=criterion.value,language=exact(c,['kind','modelId','modelSha256'])&&c.kind==='language-score'&&c.modelId==='gp29-flores-trigram-v1'&&c.modelSha256==='8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4',prefix=exact(c,['kind','values'])&&c.kind==='exact-prefix'&&Array.isArray(c.values)&&c.values.length>0&&c.values.length<=256&&c.values.every(n=>Number.isInteger(n)&&n>=0&&n<=28);
   if(!prefix&&!language&&c!=='measurement')return null;
   const Storage=typeof module==='object'&&module.exports?require('./finite-control-storage.js'):root.FiniteControlStorage;
   const declaration=Settings.factored.inspect(card),control=Storage?Storage.expand(recipe.control):recipe.control;
   if(!exact(control,['kind','members'])||control.kind!=='finite-program-controls'||!Array.isArray(control.members)||control.members.length!==declaration.programCount||control.members.length>1024)return null;
   const seen=new Set();
   for(const member of control.members){
    if(!exact(member,['settings','control']))return null;
    const selected=Settings.factored.member(card,member.settings),identity=JSON.stringify(selected.settings),test=member.control,task=test?.task;
    if(seen.has(identity)||!exact(test,['label','task','expected_result_sha256'])||!prose(test.label,300)||!hex(test.expected_result_sha256)||!object(task)||task.schema!=='liberpedia-local-task-v1'||task.engine!=='rune-program-v1'||!hex(task.taskId)||!Array.isArray(task.steps)||task.steps.length>8||!Array.isArray(task.alphabet)||task.alphabet.length!==29||!Array.isArray(task.pages)||task.pages.length!==1||!exact(task.pages[0],['id','text'])||!/^lp[12]-\d{2}$/.test(task.pages[0].id)||typeof task.pages[0].text!=='string'||!exact(task.criterion,['kind','values'])||task.criterion.kind!=='exact-prefix'||!Array.isArray(task.criterion.values)||task.criterion.values.length<1||task.criterion.values.length>256||task.criterion.values.some(n=>!Number.isInteger(n)||n<0||n>28))return null;
    const runes=new Set(task.alphabet.map(entry=>entry?.rune));if(runes.size!==29||[...runes].some(rune=>typeof rune!=='string'||Array.from(rune).length!==1)||Array.from(task.pages[0].text).filter(rune=>runes.has(rune)).length!==task.criterion.values.length)return null;
    seen.add(identity);
   }
   return rememberMetadata(identity,{kind:'finite-settings',programCount:declaration.programCount,caseCount:declaration.caseCount});
  }catch{return null;}
 }
 function resolveProtocol(item,recipes){
  const p=item.protocol;if(!exact(p,['id','version'])||p.version!==1)return null;
  if(p.id==='deor-warning-opening')return Object.hasOwn(item,'followup')?null:{id:p.id,version:1,familyId:'deor-feedback-v1'};
  if(!['word-boundary-sensitivity','fixed-program-prefix','finite-settings-output'].includes(p.id)||!Object.hasOwn(item,'followup'))return null;
  const owned=recipes.filter(recipe=>recipe?.id===item.followup);if(owned.length!==1)return null;
  const recipe=owned[0],card=recipe.card,inputs=recipe.inputs,method=card?.method,rules=card?.rules,c=rules?.evaluation?.value,scope=card?.scope;
  if(recipe.kind==='finite-settings'&&p.id!=='finite-settings-output')return null;
  if(p.id==='finite-settings-output'){if(!finiteRecipe(recipe))return null;return {id:p.id,version:1,followupId:recipe.id,inputs:clone(inputs)};}
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
 function questions(record,recipes=[],{strictAuthoring=false}={}){
  if(!object(record)||!slug(record.id)||!Array.isArray(record.research_questions)||record.research_questions.length<1||record.research_questions.length>12)return [];
  const seen=new Set(),linked=new Set(),projected=[];
  for(const item of record.research_questions){
   if(!object(item)||Reflect.ownKeys(item).some(key=>!['id','question','state','note','records','followup','protocol'].includes(key))||!['id','state','note','records'].every(key=>Object.hasOwn(item,key))||Object.values(Object.getOwnPropertyDescriptors(item)).some(field=>!Object.hasOwn(field,'value'))||!slug(item.id)||seen.has(item.id)||Object.hasOwn(item,'question')&&!prose(item.question,300)||!prose(item.note,700)||!['tested','open'].includes(item.state)||!Array.isArray(item.records)||item.records.length>12||Array.from(item.records).some(id=>!slug(id)||id===record.id)||new Set(item.records).size!==item.records.length)return [];
   if(item.state==='tested'&&!item.records.length)return [];
   if(Object.hasOwn(item,'followup')&&(!slug(item.followup)||linked.has(item.followup)||!recipes.some(recipe=>recipe.id===item.followup)))return [];
   if(Object.hasOwn(item,'followup'))linked.add(item.followup);
   const resolved=Object.hasOwn(item,'protocol')?resolveProtocol(item,recipes):null;if(Object.hasOwn(item,'protocol')&&!resolved)return [];
   const owned=resolved?.followupId?recipes.filter(recipe=>recipe.id===resolved.followupId):[],property=owned.length===1?Object.getOwnPropertyDescriptor(owned[0],'question'):null;
   const canonical=property&&Object.hasOwn(property,'value')&&prose(property.value,1200)?property.value:null;
   if(resolved?.followupId&&!canonical||!canonical&&!Object.hasOwn(item,'question'))return [];
   // Historical published aliases remain readable, but never determine the
   // executable question. New authors may omit this duplicate altogether.
   if(strictAuthoring&&canonical&&Object.hasOwn(item,'question')&&item.question!==canonical)return [];
   projected.push(canonical?{...item,question:canonical}:item);seen.add(item.id);
  }
  return projected.sort((a,b)=>(a.state==='open'?0:1)-(b.state==='open'?0:1));
 }
 function protocolReference(record,questionId,recipes=record?.browser_followups||[]){const item=questions(record,recipes).find(item=>item.id===questionId);return item&&Object.hasOwn(item,'protocol')?resolveProtocol(item,recipes):null;}
 const api={questions,protocolReference,finiteRecipe};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordQuestionModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
