/* Fixed batch orchestration. Target code runs in the visitor's existing worker. */
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import Settings from '../../finite-settings.js';
import Controls from '../../local-plan-controls.js';
import {validateCard} from './idea-relations.mjs';
import {loadInputBundle} from './official-inputs.mjs';
import {prepareFiniteCases,compileFiniteMember} from './finite-search-admission.mjs';
import {findFiniteEvidence} from './finite-search-evidence.mjs';
import {authorize} from './prepared-plans.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
const PROPOSAL=/^p_[a-f0-9]{64}$/,HEX=/^[a-f0-9]{64}$/,MAX=8*1024*1024;
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
export async function readFiniteJSON(message,max=MAX){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error('JSON required');
 const reader=message.body?.getReader();if(!reader)throw Error('Body required');let size=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('Request too large');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
export function createFiniteSearchHandler({fetcher=globalThis.fetch,now=()=>new Date(),discoverEvidence=findFiniteEvidence,prepareCases=prepareFiniteCases,taskHandler=createLocalTaskHandler({fetcher,now})}={}){
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers}),url=new URL(request.url),match=url.pathname.match(/^\/finite-search\/(p_[a-f0-9]{64})\/(evidence|prepare|create|results)$/);
  let allowed=false;try{allowed=typeof env?.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN&&['http:','https:'].includes(new URL(env.SITE_ORIGIN).protocol);}catch{}
  if(!allowed)return reply({error:'Batch research is unavailable.'},503);
  if(request.headers.get('origin')!==env.SITE_ORIGIN)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=env.SITE_ORIGIN;headers['Access-Control-Expose-Headers']='Retry-After';
  if(!match||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const keys=(request.headers.get('access-control-request-headers')||'').split(',').map(s=>s.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='POST'||keys.some(k=>k!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});
  }
  if(request.method!=='POST')return reply({error:'Method is not allowed.'},405);
  if(!env.PROPOSALS?.prepare||!env.PROPOSALS?.batch||!(env.TASK_LIMIT||env.PROPOSAL_LIMIT)?.limit)return reply({error:'Batch research is unavailable.'},503);
  const [,proposalId,action]=match,db=env.PROPOSALS,query=(sql,...args)=>db.prepare(sql).bind(...args);let quotaDay=null;
  try{
   const body=await readFiniteJSON(request,action==='evidence'?1000:MAX);
   if(!(await (env.TASK_LIMIT||env.PROPOSAL_LIMIT).limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success){headers['Retry-After']='60';return reply({error:'Please wait before trying again.',code:'rate-limited',retryAfterSeconds:60},429);}quotaDay=now().toISOString().slice(0,10);
   const row=await query('SELECT card_json FROM proposals WHERE id=?',proposalId).first();if(!row)return reply({error:'Confirmed idea not found.'},404);
   const card=validateCard(row.card_json);Settings.inspect(card);
   if(request.signal.aborted)return reply({error:'The request was cancelled.'},499);
   if(action==='evidence'||action==='prepare'){
    if(!exact(body,action==='evidence'?['inputVersion']:['inputVersion','cases'])||body.inputVersion!==card.rules.inputVersion.value||card.rules.inputVersion.status!=='specified')return reply({error:'The declared search changed.'},400);
    const controller=new AbortController(),abort=()=>controller.abort(),timer=setTimeout(abort,20000);request.signal.addEventListener('abort',abort,{once:true});let bundle;
    try{bundle=await loadInputBundle({fetcher,signal:controller.signal,read:readFiniteJSON});}finally{clearTimeout(timer);request.signal.removeEventListener('abort',abort);}
    if(request.signal.aborted)return reply({error:'The request was cancelled.'},499);
    if(action==='evidence'){
     const found=await discoverEvidence({db,card,bundle});return reply({schema:'liberpedia-finite-search-evidence-v1',proposalId,inputVersion:body.inputVersion,...found});
    }
    const preparedAt=now().toISOString();quotaDay=preparedAt.slice(0,10);
    const prepared=await prepareCases({db,proposalId,card,cases:body.cases,bundle:{schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]},crypto:globalThis.crypto,createdAt:preparedAt});
    return reply({schema:'liberpedia-finite-search-preparation-v1',proposalId,inputVersion:prepared.inputVersion,cases:prepared.cases});
   }
   // Outer admission/rate check covers this bounded batch. Internal calls use
   // the unchanged task/result handlers; there is no externally trusted bypass.
   const innerEnv={...env,TASK_LIMIT:{limit:async()=>({success:true})}},invoke=async(path,data)=>{
    const response=await taskHandler(new Request(new URL(path,url),{method:'POST',headers:{origin:env.SITE_ORIGIN,'Content-Type':'application/json'},body:JSON.stringify(data),signal:request.signal}),innerEnv),value=await response.json();
    if(!response.ok){const error=Error(value.error||'The batch could not be saved.');error.status=response.status;
     if(response.status===429&&value.code==='daily-quota'){error.code='daily-quota';if(typeof value.retryAt==='string'&&/^\d{4}-\d{2}-\d{2}T00:00:00\.000Z$/.test(value.retryAt)&&Number.isFinite(Date.parse(value.retryAt)))error.retryAt=value.retryAt;}
     if(response.status===429&&value.code==='rate-limited'){error.code='rate-limited';if(Number.isSafeInteger(value.retryAfterSeconds)&&value.retryAfterSeconds>0&&value.retryAfterSeconds<=86400)error.retryAfterSeconds=value.retryAfterSeconds;}
     throw error;}return value;
   };
   if(action==='create'){
    if(!exact(body,['cases'])||!Array.isArray(body.cases)||!body.cases.length||body.cases.length>12)return reply({error:'Select one to twelve reviewed cases.'},400);
    const seen=new Set();for(const item of body.cases){
     if(!exact(item,['task','inputVersion','parentTaskId','preparationId'])||item.parentTaskId!==null||item.inputVersion!==card.rules.inputVersion.value||seen.has(item.task?.taskId))throw Error('The reviewed cases changed.');seen.add(item.task.taskId);
     await E.checkIdentity(item.task);const controls=await Controls.prepare(item.task);if(!await authorize({db,proposalId,card,...item,controls}))return reply({error:'A case needs its original reviewed preparation.'},409);
     const issued=await query('SELECT basis_json FROM prepared_plans WHERE id=? AND proposal_id=?',item.preparationId,proposalId).first(),basis=issued&&JSON.parse(issued.basis_json);
     if(!exact(basis,['kind','settings','caseId'])||basis.kind!=='finite-settings')return reply({error:'A case needs its declared finite-settings preparation.'},409);
     const member=compileFiniteMember(card,basis.settings),descriptor=await Evidence.describe(item.task,item.inputVersion);
     if(item.task.pages.length!==1||!member.plan.pages.includes(item.task.pages[0].id)||E.stable(item.task.steps)!==E.stable(member.plan.steps)||E.stable(item.task.criterion)!==E.stable(member.plan.criterion)||member.plan.inputVersion!==item.inputVersion||descriptor.pages[0].caseId!==basis.caseId)return reply({error:'A case is outside the declared finite search.'},409);
    }
    const tasks=[];for(const item of body.cases){if(request.signal.aborted)return reply({error:'The request was cancelled; any created cases are retained.'},499);tasks.push(await invoke('/tasks',{proposalId,...item}));}
    return reply({schema:'liberpedia-finite-search-tasks-v1',proposalId,tasks});
   }
   if(!exact(body,['results'])||!Array.isArray(body.results)||!body.results.length||body.results.length>12)return reply({error:'Submit one to twelve completed cases.'},400);
   const seen=new Set();for(const item of body.results){
    if(!exact(item,['taskId','result'])||!HEX.test(item.taskId)||seen.has(item.taskId))throw Error('The completed cases changed.');seen.add(item.taskId);
    const row=await query('SELECT t.task_json FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id WHERE t.id=? AND links.proposal_id=?',item.taskId,proposalId).first();if(!row)return reply({error:'A completed case is not associated with this idea.'},409);
    await E.verify(JSON.parse(row.task_json),item.result);
   }
   const receipts=[];for(const item of body.results){if(request.signal.aborted)return reply({error:'The request was cancelled; any saved results are retained.'},499);const saved=await invoke('/tasks/'+item.taskId+'/results',{result:item.result});receipts.push({taskId:saved.taskId,state:saved.state,latestRun:saved.latestRun});}
   return reply({schema:'liberpedia-finite-search-results-v1',proposalId,receipts});
  }catch(error){
   if(error.code==='preparation-limit'&&quotaDay){const retryAt=new Date(Date.parse(quotaDay+'T00:00:00.000Z')+86400000).toISOString();return reply({error:'The daily prepared-plan limit has been reached.',code:'daily-quota',retryAt},429);}
   const details={};if(error.status===429&&['daily-quota','rate-limited'].includes(error.code)){details.code=error.code;if(error.retryAt)details.retryAt=error.retryAt;if(error.retryAfterSeconds){details.retryAfterSeconds=error.retryAfterSeconds;headers['Retry-After']=String(error.retryAfterSeconds);}}
   return reply({error:error.status?error.message:'The batch could not be checked. Retry; your original idea is unchanged.',...details},error.status||503);
  }
 };
}
