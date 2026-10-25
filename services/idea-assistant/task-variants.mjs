/* Compare one fixed measurement boundary rule. No AI, source fetch or target execution. */
import L from '../../local-experiment.js';
import C from '../../claim-specification.js';
import Variants from '../../task-variants.js';
import Controls from '../../local-plan-controls.js';
import {validateCard} from './idea-relations.mjs';
import {issue as issuePreparation} from './prepared-plans.mjs';
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
async function jsonBody(message,max){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error('JSON required');
 const length=message.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>max))throw Error('Body too large');
 const reader=message.body?.getReader();if(!reader)throw Error('Body required');const parts=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('Body too large');}parts.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);return {value:JSON.parse(text),text};
}
export function createTaskVariantHandler({now=()=>new Date()}={}){
 return async function handle(request,env){
  const allowed=env?.SITE_ORIGIN,headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let valid=false;try{valid=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!valid)return reply({error:'Word-boundary comparison is unavailable.'},503);
  if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url),match=url.pathname.match(/^\/tasks\/([a-f0-9]{64})\/variants$/);
  if(!match||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const hs=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='POST'||hs.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!=='POST'){headers.Allow='POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;
  if(!env?.PROPOSALS?.prepare||!rate?.limit)return reply({error:'Word-boundary comparison is unavailable.'},503);
  try{
   const body=await jsonBody(request,1024),v=body.value;
   if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).length!==1||v.variant!=='word-boundaries'||(body.text.match(/"(?:[^"\\]|\\.)*"/g)||[]).length!==2)throw Error();
  }catch{return reply({error:'Choose the supported word-boundary comparison.'},400);}
  try{
   if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   const query=(sql,...args)=>env.PROPOSALS.prepare(sql).bind(...args).first();
   const row=await query(`SELECT t.id,t.task_json,t.task_hash,links.proposal_id,links.input_version,p.card_json,p.card_hash
    FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id
    JOIN research_ideas public ON public.proposal_id=links.proposal_id JOIN proposals p ON p.id=links.proposal_id
    WHERE t.id=? ORDER BY CASE WHEN links.proposal_id=t.proposal_id THEN 0 ELSE 1 END,links.created_at,links.proposal_id LIMIT 1`,match[1]);
   if(!row)return reply({error:'Registered experiment not found.'},404);
   const parent=JSON.parse(row.task_json);await L.checkIdentity(parent);
   if(parent.taskId!==row.id||await digest(L.stable(parent))!==row.task_hash||!['raw','reviewed'].includes(row.input_version))throw Error('Stored task mismatch');
   const card=validateCard(row.card_json),cardHash=await digest(C.serialize(card));
   if(row.card_hash!==cardHash||row.proposal_id!=='p_'+cardHash)throw Error('Stored public card mismatch');
   const variant=Variants.inspect(parent);
   if(!variant)return reply({error:'This experiment does not support the fixed word-boundary comparison.'},422);
   const context={proposalId:row.proposal_id,parentTaskId:parent.taskId,variant:variant.kind,from:variant.from,to:variant.to};
   const saved=await query('SELECT id,result_json FROM local_task_results WHERE task_id=? ORDER BY created_at DESC,id DESC LIMIT 1',parent.taskId);
   if(!saved)return reply({state:'runs-pending',...context,pendingTasks:[{id:parent.taskId,pages:parent.pages.map(p=>p.id)}],reason:'Save the original experiment’s results before comparing word boundaries.'});
   // This table accepts only replay-verified results. Check its immutable byte
   // receipt here; reproducing the target belongs to result admission, not planning.
   const result=JSON.parse(saved.result_json);
   if(result.taskId!==parent.taskId||result.schema!==L.RESULT||result.engine!==L.ENGINE||result.runnerVersion!=='1'||L.stable(result)!==saved.result_json||await digest(saved.result_json)!==saved.id)throw Error('Stored result receipt mismatch');
   const task=await Variants.prepare(parent,crypto);await Variants.validate(parent,task,crypto);
   const existing=await query(`SELECT links.input_version,t.task_hash,t.task_json FROM local_task_ideas links JOIN local_tasks t ON t.id=links.task_id WHERE links.task_id=? AND links.proposal_id=?`,task.taskId,row.proposal_id);
   if(existing){
    if(existing.task_hash!==await digest(L.stable(task))||L.stable(await L.checkIdentity(JSON.parse(existing.task_json)))!==L.stable(task))throw Error('Existing comparison mismatch');
    if(existing.input_version!==row.input_version)return reply({error:'This comparison already uses a different input version. Its association was not changed.'},409);
    return reply({state:'existing-task',...context,taskId:task.taskId,reason:'This comparison already exists. Open it to inspect or run it.'});
   }
   const controls=await Controls.prepare(task,crypto);await Controls.validate(controls,task,crypto);
   const preparation=await issuePreparation({db:env.PROPOSALS,proposalId:row.proposal_id,card,task,inputVersion:row.input_version,parentTaskId:parent.taskId,controls,authority:'word-boundaries',basis:{kind:'word-boundaries',parentTaskId:parent.taskId,parentTaskHash:row.task_hash,from:variant.from,to:variant.to},createdAt:now().toISOString()});
   return reply({state:'plan-ready',...context,inputVersion:row.input_version,task,controls,preparation,notes:[],purpose:'This compares the two supported word-boundary rules on the same saved text. Other settings are unchanged.'});
  }catch{return reply({error:'Word-boundary comparison is temporarily unavailable.'},503);}
 };
}
export const handleTaskVariant=createTaskVariantHandler();
