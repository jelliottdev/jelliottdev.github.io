/* Read-only reuse of public, immutable, saved computation evidence. */
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import {findFamilyEvidence,resolveFamilyEvidence} from './family-evidence.mjs';

const HEX=/^[a-f0-9]{64}$/;
const IDEA=/^p_[a-f0-9]{64}$/;
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const digest=async(value,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
export async function findEvidence({db,task,inputVersion,crypto:cryptoAPI=globalThis.crypto}){
 if(typeof db?.prepare!=='function')throw Error('Computation evidence storage is unavailable.');
 await Evidence.describe(task,inputVersion,cryptoAPI);
 // Keep title and batch scope out of the protocol lookup. Both the origin and
 // public association must name this input version; otherwise omit the source
 // conservatively rather than repurpose its provenance.
 const value=await db.prepare(`SELECT t.id AS task_id,t.task_hash,t.task_json,t.input_version,
   r.id AS result_id,r.result_json,r.created_at
  FROM local_tasks t JOIN local_task_results r ON r.id=(
   SELECT latest.id FROM local_task_results latest WHERE latest.task_id=t.id
   ORDER BY latest.created_at DESC,latest.id DESC LIMIT 1)
  WHERE t.input_version=? AND json_extract(t.task_json,'$.engine')=?
   AND json_extract(t.task_json,'$.alphabet')=? AND json_extract(t.task_json,'$.steps')=?
   AND json_extract(t.task_json,'$.criterion')=?
   AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id
    WHERE links.task_id=t.id AND links.input_version=?)
  ORDER BY r.created_at DESC,r.id DESC,t.id ASC LIMIT 101`)
 .bind(inputVersion,task.engine,E.stable(task.alphabet),E.stable(task.steps),E.stable(task.criterion),inputVersion).all();
 const rows=value?.results;if(!Array.isArray(rows)||rows.length>101)throw Error('Stored computation candidates are malformed.');
 const sources=[],seen=new Set();let bytes=0;
 for(const row of rows.slice(0,100)){
  if(!row||!HEX.test(row.task_id)||seen.has(row.task_id)||!HEX.test(row.task_hash)||!HEX.test(row.result_id)||row.input_version!==inputVersion||typeof row.task_json!=='string'||typeof row.result_json!=='string')throw Error('Stored computation evidence identity is malformed.');
  seen.add(row.task_id);bytes+=row.task_json.length+row.result_json.length;if(bytes>16000000)throw Error('Stored computation evidence exceeds the bounded lookup size.');
  const saved=JSON.parse(row.task_json),result=JSON.parse(row.result_json);
  if(saved.taskId!==row.task_id||await digest(saved,cryptoAPI)!==row.task_hash)throw Error('Stored computation task differs from its immutable identity.');
  sources.push({task:saved,inputVersion:row.input_version,run:{id:row.result_id,createdAt:row.created_at,result}});
 }
 const family=await findFamilyEvidence({db,task,inputVersion,crypto:cryptoAPI}),familySources=[];
 for(const source of family.sources)if(!seen.has(source.task.taskId)){seen.add(source.task.taskId);sources.push(source);familySources.push(family.familySources.find(item=>item.taskId===source.task.taskId));}
 const comparison=await Evidence.compare(task,inputVersion,sources,cryptoAPI);
 // Retain a bounded proof, rather than every duplicate title/batch that repeats
 // it. Prefer one exact whole-task witness; otherwise each retained source must
 // add at least one requested page, so there can be at most 75 receipts.
 const represented=new Set(),proof=[];
 const candidates=comparison.evidence.slice().sort((a,b)=>Number(b.taskId===comparison.exactTaskId)-Number(a.taskId===comparison.exactTaskId)||a.taskId.localeCompare(b.taskId)||a.resultId.localeCompare(b.resultId));
 for(const item of candidates)if(item.pages.some(id=>!represented.has(id))){proof.push(item);item.pages.forEach(id=>represented.add(id));}
 const retained=new Set(proof.map(item=>item.taskId));
 const canonicalProof=await Evidence.compare(task,inputVersion,sources.filter(item=>retained.has(item.task.taskId)),cryptoAPI);
 const retainedFamilies=familySources.filter(item=>retained.has(item.taskId)).sort((a,b)=>a.taskId.localeCompare(b.taskId));
 return {...canonicalProof,truncated:rows.length===101||family.truncated,...(retainedFamilies.length?{familySources:retainedFamilies}:{})};
}

export async function rememberEvidence({db,proposalId,task,inputVersion,coverage,createdAt,crypto:cryptoAPI=globalThis.crypto}){
 if(!IDEA.test(proposalId)||typeof createdAt!=='string'||!Number.isFinite(Date.parse(createdAt))||new Date(createdAt).toISOString()!==createdAt||typeof db?.prepare!=='function')throw Error('The requested computation receipt is invalid.');
 const frozen=JSON.parse(E.stable(task));await Evidence.describe(frozen,inputVersion,cryptoAPI);
 if(!await db.prepare('SELECT id FROM proposals WHERE id=?').bind(proposalId).first())throw Error('The requested computation has no confirmed idea.');
 // coverage is deliberately not saved: it can change as other public runs land.
 // Only the exact source-bound request is durable, never a cached completion flag.
 void coverage;
 const text=E.stable(frozen),taskHash=await digest(frozen,cryptoAPI);
 const previous=await db.prepare('SELECT * FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?').bind(proposalId,frozen.taskId).first();
 if(previous&&(previous.requested_task_json!==text||previous.requested_task_hash!==taskHash||previous.input_version!==inputVersion))throw Error('The frozen request already has a different input context.');
 await db.prepare(`INSERT INTO idea_computation_evidence(proposal_id,requested_task_id,requested_task_json,requested_task_hash,input_version,created_at)
  VALUES(?,?,?,?,?,?) ON CONFLICT(proposal_id,requested_task_id) DO UPDATE SET created_at=excluded.created_at
  WHERE idea_computation_evidence.requested_task_json=excluded.requested_task_json
   AND idea_computation_evidence.requested_task_hash=excluded.requested_task_hash
   AND idea_computation_evidence.input_version=excluded.input_version`)
 .bind(proposalId,frozen.taskId,text,taskHash,inputVersion,createdAt).run();
 const saved=await db.prepare('SELECT * FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?').bind(proposalId,frozen.taskId).first();
 if(!saved||saved.requested_task_json!==text||saved.requested_task_hash!==taskHash||saved.input_version!==inputVersion)throw Error('The frozen request could not be saved consistently.');
 return {requestedTask:frozen,inputVersion};
}

export async function readIdeaEvidence({db,proposalId,taskId,crypto:cryptoAPI=globalThis.crypto}){
 if(!IDEA.test(proposalId)||typeof db?.prepare!=='function'||taskId!==undefined&&!HEX.test(taskId))throw Error('The idea evidence reference is invalid.');
 const row=taskId===undefined?await db.prepare('SELECT * FROM idea_computation_evidence WHERE proposal_id=? ORDER BY created_at DESC,requested_task_id DESC LIMIT 1').bind(proposalId).first():await db.prepare('SELECT * FROM idea_computation_evidence WHERE proposal_id=? AND requested_task_id=?').bind(proposalId,taskId).first();if(!row)return null;
 if(typeof row.requested_task_json!=='string'||!HEX.test(row.requested_task_hash)||!['raw','reviewed'].includes(row.input_version)||typeof row.created_at!=='string'||!Number.isFinite(Date.parse(row.created_at)))throw Error('The saved requested computation is malformed.');
 const task=JSON.parse(row.requested_task_json);await Evidence.describe(task,row.input_version,cryptoAPI);
 if(task.taskId!==row.requested_task_id||await digest(task,cryptoAPI)!==row.requested_task_hash)throw Error('The saved requested computation identity changed.');
 return {...await findEvidence({db,task,inputVersion:row.input_version,crypto:cryptoAPI}),requestedTask:task,inputVersion:row.input_version};
}

/* Recheck the precise immutable source receipts named by a preparation basis.
 * Newer unrelated results cannot silently replace these pinned sources. */
export async function checkedEvidence({db,task,inputVersion,evidence,crypto:cryptoAPI=globalThis.crypto}){
 await Evidence.describe(task,inputVersion,cryptoAPI);
 if(typeof db?.prepare!=='function'||!Array.isArray(evidence)||evidence.length>75)throw Error('The pinned computation evidence is malformed.');
 const sources=[],seen=new Set();
 for(const ref of evidence){
  if(!exact(ref,['taskId','resultId','pages','createdAt'])||!HEX.test(ref.taskId)||!HEX.test(ref.resultId)||seen.has(ref.taskId)||!Array.isArray(ref.pages)||ref.pages.length<1||ref.pages.length>75||new Set(ref.pages).size!==ref.pages.length||ref.pages.some(id=>typeof id!=='string')||typeof ref.createdAt!=='string'||!Number.isFinite(Date.parse(ref.createdAt)))throw Error('The pinned source reference is malformed.');
  seen.add(ref.taskId);
  const row=await db.prepare(`SELECT t.id AS task_id,t.task_hash,t.task_json,t.input_version,r.id AS result_id,r.result_json,r.created_at
   FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id AND r.id=?
   WHERE t.id=? AND t.input_version=? AND EXISTS(SELECT 1 FROM local_task_ideas links
    JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`)
  .bind(ref.resultId,ref.taskId,inputVersion,inputVersion).first();
  if(!row||row.created_at!==ref.createdAt){
   const family=await resolveFamilyEvidence({db,taskId:ref.taskId,resultId:ref.resultId,inputVersion,createdAt:ref.createdAt,crypto:cryptoAPI});
   if(!family)throw Error('Pinned public computation evidence is unavailable.');sources.push(family.source);continue;
  }
  if(row.task_id!==ref.taskId||row.result_id!==ref.resultId||!HEX.test(row.task_hash)||typeof row.task_json!=='string'||typeof row.result_json!=='string'||row.input_version!==inputVersion)throw Error('Pinned public computation evidence is unavailable.');
  const saved=JSON.parse(row.task_json);if(saved.taskId!==row.task_id||await digest(saved,cryptoAPI)!==row.task_hash)throw Error('The pinned source task identity changed.');
  sources.push({task:saved,inputVersion,run:{id:row.result_id,createdAt:row.created_at,result:JSON.parse(row.result_json)}});
 }
 const comparison=await Evidence.compare(task,inputVersion,sources,cryptoAPI);
 const sorted=evidence.slice().sort((a,b)=>a.taskId.localeCompare(b.taskId)||a.resultId.localeCompare(b.resultId));
 if(E.stable(comparison.evidence)!==E.stable(sorted))throw Error('The pinned evidence claims different covered pages.');
 return comparison;
}
