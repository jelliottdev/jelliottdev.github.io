/* Versioned declarative rune transformations. No generated code, I/O or inferred methods.
 * Alignment identifies retained input character slots, not mathematical dependencies:
 * a reversal or feedback step may change the value occupying a retained slot.
 */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON;
 const TASK='liberpedia-declarative-rune-task-v2',RESULT='liberpedia-declarative-rune-result-v2',ENGINE='rune-program-v2',RUNNER_VERSION='2';
 const LIMITS=Object.freeze({taskBytes:2000000,resultBytes:8*1024*1024,pages:75,runes:20000,characters:300000,steps:8}),verified=new WeakMap();
 const ensure=(ok,message)=>{if(!ok)throw Error(message);},same=(a,b)=>E.stable(a)===E.stable(b);
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function exact(value,keys){return value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));}
 function capture(value,maxBytes=LIMITS.taskBytes){return J.capture(value,{maxBytes,maxDepth:24,maxNodes:500000});}
 const literal=step=>['remove-rune-types','collapse-adjacent-repeats'].includes(step?.op);
 function legacyTask(task,pages=task.pages,steps=[],criterion=task.criterion){return {schema:E.TASK,engine:E.ENGINE,taskId:'0'.repeat(64),title:task.title,alphabet:task.alphabet,pages,steps,criterion};}
 function validateCaptured(task){
  ensure(exact(task,['schema','engine','taskId','title','alphabet','pages','steps','criterion'])&&task.schema===TASK&&task.engine===ENGINE&&typeof task.taskId==='string'&&task.taskId.length===64&&/^[a-f0-9]{64}$/.test(task.taskId),'Use an exact version-two task.');
  ensure(['measurement','exact-prefix','exact-prefix-set','language-score'].includes(task.criterion?.kind),'This program version needs a maintained output criterion.');
  E.validateTask(legacyTask(task));
  // E1 uses an end-anchored page regexp; require exact scalar width here as well.
  ensure(task.pages.every(p=>typeof p.id==='string'&&p.id.length===6),'Use exact page identifiers.');
  ensure(Array.isArray(task.steps)&&task.steps.length<=LIMITS.steps,'Use at most eight ordered steps.');
  for(const step of task.steps){
   if(step?.op==='remove-rune-types'){
    ensure(exact(step,['op','values'])&&Array.isArray(step.values)&&step.values.length>=1&&step.values.length<=29,'Choose a finite nonempty set of rune types.');
    ensure(step.values.every((v,i)=>Number.isSafeInteger(v)&&v>=0&&v<=28&&(i===0||step.values[i-1]<v)),'Rune types must be sorted distinct GP indices.');
   }else if(step?.op==='collapse-adjacent-repeats'){
    ensure(exact(step,['op','unit','policy'])&&['page','line','word'].includes(step.unit)&&['all-but-first','non-overlapping-pairs'].includes(step.policy),'Choose explicit collapse boundaries and run policy.');
   }else {
    // Structural E1 checks on an empty stage: finite-key coverage is checked
    // against the actual current text at execution, after any earlier deletion.
    E.validateTask(legacyTask(task,[{id:task.pages[0].id,text:''}],[step],{kind:'measurement'}));
   }
  }
  return task;
 }
 function validateTask(input){return freeze(validateCaptured(capture(input)));}
 async function digest(value,crypto){ensure(crypto?.subtle,'SHA-256 is required.');return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value)))),v=>v.toString(16).padStart(2,'0')).join('');}
 async function identity(input,crypto=root.crypto){const task=validateTask(input),body={...task};delete body.taskId;return digest(body,crypto);}
 async function prepare(input,crypto=root.crypto){
  const body=capture(input);ensure(exact(body,['title','alphabet','pages','steps','criterion']),'Use exact program inputs.');
  const task=validateCaptured({...body,schema:TASK,engine:ENGINE,taskId:'0'.repeat(64)});task.taskId=await identity(task,crypto);
  ensure(same(body,capture(input)),'The program changed during preparation.');return freeze(task);
 }
 async function checkIdentity(input,crypto=root.crypto){const task=validateTask(input);ensure(await identity(task,crypto)===task.taskId,'The program identity changed.');ensure(same(task,capture(input)),'The program changed while checking identity.');return task;}
 function run(input){
  const task=validateTask(input),index=new Map(task.alphabet.map((entry,i)=>[entry.rune,i]));
  let pages=task.pages.map(page=>{const chars=Array.from(page.text);return {id:page.id,chars,slots:Uint32Array.from({length:chars.length},(_,i)=>i),inputLength:chars.length,removed:[]};});
  task.steps.forEach((step,stepIndex)=>{
   if(!literal(step)){
    const current=pages.map(page=>({id:page.id,text:page.chars.join('')})),result=E.run(legacyTask(task,current,[step],{kind:'measurement'}));
    pages.forEach((page,i)=>{let cursor=0;for(const ch of result.transformed[i].text)page.chars[cursor++]=ch;ensure(cursor===page.chars.length,'A legacy operation changed character geometry.');});return;
   }
   for(const page of pages){
    let previous=null,runLength=0,write=0;const removedTypes=new Set(step.values||[]);
    for(let read=0;read<page.chars.length;read++){
     const ch=page.chars[read],value=index.get(ch);let remove=false;
     if(value!==undefined){
      if(step.op==='remove-rune-types')remove=removedTypes.has(value);
      else {runLength=value===previous?runLength+1:1;previous=value;remove=step.policy==='all-but-first'?runLength>1:runLength%2===0;}
     }else if(step.op==='collapse-adjacent-repeats'&&(step.unit==='word'||step.unit==='line'&&/[\r\n]/.test(ch))){previous=null;runLength=0;}
     if(remove)page.removed.push({inputIndex:page.slots[read],stepIndex,value});else {page.chars[write]=ch;page.slots[write]=page.slots[read];write++;}
    }
    page.chars.length=write;page.slots=page.slots.subarray(0,write);
   }
  });
  const finalPages=pages.map(page=>({id:page.id,text:page.chars.join('')})),assessed=E.run(legacyTask(task,finalPages,[],task.criterion));
  const result={schema:RESULT,engine:ENGINE,runnerVersion:RUNNER_VERSION,taskId:task.taskId,metrics:assessed.metrics,matches:assessed.matches,transformed:assessed.transformed,alignment:{kind:'retained-input-slots-v1',pages:pages.map(page=>({page:page.id,inputLength:page.inputLength,outputToInput:Array.from(page.slots),removed:page.removed}))},...(task.criterion.kind==='language-score'?{languageScore:assessed.languageScore}:{})};
  return freeze(capture(result,LIMITS.resultBytes));
 }
 function resultSnapshot(value){return JSON.stringify(value,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(key=>[key,v[key]])):v);}
 async function verify(input,submitted,crypto=root.crypto){
  // Keep one canonical submitted snapshot across the asynchronous identity check,
  // rather than retaining multiple character-alignment object graphs.
  const task=validateTask(input),resultText=resultSnapshot(capture(submitted,LIMITS.resultBytes));await checkIdentity(task,crypto);
  ensure(same(task,capture(input))&&resultText===resultSnapshot(capture(submitted,LIMITS.resultBytes)),'The submitted program or result changed during verification.');
  // No await or caller callback follows this mutation check.
  const expected=run(task);ensure(resultText===resultSnapshot(expected),'The submitted output, evaluation or alignment does not match the exact program.');
  const token=Object.freeze({});verified.set(token,freeze({task,result:expected,limit:'Verified execution of this declared program only. Slot alignment is not full data-dependency provenance, and output patterns do not establish filler or decryption.'}));return token;
 }
 function inspect(token){ensure(verified.has(token),'Use an independently verified result token.');return verified.get(token);}
 const api=Object.freeze({TASK,RESULT,ENGINE,RUNNER_VERSION,LIMITS,validateTask,identity,prepare,checkIdentity,run,verify,inspect});if(node)module.exports=api;else root.DeclarativeRuneProgram=api;
})(typeof globalThis!=='undefined'?globalThis:this);
