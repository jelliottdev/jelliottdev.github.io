/* Refresh only the explicitly selected cases; never rescan the whole search.
 * Stored outputs are hash/structure checked here, independently replayed by the
 * browser before they contribute to its question proof. No target execution. */
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import Q from '../../factored-finite-question.js';
import Json from '../../finite-json.js';
import {findEvidence} from './task-evidence.mjs';
import {resolveFamilyEvidence} from './family-evidence.mjs';
import {resolvePublishedEvidence} from './published-evidence.mjs';
import {readFactoredOutputEvidencePage} from './factored-output-evidence.mjs';
import {readFactoredInspectionEvidencePage} from './factored-inspection-evidence.mjs';
import {readFactoredPrefixEvidencePage} from './factored-prefix-evidence.mjs';
const MAX=8*1024*1024,enc=new TextEncoder();
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const fail=(message,status=503)=>Object.assign(Error(message),{status});
const hash=async(value,c)=>[...new Uint8Array(await c.subtle.digest('SHA-256',enc.encode(E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');
export async function selectFactoredCases({compiled,cases,crypto=globalThis.crypto}){
 const domain=Q.inspect(compiled.domain),selection=Json.capture(cases,{maxBytes:65536,maxDepth:16,maxNodes:6000});
 if(!Array.isArray(selection)||!selection.length||selection.length>12||selection.some(item=>!exact(item,['settings','pageId'])))throw fail('Select one to twelve exact declared settings and pages.',400);
 const refs=selection.map(item=>{const member=compiled.members.find(member=>E.stable(member.settings)===E.stable(item.settings));if(!member)throw fail('A selected setting is outside the original question.',400);return {programId:member.programId,pageId:item.pageId};});
 let chosen;try{chosen=await Q.select(domain,refs,crypto);}catch{throw fail('A selected case is outside the original question.',400);}
 return chosen.cases.map(item=>({...item,settings:compiled.members.find(member=>member.programId===item.programId).settings}));
}
export async function findSelectedFactoredEvidence({db,domain,cases,crypto=globalThis.crypto}){
 const d=Q.inspect(domain),groups=new Map(),sources=[],sourceLinks=[],seen=new Set(),covered=new Set();
 if(!Array.isArray(cases)||!cases.length||cases.length>12)throw fail('Select a bounded batch.',400);
 for(const item of cases){const group=groups.get(item.programId)||[];group.push(item);groups.set(item.programId,group);}
 for(const [programId,items] of groups){
  const task=await E.prepare({title:'Selected declared cases',alphabet:d.alphabet,steps:d.programs.find(program=>program.id===programId).steps,criterion:d.criterion,pages:items.map(item=>item.task.pages[0])},crypto);
  const found=await findEvidence({db,task,inputVersion:d.inputVersion,crypto});
  if(found.truncated&&found.remainingPages.length)throw fail('The selected evidence lookup is incomplete. Retry a fresh lookup before running these cases.');
  const loaded=[];
  for(const ref of found.evidence){
   const row=await db.prepare(`SELECT t.task_json,t.task_hash,t.input_version,r.result_json,r.created_at FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id AND r.id=? WHERE t.id=? AND t.input_version=? AND r.created_at=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`).bind(ref.resultId,ref.taskId,d.inputVersion,ref.createdAt,d.inputVersion).first();
   let source,link;
   if(row){const saved=JSON.parse(row.task_json);if(saved.taskId!==ref.taskId||await hash(saved,crypto)!==row.task_hash||row.input_version!==d.inputVersion||row.created_at!==ref.createdAt)throw fail('A selected immutable task changed.');source={task:saved,inputVersion:d.inputVersion,run:{id:ref.resultId,createdAt:row.created_at,result:JSON.parse(row.result_json)}};link={href:'run.html#task='+ref.taskId,label:'Inspect saved output'};}
   else {const family=await resolveFamilyEvidence({db,...ref,inputVersion:d.inputVersion,crypto}),published=family?null:await resolvePublishedEvidence({...ref,inputVersion:d.inputVersion,crypto});if(!family&&!published)throw fail('A selected original receipt is unavailable.');source=(family||published).source;
    link=family?{href:'run.html#family='+family.familySource.familyId+'&case='+family.familySource.caseId+'&revision='+family.familySource.revision,label:'Inspect family output'}:{href:'library.html#/experiment/'+published.publishedSource.recordId,label:'Inspect published calculations'};}
   loaded.push(source);const key=E.stable([source.task.taskId,source.run.id,source.run.createdAt]);
   if(!seen.has(key)){seen.add(key);sources.push(source);sourceLinks.push({taskId:source.task.taskId,...link});}
  }
  const compared=await Evidence.compare(task,d.inputVersion,loaded,crypto);
  if(E.stable(compared.evidence)!==E.stable(found.evidence)||E.stable(compared.coveredPages)!==E.stable(found.coveredPages))throw fail('The selected original receipts changed their page coverage.');
  for(const item of items)if(compared.coveredPages.includes(item.pageId))covered.add(item.id);
 }
 if(sources.length>12||enc.encode(E.stable({sources,sourceLinks})).byteLength>MAX-65536)throw fail('Selected original receipts exceed the bounded response size.',413);
 return {sources,sourceLinks,missing:cases.filter(item=>!covered.has(item.id)).map(item=>({settings:item.settings,pageId:item.pageId}))};
}

// New policy only: refresh the selected work from unchanged original outputs,
// independent of their former prefix. Never scan the entire original domain.
async function findSelectedOutputEvidence(output,{db,proposalId,domain,cases,cursorKey,now=Date.now(),crypto=globalThis.crypto},inspection=false){
 const d=Q.inspect(domain);if(!Array.isArray(cases)||!cases.length||cases.length>12)throw fail('Select a bounded batch.',400);
 const checked=await Q.select(d,cases.map(item=>({id:item.id,programId:item.programId,pageId:item.pageId})),crypto);
 if(checked.cases.some(item=>E.stable(item.task)!==E.stable(cases.find(c=>c.id===item.id)?.task)))throw fail('A selected case changed its exact reviewed computation.',400);
 const programIds=new Set(cases.map(item=>item.programId)),pageIds=new Set(cases.map(item=>item.pageId)),selected=await (inspection?Q.bindOutputInspection:output?Q.bindLanguageComparison:Q.bind)({engine:d.engine,inputVersion:d.inputVersion,alphabet:d.alphabet,criterion:d.criterion,programs:d.programs.filter(p=>programIds.has(p.id)),pages:d.pages.filter(p=>pageIds.has(p.id))},crypto),sources=[],sourceLinks=[],covered=new Set(),seen=new Set();let cursor=null,complete=false;
 for(let page=0;page<4;page++){
  const out=await (inspection?readFactoredInspectionEvidencePage:output?readFactoredOutputEvidencePage:readFactoredPrefixEvidencePage)({db,proposalId,domain:selected,inputVersion:d.inputVersion,cursor,cursorKey,now,crypto});
  for(const source of out.sources){const relevant=cases.filter(item=>!covered.has(item.id)&&source.inputVersion===d.inputVersion&&E.stable(source.task.steps)===E.stable(item.task.steps)&&source.task.pages.some(p=>p.id===item.pageId&&p.text===item.task.pages[0].text));if(!relevant.length)continue;
   const key=E.stable([source.task.taskId,source.run.id,source.run.createdAt,source.inputVersion]);if(!seen.has(key)){const link=out.sourceLinks.find(link=>link.taskId===source.task.taskId);if(!link)throw fail('A selected original source location is unavailable.');seen.add(key);sources.push(source);sourceLinks.push(link);}for(const item of relevant)covered.add(item.id);
  }
  complete=out.continuation.complete;if(covered.size===cases.length||complete)break;cursor=out.continuation.nextCursor;
 }
 if(!complete&&covered.size<cases.length)throw fail('The selected output lookup is incomplete. Retry a fresh lookup before running these cases.');
 if(sources.length>12||enc.encode(E.stable({sources,sourceLinks})).byteLength>MAX-65536)throw fail('Selected original outputs exceed the bounded response size.',413);
 return {sources,sourceLinks,missing:cases.filter(item=>!covered.has(item.id)).map(item=>({settings:item.settings,pageId:item.pageId}))};
}

export const findSelectedFactoredPrefixEvidence=options=>findSelectedOutputEvidence(false,options);
export const findSelectedFactoredOutputEvidence=options=>findSelectedOutputEvidence(true,options);
export const findSelectedFactoredInspectionEvidence=options=>findSelectedOutputEvidence(false,options,true);
