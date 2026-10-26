/* Bind ordinary preparation to a verified parameter preview's exact source bytes.
 * No new execution authority. Mismatched plans never expose their admission token. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import C from '../../claim-specification.js';
import {validateCard} from './idea-relations.mjs';
import {resolveParameterQuestion} from './parameter-question-source.mjs';
import {createPrepareTaskHandler} from './prepare-task.mjs';
import {loadInputBundle} from './official-inputs.mjs';
const PROPOSAL=/^p_[a-f0-9]{64}$/,PREP=/^prep_[a-f0-9]{64}$/;
const same=(a,b)=>E.stable(a)===E.stable(b),ensure=(ok,message)=>{if(!ok)throw Error(message);};
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const hash=async(value,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
const changed=()=>freeze({state:'review-required',code:'parameter-source-changed',error:'The manuscript text, edition or alphabet changed from the reviewed calculation. Review this variation again before running it.'});
async function readJSON(response,max,signal){
 ensure(!signal?.aborted,'Parameter preparation was cancelled.');const reader=response.body?.getReader();ensure(reader,'The response body is unavailable.');let size=0;const chunks=[];let stop;const aborted=new Promise((_,reject)=>{stop=()=>reject(Error('Parameter preparation was cancelled.'));signal?.addEventListener('abort',stop,{once:true});});
 try{while(true){ensure(!signal?.aborted,'Parameter preparation was cancelled.');const part=await Promise.race([reader.read(),aborted]);if(part.done)break;size+=part.value.byteLength;ensure(size<=max,'Parameter preparation response exceeds its byte limit.');chunks.push(part.value);}}catch(error){try{void reader.cancel().catch(()=>{});}catch{}throw error;}finally{signal?.removeEventListener('abort',stop);}
 const bytes=new Uint8Array(size);let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.byteLength;}
 return J.capture(JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(bytes)),{maxBytes:max,maxDepth:24,maxNodes:500000});
}
function taskMatches(task,expected,ids){
 E.validateTask(task);ensure(same(task.alphabet,expected.alphabet)&&same(task.steps,expected.steps)&&same(task.criterion,expected.criterion),'Parameter source changed');
 const pages=expected.pages.filter(page=>ids.includes(page.id));ensure(ids.length===pages.length&&same(ids,pages.map(page=>page.id))&&same(task.pages,pages),'Parameter source changed');
}
function coverageCheck(coverage,expected,inputVersion){
 ensure(coverage&&coverage.inputVersion===inputVersion&&coverage.requestedTask,'Exact requested inputs are missing');
 taskMatches(coverage.requestedTask,expected,expected.pages.map(p=>p.id));
 const ids=expected.pages.map(p=>p.id),covered=coverage.coveredPages,remaining=coverage.remainingPages;
 ensure(Array.isArray(covered)&&Array.isArray(remaining)&&new Set(covered).size===covered.length&&new Set(remaining).size===remaining.length
  &&same(covered,ids.filter(id=>covered.includes(id)))&&same(remaining,ids.filter(id=>remaining.includes(id)))
  &&covered.every(id=>!remaining.includes(id))&&ids.every(id=>covered.includes(id)||remaining.includes(id)),'Exact covered and remaining page scope changed');
 return remaining;
}
export async function prepareParameterQuestion(input,{db,env,crypto=globalThis.crypto,fetcher=globalThis.fetch,signal,resolver=resolveParameterQuestion,prepareHandler,now=()=>new Date(),registry,history,programIndex,clientIP}={}){
 const value=J.capture(input,{maxBytes:65536,maxDepth:16,maxNodes:10000}),hasSettings=!!value&&Object.hasOwn(value,'parentSettings');
 ensure(value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===(hasSettings?4:3)&&['source','selection','childProposalId'].every(k=>Object.hasOwn(value,k))&&typeof value.childProposalId==='string'&&PROPOSAL.test(value.childProposalId),'Use an exact source, change and public child question.');
 db??=env?.PROPOSALS;ensure(db?.prepare&&env?.PROPOSALS===db&&typeof env.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN,'Parameter preparation is unavailable.');
 const live=()=>ensure(!signal?.aborted,'Parameter preparation was cancelled.');live();
 const preview=J.capture(await resolver({source:value.source,selection:value.selection,...(hasSettings?{parentSettings:value.parentSettings}:{})},{db,crypto,fetcher,signal,registry,history,programIndex}),{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000});live();
 ensure(preview.schema==='liberpedia-parameter-question-preview-v1'&&preview.derivation?.task&&preview.derivation.card,'The authenticated parameter preview is unavailable.');
 const expected=preview.derivation.task,inputVersion=preview.derivation.parent.inputVersion;await E.checkIdentity(expected,crypto);live();
 const card=validateCard(preview.derivation.card),cardText=C.serialize(card),cardHash=await hash(cardText,crypto);live();
 ensure(value.childProposalId==='p_'+cardHash,'The child question differs from the reviewed variation.');
 const row=await db.prepare('SELECT p.id,p.card_hash,p.card_json FROM proposals p JOIN research_ideas public ON public.proposal_id=p.id WHERE p.id=?').bind(value.childProposalId).first();live();
 ensure(row&&row.id===value.childProposalId&&row.card_hash===cardHash&&row.card_json===cardText,'The exact child question must be public before preparing it.');
 // Preflight prevents an ordinary source refresh from issuing a misleading
 // token. The final response is checked again because inputs can race this read.
 const controller=new AbortController(),abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});const timer=setTimeout(()=>controller.abort(),20000);
 let official;
 try{official=await loadInputBundle({fetcher,signal:controller.signal,read:(response,max)=>readJSON(response,max,controller.signal)});live();}
 finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}
 if(!same(official.alphabet,expected.alphabet)||!['raw','reviewed'].includes(inputVersion)||expected.pages.some(page=>{const source=official.pages.get(page.id);return !source||source[inputVersion==='raw'?'raw':'reviewed_text']!==page.text;}))return changed();
 const handler=prepareHandler||createPrepareTaskHandler({fetcher,now});
 const response=await handler(new Request('https://parameter-preparation.invalid/prepare-task',{method:'POST',headers:{origin:env.SITE_ORIGIN,'Content-Type':'application/json',...(typeof clientIP==='string'&&clientIP.length<=128?{'CF-Connecting-IP':clientIP}:{})},body:JSON.stringify({proposalId:value.childProposalId,parentTaskId:null}),...(signal?{signal}:{})}),env);live();
 const body=await readJSON(response,8*1024*1024,signal);live();
 if(!response.ok)return freeze({state:'preparation-unavailable',error:typeof body.error==='string'?body.error:'The variation could not be prepared. Please retry.'});
 if(!['plan-ready','scope-covered'].includes(body.state))return freeze({state:'preparation-unavailable',error:'The variation did not produce an exact runnable plan. Review the question again.'});
 try{
  ensure(body.proposalId===value.childProposalId&&body.parentTaskId===null&&body.inputVersion===inputVersion,'Parameter source changed');
  if(body.coverage?.requestedTask){await E.checkIdentity(body.coverage.requestedTask,crypto);live();}
  const ids=expected.pages.map(p=>p.id),remaining=body.coverage?coverageCheck(body.coverage,expected,inputVersion):ids;
  if(body.state==='scope-covered')ensure(body.coverage&&remaining.length===0&&!Object.hasOwn(body,'task')&&!Object.hasOwn(body,'preparation'),'Exact saved coverage is missing');
  else{
   ensure(remaining.length>0,'No uncovered page remains');taskMatches(body.task,expected,remaining);await E.checkIdentity(body.task,crypto);live();
   const receipt=body.preparation;
   ensure(receipt&&PREP.test(receipt.id)&&receipt.version===1&&receipt.proposalId===value.childProposalId&&receipt.taskId===body.task.taskId&&receipt.cardHash===cardHash&&receipt.taskHash===await hash(body.task,crypto)&&receipt.inputVersion===inputVersion&&receipt.parentTaskId===null&&receipt.authority==='idea'&&receipt.controlsHash===await hash(body.controls,crypto),'The preparation receipt differs from the reviewed variation');live();
  }
 }catch(error){live();return changed();}
 live();return freeze(body);
}

export function createParameterQuestionPreparationHandler(options={}){
 const prepare=options.prepare||prepareParameterQuestion;
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(value,status=200)=>new Response(JSON.stringify(value),{status,headers});
  let allowed=false;try{allowed=typeof env?.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN&&['http:','https:'].includes(new URL(env.SITE_ORIGIN).protocol);}catch{}
  if(!allowed)return reply({error:'Parameter preparation is unavailable.'},503);
  if(request.headers.get('origin')!==env.SITE_ORIGIN)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=env.SITE_ORIGIN;
  const url=new URL(request.url);if(url.pathname!=='/parameter-questions/prepare'||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const fields=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='POST'||fields.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!=='POST'){headers.Allow='POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  const rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;
  if(!env.PROPOSALS?.prepare||!rate?.limit)return reply({error:'Parameter preparation is unavailable.'},503);
  if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''))return reply({error:'The preparation request could not be read.'},400);
  const length=request.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>65536))return reply({error:'The preparation request exceeds its byte bound.'},400);
  const controller=new AbortController(),abort=()=>controller.abort();request.signal?.addEventListener('abort',abort,{once:true});if(request.signal?.aborted)controller.abort();const timer=setTimeout(()=>controller.abort(),45000);let bodyChecked=false;
  try{
   const body=await readJSON(request,65536,controller.signal),hasSettings=!!body&&Object.hasOwn(body,'parentSettings');
   ensure(body&&typeof body==='object'&&!Array.isArray(body)&&Object.keys(body).length===(hasSettings?4:3)&&['source','selection','childProposalId'].every(k=>Object.hasOwn(body,k))&&typeof body.childProposalId==='string'&&PROPOSAL.test(body.childProposalId),'Malformed preparation request');
   const choice=body.selection;ensure(choice&&typeof choice==='object'&&!Array.isArray(choice)&&Object.keys(choice).length===4&&['version','step','parameter','value'].every(k=>Object.hasOwn(choice,k))&&choice.version===1&&Number.isInteger(choice.step)&&choice.step>=0&&choice.step<8&&['direction','reset'].includes(choice.parameter)&&(choice.parameter==='direction'?['add','subtract']:['page','line','word']).includes(choice.value),'Malformed preparation request');bodyChecked=true;
   const clientIP=request.headers.get('CF-Connecting-IP')||'unknown';
   if(!(await rate.limit({key:clientIP}))?.success)return reply({error:'Please wait before trying again.'},429);
   const result=await prepare(body,{...options,db:env.PROPOSALS,env,clientIP,signal:controller.signal});
   ensure(!controller.signal.aborted,'Parameter preparation was cancelled.');
   return reply(result,result.state==='review-required'?409:result.state==='preparation-unavailable'?503:200);
  }catch(error){return reply({error:controller.signal.aborted?'Parameter preparation was cancelled. Please retry.':'The variation could not be prepared. Review its source and question again.'},!bodyChecked&&!controller.signal.aborted?400:503);}
  finally{clearTimeout(timer);request.signal?.removeEventListener('abort',abort);}
 };
}
