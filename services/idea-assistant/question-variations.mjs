/* Read-only retained variation origins. No calculations, source fetching or admission. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import C from '../../claim-specification.js';
import Links from '../../question-variation-links.js';
import {validateCard} from './idea-relations.mjs';
export const PAGE_SIZE=10;
const ID=/^p_[a-f0-9]{64}$/,HEX=/^[a-f0-9]{64}$/,MAX_ORIGIN=65536;
const ensure=(value,message)=>{if(!value)throw Error(message);},exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const iso=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
const sha=async(value,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(n=>n.toString(16).padStart(2,'0')).join('');
function encodeCursor(row){return btoa(JSON.stringify({createdAt:row.created_at,id:row.id})).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function decodeCursor(value){
 ensure(typeof value==='string'&&value.length>0&&value.length<=240&&/^[-_a-zA-Z0-9]+$/.test(value),'Invalid cursor');
 const decoded=JSON.parse(atob(value.replace(/-/g,'+').replace(/_/g,'/')));ensure(exact(decoded,['createdAt','id'])&&iso(decoded.createdAt)&&typeof decoded.id==='string'&&HEX.test(decoded.id)&&encodeCursor({created_at:decoded.createdAt,id:decoded.id})===value,'Invalid cursor');return decoded;
}
async function card(row,crypto){
 ensure(typeof row.card_json==='string'&&typeof row.card_hash==='string'&&HEX.test(row.card_hash)&&ID.test(row.id),'Invalid public card');
 const value=validateCard(row.card_json),serialized=C.serialize(value);ensure(serialized===row.card_json&&await sha(serialized,crypto)===row.card_hash&&row.id==='p_'+row.card_hash,'Public card changed');return value;
}
export function createQuestionVariationsHandler({crypto=globalThis.crypto,timeoutMs=15000}={}){
 ensure(Number.isSafeInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=45000,'Invalid read deadline');
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(value,status=200)=>new Response(JSON.stringify(value),{status,headers}),unavailable=()=>reply({error:'Related variations are temporarily unavailable.'},503),allowed=env?.SITE_ORIGIN;
  try{ensure(typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol),'Origin');}catch{return unavailable();}
  if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url),match=url.pathname.match(/^\/ideas\/(p_[a-f0-9]{64})\/variations$/);if(!match)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){const wanted=request.headers.get('access-control-request-method'),keys=(request.headers.get('access-control-request-headers')||'').split(',').map(k=>k.trim().toLowerCase()).filter(Boolean);return wanted==='GET'&&keys.every(k=>k==='content-type')?new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}}):reply({error:'Request is not allowed.'},403);}
  if(request.method!=='GET'){headers.Allow='GET, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  let direction,cursor=null;try{ensure([...url.searchParams.keys()].every(k=>['direction','before'].includes(k))&&url.searchParams.getAll('direction').length===1&&url.searchParams.getAll('before').length<=1,'Query');direction=url.searchParams.get('direction');ensure(['parents','children'].includes(direction),'Direction');if(url.searchParams.has('before'))cursor=decodeCursor(url.searchParams.get('before'));}catch{return reply({error:'Choose a valid variation direction and page cursor.'},400);}
  const db=env?.PROPOSALS,rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;if(!db?.prepare||typeof rate?.limit!=='function')return unavailable();
  const controller=new AbortController(),stop=()=>controller.abort();request.signal.addEventListener('abort',stop,{once:true});if(request.signal.aborted)stop();let rejectAbort;const aborted=new Promise((_,reject)=>{rejectAbort=()=>reject(Error('Cancelled'));controller.signal.addEventListener('abort',rejectAbort,{once:true});}),timer=setTimeout(stop,timeoutMs),live=()=>ensure(!controller.signal.aborted,'Cancelled'),query=(sql,...args)=>db.prepare(sql).bind(...args);
  const work=async()=>{
   live();if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);live();
   const ideaId=match[1],current=await query('SELECT p.id,p.card_hash,p.card_json FROM proposals p JOIN research_ideas i ON i.proposal_id=p.id WHERE p.id=?',ideaId).first();live();if(!current)return reply({error:'Idea not found.'},404);await card(current,crypto);live();
   const scope=direction==='parents'?'child_proposal_id':'parent_proposal_id',after=cursor?' AND (d.created_at<? OR (d.created_at=? AND d.id<?))':'',args=cursor?[ideaId,cursor.createdAt,cursor.createdAt,cursor.id]:[ideaId];
   const found=await query(`SELECT d.id,d.parent_proposal_id,d.child_proposal_id,d.origin_json,d.created_at,d.created_day,
    p.card_hash AS parent_hash,p.card_json AS parent_json,c.card_hash AS child_hash,c.card_json AS child_json
    FROM question_derivations d JOIN research_ideas pi ON pi.proposal_id=d.parent_proposal_id
    JOIN proposals p ON p.id=pi.proposal_id JOIN research_ideas ci ON ci.proposal_id=d.child_proposal_id
    JOIN proposals c ON c.id=ci.proposal_id WHERE d.${scope}=?${after}
    ORDER BY d.created_at DESC,d.id DESC LIMIT 11`,...args).all();live();
   ensure(Array.isArray(found?.results)&&found.results.length<=PAGE_SIZE+1,'Invalid variation rows');const rows=found.results,entries=[];let previous=cursor;
   for(const row of rows){
    ensure(iso(row.created_at)&&row.created_day===row.created_at.slice(0,10)&&typeof row.id==='string'&&HEX.test(row.id)&&ID.test(row.parent_proposal_id)&&ID.test(row.child_proposal_id)&&(direction==='parents'?row.child_proposal_id:row.parent_proposal_id)===ideaId,'Invalid variation identity');
    ensure(!previous||row.created_at<previous.createdAt||row.created_at===previous.createdAt&&row.id<previous.id,'Variation order changed');previous={createdAt:row.created_at,id:row.id};
    ensure(typeof row.origin_json==='string'&&new TextEncoder().encode(row.origin_json).length<=MAX_ORIGIN,'Invalid retained origin');const origin=J.capture(JSON.parse(row.origin_json),{maxBytes:MAX_ORIGIN,maxDepth:24,maxNodes:10000});
    ensure(E.stable(origin)===row.origin_json&&await sha(row.origin_json,crypto)===row.id&&origin.parentProposalId===row.parent_proposal_id&&origin.childProposalId===row.child_proposal_id,'Retained variation changed');live();
    const parentCard=await card({id:row.parent_proposal_id,card_hash:row.parent_hash,card_json:row.parent_json},crypto),childCard=await card({id:row.child_proposal_id,card_hash:row.child_hash,card_json:row.child_json},crypto),entry={id:row.id,createdAt:row.created_at,origin,parentCard,childCard};live();
    await Links.validate(entry,{ideaId,direction,crypto});live();entries.push(entry);
   }
   live();return reply({schema:'liberpedia-question-variations-v1',ideaId,direction,entries:entries.slice(0,PAGE_SIZE),nextCursor:rows.length>PAGE_SIZE?encodeCursor(rows[PAGE_SIZE-1]):null});
  };
  try{return await Promise.race([work(),aborted]);}catch{return unavailable();}finally{clearTimeout(timer);request.signal.removeEventListener('abort',stop);controller.signal.removeEventListener('abort',rejectAbort);}
 };
}
