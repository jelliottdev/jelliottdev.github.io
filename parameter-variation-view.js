/* Presentation only: the controller verifies sources and creates reviewed variations. */
(function(root){
 'use strict';
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const text=value=>typeof value==='string'?value.trim():'';
 const phases=new Set(['choose','previewing','review','creating','error','complete']);
 function selectionEqual(a,b){return !!a&&!!b&&a.step===b.step&&a.parameter===b.parameter&&a.value===b.value;}
 function reset(value){return ({page:'each page',line:'each line',word:'each word'})[value]||'';}
 function setting(selection,value){return selection.parameter==='direction'?({add:'Add the key values',subtract:'Subtract the key values'})[value]||'':reset(value)?'Restart the key at '+reset(value):'';}
 function href(value){return typeof value==='string'&&/^run\.html#(?:task=[a-f0-9]{64}(?:&idea=p_[a-f0-9]{64})?|idea=p_[a-f0-9]{64})$/.test(value)?value:'';}
 function pageLabel(pages){
  if(typeof pages==='string')return pages;
  if(!Array.isArray(pages)||!pages.length)return '';
  const ids=pages.map(p=>typeof p==='string'?p:p?.id).filter(p=>typeof p==='string');
  if(ids.length!==pages.length)return '';
  const matches=ids.map(id=>/^(lp[12])-(\d{2})$/i.exec(id));
  if(matches.every(Boolean)&&matches.every((m,i)=>m[1].toLowerCase()===matches[0][1].toLowerCase()&&(!i||Number(m[2])===Number(matches[i-1][2])+1)))return ids.length===1?ids[0].toUpperCase():ids[0].toUpperCase()+'–'+matches.at(-1)[2];
  return ids.map(id=>id.toUpperCase()).join(', ');
 }
 function model(input={}){
  const choices=(Array.isArray(input.choices)?input.choices:[]).map((choice,index)=>{
   const s=choice?.selection;
   if(!s||!Number.isInteger(s.step)||s.step<0||!['direction','reset'].includes(s.parameter)||!setting(s,s.value))return null;
   const describe=value=>choice.op==='cumulative-difference'&&s.parameter==='reset'&&reset(value)?'Restart the running total at '+reset(value):setting(s,value);
   return {index,selection:{...s},question:text(choice.question),reason:text(choice.reason),reading:text(choice.reading),resetExample:s.parameter==='reset'&&reset(choice.from)&&choice.from!==s.value?{before:choice.from,after:s.value}:null,label:text(choice.question)||text(choice.label)||describe(s.value)+(s.parameter==='direction'?' instead':''),stepLabel:Object.hasOwn(choice,'stepLabel')?text(choice.stepLabel):'Step '+(s.step+1),before:text(choice.before)||describe(choice.from),after:text(choice.after)||describe(s.value)};
  }).filter(Boolean).slice(0,3);
  const selected=choices.find(c=>typeof input.selected==='number'?c.index===input.selected:selectionEqual(c.selection,input.selected))||null;
  const phase=phases.has(input.phase)?input.phase:'choose',change=input.change||{},scope=input.scope||{};
  const steps=(Array.isArray(input.steps)?input.steps:[]).filter(s=>Number.isInteger(s?.index)&&s.index>=0).filter((s,i,all)=>all.findIndex(other=>other.index===s.index)===i).map(s=>({index:s.index,label:text(s.label)||'Step '+(s.index+1)}));
  const stepIndex=steps.some(s=>s.index===input.stepIndex)?input.stepIndex:steps[0]?.index;
  return {choices,selected,steps,stepIndex,phase,change:{before:text(change.before)||selected?.before||'',after:text(change.after)||selected?.after||'',stepLabel:text(change.stepLabel)||selected?.stepLabel||''},scope:{pages:pageLabel(scope.pages)||text(scope.label),key:text(scope.key),keyLabel:text(scope.keyLabel)||'Key',comparison:text(scope.comparison)},error:text(input.error),check:{href:href(input.check?.href),covered:input.check?.covered===true,title:text(input.check?.title)}};
 }
 function resetIllustration(example){
  if(!example)return '';
  function sequence(mode){return Array.from({length:2},(_,line)=>'<div class="parameter-variation-example-line">'+Array.from({length:2},(_,word)=>'<span class="parameter-variation-example-word">'+Array.from({length:2},(_,rune)=>'<span>'+((mode==='page'?line*4+word*2:mode==='line'?word*2:0)+rune+1)+'</span>').join('')+'</span>').join('')+'</div>').join('');}
  return '<figure class="parameter-variation-example"><figcaption>Where the count starts over</figcaption><div class="parameter-variation-example-pair">'+[['Before',example.before],['After',example.after]].map(([label,mode])=>'<div><p>'+label+' · '+esc(reset(mode))+'</p><div aria-label="'+label+': rune count restarts at '+esc(reset(mode))+'">'+sequence(mode)+'</div></div>').join('')+'</div><p>Example: four short words on two lines. Numbers count runes since the last restart; they are not key values or results.</p></figure>';
 }
 function render(input={}){
  const m=model(input);if(!m.choices.length&&m.phase!=='complete')return '';
  let body='<h2>'+esc(m.phase==='choose'?'Try a variation':m.selected?.question||(m.phase==='complete'?'Check ready':'Review the change'))+'</h2>';
  if(m.phase==='complete'){
   body+='<p role="status">'+(m.check.covered?'This calculation already has saved results.':'Your check is ready.')+'</p>'+(m.check.href?'<a class="parameter-variation-primary" href="'+esc(m.check.href)+'">'+(m.check.covered?'View saved results':'Open check')+'</a>':'');
  }else if(m.phase==='choose'){
   body+='<p>Change one part of this calculation.</p>'+(m.steps.length>1?'<label class="parameter-variation-step-select">Change which step?<select data-parameter-variation-step>'+m.steps.map(s=>'<option value="'+s.index+'"'+(s.index===m.stepIndex?' selected':'')+'>'+esc(s.label)+'</option>').join('')+'</select></label>':'')+'<div class="parameter-variation-choices">'+m.choices.map(c=>'<button type="button" data-parameter-variation="select" data-variation-index="'+c.index+'">'+(c.stepLabel?'<span class="parameter-variation-step">'+esc(c.stepLabel)+'</span>':'')+esc(c.label)+'</button>').join('')+'</div>';
  }else{
   body+=(m.selected?.reason?'<p>'+esc(m.selected.reason)+'</p>':'')+(m.change.stepLabel?'<p class="parameter-variation-step">'+esc(m.change.stepLabel)+'</p>':'');
   body+=m.selected?.question&&m.selected.resetExample?resetIllustration(m.selected.resetExample):'<dl class="parameter-variation-change"><div><dt>Before</dt><dd>'+esc(m.change.before)+'</dd></div><div><dt>After</dt><dd>'+esc(m.change.after)+'</dd></div></dl>';
   body+='<p class="parameter-variation-scope">Applies to the full original calculation'+(m.scope.pages?': <strong>'+esc(m.scope.pages)+'</strong>':'.')+'</p>';
   const same=[m.scope.key&&[m.scope.keyLabel,m.scope.key],m.scope.comparison&&['Comparison',m.scope.comparison]].filter(Boolean);
   if(same.length)body+='<dl class="parameter-variation-same">'+same.map(([label,value])=>'<div><dt>'+esc(label)+' · unchanged</dt><dd>'+esc(value)+'</dd></div>').join('')+'</dl>';
   if(m.selected?.reading)body+='<p class="parameter-variation-reading">'+esc(m.selected.reading)+'</p>';
   if(m.phase==='previewing')body+='<p role="status" aria-live="polite">Reviewing this change…</p>';
   if(m.phase==='creating')body+='<p role="status" aria-live="polite">Preparing check…</p>';
   if(m.phase==='error')body+='<p class="parameter-variation-error" role="alert">'+esc(m.error||'The variation could not be created. Try again.')+'</p>';
   body+='<div class="parameter-variation-actions">'+(['creating','previewing'].includes(m.phase)?'':'<button type="button" class="parameter-variation-primary" data-parameter-variation="'+(m.phase==='error'?'retry':'create')+'">'+(m.phase==='error'?'Try again':'Create check')+'</button>')+'<button type="button" data-parameter-variation="cancel">Cancel</button></div>';
  }
  return '<section class="parameter-variation" aria-label="Change this calculation"'+(['creating','previewing'].includes(m.phase)?' aria-busy="true"':'')+'>'+body+'</section>';
 }
 function bind(host,actions={},input={}){
  const m=model(input),removers=[];
  for(const button of host.querySelectorAll?.('[data-parameter-variation]')||[]){
   const action=button.getAttribute('data-parameter-variation');
   const listener=()=>{if(action==='select'){const c=m.choices.find(choice=>choice.index===Number(button.getAttribute('data-variation-index')));if(c)actions.select?.(c.index,c);}else if(['create','cancel','retry'].includes(action))actions[action]?.();};
   button.addEventListener('click',listener);removers.push(()=>button.removeEventListener('click',listener));
  }
  const stepSelect=host.querySelector?.('[data-parameter-variation-step]');
  if(stepSelect){const change=event=>{const value=event?.target?.value;if(!/^(0|[1-9][0-9]*)$/.test(value))return;const index=Number(value);if(m.steps.some(step=>step.index===index))actions.step?.(index);};stepSelect.addEventListener('change',change);removers.push(()=>stepSelect.removeEventListener('change',change));}
  return ()=>removers.forEach(remove=>remove());
 }
 const api={model,render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.ParameterVariationView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
