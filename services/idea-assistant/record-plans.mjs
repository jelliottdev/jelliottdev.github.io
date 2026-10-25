/* Authored bounded follow-ups. No inference, persistence or target execution. */
import L from '../../local-experiment.js';
import Control from '../../local-control.js';
import Evaluators from '../../output-evaluators.js';
import C from '../../claim-specification.js';
import Context from '../../followup-context.js';
import {validateCard} from './idea-relations.mjs';
import {planCard} from './prepare-task.mjs';
import {loadInputBundle} from './official-inputs.mjs';
import {findEvidence} from './task-evidence.mjs';
import {boundaryComparison} from './boundary-comparison.mjs';
import {discoverOrdinaryPrefixEvidence} from './ordinary-prefix-evidence.mjs';
const BASE='https://jelliottdev.github.io',HEX=/^[a-f0-9]{64}$/,ID=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
export const recordPlanDigest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',typeof text==='string'?new TextEncoder().encode(text):text))].map(v=>v.toString(16).padStart(2,'0')).join('');
export function validOrigin(origin){return exact(origin,['recordId','followupId','recordSha256','protocolSha256'])&&[origin.recordId,origin.followupId].every(v=>typeof v==='string'&&v.length<=100&&ID.test(v))&&HEX.test(origin.recordSha256)&&HEX.test(origin.protocolSha256);}
async function readJSON(response,max){
 if(response.ok===false||!/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''))throw Error('The official source is unavailable.');
 const declared=response.headers.get('content-length');if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>max))throw Error('Source exceeds its bound.');
 const reader=response.body?.getReader();if(!reader)throw Error('Missing source.');let size=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();throw Error('Source exceeds its bound.');}chunks.push(value);}
 const bytes=new Uint8Array(size);let pos=0;for(const part of chunks){bytes.set(part,pos);pos+=part.length;}const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);return {bytes,text,value:JSON.parse(text)};
}
export async function loadRecordPlan({recordId,followupId},{fetcher=globalThis.fetch,timeoutMs=20000}={}){
 if(![recordId,followupId].every(v=>typeof v==='string'&&v.length<=100&&ID.test(v)))throw Error('Invalid record or follow-up ID.');
 if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>20000)throw Error('Invalid deadline.');
 const controller=new AbortController();let timer;
 const work=async()=>{
  const get=async(path,max=512*1024)=>{if(controller.signal.aborted)throw Error('Source loading cancelled.');return readJSON(await fetcher(BASE+path,{redirect:'manual',signal:controller.signal,cache:'no-cache'}),max);};
  const raw=await get('/experiments/records/'+recordId+'/record.json'),record=raw.value;
  if(record.id!==recordId||record.status!=='published'||!Array.isArray(record.browser_followups)||record.browser_followups.length>8)throw Error('This published follow-up is unavailable.');
  const found=record.browser_followups.filter(v=>v?.id===followupId);if(found.length!==1)throw Error('This published follow-up is unavailable.');const recipe=found[0];
  const hasMotivation=Object.hasOwn(recipe,'motivation');
  if(!exact(recipe,['id','title','question','scope_change','limitation','card','inputs','control',...(hasMotivation?['motivation']:[])]))throw Error('The follow-up declaration is malformed.');
  if(hasMotivation&&!Context.valid(recipe.motivation))throw Error('The follow-up motivation is malformed.');
  for(const name of ['title','question','scope_change','limitation'])if(typeof recipe[name]!=='string'||!recipe[name].trim()||Array.from(recipe[name]).length>(name==='title'?300:1200))throw Error('The follow-up text is malformed.');
  const card=validateCard(recipe.card);if(L.stable(card)!==L.stable(recipe.card))throw Error('The declared card is not canonical.');
  const rules=card.rules;if(!['inputVersion','representation','evaluation'].every(k=>rules[k].status==='specified')||rules.representation.value!=='GP29'||!(rules.evaluation.value==='measurement'||Evaluators.identify(rules.evaluation.value)||['exact-prefix','word-affine-count','word-prime-sums'].includes(rules.evaluation.value?.kind)))throw Error('The follow-up needs explicit input, alphabet and supported evaluation.');
  const plan=planCard(card);if(plan.reason)throw Error(plan.reason);
  const pins=recipe.inputs;if(!exact(pins,['version','alphabet_sha256','pages'])||pins.version!==plan.inputVersion||!HEX.test(pins.alphabet_sha256)||!Array.isArray(pins.pages)||pins.pages.length!==plan.pages.length)throw Error('The input pins are malformed.');
  for(let i=0;i<pins.pages.length;i++)if(!exact(pins.pages[i],['id','text_sha256'])||pins.pages[i].id!==plan.pages[i]||!HEX.test(pins.pages[i].text_sha256))throw Error('The page pins do not match the declared scope.');
  const index=(await get('/data/index.json',2*1024*1024)).value;
  if(!Array.isArray(index.alphabet)||index.alphabet.length!==29)throw Error('The official alphabet is unavailable.');
  const alphabet=index.alphabet.map(v=>({rune:v.rune,latin:v.latin,prime:v.prime}));
  if(await recordPlanDigest(L.stable(alphabet))!==pins.alphabet_sha256)throw Error('The official alphabet changed.');
  const control=recipe.control;if(!exact(control,['label','task','expected_result_sha256'])||typeof control.label!=='string'||!control.label.trim()||control.label.length>300||!HEX.test(control.expected_result_sha256))throw Error('The synthetic control is malformed.');
  await L.checkIdentity(control.task);
  const controlRunes=new Set(control.task.alphabet.map(v=>v.rune));if(control.task.pages.length!==1||Array.from(control.task.pages[0].text).filter(ch=>controlRunes.has(ch)).length>4096)throw Error('The synthetic control exceeds its bound.');
  if(!Control.compatible(control.task,{steps:plan.steps,alphabet,criterion:plan.criterion}))throw Error('The control uses a different program, alphabet or unsupported criterion.');
  const result=L.run(control.task);if(!Control.passed(control.task,result)||await recordPlanDigest(L.stable(result))!==control.expected_result_sha256)throw Error('The declared synthetic control failed.');
  const pages=Array(plan.pages.length);let next=0,total=0;
  const accept=async(i,page)=>{const id=plan.pages[i],text=pins.version==='raw'?page.raw:page.reviewed_text;if(page.id!==id||typeof text!=='string'||await recordPlanDigest(text)!==pins.pages[i].text_sha256)throw Error('The pinned manuscript input changed.');total+=new TextEncoder().encode(text).length;if(total>2000000)throw Error('The selected inputs exceed their bound.');pages[i]={id,text};};
  if(pages.length>40){
   // One fixed source keeps authored large scopes below Workers' subrequest cap.
   // Invalid aggregates must not trigger an unbounded per-page fallback.
   const bundle=await loadInputBundle({fetcher,signal:controller.signal,read:async(response,max)=>(await readJSON(response,max)).value});
   if(L.stable(bundle.alphabet)!==L.stable(alphabet))throw Error('The official input aggregate alphabet changed.');
   for(let i=0;i<pages.length;i++)await accept(i,bundle.pages.get(plan.pages[i]));
  }else{
   const worker=async()=>{while(next<pages.length){if(controller.signal.aborted)throw Error('Source loading cancelled.');const i=next++,page=(await get('/data/pages/'+plan.pages[i]+'.json')).value;await accept(i,page);}};
   await Promise.all(Array.from({length:Math.min(4,pages.length)},worker));
  }
  const task=await L.prepare({title:recipe.title,pages,alphabet,steps:plan.steps,criterion:plan.criterion});
  return {state:'plan-ready',origin:{recordId,followupId,recordSha256:await recordPlanDigest(raw.bytes),protocolSha256:await recordPlanDigest(L.stable(recipe))},card,task,inputVersion:plan.inputVersion,control,question:recipe.question,scopeChange:recipe.scope_change,limitation:recipe.limitation,...(hasMotivation?{motivation:recipe.motivation}:{}),snapshot:recipe};
 };
 try{return await Promise.race([work(),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Official source loading timed out.'));},timeoutMs);})]);}finally{clearTimeout(timer);controller.abort();}
}
export function createRecordPlanHandler({fetcher=globalThis.fetch,timeoutMs=20000,discoverEvidence=findEvidence,discoverPrefixEvidence=discoverOrdinaryPrefixEvidence}={}){
 return async(request,env)=>{
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',Vary:'Origin'},reply=(v,status=200)=>new Response(JSON.stringify(v),{status,headers});
  const allowed=env?.SITE_ORIGIN;try{if(new URL(allowed).origin!==allowed||!['http:','https:'].includes(new URL(allowed).protocol))throw Error();}catch{return reply({error:'Reviewed plans are unavailable.'},503);}
  if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url);if(url.pathname!=='/record-plans'||url.search)return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){const hs=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);if(request.headers.get('access-control-request-method')!=='POST'||hs.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});}
  if(request.method!=='POST')return reply({error:'Method is not allowed.'},405);
  const rate=env.TASK_LIMIT||env.PROPOSAL_LIMIT;if(!rate?.limit)return reply({error:'Reviewed plans are unavailable.'},503);
  try{if(!(await rate.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);}catch{return reply({error:'Reviewed plans are unavailable.'},503);}
  let body;try{body=(await readJSON(request,1024)).value;const optedIn=body&&Object.hasOwn(body,'includeExisting'),flags=['includeBoundaryComparison','includeExistingContext','includeDerivedPrefixEvidence','includeMotivation'].filter(key=>body&&Object.hasOwn(body,key));if(!exact(body,['recordId','followupId',...(optedIn?['includeExisting']:[]),...flags])||optedIn&&body.includeExisting!==true||flags.some(key=>body[key]!==true||body.includeExisting!==true)||![body.recordId,body.followupId].every(v=>typeof v==='string'&&v.length<=100&&ID.test(v)))throw Error();}catch{return reply({error:'The reviewed plan request is invalid.'},400);}
  let loaded;try{loaded=await loadRecordPlan(body,{fetcher,timeoutMs});}catch(error){return reply({state:'not-runnable',reason:error.message},422);}
  const {snapshot,motivation,...plan}=loaded;
  if(body.includeMotivation===true&&motivation!==undefined)plan.motivation=motivation;
  if(body.includeExisting===true){
   try{
    if(!env.PROPOSALS?.prepare)throw Error('Computation evidence storage is unavailable.');
    // Evidence is independent of this recipe's title and origin. Keep the
    // complete authored plan immutable: a partial remainder is reviewed through
    // the ordinary saved-card planner, never relabeled as this full recipe.
    const found=await discoverEvidence({db:env.PROPOSALS,task:plan.task,inputVersion:plan.inputVersion});
    if(found.truncated&&found.remainingPages.length)throw Error('Computation coverage could not be checked completely.');
    plan.coverage={...found,requestedTask:plan.task,inputVersion:plan.inputVersion};
    if(body.includeDerivedPrefixEvidence===true&&plan.task.criterion.kind==='exact-prefix'&&found.remainingPages.length){
     try{plan.derivedCoverage=(await discoverPrefixEvidence({db:env.PROPOSALS,task:plan.task,inputVersion:plan.inputVersion})).wire;}
     catch{return reply({state:'coverage-unavailable',coverageUnavailable:true,coverage:plan.coverage,error:'Saved output could not be checked. Retry before creating more work.'},503);}
    }
    // The task and recipe must be identical; an unrelated parent-record edit
    // may change recordSha256 without invalidating an immutable saved origin.
    const selectedContext=body.includeExistingContext===true,cardJSON=L.stable(plan.card),proposalId=selectedContext?'p_'+await recordPlanDigest(C.serialize(plan.card)):null;
    const row=await env.PROPOSALS.prepare(`SELECT t.id,o.origin_json${selectedContext?',links.proposal_id,links.input_version,links.parent_task_id,p.card_json':''},
     CASE WHEN EXISTS(SELECT 1 FROM local_task_results r WHERE r.task_id=t.id) THEN 'results-verified' ELSE 'not-run' END AS state
     FROM local_tasks t JOIN local_task_origins o ON o.task_id=t.id
     JOIN local_task_ideas links ON links.task_id=o.task_id AND links.proposal_id=o.proposal_id
     JOIN research_ideas public ON public.proposal_id=links.proposal_id
     ${selectedContext?'JOIN proposals p ON p.id=links.proposal_id':''}
     WHERE t.id=? AND t.task_hash=? AND t.task_json=? AND links.input_version=?
     ${selectedContext?'AND links.parent_task_id IS NULL AND links.proposal_id=? AND p.card_json=?':''}
     AND json_extract(o.origin_json,'$.recordId')=? AND json_extract(o.origin_json,'$.followupId')=?
     AND json_extract(o.origin_json,'$.protocolSha256')=? AND o.snapshot_json=?
     ORDER BY links.created_at,links.proposal_id,o.origin_id LIMIT 1`)
     .bind(plan.task.taskId,await recordPlanDigest(L.stable(plan.task)),L.stable(plan.task),plan.inputVersion,
      ...(selectedContext?[proposalId,cardJSON]:[]),
      plan.origin.recordId,plan.origin.followupId,plan.origin.protocolSha256,L.stable(snapshot)).first();
    if(row){const savedOrigin=JSON.parse(row.origin_json);if(row.id!==plan.task.taskId||!['not-run','results-verified'].includes(row.state)||!validOrigin(savedOrigin)||savedOrigin.recordId!==plan.origin.recordId||savedOrigin.followupId!==plan.origin.followupId||savedOrigin.protocolSha256!==plan.origin.protocolSha256||selectedContext&&(row.proposal_id!==proposalId||row.input_version!==plan.inputVersion||row.parent_task_id!==null||L.stable(validateCard(row.card_json))!==cardJSON))throw Error('Saved origin mismatch');plan.existingTask={id:row.id,state:row.state,...(selectedContext?{proposalId:row.proposal_id}:{})};}
    // New projections are explicit opt-ins so already loaded clients keep
    // their exact supported response shape during staggered deployments.
    if(body.includeBoundaryComparison===true){const comparison=await boundaryComparison({db:env.PROPOSALS,task:plan.task,inputVersion:plan.inputVersion,discoverEvidence});if(comparison)plan.boundaryComparison=comparison;}
   }catch{return reply({state:'coverage-unavailable',coverageUnavailable:true,error:'Existing computation evidence could not be checked. Please retry before creating this experiment.'},503);}
  }
  if(body.includeDerivedPrefixEvidence===true&&new TextEncoder().encode(JSON.stringify(plan)).length>8*1024*1024)return reply({state:'coverage-unavailable',coverageUnavailable:true,coverage:plan.coverage,error:'Saved output exceeds the bounded evidence response. No experiment was created.'},503);
  return reply(plan);
 };
}
