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
 function describe(parent,item){return describeMany(parent,[item])[0]||null;}
 function describeMany(parent,items){
  try{
   const task=J.capture(parent,{maxBytes:2000000,maxDepth:24,maxNodes:250000}),values=J.capture(items,{maxBytes:2000000,maxDepth:8,maxNodes:100000});
   if(!Array.isArray(values)||values.length>4096)return [];
   const choices=new Map(V.list(task).map(item=>[E.stable(item.selection)+'|'+E.stable(item.from),item]));return values.map(value=>describeCaptured(task,value,choices));
  }catch{return Array.isArray(items)?items.map(()=>null):[];}
 }
 function describeCaptured(task,input,choices){
  try{
   const value=J.capture(input,{maxBytes:2048,maxDepth:4,maxNodes:32});
   if(!exact(value,['selection','from',...(Object.hasOwn(value||{},'label')?['label']:[])])||Object.hasOwn(value,'label')&&(typeof value.label!=='string'||value.label.length>300))return null;
   const chosen=choices.get(E.stable(value.selection)+'|'+E.stable(value.from));if(!chosen)return null;
   const s=chosen.selection,step=task.steps[s.step],interpretation=reading(task.criterion);if(!interpretation)return null;let question,reason;
   if(s.parameter==='phase'){
    question='What if we start the repeating key '+s.value+' '+(s.value===1?'rune':'runes')+' later?';
    reason='Start at key position '+(s.value+1)+' instead of position 1. Continue through the same cyclic values, wrapping to the beginning after the last value. Use this starting place again at each '+step.reset+'. The addition or subtraction stays unchanged.'+(task.steps.length>1?' All other steps stay unchanged.':'');
   }else if(s.parameter==='a'||s.parameter==='b'){
    question=s.parameter==='a'?'What if we multiply rune values by '+s.value+'?':'What if we add '+s.value+' after multiplying?';
    reason='Give each rune its alphabet number from 0 to 28. Multiply by '+(s.parameter==='a'?s.value:step.a)+', add '+(s.parameter==='b'?s.value:step.b)+', then take the remainder after dividing by 29. '+(s.parameter==='a'?'The added number stays '+step.b+'.':'The multiplier stays '+step.a+'.')+' Spaces and punctuation stay in place.'+((s.parameter==='a'?s.value:step.a)===0?' Multiplying by zero removes the differences between rune values at this step.':'')+(task.steps.length>1?' All other steps stay unchanged.':'');
   }else if(s.parameter==='unit'){
    question='What if we reverse the runes within '+where[s.value]+'?';
    reason=s.value==='word'?'Reverse each uninterrupted group of runes separately. Spaces, punctuation and line breaks stay in place.':s.value==='line'?'Reverse the rune order across each line, including across word gaps. Spaces, punctuation and line breaks stay in place.':'Reverse the rune order across the whole page, including across lines and word gaps. Spaces, punctuation and line breaks stay in place.';
   }else if(s.parameter==='mode'){
    question=s.value==='repeat'?'What if we keep repeating the starting key?':s.value==='plaintext-autokey'?'What if decoded runes supply the later key numbers?':'What if original runes supply the later key numbers?';
    reason=s.value==='repeat'?'After the supplied key ends, use its starting numbers again in the same order.':s.value==='plaintext-autokey'?'After the supplied key ends, continue with the numbers of runes this step has already decoded, in order. Decoded here means calculated output, not confirmed readable text.':'After the supplied key ends, continue with the numbers of runes this step has already read, in order. Original here means this step’s input, after any earlier steps.';
   }else if(s.parameter==='direction'){
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
 const api={describe,describeMany};if(node)module.exports=api;else root.ParameterVariationQuestion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
