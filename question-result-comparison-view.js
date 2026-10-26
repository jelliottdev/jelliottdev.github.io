/* Saved outputs only. The verification module owns comparisons and source binding. */
(function(root){
 'use strict';
 const Comparison=typeof module==='object'&&module.exports?require('./question-result-comparison.js'):root.QuestionResultComparison,selections=new WeakMap();
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const pageLabel=id=>String(id).toUpperCase(),pagesLabel=ids=>ids.map(pageLabel).join(', ');
 function inspect(token){try{return Comparison.inspect(token);}catch{return null;}}
 function selected(token,m,options){const id=options.pageId||selections.get(token),page=m.pages.find(p=>p.id===id)||m.pages[0];if(page)selections.set(token,page.id);return page;}
 function excerpt(page,alphabet){
  const labels=new Map(alphabet.map(r=>[r.rune,r.latin])),changed=new Set(page.changes.map(c=>c.position)),first=page.changes[0]?.position||1,start=Math.max(1,first-8),end=Math.min(page.runeCount,start+31);
  function output(text){let ordinal=0,html='';for(const char of Array.from(text)){if(labels.has(char)){ordinal++;if(ordinal>=start&&ordinal<=end)html+='<span class="question-comparison-rune'+(changed.has(ordinal)?' is-changed':'')+'"'+(changed.has(ordinal)?' aria-label="'+esc(labels.get(char)+' — changed')+'"':'')+'>'+esc(labels.get(char))+'</span>';}else if(ordinal>=start&&ordinal<end)html+='<span class="question-comparison-separator">'+esc(char)+'</span>';}
   return (start>1?'<span aria-label="Earlier runes omitted">… </span>':'')+html+(end<page.runeCount?'<span aria-label="Later runes omitted"> …</span>':'');}
  return {start,end,before:output(page.parentText),after:output(page.childText)};
 }
 function render(token,options={}){
  const m=inspect(token);if(!m)return '';
  const page=selected(token,m,options),missing=m.childOnlyPages.length?'<p class="question-comparison-note">No original saved output for '+esc(pagesLabel(m.childOnlyPages))+'. Those pages are not compared.</p>':'',description=m.description?'<p class="question-comparison-change">'+esc(m.description)+'</p>':'';
  if(!page)return '<section class="question-result-comparison" aria-label="Saved output comparison"><h2>What changed?</h2><p>These saved outputs have no pages in common.</p>'+missing+'</section>';
  const snippet=excerpt(page,m.alphabet),picker=m.pages.length>1?'<label class="question-comparison-picker">Compare page <select data-comparison-page aria-label="Compare saved outputs on page">'+m.pages.map(p=>'<option value="'+esc(p.id)+'"'+(p.id===page.id?' selected':'')+'>'+esc(pageLabel(p.id))+'</option>').join('')+'</select></label>':'<p class="question-comparison-page">'+esc(pageLabel(page.id))+'</p>',count=page.changedRunes===0?'No runes changed':page.changedRunes+' of '+page.runeCount+' runes changed',range=snippet.end>=snippet.start?'Runes '+snippet.start+'–'+snippet.end+(page.changedRunes?' · around the first change':''):'';
  return '<section class="question-result-comparison" aria-label="Saved output comparison"><h2>What changed?</h2>'+description+picker+'<p class="question-comparison-count" aria-live="polite">'+esc(count)+'.</p><p class="question-comparison-caption">Latin rune labels, not a translation. Outlined labels differ. '+esc(range)+'.</p><div class="question-comparison-pair"><div><h3>Original question</h3><p class="question-comparison-output" aria-label="Original saved output excerpt">'+snippet.before+'</p></div><div><h3>This variation</h3><p class="question-comparison-output" aria-label="Variation saved output excerpt">'+snippet.after+'</p></div></div>'+missing+'<p class="question-comparison-note">A change in output does not establish readable text.</p></section>';
 }
 function bind(host,token,options={}){
  if(!inspect(token))return ()=>{};let clean=()=>{},dead=false;
  function connect(){const select=host.querySelector?.('[data-comparison-page]');if(!select)return;const change=()=>{const m=inspect(token);if(dead||!m.pages.some(p=>p.id===select.value))return;selections.set(token,select.value);clean();host.innerHTML=render(token,{pageId:select.value});connect();host.querySelector?.('[data-comparison-page]')?.focus?.();options.onPageChange?.(select.value);};select.addEventListener('change',change);clean=()=>select.removeEventListener('change',change);}
  connect();return ()=>{dead=true;clean();};
 }
 const api={render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.QuestionResultComparisonView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
