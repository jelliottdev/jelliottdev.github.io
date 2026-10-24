/* Propose a fixed scope extension only. No AI, persistence or execution. */
import C from '../../claim-specification.js';
import L from '../../local-experiment.js';
import {validateCard} from './idea-relations.mjs';

const MAX_BODY=1024,MAX_SOURCE=512*1024,MAX_TOTAL=2000000;
const UNSOLVED=Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0'));
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
async function jsonBody(message,max){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error('JSON required');
 const length=message.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>max))throw Error('Body too large');
 const reader=message.body?.getReader();if(!reader)throw Error('Body required');const parts=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('Body too large');}parts.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);return {value:JSON.parse(text),text};
}
export function createTaskExtensionHandler({fetcher=globalThis.fetch,timeoutMs=20000}={}){
 if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>20000)throw Error('Invalid source deadline');
 return async function handle(request,env){
  const allowed=env?.SITE_ORIGIN,headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let valid=false;try{valid=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!valid)return reply({error:'Scope extension is unavailable.'},503);
  if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url),match=url.pathname.match(/^\/tasks\/([a-f0-9]{64})\/extensions$/);
  if(!match||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const hs=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='POST'||hs.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!=='POST'){headers.Allow='POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;
  if(!env?.PROPOSALS?.prepare||!rate?.limit)return reply({error:'Scope extension is unavailable.'},503);
  try{
   const body=await jsonBody(request,MAX_BODY),value=body.value;
   if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==1||value.scope!=='remaining-lp2'||(body.text.match(/"(?:[^"\\]|\\.)*"/g)||[]).length!==2)throw Error('Invalid scope');
  }catch{return reply({error:'Choose the supported remaining LP2 scope.'},400);}
  try{
   if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   const query=(sql,...args)=>env.PROPOSALS.prepare(sql).bind(...args).first();
   const row=await query(`SELECT t.id,t.task_json,t.task_hash,links.proposal_id,links.input_version,links.parent_task_id,p.card_json,p.card_hash
    FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id
    JOIN research_ideas public ON public.proposal_id=links.proposal_id JOIN proposals p ON p.id=links.proposal_id
    WHERE t.id=? ORDER BY CASE WHEN links.proposal_id=t.proposal_id THEN 0 ELSE 1 END,links.created_at,links.proposal_id LIMIT 1`,match[1]);
   if(!row)return reply({error:'Registered experiment not found.'},404);
   const parent=JSON.parse(row.task_json);await L.checkIdentity(parent);
   if(parent.taskId!==row.id||await digest(L.stable(parent))!==row.task_hash||!['raw','reviewed'].includes(row.input_version))throw Error('Stored task mismatch');
   const card=validateCard(row.card_json),cardHash=await digest(C.serialize(card));
   if(row.card_hash!==cardHash||row.proposal_id!=='p_'+cardHash)throw Error('Stored public card mismatch');
   const covered=new Set(),addCoverage=task=>task.pages.forEach(page=>{if(UNSOLVED.includes(page.id))covered.add(page.id);});
   const protocol=task=>L.stable({alphabet:task.alphabet,steps:task.steps,criterion:task.criterion});
   addCoverage(parent);const signature=protocol(parent),seen=new Set([parent.taskId]);let ancestorId=row.parent_task_id,historyStopped=false;
   while(ancestorId!==null){
    if(typeof ancestorId!=='string'||!/^[a-f0-9]{64}$/.test(ancestorId)||seen.has(ancestorId)||seen.size>=75)throw Error('Invalid or excessive coverage history');
    seen.add(ancestorId);
    // Follow only this public idea's own edge, never a foreign private context.
    const ancestor=await query(`SELECT t.id,t.task_json,t.task_hash,links.input_version,links.parent_task_id
     FROM local_task_ideas links JOIN local_tasks t ON t.id=links.task_id
     WHERE links.task_id=? AND links.proposal_id=?`,ancestorId,row.proposal_id);
    if(!ancestor){historyStopped=true;break;}
    const task=JSON.parse(ancestor.task_json);await L.checkIdentity(task);
    if(task.taskId!==ancestor.id||ancestor.id!==ancestorId||await digest(L.stable(task))!==ancestor.task_hash)throw Error('Stored ancestor mismatch');
    if(ancestor.input_version!==row.input_version||protocol(task)!==signature){historyStopped=true;break;}
    addCoverage(task);ancestorId=ancestor.parent_task_id;
   }
   const coveredPages=UNSOLVED.filter(id=>covered.has(id)),ids=UNSOLVED.filter(id=>!covered.has(id));
   const context={proposalId:row.proposal_id,parentTaskId:parent.taskId,coveredPages};
   if(!ids.length)return reply({state:'scope-covered',...context,reason:'The linked tasks already include all 56 unsolved LP2 pages. No additional pages were added.'});
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
   const aborted=new Promise((_,reject)=>controller.signal.addEventListener('abort',()=>reject(Error('Source batch aborted')),{once:true}));
   const pages=new Array(ids.length);let next=0,total=0;
   try{
    const worker=async()=>{try{while(next<ids.length){
     if(controller.signal.aborted)throw Error('Source batch aborted');const index=next++,id=ids[index];
     const response=await Promise.race([Promise.resolve().then(()=>fetcher('https://jelliottdev.github.io/data/pages/'+id+'.json',{redirect:'manual',signal:controller.signal})),aborted]);
     if(!response.ok)throw Error('Source unavailable');const {value:page}=await Promise.race([jsonBody(response,MAX_SOURCE),aborted]);
     const text=row.input_version==='raw'?page.raw:page.reviewed_text;
     if(page.id!==id||typeof text!=='string')throw Error('Source mismatch');total+=new TextEncoder().encode(text).length;if(total>MAX_TOTAL)throw Error('Sources exceed bounds');
     pages[index]={id,text};
    }}catch(error){controller.abort();throw error;}};
    await Promise.all(Array.from({length:Math.min(4,ids.length)},()=>worker()));
   }catch{return reply({error:'The remaining manuscript text could not be loaded within the fixed source bounds.'},422);}
   finally{clearTimeout(timer);}
   const suffix=' · remaining LP2 pages',title=Array.from(parent.title).slice(0,300-Array.from(suffix).length).join('').trimEnd()+suffix;
   let task;
   try{task=await L.prepare({title,pages,alphabet:parent.alphabet,steps:parent.steps,criterion:parent.criterion});}
   catch{return reply({error:'The remaining-page plan exceeds the supported runner bounds. No plan was saved.'},422);}
   const existing=await query(`SELECT links.input_version,t.task_hash,t.task_json FROM local_task_ideas links
    JOIN local_tasks t ON t.id=links.task_id WHERE links.task_id=? AND links.proposal_id=?`,task.taskId,row.proposal_id);
   if(existing){
    if(existing.task_hash!==await digest(L.stable(task))||L.stable(await L.checkIdentity(JSON.parse(existing.task_json)))!==L.stable(task))throw Error('Existing child mismatch');
    if(existing.input_version!==row.input_version)return reply({error:'This computation is already linked to the idea under a different input version. Its association was not changed.'},409);
    return reply({state:'existing-task',...context,taskId:task.taskId,reason:'This experiment already exists. Open it to inspect or run it.'});
   }
   return reply({state:'plan-ready',...context,inputVersion:row.input_version,task,
    notes:historyStopped?['Earlier tasks used different settings or had no association with this idea. Their pages remain available for this test.']:[],
    purpose:'This extends the page scope beyond the original request. The method is unchanged, and earlier results are kept.'});
  }catch{return reply({error:'Scope extension is temporarily unavailable.'},503);}
 };
}
export const handleTaskExtension=createTaskExtensionHandler();
