/* Fixed batch orchestration. Target code runs in the visitor's existing worker. */
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import Settings from '../../finite-settings.js';
import Controls from '../../local-plan-controls.js';
import {validateCard} from './idea-relations.mjs';
import {loadInputBundle} from './official-inputs.mjs';
import {prepareFiniteCases,compileFiniteMember,unwrapAuthoredMemberBasis} from './finite-search-admission.mjs';
import {createAuthoredFiniteSourceLoader} from './authored-finite-origin.mjs';
import {findFiniteEvidence} from './finite-search-evidence.mjs';
import {authorize} from './prepared-plans.mjs';
import {createLocalTaskHandler} from './local-tasks.mjs';
import {preparePageGroups,reviewPageGroupCreation} from './page-group-admission.mjs';
const PROPOSAL=/^p_[a-f0-9]{64}$/,HEX=/^[a-f0-9]{64}$/,MAX=8*1024*1024;
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
export async function readFiniteJSON(message,max=MAX){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error('JSON required');
 const reader=message.body?.getReader();if(!reader)throw Error('Body required');let size=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('Request too large');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
export function createFiniteSearchHandler({fetcher=globalThis.fetch,now=()=>new Date(),discoverEvidence=findFiniteEvidence,prepareCases=prepareFiniteCases,taskHandler,settingsAPI=Settings,authorizeDomain,routePrefix,reuseCasesBeforeCreate,verifyGroupSnapshot}={}){
 if(settingsAPI!==Settings&&settingsAPI!==Settings.factored)throw Error('Unsupported finite search policy.');
 const factored=settingsAPI===Settings.factored;
 if(factored&&typeof authorizeDomain!=='function'||!factored&&authorizeDomain!==undefined)throw Error('A factored search needs its maintained domain authority.');
 if(routePrefix!==undefined&&(!['factored-prefix-search','factored-output-search','factored-inspection-search'].includes(routePrefix)||!factored))throw Error('Unsupported finite search route.');
 if(routePrefix!==undefined?typeof reuseCasesBeforeCreate!=='function':reuseCasesBeforeCreate!==undefined)throw Error('Unsupported create reuse policy.');
 if(verifyGroupSnapshot!==undefined&&(!factored||typeof verifyGroupSnapshot!=='function'))throw Error('Unsupported grouped snapshot authority.');
 const route=factored?(routePrefix||'factored-search'):'finite-search',routePattern=new RegExp('^/'+route+'/(p_[a-f0-9]{64})/'+(factored?'(evidence|prepare|create|results|prepare-groups|create-groups)':'(evidence|prepare|create|results)')+'$');
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers}),url=new URL(request.url),match=url.pathname.match(routePattern);
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
  const [,proposalId,action]=match,grouped=action==='prepare-groups'||action==='create-groups',creating=action==='create'||action==='create-groups',db=env.PROPOSALS,query=(sql,...args)=>db.prepare(sql).bind(...args);let quotaDay=null;
  try{
   const body=await readFiniteJSON(request,action==='evidence'?(factored?40*1024:1000):MAX);
   if(!(await (env.TASK_LIMIT||env.PROPOSAL_LIMIT).limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success){headers['Retry-After']='60';return reply({error:'Please wait before trying again.',code:'rate-limited',retryAfterSeconds:60},429);}quotaDay=now().toISOString().slice(0,10);
   const row=await query('SELECT card_json FROM proposals WHERE id=?',proposalId).first();
   if(factored){
    const keys=action==='prepare-groups'?['domainId','inputVersion','groups','snapshotToken']:action==='create-groups'?['domainId','snapshotToken','groups']:action==='evidence'?['inputVersion','domainId','cursor']:action==='prepare'?['domainId','inputVersion','cases','snapshotToken']:action==='create'?['domainId','snapshotToken','cases']:['domainId','results'];
    if(!exact(body,[...keys,...(body&&Object.hasOwn(body,'authoredOrigin')?['authoredOrigin']:[])])||typeof body.domainId!=='string'||!HEX.test(body.domainId)||((action==='prepare'||creating||grouped)&&typeof body.snapshotToken!=='string')||(action==='evidence'&&body.cursor!==null&&typeof body.cursor!=='string'))return reply({error:'The declared search request changed.'},400);
   }
   const authoredOrigin=factored?body.authoredOrigin:undefined,loadAuthoredSource=createAuthoredFiniteSourceLoader(fetcher),handleTask=taskHandler||createLocalTaskHandler({fetcher,now,loadAuthoredSource});
   if(!row&&!(factored&&action==='evidence'&&authoredOrigin!==undefined))return reply({error:'Confirmed idea not found.'},404);
   let card=row?validateCard(row.card_json):null;
   if(authoredOrigin!==undefined){
    try{const source=await loadAuthoredSource(authoredOrigin);if(!card){card=validateCard(source.card);const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(card))))].map(v=>v.toString(16).padStart(2,'0')).join('');if(proposalId!=='p_'+hash)throw Error();}if(E.stable(source.card)!==E.stable(card)||source.domain.domainId!==body.domainId||source.inputVersion!==card.rules.inputVersion.value)throw Error();}
    catch{return reply({error:'The authored finite source, card or domain changed. Review it again.',code:'stale-scan'},409);}
   }
   settingsAPI.inspect(card);
   let currentDomain,bundle;
   if(request.signal.aborted)return reply({error:'The request was cancelled.'},499);
   if(action==='evidence'||action==='prepare'||grouped||factored&&action==='create'){
    if((!factored&&!exact(body,action==='evidence'?['inputVersion']:['inputVersion','cases']))||!creating&&(body.inputVersion!==card.rules.inputVersion.value||card.rules.inputVersion.status!=='specified'))return reply({error:'The declared search changed.'},400);
    const controller=new AbortController(),abort=()=>controller.abort(),timer=setTimeout(abort,20000);request.signal.addEventListener('abort',abort,{once:true});
    try{bundle=await loadInputBundle({fetcher,signal:controller.signal,read:readFiniteJSON});}finally{clearTimeout(timer);request.signal.removeEventListener('abort',abort);}
    if(request.signal.aborted)return reply({error:'The request was cancelled.'},499);
    if(factored)currentDomain=await authorizeDomain({db,card,bundle,body,proposalId,action,env,request,authoredOrigin,loadAuthoredSource});
    if(factored&&request.signal.aborted)return reply({error:'The request was cancelled.'},499);
    if(action==='evidence'){
     const found=await discoverEvidence({db,card,bundle,body,proposalId,currentDomain,env,request});if(factored)return reply(found);return reply({schema:'liberpedia-finite-search-evidence-v1',proposalId,inputVersion:body.inputVersion,...found});
    }
    if(action==='prepare-groups'){
     if(typeof verifyGroupSnapshot!=='function')return reply({error:'Grouped page reviews are unavailable.'},503);
     const preparedAt=now().toISOString();quotaDay=preparedAt.slice(0,10);const selected=await preparePageGroups({db,proposalId,card,bundle:{schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]},currentDomain,groups:body.groups,policy:routePrefix==='factored-inspection-search'?'inspection':routePrefix==='factored-output-search'?'output':routePrefix==='factored-prefix-search'?'prefix':'strict',cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:Date.parse(preparedAt),createdAt:preparedAt,verifySnapshot:()=>verifyGroupSnapshot({db,proposalId,currentDomain,body,env}),signal:request.signal,authoredOrigin,loadAuthoredSource});
     return reply({schema:'liberpedia-page-group-preparation-v1',proposalId,domainId:selected.domainId,inputVersion:selected.inputVersion,groups:selected.groups,totals:selected.totals});
    }
    if(action==='prepare'){
    const preparedAt=now().toISOString();quotaDay=preparedAt.slice(0,10);
    const prepared=await prepareCases({db,proposalId,card,cases:body.cases,bundle:{schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]},crypto:globalThis.crypto,createdAt:preparedAt,settingsAPI,currentDomain,body,env,request,authoredOrigin,loadAuthoredSource});
    return reply({schema:'liberpedia-finite-search-preparation-v1',proposalId,inputVersion:prepared.inputVersion,cases:prepared.cases,...(factored?{sources:prepared.sources||[],sourceLinks:prepared.sourceLinks||[]}:{})});
    }
   }
   // Outer admission/rate check covers this bounded batch. Internal calls use
   // the unchanged task/result handlers; there is no externally trusted bypass.
   const innerEnv={...env,TASK_LIMIT:{limit:async()=>({success:true})}},invoke=async(path,data)=>{
    const response=await handleTask(new Request(new URL(path,url),{method:'POST',headers:{origin:env.SITE_ORIGIN,'Content-Type':'application/json'},body:JSON.stringify(data),signal:request.signal}),innerEnv),value=await response.json();
    if(!response.ok){const error=Error(value.error||'The batch could not be saved.');error.status=response.status;
     if(response.status===429&&value.code==='daily-quota'){error.code='daily-quota';if(typeof value.retryAt==='string'&&/^\d{4}-\d{2}-\d{2}T00:00:00\.000Z$/.test(value.retryAt)&&Number.isFinite(Date.parse(value.retryAt)))error.retryAt=value.retryAt;}
     if(response.status===429&&value.code==='rate-limited'){error.code='rate-limited';if(Number.isSafeInteger(value.retryAfterSeconds)&&value.retryAfterSeconds>0&&value.retryAfterSeconds<=86400)error.retryAfterSeconds=value.retryAfterSeconds;}
     throw error;}return value;
   };
   if(action==='create-groups'){
    if(typeof verifyGroupSnapshot!=='function')return reply({error:'Grouped page reviews are unavailable.'},503);
    const reviewed=await reviewPageGroupCreation({db,proposalId,card,bundle:{schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]},currentDomain,groups:body.groups,policy:routePrefix==='factored-inspection-search'?'inspection':routePrefix==='factored-output-search'?'output':routePrefix==='factored-prefix-search'?'prefix':'strict',cursorKey:env.FACTORED_EVIDENCE_CURSOR_KEY,now:now().getTime(),verifySnapshot:()=>verifyGroupSnapshot({db,proposalId,currentDomain,body,env}),signal:request.signal,authoredOrigin,loadAuthoredSource}),tasks=[];
    for(const group of reviewed.selection.groups){if(request.signal.aborted)return reply({error:'The request was cancelled; any created groups are retained.'},499);const item=reviewed.requests.find(item=>item.groupId===group.id),{groupId,...ordinary}=item;tasks.push({groupId,view:await invoke('/tasks',{proposalId,...ordinary})});}
    return reply({schema:'liberpedia-page-group-tasks-v1',proposalId,domainId:reviewed.selection.domainId,tasks});
   }
   if(action==='create'){
    if((!factored&&!exact(body,['cases']))||!Array.isArray(body.cases)||!body.cases.length||body.cases.length>12)return reply({error:'Select one to twelve reviewed cases.'},400);
    const seen=new Set(),reviewed=[];for(const item of body.cases){
     if(!exact(item,['task','inputVersion','parentTaskId','preparationId'])||item.parentTaskId!==null||item.inputVersion!==card.rules.inputVersion.value||seen.has(item.task?.taskId))throw Error('The reviewed cases changed.');seen.add(item.task.taskId);
     await E.checkIdentity(item.task);
     const issued=await query('SELECT basis_json FROM prepared_plans WHERE id=? AND proposal_id=?',item.preparationId,proposalId).first();let basis;try{basis=issued&&unwrapAuthoredMemberBasis(JSON.parse(issued.basis_json),authoredOrigin,currentDomain?.domain.id);}catch(error){return reply({error:error.message},409);}
     if(!exact(basis,['kind','settings','caseId'])||basis.kind!==(routePrefix==='factored-inspection-search'?'factored-inspection-settings':routePrefix==='factored-output-search'?'factored-output-settings':factored?'factored-finite-settings':'finite-settings'))return reply({error:'A case needs its declared finite-settings preparation.'},409);
     const controls=await Controls.prepare(item.task);if(!await authorize({db,proposalId,card,...item,controls,loadAuthoredSource}))return reply({error:'A case needs its original reviewed preparation.'},409);
     const member=compileFiniteMember(card,basis.settings,settingsAPI,routePrefix==='factored-inspection-search'?'transformed-output-inspection-v1':routePrefix==='factored-output-search'?'language-reference-comparison-v1':undefined),descriptor=await Evidence.describe(item.task,item.inputVersion);
     if(factored&&(item.task.engine!==currentDomain.domain.engine||E.stable(item.task.alphabet)!==E.stable(currentDomain.domain.alphabet)||item.task.pages.some(page=>!currentDomain.domain.pages.some(actual=>actual.id===page.id&&actual.text===page.text))))return reply({error:'A reviewed case uses an earlier source version. Prepare it again.'},409);
     if(item.task.pages.length!==1||!member.plan.pages.includes(item.task.pages[0].id)||E.stable(item.task.steps)!==E.stable(member.plan.steps)||E.stable(item.task.criterion)!==E.stable(member.plan.criterion)||member.plan.inputVersion!==item.inputVersion||descriptor.pages[0].caseId!==basis.caseId)return reply({error:'A case is outside the declared finite search.'},409);
     reviewed.push({id:basis.caseId,programId:descriptor.protocolId,pageId:item.task.pages[0].id,task:item.task,settings:basis.settings,request:item});
    }
    const reuse=reuseCasesBeforeCreate?await reuseCasesBeforeCreate({db,proposalId,currentDomain,body,env,request,cases:reviewed}):null;
    const toCreate=reuse?reviewed.filter(item=>reuse.missing.some(missing=>missing.pageId===item.pageId&&E.stable(missing.settings)===E.stable(item.settings))).map(item=>item.request):body.cases;
    const tasks=[];for(const item of toCreate){if(request.signal.aborted)return reply({error:'The request was cancelled; any created cases are retained.'},499);tasks.push(await invoke('/tasks',{proposalId,...item}));}
    if(reuse)return reply({schema:routePrefix==='factored-inspection-search'?'liberpedia-factored-inspection-search-tasks-v1':routePrefix==='factored-output-search'?'liberpedia-factored-output-search-tasks-v1':'liberpedia-factored-prefix-search-tasks-v1',proposalId,tasks,sources:reuse.sources,sourceLinks:reuse.sourceLinks});
    return reply({schema:'liberpedia-finite-search-tasks-v1',proposalId,tasks});
   }
   if((!factored&&!exact(body,['results']))||!Array.isArray(body.results)||!body.results.length||body.results.length>12)return reply({error:'Submit one to twelve completed cases.'},400);
   const seen=new Set();for(const item of body.results){
    if(!exact(item,['taskId','result'])||!HEX.test(item.taskId)||seen.has(item.taskId))throw Error('The completed cases changed.');seen.add(item.taskId);
    const row=await query('SELECT t.task_json FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id WHERE t.id=? AND links.proposal_id=?',item.taskId,proposalId).first();if(!row)return reply({error:'A completed case is not associated with this idea.'},409);
    if(authoredOrigin!==undefined){const owned=await query('SELECT origin_json FROM local_task_all_origins WHERE task_id=? AND proposal_id=? AND origin_json=?',item.taskId,proposalId,E.stable(authoredOrigin)).first();if(!owned||E.stable(JSON.parse(owned.origin_json))!==E.stable(authoredOrigin))return reply({error:'A completed case belongs to another authored finite source.'},409);}
    await E.verify(JSON.parse(row.task_json),item.result);
   }
   const receipts=[];for(const item of body.results){if(request.signal.aborted)return reply({error:'The request was cancelled; any saved results are retained.'},499);const saved=await invoke('/tasks/'+item.taskId+'/results',{result:item.result});receipts.push({taskId:saved.taskId,state:saved.state,latestRun:saved.latestRun});}
   return reply({schema:'liberpedia-finite-search-results-v1',proposalId,receipts});
  }catch(error){
   if(factored&&request.signal.aborted)return reply({error:'The request was cancelled.'},499);
   if(error.code==='group-review-required')return reply({error:error.message,code:error.code,refreshRequired:true,sources:error.sources,sourceLinks:error.sourceLinks},409);
   if(error.code==='preparation-limit'&&quotaDay){const retryAt=new Date(Date.parse(quotaDay+'T00:00:00.000Z')+86400000).toISOString();return reply({error:'The daily prepared-plan limit has been reached.',code:'daily-quota',retryAt},429);}
   const details={};if(typeof error.code==='string'&&['invalid-cursor','stale-scan','source-too-large'].includes(error.code))details.code=error.code;if(error.status===429&&['daily-quota','rate-limited'].includes(error.code)){details.code=error.code;if(error.retryAt)details.retryAt=error.retryAt;if(error.retryAfterSeconds){details.retryAfterSeconds=error.retryAfterSeconds;headers['Retry-After']=String(error.retryAfterSeconds);}}
   return reply({error:error.status?error.message:'The batch could not be checked. Retry; your original idea is unchanged.',...details},error.status||503);
  }
 };
}
