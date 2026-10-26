import {readReviewedProgram} from './reviewed-program-source.mjs';
import Compiler from '../../fixed-plan-compiler.js';
import {prepareOriginWrite} from './finite-origin-storage.mjs';
import {readAdmittedResult} from './admitted-result.mjs';
import {createReadControlCache} from './read-control-cache.mjs';
import {readAdmittedFiniteSnapshotMember,createAuthoredFiniteSourceLoader} from './authored-finite-origin.mjs';
import {authorize as authorizePreparation} from './prepared-plans.mjs';
import {loadInputBundle} from './official-inputs.mjs';
/* Bounded declarative computation persistence. No user code or scientific verdicts. */
import L from '../../local-experiment.js';
import PlanControls from '../../local-plan-controls.js';
import {validateCard} from './idea-relations.mjs';
import {loadRecordPlan,validOrigin as validRecordedOrigin} from './record-plans.mjs';
import {findEvidence} from './task-evidence.mjs';
import {boundaryComparison} from './boundary-comparison.mjs';
import {storageLimits as checkedStorageLimits} from './storage-limits.mjs';
import {scopeRelation} from './authored-prefix-remainder.mjs';
const MAX_BODY=2*1024*1024, HEX=/^[a-f0-9]{64}$/, PROPOSAL=/^p_[a-f0-9]{64}$/;
const NOTICE='Verified computation only; this does not establish a correct reading or scientific conclusion.';
const originalPrepareControls=PlanControls.prepare,readControls=createReadControlCache();
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
function projection(row,task,run,context){
 return {id:row.id,proposalId:context.proposal_id,card:validateCard(context.card_json),title:task.title,plan:task,
  inputVersion:context.input_version,parentTaskId:context.parent_task_id,createdAt:context.created_at,
  state:run?'results-verified':'not-run',...(run?{latestRun:run}:{}),verification:NOTICE};
}
export function createLocalTaskHandler({fetcher=globalThis.fetch,now=()=>new Date(),prepareControls=PlanControls.prepare,discoverEvidence=findEvidence,storageLimits,loadAuthoredSource,loadPinnedDomain,loadPinnedBundle}={}){
 const limits=checkedStorageLimits(storageLimits);
 return async function handle(request,env){
  const sourceLoader=loadAuthoredSource||createAuthoredFiniteSourceLoader(fetcher);
  const allowed=env?.SITE_ORIGIN,origin=request.headers.get('origin');
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let validOrigin=false;try{validOrigin=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!validOrigin)return reply({error:'Local experiments are unavailable.'},503);
  if(origin!==allowed)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=allowed;headers['Access-Control-Expose-Headers']='Retry-After';
  const url=new URL(request.url),path=url.pathname,match=path.match(/^\/tasks\/([a-f0-9]{64})(\/results|\/boundary-comparison)?$/),create=path==='/tasks',comparisonRoute=match?.[2]==='/boundary-comparison';
  if(!create&&!match)return reply({error:'Not found.'},404);
  if(comparisonRoute&&url.search)return reply({error:'Not found.'},404);
  const method=create||match?.[2]==='/results'?'POST':'GET';
  if(request.method==='OPTIONS'){
   const wanted=request.headers.get('access-control-request-method'),hs=(request.headers.get('access-control-request-headers')||'').split(',').map(s=>s.trim().toLowerCase()).filter(Boolean);
   if(wanted!==method||hs.some(s=>s!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':method+', OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});
  }
  if(request.method!==method){headers.Allow=method+', OPTIONS';return reply({error:'Method is not allowed.'},405);}
  let selectedIdea=null;
  if(request.method==='GET'&&!create&&!comparisonRoute&&url.searchParams.has('idea')){
   if(url.searchParams.getAll('idea').length!==1||[...url.searchParams.keys()].some(key=>key!=='idea')||!PROPOSAL.test(url.searchParams.get('idea')||''))return reply({error:'The selected idea is invalid.'},400);
   selectedIdea=url.searchParams.get('idea');
  }
  if(!env.PROPOSALS?.prepare||!env.PROPOSALS?.batch||!(env.TASK_LIMIT||env.PROPOSAL_LIMIT)?.limit)return reply({error:'Local experiments are unavailable.'},503);
  const db=env.PROPOSALS,query=(sql,...args)=>db.prepare(sql).bind(...args),find=id=>query('SELECT * FROM local_tasks WHERE id = ?',id).first();
  const controlsFor=async(task,readOnly=false)=>{if(readOnly&&prepareControls===originalPrepareControls)return readControls.read(task,crypto);const suite=await prepareControls(task,crypto);if(prepareControls!==originalPrepareControls)await PlanControls.validate(suite,task,crypto);else readControls.prime(task,suite);return suite;};
  const publicContext=row=>query(`SELECT links.proposal_id,links.input_version,links.parent_task_id,links.created_at,p.card_json
   FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id
   JOIN proposals p ON p.id=links.proposal_id WHERE links.task_id=?
   ORDER BY CASE WHEN links.proposal_id=? THEN 0 ELSE 1 END,links.created_at,links.proposal_id LIMIT 1`,row.id,row.proposal_id).first();
  const view=async (row,task,linkedProposalId=null,selectedContext=null,preferredOriginId=null)=>{
   const context=selectedContext||(linkedProposalId?await query(`SELECT links.proposal_id,links.input_version,links.parent_task_id,links.created_at,p.card_json
    FROM local_task_ideas links JOIN proposals p ON p.id=links.proposal_id
    WHERE links.task_id=? AND links.proposal_id=?`,row.id,linkedProposalId).first():await publicContext(row));
   if(!context)throw Error('Missing visible task association');
   const latest=await query('SELECT * FROM local_task_results WHERE task_id=? ORDER BY created_at DESC,id DESC LIMIT 1',row.id).first();let run=null;
   const publicRows=await query(`SELECT json_group_array(proposal_id) AS ids FROM (
    SELECT links.proposal_id FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id
    WHERE links.task_id=? ORDER BY links.created_at,links.proposal_id LIMIT 51)`,row.id).first();
   const publicIds=JSON.parse(publicRows?.ids||'[]');
   const selectedOriginRow=linkedProposalId?await query(`SELECT o.origin_id,o.origin_json FROM local_task_all_origins o JOIN research_ideas public ON public.proposal_id=o.proposal_id WHERE o.task_id=? AND o.proposal_id=? ORDER BY CASE WHEN o.origin_id=? THEN 0 ELSE 1 END,o.created_at,o.origin_id LIMIT 1`,row.id,linkedProposalId,preferredOriginId).first():null;
   if(selectedOriginRow)preferredOriginId=selectedOriginRow.origin_id;
   const originRows=await query(`SELECT json_group_array(json_object('origin',json(origin_json),'snapshotText',snapshot_json,'storage',storage_kind)) AS entries FROM (
    SELECT o.origin_json,o.snapshot_json,o.storage_kind FROM local_task_all_origins o JOIN research_ideas public ON public.proposal_id=o.proposal_id
    WHERE o.task_id=? GROUP BY o.origin_id,o.origin_json,o.snapshot_json
    ORDER BY CASE WHEN o.origin_id=? THEN 0 ELSE 1 END,MIN(o.created_at),o.origin_id LIMIT 11)`,row.id,preferredOriginId).first();
   const savedOrigins=JSON.parse(originRows?.entries||'[]').map(saved=>({...saved,snapshot:JSON.parse(saved.snapshotText)})),origins=[];
   for(const saved of savedOrigins.slice(0,10)){if(!validRecordedOrigin(saved.origin)||saved.storage==='shared'&&L.stable(saved.snapshot)!==saved.snapshotText||await digest(L.stable(saved.snapshot))!==saved.origin.protocolSha256)throw Error('Stored reviewed origin mismatch');const s=saved.snapshot,finite=s.kind==='finite-settings'?await readAdmittedFiniteSnapshotMember(task,s):null,relation=finite?finite.scopeRelation:await scopeRelation(task,s);origins.push({origin:saved.origin,control:finite?finite.control:s.control,question:s.question,scopeChange:s.scope_change,limitation:s.limitation,...(relation?{scopeRelation:relation}:{})});}
   const controls=origins.length&&!origins.some(item=>item.scopeRelation)&&task.criterion.kind!=='language-score'?null:await controlsFor(task,!!latest);
   let selectedRecordOrigin=null;if(selectedOriginRow){const candidate=JSON.parse(selectedOriginRow.origin_json);if(!origins.some(item=>L.stable(item.origin)===L.stable(candidate)))throw Error('Selected authored context is not included in the validated origins');selectedRecordOrigin=candidate;}
   if(latest){const result=await readAdmittedResult(task,latest);run={id:latest.id,createdAt:latest.created_at,result};}
   let shared=null,coverageUnavailable=false;
   if(!run){try{shared=await discoverEvidence({db,task,inputVersion:context.input_version});if(shared.truncated&&shared.remainingPages.length)coverageUnavailable=true;}catch{coverageUnavailable=true;}}
   let reviewedProgram=null;const originalCard=validateCard(context.card_json);if(Compiler.compile(originalCard).reason){try{reviewedProgram=await readReviewedProgram({db,proposalId:context.proposal_id,card:originalCard,task,inputVersion:context.input_version,parentTaskId:context.parent_task_id});}catch{/* Invalid optional mapping proof cannot authorize a variation. The archived task remains readable. */}}
   const coverage=shared?.coveredPages.length?{...shared,requestedTask:task,inputVersion:context.input_version}:null;
   return {...projection(row,task,run,context),origins,...(reviewedProgram?{reviewedProgram}:{}),...(selectedRecordOrigin?{selectedRecordOrigin}:{}),...(coverage?{coverage}:{}),...(coverageUnavailable?{coverageUnavailable:true}:{}),...(controls?{controls}:{}),...(savedOrigins.length>10?{originsTruncated:true}:{}),relatedIdeaIds:publicIds.slice(0,50),...(publicIds.length>50?{relatedIdeasTruncated:true}:{}),...(linkedProposalId?{linkedProposalId,linkedInputVersion:context.input_version,linkedParentTaskId:context.parent_task_id}:{})};
  };
  try{
   let body;
   if(method==='POST'){
    try{body=await boundedJSON(request);}catch{return reply({error:'The experiment file could not be read.'},400);}
    const limit=await (env.TASK_LIMIT||env.PROPOSAL_LIMIT).limit({key:request.headers.get('CF-Connecting-IP')||'unknown'});
    if(!limit?.success){headers['Retry-After']='60';return reply({error:'Please wait before trying again.',code:'rate-limited',retryAfterSeconds:60},429);}
   }
   const at=now().toISOString(),day=at.slice(0,10),retryAt=new Date(Date.parse(day+'T00:00:00.000Z')+86400000).toISOString();
   if(create){
    let task,taskJson,taskHash,createHash;
    try{
     exact(body,['proposalId','task','inputVersion','parentTaskId',...(Object.hasOwn(body,'origin')?['origin']:[]),...(Object.hasOwn(body,'preparationId')?['preparationId']:[])]);
     if(Object.hasOwn(body,'preparationId')&&(typeof body.preparationId!=='string'||!/^prep_[a-f0-9]{64}$/.test(body.preparationId)||Object.hasOwn(body,'origin')))throw Error();
     if(Object.hasOwn(body,'origin')&&!validRecordedOrigin(body.origin))throw Error();
     if(!PROPOSAL.test(body.proposalId)||!['raw','reviewed'].includes(body.inputVersion)||(body.parentTaskId!==null&&!HEX.test(body.parentTaskId)))throw Error();
     task=await L.checkIdentity(body.task);taskJson=L.stable(task);taskHash=await digest(taskJson);createHash=await digest(L.stable(body));
    }catch{return reply({error:'The experiment plan is invalid or changed.'},400);}
    let existing=await find(task.taskId);
    const proposal=await query('SELECT card_json FROM proposals WHERE id = ?',body.proposalId).first();
    if(!proposal)return reply({error:'Confirmed idea not found.'},404);
    const cardJson=L.stable(validateCard(proposal.card_json));
    if(body.parentTaskId&&!await find(body.parentTaskId))return reply({error:'Parent task not found.'},404);
    let reviewed=null,originId=null;
    if(body.origin){
     try{reviewed=await loadRecordPlan(body.origin,{fetcher});if(L.stable(reviewed.origin)!==L.stable(body.origin)||L.stable(reviewed.card)!==cardJson||L.stable(reviewed.task)!==taskJson||reviewed.inputVersion!==body.inputVersion||body.parentTaskId!==null)throw Error();originId=await digest(L.stable(reviewed.origin));}
     catch{return reply({error:'The reviewed origin, input pins, card or task could not be verified.'},422);}
    }
    let originWrite=null;
    const prepareOrigin=async()=>{if(reviewed&&!originWrite)originWrite=await prepareOriginWrite({db,reviewed,taskId:task.taskId,proposalId:body.proposalId,originId,at,day,finiteLimit:limits.tasks});return originWrite;};
    const originGate=()=>originWrite?.gate.sql||'',originArgs=()=>originWrite?.gate.args||[];
    const saveOrigin=async()=>{const write=await prepareOrigin();if(!write)return;if(write.statements.length)await db.batch(write.statements);await write.verify();};
    if(existing){
     const saved=await storedTask(existing);
     if(existing.task_hash!==taskHash||L.stable(saved)!==taskJson)return reply({error:'This computation identity has different task content.'},409);
    }
    const association=()=>query('SELECT * FROM local_task_ideas WHERE task_id=? AND proposal_id=?',task.taskId,body.proposalId).first();
    const compatible=link=>link.input_version===body.inputVersion&&link.parent_task_id===body.parentTaskId;
    const linked=await association();
    if(linked){
     if(!compatible(linked))return reply({error:'This idea already links the computation with a different input version or parent.'},409);
     // A previously linked pending task is not permission to bypass the new
     // reviewed prefix-evidence snapshot. Legacy idempotent links stay unchanged.
     if(body.preparationId&&!reviewed){const prepared=await query('SELECT basis_json FROM prepared_plans WHERE id=?',body.preparationId).first();if(prepared&&['pinned-domain-member-v1','authored-finite-member-v1','ordinary-derived-prefix-remainder-v1','record-derived-prefix-remainder-v1','record-strict-evidence-remainder-v1'].includes(JSON.parse(prepared.basis_json).kind)){
      let controls;try{controls=await controlsFor(task);}catch{return reply({error:'The implementation controls could not be verified. No experiment was saved.'},422);}
      const authorized=await authorizePreparation({db,preparationId:body.preparationId,proposalId:body.proposalId,card:JSON.parse(cardJson),task,inputVersion:body.inputVersion,parentTaskId:body.parentTaskId,controls,fetcher,loadAuthoredSource:sourceLoader,loadPinnedDomain,loadPinnedBundle});if(!authorized)return reply({error:'Review a freshly prepared plan before creating this experiment.'},409);if(authorized.reviewed){reviewed=authorized.reviewed;originId=await digest(L.stable(reviewed.origin));}
     }}
     existing=existing||await find(task.taskId);if(!existing)throw Error('Linked task unavailable');await saveOrigin();return reply(await view(existing,await storedTask(existing),body.proposalId,null,originId));
    }
    if(!reviewed){
     let controls;try{controls=await controlsFor(task);}catch{return reply({error:'The implementation controls could not be verified. No experiment was saved.'},422);}
     const authorized=await authorizePreparation({db,preparationId:body.preparationId,proposalId:body.proposalId,card:JSON.parse(cardJson),task,inputVersion:body.inputVersion,parentTaskId:body.parentTaskId,controls,fetcher,loadAuthoredSource:sourceLoader,loadPinnedDomain,loadPinnedBundle});
     if(!authorized)return reply({error:'Review a freshly prepared plan before creating this experiment.'},409);
     if(authorized.reviewed){reviewed=authorized.reviewed;originId=await digest(L.stable(reviewed.origin));}
    }
    // Identical bytes under the same already-verified input version can be reused.
    // A different version must independently match that version's official source.
    if(!reviewed&&(!existing||existing.input_version!==body.inputVersion)){
    const sourceController=new AbortController(),sourceTimer=setTimeout(()=>sourceController.abort(),20000);
    try{
     let fetched=0,next=0;
     const bundle=task.pages.length>40?await loadInputBundle({fetcher,signal:sourceController.signal,read:boundedJSON}):null;if(bundle&&L.stable(bundle.alphabet)!==L.stable(task.alphabet))throw Error();
     const worker=async()=>{
      try{
       while(next<task.pages.length){
        if(sourceController.signal.aborted)throw Error();
        const page=task.pages[next++];
        const response=bundle?null:await fetcher('https://jelliottdev.github.io/data/pages/'+page.id+'.json',{redirect:'manual',signal:sourceController.signal});
        if(response&&!response.ok)throw Error();const source=bundle?bundle.pages.get(page.id):await boundedJSON(response,512*1024);
        const text=body.inputVersion==='raw'?source.raw:source.reviewed_text;
        if(source.id!==page.id||typeof text!=='string'||text!==page.text)throw Error();
        fetched+=new TextEncoder().encode(text).length;if(fetched>MAX_BODY)throw Error();
       }
      }catch(error){sourceController.abort();throw error;}
     };
     await Promise.all(Array.from({length:Math.min(4,task.pages.length)},()=>worker()));
    }catch{return reply({error:'The selected manuscript text could not be verified.'},422);}
    finally{clearTimeout(sourceTimer);}
    }
    await prepareOrigin();
    await db.batch([query(`INSERT INTO local_tasks (id,task_hash,create_hash,proposal_id,card_json,task_json,input_version,parent_task_id,created_at,created_day)
     SELECT ?,?,?,?,?,?,?,?,?,? WHERE (SELECT COUNT(*) FROM local_tasks WHERE created_day=?)<?
     AND (SELECT COUNT(*) FROM local_task_ideas WHERE created_day=?)<?${originGate()} ON CONFLICT(id) DO NOTHING`,
     task.taskId,taskHash,createHash,body.proposalId,cardJson,taskJson,body.inputVersion,body.parentTaskId,at,day,day,limits.tasks,day,limits.taskIdeaLinks,...originArgs()),
     query(`INSERT INTO local_task_ideas (task_id,proposal_id,input_version,parent_task_id,created_at,created_day)
      SELECT ?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM local_tasks WHERE id=? AND task_hash=? AND task_json=?)
      AND (SELECT COUNT(*) FROM local_task_ideas WHERE created_day=?)<?${originGate()} ON CONFLICT(task_id,proposal_id) DO NOTHING`,
      task.taskId,body.proposalId,body.inputVersion,body.parentTaskId,at,day,task.taskId,taskHash,taskJson,day,limits.taskIdeaLinks,...originArgs()),...(originWrite?.statements||[])]);
    existing=await find(task.taskId);const accepted=await association();
    if(!existing||!accepted)return reply({error:'The daily experiment or idea-link limit has been reached.',code:'daily-quota',retryAt},429);
    if(!compatible(accepted))return reply({error:'This idea already links the computation with a different input version or parent.'},409);
    if(originWrite)await originWrite.verify();return reply(await view(existing,await storedTask(existing),body.proposalId,null,originId));
   }
   const row=await find(match[1]);if(!row)return reply({error:'Experiment not found.'},404);
   const context=selectedIdea?await query(`SELECT links.proposal_id,links.input_version,links.parent_task_id,links.created_at,p.card_json
    FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id
    JOIN proposals p ON p.id=links.proposal_id WHERE links.task_id=? AND links.proposal_id=?`,row.id,selectedIdea).first():await publicContext(row);
   if(!context)return reply({error:'Experiment not found.'},404);
   const task=await storedTask(row);
   if(comparisonRoute){const comparison=await boundaryComparison({db,task,inputVersion:context.input_version,discoverEvidence});return comparison?reply(comparison):reply({error:'This experiment has no supported boundary comparison.'},422);}
   if(method==='GET')return reply(await view(row,task,selectedIdea,context));
   let result,controls;
   try{
    exact(body,['result']);
    const authored=await query('SELECT COUNT(*) AS count FROM local_task_all_origins o JOIN research_ideas public ON public.proposal_id=o.proposal_id WHERE o.task_id=?',row.id).first();
    if(!Number.isSafeInteger(authored?.count)||authored.count<0)throw Error('Invalid reviewed origin count');
    if(!authored.count||task.criterion.kind==='language-score')controls=await controlsFor(task);
    result=await L.verify(task,body.result);
   }catch{return reply({error:'The implementation controls or results do not match this exact experiment.'},422);}
   const resultJson=L.stable(result),runId=await digest(resultJson);
   let saved=await query('SELECT * FROM local_task_results WHERE id=?',runId).first();
   if(!saved){await db.batch([query(`INSERT INTO local_task_results (id,task_id,result_json,created_at,created_day)
    SELECT ?,?,?,?,? WHERE (SELECT COUNT(*) FROM local_task_results WHERE created_day=?)<? ON CONFLICT(id) DO NOTHING`,runId,row.id,resultJson,at,day,day,limits.results)]);saved=await query('SELECT * FROM local_task_results WHERE id=?',runId).first();}
   if(!saved)return reply({error:'The daily result limit has been reached.',code:'daily-quota',retryAt},429);
   // Admission already independently replayed this exact result above. Read
   // back the committed bytes, not another execution of the same calculation.
   if(saved.task_id!==row.id||saved.id!==runId||saved.result_json!==resultJson)throw Error('Stored result mismatch');
   const savedResult=result;
   return reply({taskId:row.id,state:'results-verified',latestRun:{id:saved.id,createdAt:saved.created_at,result:savedResult},...(controls?{controls}:{}),verification:NOTICE});
  }catch(error){if(error.code==='daily-quota'){const day=now().toISOString().slice(0,10),retryAt=new Date(Date.parse(day+'T00:00:00.000Z')+86400000).toISOString();return reply({error:error.message,code:'daily-quota',retryAt},429);}return reply({error:'Local experiments are temporarily unavailable.'},503);}
 };
}
