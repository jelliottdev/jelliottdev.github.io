/* Exact saved-computation relations. No decoding, novelty judgment or result admission. */
(function(root){
 'use strict';
 const L=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const HEX=/^[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const clone=v=>JSON.parse(L.stable(v));
 const whole=v=>Number.isSafeInteger(v)&&v>=0;
 const scalar=s=>typeof s==='string'&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(s);
 async function hash(value,cryptoAPI){return Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(L.stable(value)))),n=>n.toString(16).padStart(2,'0')).join('');}
 async function describe(task,inputVersion,cryptoAPI=root.crypto){
  const frozen=clone(task);if(!['raw','reviewed'].includes(inputVersion))throw Error('An exact input version is required.');await L.checkIdentity(frozen,cryptoAPI);
  const protocolId=await hash({schema:'liberpedia-computation-protocol-v1',engine:frozen.engine,inputVersion,alphabet:frozen.alphabet,steps:frozen.steps,criterion:frozen.criterion},cryptoAPI);
  const pages=[];for(const page of frozen.pages)pages.push({id:page.id,caseId:await hash({protocolId,page},cryptoAPI)});
  return {protocolId,pages};
 }
 function rational(value){return exact(value,['numerator','denominator'])&&typeof value.numerator==='string'&&typeof value.denominator==='string'&&/^(?:0|[1-9][0-9]{0,99})$/.test(value.numerator)&&/^[1-9][0-9]{0,99}$/.test(value.denominator);}
 function resultShape(task,result){
  const kind=task.criterion.kind,extra=kind==='word-prime-sums'?['wordSums']:kind==='word-affine-count'?['wordPairs']:[];
  if(!exact(result,['schema','taskId','engine','runnerVersion','metrics','matches','transformed',...extra])||result.schema!=='liberpedia-local-result-v1'||result.taskId!==task.taskId||result.engine!==task.engine||result.runnerVersion!=='1'||!Array.isArray(result.transformed)||result.transformed.length!==task.pages.length||!Array.isArray(result.matches))throw Error('The saved computation result has an invalid envelope.');
  const index=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),counts=Array(29).fill(0);let runeCount=0,adjacent=0,equal=0;
  for(let p=0;p<task.pages.length;p++){
   const output=result.transformed[p],input=task.pages[p];
   if(!exact(output,['page','text'])||output.page!==input.id||!scalar(output.text))throw Error('The saved output page order is invalid.');
   const a=Array.from(input.text),b=Array.from(output.text);if(a.length!==b.length||a.some((ch,i)=>index.has(ch)?!index.has(b[i]):b[i]!==ch))throw Error('The saved output does not preserve input rune geometry.');
   const values=b.filter(ch=>index.has(ch)).map(ch=>index.get(ch));runeCount+=values.length;adjacent+=Math.max(0,values.length-1);for(let i=0;i<values.length;i++){counts[values[i]]++;if(i&&values[i]===values[i-1])equal++;}
   if(kind==='exact-prefix'){const match=result.matches[p];if(!exact(match,['page','matched'])||match.page!==input.id||typeof match.matched!=='boolean'||match.matched!==task.criterion.values.every((v,i)=>values[i]===v))throw Error('The saved opening result is inconsistent.');}
  }
  if(result.matches.length!==(kind==='exact-prefix'?task.pages.length:0))throw Error('The saved matches do not cover the task.');
  const metrics=result.metrics,ioc=runeCount>1?counts.reduce((s,n)=>s+n*(n-1),0)/(runeCount*(runeCount-1)):0;
  if(!exact(metrics,['pages','runes','adjacentPairs','equalAdjacentPairs','ioc'])||metrics.pages!==task.pages.length||metrics.runes!==runeCount||metrics.adjacentPairs!==adjacent||metrics.equalAdjacentPairs!==equal||!Number.isFinite(metrics.ioc)||metrics.ioc<0||metrics.ioc>1||Math.abs(metrics.ioc-ioc)>1e-12)throw Error('The saved output metrics are inconsistent.');
  if(kind==='word-prime-sums'){
   const sums=result.wordSums;if(!exact(sums,['words','total','pages'])||!whole(sums.words)||!whole(sums.total)||!Array.isArray(sums.pages)||sums.pages.length!==task.pages.length)throw Error('Invalid saved word sums.');
   let words=0,total=0;for(let i=0;i<sums.pages.length;i++){
    const page=sums.pages[i];if(!exact(page,['page','words'])||page.page!==task.pages[i].id||!Array.isArray(page.words))throw Error('Invalid saved word-sum pages.');
    for(const word of page.words){if(!exact(word,['runes','sum'])||!scalar(word.runes)||!word.runes||!whole(word.sum)||Array.from(word.runes).some(ch=>!index.has(ch)))throw Error('Invalid saved word sum.');words++;total+=word.sum;}
   }
   if(words!==sums.words||total!==sums.total)throw Error('Inconsistent saved word-sum totals.');
  }
  if(kind==='word-affine-count'){
   const pairs=result.wordPairs;if(!exact(pairs,['opportunities','matches','expected','pages'])||!whole(pairs.opportunities)||!whole(pairs.matches)||pairs.matches>pairs.opportunities||!rational(pairs.expected)||!Array.isArray(pairs.pages)||pairs.pages.length!==task.pages.length)throw Error('Invalid saved word-pair totals.');
   let opportunities=0,matches=0;for(let i=0;i<pairs.pages.length;i++){const page=pairs.pages[i];if(!exact(page,['page','opportunities','matches','expected'])||page.page!==task.pages[i].id||!whole(page.opportunities)||!whole(page.matches)||page.matches>page.opportunities||!rational(page.expected))throw Error('Invalid saved word-pair page.');opportunities+=page.opportunities;matches+=page.matches;}
   if(opportunities!==pairs.opportunities||matches!==pairs.matches)throw Error('Inconsistent saved word-pair totals.');
  }
 }
 async function compare(requestedTask,requestedVersion,sources,cryptoAPI=root.crypto){
  const requested=clone(requestedTask),saved=clone(sources);if(!Array.isArray(saved))throw Error('Saved computation sources must be an array.');
  const wanted=await describe(requested,requestedVersion,cryptoAPI),wantedCases=new Map(wanted.pages.map(p=>[p.caseId,p.id])),covered=new Set(),seen=new Map(),evidence=[],exactTasks=[];
  for(const source of saved){
   if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result'])||typeof source.run.id!=='string'||!HEX.test(source.run.id)||typeof source.run.createdAt!=='string'||!Number.isFinite(Date.parse(source.run.createdAt)))throw Error('The saved evidence receipt is invalid.');
   const described=await describe(source.task,source.inputVersion,cryptoAPI),signature=L.stable(source);
   if(seen.has(source.task.taskId)){if(seen.get(source.task.taskId)!==signature)throw Error('Conflicting saved evidence for one task.');continue;}seen.set(source.task.taskId,signature);
   resultShape(source.task,source.run.result);if(await hash(source.run.result,cryptoAPI)!==source.run.id)throw Error('The saved result identity does not match its bytes.');
   if(described.protocolId!==wanted.protocolId)continue;
   const pages=described.pages.filter(p=>wantedCases.has(p.caseId)).map(p=>wantedCases.get(p.caseId));if(!pages.length)continue;
   pages.sort((a,b)=>requested.pages.findIndex(p=>p.id===a)-requested.pages.findIndex(p=>p.id===b));pages.forEach(id=>covered.add(id));
   evidence.push({taskId:source.task.taskId,resultId:source.run.id,pages,createdAt:source.run.createdAt});
   if(described.pages.length===wanted.pages.length&&pages.length===wanted.pages.length)exactTasks.push(source.task.taskId);
  }
  evidence.sort((a,b)=>a.taskId.localeCompare(b.taskId)||a.resultId.localeCompare(b.resultId));
  return {coveredPages:requested.pages.filter(p=>covered.has(p.id)).map(p=>p.id),remainingPages:requested.pages.filter(p=>!covered.has(p.id)).map(p=>p.id),evidence,exactTaskId:exactTasks.sort()[0]||null};
 }
 const api={describe,compare};if(typeof module==='object'&&module.exports)module.exports=api;else root.ComputationEvidence=api;
})(typeof globalThis!=='undefined'?globalThis:this);
