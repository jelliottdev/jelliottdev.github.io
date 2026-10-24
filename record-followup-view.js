/* Shared record actions. This view links to plan review; the plan loader verifies execution readiness. */
(function(root){
 'use strict';
 const slug=value=>typeof value==='string'&&value.length<=100&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
 const text=(value,max)=>typeof value==='string'&&value.trim().length>0&&Array.from(value).length<=max;
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function recipes(record){
  if(!object(record)||!slug(record.id)||!Array.isArray(record.browser_followups)||record.browser_followups.length>8)return [];
  const seen=new Set();return record.browser_followups.filter(item=>{
   if(!object(item)||!slug(item.id)||seen.has(item.id)||!text(item.title,300)||!text(item.scope_change,1200)||!text(item.question,1200)||!text(item.limitation,1200))return false;
   const pins=item.inputs,control=item.control,task=control?.task;
   if(!object(item.card)||item.card.version!==1||!object(pins)||!['raw','reviewed'].includes(pins.version)||!hash(pins.alphabet_sha256)||!Array.isArray(pins.pages)||!pins.pages.length||pins.pages.length>75||pins.pages.some(p=>!object(p)||!/^lp[12]-\d{2}$/.test(p.id)||!hash(p.text_sha256))||new Set(pins.pages.map(p=>p.id)).size!==pins.pages.length)return false;
   if(!object(control)||!text(control.label,300)||!hash(control.expected_result_sha256)||!object(task)||task.schema!=='liberpedia-local-task-v1'||task.engine!=='rune-program-v1'||!hash(task.taskId)||!Array.isArray(task.steps)||!Array.isArray(task.alphabet)||task.alphabet.length!==29||task.criterion?.kind!=='exact-prefix'||!Array.isArray(task.criterion.values)||!task.criterion.values.length)return false;
   seen.add(item.id);return true;
  });
 }
 const href=(record,item)=>'run.html#record='+record.id+'&followup='+item.id;
 function render(record,{headingLevel=3,selectId='prepared-followup-setting'}={}){
  const items=recipes(record);if(!items.length)return '';
  const level=[2,3,4].includes(headingLevel)?headingLevel:3,id=/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(selectId)?selectId:'prepared-followup-setting',first=items[0];
  return '<section class="record-followups"><h'+level+'>Try a follow-up</h'+level+'>'+(items.length>1?'<label for="'+id+'">Setting</label><select id="'+id+'" data-prepared-setting>'+items.map(item=>'<option value="'+item.id+'">'+esc(item.title)+'</option>').join('')+'</select>':'<p class="followup-title"><strong>'+esc(first.title)+'</strong></p>')+'<p data-prepared-scope>'+esc(first.scope_change)+'</p><a data-prepared-link href="'+esc(href(record,first))+'">Review follow-up</a></section>';
 }
 function bind(container,record){
  const select=container?.querySelector('[data-prepared-setting]');if(!select)return;
  const items=recipes(record),scope=container.querySelector('[data-prepared-scope]'),link=container.querySelector('[data-prepared-link]');if(!scope||!link||items.length<2)return;
  let selected=items[0].id;
  select.onchange=()=>{const item=items.find(item=>item.id===select.value);if(!item){select.value=selected;return;}selected=item.id;scope.textContent=item.scope_change;link.href=href(record,item);};
 }
 const api={recipes,render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordFollowupView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
