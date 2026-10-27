/* A separate descriptive assessment of independently verified saved output.
 * This never creates a requested-task receipt or a historical language verdict. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,R=node?require('./computation-evidence.js'):root.ComputationEvidence,J=node?require('./finite-json.js'):root.FiniteJSON,L=node?require('./language-score.js'):root.RuneLanguageScore;
 const MAX_BYTES=8*1024*1024,MAX_SOURCES=75,MAX_RUNES=200000,proofs=new WeakSet(),HEX=/^[a-f0-9]{64}$/;
 const need=(ok,message)=>{if(!ok)throw Error(message);},same=(a,b)=>E.stable(a)===E.stable(b),capture=v=>J.capture(v,{maxBytes:MAX_BYTES,maxDepth:24,maxNodes:500000});
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 const key=s=>E.stable([s.task.taskId,s.run.id,s.run.createdAt]);
 const hash=async(v,c)=>[...new Uint8Array(await c.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
 async function evaluate(options,crypto=root.crypto){
  const input=capture(options);need(exact(input,['task','inputVersion','sources'])&&['raw','reviewed'].includes(input.inputVersion)&&Array.isArray(input.sources)&&input.sources.length<=MAX_SOURCES,'Use an explicit requested task and at most 75 original receipts.');
  const {task,inputVersion,sources}=input;await E.checkIdentity(task,crypto);L.validateCriterion(task.criterion);
  const index=new Map(task.alphabet.map((r,i)=>[r.rune,i])),requestedPages=new Map(task.pages.map(p=>[p.id,p.text])),program=E.stable([task.engine,task.alphabet,task.steps]);
  need(task.pages.reduce((n,p)=>n+[...p.text].filter(ch=>index.has(ch)).length,0)<=MAX_RUNES,'The assessment exceeds its 200,000-rune bound.');
  // Preflight the complete replay budget before any original replay or score.
  // Repeated dated envelopes share work only when every task/result byte agrees.
  const planned=new Map();let replayRunes=0;
  for(const source of sources){
   need(exact(source,['task','inputVersion','run'])&&['raw','reviewed'].includes(source.inputVersion)&&exact(source.run,['id','createdAt','result'])&&typeof source.run.id==='string'&&HEX.test(source.run.id)&&typeof source.run.createdAt==='string'&&Number.isFinite(Date.parse(source.run.createdAt)),'Use a complete original receipt.');
   need(['measurement','exact-prefix','exact-prefix-set','language-score'].includes(source.task?.criterion?.kind),'The original evaluation cannot supply this assessment.');
   E.validateTask(source.task);
   const id=E.stable([source.task.taskId,source.run.id]),taskBytes=E.stable(source.task),resultBytes=E.stable(source.run.result),prior=planned.get(id);
   need(!prior||prior.taskBytes===taskBytes&&prior.resultBytes===resultBytes,'Conflicting original computation bytes.');
   if(!prior){const runes=new Set(source.task.alphabet.map(r=>r.rune));replayRunes+=source.task.pages.reduce((n,p)=>n+[...p.text].filter(ch=>runes.has(ch)).length,0);need(replayRunes<=MAX_RUNES,'Original replay exceeds its 200,000-rune bound.');planned.set(id,{taskBytes,resultBytes});}
  }
  const description=await R.describe(task,inputVersion,crypto),targetCases=new Map(description.pages.map(p=>[p.id,p.caseId])),claims=new Map(),verified=new Map(),replayed=new Map(),descriptions=new Map();
  for(const source of sources){
   const replayKey=E.stable([source.task.taskId,source.run.id]),prior=replayed.get(replayKey);
   // E.verify checks the exact original task, all result fields and arithmetic;
   // hashing its returned result binds the dated envelope without a second
   // Relations.compare language-score calculation over the same original.
   let result=prior?.result;if(!prior){result=await E.verify(source.task,source.run.result,crypto);need(await hash(result,crypto)===source.run.id,'The original result digest changed.');replayed.set(replayKey,{result});}
   const id=key(source),existing=verified.get(id);need(!existing||same(existing,source),'Conflicting dated original receipts.');verified.set(id,{task:source.task,inputVersion:source.inputVersion,run:{...source.run,result}});
   if(source.inputVersion!==inputVersion||E.stable([source.task.engine,source.task.alphabet,source.task.steps])!==program)continue;
   const descriptionKey=E.stable([source.task.taskId,source.inputVersion]);let sourceDescription=descriptions.get(descriptionKey);if(!sourceDescription){sourceDescription=await R.describe(source.task,source.inputVersion,crypto);descriptions.set(descriptionKey,sourceDescription);}const sourceCases=new Map(sourceDescription.pages.map(p=>[p.id,p.caseId]));
   for(const page of source.task.pages){
    if(requestedPages.get(page.id)!==page.text)continue;
    const text=result.transformed.find(p=>p.page===page.id).text,old=claims.get(page.id);need(!old||old.text===text,'Conflicting output for an exact page and transformation.');
    if(!old||id<old.id){claims.set(page.id,{id,text,page:{pageId:page.id,targetCaseId:targetCases.get(page.id),sourceCriterion:source.task.criterion,sourceCaseId:sourceCases.get(page.id),source:{taskId:source.task.taskId,resultId:source.run.id,createdAt:source.run.createdAt,inputVersion:source.inputVersion}}});}
   }
  }
  const pages=task.pages.filter(p=>claims.has(p.id)).map(p=>{const claim=claims.get(p.id),values=[...claim.text].filter(ch=>index.has(ch)).map(ch=>index.get(ch));return {...claim.page,assessment:L.evaluate(values)};}),used=new Set([...claims.values()].map(p=>p.id)),coveredPages=pages.map(p=>p.pageId),remainingPages=task.pages.filter(p=>!claims.has(p.id)).map(p=>p.id),insufficientPages=pages.filter(p=>p.assessment.status==='insufficient').map(p=>p.pageId),originalSources=[...verified].filter(([id])=>used.has(id)).sort((a,b)=>a[0].localeCompare(b[0])).map(([,s])=>s);
  const body=capture({schema:'liberpedia-derived-output-assessment-v1',kind:'language-comparison-from-verified-output-v1',requested:{taskId:task.taskId,inputVersion,criterion:task.criterion},coveredPages,remainingPages,insufficientPages,complete:!remainingPages.length,pages,originalSources,limit:'This descriptive language-sample comparison is assessed now from independently verified saved output. Insufficient text is not a negative result; similarity is not a translation. No requested-task receipt, historical language verdict, public attribution or search-completeness claim is established.'});
  const proofId=await hash(body,crypto);need(same(capture(options),input),'Assessment input changed during verification.');const proof=freeze(capture({...body,proofId}));proofs.add(proof);return proof;
 }
 function inspect(proof){need(proofs.has(proof),'Independently verify the output assessment first.');return proof;}
 const api={evaluate,inspect,MAX_BYTES,MAX_SOURCES,MAX_RUNES};if(node)module.exports=api;else root.VerifiedOutputAssessment=api;
})(typeof globalThis!=='undefined'?globalThis:this);
