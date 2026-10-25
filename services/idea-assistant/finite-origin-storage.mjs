/* One immutable canonical family snapshot, lightweight per-task provenance. */
import E from '../../local-experiment.js';
const hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(v=>v.toString(16).padStart(2,'0')).join('');
const require=(value,message)=>{if(!value)throw Error(message);};
export const ORIGINS_VIEW='local_task_all_origins';

export async function prepareOriginWrite({db,reviewed,taskId,proposalId,originId,at,day,finiteLimit,fixedLimit=50}){
 const query=(sql,...args)=>db.prepare(sql).bind(...args),originJson=E.stable(reviewed.origin),snapshotJson=E.stable(reviewed.snapshot),finite=reviewed.snapshot.kind==='finite-settings';
 require(await hash(originJson)===originId&&await hash(snapshotJson)===reviewed.origin.protocolSha256,'Reviewed source snapshot bytes changed');
 const existing=await query(`SELECT origin_json,snapshot_json FROM ${ORIGINS_VIEW} WHERE task_id=? AND proposal_id=? AND origin_id=?`,taskId,proposalId,originId).first();
 if(existing)require(existing.origin_json===originJson&&existing.snapshot_json===snapshotJson,'Stored reviewed origin differs from its immutable source');
 if(finite){const shared=await query('SELECT snapshot_json FROM authored_finite_snapshots WHERE protocol_sha256=?',reviewed.origin.protocolSha256).first();if(shared)require(shared.snapshot_json===snapshotJson,'Stored shared finite source bytes differ');}
 const count=finite?"((SELECT COUNT(*) FROM local_task_finite_origins WHERE created_day=?)+(SELECT COUNT(*) FROM local_task_origin_kinds WHERE created_day=? AND kind='finite-settings'))":"(SELECT COUNT(*) FROM local_task_origin_kinds WHERE created_day=? AND kind='fixed')";
 const gate={sql:` AND (EXISTS(SELECT 1 FROM ${ORIGINS_VIEW} WHERE task_id=? AND proposal_id=? AND origin_id=?) OR ${count}<?)`,args:[taskId,proposalId,originId,day,...(finite?[day]:[]),finite?finiteLimit:fixedLimit]};
 const linked='EXISTS(SELECT 1 FROM local_task_ideas WHERE task_id=? AND proposal_id=?)',statements=[];
 if(!existing){
  if(finite){
   statements.push(query(`INSERT INTO authored_finite_snapshots(protocol_sha256,snapshot_json,created_at)
    SELECT ?,?,? WHERE ${linked}${gate.sql} ON CONFLICT(protocol_sha256) DO NOTHING`,reviewed.origin.protocolSha256,snapshotJson,at,taskId,proposalId,...gate.args));
   statements.push(query(`INSERT INTO local_task_finite_origins(task_id,proposal_id,origin_id,origin_json,protocol_sha256,created_at,created_day)
    SELECT ?,?,?,?,?,?,? WHERE ${linked}${gate.sql}
    AND EXISTS(SELECT 1 FROM authored_finite_snapshots WHERE protocol_sha256=? AND snapshot_json=?)
    ON CONFLICT(task_id,proposal_id,origin_id) DO NOTHING`,taskId,proposalId,originId,originJson,reviewed.origin.protocolSha256,at,day,taskId,proposalId,...gate.args,reviewed.origin.protocolSha256,snapshotJson));
  }else statements.push(query(`INSERT INTO local_task_origins(task_id,proposal_id,origin_id,origin_json,snapshot_json,created_at,created_day)
    SELECT ?,?,?,?,?,?,? WHERE ${linked}${gate.sql} ON CONFLICT(task_id,proposal_id,origin_id) DO NOTHING`,taskId,proposalId,originId,originJson,snapshotJson,at,day,taskId,proposalId,...gate.args));
 }
 return {gate,statements,async verify(){
  const saved=await query(`SELECT origin_json,snapshot_json FROM ${ORIGINS_VIEW} WHERE task_id=? AND proposal_id=? AND origin_id=?`,taskId,proposalId,originId).first();
  if(!saved)throw Object.assign(Error('The daily authored-origin limit has been reached.'),{code:'daily-quota'});
  require(saved.origin_json===originJson&&saved.snapshot_json===snapshotJson,'Stored reviewed origin differs from its immutable source');
 }};
}
