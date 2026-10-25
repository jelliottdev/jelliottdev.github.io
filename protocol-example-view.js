/* Small illustrative calculations; no manuscript evaluation or execution state. */
(function(root){
 'use strict';
 const P=typeof module==='object'&&module.exports?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function validAlphabet(alphabet){
  return Array.isArray(alphabet)&&alphabet.length===29&&alphabet.every(item=>item&&typeof item==='object'&&typeof item.rune==='string'&&/^[\u16a0-\u16ff]$/u.test(item.rune)&&Number.isSafeInteger(item.prime)&&item.prime>1&&item.prime<=Number.MAX_SAFE_INTEGER/3)&&new Set(alphabet.map(item=>item.rune)).size===29&&new Set(alphabet.map(item=>item.prime)).size===29;
 }
 function affine(criterion,alphabet){
  const {a,b,lag}=criterion,later=(a+b)%29,earlierRune=esc(alphabet[1].rune),laterRune=esc(alphabet[later].rune),gap=lag-1;
  return '<div class="protocol-example-pair"><span><span class="protocol-example-runes">'+earlierRune+'</span><small>index 1</small></span><span class="protocol-example-distance">'+(gap?gap+' intervening rune'+(gap===1?'':'s'):'Adjacent runes')+'</span><span><span class="protocol-example-runes">'+laterRune+'</span><small>index '+later+'</small></span><span class="protocol-example-equation">('+a+' × 1 + '+b+') mod 29 = '+later+'</span></div>'+
   '<p>If the rune '+lag+' position'+(lag===1?'':'s')+' ahead in the same word has index '+later+', count one match. “mod 29” keeps the remainder after dividing by 29.</p>';
 }
 function sums(criterion,alphabet){
  const values=alphabet.slice(0,3).map((item,index)=>({rune:esc(item.rune),prime:alphabet[criterion.table==='reversed'?28-index:index].prime}));
  return '<div class="protocol-example-assignments">'+values.map(item=>'<span><span class="protocol-example-runes">'+item.rune+'</span> = '+item.prime+'</span>').join('<span aria-hidden="true"> · </span>')+'<span class="protocol-example-equation">'+values.map(item=>item.prime).join(' + ')+' = '+values.reduce((total,item)=>total+item.prime,0)+'</span></div>'+
   '<p>These first three alphabet runes form an example word.'+(criterion.table==='reversed'?' Prime assignments reverse across all 29 alphabet runes; rune order stays the same.':' Use each rune’s usual prime value.')+'</p>';
 }
 function render(input){
  try{
   const {criterion,alphabet}=input||{};
   if(!P?.identify(criterion)||!validAlphabet(alphabet))return '';
   return '<section class="protocol-example" aria-label="Illustrative worked example"><p class="protocol-example-label">Illustrative example · not manuscript evidence</p>'+(criterion.kind==='word-affine-count'?affine(criterion,alphabet):sums(criterion,alphabet))+'</section>';
  }catch{return '';}
 }
 const api={render};if(typeof module==='object'&&module.exports)module.exports=api;else root.ProtocolExampleView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
