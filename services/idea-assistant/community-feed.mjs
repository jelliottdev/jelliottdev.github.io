/* Public navigation metadata only; never selects private contributions or runs models. */
import C from '../../claim-specification.js';
import {validateCard} from './idea-relations.mjs';

const IDEA=/^p_[a-f0-9]{64}$/,TASK=/^[a-f0-9]{64}$/,PAGE_SIZE=50,TASKS_PER_IDEA=10;
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
function iso(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value).toISOString()===value;}
function encodeCursor(row){return btoa(JSON.stringify({createdAt:row.created_at,id:row.proposal_id})).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function decodeCursor(text){
 if(typeof text!=='string'||text.length>240||!/^[-_a-zA-Z0-9]+$/.test(text))throw Error('Invalid cursor');
 const row=JSON.parse(atob(text.replace(/-/g,'+').replace(/_/g,'/')));
 if(!row||typeof row!=='object'||Array.isArray(row)||Object.keys(row).length!==2||!Object.hasOwn(row,'createdAt')||!Object.hasOwn(row,'id')||!iso(row.createdAt)||typeof row.id!=='string'||!IDEA.test(row.id)||encodeCursor({created_at:row.createdAt,proposal_id:row.id})!==text)throw Error('Invalid cursor');
 return row;
}
export function createCommunityFeedHandler(){
 return async function handle(request,env){
  const allowed=env?.SITE_ORIGIN,origin=request.headers.get('origin');
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let valid=false;try{valid=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!valid)return reply({error:'Community research is unavailable.'},503);
  if(origin!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url);
  if(url.pathname!=='/community-research')return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const hs=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='GET'||hs.some(h=>h!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!=='GET'){headers.Allow='GET, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  let cursor=null;
  try{
   if([...url.searchParams.keys()].some(k=>k!=='before')||url.searchParams.getAll('before').length>1)throw Error('Invalid cursor');
   if(url.searchParams.has('before'))cursor=decodeCursor(url.searchParams.get('before'));
  }catch{return reply({error:'Invalid page cursor.'},400);}
  if(!env?.PROPOSALS?.prepare)return reply({error:'Community research is unavailable.'},503);
  try{
   const query=(sql,...args)=>env.PROPOSALS.prepare(sql).bind(...args).all();
   const where=cursor?' WHERE (i.created_at<? OR (i.created_at=? AND i.proposal_id<?))':'';
   const args=cursor?[cursor.createdAt,cursor.createdAt,cursor.id]:[];
   const found=await query(`SELECT i.proposal_id,i.created_at,p.card_json,p.card_hash
    FROM research_ideas i JOIN proposals p ON p.id=i.proposal_id${where}
    ORDER BY i.created_at DESC,i.proposal_id DESC LIMIT 51`,...args);
   if(!Array.isArray(found.results)||found.results.length>PAGE_SIZE+1)throw Error('Invalid database response');
   const rows=found.results.slice(0,PAGE_SIZE),entries=[],byId=new Map();
   for(const row of rows){
    if(typeof row.proposal_id!=='string'||!IDEA.test(row.proposal_id)||!iso(row.created_at)||byId.has(row.proposal_id))throw Error('Invalid idea metadata');
    const card=validateCard(row.card_json),hash=await digest(C.serialize(card));
    if(row.card_hash!==hash||row.proposal_id!=='p_'+hash)throw Error('Stored card identity mismatch');
    const entry={id:row.proposal_id,card,createdAt:row.created_at,tasks:[],taskCount:0,verifiedTaskCount:0};entries.push(entry);byId.set(entry.id,entry);
   }
   if(entries.length){
    // Rank/count small identity columns before extracting JSON. Only the ten
    // selected summaries per idea cross the D1 boundary, never complete plans.
    const taskRows=await query(`WITH ranked AS (
     SELECT proposal_id,task_id AS id,created_at,
      ROW_NUMBER() OVER (PARTITION BY proposal_id ORDER BY created_at DESC,task_id DESC) AS position,
      COUNT(*) OVER (PARTITION BY proposal_id) AS task_count,
      SUM(EXISTS(SELECT 1 FROM local_task_results v WHERE v.task_id=local_task_ideas.task_id))
       OVER (PARTITION BY proposal_id) AS verified_task_count
     FROM local_task_ideas WHERE proposal_id IN (${entries.map(()=>'?').join(',')})
    ) SELECT r.proposal_id,r.id,r.created_at,r.task_count,r.verified_task_count,
     json_extract(t.task_json,'$.title') AS title,
     json_extract(t.task_json,'$.taskId') AS embedded_id,
     EXISTS(SELECT 1 FROM local_task_results a WHERE a.task_id=r.id) AS has_results
    FROM ranked r JOIN local_tasks t ON t.id=r.id WHERE r.position<=10
    ORDER BY r.proposal_id,r.created_at DESC,r.id DESC`,...entries.map(e=>e.id));
    if(!Array.isArray(taskRows.results)||taskRows.results.length>PAGE_SIZE*TASKS_PER_IDEA)throw Error('Invalid task metadata response');
    const seen=new Set();
    for(const row of taskRows.results){
     const entry=byId.get(row.proposal_id),key=row.proposal_id+':'+row.id;
     if(!entry||typeof row.id!=='string'||!TASK.test(row.id)||row.embedded_id!==row.id||!iso(row.created_at)||typeof row.title!=='string'||!row.title.trim()||Array.from(row.title).length>300||!Number.isSafeInteger(row.task_count)||row.task_count<1||!Number.isSafeInteger(row.verified_task_count)||row.verified_task_count<0||row.verified_task_count>row.task_count||![0,1].includes(row.has_results)||entry.tasks.length>=TASKS_PER_IDEA||seen.has(key)||(entry.taskCount&&(entry.taskCount!==row.task_count||entry.verifiedTaskCount!==row.verified_task_count)))throw Error('Invalid task summary');
     entry.taskCount=row.task_count;entry.verifiedTaskCount=row.verified_task_count;entry.tasks.push({id:row.id,title:row.title,state:row.has_results?'results-verified':'not-run'});seen.add(key);
    }
    for(const entry of entries){
     const visibleVerified=entry.tasks.filter(t=>t.state==='results-verified').length;
     if(entry.tasks.length!==Math.min(TASKS_PER_IDEA,entry.taskCount)||visibleVerified>entry.verifiedTaskCount||entry.verifiedTaskCount-visibleVerified>entry.taskCount-entry.tasks.length)throw Error('Incomplete task summaries');
    }
   }
   return reply({schema:'liberpedia-community-research-v1',entries,
    nextCursor:found.results.length>PAGE_SIZE?encodeCursor(rows.at(-1)):null});
  }catch{return reply({error:'Community research is temporarily unavailable.'},503);}
 };
}
export const handleCommunityFeed=createCommunityFeedHandler();
