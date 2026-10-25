/* Verified page evidence for a bounded research question. No fetching or generated code. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const E=node?require('./local-experiment.js'):root.LocalExperiment;
 const Evidence=node?require('./computation-evidence.js'):root.ComputationEvidence;
 const aggregates=new WeakMap(),HEX=/^[a-f0-9]{64}$/;
 const clone=value=>JSON.parse(E.stable(value));
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
 function freeze(value){if(value&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value);}return value;}
 function gcd(a,b){while(b){const r=a%b;a=b;b=r;}return a;}
 function rational(value){const n=BigInt(value.numerator),d=BigInt(value.denominator);if(n<0n||d<=0n)throw Error('Invalid exact page expectation.');const g=gcd(n,d);return {numerator:String(n/g),denominator:String(d/g)};}
 function sum(a,b){const n=BigInt(a.numerator)*BigInt(b.denominator)+BigInt(b.numerator)*BigInt(a.denominator),d=BigInt(a.denominator)*BigInt(b.denominator);return rational({numerator:String(n),denominator:String(d)});}
 function inspect(value){if(!value||!aggregates.has(value))throw Error('Question evidence must be independently verified before use.');return value;}
 async function summarize(task,inputVersion,sources,cryptoAPI=root.crypto){
  const requested=clone(task);
  const prefix=requested.criterion?.kind==='exact-prefix';
  if(!prefix&&(requested.criterion?.kind!=='word-affine-count'||requested.steps.length))throw Error('Question evidence supports exact prefixes or untransformed within-word affine counts only.');
  if(!Array.isArray(sources)||sources.length>75)throw Error('Use at most 75 saved computation sources for this question.');
  // Preserve an engine-branded frozen result when available; otherwise capture
  // a detached submission before awaiting validation. Never freeze caller data.
  const captured=sources.map(source=>{
   if(!exact(source,['task','inputVersion','run'])||!exact(source.run,['id','createdAt','result'])||!HEX.test(source.run.id))throw Error('Invalid saved question evidence.');
   const savedTask=clone(source.task);let result;
   try{E.summary(savedTask,source.run.result);result=source.run.result;}catch{result=clone(source.run.result);}
   return {task:savedTask,inputVersion:source.inputVersion,run:{id:source.run.id,createdAt:source.run.createdAt,result}};
  });
  await Evidence.describe(requested,inputVersion,cryptoAPI);
  if(captured.reduce((n,source)=>n+E.stable(source).length,0)>16000000)throw Error('Question evidence exceeds the bounded input size.');
  const comparison=await Evidence.compare(requested,inputVersion,captured,cryptoAPI),byTask=new Map(captured.map(source=>[source.task.taskId,source]));
  const choices=new Map(),values=new Map();
  // Compare all matching claims before selecting a witness. A second receipt
  // cannot disagree about the same exact page case and be silently ignored.
  for(const ref of comparison.evidence){
   const source=byTask.get(ref.taskId);
   for(const page of ref.pages){
    const measured=prefix?source.run.result.matches.find(item=>item.page===page):source.run.result.wordPairs.pages.find(item=>item.page===page),output=source.run.result.transformed.find(item=>item.page===page);
    const signature=E.stable(prefix?{matched:measured.matched,text:output.text}:{opportunities:measured.opportunities,matches:measured.matches,expected:rational(measured.expected),text:output.text});
    if(values.has(page)&&values.get(page)!==signature)throw Error('Conflicting saved results for the same exact question page.');
    values.set(page,signature);if(!choices.has(page))choices.set(page,{source,ref});
   }
  }
  const verified=new Map();
  for(const {source} of choices.values())if(!verified.has(source.task.taskId)){
   let result;try{E.summary(source.task,source.run.result);result=source.run.result;}catch{result=await E.verify(source.task,source.run.result,cryptoAPI);}
   verified.set(source.task.taskId,result);
  }
  if(prefix){
   const pages=[];for(const page of requested.pages){const selected=choices.get(page.id);if(!selected)continue;const {source,ref}=selected,match=verified.get(source.task.taskId).matches.find(item=>item.page===page.id);pages.push({page:page.id,matched:match.matched,source:{taskId:ref.taskId,resultId:ref.resultId,createdAt:ref.createdAt}});}
   const value=freeze({kind:'verified-exact-prefix-aggregate-v1',taskId:requested.taskId,inputVersion,criterion:clone(requested.criterion),complete:comparison.remainingPages.length===0,scope:'covered-pages-only',coveredPages:comparison.coveredPages.slice(),remainingPages:comparison.remainingPages.slice(),pages,matchingPages:pages.filter(page=>page.matched).map(page=>page.page),evidence:comparison.evidence.filter(ref=>verified.has(ref.taskId)).map(clone)});
   aggregates.set(value,{task:freeze(requested),inputVersion});return value;
  }
  let opportunities=0,matches=0,expected={numerator:'0',denominator:'1'};const pages=[];
  for(const page of requested.pages){
   const selected=choices.get(page.id);if(!selected)continue;
   const {source,ref}=selected,measured=verified.get(source.task.taskId).wordPairs.pages.find(item=>item.page===page.id),mean=rational(measured.expected);
   opportunities+=measured.opportunities;matches+=measured.matches;expected=sum(expected,mean);
   pages.push({page:page.id,opportunities:measured.opportunities,matches:measured.matches,expected:mean,source:{taskId:ref.taskId,resultId:ref.resultId,createdAt:ref.createdAt}});
  }
  const value=freeze({kind:'verified-word-affine-aggregate-v1',taskId:requested.taskId,inputVersion,criterion:clone(requested.criterion),complete:comparison.remainingPages.length===0,scope:'covered-pages-only',coveredPages:comparison.coveredPages.slice(),remainingPages:comparison.remainingPages.slice(),pages,wordPairs:{opportunities,matches,expected},evidence:comparison.evidence.filter(ref=>verified.has(ref.taskId)).map(clone)});
  aggregates.set(value,{task:freeze(requested),inputVersion});return value;
 }
 function paired(a,b){
  inspect(a);inspect(b);if(a.kind!=='verified-word-affine-aggregate-v1'||b.kind!=='verified-word-affine-aggregate-v1')throw Error('Paired boundary evidence requires affine counts.');if(!a.complete||!b.complete)throw Error('Both boundary comparisons need complete verified page coverage.');
  const left=aggregates.get(a),right=aggregates.get(b),signature=entry=>E.stable({inputVersion:entry.inputVersion,engine:entry.task.engine,alphabet:entry.task.alphabet,steps:entry.task.steps,criterion:{...entry.task.criterion,boundaries:'non-rune'},pages:entry.task.pages.slice().sort((x,y)=>x.id.localeCompare(y.id))});
  if(signature(left)!==signature(right)||a.criterion.boundaries===b.criterion.boundaries)throw Error('Paired question evidence needs identical text, settings and source version with opposite boundary rules.');
  return freeze({separate:a.criterion.boundaries==='non-rune'?a:b,joined:a.criterion.boundaries==='hyphen-period'?a:b});
 }
 const api={summarize,inspect,paired};if(node)module.exports=api;else root.QuestionEvidence=api;
})(typeof globalThis!=='undefined'?globalThis:this);
