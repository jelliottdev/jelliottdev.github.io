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
  if(exact(criterion,['kind'])&&criterion.kind==='measurement')return freeze({id:'transformed-output-inspection-v1',criterion,completion:'all-cases',statuses:['rune-output','no-runes'],limit:'The declared outputs are ready to inspect. No language, readability or decryption result has been decided.'});
  if(exact(criterion,['kind','values'])&&criterion.kind==='exact-prefix'&&Array.isArray(criterion.values)&&criterion.values.length>=1&&criterion.values.length<=256&&criterion.values.every(n=>Number.isInteger(n)&&n>=0&&n<=28))return freeze({id:'exact-prefix-v1',criterion,completion:'first-match-or-exhaustion',statuses:['matched','not-matched'],limit:'An exact opening match is not a complete reading. A missing match does not reject the broader deciphering idea.'});
  if(exact(criterion,['kind','openings'])&&criterion.kind==='exact-prefix-set'&&Array.isArray(criterion.openings)&&criterion.openings.length>=1&&criterion.openings.length<=32){
   const names=new Set(),vectors=new Set();for(const opening of criterion.openings){if(!exact(opening,['id','values'])||typeof opening.id!=='string'||!/^[a-z][a-z0-9-]{0,63}$/.test(opening.id)||names.has(opening.id)||!Array.isArray(opening.values)||opening.values.length<1||opening.values.length>256||opening.values.some(n=>!Number.isInteger(n)||n<0||n>28)||vectors.has(E.stable(opening.values)))throw Error('Use distinct named complete rune openings.');names.add(opening.id);vectors.add(E.stable(opening.values));}
   return freeze({id:'exact-prefix-set-v1',criterion,completion:'all-cases',statuses:['matched','not-matched','no-runes'],limit:'Compare every declared output with each complete named opening. A match is a candidate, not a complete reading. Pages without runes are recorded separately.'});
  }
  const evaluation=Evaluators.describe(criterion);
  if(evaluation)return freeze({id:'language-reference-comparison-v1',criterion,completion:'all-cases',statuses:['compared','insufficient'],references:evaluation.references,minimumRunes:evaluation.minimumRunes,replicates:evaluation.replicates,limit:evaluation.limit});
  throw Error('Choose an explicit maintained opening, output inspection or pinned language-reference comparison.');
 }
 function assessValues(input,sequence){
  const policy=describe(input),values=capture(sequence);if(!Array.isArray(values)||values.length>20000||values.some(n=>!Number.isInteger(n)||n<0||n>28))throw Error('Use the exact bounded transformed rune indices.');
  if(policy.id==='transformed-output-inspection-v1')return freeze({status:values.length?'rune-output':'no-runes',runes:values.length});
  if(policy.id==='exact-prefix-v1')return freeze({status:policy.criterion.values.every((n,i)=>values[i]===n)?'matched':'not-matched',runes:values.length});
  if(policy.id==='exact-prefix-set-v1'){const matchingOpenings=policy.criterion.openings.filter(o=>o.values.every((n,i)=>values[i]===n)).map(o=>o.id);return freeze({status:values.length?(matchingOpenings.length?'matched':'not-matched'):'no-runes',runes:values.length,matchingOpenings});}
  const scorer=node?require('./language-score.js'):root.RuneLanguageScore;if(!scorer)throw Error('The pinned language-reference comparison is unavailable.');scorer.validateCriterion(policy.criterion);
  // This classification contains no score or verdict. Its two fields depend
  // only on the already validated length and maintained minimum. Actual score
  // claims are independently recomputed when their result receipt is admitted.
  return freeze({status:values.length<policy.minimumRunes?'insufficient':'compared',runes:values.length});
 }
 async function prepare(input,crypto=root.crypto){
  const source=capture(input);
  if(!exact(source,['task','inputVersion','run'])||!['raw','reviewed'].includes(source.inputVersion)||!exact(source.run,['id','createdAt','result'])||!HEX.test(source.run.id)||typeof source.run.createdAt!=='string'||!Number.isFinite(Date.parse(source.run.createdAt))||new Date(source.run.createdAt).toISOString()!==source.run.createdAt||!crypto?.subtle)throw Error('Use an unchanged original computation receipt and its text edition.');
  const policy=describe(source.task?.criterion);
  if(await hash(source.run.result,crypto)!==source.run.id)throw Error('The original result digest changed.');
  const result=await E.verify(source.task,source.run.result,crypto),runeSet=new Set(source.task.alphabet.map(v=>v.rune)),pages=[];
  for(const page of source.task.pages){
   const output=result.transformed.find(p=>p.page===page.id),runes=Array.from(output.text).filter(ch=>runeSet.has(ch)).length;
   const status=policy.id==='transformed-output-inspection-v1'?(runes?'rune-output':'no-runes'):policy.id==='exact-prefix-set-v1'?(!runes?'no-runes':result.matches.find(m=>m.page===page.id).matched?'matched':'not-matched'):policy.id==='exact-prefix-v1'?(result.matches.find(m=>m.page===page.id).matched?'matched':'not-matched'):result.languageScore.pages.find(p=>p.page===page.id).status;
   pages.push({pageId:page.id,inputSha256:await hash(page,crypto),runes,status});
  }
  const insufficientPages=pages.filter(p=>p.status==='insufficient').length,counts=policy.id==='exact-prefix-set-v1'?{computedPages:pages.length,usablePages:pages.filter(p=>p.status!=='no-runes').length,insufficientPages:0,noRunePages:pages.filter(p=>p.status==='no-runes').length,matchedPages:pages.filter(p=>p.status==='matched').length}:policy.id==='transformed-output-inspection-v1'?{computedPages:pages.length,runeOutputPages:pages.filter(p=>p.status==='rune-output').length,noRunePages:pages.filter(p=>p.status==='no-runes').length}:{computedPages:pages.length,usablePages:pages.length-insufficientPages,insufficientPages,...(policy.id==='exact-prefix-v1'?{matchedPages:pages.filter(p=>p.status==='matched').length}:{})};
  const token=Object.freeze({});prepared.set(token,freeze({schema:'liberpedia-finite-output-assessment-v1',policy,criterion:policy.criterion,source:{taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt},pages,counts}));return token;
 }
 function inspect(token){const value=prepared.get(token);if(!value)throw Error('Use an independently prepared output assessment.');return value;}
 const api={LIMITS,describe,assessValues,prepare,inspect};if(node)module.exports=api;else root.FiniteQuestionPolicy=api;
})(typeof globalThis!=='undefined'?globalThis:this);
