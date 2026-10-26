/* Explicit public question lineage only. This handler never creates or runs a task. */
import E from '../../local-experiment.js';
import C from '../../claim-specification.js';
import {validateCard} from './idea-relations.mjs';
import {resolveParameterQuestion} from './parameter-question-source.mjs';
const ID=/^p_[a-f0-9]{64}$/,HEX=/^[a-f0-9]{64}$/,MAX=65536;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const sha=async(v,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
async function bodyJSON(request){
 if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''))throw Error();
 const length=request.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>MAX))throw Error();
 const reader=request.body?.getReader();if(!reader)throw Error();const chunks=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX){await reader.cancel();throw Error();}chunks.push(value);}
 const bytes=new Uint8Array(size);let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
export function createParameterQuestionHandler({now=()=>new Date(),crypto=globalThis.crypto,fetcher=globalThis.fetch,registry,history,programIndex,dailyCap=50}={}){
 if(!Number.isSafeInteger(dailyCap)||dailyCap<1||dailyCap>50)throw Error('Invalid lineage limit');
 return async function handle(request,env){
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(value,status=200)=>new Response(JSON.stringify(value),{status,headers}),allowed=env?.SITE_ORIGIN;
  try{if(typeof allowed!=='string'||new URL(allowed).origin!==allowed||!['http:','https:'].includes(new URL(allowed).protocol))throw Error();}catch{return reply({error:'Question variations are unavailable.'},503);}
  if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url),action=url.pathname.match(/^\/parameter-questions\/(preview|confirm)$/)?.[1],read=url.pathname.match(/^\/parameter-questions\/(p_[a-f0-9]{64})$/)?.[1];
  if((!action&&!read)||url.search)return reply({error:'Not found.'},404);const method=read?'GET':'POST';
  if(request.method==='OPTIONS'){const hs=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);return request.headers.get('access-control-request-method')===method&&hs.every(v=>v==='content-type')?new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':method+', OPTIONS','Access-Control-Allow-Headers':'Content-Type'}}):reply({error:'Request is not allowed.'},403);}
  if(request.method!==method){headers.Allow=method+', OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const db=env?.PROPOSALS,rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;if(!db?.prepare||(!read&&(!db.batch||!rate?.limit)))return reply({error:'Question variations are unavailable.'},503);
  const query=(sql,...args)=>db.prepare(sql).bind(...args),live=()=>{if(request.signal.aborted)throw Error('Cancelled');};
  try{
   if(read){
    const publicRow=await query('SELECT proposal_id FROM research_ideas WHERE proposal_id=?',read).first();if(!publicRow)return reply({error:'Public question not found.'},404);
    const load=async column=>{const rows=(await query(`SELECT d.* FROM question_derivations d JOIN research_ideas parent ON parent.proposal_id=d.parent_proposal_id JOIN research_ideas child ON child.proposal_id=d.child_proposal_id WHERE d.${column}=? ORDER BY d.created_at DESC,d.id DESC LIMIT 51`,read).all()).results;if(!Array.isArray(rows))throw Error();const values=[];for(const row of rows.slice(0,50)){if(!HEX.test(row.id)||typeof row.origin_json!=='string'||row.origin_json.length>MAX||await sha(row.origin_json,crypto)!==row.id)throw Error();const origin=JSON.parse(row.origin_json);if(!['liberpedia-question-derivation-v1','liberpedia-question-derivation-v2','liberpedia-question-derivation-v3','liberpedia-question-derivation-v4'].includes(origin.schema)||origin.parentProposalId!==row.parent_proposal_id||origin.childProposalId!==row.child_proposal_id||!Number.isFinite(Date.parse(row.created_at)))throw Error();values.push({id:row.id,...origin,createdAt:row.created_at});}return {items:values,truncated:rows.length>50};};
    return reply({proposalId:read,parents:await load('child_proposal_id'),children:await load('parent_proposal_id')});
   }
   let body;try{body=await bodyJSON(request);const settings=Object.hasOwn(body||{},'parentSettings');if(!exact(body,['source','selection',...(settings?['parentSettings']:[]),...(action==='confirm'?['childProposalId','expectedPreviewHash']:[])])||action==='confirm'&&(!ID.test(body.childProposalId)||!HEX.test(body.expectedPreviewHash)))throw Error();}catch{return reply({error:'The selected variation could not be read.'},400);}
   if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);live();
   let preview;try{preview=await resolveParameterQuestion({source:body.source,selection:body.selection,...(Object.hasOwn(body,'parentSettings')?{parentSettings:body.parentSettings}:{})},{db,crypto,fetcher,registry,history,programIndex,signal:request.signal});}catch{return reply({error:'The original calculation or selected change is unavailable. Review it again.'},422);}
   const childCardJson=C.serialize(preview.derivation.card),childProposalId='p_'+await sha(childCardJson,crypto),previewHash=await sha(preview,crypto);live();
   if(action==='preview')return reply({preview,childProposalId,previewHash});
   if(childProposalId!==body.childProposalId||previewHash!==body.expectedPreviewHash)return reply({error:'The variation changed since preview. Review it again.'},409);
   const child=await query('SELECT p.id,p.card_hash,p.card_json FROM proposals p JOIN research_ideas i ON i.proposal_id=p.id WHERE p.id=?',childProposalId).first();
   if(!child)return reply({error:'Confirm and publish the new question before linking this variation.'},409);
   if(child.card_json!==childCardJson||child.card_hash!==childProposalId.slice(2)||C.serialize(validateCard(child.card_json))!==childCardJson)throw Error('Changed public child');
   const origin={schema:preview.derivation.selection.parameter==='evaluation'?'liberpedia-question-derivation-v4':preview.source.questionProgram?'liberpedia-question-derivation-v3':preview.source.reviewedProgram?'liberpedia-question-derivation-v2':'liberpedia-question-derivation-v1',parentProposalId:preview.parentQuestion.proposalId,childProposalId,previewHash,source:preview.source,selection:preview.derivation.selection,...(preview.derivation.parent.settings?{parentSettings:preview.derivation.parent.settings}:{}),childTaskId:preview.derivation.task.taskId},json=E.stable(origin),id=await sha(json,crypto);live();
   if(json.length>MAX||origin.parentProposalId===childProposalId)throw Error('Invalid lineage');
   const find=()=>query('SELECT id,origin_json,created_at FROM question_derivations WHERE id=?',id).first();let saved=await find();
   if(!saved){const at=now().toISOString(),day=at.slice(0,10);live();await db.batch([query(`INSERT INTO question_derivations(id,parent_proposal_id,child_proposal_id,origin_json,created_at,created_day) SELECT ?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM research_ideas WHERE proposal_id=?) AND EXISTS(SELECT 1 FROM research_ideas WHERE proposal_id=?) AND (SELECT COUNT(*) FROM question_derivations WHERE created_day=?)<? ON CONFLICT(id) DO NOTHING`,id,origin.parentProposalId,childProposalId,json,at,day,origin.parentProposalId,childProposalId,day,dailyCap)]);saved=await find();}
   if(!saved)return reply({error:'The daily variation limit has been reached.'},429);if(saved.origin_json!==json)throw Error('Changed lineage');return reply({id,childProposalId,parentProposalId:origin.parentProposalId,createdAt:saved.created_at});
  }catch{return reply({error:'Question variations are temporarily unavailable.'},503);}
 };
}
