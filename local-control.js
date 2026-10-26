/* Success properties for replayed synthetic controls, never target verdicts. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment,Evaluators=typeof module==='object'&&module.exports?require('./output-evaluators.js'):root.OutputEvaluators;
 // Compare validated programs; callers verify complete task identities separately.
 function compatible(control,target){
  if(!Array.isArray(control?.alphabet)||!Array.isArray(target?.alphabet)||!Array.isArray(control?.steps)||!Array.isArray(target?.steps)||E.stable(control.alphabet)!==E.stable(target.alphabet)||E.stable(control.steps)!==E.stable(target.steps))return false;
  const c=control.criterion,t=target.criterion;
  const runes=new Set(control.alphabet.map(v=>v.rune)),count=Array.isArray(control.pages)?control.pages.reduce((n,page)=>n+Array.from(page.text||'').filter(ch=>runes.has(ch)).length,0):0;
  if(t?.kind==='exact-prefix-set'){try{E.validateTask(target);}catch{return false;}}
  if(t?.kind==='measurement'||t?.kind==='exact-prefix-set'||Evaluators?.identify(t))return (t?.kind==='exact-prefix-set'||Evaluators?.identify(t)||Object.keys(t).length===1)&&c?.kind==='exact-prefix'&&Object.keys(c).length===2&&Array.isArray(c.values)&&c.values.length>0&&c.values.length<=256&&c.values.length===count&&c.values.every(v=>Number.isInteger(v)&&v>=0&&v<=28);
  return ['exact-prefix','word-affine-count','word-prime-sums'].includes(t?.kind)&&E.stable(c)===E.stable(t);
 }
 function passed(task,result){
  if(task?.criterion?.kind==='word-prime-sums')return Number.isSafeInteger(result?.wordSums?.words)&&result.wordSums.words>0&&Number.isSafeInteger(result.wordSums.total)&&result.wordSums.total>0;
  if(task?.criterion?.kind==='exact-prefix')return Array.isArray(result?.matches)&&result.matches.length>0&&result.matches.every(v=>v.matched===true);
  if(task?.criterion?.kind==='word-affine-count'){
   const p=result?.wordPairs,e=p?.expected;
   if(!Number.isSafeInteger(p?.opportunities)||p.opportunities<=0||p.matches!==p.opportunities||typeof e?.numerator!=='string'||typeof e?.denominator!=='string'||!/^\d+$/.test(e.numerator)||!/^[1-9]\d*$/.test(e.denominator))return false;
   return BigInt(e.numerator)<BigInt(p.opportunities)*BigInt(e.denominator);
  }
  return false;
 }
 const api={passed,compatible};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalControl=api;
})(typeof globalThis!=='undefined'?globalThis:this);
