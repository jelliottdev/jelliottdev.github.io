/* The question at a glance. Presentation only; task links are not coverage evidence. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,H=node?require('./claim-share.js'):root.ClaimShare,J=node?require('./finite-json.js'):root.FiniteJSON;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const text=v=>typeof v==='string'?v.trim():'',IDEA=/^p_[a-f0-9]{64}$/,HEX=/^[a-f0-9]{64}$/;
 function action(op,card){
  if(op.id==='reverse_runes'&&['word','line','page'].includes(op.unit))return 'Reverse rune order within each '+op.unit;
  if(op.id==='reverse_row_runes')return card.rules.boundaryMode.status==='specified'&&card.rules.boundaryMode.value==='within_words'?'Reverse rune order within each word':'Reverse rune order within rows';
  if(op.id==='affine')return op.a===28&&op.b===28?'Use the reversed rune alphabet':'Transform rune positions with a formula';
  if(['vigenere','repeating_key'].includes(op.id))return 'Use a repeating key';
  if(op.id==='plaintext_autokey')return 'Extend a key using decoded runes';
  if(op.id==='ciphertext_autokey')return 'Extend a key using input runes';
  if(op.id==='interrupted_repeating_key')return 'Use a repeating key with pauses';
  if(['finite_key','finite_key_bank'].includes(op.id))return 'Use a number sequence as the key';
  if(op.id==='cumulative_difference')return 'Subtract a running total of rune values';
  if(op.id==='word_prime_sums'&&['canonical','reversed'].includes(op.table))return op.table==='reversed'?'Add reversed-table rune values within words':'Add rune values within each word';
  if(op.id==='word_affine_count')return op.a===1&&op.b===0?'Count repeated runes inside words':'Count a rune relation inside words';
  return null;
 }
 function compactTitle(steps){
  if(steps.length===1){const step=steps[0],literal=step.text.replace(/[.!?]$/,'');return step.action||literal.length<=100&&!/[\n\r{}<>`]/.test(literal)&&literal||'Research question';}
  if(steps.length===2&&steps.every(step=>step.action)){const title=steps[0].action+', then '+steps[1].action.charAt(0).toLowerCase()+steps[1].action.slice(1);if(title.length<=120)return title;}
  return 'Research question';
 }
 function questionIntent(input){
  try{
   const card=J.capture(input,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000});H.sections(card);
   const operations=card.method.status==='specified'?card.method.value.operations:[],opaque=new Set(['described_method','family_selection','ambiguous_reversal']);
   const notes=(Array.isArray(card.unresolved)?card.unresolved:[]).filter(item=>item.kind==='source_note'&&typeof item.text==='string'&&item.text.trim());
   const needsDefinition=!operations.length||operations.some(op=>opaque.has(op.id))||notes.length>0;
   const exceptions=card.rules.exceptionalCases,prefix='Uninterpreted original wording: ',originalIdea=exceptions.status==='specified'&&typeof exceptions.value==='string'&&exceptions.value.startsWith(prefix)&&exceptions.value.length>prefix.length?exceptions.value.slice(prefix.length):notes.length?notes.map(note=>note.text).join('\n\n'):null;
   return {needsDefinition,originalIdea,originalLabel:originalIdea?(exceptions.status==='specified'&&exceptions.value===prefix+originalIdea?'Original idea':'Retained wording'):null,sourceNotes:notes.map(note=>note.text)};
  }catch{return null;}
 }
 function model(input={}){
  try{
   const value=J.capture(input,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000}),card=value.card,rows=H.sections(card),row=name=>rows.find(item=>item[0]===name)?.[1]||'';
   const operations=card.method.status==='specified'?card.method.value.operations:[],steps=operations.map((op,i)=>{const label=row('Step '+(i+1)),parameters=H.operationParameters(op),details=parameters.map(item=>item.label+': '+item.value).join('\n'),visibleItems=parameters.map(item=>{const key=Object.entries(op).find(([name,v])=>Array.isArray(v)&&String(item.label).toLowerCase()===name.toLowerCase());return {label:item.label,value:item.label+': '+(key&&key[1].length>12?key[1].length+' supplied values':item.value)};}),visible=visibleItems.map(item=>item.value).join(' · '),visibleWithoutNamedUnit=visibleItems.filter(item=>!(op.id==='reverse_runes'&&['word','line','page'].includes(op.unit)&&item.label==='Unit')).map(item=>item.value).join(' · ');return {text:label,action:action(op,card),details,visible,visibleWithoutNamedUnit};});
   const intent=questionIntent(card),scope=row('Scope'),check=row('Evaluation')||'What to check has not been chosen.',objective=row('Outcome'),skip=new Set(['Outcome','Scope','Evaluation','Input version','Representation','Other rules']);
   const conditions=rows.filter(([label])=>!(label==='Exceptions'&&intent.originalIdea&&card.rules.exceptionalCases.value==='Uninterpreted original wording: '+intent.originalIdea)&&!(label==='Unresolved'&&intent.originalIdea&&card.unresolved.every(item=>item.kind==='source_note'))&&!skip.has(label)&&!/^Step \d+$/.test(label)&&label!=='Method').map(([label,value])=>({label,value:label==='Unresolved'?card.unresolved.filter(item=>!(intent.originalIdea&&item.kind==='source_note')).map(item=>text(item.text)||text(item.reason)||'Some supplied details still need clarification.').join(' · '):value,...(label==='Word boundaries'&&card.rules.wordBoundaries.status==='specified'&&card.rules.wordBoundaries.value==='preserve'?{plain:'Keep word boundaries'}:label==='Unmapped values'&&card.rules.unmapped.status==='specified'&&card.rules.unmapped.value==='preserve'?{plain:'Leave non-rune characters unchanged'}:{})}));
   const ideaId=typeof value.ideaId==='string'&&IDEA.test(value.ideaId)?value.ideaId:null,seen=new Set(),navigation=(Array.isArray(value.tasks)?value.tasks:[]).filter(task=>task&&typeof task.id==='string'&&HEX.test(task.id)&&!seen.has(task.id)&&['not-run','results-verified'].includes(task.state)&&(seen.add(task.id),true)).map(task=>({id:task.id,title:text(task.title)||'Open calculation',state:task.state,href:ideaId?'run.html#task='+task.id+'&idea='+ideaId:null})).filter(task=>task.href),selected=navigation.find(task=>task.state==='results-verified')||navigation[0]||null;
   const primary=selected?{href:selected.href,label:selected.state==='results-verified'?'View saved result':'Continue check'}:null;
   return {title:compactTitle(steps),intent,objective,steps,scope,check,conditions,navigation,primary,tasksTruncated:value.tasksTruncated===true};
  }catch{return null;}
 }
 function methodHTML(m,options){
  if(!m.steps.length)return '<p>The method has not been specified.</p>';
  const literal=step=>step.action&&step.action!==step.text&&step.text&&!/^[a-z_]+$/.test(step.text)&&!/^(Affine substitution|Affine|Vigen[eè]re|Repeating key|Plaintext autokey|Ciphertext autokey|Finite key stream|Interrupted repeating key|Cumulative difference|Word prime sums|Word affine count)$/i.test(step.text);
  const content=(step,omitAction)=>{const visible=omitAction?step.visibleWithoutNamedUnit:step.visible;return (!omitAction?'<p>'+esc(step.action||step.text)+'</p>':'')+(literal(step)?'<p class="question-summary-wording">'+esc(step.text)+'</p>':'')+(visible?'<p class="question-summary-settings">'+esc(visible)+'</p>':'');};
  const step=m.steps[0],sameTitle=m.steps.length===1&&m.title!=='Research question'&&m.title===(step.action||step.text.replace(/[.!?]$/,''));
  if(options.titleShown===true&&sameTitle){const body=content(step,true);return body?'<div class="question-summary-method-detail">'+body+'</div>':'';}
  return '<ol class="question-summary-method">'+m.steps.map(step=>'<li>'+content(step,false)+'</li>').join('')+'</ol>';
 }
 function render(input={},options={}){
  const m=model(input);if(!m)return '';
  return '<section class="question-summary" aria-label="Research question">'+(options.heading===true?'<h1>'+esc(m.title)+'</h1>':'')+methodHTML(m,options)+'<dl class="question-summary-facts"><div><dt>Scope</dt><dd>'+esc(m.scope)+'</dd></div><div><dt>What it checks</dt><dd>'+esc(m.check)+'</dd></div></dl>'+(m.conditions.length?'<p class="question-summary-conditions"><strong>Conditions:</strong> '+m.conditions.map(item=>item.plain?esc(item.plain):esc(item.label)+': '+esc(item.value)).join(' · ')+'</p>':'')+(m.intent.originalIdea?'<details class="question-original"><summary>'+esc(m.intent.originalLabel)+'</summary><p>'+esc(m.intent.originalIdea)+'</p></details>':'')+(m.objective?'<p class="question-summary-objective"><strong>Aim:</strong> '+esc(m.objective)+'</p>':'')+(options.navigation!==false&&m.primary?'<a class="question-summary-primary" href="'+esc(m.primary.href)+'">'+esc(m.primary.label)+'</a>':'')+'</section>';
 }
 const api={questionIntent,model,render};if(node)module.exports=api;else root.QuestionSummaryView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
