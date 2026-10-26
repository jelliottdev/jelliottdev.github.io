/* Lossless finite witness storage only; callers must still validate every plan and control. */
(function(root){
 'use strict';
 const J=typeof module==='object'&&module.exports?require('./finite-json.js'):root.FiniteJSON;
 const SHARED='finite-program-controls-shared-v1',POOLED='finite-program-controls-pooled-v1',LEGACY='finite-program-controls',HEX=/^[a-f0-9]{64}$/;
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
 function input(value){const result=capture(value);if(typeof result?.kind==='string'&&(result.kind.startsWith('finite-program-controls-shared')&&result.kind!==SHARED||result.kind.startsWith('finite-program-controls-pooled')&&result.kind!==POOLED))throw Error('Unsupported finite control format.');return result;}
 function compact(control){
  const value=input(control);if(value?.kind===POOLED){expandPooled(value);return value;}if(value?.kind===SHARED)return checkedShared(value);
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
  const value=input(control);if(value?.kind===POOLED)return expandPooled(value);if(value?.kind!==SHARED)return value;checkedShared(value);
  return capture({kind:LEGACY,members:value.members.map(member=>({settings:member.settings,control:{label:member.control.label,task:{...member.control.task,alphabet:value.alphabet,criterion:value.criterion},expected_result_sha256:member.control.expected_result_sha256}}))});
 }
 const CODES='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',encoder=new TextEncoder(),TEXT=Symbol('pooled-text'),STEP=Symbol('pooled-step');
 const need=(v,m)=>{if(!v)throw Error(m||'Malformed pooled finite controls.');},vector=v=>Array.isArray(v)&&v.length>=1&&v.length<=20000&&v.every(n=>Number.isInteger(n)&&n>=0&&n<29);
 function unicode(value){if(typeof value==='string'){need(!/[\ud800-\udfff]/u.test(value),'Pooled controls require valid Unicode.');return;}if(value&&typeof value==='object')for(const key of Object.keys(value)){unicode(key);unicode(value[key]);}}
 function compactPooled(control){
  let value=input(control);unicode(value);if(value?.kind===POOLED){expandPooled(value);return value;}
  value=compact(value);if(value?.kind!==SHARED)return value;checkedShared(value);
  const maps={strings:new Map(),keys:new Map(),texts:new Map(),steps:new Map()},pools={strings:[],keys:[],texts:[],steps:[]};
  const intern=(kind,v)=>{const id=stable(v);if(!maps[kind].has(id)){maps[kind].set(id,pools[kind].length);pools[kind].push(v);}return maps[kind].get(id);};
  let textSymbols=[...new Set(value.members.flatMap(m=>m.control.task.pages.flatMap(p=>Array.from(p.text))))].sort((a,b)=>a.codePointAt(0)-b.codePointAt(0));if(textSymbols.length>64)textSymbols=[];
  const codes=new Map(textSymbols.map((ch,i)=>[ch,CODES[i]])),rows=value.members.map(member=>{const c=member.control,t=c.task;return [member.settings.map(s=>[s.operation,intern('strings',s.name),vector(s.value)?[1,intern('keys',s.value)]:[0,s.value]]),...[t.schema,t.engine,t.title,c.label].map(s=>intern('strings',s)),t.pages.map(p=>[intern('strings',p.id),intern('texts',textSymbols.length?[1,Array.from(p.text,ch=>codes.get(ch)).join('')]:[0,p.text])]),t.steps.map(step=>{if(vector(step.key)){const {key,...rest}=step;return intern('steps',[rest,intern('keys',key)]);}return intern('steps',[step,null]);}),t.taskId,c.expected_result_sha256];});
  const packed=capture({kind:POOLED,alphabet:value.alphabet,criterion:value.criterion,textSymbols,pools,rows});expandPooled(packed);return packed;
 }
 function expandPooled(value){
  let packedNodes=0;function countPacked(v){need(++packedNodes<=LIMITS.maxNodes,'Pooled controls exceed their node bound.');if(v&&typeof v==='object')for(const key of Object.keys(v)){if(!Array.isArray(v))need(++packedNodes<=LIMITS.maxNodes,'Pooled controls exceed their node bound.');countPacked(v[key]);}}countPacked(value);unicode(value);need(exact(value,['kind','alphabet','criterion','textSymbols','pools','rows'])&&value.kind===POOLED&&alphabet(value.alphabet)&&criterion(value.criterion));
  need(Array.isArray(value.textSymbols)&&value.textSymbols.length<=64&&new Set(value.textSymbols).size===value.textSymbols.length&&value.textSymbols.every(ch=>typeof ch==='string'&&Array.from(ch).length===1),'Invalid pooled text symbols.');
  const p=value.pools;need(exact(p,['strings','keys','texts','steps'])&&Object.values(p).every(Array.isArray));
  need(p.strings.every(s=>typeof s==='string')&&p.keys.every(vector));
  const used={strings:new Set(),keys:new Set(),texts:new Set(),steps:new Set()},ref=(kind,id)=>{need(Number.isSafeInteger(id)&&id>=0&&id<p[kind].length,'Invalid pooled control reference.');used[kind].add(id);return p[kind][id];};
  const costs=p.texts.map(wire=>{need(Array.isArray(wire)&&wire.length===2&&[0,1].includes(wire[0])&&typeof wire[1]==='string','Invalid pooled text.');if(wire[0]===0)return encoder.encode(JSON.stringify(wire[1])).length;let cost=2;for(const ch of wire[1]){const at=CODES.indexOf(ch);need(at>=0&&at<value.textSymbols.length,'Invalid pooled text index.');cost+=encoder.encode(JSON.stringify(value.textSymbols[at])).length-2;need(cost<=LIMITS.maxBytes,'Expanded finite controls exceed their byte bound.');}return cost;});
  for(const step of p.steps)need(Array.isArray(step)&&step.length===2&&object(step[0])&&(step[1]===null||Number.isSafeInteger(step[1])&&step[1]>=0&&step[1]<p.keys.length&&!Object.hasOwn(step[0],'key')),'Invalid pooled step.');
  need(Array.isArray(value.rows)&&value.rows.length>=1&&value.rows.length<=1024);
  const selectedText=id=>{ref('texts',id);return {[TEXT]:id};},meta=(id,max)=>{const s=ref('strings',id);need(text(s,max));return s;};
  const members=value.rows.map(row=>{need(Array.isArray(row)&&row.length===9);const [settings,schema,engine,title,label,pages,steps,taskId,result]=row;
   need(Array.isArray(settings)&&settings.length<=56&&Array.isArray(pages)&&pages.length>=1&&pages.length<=75&&Array.isArray(steps)&&steps.length<=8&&typeof taskId==='string'&&HEX.test(taskId)&&typeof result==='string'&&HEX.test(result));
   return {settings:settings.map(s=>{need(Array.isArray(s)&&s.length===3&&Number.isInteger(s[0])&&s[0]>=0&&s[0]<=7&&Array.isArray(s[2])&&s[2].length===2&&[0,1].includes(s[2][0]));return {operation:s[0],name:meta(s[1],32),value:s[2][0]===1?ref('keys',s[2][1]):s[2][1]};}),control:{label:meta(label,1200),task:{schema:meta(schema,100),engine:meta(engine,100),title:meta(title,300),pages:pages.map(page=>{need(Array.isArray(page)&&page.length===2);return {id:meta(page[0],100),text:selectedText(page[1])};}),steps:steps.map(id=>{const [step,key]=ref('steps',id);return key===null?step:{[STEP]:{step,key:ref('keys',key)}};}),taskId,alphabet:value.alphabet,criterion:value.criterion},expected_result_sha256:result}};
  });
  for(const kind of Object.keys(used))need(used[kind].size===p[kind].length,'Unused pooled control values.');
  const graph={kind:LEGACY,members};let bytes=0,nodes=0;const add=n=>{bytes+=n;need(bytes<=LIMITS.maxBytes,'Expanded finite controls exceed their byte bound.');};
  // Account for every repeated reference as expanded JSON BEFORE copying any
  // members or decoding a potentially amplified Unicode string.
  function account(v,depth){need(depth<=LIMITS.maxDepth&&++nodes<=LIMITS.maxNodes,'Expanded finite controls exceed their node or depth bound.');if(v&&typeof v==='object'&&Object.hasOwn(v,TEXT)){add(costs[v[TEXT]]);return;}if(v&&typeof v==='object'&&Object.hasOwn(v,STEP)){const {step,key}=v[STEP],names=Object.keys(step);add(2+names.length);for(const name of names){need(++nodes<=LIMITS.maxNodes,'Expanded finite controls exceed their node or depth bound.');add(encoder.encode(JSON.stringify(name)).length+1);account(step[name],depth+1);}need(++nodes<=LIMITS.maxNodes,'Expanded finite controls exceed their node or depth bound.');add(6);account(key,depth+1);return;}if(typeof v==='string'){add(encoder.encode(JSON.stringify(v)).length);return;}if(v===null||typeof v!=='object'){add(JSON.stringify(v).length);return;}const array=Array.isArray(v),keys=Object.keys(v);add(2+Math.max(0,keys.length-1));for(const key of keys){if(!array){need(++nodes<=LIMITS.maxNodes,'Expanded finite controls exceed their node or depth bound.');add(encoder.encode(JSON.stringify(key)).length+1);}account(v[key],depth+1);}}
  account(graph,0);const decoded=new Map();function clone(v){if(v&&typeof v==='object'&&Object.hasOwn(v,TEXT)){const id=v[TEXT];if(!decoded.has(id)){const [tag,s]=p.texts[id];decoded.set(id,tag===0?s:Array.from(s,ch=>value.textSymbols[CODES.indexOf(ch)]).join(''));}return decoded.get(id);}if(v&&typeof v==='object'&&Object.hasOwn(v,STEP)){const {step,key}=v[STEP];return Object.fromEntries([...Object.keys(step).map(k=>[k,clone(step[k])]),['key',clone(key)]]);}if(Array.isArray(v))return v.map(clone);if(object(v))return Object.fromEntries(Object.keys(v).map(k=>[k,clone(v[k])]));return v;}
  return clone(graph);
 }
 const api={compact,compactPooled,expand};if(typeof module==='object'&&module.exports)module.exports=api;else root.FiniteControlStorage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
