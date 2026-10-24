/* Explicit normalized-card publication. No original wording, notes or inference. */
import C from '../../claim-specification.js';
import {validateCard} from './idea-relations.mjs';

const ID=/^p_[a-f0-9]{64}$/,HEX=/^[a-f0-9]{64}$/,MAX_BODY=1024,PAGE_SIZE=50;
const FIND=`SELECT i.proposal_id,i.created_at,p.card_json,p.card_hash
 FROM research_ideas i JOIN proposals p ON p.id=i.proposal_id WHERE i.proposal_id=?`;
const INSERT=`INSERT INTO research_ideas (proposal_id,created_at,created_day)
 SELECT ?,?,? WHERE EXISTS (SELECT 1 FROM proposals WHERE id=?)
 AND (SELECT COUNT(*) FROM research_ideas WHERE created_day=?)<50
 ON CONFLICT(proposal_id) DO NOTHING`;
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
function exact(value,keys){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(k=>!Object.hasOwn(value,k)))throw Error('Invalid fields');}
function iso(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value).toISOString()===value;}
function encodeCursor(row){return btoa(JSON.stringify({createdAt:row.created_at,id:row.id})).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function decodeCursor(text){
 if(typeof text!=='string'||text.length>240||!/^[-_a-zA-Z0-9]+$/.test(text))throw Error('Invalid cursor');
 const row=JSON.parse(atob(text.replace(/-/g,'+').replace(/_/g,'/')));exact(row,['createdAt','id']);
 if(!iso(row.createdAt)||typeof row.id!=='string'||!HEX.test(row.id)||encodeCursor({created_at:row.createdAt,id:row.id})!==text)throw Error('Invalid cursor');
 return row;
}
async function bodyJSON(request){
 if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''))throw Error('JSON required');
 const length=request.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>MAX_BODY))throw Error('Body too large');
 const reader=request.body?.getReader();if(!reader)throw Error('Body required');const chunks=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX_BODY){await reader.cancel();throw Error('Body too large');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes),body=JSON.parse(text);exact(body,['proposalId']);
 if(typeof body.proposalId!=='string'||!ID.test(body.proposalId))throw Error('Invalid proposal');
 // This schema contains exactly two JSON strings (one key and one value).
 // Count lexical strings after parsing to reject duplicate, even escaped, keys.
 if((text.match(/"(?:[^"\\]|\\.)*"/g)||[]).length!==2)throw Error('Duplicate JSON field');return body;
}
async function publicCard(row){
 const card=validateCard(row.card_json),hash=await digest(C.serialize(card));
 if(row.card_hash!==hash||row.proposal_id!=='p_'+hash)throw Error('Stored card identity mismatch');
 return card;
}
export function createCommunityIdeaHandler({now=()=>new Date()}={}){
 return async function handle(request,env){
  const allowed=env?.SITE_ORIGIN,origin=request.headers.get('origin'),headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let valid=false;try{valid=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['https:','http:'].includes(new URL(allowed).protocol);}catch{}
  if(!valid)return reply({error:'Community ideas are unavailable.'},503);
  if(origin!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url),create=url.pathname==='/ideas',match=url.pathname.match(/^\/ideas\/(p_[a-f0-9]{64})$/);
  if(!create&&!match)return reply({error:'Not found.'},404);
  const method=create?'POST':'GET';
  if(request.method==='OPTIONS'){
   const wanted=request.headers.get('access-control-request-method'),hs=(request.headers.get('access-control-request-headers')||'').split(',').map(s=>s.trim().toLowerCase()).filter(Boolean);
   if(wanted!==method||hs.some(s=>s!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':method+', OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!==method){headers.Allow=method+', OPTIONS';return reply({error:'Method is not allowed.'},405);}
  let cursor=null;
  try{
   if([...url.searchParams.keys()].some(key=>key!=='before')||url.searchParams.getAll('before').length>1||(create&&url.search))throw Error();
   if(url.searchParams.has('before'))cursor=decodeCursor(url.searchParams.get('before'));
  }catch{return reply({error:'Invalid page cursor.'},400);}
  const db=env?.PROPOSALS,rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;
  if(!db?.prepare||(create&&(!db.batch||!rate?.limit)))return reply({error:'Community ideas are unavailable.'},503);
  const query=(sql,...values)=>db.prepare(sql).bind(...values),find=id=>query(FIND,id).first();
  const view=async row=>{
   const card=await publicCard(row);
   if(!iso(row.created_at))throw Error('Stored entry timestamp mismatch');
   const after=cursor?' AND (a.created_at<? OR (a.created_at=? AND t.id<?))':'';
   const args=cursor?[row.proposal_id,cursor.createdAt,cursor.createdAt,cursor.id]:[row.proposal_id];
   // Plans were validated on creation and are immutable. Project only bounded
   // summary fields; the task endpoint rechecks full identity when opened.
   const loaded=await query(`SELECT t.id,json_extract(t.task_json,'$.title') AS title,
    json_extract(t.task_json,'$.taskId') AS embedded_id,a.created_at,
    EXISTS(SELECT 1 FROM local_task_results r WHERE r.task_id=t.id) AS has_results
    FROM local_task_ideas a JOIN local_tasks t ON t.id=a.task_id
    WHERE a.proposal_id=?${after} ORDER BY a.created_at DESC,t.id DESC LIMIT 51`,...args).all();
   const rows=loaded.results;if(!Array.isArray(rows))throw Error('Invalid task response');
   const selected=rows.slice(0,PAGE_SIZE),tasks=[];
   for(const entry of selected){
    if(!iso(entry.created_at)||typeof entry.id!=='string'||!HEX.test(entry.id)||entry.embedded_id!==entry.id||typeof entry.title!=='string'||!entry.title.trim()||Array.from(entry.title).length>300)throw Error('Stored task summary mismatch');
    tasks.push({id:entry.id,title:entry.title,state:entry.has_results?'results-verified':'not-run'});
   }
   return {id:row.proposal_id,card,createdAt:row.created_at,tasks,tasksTruncated:rows.length>PAGE_SIZE,
    nextCursor:rows.length>PAGE_SIZE?encodeCursor(selected.at(-1)):null};
  };
  try{
   if(!create){const row=await find(match[1]);return row?reply(await view(row)):reply({error:'Idea not found.'},404);}
   let body;try{body=await bodyJSON(request);}catch{return reply({error:'The confirmed idea identifier could not be read.'},400);}
   if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   let row=await find(body.proposalId);if(row)return reply(await view(row));
   const proposal=await query('SELECT id AS proposal_id,card_hash,card_json FROM proposals WHERE id=?',body.proposalId).first();
   if(!proposal)return reply({error:'Confirmed idea not found.'},404);
   await publicCard(proposal);
   const at=now().toISOString();if(!iso(at))throw Error('Invalid publication timestamp');const day=at.slice(0,10);
   const batch=await db.batch([query(INSERT,body.proposalId,at,day,body.proposalId,day)]);
   if(batch.some(item=>item?.success===false))throw Error('Persistence failed');
   row=await find(body.proposalId);
   return row?reply(await view(row)):reply({error:'The daily publication limit has been reached.'},429);
  }catch{return reply({error:'Community ideas are temporarily unavailable.'},503);}
 };
}
export const handleCommunityIdea=createCommunityIdeaHandler();
