/* Confirmed idea persistence only: no inference, network fetch or IP storage. */
import ClaimShare from '../../claim-share.js';
import ClaimSpecification from '../../claim-specification.js';
import MethodDesign from '../../method-design.js';

const MAX_BODY=32000,DAILY_CAP=50;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const FIND='SELECT request_id, proposal_id, request_hash, received_at FROM proposal_submissions WHERE request_id = ?';
const INSERT_CARD=`INSERT INTO proposals (id, card_hash, card_json, fragment, created_at)
 SELECT ?, ?, ?, ?, ?
 WHERE NOT EXISTS (SELECT 1 FROM proposal_submissions WHERE request_id = ?)
 AND (SELECT COUNT(*) FROM proposal_submissions WHERE received_day = ?) < ?
 ON CONFLICT(card_hash) DO NOTHING`;
const INSERT_SUBMISSION=`INSERT INTO proposal_submissions
 (request_id, proposal_id, request_hash, note, source_url, received_at, received_day, original_idea)
 SELECT ?, ?, ?, ?, ?, ?, ?, ?
 WHERE EXISTS (SELECT 1 FROM proposals WHERE id = ?)
 AND (SELECT COUNT(*) FROM proposal_submissions WHERE received_day = ?) < ?
 ON CONFLICT(request_id) DO NOTHING`;

async function bodyJSON(request){
 if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''))throw Error('Invalid request');
 if(Number(request.headers.get('content-length')||0)>MAX_BODY)throw Error('Invalid request');
 const reader=request.body?.getReader();if(!reader)throw Error('Invalid request');
 const parts=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX_BODY){await reader.cancel();throw Error('Invalid request');}parts.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
function sourceURL(value){
 if(value==='')return '';
 if(typeof value!=='string'||value.length>1500||/[\u0000-\u0020\u007f]/.test(value))throw Error('Invalid source');
 const url=new URL(value),host=url.hostname.toLowerCase();
 if(!['http:','https:'].includes(url.protocol)||url.username||url.password||!host.includes('.')||host.endsWith('.')||
  /\.(?:local|localhost|internal|test|invalid|example)$/.test(host)||host.includes(':'))throw Error('Invalid source');
 if(/^\d+(?:\.\d+){3}$/.test(host)){
  const [a,b,c]=host.split('.').map(Number);
  if(a===0||a===10||a===127||a>=224||(a===169&&b===254)||(a===172&&b>=16&&b<=31)||(a===192&&b===168)||(a===100&&b>=64&&b<=127)||(a===198&&(b===18||b===19))||
   (a===192&&b===0&&(c===0||c===2))||(a===198&&b===51&&c===100)||(a===203&&b===0&&c===113))throw Error('Invalid source');
 }
 return value;
}
async function digest(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
export async function canonicalProposal(data){
 if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).some(k=>!['requestId','fragment','note','sourceUrl','originalIdea'].includes(k))||!UUID.test(data.requestId||'')||typeof data.fragment!=='string')throw Error('Invalid request');
 const requestId=data.requestId.toLowerCase(),note=Object.hasOwn(data,'note')?data.note:'',sourceUrl=sourceURL(Object.hasOwn(data,'sourceUrl')?data.sourceUrl:'');
 if(typeof note!=='string'||note.length>1200)throw Error('Invalid note');
 const originalIdea=Object.hasOwn(data,'originalIdea')?data.originalIdea:'';
 if(typeof originalIdea!=='string'||originalIdea.length>8000)throw Error('Invalid original idea');
 const imported=ClaimShare.decode(data.fragment);
 if(imported.draft.method.status!=='specified'||!imported.draft.method.value.operations.length)throw Error('Method required');
 // Sorting object keys makes identity independent of JSON member order. Step
 // order, exact wording, parameters, scope holes and explicit states remain.
 const draft=JSON.parse(ClaimSpecification.serialize(imported.draft));
 const confirmed=ClaimSpecification.confirm(draft,{id:'proposal-validation',at:'2000-01-01T00:00:00.000Z'});
 const fragment=ClaimShare.encode(confirmed),cardJson=ClaimSpecification.serialize(ClaimShare.cardData(confirmed));
 // Recognized structured declarations must retain every copied scope and check
 // field coherently. Ordinary cards and legacy prose remain ordinary.
 MethodDesign.readCard(JSON.parse(cardJson));
 const cardHash=await digest(cardJson),id='p_'+cardHash;
 const requestHash=await digest(JSON.stringify({requestId,cardHash,note,sourceUrl,originalIdea}));
 return {requestId,note,sourceUrl,originalIdea,fragment,cardJson,cardHash,id,requestHash};
}
export function createProposalHandler({now=()=>new Date()}={}){
 return async function handleProposal(request,env){
  const origin=request.headers.get('origin'),allowed=env?.SITE_ORIGIN;
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  let configuredOrigin=false;try{configuredOrigin=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  if(!configuredOrigin)return reply({error:'Proposal intake is unavailable.'},503);
  if(origin!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;
  if(new URL(request.url).pathname!=='/proposals')return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const wanted=request.headers.get('access-control-request-method');
   const requestedHeaders=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(wanted!=='POST'||requestedHeaders.some(h=>h!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!=='POST'){headers.Allow='POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  if(!env.PROPOSALS?.prepare||!env.PROPOSALS?.batch||!env.PROPOSAL_LIMIT?.limit)return reply({error:'Proposal intake is unavailable.'},503);
  let p;try{p=await canonicalProposal(await bodyJSON(request));}catch{return reply({error:'The idea or source link could not be read. Review the card and link before retrying.'},400);}
  const db=env.PROPOSALS;
  const result=(row,status)=>reply({id:row.proposal_id,status,receivedAt:row.received_at});
  const retry=row=>row.request_hash===p.requestHash?result(row,'already_received'):reply({error:'Request identifier was already used.'},409);
  try{
   const limited=await env.PROPOSAL_LIMIT.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'});
   if(!limited?.success)return reply({error:'Submission limit reached. Please try later.'},429);
   const existing=await db.prepare(FIND).bind(p.requestId).first();if(existing)return retry(existing);
   const receivedAt=now().toISOString(),day=receivedAt.slice(0,10);
   // D1 batch is one transaction. Both cap-guarded INSERTs run atomically; a
   // concurrent request cannot interleave and exceed the durable daily cap.
   const batch=await db.batch([
    db.prepare(INSERT_CARD).bind(p.id,p.cardHash,p.cardJson,p.fragment,receivedAt,p.requestId,day,DAILY_CAP),
    db.prepare(INSERT_SUBMISSION).bind(p.requestId,p.id,p.requestHash,p.note,p.sourceUrl,receivedAt,day,p.originalIdea,p.id,day,DAILY_CAP)
   ]);
   if(batch.some(item=>item?.success===false))throw Error('Persistence failed');
   const saved=await db.prepare(FIND).bind(p.requestId).first();
   if(!saved)return reply({error:'Submission limit reached. Please try later.'},429);
   if(saved.request_hash!==p.requestHash)return retry(saved);
   return result(saved,Number(batch[1]?.meta?.changes)>0?'received':'already_received');
  }catch{return reply({error:'Proposal intake is temporarily unavailable.'},503);}
 };
}
export const handleProposal=createProposalHandler();
