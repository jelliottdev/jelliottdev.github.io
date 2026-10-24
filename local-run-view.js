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
 function prefixAlignment(task,result,pageId,mode='runes'){
  const indices=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),text=result.transformed.find(page=>page.page===pageId).text,observed=Array.from(text).filter(rune=>indices.has(rune)).map(rune=>indices.get(rune)),expected=task.criterion.values;
  const mismatch=expected.findIndex((value,i)=>observed[i]!==value),start=mismatch<0?0:Math.max(0,mismatch-3),end=Math.min(expected.length,start+8),label=value=>value===undefined?'Missing':mode==='latin'?task.alphabet[value].latin:task.alphabet[value].rune;
  const status=mismatch<0?'All '+expected.length+' prefix positions match.':observed[mismatch]===undefined?'The output ends before prefix position '+(mismatch+1)+'.':'First mismatch at prefix position '+(mismatch+1)+'.';
  return '<section class="run-prefix-alignment"><h3>Expected and observed prefix</h3><p class="run-prefix-status">'+esc(pageId.toUpperCase()+': '+status)+'</p><p class="run-text-note">'+'Showing positions '+(start+1)+'–'+end+' of '+expected.length+'. '+'Positions count runes only; separators do not occupy a position.</p><table class="run-prefix-table"><thead><tr><th scope="col">Position</th><th scope="col">Expected</th><th scope="col">Actual</th><th scope="col">Result</th></tr></thead><tbody>'+expected.slice(start,end).map((value,offset)=>{const i=start+offset,missing=observed[i]===undefined,same=value===observed[i];return '<tr class="run-prefix-pair'+(same?'':' is-different')+'"><th scope="row">'+(i+1)+'</th><td class="run-prefix-symbol">'+esc(label(value))+'</td><td'+(missing?'':' class="run-prefix-symbol"')+'>'+esc(label(observed[i]))+'</td><td>'+(same?'Match':missing?'Missing':'Different')+'</td></tr>';}).join('')+'</tbody></table></section>';
 }
 function prefixChart(task,result){
  const matched=result.matches.filter(row=>row.matched).length,total=task.pages.length,notMatched=total-matched;
  return '<figure class="local-run-chart run-prefix-chart"><figcaption>Exact starting-sequence check</figcaption><div class="run-prefix-total" role="img" aria-label="'+matched+' of '+total+' pages matched all '+task.criterion.values.length+' prefix positions; '+notMatched+' did not match."><span class="run-prefix-match" style="width:'+(100*matched/total).toFixed(4)+'%"></span><span class="run-prefix-other" style="width:'+(100*notMatched/total).toFixed(4)+'%"></span></div><dl class="run-prefix-counts"><div><dt>Matched every position</dt><dd>'+matched+' of '+total+' pages</dd></div><div><dt>Did not match</dt><dd>'+notMatched+' of '+total+' pages</dd></div></dl><p class="run-chart-note">The fixed prefix has '+task.criterion.values.length+' rune positions.</p></figure>';
 }
 function inspector(task,result){
  const first=task.pages[0],after=result.transformed.find(page=>page.page===first.id);
  return '<details class="run-text-inspector"><summary>Inspect the text</summary><div class="run-text-controls">'+
   (task.pages.length>1?'<label class="run-text-page">Page<select data-run-text-page>'+task.pages.map(page=>'<option value="'+esc(page.id)+'">'+esc(page.id.toUpperCase())+'</option>').join('')+'</select></label>':'<p class="run-text-single">'+esc(first.id.toUpperCase())+'</p>')+
   '<div class="run-text-modes" role="group" aria-label="Text representation"><button type="button" data-run-text-mode="runes" aria-pressed="true">Runes</button><button type="button" data-run-text-mode="latin" aria-pressed="false">Transliteration</button></div></div>'+
   '<p class="run-text-note">Transliteration shows rune labels, not a translation. A middle dot (·) separates adjacent labels; original spaces, punctuation and line breaks remain.</p>'+
   (task.criterion.kind==='exact-prefix'?'<div data-run-prefix>'+prefixAlignment(task,result,first.id)+'</div>':'')+
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
   const prefix=panel.querySelector('[data-run-prefix]');if(prefix)prefix.innerHTML=prefixAlignment(snapshot.task,snapshot.result,pageId,mode);
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
   (task.criterion.kind==='exact-prefix'?prefixChart(task,result):'<figure class="local-run-chart"><figcaption>Repeated neighbouring runes</figcaption><div role="img" aria-label="'+esc(data.comparison.map(r=>r.label+': '+r.value+' of '+r.total+' pairs').join('. '))+'">'+
   data.comparison.map((row,i)=>'<div class="run-bar-row"><span>'+esc(row.label)+'</span><div class="run-bar-track"><span class="run-bar run-bar-'+i+'" style="width:'+(row.value/max*100).toFixed(4)+'%"></span></div><strong>'+row.value+'</strong></div>').join('')+
   '</div><p class="run-chart-note">Counts follow the rune sequence on each page, ignoring spaces and punctuation.</p></figure>')+
   '<p class="run-limit">'+esc(data.limit)+'</p><dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'</section>';
 }
 const api={render,bind,pageLabel};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
