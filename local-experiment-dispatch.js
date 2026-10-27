/* Exact version dispatch only. V1 bytes/identities and its native result brand stay unchanged.
 * prepare(body,crypto) is legacy V1; V2 requires the exact third {schema,engine} selector.
 * verify returns a verified result for either version. inspect accepts only result objects
 * returned by THIS dispatcher's verify; a cloned result is never a verification certificate.
 */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,V=node?require('./declarative-rune-program.js'):root.DeclarativeRuneProgram,J=node?require('./finite-json.js'):root.FiniteJSON,verified=new WeakMap();
 const need=(ok,message)=>{if(!ok)throw Error(message);},freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
 function pair(value){need(value&&typeof value==='object'&&!Array.isArray(value),'Use an exact experiment version.');const schema=Object.getOwnPropertyDescriptor(value,'schema'),engine=Object.getOwnPropertyDescriptor(value,'engine');need(schema&&engine&&Object.hasOwn(schema,'value')&&Object.hasOwn(engine,'value'),'Experiment versions must be data fields.');return {schema:schema.value,engine:engine.value};}
 function select(value){const p=pair(value);if(p.schema===E.TASK&&p.engine===E.ENGINE)return E;if(V&&p.schema===V.TASK&&p.engine===V.ENGINE)return V;throw Error('Unsupported or mismatched experiment version.');}
 function resultVersion(engine,result){const p=pair(result);need(p.schema===engine.RESULT&&p.engine===engine.ENGINE,'The result belongs to another experiment version.');}
 function validateTask(task){return select(task).validateTask(task);}
 async function identity(task,crypto=root.crypto){return select(task).identity(task,crypto);}
 async function checkIdentity(task,crypto=root.crypto){return select(task).checkIdentity(task,crypto);}
 async function prepare(body,crypto=root.crypto,version){let engine=E;if(version!==undefined){need(version&&Reflect.ownKeys(version).length===2&&Object.hasOwn(version,'schema')&&Object.hasOwn(version,'engine'),'Choose an exact schema and engine pair.');engine=select(version);}return engine.prepare(body,crypto);}
 function run(task,options){return select(task).run(task,options);}
 async function verify(task,result,crypto=root.crypto){const engine=select(task);resultVersion(engine,result);const snapshot=freeze(J.capture(task,{maxBytes:2000000,maxDepth:24,maxNodes:500000})),receipt=await engine.verify(task,result,crypto);if(engine===E){verified.set(receipt,Object.freeze({task:snapshot,result:receipt}));return receipt;}const model=engine.inspect(receipt);verified.set(model.result,Object.freeze({token:receipt,engine}));return model.result;}
 function inspect(result){need(result&&typeof result==='object'&&verified.has(result),'Use a dispatcher-verified result object.');const receipt=verified.get(result);return receipt.engine?receipt.engine.inspect(receipt.token):receipt;}
 function summary(task,result){
  if(select(task)===E)return E.summary(task,result);
  task=V.validateTask(task);
  const receipt=inspect(result);need(E.stable(receipt.task)===E.stable(task),'The result belongs to another exact program.');
  const limit='Verified calculation only. Removing repeats changes their counts by construction; this does not identify filler, statistical significance, readable text or a decryption.';
  if(task.criterion.kind==='language-score'){const compared=result.languageScore.pages.filter(p=>p.status==='compared').length;return {finding:compared+' of '+task.pages.length+' pages compared with eight rune-language references.',comparison:[],limit:'These scores compare output rune order with fixed models and shuffled orders. They do not establish readability, identify a language or show decryption. Shuffle counts are not p-values.'};}
  if(task.criterion.kind==='exact-prefix-set')return {finding:result.matches.filter(p=>p.matched).length+' of '+task.pages.length+' pages begin with a supplied opening.',comparison:[],limit:'Only the declared complete openings are checked. A prefix match alone does not establish a decryption.'};
  const names=new Set(task.alphabet.map(a=>a.rune));let pairs=0,equal=0;for(const page of task.pages){let previous=null;for(const ch of page.text)if(names.has(ch)){if(previous!==null){pairs++;if(ch===previous)equal++;}previous=ch;}}
  return {finding:task.criterion.kind==='exact-prefix'?result.matches.filter(p=>p.matched).length+' of '+task.pages.length+' pages begin with the supplied opening.':'The program changed equal adjacent rune pairs from '+equal+' to '+result.metrics.equalAdjacentPairs+'.',comparison:[{label:'Original text',value:equal,total:pairs},{label:'After the program',value:result.metrics.equalAdjacentPairs,total:result.metrics.adjacentPairs}],limit};
 }
 const api=Object.freeze({stable:E.stable,validateTask,identity,prepare,checkIdentity,run,verify,inspect,summary});if(node)module.exports=api;else root.LocalExperimentDispatch=api;
})(typeof globalThis!=='undefined'?globalThis:this);
