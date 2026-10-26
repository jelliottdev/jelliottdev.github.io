import QuestionResult from '../../question-result-context.js';
import {loadInputBundle} from './official-inputs.mjs';
import {readReviewedProgramDetails} from './reviewed-program-source.mjs';
import Compiler from '../../fixed-plan-compiler.js';
/* Resolve an exact public calculation into a detached parameter-question preview.
 * No writes, task admission, target calculation, URL inference or novelty claim. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import C from '../../claim-specification.js';
import Question from '../../task-parameter-question.js';
import {validateCard} from './idea-relations.mjs';
import {readAdmittedResult} from './admitted-result.mjs';
import {readPublishedEvidence} from './published-evidence.mjs';

const HEX=/^[a-f0-9]{64}$/,PROPOSAL=/^p_[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const ensure=(value,message)=>{if(!value)throw Error(message);};
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const hash=async(value,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');

async function readOfficialJSON(response,max,signal){
 ensure(!response.redirected&&!signal.aborted,'The official source redirected or loading was cancelled.');
 const reader=response.body?.getReader();ensure(reader,'The official source body is unavailable.');let size=0,stop;const chunks=[],aborted=new Promise((_,reject)=>{stop=()=>reject(Error('Official source loading was cancelled.'));signal.addEventListener('abort',stop,{once:true});});
 try{while(true){ensure(!signal.aborted,'Official source loading was cancelled.');const part=await Promise.race([reader.read(),aborted]);if(part.done)break;size+=part.value.byteLength;ensure(size<=max,'The official source exceeds its byte bound.');chunks.push(part.value);}}catch(error){try{void reader.cancel().catch(()=>{});}catch{}throw error;}finally{signal.removeEventListener('abort',stop);}
 const bytes=new Uint8Array(size);let at=0;for(const part of chunks){bytes.set(part,at);at+=part.byteLength;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}

export async function resolveParameterQuestionDetails(input,{db,crypto=globalThis.crypto,fetcher=globalThis.fetch,registry,history,programIndex,signal}={}){
 const value=J.capture(input,{maxBytes:65536,maxDepth:16,maxNodes:10000}),hasSettings=!!value&&Object.hasOwn(value,'parentSettings');
 ensure(exact(value,['source','selection',...(hasSettings?['parentSettings']:[])]),'Declare an exact source and selected parameter change.');
 const ref=value.source,choice=Question.selection(value.selection);
 ensure(choice.parameter!=='evaluation'||ref?.kind==='saved-question-program','An output-check follow-up requires the complete saved question program.');
 ensure(ref&&typeof ref==='object'&&!Array.isArray(ref)&&typeof ref.proposalId==='string'&&PROPOSAL.test(ref.proposalId),'Use an exact public parent question.');
 if(['saved-task','saved-question-program'].includes(ref.kind))ensure(exact(ref,['kind','proposalId','taskId'])&&typeof ref.taskId==='string'&&HEX.test(ref.taskId),'Use an exact saved-task source reference.');
 else ensure(['published-program','archived-program'].includes(ref.kind)&&exact(ref,['kind','proposalId','recordId','revision','caseId'])&&typeof ref.recordId==='string'&&ref.recordId.length<=100&&SLUG.test(ref.recordId)&&typeof ref.revision==='string'&&HEX.test(ref.revision)&&typeof ref.caseId==='string'&&ref.caseId.length<=200&&/^[a-z0-9-]+$/.test(ref.caseId),'Use an exact pinned published-program reference.');
 ensure(typeof db?.prepare==='function'&&crypto?.subtle,'Public source resolution is unavailable.');
 const live=()=>{ensure(!signal?.aborted,'Parameter-question source resolution was cancelled.');};
 const query=(sql,...args)=>db.prepare(sql).bind(...args).first();
 live();
 const archived=ref.kind==='archived-program',fullQuestion=ref.kind==='saved-question-program';
 ensure(!(archived||fullQuestion)||!hasSettings,'This fixed question program does not accept family settings.');
 let parentCard,cardSha256,task,inputVersion,resultId,createdAt,publishedSource,reviewedProgram,reviewedPreparation,savedResult,parentTaskId;
 if(!archived){
  const publicRow=await query(`SELECT p.id,p.card_hash,p.card_json FROM proposals p
   JOIN research_ideas public ON public.proposal_id=p.id WHERE p.id=?`,ref.proposalId);live();
  ensure(publicRow&&publicRow.id===ref.proposalId&&typeof publicRow.card_json==='string'&&typeof publicRow.card_hash==='string'&&HEX.test(publicRow.card_hash),'The public parent question is unavailable.');
  parentCard=validateCard(publicRow.card_json);const cardText=C.serialize(parentCard);cardSha256=await hash(cardText,crypto);live();
  ensure(publicRow.card_json===cardText&&publicRow.card_hash===cardSha256&&ref.proposalId==='p_'+cardSha256,'The public parent question changed its canonical identity.');
 }
 if(['saved-task','saved-question-program'].includes(ref.kind)){
  const row=await query(`SELECT t.id,t.task_hash,t.task_json,t.input_version,links.input_version AS linked_input_version,links.parent_task_id
   FROM local_tasks t JOIN local_task_ideas links ON links.task_id=t.id
   JOIN research_ideas public ON public.proposal_id=links.proposal_id
   WHERE t.id=? AND links.proposal_id=?`,ref.taskId,ref.proposalId);live();
  ensure(row&&row.id===ref.taskId&&typeof row.task_json==='string'&&new TextEncoder().encode(row.task_json).length<=2000000&&typeof row.task_hash==='string'&&HEX.test(row.task_hash)&&['raw','reviewed'].includes(row.linked_input_version),'The saved task has no exact public question association.');
  task=JSON.parse(row.task_json);inputVersion=row.linked_input_version;parentTaskId=row.parent_task_id;const expectedHash=row.task_hash;
  await E.checkIdentity(task,crypto);ensure(task.taskId===ref.taskId&&await hash(task,crypto)===expectedHash,'The saved task changed its exact bytes or identity.');live();
  const latest=await query('SELECT id,task_id,result_json,created_at FROM local_task_results WHERE task_id=? ORDER BY created_at DESC,id DESC LIMIT 1',ref.taskId);live();
  ensure(latest&&latest.task_id===ref.taskId,'The saved task has no admitted saved result.');
  const admitted=J.capture(latest,{maxBytes:8*1024*1024+1024,maxDepth:3,maxNodes:16});
  savedResult=await readAdmittedResult(task,admitted,crypto);live();resultId=admitted.id;createdAt=admitted.created_at;
  if(Compiler.compile(parentCard).reason&&!hasSettings){const retained=await readReviewedProgramDetails({db,proposalId:ref.proposalId,card:parentCard,task,inputVersion,parentTaskId:row.parent_task_id,crypto,signal});live();ensure(retained,'The original question has no exact retained reviewed mapping.');reviewedProgram=retained.proof;reviewedPreparation=retained.preparation;}
 }else{
  const published=await readPublishedEvidence({recordId:ref.recordId,revision:ref.revision,caseId:ref.caseId,crypto,fetcher,registry,history,programIndex,signal});live();
  ensure(published&&published.publishedSource?.recordId===ref.recordId&&published.publishedSource.revision===ref.revision&&published.publishedSource.caseId===ref.caseId,'The pinned published calculation is unavailable.');
  task=published.task;inputVersion=published.inputVersion;resultId=published.run.id;createdAt=published.run.createdAt;publishedSource=published.publishedSource;
  if(archived){
   const derived=await Question.archived({task,inputVersion},crypto);live();
   ensure(derived.proposalId===ref.proposalId,'The archived program identifies another canonical parent question.');
   parentCard=validateCard(derived.card);cardSha256=derived.cardSha256;
   ensure(C.serialize(parentCard)===C.serialize(derived.card)&&cardSha256===await hash(C.serialize(parentCard),crypto)&&ref.proposalId==='p_'+cardSha256,'The archived parent changed its canonical identity.');live();
   const existing=await query('SELECT id,card_hash,card_json FROM proposals WHERE id=?',ref.proposalId);live();
   ensure(!existing||existing.id===ref.proposalId&&existing.card_hash===cardSha256&&existing.card_json===C.serialize(parentCard),'The retained archived parent changed its canonical content.');
  }

 }
 let programTask=task,questionProgram;
 if(fullQuestion){
  const controller=new AbortController(),stop=()=>controller.abort();signal?.addEventListener('abort',stop,{once:true});if(signal?.aborted)stop();const timer=setTimeout(stop,20000);
  try{const loaded=await loadInputBundle({fetcher,signal:controller.signal,read:(response,max)=>readOfficialJSON(response,max,controller.signal)});live();
   const bundle={schema:'liberpedia-local-inputs-v1',alphabet:loaded.alphabet,pages:[...loaded.pages.values()]},projection={id:task.taskId,plan:task,proposalId:ref.proposalId,card:parentCard,inputVersion,parentTaskId,linkedProposalId:ref.proposalId,linkedInputVersion:inputVersion,linkedParentTaskId:parentTaskId,state:'results-verified',latestRun:{id:resultId,createdAt,result:savedResult},...(reviewedProgram?{reviewedProgram}:{})},context=await QuestionResult.prepare({proposalId:ref.proposalId,card:parentCard,projection,bundle},crypto);live();programTask=context.questionTask;questionProgram={taskId:programTask.taskId,taskSha256:await hash(programTask,crypto),inputVersion};live();
  }finally{clearTimeout(timer);signal?.removeEventListener('abort',stop);}
 }
 const derivation=await Question.prepare({parentTask:programTask,parentCard,inputVersion,selection:value.selection,...(hasSettings?{parentSettings:value.parentSettings}:{}),...(reviewedProgram?{reviewedProgram}:{})},crypto);live();
 ensure(derivation.parent.cardSha256===cardSha256&&derivation.parent.taskId===programTask.taskId,'The derived question changed its authenticated parent.');
 const taskSha256=await hash(task,crypto);live();
 const preview={schema:'liberpedia-parameter-question-preview-v1',source:{reference:ref,receipt:{taskId:task.taskId,taskSha256,resultId,createdAt,inputVersion},...(publishedSource?{publishedSource}: {}),...(reviewedProgram?{reviewedProgram}:{}),...(questionProgram?{questionProgram}:{})},parentQuestion:{proposalId:ref.proposalId,cardSha256},derivation};
 return freeze({preview,parentCard,...(reviewedPreparation?{reviewedPreparation}:{})});
}
export async function resolveParameterQuestion(input,options){return (await resolveParameterQuestionDetails(input,options)).preview;}
