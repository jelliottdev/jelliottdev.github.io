/* Fixed reviewed family, exact official inputs and independently replayed results. */
import F from '../../research-family.js';
import L from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import {loadInputBundle} from './official-inputs.mjs';
import {readFamilyEvidence} from './family-evidence.mjs';
import {sharedFamilyCoverage,readSharedFamilyCase} from './family-shared-coverage.mjs';

const FAMILY='deor-feedback-v1',MAX_BODY=2*1024*1024;
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(L.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
async function storedEvidence(row,expected){
 const result=JSON.parse(row.result_json);
 if(row.task_id!==expected.taskId||row.task_json!==L.stable(expected)||await hash(result)!==row.result_hash||!exact(result,['schema','taskId','engine','runnerVersion','metrics','matches','transformed'])||result.schema!==L.RESULT||result.taskId!==expected.taskId||result.engine!==L.ENGINE||result.runnerVersion!=='1'||!Array.isArray(result.matches)||result.matches.length!==1||!exact(result.matches[0],['page','matched'])||result.matches[0].page!==expected.pages[0].id||typeof result.matches[0].matched!=='boolean'||row.matched!==Number(result.matches[0].matched)||!Array.isArray(result.transformed)||result.transformed.length!==1||!exact(result.transformed[0],['page','text'])||result.transformed[0].page!==expected.pages[0].id||typeof result.transformed[0].text!=='string'||result.transformed[0].text.length>300000||!exact(result.metrics,['pages','runes','adjacentPairs','equalAdjacentPairs','ioc'])||result.metrics.pages!==1||!['runes','adjacentPairs','equalAdjacentPairs'].every(key=>Number.isSafeInteger(result.metrics[key])&&result.metrics[key]>=0)||result.metrics.runes>20000||result.metrics.equalAdjacentPairs>result.metrics.adjacentPairs||!Number.isFinite(result.metrics.ioc)||result.metrics.ioc<0||result.metrics.ioc>1||typeof row.created_at!=='string'||!Number.isFinite(Date.parse(row.created_at)))throw Error('Stored result identity is malformed');
 const values=Array.from(result.transformed[0].text).filter(ch=>expected.alphabet.some(a=>a.rune===ch)).map(ch=>expected.alphabet.findIndex(a=>a.rune===ch));
 if(result.matches[0].matched!==expected.criterion.values.every((value,i)=>values[i]===value))throw Error('Stored criterion is malformed');
 return result;
}
async function readJSON(message,max){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error('JSON required');
 const length=message.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>max))throw Error('Body exceeds bounds');
 const reader=message.body?.getReader();if(!reader)throw Error('Body required');const parts=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('Body exceeds bounds');}parts.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
