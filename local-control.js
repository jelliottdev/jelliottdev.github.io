/* Success properties for replayed synthetic controls, never target verdicts. */
(function(root){
 'use strict';
 function passed(task,result){
  if(task?.criterion?.kind==='exact-prefix')return Array.isArray(result?.matches)&&result.matches.length>0&&result.matches.every(v=>v.matched===true);
  if(task?.criterion?.kind==='word-affine-count'){
   const p=result?.wordPairs,e=p?.expected;
   if(!Number.isSafeInteger(p?.opportunities)||p.opportunities<=0||p.matches!==p.opportunities||typeof e?.numerator!=='string'||typeof e?.denominator!=='string'||!/^\d+$/.test(e.numerator)||!/^[1-9]\d*$/.test(e.denominator))return false;
   return BigInt(e.numerator)<BigInt(p.opportunities)*BigInt(e.denominator);
  }
  return false;
 }
 const api={passed};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalControl=api;
})(typeof globalThis!=='undefined'?globalThis:this);
