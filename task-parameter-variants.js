/* Closed parameter deltas over exact saved tasks. No target execution or I/O. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON;
 const keyed=new Set(['keyed-shift','interrupted-keyed-shift','finite-shift']),resets=['page','line','word'],directions=['subtract','add'];
 const own=(value,key)=>Object.prototype.hasOwnProperty.call(value,key),stable=value=>E.stable(value);
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 function captureTask(value){
  const task=J.capture(value,{maxBytes:2000000,maxDepth:24,maxNodes:250000});
  E.validateTask(task);return task;
 }
 function captureSelection(value){
  const selection=J.capture(value,{maxBytes:512,maxDepth:3,maxNodes:16}),keys=['version','step','parameter','value'];
  if(!selection||typeof selection!=='object'||Array.isArray(selection)||Object.keys(selection).length!==keys.length||!keys.every(key=>own(selection,key))||selection.version!==1||!Number.isInteger(selection.step)||selection.step<0||!['direction','reset'].includes(selection.parameter)||!(selection.parameter==='direction'?directions:resets).includes(selection.value))throw Error('Choose one exact supported step parameter and destination.');
  return selection;
 }
 function unchanged(value,snapshot,capture){if(stable(capture(value))!==stable(snapshot))throw Error('The task or selected variation changed during preparation.');}
 function derive(parent,selection){
  const step=parent.steps[selection.step],parameter=selection.parameter;
  if(!step||!(parameter==='direction'?keyed.has(step.op):keyed.has(step.op)||step.op==='cumulative-difference'))throw Error('The selected step does not support this parameter variation.');
  if(step[parameter]===selection.value)throw Error('Choose a value different from the saved task.');
  const steps=JSON.parse(stable(parent.steps));steps[selection.step][parameter]=selection.value;
  const action=parameter==='direction'?(selection.value==='add'?'add key indices':'subtract key indices'):'restart at each '+selection.value;
  const body={title:'Step '+(selection.step+1)+': '+action,pages:JSON.parse(stable(parent.pages)),alphabet:JSON.parse(stable(parent.alphabet)),steps,criterion:JSON.parse(stable(parent.criterion))};
  // The normal runner checks the entire resulting geometry, including all
  // finite-key segments. An unavailable restart is rejected, never shortened.
  E.validateTask({...body,schema:E.TASK,engine:E.ENGINE,taskId:'0'.repeat(64)});
  return body;
 }
 // Listing proves structural eligibility only. Async preparation additionally
 // verifies the immutable parent identity and rejects concurrent mutations.
 function list(parent){
  const task=captureTask(parent),items=[];
  for(let step=0;step<task.steps.length;step++){
   const operation=task.steps[step],parameters=keyed.has(operation.op)?['direction','reset']:operation.op==='cumulative-difference'?['reset']:[];
   for(const parameter of parameters)for(const value of parameter==='direction'?directions:resets){
    if(operation[parameter]===value)continue;
    const selection={version:1,step,parameter,value};
    try{derive(task,selection);}catch{continue;}
    items.push({selection,from:operation[parameter],label:parameter==='direction'?(value==='add'?'Add the key values':'Subtract the key values'):'Restart at each '+value});
   }
  }
  return freeze(items);
 }
 // Suggestions omit only choices whose outputs are provably unchanged on this
 // scope. Every operation preserves rune positions and separators, so these
 // clocks remain valid after arbitrary earlier operations. They contain no
 // transformed rune values and do not run or admit a calculation.
 function suggestions(parent){
  const task=captureTask(parent),items=list(task),runes=new Set(task.alphabet.map(entry=>entry.rune)),positions={page:[],line:[],word:[]};
  for(const page of task.pages){let p=0,l=0,w=0;for(const ch of page.text){
   if(runes.has(ch)){positions.page.push(p++);positions.line.push(l++);positions.word.push(w++);}
   else{w=0;if(/[\r\n]/.test(ch))l=0;}
  }}
  const equal=(a,b)=>a.every((value,index)=>value===b[index]),maximum=a=>a.reduce((max,value)=>Math.max(max,value),-1)+1;
  const sameOutputs=item=>{
   if(!positions.page.length)return true;
   const {step:index,parameter,value}=item.selection,step=task.steps[index],before=positions[step.reset];
   // A later constant affine substitution discards every earlier rune value.
   if(task.steps.slice(index+1).some(later=>later.op==='affine'&&later.a===0))return true;
   if(step.op==='interrupted-keyed-shift'&&step.interrupts.length===29)return true;
   if(parameter==='direction'){
    if(step.op==='interrupted-keyed-shift')return step.key.slice(0,Math.min(step.key.length,maximum(before))).every(k=>k===0);
    if(step.op==='keyed-shift'&&step.mode!=='repeat'&&maximum(before)>step.key.length)return false;
    return before.every(position=>step.key[step.op==='finite-shift'?position:position%step.key.length]===0);
   }
   const after=positions[value];if(equal(before,after))return true;
   if(step.op==='cumulative-difference')return false;
   if(step.op==='interrupted-keyed-shift'){
    // Interrupts depend on this step's input, which preceding operations can
    // change. A nonconstant key must not use the ordinary rune clock here.
    const reachable=step.key.slice(0,Math.min(step.key.length,Math.max(maximum(before),maximum(after))));
    return reachable.every(k=>k===reachable[0]);
   }
   if(step.op==='keyed-shift'&&step.mode!=='repeat'){
    // Zero or periodic seeds alone prove nothing once feedback is in use.
    if(Math.max(maximum(before),maximum(after))>step.key.length)return false;
    return before.every((position,i)=>step.key[position]===step.key[after[i]]);
   }
   return before.every((position,i)=>step.key[step.op==='finite-shift'?position:position%step.key.length]===step.key[step.op==='finite-shift'?after[i]:after[i]%step.key.length]);
  };
  return freeze(items.filter(item=>!sameOutputs(item)));
 }
 async function prepare(parent,selection,cryptoAPI=root.crypto){
  const original=captureTask(parent),chosen=captureSelection(selection),body=derive(original,chosen);
  await E.checkIdentity(original,cryptoAPI);
  unchanged(parent,original,captureTask);unchanged(selection,chosen,captureSelection);
  const child=await E.prepare(body,cryptoAPI);
  unchanged(parent,original,captureTask);unchanged(selection,chosen,captureSelection);
  return freeze(child);
 }
 async function validate(parent,child,selection,cryptoAPI=root.crypto){
  const original=captureTask(parent),candidate=captureTask(child),chosen=captureSelection(selection),body=derive(original,chosen);
  const assertUnchanged=()=>{unchanged(parent,original,captureTask);unchanged(child,candidate,captureTask);unchanged(selection,chosen,captureSelection);};
  await E.checkIdentity(original,cryptoAPI);assertUnchanged();
  await E.checkIdentity(candidate,cryptoAPI);assertUnchanged();
  const expected=await E.prepare(body,cryptoAPI);assertUnchanged();
  if(stable(expected)!==stable(candidate))throw Error('The child changed more than the selected step parameter.');
  return freeze(candidate);
 }
 const api={list,suggestions,prepare,validate};if(node)module.exports=api;else root.TaskParameterVariants=api;
})(typeof globalThis!=='undefined'?globalThis:this);
