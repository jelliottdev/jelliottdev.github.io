/* Closed parameter deltas over exact saved tasks. No target execution or I/O. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON;
 const keyed=new Set(['keyed-shift','interrupted-keyed-shift','finite-shift']),resets=['page','line','word'],directions=['subtract','add'],modes=['repeat','plaintext-autokey','ciphertext-autokey'],coefficients=Array.from({length:29},(_,i)=>i);
 const valuesFor=parameter=>parameter==='a'||parameter==='b'?coefficients:parameter==='direction'?directions:parameter==='mode'?modes:resets;
 const own=(value,key)=>Object.prototype.hasOwnProperty.call(value,key),stable=value=>E.stable(value);
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 function captureTask(value){
  const task=J.capture(value,{maxBytes:2000000,maxDepth:24,maxNodes:250000});
  E.validateTask(task);return task;
 }
 function captureSelection(value){
  const selection=J.capture(value,{maxBytes:512,maxDepth:3,maxNodes:16}),keys=['version','step','parameter','value'];
  if(!selection||typeof selection!=='object'||Array.isArray(selection)||Object.keys(selection).length!==keys.length||!keys.every(key=>own(selection,key))||selection.version!==1||!Number.isInteger(selection.step)||selection.step<0||!['direction','reset','unit','mode','a','b','phase'].includes(selection.parameter)||(selection.parameter==='phase'?!(Number.isInteger(selection.value)&&selection.value>=1&&selection.value<=255):!valuesFor(selection.parameter).includes(selection.value)))throw Error('Choose one exact supported step parameter and destination.');
  return selection;
 }
 function unchanged(value,snapshot,capture){if(stable(capture(value))!==stable(snapshot))throw Error('The task or selected variation changed during preparation.');}
 // This structural helper grants no task, execution or evidence authority.
 // Full task geometry and identities remain checked by derive/prepare/validate.
 function changedSteps(input,chosen){
  const original=J.capture(input,{maxBytes:2000000,maxDepth:8,maxNodes:200000}),selection=captureSelection(chosen);
  if(!Array.isArray(original)||original.length>8||original.some(step=>!step||typeof step!=='object'||Array.isArray(step)))throw Error('Use at most eight plain method steps.');
  const step=original[selection.step],parameter=selection.parameter;
  if(step){
   const keys=step.op==='affine'?['op','a','b']:step.op==='reverse'?['op','unit']:step.op==='cumulative-difference'?['op','reset']:step.op==='keyed-shift'?['op','key','mode','direction','reset']:step.op==='interrupted-keyed-shift'?['op','key','direction','reset','interrupts']:step.op==='finite-shift'?['op','key','direction','reset']:null;
   const index=value=>Number.isInteger(value)&&value>=0&&value<=28;
   if(!keys||Object.keys(step).length!==keys.length||!keys.every(key=>own(step,key))||step.op==='affine'&&(!index(step.a)||!index(step.b))||step.op==='reverse'&&!resets.includes(step.unit)||own(step,'reset')&&!resets.includes(step.reset)||keyed.has(step.op)&&(!Array.isArray(step.key)||step.key.length<1||step.key.length>(step.op==='finite-shift'?20000:256)||!step.key.every(index)||!directions.includes(step.direction))||step.op==='keyed-shift'&&!modes.includes(step.mode)||step.op==='interrupted-keyed-shift'&&(!Array.isArray(step.interrupts)||!step.interrupts.length||step.interrupts.length>29||!step.interrupts.every((n,i)=>index(n)&&(!i||n>step.interrupts[i-1]))))throw Error('The selected method step is invalid.');
  }
  if(!step||!(['a','b'].includes(parameter)?step.op==='affine':parameter==='phase'?step.op==='keyed-shift'&&step.mode==='repeat':parameter==='direction'?keyed.has(step.op):parameter==='unit'?step.op==='reverse':parameter==='mode'?step.op==='keyed-shift':keyed.has(step.op)||step.op==='cumulative-difference'))throw Error('The selected step does not support this parameter variation.');
  if(parameter==='phase'&&selection.value>=step.key.length)throw Error('Choose a starting position within the saved repeating key.');
  if(step[parameter]===selection.value)throw Error('Choose a value different from the saved task.');
  const steps=JSON.parse(stable(original));if(parameter==='phase'){steps[selection.step].key=step.key.slice(selection.value).concat(step.key.slice(0,selection.value));if(stable(steps[selection.step].key)===stable(step.key))throw Error('This starting position repeats the unchanged key.');}else steps[selection.step][parameter]=selection.value;
  return freeze(steps);
 }
 function derive(parent,selection){
  const parameter=selection.parameter,steps=changedSteps(parent.steps,selection);
  const action=parameter==='phase'?'start at key position '+(selection.value+1):parameter==='a'?'multiply rune values by '+selection.value:parameter==='b'?'add '+selection.value+' to rune values':parameter==='direction'?(selection.value==='add'?'add key indices':'subtract key indices'):parameter==='unit'?'reverse runes within each '+selection.value:parameter==='mode'?'use '+selection.value:'restart at each '+selection.value;
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
   const operation=task.steps[step],parameters=operation.op==='affine'?['a','b']:operation.op==='keyed-shift'?['direction','reset','mode',...(operation.mode==='repeat'?['phase']:[])]:keyed.has(operation.op)?['direction','reset']:operation.op==='cumulative-difference'?['reset']:operation.op==='reverse'?['unit']:[];
   const seenPhases=new Set(operation.key?[stable(operation.key)]:[]);
   for(const parameter of parameters)for(const value of parameter==='phase'?Array.from({length:operation.key.length-1},(_,i)=>i+1):valuesFor(parameter)){
    if(operation[parameter]===value)continue;
    if(parameter==='phase'){const key=stable(operation.key.slice(value).concat(operation.key.slice(0,value)));if(seenPhases.has(key))continue;seenPhases.add(key);}
    const selection={version:1,step,parameter,value};
    try{derive(task,selection);}catch{continue;}
    items.push({selection,from:parameter==='phase'?0:operation[parameter],label:parameter==='phase'?'Start at key position '+(value+1):parameter==='a'?'Multiply rune values by '+value:parameter==='b'?'Add '+value+' to rune values':parameter==='direction'?(value==='add'?'Add the key values':'Subtract the key values'):parameter==='unit'?'Reverse runes within each '+value:parameter==='mode'?(value==='repeat'?'Repeat the starting key':value==='plaintext-autokey'?'Continue the key with decoded runes':'Continue the key with input runes'):'Restart at each '+value});
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
  const permutations={};
  function reversal(unit){
   if(permutations[unit])return permutations[unit];
   const output=[];let ordinal=0;
   for(const page of task.pages){let group=[];const flush=()=>{for(let i=group.length-1;i>=0;i--)output.push(group[i]);group=[];};
    for(const ch of page.text){if(runes.has(ch))group.push(ordinal++);else if(unit==='word'||unit==='line'&&/[\r\n]/.test(ch))flush();}flush();
   }
   return permutations[unit]=output;
  }
  const sameOutputs=item=>{
   if(!positions.page.length)return true;
   const {step:index,parameter,value}=item.selection,step=task.steps[index],before=positions[step.reset];
   // A later constant affine substitution discards every earlier rune value.
   if(task.steps.slice(index+1).some(later=>later.op==='affine'&&later.a===0))return true;
   if(parameter==='phase')return before.every(position=>step.key[position%step.key.length]===step.key[(position+value)%step.key.length]);
   if(parameter==='a'||parameter==='b'){
    // Compare the two complete substitutions over GP29, never actual page
    // outputs. Different coefficients are retained unless every residue agrees.
    const changed={...step,[parameter]:value};
    return coefficients.every(rune=>(step.a*rune+step.b)%29===(changed.a*rune+changed.b)%29);
   }
   if(parameter==='unit')return equal(reversal(step.unit),reversal(value));
   // All three modes use the literal seed until the segment exhausts it.
   // Once feedback is reached, no seed pattern alone proves equivalence.
   if(parameter==='mode')return maximum(before)<=step.key.length;
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
 const api={list,suggestions,prepare,validate,changedSteps,selection:value=>freeze(captureSelection(value))};if(node)module.exports=api;else root.TaskParameterVariants=api;
})(typeof globalThis!=='undefined'?globalThis:this);
