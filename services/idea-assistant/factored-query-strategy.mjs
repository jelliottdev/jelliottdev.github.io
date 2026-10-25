/* Optional metadata-query planning only. Never grants evidence, advances a
 * cursor, reads result bodies, or changes any predicate/fence/order/limit.
 * Only the maintained provider selects this internal performance policy. */
import Json from '../../finite-json.js';
const FROM='FROM local_task_results r JOIN local_tasks t ON t.id=r.task_id',ROWID='FROM local_task_results r NOT INDEXED CROSS JOIN local_tasks t ON t.id=r.task_id',ORDER=' ORDER BY r.rowid,r.id LIMIT ?';
export const LIMITS=Object.freeze({probeRowids:512,minPrograms:64,densityDenominator:16});
const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
export async function chooseLocalMetadataQuery(options){
 const descriptors=options&&typeof options==='object'&&!Array.isArray(options)?Object.getOwnPropertyDescriptors(options):null;if(!descriptors||Reflect.ownKeys(options).length!==3||!['db','sql','bindings'].every(k=>Object.hasOwn(descriptors,k)&&Object.hasOwn(descriptors[k],'value')&&descriptors[k].enumerable))throw Error('Use the maintained metadata query and explicit bindings.');
 const {sql,bindings}=Json.capture({sql:descriptors.sql.value,bindings:descriptors.bindings.value},{maxBytes:8*1024*1024,maxDepth:5,maxNodes:1000}),db=descriptors.db.value;
 // This helper is an internal policy boundary, not an arbitrary SQL API. The
 // selected columns and binding layout are fixed by the maintained provider.
 if(typeof db?.prepare!=='function'||typeof sql!=='string'||sql.length>20000||!sql.startsWith('SELECT r.rowid AS position,t.id AS task_id,t.task_hash,r.id AS result_id,r.created_at,')||sql.includes(';')||!sql.includes(FROM)||!sql.endsWith(ORDER)||!sql.includes('WHERE r.rowid>? AND r.rowid<=? AND t.rowid<=?')||!Array.isArray(bindings)||bindings.length!==14||bindings.some(v=>!['string','number'].includes(typeof v))||![1,2,3,10,11,13].every(i=>Number.isSafeInteger(bindings[i])&&bindings[i]>=0)||bindings[13]<1||bindings[13]>256||bindings[2]<bindings[1])throw Error('Unsupported metadata query shape.');
 const columns=sql.slice(0,sql.indexOf(FROM));if(columns.includes('result_json')||columns.replaceAll("json_extract(t.task_json,'$.steps')",'').replaceAll("json_each(t.task_json,'$.pages')",'').includes('task_json'))throw Error('Metadata planning cannot load task or result bodies.');
 const steps=JSON.parse(bindings[8]);if(!Array.isArray(steps)||!steps.length||steps.length>1024||steps.some(v=>typeof v!=='string'))throw Error('Unsupported metadata program list.');
 const rowidSQL=sql.replace(FROM,ROWID),answer=(strategy,probe=null)=>freeze({sql:strategy==='rowid-keyset'?rowidSQL:sql,bindings,strategy,probe});
 if(steps.length<LIMITS.minPrograms)return answer('protocol-index');
 const after=bindings[1],high=bindings[2];if(high-after<=LIMITS.probeRowids)return answer('rowid-keyset');
 // The selected-page metadata subquery (first binding) and final LIMIT are
 // absent from this COUNT-only probe; every WHERE binding remains unchanged.
 const upper=Math.min(high,after+LIMITS.probeRowids),probeBindings=bindings.slice(1,-1);probeBindings[1]=upper;
 const from=rowidSQL.indexOf(ROWID),order=rowidSQL.lastIndexOf(ORDER),probeSQL='SELECT (SELECT COUNT(*) FROM local_task_results WHERE rowid>? AND rowid<=?) AS scanned,COUNT(*) AS matching '+rowidSQL.slice(from,order);
 const row=await db.prepare(probeSQL).bind(after,upper,...probeBindings).first();
 if(!row||Object.keys(row).length!==2||!Number.isSafeInteger(row.scanned)||!Number.isSafeInteger(row.matching)||row.scanned<0||row.scanned>LIMITS.probeRowids||row.matching<0||row.matching>row.scanned)throw Error('The bounded metadata density probe failed.');
 return answer(row.scanned&&row.matching*LIMITS.densityDenominator>=row.scanned?'rowid-keyset':'protocol-index',{scanned:row.scanned,matching:row.matching});
}
