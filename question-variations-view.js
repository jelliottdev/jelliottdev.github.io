/* Presentation only: relationship validation and loading belong to the caller. */
(function(root){
 'use strict';
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const text=value=>typeof value==='string'?value.trim():'';
 const questionHref=value=>typeof value==='string'&&/^run\.html#idea=p_[a-f0-9]{64}$/.test(value)?value:'';
 const sourceHref=value=>typeof value==='string'&&/^run\.html#published=[a-z0-9]+(?:-[a-z0-9]+)*&case=[a-z0-9][a-z0-9-]*&revision=[a-f0-9]{64}$/.test(value)?value:'';
 function entries(values,direction){
  const seen=new Set();return (Array.isArray(values)?values:[]).map(value=>{
   if(!value||value.direction!==direction||!questionHref(value.href))return null;
   const id=text(value.id),href=questionHref(value.href);if(!id||seen.has(href))return null;seen.add(href);
   return {id,href,label:text(value.label)||(direction==='parents'?'Open original question':'Open variation'),description:text(value.description),sourceHref:sourceHref(value.sourceHref)};
  }).filter(Boolean);
 }
 function model(input={}){return {parents:entries(input.parents,'parents'),children:entries(input.children,'children'),loading:input.loading===true,error:text(input.error),moreParents:input.moreParents===true,moreChildren:input.moreChildren===true};}
 function render(input={}){
  const m=model(input);if(!m.parents.length&&!m.children.length&&!m.moreParents&&!m.moreChildren&&!m.error)return '';
  const group=(values,title,more,kind)=>!values.length&&!more?'':'<div class="question-variations-group"><h2>'+title+'</h2>'+(values.length?'<ul>'+values.map(value=>'<li><a class="question-variations-question" href="'+esc(value.href)+'">'+(kind==='parents'?'Original question':esc(value.label))+'</a>'+(kind==='parents'&&!value.description?'<p class="question-variations-change">This question changes: '+esc(value.label)+'.</p>':'')+(value.description?'<p>'+esc(value.description)+'</p>':'')+(value.sourceHref?'<a class="question-variations-source" href="'+esc(value.sourceHref)+'">Original calculation</a>':'')+'</li>').join('')+'</ul>':'')+(more?'<button type="button" data-question-variations="more-'+kind+'"'+(m.loading?' disabled':'')+'>Show more '+(kind==='parents'?'original questions':'variations')+'</button>':'')+'</div>';
  return '<section class="question-variations" aria-label="Related questions"'+(m.loading?' aria-busy="true"':'')+'>'+group(m.parents,'Based on',m.moreParents,'parents')+group(m.children,'Variations of this question',m.moreChildren,'children')+(m.error?'<div class="question-variations-error"><p role="alert">'+esc(m.error)+'</p><button type="button" data-question-variations="retry"'+(m.loading?' disabled':'')+'>Try again</button></div>':'')+'</section>';
 }
 function bind(host,actions={},input={}){
  const m=model(input),cleanup=[],callbacks={'more-parents':'moreParents','more-children':'moreChildren',retry:'retry'};
  for(const button of host.querySelectorAll?.('[data-question-variations]')||[]){
   const action=button.getAttribute('data-question-variations');
   if(!callbacks[action])continue;
   const click=()=>{if(m.loading||action==='more-parents'&&!m.moreParents||action==='more-children'&&!m.moreChildren||action==='retry'&&!m.error)return;actions[callbacks[action]]?.();};
   button.addEventListener('click',click);cleanup.push(()=>button.removeEventListener('click',click));
  }
  return ()=>cleanup.forEach(remove=>remove());
 }
 const api={model,render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.QuestionVariationsView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
