import Compiler from '../../fixed-plan-compiler.js';
import AffineChoices from '../../affine-search-clarification.js';
import {issue as issuePreparation} from './prepared-plans.mjs';
import {loadInputBundle} from './official-inputs.mjs';
import PlanControls from '../../local-plan-controls.js';
import Protocols from '../../experiment-protocols.js';
import Evaluators from '../../output-evaluators.js';
import {findEvidence,rememberEvidence} from './task-evidence.mjs';
/* Source-bound proposed plans; inference can map wording, never execute code. */
import L from '../../local-experiment.js';
import C from '../../claim-specification.js';
import {validateCard} from './idea-relations.mjs';
import {createAIPlanner} from './propose-task-plan.mjs';
// Exact ordered GP table from data/index.json; RUNES/LATIN agree with scripts/reproduce_reading.py.
const ALPHABET=[{"rune":"ᚠ","latin":"F","prime":2},{"rune":"ᚢ","latin":"U","prime":3},{"rune":"ᚦ","latin":"TH","prime":5},{"rune":"ᚩ","latin":"O","prime":7},{"rune":"ᚱ","latin":"R","prime":11},{"rune":"ᚳ","latin":"C","prime":13},{"rune":"ᚷ","latin":"G","prime":17},{"rune":"ᚹ","latin":"W","prime":19},{"rune":"ᚻ","latin":"H","prime":23},{"rune":"ᚾ","latin":"N","prime":29},{"rune":"ᛁ","latin":"I","prime":31},{"rune":"ᛄ","latin":"J","prime":37},{"rune":"ᛇ","latin":"EO","prime":41},{"rune":"ᛈ","latin":"P","prime":43},{"rune":"ᛉ","latin":"X","prime":47},{"rune":"ᛋ","latin":"S","prime":53},{"rune":"ᛏ","latin":"T","prime":59},{"rune":"ᛒ","latin":"B","prime":61},{"rune":"ᛖ","latin":"E","prime":67},{"rune":"ᛗ","latin":"M","prime":71},{"rune":"ᛚ","latin":"L","prime":73},{"rune":"ᛝ","latin":"NG","prime":79},{"rune":"ᛟ","latin":"OE","prime":83},{"rune":"ᛞ","latin":"D","prime":89},{"rune":"ᚪ","latin":"A","prime":97},{"rune":"ᚫ","latin":"AE","prime":101},{"rune":"ᚣ","latin":"Y","prime":103},{"rune":"ᛡ","latin":"IA","prime":107},{"rune":"ᛠ","latin":"EA","prime":109}];
const PURPOSE='A proposed bounded computation, not a confirmed cipher rule or a decryption verdict.';
const MEASUREMENT_IDS=new Set(Protocols.list().map(d=>d.operation.id)),MEASUREMENT_KINDS=new Set(Protocols.list().map(d=>d.id));
export const planCard=input=>Compiler.compile(validateCard(input));
const proposePlan=createAIPlanner({compile:planCard});
async function jsonBody(message,max){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error();
 const declared=message.headers.get('content-length');if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>max))throw Error();
 const reader=message.body?.getReader();if(!reader)throw Error();const chunks=[];let size=0;
 while(true){const r=await reader.read();if(r.done)break;size+=r.value.length;if(size>max){await reader.cancel();throw Error();}chunks.push(r.value);}
 const bytes=new Uint8Array(size);let i=0;for(const chunk of chunks){bytes.set(chunk,i);i+=chunk.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
export function createPrepareTaskHandler({fetcher=globalThis.fetch,now=()=>new Date(),prepareControls=PlanControls.prepare,discoverEvidence=findEvidence,remember=rememberEvidence}={}){
 return async function handle(request,env){
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let allowed=false;try{allowed=typeof env?.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN&&['http:','https:'].includes(new URL(env.SITE_ORIGIN).protocol);}catch{}
  if(!allowed)return reply({error:'Plan preparation is unavailable.'},503);
  if(request.headers.get('origin')!==env.SITE_ORIGIN)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=env.SITE_ORIGIN;
  if(new URL(request.url).pathname!=='/prepare-task')return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const fields=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='POST'||fields.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});
  }
  if(request.method!=='POST')return reply({error:'Method is not allowed.'},405);
  if(!env.PROPOSALS?.prepare||!(env.TASK_LIMIT||env.PROPOSAL_LIMIT)?.limit)return reply({error:'Plan preparation is unavailable.'},503);
  let body;try{body=await jsonBody(request,32000);const methodClarification=body&&Object.hasOwn(body,'includeMethodClarification');if(!body||typeof body!=='object'||Array.isArray(body)||Object.keys(body).length!==(methodClarification?3:2)||!Object.hasOwn(body,'proposalId')||!Object.hasOwn(body,'parentTaskId')||methodClarification&&body.includeMethodClarification!==true||!/^p_[a-f0-9]{64}$/.test(body.proposalId)||(body.parentTaskId!==null&&!/^[a-f0-9]{64}$/.test(body.parentTaskId)))throw Error();}catch{return reply({error:'The plan request could not be read.'},400);}
  try{
   if(!(await (env.TASK_LIMIT||env.PROPOSAL_LIMIT).limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   const query=(sql,...args)=>env.PROPOSALS.prepare(sql).bind(...args).first();
   const row=await query('SELECT card_json FROM proposals WHERE id=?',body.proposalId);if(!row)return reply({error:'Confirmed idea not found.'},404);
   if(body.parentTaskId&&!await query('SELECT id FROM local_tasks WHERE id=?',body.parentTaskId))return reply({error:'Parent task not found.'},404);
   const card=validateCard(row.card_json);let plan=planCard(card),interpretationNotes=[],basis={kind:'compiled-card',normalizedCard:card};
   // Choosing a check is a research decision. Neither the planner nor its AI
   // wording adapter may silently replace it with descriptive measurements.
   if(plan.field==='evaluation')return reply({state:plan.state,proposalId:body.proposalId,...(plan.state==='needs-clarification'?{field:'evaluation'}:{}),reason:plan.reason});
   if(body.includeMethodClarification===true&&plan.reason){
    const clarification=AffineChoices.describe(card);
    if(clarification)return reply({state:'needs-clarification',proposalId:body.proposalId,field:'method',reason:'Confirm the affine convention and the settings to enumerate.',clarification});
   }
   // Older clients only understand evaluation clarification. Keep this exact
   // supported-method question opt-in during the frontend transition.
   if(body.includeMethodClarification===true&&plan.state==='needs-clarification'&&plan.field==='method')return reply({state:plan.state,proposalId:body.proposalId,field:plan.field,reason:plan.reason,clarification:plan.clarification});
   if(plan.reason){
    if(card.method.value?.operations?.some(op=>MEASUREMENT_IDS.has(op.id))||MEASUREMENT_KINDS.has(card.rules.evaluation.value?.kind))return reply({state:'needs-adapter',reason:plan.reason,proposalId:body.proposalId});
    const mapped=await proposePlan(card,env);
    if(!mapped.reason){plan=mapped.plan;interpretationNotes=mapped.notes;basis={kind:'mapped-card',normalizedCard:mapped.card,mapping:mapped.mapping};}
    else return reply({state:'needs-adapter',reason:mapped.reason,proposalId:body.proposalId});
   }
   if(plan.reason)return reply({state:'needs-adapter',reason:plan.reason,proposalId:body.proposalId});
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),20000);const pages=Array(plan.pages.length);let next=0,totalBytes=0;
   try{
    const bundle=plan.pages.length>40?await loadInputBundle({fetcher,signal:controller.signal,read:jsonBody}):null;if(bundle&&L.stable(bundle.alphabet)!==L.stable(ALPHABET))throw Error();
    const worker=async()=>{try{while(next<plan.pages.length){if(controller.signal.aborted)throw Error();const index=next++,id=plan.pages[index];const response=bundle?null:await fetcher('https://jelliottdev.github.io/data/pages/'+id+'.json',{redirect:'manual',signal:controller.signal});if(response&&!response.ok)throw Error();const page=bundle?bundle.pages.get(id):await jsonBody(response,512*1024),text=plan.inputVersion==='raw'?page.raw:page.reviewed_text;if(page.id!==id||typeof text!=='string')throw Error();totalBytes+=new TextEncoder().encode(text).length;if(totalBytes>2000000)throw Error();pages[index]={id,text};}}catch(error){controller.abort();throw error;}};
    await Promise.all(Array.from({length:Math.min(4,pages.length)},()=>worker()));
   }catch(error){console.warn('prepare-task: official manuscript source unavailable',error?.name||'Error',error?.message||'');return reply({error:'The selected manuscript text could not be loaded.'},422);}finally{clearTimeout(timer);}
   const title=Protocols.describe(plan.criterion)?.title||plan.steps.map(s=>s.op==='reverse'?'Reverse rune order within each '+s.unit:s.op==='affine'?'Affine mapping ('+s.a+', '+s.b+')':s.op==='finite-shift'?'Finite key stream '+(s.direction==='subtract'?'subtraction':'addition')+' · '+s.key.length+' indices · '+s.reset+' resets':s.op==='interrupted-keyed-shift'?'Interrupted repeating-key '+(s.direction==='subtract'?'subtraction':'addition')+' · '+s.key.length+'-rune key · '+s.reset+' resets':s.op==='keyed-shift'?(s.mode==='repeat'?'Repeating-key':s.mode==='plaintext-autokey'?'Plaintext autokey':'Ciphertext autokey')+' '+(s.direction==='subtract'?'subtraction':'addition')+' · '+s.key.length+'-rune '+(s.mode==='repeat'?'key':'seed')+' · '+s.reset+' resets':'Cumulative difference with '+s.reset+' resets').join(', then ').slice(0,300);
   let task;try{task=await L.prepare({title,pages,alphabet:ALPHABET,steps:plan.steps,criterion:plan.criterion});}catch(error){return reply({state:'needs-adapter',reason:String(error?.message||'').startsWith('The finite key stream is shorter')?'The supplied finite stream is too short for a complete page segment. Supply enough values or specify a different reset.':'The explicit plan exceeds the supported runner bounds or criterion.',proposalId:body.proposalId});}
   const requestedTask=task,found=await discoverEvidence({db:env.PROPOSALS,task:requestedTask,inputVersion:plan.inputVersion});
   const coverage={...found,requestedTask,inputVersion:plan.inputVersion};
   if(found.truncated&&found.remainingPages.length){
    await remember({db:env.PROPOSALS,proposalId:body.proposalId,task:requestedTask,inputVersion:plan.inputVersion,coverage,createdAt:now().toISOString()});
    return reply({state:'coverage-unavailable',coverageUnavailable:true,coverage,error:'Saved computation evidence could not be checked completely. Please retry before creating more work.'},503);
   }
   if(!found.remainingPages.length){
   await remember({db:env.PROPOSALS,proposalId:body.proposalId,task:requestedTask,inputVersion:plan.inputVersion,coverage,createdAt:now().toISOString()});
   return reply({state:'scope-covered',proposalId:body.proposalId,parentTaskId:body.parentTaskId,inputVersion:plan.inputVersion,coverage,notes:[...interpretationNotes,...plan.notes],purpose:PURPOSE});}
   if(found.coveredPages.length){
    task=await L.prepare({...requestedTask,pages:requestedTask.pages.filter(page=>found.remainingPages.includes(page.id))});
    basis={kind:'evidence-remainder',originalBasis:basis,requestedTaskId:requestedTask.taskId,evidence:found.evidence};
   }
   let controls;
   try{controls=await prepareControls(task,crypto);await PlanControls.validate(controls,task,crypto);}
   catch{return reply({error:'The runner checks failed. No experiment was created.'},422);}
   await remember({db:env.PROPOSALS,proposalId:body.proposalId,task:requestedTask,inputVersion:plan.inputVersion,coverage,createdAt:now().toISOString()});
   const preparation=await issuePreparation({db:env.PROPOSALS,proposalId:body.proposalId,card,task,inputVersion:plan.inputVersion,parentTaskId:body.parentTaskId,controls,authority:'idea',basis,createdAt:now().toISOString()});
   return reply({state:'plan-ready',proposalId:body.proposalId,parentTaskId:body.parentTaskId,inputVersion:plan.inputVersion,task,controls,preparation,...(found.coveredPages.length?{coverage}:{}),notes:[...interpretationNotes,...plan.notes],purpose:PURPOSE});
  }catch{return reply({error:'Plan preparation is temporarily unavailable.'},503);}
 };
}
