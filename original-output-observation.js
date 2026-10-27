/* Descriptive observations of exact verified input/output. No execution or baseline receipt. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const Dispatch=node?require('./local-experiment-dispatch.js'):root.LocalExperimentDispatch;
 const TASK='liberpedia-declarative-rune-task-v2',ENGINE='rune-program-v2',SCHEMA='liberpedia-original-output-observation-v1',observations=new WeakMap();
 const LIMIT='These observations describe this verified computation on these pages only. Removing repeats changes their counts by construction. They do not identify filler, measure statistical significance, establish readability or test a scientific null. Combined index of coincidence pools rune frequencies across pages; it is not a mean of page scores.';
 const need=(ok,message)=>{if(!ok)throw Error(message);};
 const freeze=value=>{if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
 function accumulator(){return {pages:0,runes:0,adjacentPairs:0,equalAdjacentPairs:0,histogram:new Uint32Array(29)};}
 function count(text,index){
  const value=accumulator();value.pages=1;let previous=-1;
  for(const ch of text){const rune=index.get(ch);if(rune===undefined)continue;value.runes++;value.histogram[rune]++;if(previous!==-1){value.adjacentPairs++;if(previous===rune)value.equalAdjacentPairs++;}previous=rune;}
  return value;
 }
 function add(total,page){for(const key of ['pages','runes','adjacentPairs','equalAdjacentPairs'])total[key]+=page[key];page.histogram.forEach((n,i)=>total.histogram[i]+=n);}
 function metrics(value){
  return freeze({pages:value.pages,runes:value.runes,adjacentPairs:value.adjacentPairs,equalAdjacentPairs:value.equalAdjacentPairs,equalPairRate:{numerator:value.equalAdjacentPairs,denominator:value.adjacentPairs,value:value.adjacentPairs?value.equalAdjacentPairs/value.adjacentPairs:null},ioc:value.runes>1?value.histogram.reduce((sum,n)=>sum+n*(n-1),0)/(value.runes*(value.runes-1)):0});
 }
 function derive(certificate){
  // inspect accepts only the exact result object returned by this dispatcher's
  // verifier. No caller-supplied task, plaintext, receipt flag or getter is read.
  const verified=Dispatch.inspect(certificate),{task,result}=verified;
  need(task.schema===TASK&&task.engine===ENGINE&&result===certificate&&result.taskId===task.taskId,'Use a genuine dispatcher-verified version-two result.');
  const index=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),originalTotal=accumulator(),outputTotal=accumulator(),pages=[];let removedRunes=0;
  for(let i=0;i<task.pages.length;i++){
   const input=task.pages[i],output=result.transformed[i],alignment=result.alignment.pages[i];
   need(output.page===input.id&&alignment.page===input.id,'The verified input/output page order changed.');
   const original=count(input.text,index),after=count(output.text,index),removed=alignment.removed.length;
   need(original.runes-after.runes===removed,'The verified removal count differs from its alignment.');
   add(originalTotal,original);add(outputTotal,after);removedRunes+=removed;
   pages.push({page:input.id,original:metrics(original),output:metrics(after),removedRunes:removed});
  }
  const original=metrics(originalTotal),output=metrics(outputTotal);
  for(const key of ['pages','runes','adjacentPairs','equalAdjacentPairs','ioc'])need(output[key]===result.metrics[key],'Observed output metrics differ from the verified result.');
  const model=freeze({schema:SCHEMA,taskId:task.taskId,certificate,pageIds:task.pages.map(page=>page.id),original,output,pages,removedRunes,limit:LIMIT}),token=Object.freeze({});
  observations.set(token,model);return token;
 }
 function inspect(token){const value=observations.get(token);need(value,'Use a private original/output observation token.');return value;}
 const api=Object.freeze({SCHEMA,LIMIT,derive,inspect});if(node)module.exports=api;else root.OriginalOutputObservation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
