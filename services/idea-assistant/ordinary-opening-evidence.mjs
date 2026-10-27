/* New literal opening evaluations over unchanged authoritative originals.
 * No requested-task result or historical finding is generated here. */
import E from '../../local-experiment.js';
import R from '../../computation-evidence.js';
import J from '../../finite-json.js';
import Programs from '../../published-opening-evidence-data.js';
import {findOpeningEvaluationSources} from './prefix-evaluation-sources.mjs';
import {publishedProgramIndex,readPublishedEvidence} from './published-evidence.mjs';
import {checkedEvidence} from './task-evidence.mjs';
export const SCHEMA='liberpedia-ordinary-derived-openings-coverage-v1';
const MAX=8*1024*1024,HEX=/^[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const need=(ok,message)=>{if(!ok)throw Error(message);},same=(a,b)=>E.stable(a)===E.stable(b),capture=v=>J.capture(v,{maxBytes:MAX,maxDepth:24,maxNodes:500000});
const hash=async(v,c)=>[...new Uint8Array(await c.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
const sourceOf=source=>({task:source.task,inputVersion:source.inputVersion,run:source.run});
const key=origin=>E.stable(origin),allowed=kind=>['measurement','exact-prefix','exact-prefix-set'].includes(kind);
function originFor(source,reference){return {kind:reference?'published':'local',taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt,...(reference?{recordId:reference.recordId,revision:reference.revision,caseId:reference.caseId}:{})};}
function validateOrigin(value){
 need(exact(value,['kind','taskId','resultId','inputVersion','createdAt',...(value?.kind==='published'?['recordId','revision','caseId']:[])])&&['local','published'].includes(value.kind)&&[value.taskId,value.resultId].every(s=>typeof s==='string'&&HEX.test(s))&&['raw','reviewed'].includes(value.inputVersion)&&typeof value.createdAt==='string'&&Number.isFinite(Date.parse(value.createdAt))&&new Date(value.createdAt).toISOString()===value.createdAt,'Invalid original opening receipt');
 if(value.kind==='published')need(typeof value.recordId==='string'&&value.recordId.length<=100&&SLUG.test(value.recordId)&&typeof value.revision==='string'&&HEX.test(value.revision)&&typeof value.caseId==='string'&&value.caseId.length<=200&&/^[a-z0-9][a-z0-9-]*$/.test(value.caseId),'Invalid published opening origin');
}
function bindOriginal(original){
 need(exact(original,['origin','source']),'Invalid original opening envelope');const {origin,source}=original;validateOrigin(origin);
 need(exact(source,['task','inputVersion','run',...(origin.kind==='published'?['publishedSource','provenance']:[])])&&exact(source.run,['id','createdAt','result'])&&same(originFor(source,origin.kind==='published'?origin:null),origin),'The original opening identity changed');
 if(origin.kind==='published'){need(source.provenance?.schema==='liberpedia-published-program-projection-v1'&&same(source.publishedSource,{taskId:origin.taskId,resultId:origin.resultId,recordId:origin.recordId,revision:origin.revision,caseId:origin.caseId}),'The original publication changed');}
 return sourceOf(source);
}
async function project(task,inputVersion,raw,crypto){
 const originals=capture(raw);need(Array.isArray(originals)&&originals.length<=75&&['exact-prefix','exact-prefix-set'].includes(task.criterion.kind),'Invalid literal opening derivation');await E.checkIdentity(task,crypto);
 const pages=new Map(task.pages.map(p=>[p.id,p.text])),runes=new Map(task.alphabet.map((r,i)=>[r.rune,i])),program=E.stable([task.engine,task.alphabet,task.steps]),claims=new Map(),used=new Map();
 for(const original of originals){const source=bindOriginal(original);need(source.inputVersion===inputVersion&&allowed(source.task?.criterion?.kind),'Unsupported original opening evaluation');await R.compare(source.task,inputVersion,[source],crypto);need(E.stable([source.task.engine,source.task.alphabet,source.task.steps])===program,'The original transformation changed');const id=key(original.origin);need(!used.has(id)||same(used.get(id),original),'Conflicting original receipts');used.set(id,original);
  for(const p of source.task.pages){if(pages.get(p.id)!==p.text)continue;const text=source.run.result.transformed.find(t=>t.page===p.id)?.text;need(typeof text==='string','Missing complete original page output');const values=[...text].filter(ch=>runes.has(ch)).map(ch=>runes.get(ch)),matched=task.criterion.kind==='exact-prefix'?task.criterion.values.every((v,i)=>values[i]===v):task.criterion.openings.some(o=>o.values.every((v,i)=>values[i]===v)),prior=claims.get(p.id);need(!prior||prior.text===text,'Conflicting original transformed pages');if(!prior||id<prior.id)claims.set(p.id,{id,text,matched});}
 }
 const coveredPages=task.pages.filter(p=>claims.has(p.id)).map(p=>p.id),remainingPages=task.pages.filter(p=>!claims.has(p.id)).map(p=>p.id),matchingPages=coveredPages.filter(id=>claims.get(id).matched),ids=[...new Set(coveredPages.map(id=>claims.get(id).id))].sort();
 return {summary:{coveredPages,matchingPages,remainingPages},originals:ids.map(id=>used.get(id)),evidence:ids.map(id=>({origin:used.get(id).origin,pages:coveredPages.filter(page=>claims.get(page).id===id)}))};
}
async function discoverOpeningEvidence({db,task,inputVersion,crypto=globalThis.crypto,fetcher=globalThis.fetch,signal,registry,history,programIndex}){
 const live=()=>need(!signal?.aborted,'Opening lookup cancelled');live();
 const local=await findOpeningEvaluationSources({db,task,inputVersion,crypto});live();let lookupComplete=local.lookupComplete,bytes=0;const originals=[],covered=new Set(),wanted=new Map(task.pages.map(p=>[p.id,p.text]));
 const retain=original=>{const source=bindOriginal(original),intersection=task.pages.filter(p=>source.task.pages.some(q=>q.id===p.id&&q.text===p.text)).map(p=>p.id);if(!intersection.some(id=>!covered.has(id)))return;const size=new TextEncoder().encode(E.stable(original)).length;if(originals.length>=75||bytes+size>MAX-131072){lookupComplete=false;return;}bytes+=size;originals.push(original);intersection.forEach(id=>covered.add(id));};
 for(const source of local.sources)retain({origin:originFor(source),source});
 const index=await publishedProgramIndex({registry,programIndex});live();const alphabetSha256=await hash(task.alphabet,crypto),pageHashes=new Map(await Promise.all(task.pages.map(async p=>[p.id,await hash(p.text,crypto)]))),candidates=[];
 for(const item of index?.entries||[])if(item.inputVersion===inputVersion&&item.alphabetSha256===alphabetSha256&&same(item.steps,task.steps)&&allowed(item.criterion.kind)){const pages=item.pages.filter(p=>pageHashes.get(p.id)===p.textSha256).map(p=>p.id);if(pages.length)candidates.push({reference:{recordId:item.recordId,revision:item.revision,caseId:item.caseId},pages,bytes:item.bytes});}
 const embedded=registry===undefined?Programs:registry;
 for(const entry of embedded?.entries||[])if(entry.task&&entry.inputVersion===inputVersion&&same(entry.task.alphabet,task.alphabet)&&same(entry.task.steps,task.steps)&&allowed(entry.task.criterion.kind)){const pages=entry.task.pages.filter(p=>wanted.get(p.id)===p.text).map(p=>p.id);if(pages.length)candidates.push({reference:{recordId:entry.recordId,revision:entry.revision,caseId:entry.caseId},pages,bytes:new TextEncoder().encode(E.stable(embedded)).length});}
 candidates.sort((a,b)=>b.pages.length-a.pages.length||E.stable(a.reference).localeCompare(E.stable(b.reference)));
 for(const candidate of candidates){if(!candidate.pages.some(id=>!covered.has(id)))continue;if(originals.length>=75||bytes+candidate.bytes>MAX-131072){lookupComplete=false;continue;}const source=await readPublishedEvidence({...candidate.reference,crypto,fetcher,signal,registry,history,programIndex});live();need(source&&source.provenance?.schema==='liberpedia-published-program-projection-v1','The original published program is unavailable');retain({origin:originFor(source,candidate.reference),source});}
 const p=await project(task,inputVersion,originals,crypto);live();const wire={schema:SCHEMA,provider:'public-opening-originals-v1',requestedTaskId:task.taskId,inputVersion,originals:p.originals,lookupComplete,summary:p.summary};need(new TextEncoder().encode(E.stable({task,wire})).length<=MAX-65536,'The opening request and original receipts exceed their replay bound');return {wire,evidence:p.evidence};
}
async function checkOpeningEvidence({db,task,inputVersion,evidence,crypto=globalThis.crypto,fetcher=globalThis.fetch,signal,registry,history,programIndex}){
 const refs=capture(evidence);need(Array.isArray(refs)&&refs.length<=75&&new Set(refs.map(r=>key(r?.origin))).size===refs.length,'Invalid pinned opening references');const originals=[];
 for(const ref of refs){need(exact(ref,['origin','pages'])&&Array.isArray(ref.pages)&&ref.pages.length>=1&&ref.pages.length<=75&&new Set(ref.pages).size===ref.pages.length,'Invalid pinned opening pages');validateOrigin(ref.origin);const o=ref.origin;let source;
  if(o.kind==='published')source=await readPublishedEvidence({recordId:o.recordId,revision:o.revision,caseId:o.caseId,crypto,fetcher,signal,registry,history,programIndex});
  else{const row=await db.prepare(`SELECT t.task_hash,t.task_json,t.input_version,r.result_json,r.created_at FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id AND r.id=? WHERE t.id=? AND t.input_version=? AND r.created_at=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`).bind(o.resultId,o.taskId,o.inputVersion,o.createdAt,o.inputVersion).first();need(row&&typeof row.task_json==='string'&&typeof row.result_json==='string'&&new TextEncoder().encode(row.task_json+row.result_json).length<=MAX,'Pinned local original is unavailable');const saved=JSON.parse(row.task_json);need(await hash(saved,crypto)===row.task_hash&&row.input_version===o.inputVersion&&row.created_at===o.createdAt,'Pinned original changed');source={task:saved,inputVersion:row.input_version,run:{id:o.resultId,createdAt:row.created_at,result:JSON.parse(row.result_json)}};}
  need(!signal?.aborted&&source,'Pinned original is unavailable');const original={origin:o,source};bindOriginal(original);originals.push(original);
 }
 const p=await project(task,inputVersion,originals,crypto);need(same(p.evidence,refs.slice().sort((a,b)=>key(a.origin).localeCompare(key(b.origin)))),'Pinned opening coverage changed');return p.summary;
}
export function combineOrdinaryOpeningCoverage(task,strict,derived){const covered=new Set([...strict.coveredPages,...derived.coveredPages]);return {coveredPages:task.pages.filter(p=>covered.has(p.id)).map(p=>p.id),remainingPages:task.pages.filter(p=>!covered.has(p.id)).map(p=>p.id),matchingPages:derived.matchingPages};}

// A positive may come from a strict family source outside the local/published
// original-output provider. Keep that decision separate from derived evidence.
export async function strictOpeningMatchingPages({db,task,inputVersion,evidence,crypto=globalThis.crypto,fetcher=globalThis.fetch,signal}){
 need(['exact-prefix','exact-prefix-set'].includes(task.criterion.kind),'Strict opening decisions require a literal opening criterion');
 const refs=capture(evidence);need(!signal?.aborted,'Strict opening verification cancelled');
 const checked=await checkedEvidence({db,task,inputVersion,evidence:refs,crypto,fetcher,signal,includeSources:true});need(!signal?.aborted,'Strict opening verification cancelled');
 const matches=new Map();
 for(const source of checked.sources){const ref=refs.find(ref=>ref.taskId===source.task.taskId&&ref.resultId===source.run.id&&ref.createdAt===source.run.createdAt);need(ref,'The strict opening receipt changed');for(const page of source.run.result.matches){if(!ref.pages.includes(page.page))continue;need(typeof page.matched==='boolean'&&(!matches.has(page.page)||matches.get(page.page)===page.matched),'Conflicting strict opening decisions');matches.set(page.page,page.matched);}}
 need(checked.comparison.coveredPages.every(id=>matches.has(id)),'A strict covered page has no opening decision');
 return {comparison:checked.comparison,matchingPages:task.pages.filter(page=>matches.get(page.id)===true).map(page=>page.id)};
}

async function boundedOpeningRead(work,options){
 const timeoutMs=options.timeoutMs??20000;need(Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=20000,'Invalid original-output deadline');const controller=new AbortController(),signal=options.signal?AbortSignal.any([options.signal,controller.signal]):controller.signal;let abort;const timer=setTimeout(()=>controller.abort(),timeoutMs),cancelled=new Promise((_,reject)=>{abort=()=>reject(Error('Original-output lookup cancelled or timed out'));signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();});
 try{return await Promise.race([Promise.resolve().then(()=>{need(!signal.aborted,'Opening lookup cancelled');return work({...options,signal});}),cancelled]);}finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
}
export const discoverOrdinaryOpeningEvidence=options=>boundedOpeningRead(discoverOpeningEvidence,options);
export const checkedOrdinaryOpeningEvidence=options=>boundedOpeningRead(checkOpeningEvidence,options);
