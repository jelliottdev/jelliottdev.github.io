/* Read-only candidates for derived prefix evaluation; hashes are not a replay verdict.
 * lookupComplete describes only this bounded public-local-tasks provider lookup.
 * It never establishes global absence or new work: other providers must be
 * considered separately, and every candidate needs client replay before use.
 */
import E from '../../local-experiment.js';
import Relations from '../../computation-evidence.js';
import Json from '../../finite-json.js';
export const LIMITS=Object.freeze({candidateRows:1024,sources:75,bytes:8*1024*1024});
const HEX=/^[a-f0-9]{64}$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable);
const hash=async(v,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
export async function findPrefixEvaluationSources(options){
 const keys=['db','task','inputVersion',...(options&&Object.hasOwn(options,'crypto')?['crypto']:[])];if(!exact(options,keys))throw Error('Prefix source lookup needs explicit database, task and input version.');
 const {db,crypto:cryptoAPI=globalThis.crypto}=options,input=Json.capture({task:options.task,inputVersion:options.inputVersion},{maxBytes:2*1024*1024,maxDepth:20,maxNodes:100000}),{task,inputVersion}=input;
 if(!db?.prepare||!['raw','reviewed'].includes(inputVersion))throw Error('Public prefix source lookup is unavailable.');await E.checkIdentity(task,cryptoAPI);if(task.criterion.kind!=='exact-prefix')throw Error('The target must request an exact prefix.');
 const scope=E.stable(task.pages),alphabet=E.stable(task.alphabet),steps=E.stable(task.steps),wanted=new Map(task.pages.map(p=>[p.id,p.text]));
 const raw=await db.prepare(`SELECT t.id AS task_id,t.task_hash,r.id AS result_id,r.created_at,
  json_array_length(t.task_json,'$.pages') AS source_page_count,
  length(CAST(t.task_json AS BLOB))+length(CAST(r.result_json AS BLOB)) AS source_bytes,
  (SELECT json_group_array(json_extract(requested.value,'$.id')) FROM json_each(?) requested
   WHERE EXISTS(SELECT 1 FROM json_each(t.task_json,'$.pages') saved
    WHERE json_extract(saved.value,'$.id')=json_extract(requested.value,'$.id')
     AND json_extract(saved.value,'$.text')=json_extract(requested.value,'$.text'))) AS matching_pages
 FROM local_tasks t JOIN local_task_results r ON r.id=(SELECT latest.id FROM local_task_results latest WHERE latest.task_id=t.id ORDER BY latest.created_at DESC,latest.id DESC LIMIT 1)
 WHERE t.input_version=? AND json_extract(t.task_json,'$.engine')=? AND json_extract(t.task_json,'$.alphabet')=? AND json_extract(t.task_json,'$.steps')=?
  AND json_extract(t.task_json,'$.criterion.kind') IN ('measurement','exact-prefix')
  AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)
  AND EXISTS(SELECT 1 FROM json_each(?) requested JOIN json_each(t.task_json,'$.pages') saved
   ON json_extract(saved.value,'$.id')=json_extract(requested.value,'$.id') AND json_extract(saved.value,'$.text')=json_extract(requested.value,'$.text'))
 ORDER BY r.created_at DESC,r.id DESC,t.id LIMIT 1025`).bind(scope,inputVersion,task.engine,alphabet,steps,inputVersion,scope).all();
 const rows=Json.capture(raw?.results,{maxBytes:2*1024*1024,maxDepth:6,maxNodes:20000});if(!Array.isArray(rows)||rows.length>LIMITS.candidateRows+1)throw Error('The prefix candidate index exceeds its bound.');
 let lookupComplete=rows.length<=LIMITS.candidateRows;const seen=new Set(),metadata=[];
 for(const row of rows.slice(0,LIMITS.candidateRows)){
  if(!exact(row,['task_id','task_hash','result_id','created_at','source_page_count','source_bytes','matching_pages'])||!HEX.test(row.task_id)||!HEX.test(row.task_hash)||!HEX.test(row.result_id)||seen.has(row.task_id)||typeof row.created_at!=='string'||!Number.isFinite(Date.parse(row.created_at))||!Number.isSafeInteger(row.source_page_count)||row.source_page_count<1||row.source_page_count>75||!Number.isSafeInteger(row.source_bytes)||row.source_bytes<1||typeof row.matching_pages!=='string')throw Error('A prefix source candidate is malformed.');
  seen.add(row.task_id);const pages=JSON.parse(row.matching_pages);if(!Array.isArray(pages)||!pages.length||pages.length>task.pages.length||new Set(pages).size!==pages.length||pages.some(id=>!wanted.has(id)))throw Error('A prefix source intersection is malformed.');metadata.push({...row,pages,exact:pages.length===task.pages.length&&row.source_page_count===task.pages.length});
 }
 metadata.sort((a,b)=>Number(b.exact)-Number(a.exact)||a.task_id.localeCompare(b.task_id)||a.result_id.localeCompare(b.result_id));
 const selected=[],covered=new Set();let plannedBytes=0;
 for(const item of metadata){if(!item.pages.some(id=>!covered.has(id)))continue;if(selected.length>=LIMITS.sources||plannedBytes+item.source_bytes>LIMITS.bytes-65536){lookupComplete=false;continue;}selected.push(item);plannedBytes+=item.source_bytes;item.pages.forEach(id=>covered.add(id));}
 const sources=[],sourceLocations=[];let bytes=0;
 if(selected.length){
  const fetched=await db.prepare(`SELECT t.id AS task_id,t.task_hash,t.task_json,t.input_version,r.id AS result_id,r.result_json,r.created_at
   FROM json_each(?) pin JOIN local_tasks t ON t.id=json_extract(pin.value,'$.task_id') AND t.task_hash=json_extract(pin.value,'$.task_hash')
   JOIN local_task_results r ON r.task_id=t.id AND r.id=json_extract(pin.value,'$.result_id') AND r.created_at=json_extract(pin.value,'$.created_at')
   WHERE length(CAST(t.task_json AS BLOB))+length(CAST(r.result_json AS BLOB))=json_extract(pin.value,'$.source_bytes')
    AND t.input_version=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`).bind(E.stable(selected.map(({task_id,task_hash,result_id,created_at,source_bytes})=>({task_id,task_hash,result_id,created_at,source_bytes}))),inputVersion,inputVersion).all();
  const loaded=Json.capture(fetched?.results,{maxBytes:LIMITS.bytes,maxDepth:6,maxNodes:1000});if(!Array.isArray(loaded)||loaded.length!==selected.length)throw Error('A selected public prefix receipt is unavailable.');const byId=new Map();
  for(const row of loaded){const pin=selected.find(p=>p.task_id===row.task_id);if(!exact(row,['task_id','task_hash','task_json','input_version','result_id','result_json','created_at'])||!pin||byId.has(row.task_id)||row.task_hash!==pin.task_hash||row.result_id!==pin.result_id||row.created_at!==pin.created_at||row.input_version!==inputVersion||typeof row.task_json!=='string'||typeof row.result_json!=='string')throw Error('A pinned prefix source changed.');
   const saved=JSON.parse(row.task_json),result=JSON.parse(row.result_json);if(saved.taskId!==row.task_id||await hash(saved,cryptoAPI)!==row.task_hash)throw Error('An original prefix source task changed.');
   await E.checkIdentity(saved,cryptoAPI);if(saved.engine!==task.engine||E.stable(saved.alphabet)!==alphabet||E.stable(saved.steps)!==steps||!['measurement','exact-prefix'].includes(saved.criterion.kind))throw Error('An original source changed its transformation.');
   const intersection=task.pages.filter(requested=>saved.pages.some(p=>p.id===requested.id&&p.text===requested.text)).map(p=>p.id);if(E.stable(intersection)!==E.stable(pin.pages))throw Error('An original source changed its exact page intersection.');
   const source={task:saved,inputVersion,run:{id:row.result_id,createdAt:row.created_at,result}};
   // Validates original envelopes, geometry, criterion consistency and complete
   // hashes only. The client must replay via VerifiedPrefixEvaluation before
   // deriving any requested-prefix evidence or answer.
   await Relations.compare(saved,inputVersion,[source],cryptoAPI);const size=new TextEncoder().encode(E.stable(source)).length;if(bytes+size>LIMITS.bytes-65536)throw Error('The selected prefix sources exceed the planned byte budget.');bytes+=size;byId.set(row.task_id,source);
  }
  for(const pin of selected){sources.push(byId.get(pin.task_id));sourceLocations.push({taskId:pin.task_id,href:'run.html#task='+pin.task_id,label:'Original computation'});}
 }
 const value={schema:'liberpedia-prefix-source-candidates-v1',provider:'public-local-tasks-v1',requestedTaskId:task.taskId,inputVersion,sources,sourceLocations,lookupComplete};if(new TextEncoder().encode(E.stable(value)).length>LIMITS.bytes)throw Error('The prefix source response exceeds its byte bound.');return value;
}
