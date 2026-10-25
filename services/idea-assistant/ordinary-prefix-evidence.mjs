/* Ordinary prefix reuse from immutable server-verified public originals. No target execution. */
import E from '../../local-experiment.js';
import Relations from '../../computation-evidence.js';
import Json from '../../finite-json.js';
import {findPrefixEvaluationSources} from './prefix-evaluation-sources.mjs';
const HEX=/^[a-f0-9]{64}$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const hash=async(v,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
const capture=v=>Json.capture(v,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000});
async function project(task,inputVersion,raw,cryptoAPI){
 const sources=capture(raw);await E.checkIdentity(task,cryptoAPI);if(task.criterion.kind!=='exact-prefix'||!['raw','reviewed'].includes(inputVersion)||!Array.isArray(sources)||sources.length>75)throw Error('Invalid ordinary prefix evidence.');
 const pages=new Map(task.pages.map(p=>[p.id,p.text])),runes=new Map(task.alphabet.map((r,i)=>[r.rune,i])),program=E.stable({engine:task.engine,alphabet:task.alphabet,steps:task.steps}),claims=new Map(),used=new Map();
 for(const s of sources){
  if(!exact(s,['task','inputVersion','run'])||s.inputVersion!==inputVersion||!exact(s.run,['id','createdAt','result'])||!HEX.test(s.run.id)||typeof s.run.createdAt!=='string'||!Number.isFinite(Date.parse(s.run.createdAt))||!['measurement','exact-prefix'].includes(s.task?.criterion?.kind))throw Error('Invalid original prefix source.');
  await E.checkIdentity(s.task,cryptoAPI);await Relations.compare(s.task,inputVersion,[s],cryptoAPI);
  if(E.stable({engine:s.task.engine,alphabet:s.task.alphabet,steps:s.task.steps})!==program)throw Error('The original transformation changed.');
  const key=E.stable([s.task.taskId,s.run.id,s.run.createdAt]);if(used.has(key)&&E.stable(used.get(key))!==E.stable(s))throw Error('Conflicting original prefix source.');used.set(key,s);
  for(const p of s.task.pages){if(pages.get(p.id)!==p.text)continue;const text=s.run.result.transformed.find(x=>x.page===p.id)?.text;if(typeof text!=='string')throw Error('Missing original transformed output.');const values=[...text].filter(r=>runes.has(r)).map(r=>runes.get(r)),matched=task.criterion.values.every((v,i)=>values[i]===v),prior=claims.get(p.id);if(prior&&prior.text!==text)throw Error('Conflicting original outputs.');if(!prior||key<prior.key)claims.set(p.id,{key,text,matched});}
 }
 const coveredPages=task.pages.filter(p=>claims.has(p.id)).map(p=>p.id),matchingPages=coveredPages.filter(id=>claims.get(id).matched),remainingPages=task.pages.filter(p=>!claims.has(p.id)).map(p=>p.id),keys=[...new Set(coveredPages.map(id=>claims.get(id).key))].sort(),originals=keys.map(k=>used.get(k));
 const evidence=keys.map(key=>{const s=used.get(key);return {taskId:s.task.taskId,resultId:s.run.id,createdAt:s.run.createdAt,pages:coveredPages.filter(id=>claims.get(id).key===key)};});
 return {summary:{coveredPages,matchingPages,remainingPages},sources:originals,evidence};
}
export async function discoverOrdinaryPrefixEvidence({db,task,inputVersion,crypto:cryptoAPI=globalThis.crypto}){
 const candidates=await findPrefixEvaluationSources({db,task,inputVersion,crypto:cryptoAPI});
 if(new TextEncoder().encode(E.stable({task,inputVersion,sources:candidates.sources})).length>8*1024*1024-65536)throw Error('The original request and receipt proof exceed the client replay byte budget.');
 const p=await project(task,inputVersion,candidates.sources,cryptoAPI);
 return {wire:{schema:'liberpedia-ordinary-derived-prefix-coverage-v1',provider:'public-local-tasks-v1',requestedTaskId:task.taskId,inputVersion,sources:p.sources,sourceLocations:p.sources.map(s=>({taskId:s.task.taskId,href:'run.html#task='+s.task.taskId,label:'Original computation'})),lookupComplete:candidates.lookupComplete,summary:p.summary},evidence:p.evidence};
}
export async function checkedOrdinaryPrefixEvidence({db,task,inputVersion,evidence,crypto:cryptoAPI=globalThis.crypto}){
 const refs=capture(evidence);if(!Array.isArray(refs)||refs.length>75||new Set(refs.map(r=>r?.taskId)).size!==refs.length)throw Error('Invalid pinned prefix references.');const sources=[];
 for(const ref of refs){if(!exact(ref,['taskId','resultId','createdAt','pages'])||!HEX.test(ref.taskId)||!HEX.test(ref.resultId)||typeof ref.createdAt!=='string'||!Number.isFinite(Date.parse(ref.createdAt))||!Array.isArray(ref.pages)||!ref.pages.length||ref.pages.length>75||new Set(ref.pages).size!==ref.pages.length)throw Error('Invalid pinned prefix reference.');
  const row=await db.prepare(`SELECT t.task_hash,t.task_json,t.input_version,r.result_json,r.created_at FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id AND r.id=? WHERE t.id=? AND t.input_version=? AND r.created_at=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`).bind(ref.resultId,ref.taskId,inputVersion,ref.createdAt,inputVersion).first();
  if(!row||typeof row.task_json!=='string'||typeof row.result_json!=='string'||row.input_version!==inputVersion)throw Error('Pinned public prefix source unavailable.');const saved=JSON.parse(row.task_json);if(saved.taskId!==ref.taskId||await hash(saved,cryptoAPI)!==row.task_hash)throw Error('Pinned prefix task identity changed.');sources.push({task:saved,inputVersion,run:{id:ref.resultId,createdAt:ref.createdAt,result:JSON.parse(row.result_json)}});
 }
 const p=await project(task,inputVersion,sources,cryptoAPI);if(E.stable(p.evidence)!==E.stable(refs.slice().sort((a,b)=>E.stable([a.taskId,a.resultId,a.createdAt]).localeCompare(E.stable([b.taskId,b.resultId,b.createdAt])))))throw Error('Pinned prefix page claims changed.');return p.summary;
}
export function combineOrdinaryPrefixCoverage(task,strict,derived){const ids=new Set([...strict.coveredPages,...derived.coveredPages]);return {coveredPages:task.pages.filter(p=>ids.has(p.id)).map(p=>p.id),remainingPages:task.pages.filter(p=>!ids.has(p.id)).map(p=>p.id),matchingPages:derived.matchingPages};}
