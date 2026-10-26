/* Plain-language descriptions of maintained parameter choices. No calculations or I/O. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,V=node?require('./task-parameter-variants.js'):root.TaskParameterVariants;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const where={page:'each page',line:'each line',word:'each word'};
 function reading(criterion){
  if(criterion.kind==='exact-prefix')return 'If the opening matches, inspect the full output; a match is not a decryption. If it does not match, this version did not recover the supplied opening on these pages. Other text is still possible.';
  if(criterion.kind==='exact-prefix-set')return 'If an opening matches, inspect the full output; a match is not a decryption. If none match, this version did not recover the supplied openings on these pages. Other text is still possible.';
  if(criterion.kind==='language-score')return 'Compare each language score with its rearranged-text baseline, then inspect the output. Similarity does not identify the language or establish a decryption.';
  if(criterion.kind==='measurement')return 'Inspect the output and counts. These measurements are not a decryption verdict.';
  if(criterion.kind==='word-affine-count')return 'The count measures how often the chosen rune relation occurs. It does not identify the encryption rule.';
  if(criterion.kind==='word-prime-sums')return 'The totals measure words using the chosen number table. They do not establish a decryption.';
  return null;
 }
 function describe(parent,item){
  try{
   const task=J.capture(parent,{maxBytes:2000000,maxDepth:24,maxNodes:250000}),value=J.capture(item,{maxBytes:2048,maxDepth:4,maxNodes:32});
   if(!exact(value,['selection','from',...(Object.hasOwn(value||{},'label')?['label']:[])])||Object.hasOwn(value,'label')&&(typeof value.label!=='string'||value.label.length>300))return null;
   const chosen=V.list(task).find(candidate=>E.stable(candidate.selection)===E.stable(value.selection)&&candidate.from===value.from);if(!chosen)return null;
   const s=chosen.selection,step=task.steps[s.step],interpretation=reading(task.criterion);if(!interpretation)return null;let question,reason;
   if(s.parameter==='direction'){
    question='What if we '+(s.value==='add'?'add':'subtract')+' the key values?';
    if(step.op==='finite-shift')reason=(s.value==='add'?'Add the same number sequence to':'Subtract the same number sequence from')+' rune positions, without repeating it within a segment.';
    else if(step.op==='interrupted-keyed-shift')reason='The same repeating numbers shift the runes; selected runes are still copied without advancing the key.';
    else if(step.mode==='plaintext-autokey')reason='After the starting numbers, runes already produced supply more key numbers to shift the runes.';
    else if(step.mode==='ciphertext-autokey')reason='After the starting numbers, runes already read supply more key numbers to shift the runes.';
    else reason='The key’s numbers shift rune positions along the alphabet, repeating in the same order.';
   }else if(step.op==='cumulative-difference'){
    question='What if the running total starts over at '+where[s.value]+'?';
    reason='Subtract the total of earlier output values; starting over clears that total and leaves the next rune unchanged.';
   }else{
    const finite=step.op==='finite-shift';
    question='What if the '+(finite?'number sequence':'key')+' starts over at '+where[s.value]+'?';
    if(step.op==='interrupted-keyed-shift')reason='Start the repeating key again; selected runes are still copied without advancing the key.';
    else if(finite)reason='Use the number sequence once within each '+s.value+', starting from its beginning for the next '+s.value+'.';
    else if(step.mode==='plaintext-autokey')reason='Reuse the starting key numbers and stop using runes produced before the boundary as later key numbers.';
    else if(step.mode==='ciphertext-autokey')reason='Reuse the starting key numbers and stop using runes read before the boundary as later key numbers.';
    else reason=s.value==='word'?'Spaces, punctuation and other non-rune characters restart the same repeating key.':s.value==='line'?'Each line break restarts the same repeating key.':'Each page starts the same repeating key again.';
   }
   return Object.freeze({question,reason,reading:interpretation});
  }catch{return null;}
 }
 const api={describe};if(node)module.exports=api;else root.ParameterVariationQuestion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
