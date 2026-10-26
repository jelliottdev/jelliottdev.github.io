/* Small illustrative calculations; no manuscript evaluation or execution state. */
(function(root){
 'use strict';
 const P=typeof module==='object'&&module.exports?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function validAlphabet(alphabet){
  return Array.isArray(alphabet)&&alphabet.length===29&&Array.from(alphabet).every(item=>item&&typeof item==='object'&&typeof item.rune==='string'&&/^[\u16a0-\u16ff]$/u.test(item.rune)&&Number.isSafeInteger(item.prime)&&item.prime>1&&item.prime<=Number.MAX_SAFE_INTEGER/3)&&new Set(alphabet.map(item=>item.rune)).size===29&&new Set(alphabet.map(item=>item.prime)).size===29;
 }
 function affine(criterion,alphabet){
  const {a,b,lag}=criterion,later=(a+b)%29,earlierRune=esc(alphabet[1].rune),laterRune=esc(alphabet[later].rune),gap=lag-1;
  if(a===1&&b===0)return '<div class="protocol-example-pair"><span><span class="protocol-example-runes">'+earlierRune+'</span><small>Earlier</small></span><span class="protocol-example-distance">'+(gap?gap+' intervening rune'+(gap===1?'':'s'):'Adjacent runes')+'</span><span><span class="protocol-example-runes">'+earlierRune+'</span><small>Later</small></span></div>'+
   '<p>If the same rune appears '+lag+' position'+(lag===1?'':'s')+' ahead inside the same word, count one match.</p>';
  return '<div class="protocol-example-pair"><span><span class="protocol-example-runes">'+earlierRune+'</span><small>index 1</small></span><span class="protocol-example-distance">'+(gap?gap+' intervening rune'+(gap===1?'':'s'):'Adjacent runes')+'</span><span><span class="protocol-example-runes">'+laterRune+'</span><small>index '+later+'</small></span><span class="protocol-example-equation">('+a+' × 1 + '+b+') mod 29 = '+later+'</span></div>'+
   '<p>If the rune '+lag+' position'+(lag===1?'':'s')+' ahead in the same word has index '+later+', count one match. “mod 29” keeps the remainder after dividing by 29.</p>';
 }
 function sums(criterion,alphabet){
  const values=alphabet.slice(0,3).map((item,index)=>({rune:esc(item.rune),prime:alphabet[criterion.table==='reversed'?28-index:index].prime}));
  return '<div class="protocol-example-assignments">'+values.map(item=>'<span><span class="protocol-example-runes">'+item.rune+'</span> = '+item.prime+'</span>').join('<span aria-hidden="true"> · </span>')+'<span class="protocol-example-equation">'+values.map(item=>item.prime).join(' + ')+' = '+values.reduce((total,item)=>total+item.prime,0)+'</span></div>'+
   '<p>These first three alphabet runes form an example word.'+(criterion.table==='reversed'?' Prime assignments reverse across all 29 alphabet runes; rune order stays the same.':' Use each rune’s usual prime value.')+'</p>';
 }
 function keyedExample(plan){
  try{
   if(!validAlphabet(plan?.alphabet)||!Array.isArray(plan.steps)||plan.steps.length!==1)return null;
   const step=plan.steps[0];
   if(!step||Object.keys(step).length!==5||!['op','mode','key','direction','reset'].every(k=>Object.hasOwn(step,k))||step.op!=='keyed-shift'||!['repeat','plaintext-autokey','ciphertext-autokey'].includes(step.mode)||!['add','subtract'].includes(step.direction)||!['page','line','word'].includes(step.reset)||!Array.isArray(step.key)||!step.key.length||step.key.length>256||Array.from(step.key).some(v=>!Number.isInteger(v)||v<0||v>28))return null;
   const wrap=v=>((v%29)+29)%29,apply=(input,key)=>wrap(input+(step.direction==='add'?key:-key)),input=5,key=step.key[0],output=apply(input,key),nextInput=(5+step.key.length)%29,nextKey=step.mode==='repeat'?key:step.mode==='plaintext-autokey'?output:input;
   return {mode:step.mode,direction:step.direction,reset:step.reset,length:step.key.length,first:{position:1,input,key,output},next:{position:step.key.length+1,input:nextInput,key:nextKey,output:apply(nextInput,nextKey)}};
  }catch{return null;}
 }
 function foldedExample(plan,reference){
  try{
   if(!keyedExample(plan)||plan.steps[0].mode!=='repeat')return null;
   const banks=typeof module==='object'&&module.exports?require('./repeating-key-banks.js'):root.RepeatingKeyBanks;if(!banks)return null;
   const keys=banks.resolve(reference),bank=banks.list().find(item=>item.id===reference.bankId&&item.sha256===reference.bankSha256),mode=({'fold-repeat-endpoints-v1':'repeat','fold-skip-endpoints-v1':'skip'})[bank?.rule];
   if(!mode||!keys.some(key=>key.length===plan.steps[0].key.length&&key.every((value,index)=>value===plan.steps[0].key[index])))return null;
   return {mode};
  }catch{return null;}
 }
 function renderFolded(example){
  const chips=value=>'<span class="protocol-fold-cycle">'+Array.from(value,letter=>'<span'+(letter!=='B'?' class="protocol-fold-end"':'')+'>'+letter+'</span>').join('')+'</span>',row=(mode,label,cycle)=>'<div class="protocol-fold-row"><p>'+label+(example.mode===mode?' <strong>Used here</strong>':'')+'</p><div class="protocol-fold-cycles" role="img" aria-label="'+label+': '+cycle+', then '+cycle+'.">'+chips(cycle)+chips(cycle)+'</div></div>';
  return '<figure class="protocol-example protocol-fold-example"><figcaption>How the key repeats</figcaption><p class="protocol-example-label">Illustration only. A, B and C mark three key positions.</p><div class="protocol-fold-start"><span>Starting key</span>'+chips('ABC')+'</div>'+row('repeat','Repeat the ends','ABCCBA')+row('skip','Skip repeated ends','ABCB')+'<p class="protocol-fold-note">Outlined A and C mark the ends. Starting elsewhere shifts the same cycle.</p></figure>';
 }
 function renderKeyed(plan,{compact=false,settingCount,bankReference}={}){
  const example=keyedExample(plan);if(!example)return '';
  const folded=bankReference&&foldedExample(plan,bankReference);if(folded)return renderFolded(folded);
  const {first,next,mode,direction,reset,length}=example,cell=value=>'<td><span class="protocol-example-runes">'+esc(plan.alphabet[value].rune)+'</span><small>'+value+'</small></td>',raw=first.input+(direction==='add'?first.key:-first.key),source=mode==='repeat'?'return to the first key rune.':mode==='plaintext-autokey'?'take the next key rune from the first output above.':'take the next key rune from the first input above.';
  if(compact){const count=Number.isSafeInteger(settingCount)&&settingCount>1?'One of '+settingCount.toLocaleString('en-US')+' settings':'One example setting';return '<section class="protocol-example protocol-keyed-example" aria-label="Example rune change"><table><caption>'+count+' · invented input · rune numbers 0–28</caption><thead><tr><th scope="col">Rune in</th><th scope="col">Number used</th><th scope="col">Rune out</th></tr></thead><tbody><tr>'+cell(first.input)+'<td>'+first.key+'</td>'+cell(first.output)+'</tr></tbody></table><p class="protocol-example-equation">'+first.input+(direction==='add'?' + ':' − ')+first.key+(raw===first.output?' = '+first.output:': wrap around 29 to '+first.output)+'.</p><p>At each new '+reset+', start again with <strong>'+first.key+'</strong>.</p></section>';}
  return '<section class="protocol-example protocol-keyed-example" aria-label="Illustrative key calculation"><p class="protocol-example-label">Illustrative example · not manuscript evidence</p><table><caption>First rune · alphabet positions 0–28</caption><thead><tr><th scope="col">Input</th><th scope="col">Key</th><th scope="col">Output</th></tr></thead><tbody><tr>'+cell(first.input)+cell(first.key)+cell(first.output)+'</tr></tbody></table><p class="protocol-example-equation">'+first.input+(direction==='add'?' + ':' − ')+first.key+' = '+raw+(raw===first.output?'.':'; wrap to '+first.output+'.')+'</p><p>In a '+reset+' longer than '+length+' rune'+(length===1?'':'s')+', at rune '+next.position+' '+source+'</p></section>';
 }
 function render(input){
  try{
   const {criterion,alphabet}=input||{};
   if(!P?.identify(criterion)||!validAlphabet(alphabet))return '';
   return '<section class="protocol-example" aria-label="Illustrative worked example"><p class="protocol-example-label">Illustrative example · not manuscript evidence</p>'+(criterion.kind==='word-affine-count'?affine(criterion,alphabet):sums(criterion,alphabet))+'</section>';
  }catch{return '';}
 }
 const api={render,keyedExample,renderKeyed,foldedExample};if(typeof module==='object'&&module.exports)module.exports=api;else root.ProtocolExampleView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