export function createFamilyRunHandler({fetcher=globalThis.fetch,now=()=>new Date(),timeoutMs=20000}={}){
 if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>20000)throw Error('Invalid source deadline');
 return async function handle(request,env){
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let valid=false;try{valid=typeof env?.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN&&['https:','http:'].includes(new URL(env.SITE_ORIGIN).protocol);}catch{}
  if(!valid)return reply({error:'Family experiments are unavailable.'},503);
  if(request.headers.get('origin')!==env.SITE_ORIGIN)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=env.SITE_ORIGIN;
  const url=new URL(request.url),match=url.pathname.match(/^\/families\/deor-feedback-v1(?:\/(prepare|results)|\/cases\/([^/]+))?$/),action=match?.[2]?'case':match?.[1]||'snapshot';
  if(!match)return reply({error:'Not found.'},404);
  const revision=url.searchParams.get('revision');
  if(url.search&&(action!=='case'||[...url.searchParams.keys()].length!==1||!/^[a-f0-9]{64}$/.test(revision||'')))return reply({error:'Not found.'},404);
  let caseId=null;if(action==='case')try{caseId=decodeURIComponent(match[2]);if(caseId.length>200)throw Error();}catch{return reply({error:'Case not found.'},404);}
  const method=['snapshot','case'].includes(action)?'GET':'POST';
  if(request.method==='OPTIONS'){
   const fields=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!==method||fields.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':method+', OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});
  }
  if(request.method!==method)return reply({error:'Method is not allowed.'},405);
  if(!env.PROPOSALS?.prepare||!env.PROPOSALS?.batch||!env.TASK_LIMIT?.limit)return reply({error:'Family experiments are unavailable.'},503);
  if(request.signal.aborted)return reply({error:'The family request was cancelled. No coverage was saved.'},499);
  let body;
  if(method==='POST')try{body=await readJSON(request,action==='prepare'?16000:MAX_BODY);if(!exact(body,action==='prepare'?['revision','caseIds']:['plan','results','controls']))throw Error();}catch{return reply({error:'The family request could not be read.'},400);}
  try{
   if(!(await env.TASK_LIMIT.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   const db=env.PROPOSALS,query=(sql,...args)=>db.prepare(sql).bind(...args);
   if(action==='case'&&revision){
    const pinned=await readFamilyEvidence({db,familyId:FAMILY,revision,caseId});
    if(pinned){const {source}=pinned;return reply({familyId:FAMILY,revision,caseId,task:source.task,result:source.run.result,resultId:source.run.id,verifiedAt:source.run.createdAt});}
   }
   const controller=new AbortController(),cancel=()=>controller.abort(),timer=setTimeout(()=>controller.abort(),timeoutMs);request.signal.addEventListener('abort',cancel,{once:true});let bundle;
   try{const parsed=await loadInputBundle({fetcher,signal:controller.signal,read:readJSON});bundle={schema:'liberpedia-local-inputs-v1',alphabet:parsed.alphabet,pages:[...parsed.pages.values()]};}
   catch{return reply({error:'The official manuscript inputs could not be loaded.'},422);}finally{clearTimeout(timer);request.signal.removeEventListener('abort',cancel);}
   if(request.signal.aborted)return reply({error:'The family request was cancelled. No coverage was saved.'},499);
   // Validate and freeze the official source once per request. Each selected
   // case hashes only its own task, never all 75 source pages again.
   const preparer=await F.createPreparer(bundle),snapshot=preparer.snapshot,ids=new Set(F.caseIds(snapshot));
   if(action==='case'){
    if(revision&&revision!==snapshot.revision)return reply({error:'No verified result has been saved for this case and input snapshot.'},404);
    if(!ids.has(caseId))return reply({error:'Case not found.'},404);
    const row=await query('SELECT * FROM family_case_results WHERE family_id=? AND revision=? AND case_id=?',FAMILY,snapshot.revision,caseId).first();
    if(!row){
     const shared=await readSharedFamilyCase({db,preparer,caseId});
     if(!shared)return reply({error:'No verified result has been saved for this case.'},404);
     return reply({familyId:FAMILY,revision:snapshot.revision,caseId,source:shared.source});
    }
    const task=(await preparer.prepare([caseId])).cases[0].task,result=await storedEvidence(row,task);
    return reply({familyId:FAMILY,revision:snapshot.revision,caseId,task,result,resultId:row.result_hash,verifiedAt:row.created_at});
   }
   if(action==='snapshot'){
    const rows=(await query('SELECT * FROM family_case_results WHERE family_id=? AND revision=? ORDER BY case_id',FAMILY,snapshot.revision).all()).results;
    if(!Array.isArray(rows)||rows.length>snapshot.totalCases)throw Error('Stored coverage is malformed');
    const completed=[],matched=[],seen=new Set(),expectedTasks=new Map();
    for(const row of rows){
     if(!ids.has(row.case_id)||seen.has(row.case_id))throw Error('Stored case identity is malformed');seen.add(row.case_id);
    }
    for(let offset=0;offset<rows.length;offset+=12){
     const plan=await preparer.prepare(rows.slice(offset,offset+12).map(row=>row.case_id));
     for(const item of plan.cases)expectedTasks.set(item.id,item.task);
    }
    for(const row of rows){
     await storedEvidence(row,expectedTasks.get(row.case_id));
     completed.push(row.case_id);if(row.matched)matched.push(row.case_id);
    }
    const shared=await sharedFamilyCoverage({db,preparer});
    for(const id of shared.completed){if(seen.has(id)&&matched.includes(id)!==shared.matched.includes(id))throw Error('Conflicting saved family coverage');if(!seen.has(id)){completed.push(id);if(shared.matched.includes(id))matched.push(id);}}
    return reply({family:snapshot,coverage:{completed:completed.sort(),matched:matched.sort()}});
   }
   if(action==='prepare'){
    if(body.revision!==snapshot.revision)return reply({error:'The family inputs changed. Reload the family before preparing work.'},409);
    let plan;try{plan=await preparer.prepare(body.caseIds);}catch{return reply({error:'Choose one to twelve distinct supported cases.'},400);}
    const savedRows=(await query('SELECT case_id FROM family_case_results WHERE family_id=? AND revision=?',FAMILY,snapshot.revision).all()).results;
    if(!Array.isArray(savedRows))throw Error('Saved coverage unavailable');
    const shared=await sharedFamilyCoverage({db,preparer}),covered=new Set([...savedRows.map(row=>row.case_id),...shared.completed]);
    if(plan.cases.some(item=>covered.has(item.id)))return reply({error:'Some of these cases already have saved results. Reload the family to choose the remaining pages.'},409);
    const controls=[];for(const item of plan.cases)controls.push({caseId:item.id,suite:await Controls.prepare(item.task)});
    return reply({plan,controls});
   }
   let plan;try{plan=await preparer.validatePlan(body.plan);}catch{return reply({error:'The family plan does not match the current official inputs.'},422);}
   if(!Array.isArray(body.results)||!Array.isArray(body.controls)||body.results.length!==plan.cases.length||body.controls.length!==plan.cases.length)return reply({error:'Submit complete results and controls for this bounded batch.'},422);
   const resultMap=new Map(),controlMap=new Map();
   try{
    for(const item of body.results){if(!exact(item,['caseId','result'])||resultMap.has(item.caseId))throw Error();resultMap.set(item.caseId,item.result);}
    for(const item of body.controls){if(!exact(item,['caseId','results'])||controlMap.has(item.caseId))throw Error();controlMap.set(item.caseId,item.results);}
    if(plan.cases.some(item=>!resultMap.has(item.id)||!controlMap.has(item.id)))throw Error();
   }catch{return reply({error:'The submitted case identities do not match this batch.'},422);}
   const at=now().toISOString(),day=at.slice(0,10),existing=new Map();
   for(const item of plan.cases){const row=await query('SELECT * FROM family_case_results WHERE family_id=? AND revision=? AND case_id=?',FAMILY,plan.revision,item.id).first();if(row)existing.set(item.id,row);}
   const quota=await query('SELECT COUNT(*) AS count FROM family_case_results WHERE created_day=?',day).first();
   if(!Number.isSafeInteger(quota?.count)||quota.count<0)throw Error('Invalid stored quota');
   if(quota.count+plan.cases.length-existing.size>1000)return reply({error:'The daily family result limit has been reached. Your local results can be submitted later.'},429);
   const verified=[];
   try{
    for(const item of plan.cases){
     const suite=await Controls.prepare(item.task),submitted=controlMap.get(item.id);
     if(!Array.isArray(submitted)||submitted.length!==suite.cases.length)throw Error();const controls=new Map();
     for(const control of submitted){if(!exact(control,['id','result'])||controls.has(control.id))throw Error();controls.set(control.id,control.result);}
     for(const fixture of suite.cases)if(!controls.has(fixture.id)||await hash(controls.get(fixture.id))!==fixture.expectedResultSha256)throw Error();
    }
    // Reject every malformed control before spending CPU on any manuscript.
    for(const item of plan.cases){
     const result=await L.verify(item.task,resultMap.get(item.id)),resultJson=L.stable(result),resultHash=await hash(result),taskJson=L.stable(item.task),matched=Number(result.matches[0].matched);
     const prior=existing.get(item.id);if(prior&&(prior.task_id!==item.task.taskId||prior.task_json!==taskJson||prior.result_hash!==resultHash||prior.result_json!==resultJson||prior.matched!==matched))throw Error();
     verified.push({id:item.id,taskId:item.task.taskId,taskJson,resultHash,resultJson,matched});
    }
   }catch{return reply({error:'A control or result does not match this exact family batch. No coverage was saved.'},422);}
   if(request.signal.aborted)return reply({error:'The family request was cancelled. No coverage was saved.'},499);
   try{
    const inserts=verified.filter(item=>!existing.has(item.id)).map(item=>query(`INSERT INTO family_case_results(family_id,revision,case_id,task_id,task_json,result_hash,result_json,matched,created_at,created_day)
     SELECT ?,?,?,?,?,?,?,?,?,? WHERE NOT EXISTS(SELECT 1 FROM family_case_results WHERE family_id=? AND revision=? AND case_id=?)`,FAMILY,plan.revision,item.id,item.taskId,item.taskJson,item.resultHash,item.resultJson,item.matched,at,day,FAMILY,plan.revision,item.id));
    if(inserts.length)await db.batch(inserts);
   }catch(error){if(String(error?.message||'').includes('family daily result limit'))return reply({error:'The daily family result limit has been reached. No coverage was saved.'},429);throw error;}
   for(const item of verified){const row=await query('SELECT * FROM family_case_results WHERE family_id=? AND revision=? AND case_id=?',FAMILY,plan.revision,item.id).first();if(!row||row.result_hash!==item.resultHash||row.result_json!==item.resultJson||row.task_json!==item.taskJson||row.task_id!==item.taskId||row.matched!==item.matched)throw Error('Saved family batch mismatch');}
   return reply({familyId:FAMILY,revision:plan.revision,accepted:verified.map(item=>item.id),matched:verified.filter(item=>item.matched).map(item=>item.id)});
  }catch{return reply({error:'Family experiments are temporarily unavailable.'},503);}
 };
}
