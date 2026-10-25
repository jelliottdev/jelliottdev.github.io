/* Build-time retention validation reuses the current published adapter, then replays. */
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import E from '../local-experiment.js';
import History from '../published-evidence-history.js';
import {readPublishedEvidence} from '../services/idea-assistant/published-evidence.mjs';
export const BUDGET=History.BUDGET;
const HEX=/^[a-f0-9]{64}$/,COMMIT=/^[a-f0-9]{40}$/,SCHEMAS=['liberpedia-published-count-evidence-v1','liberpedia-published-program-evidence-v1'],PATHS=['data/published-count-evidence.json','data/published-opening-evidence.json'];
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),key=r=>[r.recordId,r.revision,r.caseId].join('|');
export async function validateRegistry(registry){
 if(!registry?.entries?.length)throw Error('A retained source registry must contain a receipt.');
 const first=registry.entries[0];
 if(!await readPublishedEvidence({recordId:first.recordId,revision:first.revision,caseId:first.caseId,registry}))throw Error('A retained source registry could not be validated.');
 for(const entry of registry.entries)await E.verify(entry.task,entry.run.result);
 return registry;
}
export function manifestFor(history,receipt){
 const manifest=History.create(history).find({recordId:receipt.recordId,revision:receipt.revision,caseId:receipt.caseId});if(!manifest)throw Error('The exact historical receipt does not exist.');return manifest;
}
export async function validateHistory(history){
 const archive=History.create(history);
 if(!exact(history,['schema','tasks','results','receipts','seedSources'])||history.schema!=='liberpedia-published-evidence-history-v1')throw Error('Published proof history has an unsupported schema.');
 if(Buffer.byteLength(E.stable(history))>BUDGET.bytes)throw Error('Published proof history exceeds its byte budget; no receipts may be evicted.');
 for(const field of ['tasks','results','receipts','seedSources'])if(!Array.isArray(history[field])||history[field].length>BUDGET[field])throw Error('Published proof history exceeds its '+field+' budget; no receipts may be evicted.');
 const tasks=new Set(),results=new Set(),referencedTasks=new Set(),referencedResults=new Set(),receipts=new Set(),replayed=new Set(),seeds=new Set();
 for(const row of history.tasks){if(!exact(row,['id','task'])||!HEX.test(row.id)||row.task?.taskId!==row.id||tasks.has(row.id))throw Error('A retained task body is duplicated or changed.');await E.checkIdentity(row.task);tasks.add(row.id);}
 for(const row of history.results){if(!exact(row,['id','result'])||!HEX.test(row.id)||hash(row.result)!==row.id||results.has(row.id))throw Error('A retained result body is duplicated or changed.');results.add(row.id);}
 for(const row of history.seedSources){if(!exact(row,['commit','path','sha256'])||!COMMIT.test(row.commit)||!PATHS.includes(row.path)||!HEX.test(row.sha256)||seeds.has(row.commit+'|'+row.path))throw Error('Public-history seed metadata is invalid or duplicated.');seeds.add(row.commit+'|'+row.path);}
 for(const receipt of history.receipts){
  if(!exact(receipt,['recordId','revision','caseId','registrySchema','taskId','resultId','inputVersion','createdAt','provenance'])||!SCHEMAS.includes(receipt.registrySchema)||!tasks.has(receipt.taskId)||!results.has(receipt.resultId)||receipts.has(key(receipt)))throw Error('A historical receipt identity is missing or duplicated.');
  const manifest=archive.find({recordId:receipt.recordId,revision:receipt.revision,caseId:receipt.caseId}),entry=manifest.entries[0];if(entry.run.result.taskId!==receipt.taskId)throw Error('A historical result belongs to a different task.');
  // Each envelope is checked separately: multiple old provenance revisions can
  // legitimately refer to the same mathematical task and result body.
  if(!await readPublishedEvidence({recordId:receipt.recordId,revision:receipt.revision,caseId:receipt.caseId,registry:manifest}))throw Error('The exact historical provenance envelope is invalid.');
  const pair=receipt.taskId+'|'+receipt.resultId;if(!replayed.has(pair)){await E.verify(entry.task,entry.run.result);replayed.add(pair);}
  receipts.add(key(receipt));referencedTasks.add(receipt.taskId);referencedResults.add(receipt.resultId);
 }
 if(tasks.size!==referencedTasks.size||results.size!==referencedResults.size)throw Error('Published proof history contains unreferenced bodies.');
 for(const [field,keys] of [['tasks',history.tasks.map(r=>r.id)],['results',history.results.map(r=>r.id)],['receipts',history.receipts.map(key)],['seedSources',history.seedSources.map(r=>r.commit+'|'+r.path)]])if(E.stable(keys)!==E.stable(keys.slice().sort()))throw Error('Published proof history '+field+' must use deterministic ordering.');
 return {receipts:receipts.size,tasks:tasks.size,results:results.size,replayed:replayed.size};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{const raw=readFileSync(0);if(raw.byteLength>BUDGET.bytes)throw Error('Published proof history exceeds its byte budget.');const value=JSON.parse(raw.toString('utf8')),summary=process.argv.includes('--registry')?(await validateRegistry(value),{registry:'verified'}):await validateHistory(value);console.log(JSON.stringify(summary));}catch(error){console.error(error.message);process.exitCode=1;}
}
