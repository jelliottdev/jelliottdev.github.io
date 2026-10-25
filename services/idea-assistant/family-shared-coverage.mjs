/* Read existing public task evidence into a finite family, without copying runs. */
import L from '../../local-experiment.js';
import F from '../../research-family.js';
import Evidence from '../../computation-evidence.js';

const HEX=/^[a-f0-9]{64}$/;
const hash=async(value,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(L.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');
async function lookup({db,preparer,crypto:cryptoAPI=globalThis.crypto},onlyCaseId=null,proofCases=null){
 if(typeof db?.prepare!=='function'||typeof preparer?.prepare!=='function'||preparer.snapshot?.id!=='deor-feedback-v1'||!HEX.test(preparer.snapshot.revision)||preparer.snapshot.configurations?.length!==18||preparer.snapshot.pages?.length!==55)throw Error('Shared family evidence lookup is unavailable.');
 const view=JSON.parse(L.stable(preparer.snapshot)),allowed=new Set(F.caseIds(view)),records=new Map();let bytes=0;
 if(onlyCaseId!==null&&!allowed.has(onlyCaseId))throw Error('The requested shared family case is invalid.');
 if(proofCases!==null&&(!(proofCases instanceof Set)||[...proofCases].some(id=>!allowed.has(id))))throw Error('The requested family question cases are invalid.');
 for(const config of view.configurations){
  if(onlyCaseId!==null&&!onlyCaseId.startsWith(config.id+'--'))continue;
  const samplePlan=await preparer.prepare([config.id+'--'+view.pages[0].id]);await F.validateExecutionPlan(samplePlan,cryptoAPI);
  const sample=samplePlan.cases[0].task;
  const requested=await L.prepare({...sample,title:'Shared evidence lookup: '+config.id,pages:view.pages},cryptoAPI);
  const found=await db.prepare(`SELECT t.id AS task_id,t.task_hash,t.task_json,t.input_version,
   r.id AS result_id,r.result_json,r.created_at
   FROM local_tasks t JOIN local_task_results r ON r.id=(
    SELECT latest.id FROM local_task_results latest WHERE latest.task_id=t.id
    ORDER BY latest.created_at DESC,latest.id DESC LIMIT 1)
   WHERE t.input_version='raw' AND json_extract(t.task_json,'$.engine')=?
    AND json_extract(t.task_json,'$.alphabet')=? AND json_extract(t.task_json,'$.steps')=?
    AND json_extract(t.task_json,'$.criterion')=?
    AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id
     WHERE links.task_id=t.id AND links.input_version='raw')
   ORDER BY t.id ASC LIMIT 101`)
   .bind(requested.engine,L.stable(requested.alphabet),L.stable(requested.steps),L.stable(requested.criterion)).all();
  if(!Array.isArray(found?.results)||found.results.length>101)throw Error('Shared family evidence candidates are malformed.');
  if(found.results.length>100)throw Error('Shared family evidence exceeds the 100-source lookup limit for one configuration.');
  const sources=[],byTask=new Map();
  for(const row of found.results){
   if(!row||typeof row.task_id!=='string'||!HEX.test(row.task_id)||byTask.has(row.task_id)||typeof row.task_hash!=='string'||!HEX.test(row.task_hash)||typeof row.result_id!=='string'||!HEX.test(row.result_id)||typeof row.task_json!=='string'||typeof row.result_json!=='string'||row.input_version!=='raw')throw Error('Shared family evidence receipt is malformed.');
   bytes+=new TextEncoder().encode(row.task_json).length+new TextEncoder().encode(row.result_json).length;
   if(bytes>16000000)throw Error('Shared family evidence exceeds the 16 MB lookup limit.');
   const task=JSON.parse(row.task_json),result=JSON.parse(row.result_json);
   if(task.taskId!==row.task_id||await hash(task,cryptoAPI)!==row.task_hash)throw Error('Shared family source task identity changed.');
   const source={task,inputVersion:'raw',run:{id:row.result_id,createdAt:row.created_at,result}};sources.push(source);byTask.set(task.taskId,source);
  }
  if(!sources.length)continue;
  const comparison=await Evidence.compare(requested,'raw',sources,cryptoAPI);
  for(const ref of comparison.evidence){
   const source=byTask.get(ref.taskId);
   for(const pageId of ref.pages){
    const caseId=config.id+'--'+pageId;if(!allowed.has(caseId))throw Error('Shared evidence refers to a case outside this family.');
    if(proofCases!==null&&!proofCases.has(caseId))continue;
    const output=source.run.result.transformed.find(page=>page.page===pageId),match=source.run.result.matches.find(page=>page.page===pageId);
    const signature=L.stable({text:output.text,matched:match.matched}),candidate={caseId,taskId:ref.taskId,resultId:ref.resultId,createdAt:ref.createdAt},existing=records.get(caseId);
    if(existing&&existing.signature!==signature)throw Error('Saved public computations disagree on the same family case.');
    if(!existing||candidate.taskId.localeCompare(existing.source.taskId)<0||candidate.taskId===existing.source.taskId&&candidate.resultId.localeCompare(existing.source.resultId)<0)records.set(caseId,{signature,matched:match.matched,source:candidate,...(proofCases!==null?{proof:source}:{})});
   }
  }
 }
 const completed=[...records.keys()].sort();
 return {completed,matched:completed.filter(id=>records.get(id).matched),sources:completed.map(id=>records.get(id).source),...(proofCases!==null?{proofs:completed.map(caseId=>({familyId:view.id,revision:view.revision,caseId,source:records.get(caseId).proof}))}:{})};
}
export async function sharedFamilyCoverage(options){return lookup(options);}
export async function sharedFamilyQuestionEvidence(options,caseIds){
 if(!Array.isArray(caseIds)||caseIds.length>990||new Set(caseIds).size!==caseIds.length)throw Error('Invalid question case selection.');
 return lookup(options,null,new Set(caseIds));
}
export async function readSharedFamilyCase({db,preparer,caseId,crypto:cryptoAPI=globalThis.crypto}){
 const coverage=await lookup({db,preparer,crypto:cryptoAPI},caseId),reference=coverage.sources.find(item=>item.caseId===caseId);if(!reference)return null;
 const row=await db.prepare(`SELECT t.id AS task_id,t.task_hash,t.task_json,t.input_version,r.id AS result_id,r.result_json,r.created_at
  FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id AND r.id=?
  WHERE t.id=? AND t.input_version='raw' AND EXISTS(SELECT 1 FROM local_task_ideas links
   JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version='raw')`)
  .bind(reference.resultId,reference.taskId).first();
 if(!row||row.task_id!==reference.taskId||row.result_id!==reference.resultId||row.created_at!==reference.createdAt||row.input_version!=='raw'||!HEX.test(row.task_hash)||typeof row.task_json!=='string'||typeof row.result_json!=='string')throw Error('The original shared family receipt is unavailable.');
 const task=JSON.parse(row.task_json),result=JSON.parse(row.result_json);
 if(task.taskId!==row.task_id||await hash(task,cryptoAPI)!==row.task_hash)throw Error('The original shared family task identity changed.');
 const source={task,inputVersion:'raw',run:{id:row.result_id,createdAt:row.created_at,result}},plan=await preparer.prepare([caseId]),comparison=await Evidence.compare(plan.cases[0].task,'raw',[source],cryptoAPI);
 if(comparison.coveredPages.length!==1||comparison.coveredPages[0]!==plan.cases[0].pageId)throw Error('The original receipt does not cover this family case.');
 return {source,reference};
}
