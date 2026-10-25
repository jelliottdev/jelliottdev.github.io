/* Illustrative word grouping only. No calculations, evidence or execution state. */
(function(root){
 'use strict';
 const P=typeof module==='object'&&module.exports?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function valid(task){
  try{return task?.criterion?.kind==='word-affine-count'&&!!P?.identify(task.criterion)&&Array.isArray(task.alphabet)&&task.alphabet.length===29&&task.alphabet.every(item=>item&&typeof item.rune==='string'&&/^[\u16a0-\u16ff]$/u.test(item.rune))&&new Set(task.alphabet.map(item=>item.rune)).size===29;}catch{return false;}
 }
 function describe(task){
  try{
  if(!valid(task))return '';
  return task.criterion.boundaries==='hyphen-period'?{
   actionLabel:'Review with joined words',
   explanation:"Join groups across spaces, slashes and line breaks; only '-' and '.' end a group. The counting rule, rune order and pages stay the same."
  }:{
   actionLabel:'Review with separated words',
   explanation:'Keep each stretch of runes separate. Spaces, punctuation and line breaks end a group; the counting rule, rune order and pages stay the same.'
  };
  }catch{return '';}
 }
 function render(task){
  try{
  if(!valid(task))return '';
  const runes=task.alphabet.slice(0,4).map(item=>esc(item.rune)),left=runes.slice(0,2).join(''),right=runes.slice(2).join('');
  const word=text=>'<span class="boundary-comparison-word">'+text+'</span>',space='<span class="boundary-comparison-space" aria-label="synthetic space">space</span>';
  return '<figure class="boundary-comparison-example" data-boundary-mode="'+esc(task.criterion.boundaries)+'"><figcaption>Illustrative grouping · not manuscript evidence</figcaption>'+
   '<div class="boundary-comparison-row"><span class="boundary-comparison-label">Separated</span><span class="boundary-comparison-groups" role="group" aria-label="Two groups, separated at the synthetic space">'+word(left)+space+word(right)+'</span></div>'+
   '<div class="boundary-comparison-row"><span class="boundary-comparison-label">Joined</span><span class="boundary-comparison-groups" role="group" aria-label="One group, joined across the same synthetic space">'+word(left+space+right)+'</span></div>'+
   '<p>Joined groups stop only at the characters <code>-</code> and <code>.</code>. Pages remain separate.</p></figure>';
  }catch{return '';}
 }
 const api={describe,render};if(typeof module==='object'&&module.exports)module.exports=api;else root.BoundaryComparisonView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
