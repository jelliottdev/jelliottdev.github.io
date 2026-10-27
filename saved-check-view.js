/* A preview of one verified saved computation, never coverage of a whole question. */
(function(root){
 'use strict';
 const HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/;
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function field(value,key){const d=value&&typeof value==='object'?Object.getOwnPropertyDescriptor(value,key):null;return d&&Object.hasOwn(d,'value')?d.value:undefined;}
 function summary(proof){try{const S=typeof module==='object'&&module.exports?require('./saved-check-summary.js'):root.SavedCheckSummary;return S.inspect(proof);}catch{return null;}}
 function pagesLabel(pages){
  const groups=[];
  for(let i=0;i<pages.length;i++){
   const start=pages[i];let end=start;
   while(i+1<pages.length&&/^lp[12]-\d{2}$/.test(start)&&pages[i+1].slice(0,4)===start.slice(0,4)&&Number(pages[i+1].slice(4))===Number(end.slice(4))+1)end=pages[++i];
   groups.push(start.toUpperCase()+(end===start?'':'–'+end.slice(4)));
  }
  return groups.join(', ');
 }
 function render(proof,context,options={}){
  const m=summary(proof),taskId=field(context,'taskId'),proposalId=field(context,'proposalId'),inputVersion=field(context,'inputVersion');
  // Association and edition are authenticated by the caller, not established by a summary.
  if(!m||typeof taskId!=='string'||!HEX.test(taskId)||m.taskId!==taskId||typeof proposalId!=='string'||!IDEA.test(proposalId)||!['raw','reviewed'].includes(inputVersion))return '';
  const level=Number.isInteger(options.headingLevel)&&options.headingLevel>=2&&options.headingLevel<=6?options.headingLevel:3;
  return '<section class="saved-check-preview" aria-label="Saved check"><p class="saved-check-criterion">'+esc(m.criterionLabel)+'</p><h'+level+'>'+esc(m.heading)+'</h'+level+'><p class="saved-check-finding">'+esc(m.finding)+'</p><p class="saved-check-scope">Pages checked: '+esc(pagesLabel(m.pageIds))+'. '+(inputVersion==='reviewed'?'Reviewed transcription.':'Raw transcription.')+'</p><p class="saved-check-limit">'+esc(m.limit)+'</p>'+(options.link===false?'':'<a class="saved-check-link" href="run.html#task='+taskId+'&amp;idea='+proposalId+'">View this saved check</a>')+'</section>';
 }
 function renderState(state){
  if(state==='loading')return '<p class="saved-check-state" role="status">Loading the saved check…</p>';
  if(state==='error')return '<p class="saved-check-state">The saved check could not be verified. The question is still available.</p>';
  if(state==='empty')return '<p class="saved-check-state">This computation has no saved result available.</p>';
  return '';
 }
 const api=Object.freeze({render,renderState});if(typeof module==='object'&&module.exports)module.exports=api;else root.SavedCheckView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
