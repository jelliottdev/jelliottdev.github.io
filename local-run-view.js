/* Shared result view. All conclusions and chart values come from replayed data. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function render(task,result){
  const data=E.summary(task,result),max=Math.max(1,...data.comparison.map(r=>r.value));
  return '<section class="local-run-result" aria-labelledby="local-run-finding"><p class="run-state">Computation verified</p><h2 id="local-run-finding">What this run found</h2><p>'+esc(data.finding)+'</p>'+
   '<figure class="local-run-chart"><figcaption>Repeated neighbouring runes</figcaption><div role="img" aria-label="'+esc(data.comparison.map(r=>r.label+': '+r.value+' of '+r.total+' pairs').join('. '))+'">'+
   data.comparison.map((row,i)=>'<div class="run-bar-row"><span>'+esc(row.label)+'</span><div class="run-bar-track"><span class="run-bar run-bar-'+i+'" style="width:'+(row.value/max*100).toFixed(4)+'%"></span></div><strong>'+row.value+'</strong></div>').join('')+
   '</div><p class="run-chart-note">Counts follow the rune sequence on each page, ignoring spaces and punctuation.</p></figure>'+
   '<p class="run-limit">'+esc(data.limit)+'</p><dl class="run-scope"><div><dt>Pages</dt><dd>'+task.pages.map(p=>esc(p.id.toUpperCase())).join(', ')+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl></section>';
 }
 const api={render};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
