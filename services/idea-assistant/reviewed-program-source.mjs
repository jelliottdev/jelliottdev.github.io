/* Read a compatible retained mapping proof. Never asserts a token was consumed. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import C from '../../claim-specification.js';
import Reviewed from '../../reviewed-program.js';
const HEX=/^[a-f0-9]{64}$/,PREP=/^prep_[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/;
const same=(a,b)=>E.stable(a)===E.stable(b),exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k)),ensure=(v,m)=>{if(!v)throw Error(m);},freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},iso=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
const sha=async(v,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
function mappedBasis(value){
 let basis=value;
 if(basis?.kind==='evidence-remainder'){ensure(exact(basis,['kind','originalBasis','requestedTaskId','evidence'])&&typeof basis.requestedTaskId==='string'&&HEX.test(basis.requestedTaskId)&&Array.isArray(basis.evidence)&&basis.evidence.length<=75,'The retained remainder mapping changed.');basis=basis.originalBasis;}
 if(basis?.kind!=='mapped-card')return null;
 ensure(exact(basis,['kind','normalizedCard','mapping']),'The retained mapping fields changed.');return basis;
}
export async function readReviewedProgramDetails({db,proposalId,card,task,inputVersion,parentTaskId=null,crypto=globalThis.crypto,signal}={}){
 ensure(typeof db?.prepare==='function'&&crypto?.subtle&&typeof proposalId==='string'&&IDEA.test(proposalId)&&['raw','reviewed'].includes(inputVersion)&&(parentTaskId===null||typeof parentTaskId==='string'&&HEX.test(parentTaskId)),'An exact saved question association is required.');
 const input=J.capture({card,task},{maxBytes:2*1024*1024,maxDepth:24,maxNodes:250000}),live=()=>ensure(!signal?.aborted,'Mapping source lookup was cancelled.');live();E.validateTask(input.task);
 const cardHash=await sha(C.serialize(input.card),crypto);live();ensure(proposalId==='p_'+cardHash,'The original public question changed.');
 const result=await db.prepare('SELECT * FROM prepared_plans WHERE proposal_id=? AND task_id=? AND input_version=? AND parent_task_id IS ? AND authority=? ORDER BY created_at,id LIMIT 11').bind(proposalId,input.task.taskId,inputVersion,parentTaskId,'idea').all();live();
 ensure(result&&Array.isArray(result.results),'The retained mapping lookup is unavailable.');ensure(result.results.length<=10,'The retained mapping lookup is ambiguous.');
 if(!result.results.length)return null;await E.checkIdentity(input.task,crypto);live();const taskHash=await sha(input.task,crypto);live();
 let chosen=null,meaning=null,preparation=null;
 for(const raw of result.results){
  const row=J.capture(raw,{maxBytes:160000,maxDepth:3,maxNodes:100});
  ensure(typeof row.id==='string'&&PREP.test(row.id)&&row.proposal_id===proposalId&&row.card_hash===cardHash&&row.task_id===input.task.taskId&&row.task_hash===taskHash&&row.input_version===inputVersion&&row.parent_task_id===parentTaskId&&row.authority==='idea'&&[row.binding_hash,row.controls_hash,row.basis_hash].every(v=>typeof v==='string'&&HEX.test(v))&&typeof row.basis_json==='string'&&new TextEncoder().encode(row.basis_json).length<=128000&&iso(row.created_at)&&row.created_day===row.created_at.slice(0,10),'The retained preparation binding changed.');
  const basis=J.capture(JSON.parse(row.basis_json),{maxBytes:128000,maxDepth:24,maxNodes:30000});ensure(E.stable(basis)===row.basis_json&&await sha(row.basis_json,crypto)===row.basis_hash,'The retained preparation basis changed.');live();
  const base={version:1,proposalId,cardHash,taskId:input.task.taskId,taskHash,inputVersion,parentTaskId,controlsHash:row.controls_hash};
  ensure(await sha(base,crypto)===row.binding_hash&&'prep_'+await sha({...base,authority:row.authority,basisHash:row.basis_hash},crypto)===row.id,'The retained preparation identity changed.');live();
  const mapped=mappedBasis(basis);if(!mapped)continue;
  await Reviewed.verify({originalCard:input.card,normalizedCard:mapped.normalizedCard,mapping:mapped.mapping,task:input.task,inputVersion},crypto);live();
  const semantic=E.stable(mapped);ensure(meaning===null||meaning===semantic,'Multiple incompatible reviewed mappings identify this task.');meaning=semantic;
  if(!chosen){preparation=row;chosen={schema:'liberpedia-prepared-program-proof-v1',preparationId:row.id,basisSha256:await sha(mapped,crypto),normalizedCard:mapped.normalizedCard,mapping:mapped.mapping};}
 }
 live();return chosen?freeze({proof:chosen,preparation}):null;
}

export async function readReviewedProgram(options){return (await readReviewedProgramDetails(options))?.proof||null;}
