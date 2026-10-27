/* Typed fixed-program descriptions only; no execution, inference or record prose. */
(function(root){
 'use strict';
 function step(step){
 const reset='Start the sequence again on each '+step.reset+'.',key=step.key,preview=key?' Key begins: '+key.slice(0,6).join(', ')+(key.length>6?' (first 6 of '+key.length+')':' ('+key.length+' values)')+'.':'';
 const action=step.direction==='subtract'?'Subtract successive key values from the rune values.':'Add successive key values to the rune values.';
 if(step.op==='keyed-shift')return action+' '+(step.mode==='repeat'?'Repeat the key when it ends.':step.mode==='plaintext-autokey'?'When the starting key ends, continue it with the rune values already decoded.':'When the starting key ends, continue it with the original input rune values.')+' '+reset+preview;
 if(step.op==='finite-shift')return action+' Use each key value once, in sequence. '+reset+preview;
 if(step.op==='interrupted-keyed-shift')return action+' Repeat the key when it ends. Leave rune indices '+step.interrupts.join(', ')+' unchanged and pause the key at those runes. '+reset+preview;
 if(step.op==='reverse')return 'Read the runes in each '+step.unit+' in reverse order.';
 if(step.op==='affine')return 'Multiply each rune value by '+step.a+', add '+step.b+', then take the remainder after dividing by 29.';
 if(step.op==='cumulative-difference')return 'Subtract the total of all rune values already decoded in the sequence. '+reset;
 throw Error('A published operation has no maintained discovery description');
}
 const api={step};if(typeof module==='object'&&module.exports)module.exports=api;else root.PublishedProgramDescription=api;
})(typeof globalThis!=='undefined'?globalThis:this);
