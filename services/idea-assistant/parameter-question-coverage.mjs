/* Read-only prior-work lookup for one exact reviewed variation. No admission. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import {resolveParameterQuestion} from './parameter-question-source.mjs';
import {findEvidence,checkedEvidence} from './task-evidence.mjs';
import {resolveFamilyEvidence} from './family-evidence.mjs';
import {readPublishedEvidence} from './published-evidence.mjs';
const HEX=/^[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/,CASE=/^[a-z0-9][a-z0-9-]*$/,MAX=65536;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),same=(a,b)=>E.stable(a)===E.stable(b);
const ensure=(ok,message)=>{if(!ok)throw Error(message);},sha=async(v,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
async function readBody(request,signal){
 ensure(/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''),'JSON required');const length=request.headers.get('content-length');ensure(length===null||/^\d+$/.test(length)&&Number(length)<=MAX,'Body too large');ensure(!signal.aborted,'Cancelled');const reader=request.body?.getReader();ensure(reader,'Body required');let size=0,stop;const chunks=[],abort=new Promise((_,reject)=>{stop=()=>reject(Error('Cancelled'));signal.addEventListener('abort',stop,{once:true});});
 try{while(true){ensure(!signal.aborted,'Cancelled');const {done,value}=await Promise.race([reader.read(),abort]);if(done)break;size+=value.byteLength;ensure(size<=MAX,'Body too large');chunks.push(value);}}catch(error){try{void reader.cancel().catch(()=>{});}catch{}throw error;}finally{signal.removeEventListener('abort',stop);}
 const bytes=new Uint8Array(size);let at=0;for(const part of chunks){bytes.set(part,at);at+=part.byteLength;}return J.capture(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)),{maxBytes:MAX,maxDepth:16,maxNodes:10000});
}
export function createParameterQuestionCoverageHandler({crypto=globalThis.crypto,fetcher=globalThis.fetch,registry,history,programIndex,discoverEvidence=findEvidence,timeoutMs=45000}={}){
 ensure(Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=45000&&typeof discoverEvidence==='function','Invalid coverage options');
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers}),unavailable=()=>reply({state:'coverage-unavailable',code:'parameter-coverage-unavailable',lookupComplete:false,error:'Earlier work could not be checked reliably. Please retry.'},503),review=()=>reply({state:'review-required',code:'parameter-source-changed',error:'The reviewed variation changed. Review it again before checking earlier work.'},409),origin=env?.SITE_ORIGIN;
  try{ensure(typeof origin==='string'&&new URL(origin).origin===origin&&['http:','https:'].includes(new URL(origin).protocol),'Origin');}catch{return unavailable();}
  if(request.headers.get('origin')!==origin)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=origin;const url=new URL(request.url);if(url.pathname!=='/parameter-questions/coverage'||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){const keys=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);return request.headers.get('access-control-request-method')==='POST'&&keys.every(k=>k==='content-type')?new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}}):reply({error:'Request is not allowed.'},403);}
  if(request.method!=='POST'){headers.Allow='POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const db=env?.PROPOSALS,rates=[env?.TASK_LIMIT||env?.PROPOSAL_LIMIT].filter(Boolean);if(!db?.prepare||!rates.length||rates.some(r=>typeof r.limit!=='function'))return unavailable();
  const controller=new AbortController(),stop=()=>controller.abort();request.signal.addEventListener('abort',stop,{once:true});if(request.signal.aborted)stop();let rejectAbort;const aborted=new Promise((_,reject)=>{rejectAbort=()=>reject(Error('Cancelled'));controller.signal.addEventListener('abort',rejectAbort,{once:true});}),timer=setTimeout(stop,timeoutMs),live=()=>ensure(!controller.signal.aborted,'Cancelled');
  const work=async()=>{
   let body;try{body=await readBody(request,controller.signal);ensure(exact(body,['source','selection',...(Object.hasOwn(body||{},'parentSettings')?['parentSettings']:[]),'expectedPreviewHash'])&&typeof body.expectedPreviewHash==='string'&&HEX.test(body.expectedPreviewHash),'Body fields');}catch{live();return reply({error:'The reviewed variation could not be read.'},400);}
   for(const rate of rates){if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);live();}
   let preview;try{preview=await resolveParameterQuestion({source:body.source,selection:body.selection,...(Object.hasOwn(body,'parentSettings')?{parentSettings:body.parentSettings}:{})},{db,crypto,fetcher,registry,history,programIndex,signal:controller.signal});}catch{live();return review();}live();const previewHash=await sha(preview,crypto);live();if(previewHash!==body.expectedPreviewHash)return review();
   const task=preview.derivation.task,inputVersion=preview.derivation.parent.inputVersion,found=J.capture(await discoverEvidence({db,task,inputVersion,crypto,fetcher,signal:controller.signal}),{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000});live();
   const ids=task.pages.map(p=>p.id),covered=found?.coveredPages,remaining=found?.remainingPages,refs=found?.evidence;
   ensure(typeof found?.truncated==='boolean'&&Array.isArray(covered)&&Array.isArray(remaining)&&new Set(covered).size===covered.length&&new Set(remaining).size===remaining.length&&same(covered,ids.filter(id=>covered.includes(id)))&&same(remaining,ids.filter(id=>remaining.includes(id)))&&covered.every(id=>!remaining.includes(id))&&ids.every(id=>covered.includes(id)||remaining.includes(id))&&Array.isArray(refs)&&refs.length<=75,'Invalid coverage partition');
   // Recheck the exact retained receipts, rather than trusting a count or a
   // discovery adapter's source labels. No new target program is evaluated.
   const verified=await checkedEvidence({db,task,inputVersion,evidence:refs,crypto,fetcher,signal:controller.signal,includeSources:true});live();ensure(same(verified.comparison.coveredPages,covered)&&same(verified.comparison.remainingPages,remaining),'Coverage proof changed');
   let finding=null;
   if(['exact-prefix','exact-prefix-set'].includes(task.criterion.kind)){
    const matched=new Map();
    for(const source of verified.sources){const proved=refs.find(ref=>ref.taskId===source.task.taskId);ensure(proved,'Unreferenced opening source');for(const match of source.run.result.matches){if(!proved.pages.includes(match.page))continue;ensure(covered.includes(match.page)&&typeof match.matched==='boolean','Invalid opening finding');ensure(!matched.has(match.page)||matched.get(match.page)===match.matched,'Conflicting saved opening findings');matched.set(match.page,match.matched);}}
    ensure(covered.every(id=>matched.has(id)),'Missing covered opening finding');finding={kind:'opening-check',matchingPages:covered.filter(id=>matched.get(id))};
   }
   const families=new Map(),published=new Map();
   for(const p of found.familySources||[]){ensure(exact(p,['taskId','familyId','revision','caseId'])&&p.familyId==='deor-feedback-v1'&&HEX.test(p.taskId)&&HEX.test(p.revision)&&typeof p.caseId==='string'&&p.caseId.length<=200&&CASE.test(p.caseId)&&!families.has(p.taskId)&&refs.some(r=>r.taskId===p.taskId),'Invalid family mapping');families.set(p.taskId,p);}
   for(const p of found.publishedSources||[]){ensure(exact(p,['taskId','resultId','recordId','revision','caseId'])&&HEX.test(p.taskId)&&HEX.test(p.resultId)&&typeof p.recordId==='string'&&p.recordId.length<=100&&SLUG.test(p.recordId)&&HEX.test(p.revision)&&typeof p.caseId==='string'&&p.caseId.length<=200&&CASE.test(p.caseId)&&!families.has(p.taskId)&&!published.has(p.taskId)&&refs.some(r=>r.taskId===p.taskId&&r.resultId===p.resultId),'Invalid publication mapping');published.set(p.taskId,p);}
   const evidence=[];
   for(const ref of refs){let source;const family=families.get(ref.taskId),publication=published.get(ref.taskId);
    if(family){const proof=await resolveFamilyEvidence({db,taskId:ref.taskId,resultId:ref.resultId,inputVersion,createdAt:ref.createdAt,crypto,fetcher,signal:controller.signal});live();ensure(proof&&same(proof.familySource,family),'Family source changed');source={kind:'family',familyId:family.familyId,revision:family.revision,caseId:family.caseId};}
    else if(publication){const proof=await readPublishedEvidence({recordId:publication.recordId,revision:publication.revision,caseId:publication.caseId,crypto,fetcher,registry,history,programIndex,signal:controller.signal});live();ensure(proof&&proof.task.taskId===ref.taskId&&proof.run.id===ref.resultId&&proof.run.createdAt===ref.createdAt&&proof.inputVersion===inputVersion&&same(proof.publishedSource,publication),'Published source changed');source={kind:'published',recordId:publication.recordId,revision:publication.revision,caseId:publication.caseId};}
    else{const local=await db.prepare(`SELECT t.id FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id WHERE t.id=? AND t.input_version=? AND r.id=? AND r.created_at=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas i ON i.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`).bind(ref.taskId,inputVersion,ref.resultId,ref.createdAt,inputVersion).first();live();ensure(local?.id===ref.taskId,'Missing local source association');source={kind:'saved-task'};}
    evidence.push({taskId:ref.taskId,resultId:ref.resultId,createdAt:ref.createdAt,pages:ref.pages,source});
   }
   live();return reply({schema:'liberpedia-parameter-question-coverage-v1',previewHash,taskId:task.taskId,inputVersion,coveredPages:covered,remainingPages:remaining,lookupComplete:!found.truncated,finding,evidence});
  };
  try{return await Promise.race([work(),aborted]);}catch{return unavailable();}finally{clearTimeout(timer);request.signal.removeEventListener('abort',stop);controller.signal.removeEventListener('abort',rejectAbort);}
 };
}
