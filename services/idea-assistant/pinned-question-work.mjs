/* Public bounded question work. Source selection stays on the server; execution stays in the browser. */
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import J from '../../finite-json.js';
import {validateCard} from './idea-relations.mjs';
import {prepare as bindQuestion,identify} from './pinned-domain-question.mjs';
import {createPinnedQuestionCoordinator} from './pinned-question-coordinator.mjs';
import {createPinnedQuestionJobs} from './pinned-question-jobs.mjs';
const SCHEMA='liberpedia-pinned-question-work-v1',MAX_BODY=8192,ROUTE=/^\/ideas\/(p_[a-f0-9]{64})\/work$/;
const need=(v,m)=>{if(!v)throw Error(m);},exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x));
function validAction(value){
 if(!value||!Number.isSafeInteger(value.expectedRevision)||value.expectedRevision<0)return false;
 if(['advance','prepare-next'].includes(value.action))return exact(value,['action','expectedRevision']);
 if(value.action==='import-existing')return exact(value,['action','expectedRevision','importToken'])&&typeof value.importToken==='string'&&value.importToken.length>0&&value.importToken.length<=7000;
 if(value.action==='record-saved')return exact(value,['action','expectedRevision','reference','preparationId'])&&typeof value.preparationId==='string'&&/^prep_[a-f0-9]{64}$/.test(value.preparationId)&&exact(value.reference,['taskId','resultId','inputVersion','createdAt'])&&['taskId','resultId'].every(k=>typeof value.reference[k]==='string'&&/^[a-f0-9]{64}$/.test(value.reference[k]))&&typeof value.reference.inputVersion==='string'&&value.reference.inputVersion.length<=128&&typeof value.reference.createdAt==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value.reference.createdAt)&&Number.isFinite(Date.parse(value.reference.createdAt));
 return false;
}
async function body(request,signal){
 need(/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''),'JSON required');const declared=request.headers.get('content-length');need(declared===null||/^\d+$/.test(declared)&&Number(declared)<=MAX_BODY,'Body too large');const reader=request.body?.getReader();need(reader,'Missing body');let count=0;const parts=[],abort=()=>{reader.cancel().catch(()=>{});};signal.addEventListener('abort',abort,{once:true});try{for(;;){need(!signal.aborted,'Request cancelled');const {done,value}=await reader.read();if(done)break;count+=value.byteLength;need(count<=MAX_BODY,'Body too large');parts.push(value);}const bytes=new Uint8Array(count);let at=0;for(const part of parts){bytes.set(part,at);at+=part.byteLength;}const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));need(validAction(value),'Invalid action');return value;}finally{signal.removeEventListener('abort',abort);if(count>MAX_BODY||signal.aborted)await reader.cancel().catch(()=>{});}
}
export function createPinnedQuestionWorkHandler({fetcher=globalThis.fetch,crypto=globalThis.crypto,now=()=>new Date(),cursorKey,timeoutMs=20000}={}){
 need(typeof fetcher==='function'&&crypto?.subtle&&typeof now==='function'&&Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=20000,'Use bounded work-handler dependencies.');
 const clock=()=>{const value=now(),time=value instanceof Date?value.getTime():value;need(Number.isSafeInteger(time)&&time>=0,'Invalid work clock');return time;};
 const digest=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(n=>n.toString(16).padStart(2,'0')).join('');
 return async function handle(request,env){
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',Vary:'Origin'},reply=(value,status=200)=>new Response(JSON.stringify(value),{status,headers}),url=new URL(request.url),match=ROUTE.exec(url.pathname);let validOrigin=false;try{validOrigin=typeof env?.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN&&['http:','https:'].includes(new URL(env.SITE_ORIGIN).protocol);}catch{}
  if(!validOrigin)return reply({error:'Research progress is unavailable.'},503);if(request.headers.get('origin')!==env.SITE_ORIGIN)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=env.SITE_ORIGIN;
  if(!match)return reply({error:'Not found.'},404);if(url.search)return reply({error:'Use the saved question without extra request fields.'},400);
  if(request.method==='OPTIONS'){const method=request.headers.get('access-control-request-method'),fields=(request.headers.get('access-control-request-headers')||'').split(',').map(s=>s.trim().toLowerCase()).filter(Boolean);if(!['GET','POST'].includes(method)||fields.some(s=>s!=='content-type'))return reply({error:'Request is not allowed.'},403);return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});}
  if(!['GET','POST'].includes(request.method)){headers.Allow='GET, POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const db=env?.PROPOSALS,rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;if(!db?.prepare||!db?.batch||!rate?.limit)return reply({error:'Research progress is unavailable.'},503);
  const deadline=new AbortController(),signal=AbortSignal.any([request.signal,deadline.signal]),timer=setTimeout(()=>deadline.abort(),timeoutMs),live=()=>need(!signal.aborted,'Request cancelled or timed out'),boundedFetch=(url,init={})=>{live();return fetcher(url,{...init,signal:init.signal?AbortSignal.any([signal,init.signal]):signal});};let abort;
  const work=async()=>{
   live();let input=null;if(request.method==='POST')try{input=await body(request,signal);}catch{live();return reply({error:'Use a supported action and the current progress revision.'},400);}
   if(!(await rate.limit({key:'pinned-work:'+(request.headers.get('CF-Connecting-IP')||'unknown')}))?.success){headers['Retry-After']='60';return reply({error:'Please wait before continuing.',code:'rate-limited',retryAfterSeconds:60},429);}live();
   const proposalId=match[1],row=await db.prepare('SELECT p.id,p.card_hash,CASE WHEN length(CAST(p.card_json AS BLOB))<=? THEN p.card_json ELSE NULL END AS card_json,length(CAST(p.card_json AS BLOB)) AS card_bytes FROM research_ideas public JOIN proposals p ON p.id=public.proposal_id WHERE public.proposal_id=? LIMIT 1').bind(H.MAX_BYTES,proposalId).first();live();if(!row)return reply({error:'Saved idea not found.'},404);
   need(row.id===proposalId&&typeof row.card_hash==='string'&&/^[a-f0-9]{64}$/.test(row.card_hash)&&Number.isSafeInteger(row.card_bytes)&&row.card_bytes>=1&&row.card_bytes<=H.MAX_BYTES&&typeof row.card_json==='string','Saved question metadata changed');const card=validateCard(row.card_json),serialized=C.serialize(card);need(serialized===row.card_json&&await digest(serialized)===row.card_hash&&proposalId==='p_'+row.card_hash,'Saved question identity changed');live();
   if(identify(card)===null)return reply({schema:SCHEMA,supported:false,proposalId});
   const question=await bindQuestion({card,proposalId},{fetcher:boundedFetch,crypto});live();const deps={db,cursorKey:cursorKey??env.FACTORED_EVIDENCE_CURSOR_KEY,fetcher:boundedFetch,crypto,now:clock,signal,timeoutMs};let result;if(request.method==='GET'||input.action==='advance'){const coordinator=await createPinnedQuestionCoordinator(question,deps);live();const view=request.method==='POST'?await coordinator.advance({expectedRevision:input.expectedRevision}):await coordinator.read();result={work:view};}else{const jobs=await createPinnedQuestionJobs(question,deps);live();const {action,...args}=input;result=await jobs[action==='prepare-next'?'prepareNext':action==='import-existing'?'importExisting':'recordSaved'](args);}live();return reply({schema:SCHEMA,supported:true,proposalId,...J.capture(result,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:60000})});
  };
  try{return await Promise.race([Promise.resolve().then(work),new Promise((_,reject)=>{abort=()=>reject(Error('Request cancelled or timed out'));signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();})]);}catch(error){if(signal.aborted)return reply({error:'Research progress took too long. Your saved work is kept; try again.'},503);if(/revision changed|advanced concurrently|compare-and-swap|stale|generation|evidence changed/i.test(error?.message||''))return reply({error:'Saved work changed. Refresh before continuing.',code:'stale-progress'},409);return reply({error:'Research progress could not be verified. Please try again.'},503);}finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
 };
}
export {SCHEMA,MAX_BODY};
