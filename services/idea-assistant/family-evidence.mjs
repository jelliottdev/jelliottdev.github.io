/* Public verified family receipts, with no copied proposals or target replay. */
import E from '../../local-experiment.js';
import Family from '../../research-family.js';
import Evidence from '../../computation-evidence.js';
const FAMILY='deor-feedback-v1',HEX=/^[a-f0-9]{64}$/;
const hash=async(value,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
async function checked(row,cryptoAPI){
 if(!row||row.family_id!==FAMILY||!HEX.test(row.revision)||!HEX.test(row.task_id)||!HEX.test(row.result_hash)||typeof row.case_id!=='string'||typeof row.task_json!=='string'||typeof row.result_json!=='string'||typeof row.created_at!=='string'||!Number.isFinite(Date.parse(row.created_at))||![0,1].includes(row.matched))throw Error('The saved family receipt is malformed.');
 const task=JSON.parse(row.task_json),result=JSON.parse(row.result_json),pageId=row.case_id.slice(-6),configuration=row.case_id.slice(0,-8);
 if(task.taskId!==row.task_id||E.stable(task)!==row.task_json)throw Error('The saved family task identity changed.');
 const body={schema:'liberpedia-family-plan-v1',familyId:FAMILY,revision:row.revision,cases:[{id:row.case_id,configuration,pageId,task}]};
 await Family.validateExecutionPlan({...body,planId:await hash(body,cryptoAPI)},cryptoAPI);
 const source={task,inputVersion:'raw',run:{id:row.result_hash,createdAt:row.created_at,result}};
 await Evidence.compare(task,'raw',[source],cryptoAPI);
 if(row.matched!==Number(result.matches[0].matched))throw Error('The saved family verdict changed.');
 return {source,familySource:{taskId:row.task_id,familyId:FAMILY,revision:row.revision,caseId:row.case_id}};
}
// The finite-domain lookup applies the same receipt checks after one bulk query.
export const validateFamilyReceipt=checked;
export async function readFamilyEvidence({db,familyId,revision,caseId,taskId,resultId,crypto:cryptoAPI=globalThis.crypto}){
 if(typeof db?.prepare!=='function'||familyId!==FAMILY||!HEX.test(revision)||typeof caseId!=='string'||caseId.length>200||taskId!==undefined&&!HEX.test(taskId)||resultId!==undefined&&!HEX.test(resultId))throw Error('The family evidence reference is invalid.');
 const row=await db.prepare('SELECT * FROM family_case_results WHERE family_id=? AND revision=? AND case_id=?').bind(familyId,revision,caseId).first();if(!row)return null;
 if(taskId!==undefined&&row.task_id!==taskId||resultId!==undefined&&row.result_hash!==resultId)throw Error('The family evidence reference identifies another computation.');
 return checked(row,cryptoAPI);
}
export async function resolveFamilyEvidence({db,taskId,resultId,inputVersion,createdAt,crypto:cryptoAPI=globalThis.crypto}){
 if(inputVersion!=='raw')return null;
 if(typeof db?.prepare!=='function'||!HEX.test(taskId)||!HEX.test(resultId))throw Error('The pinned family source reference is invalid.');
 if(createdAt!==undefined&&(typeof createdAt!=='string'||!Number.isFinite(Date.parse(createdAt))))throw Error('The pinned family timestamp is invalid.');
 const row=createdAt===undefined?await db.prepare('SELECT * FROM family_case_results WHERE family_id=? AND task_id=? AND result_hash=? ORDER BY created_at DESC,revision DESC,case_id ASC LIMIT 1').bind(FAMILY,taskId,resultId).first():await db.prepare('SELECT * FROM family_case_results WHERE family_id=? AND task_id=? AND result_hash=? AND created_at=? ORDER BY revision DESC,case_id ASC LIMIT 1').bind(FAMILY,taskId,resultId,createdAt).first();
 return row?checked(row,cryptoAPI):null;
}
export async function findFamilyEvidence({db,task,inputVersion,crypto:cryptoAPI=globalThis.crypto}){
 if(inputVersion!=='raw')return {sources:[],familySources:[],truncated:false};
 await Evidence.describe(task,inputVersion,cryptoAPI);
 const value=await db.prepare(`SELECT saved.* FROM family_case_results saved
  WHERE saved.family_id=? AND json_extract(saved.task_json,'$.engine')=?
   AND json_extract(saved.task_json,'$.alphabet')=? AND json_extract(saved.task_json,'$.steps')=?
   AND json_extract(saved.task_json,'$.criterion')=?
   AND EXISTS(SELECT 1 FROM json_each(?) requested JOIN json_each(saved.task_json,'$.pages') actual
    ON json_extract(requested.value,'$.id')=json_extract(actual.value,'$.id')
     AND json_extract(requested.value,'$.text')=json_extract(actual.value,'$.text'))
  ORDER BY saved.created_at DESC,saved.revision DESC,saved.case_id ASC LIMIT 101`)
 .bind(FAMILY,task.engine,E.stable(task.alphabet),E.stable(task.steps),E.stable(task.criterion),E.stable(task.pages)).all();
 const rows=value?.results;if(!Array.isArray(rows)||rows.length>101)throw Error('Stored family candidates are malformed.');
 const sources=[],familySources=[],seen=new Set();let bytes=0;
 for(const row of rows.slice(0,100)){
  bytes+=(typeof row.task_json==='string'?row.task_json.length:0)+(typeof row.result_json==='string'?row.result_json.length:0);if(bytes>16000000)throw Error('Family evidence exceeds the bounded lookup size.');
  const receipt=await checked(row,cryptoAPI);if(seen.has(receipt.source.task.taskId))continue;seen.add(receipt.source.task.taskId);sources.push(receipt.source);familySources.push(receipt.familySource);
 }
 return {sources,familySources,truncated:rows.length===101};
}
