/* Maintained per-output assessments. Coverage and search decisions belong to a ledger. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,Evaluators=node?require('./output-evaluators.js'):root.OutputEvaluators;
 const LIMITS=Object.freeze({bytes:8*1024*1024,pages:75}),prepared=new WeakMap(),HEX=/^[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const capture=v=>J.capture(v,{maxBytes:LIMITS.bytes,maxDepth:24,maxNodes:500000});
 const hash=async(value,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');
 function describe(input){
  const criterion=capture(input);
  if(exact(criterion,['kind','values'])&&criterion.kind==='exact-prefix'&&Array.isArray(criterion.values)&&criterion.values.length>=1&&criterion.values.length<=256&&criterion.values.every(n=>Number.isInteger(n)&&n>=0&&n<=28))return freeze({id:'exact-prefix-v1',criterion,completion:'first-match-or-exhaustion',statuses:['matched','not-matched'],limit:'An exact opening match is not a complete reading. A missing match does not reject the broader deciphering idea.'});
  const evaluation=Evaluators.describe(criterion);
  if(evaluation)return freeze({id:'language-reference-comparison-v1',criterion,completion:'all-cases',statuses:['compared','insufficient'],references:evaluation.references,minimumRunes:evaluation.minimumRunes,replicates:evaluation.replicates,limit:evaluation.limit});
  throw Error('Choose an explicit maintained opening or pinned language-reference comparison.');
 }
 async function prepare(input,crypto=root.crypto){
  const source=capture(input);
  if(!exact(source,['task','inputVersion','run'])||!['raw','reviewed'].includes(source.inputVersion)||!exact(source.run,['id','createdAt','result'])||!HEX.test(source.run.id)||typeof source.run.createdAt!=='string'||!Number.isFinite(Date.parse(source.run.createdAt))||new Date(source.run.createdAt).toISOString()!==source.run.createdAt||!crypto?.subtle)throw Error('Use an unchanged original computation receipt and its text edition.');
  const policy=describe(source.task?.criterion);
  if(await hash(source.run.result,crypto)!==source.run.id)throw Error('The original result digest changed.');
  const result=await E.verify(source.task,source.run.result,crypto),runeSet=new Set(source.task.alphabet.map(v=>v.rune)),pages=[];
  for(const page of source.task.pages){
   const output=result.transformed.find(p=>p.page===page.id),runes=Array.from(output.text).filter(ch=>runeSet.has(ch)).length;
   const status=policy.id==='exact-prefix-v1'?(result.matches.find(m=>m.page===page.id).matched?'matched':'not-matched'):result.languageScore.pages.find(p=>p.page===page.id).status;
   pages.push({pageId:page.id,inputSha256:await hash(page,crypto),runes,status});
  }
  const insufficientPages=pages.filter(p=>p.status==='insufficient').length,counts={computedPages:pages.length,usablePages:pages.length-insufficientPages,insufficientPages,...(policy.id==='exact-prefix-v1'?{matchedPages:pages.filter(p=>p.status==='matched').length}:{})};
  const token=Object.freeze({});prepared.set(token,freeze({schema:'liberpedia-finite-output-assessment-v1',policy,criterion:policy.criterion,source:{taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt},pages,counts}));return token;
 }
 function inspect(token){const value=prepared.get(token);if(!value)throw Error('Use an independently prepared output assessment.');return value;}
 const api={LIMITS,describe,prepare,inspect};if(node)module.exports=api;else root.FiniteQuestionPolicy=api;
})(typeof globalThis!=='undefined'?globalThis:this);
