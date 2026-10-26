/* Lossless finite witness storage only; callers must still validate every plan and control. */
(function(root){
 'use strict';
 const J=typeof module==='object'&&module.exports?require('./finite-json.js'):root.FiniteJSON;
 const SHARED='finite-program-controls-shared-v1',LEGACY='finite-program-controls',HEX=/^[a-f0-9]{64}$/;
 const LIMITS=Object.freeze({maxBytes:2*1024*1024,maxDepth:24,maxNodes:300000});
 const capture=value=>{if(!J?.capture)throw Error('Finite control JSON capture is unavailable.');return J.capture(value,LIMITS);};
 const object=v=>v&&typeof v==='object'&&!Array.isArray(v),exact=(v,keys)=>object(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const text=(v,max)=>typeof v==='string'&&Array.from(v).length>=1&&Array.from(v).length<=max;
 const stable=v=>JSON.stringify(v,(_,item)=>object(item)?Object.fromEntries(Object.keys(item).sort().map(k=>[k,item[k]])):item);
 const alphabet=v=>Array.isArray(v)&&v.length===29&&v.every(row=>exact(row,['rune','latin','prime'])&&text(row.rune,1)&&text(row.latin,16)&&Number.isSafeInteger(row.prime)&&row.prime>=1&&row.prime<=1000000);
 const criterion=v=>exact(v,['kind','values'])&&v.kind==='exact-prefix'&&Array.isArray(v.values)&&v.values.length>=1&&v.values.length<=256&&v.values.every(n=>Number.isInteger(n)&&n>=0&&n<29);
 const setting=v=>exact(v,['operation','name','value'])&&Number.isInteger(v.operation)&&v.operation>=0&&v.operation<=7&&text(v.name,32);
 function task(v,shared){
  const fields=['schema','engine','title','pages','steps','taskId',...(shared?[]:['alphabet','criterion'])];
  return exact(v,fields)&&text(v.schema,100)&&text(v.engine,100)&&text(v.title,300)&&typeof v.taskId==='string'&&HEX.test(v.taskId)
   &&Array.isArray(v.pages)&&v.pages.length>=1&&v.pages.length<=75&&v.pages.every(p=>exact(p,['id','text'])&&text(p.id,100)&&typeof p.text==='string')
   &&Array.isArray(v.steps)&&v.steps.length<=8&&v.steps.every(object)&& (shared||alphabet(v.alphabet)&&criterion(v.criterion));
 }
 function members(v,shared){return Array.isArray(v)&&v.length>=1&&v.length<=1024&&v.every(member=>exact(member,['settings','control'])&&Array.isArray(member.settings)&&member.settings.length<=56&&member.settings.every(setting)&&exact(member.control,['label','task','expected_result_sha256'])&&text(member.control.label,1200)&&typeof member.control.expected_result_sha256==='string'&&HEX.test(member.control.expected_result_sha256)&&task(member.control.task,shared));}
 function checkedShared(value){
  if(!exact(value,['kind','alphabet','criterion','members'])||value.kind!==SHARED||!alphabet(value.alphabet)||!criterion(value.criterion)||!members(value.members,true))throw Error('Malformed shared finite controls.');
  return value;
 }
 function input(value){const result=capture(value);if(typeof result?.kind==='string'&&result.kind.startsWith('finite-program-controls-shared')&&result.kind!==SHARED)throw Error('Unsupported shared finite control format.');return result;}
 function compact(control){
  const value=input(control);if(value?.kind===SHARED)return checkedShared(value);
  // Legacy data is never trimmed or repaired: unsupported shapes remain for
  // the existing scientific validator, with every original field retained.
  if(!exact(value,['kind','members'])||value.kind!==LEGACY||!members(value.members,false))return value;
  const first=value.members[0].control.task,a=stable(first.alphabet),c=stable(first.criterion);
  if(!value.members.every(member=>stable(member.control.task.alphabet)===a&&stable(member.control.task.criterion)===c))return value;
  return capture({kind:SHARED,alphabet:first.alphabet,criterion:first.criterion,members:value.members.map(member=>{
   const {alphabet:ignoredAlphabet,criterion:ignoredCriterion,...rest}=member.control.task;
   return {settings:member.settings,control:{label:member.control.label,task:rest,expected_result_sha256:member.control.expected_result_sha256}};
  })});
 }
 function expand(control){
  const value=input(control);if(value?.kind!==SHARED)return value;checkedShared(value);
  return capture({kind:LEGACY,members:value.members.map(member=>({settings:member.settings,control:{label:member.control.label,task:{...member.control.task,alphabet:value.alphabet,criterion:value.criterion},expected_result_sha256:member.control.expected_result_sha256}}))});
 }
 const api={compact,expand};if(typeof module==='object'&&module.exports)module.exports=api;else root.FiniteControlStorage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
