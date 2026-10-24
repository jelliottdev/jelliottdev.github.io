/* Bounded declarative computation persistence. No user code or scientific verdicts. */
import L from '../../local-experiment.js';
import {validateCard} from './idea-relations.mjs';
const MAX_BODY=2*1024*1024, HEX=/^[a-f0-9]{64}$/, PROPOSAL=/^p_[a-f0-9]{64}$/;
const NOTICE='Verified computation only; this does not establish a correct reading or scientific conclusion.';
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join('');
function exact(value,keys){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(k=>!Object.hasOwn(value,k)))throw Error('Invalid fields');}
async function boundedJSON(message,max=MAX_BODY){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error('JSON required');
 const declared=message.headers.get('content-length');if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>max))throw Error('Body too large');
 const reader=message.body?.getReader();if(!reader)throw Error('Missing body');let size=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('Body too large');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
async function storedTask(row){
 const task=JSON.parse(row.task_json);await L.checkIdentity(task);
 if(task.taskId!==row.id||await digest(L.stable(task))!==row.task_hash)throw Error('Stored task mismatch');
 return task;
}
function projection(row,task,run){
 return {id:row.id,proposalId:row.proposal_id,card:validateCard(row.card_json),title:task.title,plan:task,
  inputVersion:row.input_version,parentTaskId:row.parent_task_id,createdAt:row.created_at,
  state:run?'results-verified':'not-run',...(run?{latestRun:run}:{}),verification:NOTICE};
}
export function createLocalTaskHandler({fetcher=globalThis.fetch,now=()=>new Date()}={}){
 return async function handle(request,env){
  const allowed=env?.SITE_ORIGIN,origin=request.headers.get('origin');
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let validOrigin=false;try{validOrigin=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!validOrigin)return reply({error:'Local experiments are unavailable.'},503);
  if(origin!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;
  const path=new URL(request.url).pathname,match=path.match(/^\/tasks\/([a-f0-9]{64})(\/results)?$/),create=path==='/tasks';
  if(!create&&!match)return reply({error:'Not found.'},404);
  const method=create||match?.[2]?'POST':'GET';
  if(request.method==='OPTIONS'){
   const wanted=request.headers.get('access-control-request-method'),hs=(request.headers.get('access-control-request-headers')||'').split(',').map(s=>s.trim().toLowerCase()).filter(Boolean);
   if(wanted!==method||hs.some(s=>s!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':method+', OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!==method){headers.Allow=method+', OPTIONS';return reply({error:'Method is not allowed.'},405);}
  if(!env.PROPOSALS?.prepare||!env.PROPOSALS?.batch||!(env.TASK_LIMIT||env.PROPOSAL_LIMIT)?.limit)return reply({error:'Local experiments are unavailable.'},503);
  const db=env.PROPOSALS,query=(sql,...args)=>db.prepare(sql).bind(...args),find=id=>query('SELECT * FROM local_tasks WHERE id = ?',id).first();
  const view=async row=>{
   const task=await storedTask(row),latest=await query('SELECT * FROM local_task_results WHERE task_id=? ORDER BY created_at DESC,id DESC LIMIT 1',row.id).first();let run=null;
   if(latest){const result=await L.verify(task,JSON.parse(latest.result_json));if(await digest(L.stable(result))!==latest.id)throw Error('Stored result mismatch');run={id:latest.id,createdAt:latest.created_at,result};}
   return projection(row,task,run);
  };
  try{
   let body;
   if(method==='POST'){
    try{body=await boundedJSON(request);}catch{return reply({error:'The experiment file could not be read.'},400);}
    const limit=await (env.TASK_LIMIT||env.PROPOSAL_LIMIT).limit({key:request.headers.get('CF-Connecting-IP')||'unknown'});
    if(!limit?.success)return reply({error:'Please wait before trying again.'},429);
   }
   const at=now().toISOString(),day=at.slice(0,10);
   if(create){
    let task,taskJson,taskHash,createHash;
    try{
     exact(body,['proposalId','task','inputVersion','parentTaskId']);
     if(!PROPOSAL.test(body.proposalId)||!['raw','reviewed'].includes(body.inputVersion)||(body.parentTaskId!==null&&!HEX.test(body.parentTaskId)))throw Error();
     task=await L.checkIdentity(body.task);taskJson=L.stable(task);taskHash=await digest(taskJson);createHash=await digest(L.stable(body));
    }catch{return reply({error:'The experiment plan is invalid or changed.'},400);}
    let existing=await find(task.taskId);
    if(existing){if(existing.create_hash!==createHash)return reply({error:'This task identity already has a different source or parent.'},409);return reply(await view(existing));}
    const proposal=await query('SELECT card_json FROM proposals WHERE id = ?',body.proposalId).first();
    if(!proposal)return reply({error:'Confirmed idea not found.'},404);
    const cardJson=L.stable(validateCard(proposal.card_json));
    if(body.parentTaskId&&!await find(body.parentTaskId))return reply({error:'Parent task not found.'},404);
    const sourceController=new AbortController(),sourceTimer=setTimeout(()=>sourceController.abort(),20000);
    try{
     let fetched=0,next=0;
     const worker=async()=>{
      try{
       while(next<task.pages.length){
        if(sourceController.signal.aborted)throw Error();
        const page=task.pages[next++];
        const response=await fetcher('https://jelliottdev.github.io/data/pages/'+page.id+'.json',{redirect:'error',signal:sourceController.signal});
        if(!response.ok)throw Error();const source=await boundedJSON(response,512*1024);
        const text=body.inputVersion==='raw'?source.raw:source.reviewed_text;
        if(source.id!==page.id||typeof text!=='string'||text!==page.text)throw Error();
        fetched+=new TextEncoder().encode(text).length;if(fetched>MAX_BODY)throw Error();
       }
      }catch(error){sourceController.abort();throw error;}
     };
     await Promise.all(Array.from({length:Math.min(4,task.pages.length)},()=>worker()));
    }catch{return reply({error:'The selected manuscript text could not be verified.'},422);}
    finally{clearTimeout(sourceTimer);}
    await db.batch([query(`INSERT INTO local_tasks (id,task_hash,create_hash,proposal_id,card_json,task_json,input_version,parent_task_id,created_at,created_day)
     SELECT ?,?,?,?,?,?,?,?,?,? WHERE (SELECT COUNT(*) FROM local_tasks WHERE created_day=?)<50 ON CONFLICT(id) DO NOTHING`,
     task.taskId,taskHash,createHash,body.proposalId,cardJson,taskJson,body.inputVersion,body.parentTaskId,at,day,day)]);
    existing=await find(task.taskId);if(!existing)return reply({error:'The daily experiment limit has been reached.'},429);
    if(existing.create_hash!==createHash)return reply({error:'This task identity already has a different source or parent.'},409);
    return reply(await view(existing));
   }
   const row=await find(match[1]);if(!row)return reply({error:'Experiment not found.'},404);
   const task=await storedTask(row);
   if(method==='GET')return reply(await view(row));
   let result;try{exact(body,['result']);result=await L.verify(task,body.result);}catch{return reply({error:'The results do not match this exact experiment.'},422);}
   const resultJson=L.stable(result),runId=await digest(resultJson);
   let saved=await query('SELECT * FROM local_task_results WHERE id=?',runId).first();
   if(!saved){await db.batch([query(`INSERT INTO local_task_results (id,task_id,result_json,created_at,created_day)
    SELECT ?,?,?,?,? WHERE (SELECT COUNT(*) FROM local_task_results WHERE created_day=?)<50 ON CONFLICT(id) DO NOTHING`,runId,row.id,resultJson,at,day,day)]);saved=await query('SELECT * FROM local_task_results WHERE id=?',runId).first();}
   if(!saved)return reply({error:'The daily result limit has been reached.'},429);
   const savedResult=await L.verify(task,JSON.parse(saved.result_json));
   if(saved.task_id!==row.id||await digest(L.stable(savedResult))!==saved.id)throw Error('Stored result mismatch');
   return reply({taskId:row.id,state:'results-verified',latestRun:{id:saved.id,createdAt:saved.created_at,result:savedResult},verification:NOTICE});
  }catch{return reply({error:'Local experiments are temporarily unavailable.'},503);}
 };
}
