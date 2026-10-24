/* Shared result view. All conclusions and chart values come from replayed data. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const bindings=new WeakMap();
 function pageLabel(pages){
  const groups=[];for(const page of pages){const id=page.id,last=groups.at(-1);if(last&&last.at(-1).slice(0,4)===id.slice(0,4)&&Number(last.at(-1).slice(4))+1===Number(id.slice(4)))last.push(id);else groups.push([id]);}
  return groups.map(group=>group[0].toUpperCase()+(group.length>1?'–'+group.at(-1).slice(4):'')).join(', ')+(pages.length>1?' ('+pages.length+' pages)':'');
 }
 function transliteration(text,alphabet){
  const labels=new Map(alphabet.map(entry=>[entry.rune,entry.latin]));let previousRune=false,out='';
  for(const character of text){const rune=labels.has(character);out+=(rune&&previousRune?'·':'')+(rune?labels.get(character):character);previousRune=rune;}
  return out;
 }
 function inspector(task,result){
  const first=task.pages[0],after=result.transformed.find(page=>page.page===first.id);
  return '<details class="run-text-inspector"><summary>Inspect the text</summary><div class="run-text-controls">'+
   (task.pages.length>1?'<label class="run-text-page">Page<select data-run-text-page>'+task.pages.map(page=>'<option value="'+esc(page.id)+'">'+esc(page.id.toUpperCase())+'</option>').join('')+'</select></label>':'<p class="run-text-single">'+esc(first.id.toUpperCase())+'</p>')+
   '<div class="run-text-modes" role="group" aria-label="Text representation"><button type="button" data-run-text-mode="runes" aria-pressed="true">Runes</button><button type="button" data-run-text-mode="latin" aria-pressed="false">Transliteration</button></div></div>'+
   '<p class="run-text-note">Transliteration shows rune labels, not a translation. A middle dot (·) separates adjacent labels; original spaces, punctuation and line breaks remain.</p>'+
   '<div class="run-text-columns"><section><h3>Original</h3><pre class="run-text-value" data-run-original>'+esc(first.text)+'</pre></section><section><h3>After the method</h3><pre class="run-text-value" data-run-after>'+esc(after.text)+'</pre></section></div></details>';
 }
 function bind(host,task,result){
  bindings.get(host)?.();
  E.summary(task,result);const snapshot=JSON.parse(JSON.stringify({task,result}));
  const panel=host.querySelector?.('.run-text-inspector');if(!panel)return ()=>{};
  const select=panel.querySelector('[data-run-text-page]'),buttons=[...panel.querySelectorAll('[data-run-text-mode]')];
  const original=panel.querySelector('[data-run-original]'),after=panel.querySelector('[data-run-after]');
  if(!original||!after)return ()=>{};
  let pageId=snapshot.task.pages[0].id,mode='runes';const listeners=[];
  const update=()=>{
   const page=snapshot.task.pages.find(p=>p.id===pageId),output=snapshot.result.transformed.find(p=>p.page===pageId);
   original.textContent=mode==='latin'?transliteration(page.text,snapshot.task.alphabet):page.text;
   after.textContent=mode==='latin'?transliteration(output.text,snapshot.task.alphabet):output.text;
   panel.dataset.textMode=mode;
   buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.getAttribute('data-run-text-mode')===mode)));
  };
  const listen=(node,event,fn)=>{node.addEventListener(event,fn);listeners.push(()=>node.removeEventListener?.(event,fn));};
  if(select)listen(select,'change',()=>{if(snapshot.task.pages.some(p=>p.id===select.value)){pageId=select.value;update();}});
  buttons.forEach(button=>listen(button,'click',()=>{const chosen=button.getAttribute('data-run-text-mode');if(['runes','latin'].includes(chosen)){mode=chosen;update();}}));
  update();const cleanup=()=>listeners.forEach(remove=>remove());bindings.set(host,cleanup);return cleanup;
 }
 function render(task,result){
  const data=E.summary(task,result),max=Math.max(1,...data.comparison.map(r=>r.value));
  return '<section class="local-run-result" aria-labelledby="local-run-finding"><p class="run-state">Computation verified</p><h2 id="local-run-finding">What this run found</h2><p>'+esc(data.finding)+'</p>'+
   '<figure class="local-run-chart"><figcaption>Repeated neighbouring runes</figcaption><div role="img" aria-label="'+esc(data.comparison.map(r=>r.label+': '+r.value+' of '+r.total+' pairs').join('. '))+'">'+
   data.comparison.map((row,i)=>'<div class="run-bar-row"><span>'+esc(row.label)+'</span><div class="run-bar-track"><span class="run-bar run-bar-'+i+'" style="width:'+(row.value/max*100).toFixed(4)+'%"></span></div><strong>'+row.value+'</strong></div>').join('')+
   '</div><p class="run-chart-note">Counts follow the rune sequence on each page, ignoring spaces and punctuation.</p></figure>'+
   '<p class="run-limit">'+esc(data.limit)+'</p><dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'</section>';
 }
 const api={render,bind,pageLabel};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
