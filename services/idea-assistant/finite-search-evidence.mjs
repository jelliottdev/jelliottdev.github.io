/* One bulk source lookup for a declared domain, independent of titles and filing. */
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import Settings from '../../finite-settings.js';
import Compiler from '../../fixed-plan-compiler.js';
import PublishedCounts from '../../published-count-evidence-data.js';
import PublishedPrograms from '../../published-opening-evidence-data.js';
import {readPublishedEvidence} from './published-evidence.mjs';
import {validateFamilyReceipt} from './family-evidence.mjs';
const MAX_ROWS=8192,MAX_BYTES=8*1024*1024,HEX=/^[a-f0-9]{64}$/;
const hash=async(v,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(v=>v.toString(16).padStart(2,'0')).join('');

export async function findFiniteEvidence({db,card,bundle,crypto:cryptoAPI=globalThis.crypto}){
 const expanded=Settings.expand(card),plans=expanded.variants.map(v=>Compiler.compile(v.card));
 if(plans.some(p=>p.reason||p.criterion?.kind!=='exact-prefix')||card.rules.inputVersion.status!=='specified')throw Error('The declared settings need a supported exact opening check.');
 const first=plans[0],version=first.inputVersion,pages=first.pages.map(id=>{
  const row=bundle.pages.get(id),text=version==='raw'?row?.raw:row?.reviewed_text;if(typeof text!=='string')throw Error('The declared source text is unavailable.');return {id,text};
 });
 const criterion=E.stable(first.criterion),alphabet=E.stable(bundle.alphabet),steps=[...new Set(plans.map(plan=>{
  if(plan.inputVersion!==version||E.stable(plan.pages)!==E.stable(first.pages)||E.stable(plan.criterion)!==criterion)throw Error('An alternative changes the common question.');return E.stable(plan.steps);
 }))];
 if(steps.length!==plans.length)throw Error('Duplicate programs are not distinct search settings.');
 const stepSet=new Set(steps),sourceTexts=new Map(pages.map(p=>[p.id,p.text])),scope=E.stable(pages),sources=[],sourceLinks=[],seen=new Set();let bytes=0,lookupComplete=true;
 async function retain(source,link){
  const id=source.task.taskId+'|'+source.run.id;
  if(seen.has(id)||source.inputVersion!==version||source.task.engine!==E.ENGINE||E.stable(source.task.alphabet)!==alphabet||E.stable(source.task.criterion)!==criterion||!stepSet.has(E.stable(source.task.steps))||!source.task.pages.some(p=>sourceTexts.get(p.id)===p.text))return;
  const size=new TextEncoder().encode(E.stable(source)).length+new TextEncoder().encode(E.stable({taskId:source.task.taskId,...link})).length+4;if(bytes+size>MAX_BYTES-1024){lookupComplete=false;return;}
  await Evidence.compare(source.task,version,[source],cryptoAPI);seen.add(id);bytes+=size;sources.push(source);sourceLinks.push({taskId:source.task.taskId,...link});
 }
 const rows=(await db.prepare(`SELECT t.id AS task_id,t.task_hash,r.id AS result_id,r.created_at,
   json_extract(t.task_json,'$.steps') AS steps,
   length(t.task_json)+length(r.result_json) AS source_bytes,
   (SELECT json_group_array(json_extract(requested.value,'$.id')) FROM json_each(?) requested
    WHERE EXISTS(SELECT 1 FROM json_each(t.task_json,'$.pages') saved
     WHERE json_extract(saved.value,'$.id')=json_extract(requested.value,'$.id')
      AND json_extract(saved.value,'$.text')=json_extract(requested.value,'$.text'))) AS matching_pages
  FROM local_tasks t JOIN local_task_results r ON r.id=(SELECT latest.id FROM local_task_results latest WHERE latest.task_id=t.id ORDER BY latest.created_at DESC,latest.id DESC LIMIT 1)
  WHERE t.input_version=? AND json_extract(t.task_json,'$.engine')=? AND json_extract(t.task_json,'$.alphabet')=? AND json_extract(t.task_json,'$.criterion')=?
   AND json_extract(t.task_json,'$.steps') IN (SELECT value FROM json_each(?))
   AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)
   AND EXISTS(SELECT 1 FROM json_each(?) requested JOIN json_each(t.task_json,'$.pages') saved ON json_extract(saved.value,'$.id')=json_extract(requested.value,'$.id') AND json_extract(saved.value,'$.text')=json_extract(requested.value,'$.text'))
  ORDER BY r.created_at DESC,r.id DESC,t.id LIMIT 8193`).bind(scope,version,E.ENGINE,alphabet,criterion,E.stable(steps),version,scope).all()).results;
 if(!Array.isArray(rows)||rows.length>MAX_ROWS+1)throw Error('The finite source index is malformed.');if(rows.length>MAX_ROWS)lookupComplete=false;
 const represented=new Set(),selected=[];let selectedBytes=0;
 for(const row of rows.slice(0,MAX_ROWS)){
  if(!HEX.test(row.task_id)||!HEX.test(row.task_hash)||!HEX.test(row.result_id)||!stepSet.has(row.steps)||!Number.isFinite(Date.parse(row.created_at))||!Number.isSafeInteger(row.source_bytes)||row.source_bytes<1)throw Error('A finite source reference is malformed.');
  const ids=JSON.parse(row.matching_pages);if(!Array.isArray(ids)||!ids.length||new Set(ids).size!==ids.length||ids.some(id=>!sourceTexts.has(id)))throw Error('A finite source scope is malformed.');
  const fresh=ids.filter(id=>!represented.has(row.steps+'|'+id));if(!fresh.length)continue;
  if(selectedBytes+row.source_bytes>MAX_BYTES){lookupComplete=false;continue;}selectedBytes+=row.source_bytes;selected.push(row);ids.forEach(id=>represented.add(row.steps+'|'+id));
 }
 if(selected.length){
  const fetched=(await db.prepare(`SELECT t.id AS task_id,t.task_hash,t.task_json,t.input_version,r.id AS result_id,r.result_json,r.created_at
   FROM json_each(?) proof JOIN local_tasks t ON t.id=json_extract(proof.value,'$.task_id') AND t.task_hash=json_extract(proof.value,'$.task_hash')
   JOIN local_task_results r ON r.task_id=t.id AND r.id=json_extract(proof.value,'$.result_id') AND r.created_at=json_extract(proof.value,'$.created_at')
   WHERE t.input_version=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=?)`).bind(E.stable(selected),version,version).all()).results;
  if(!Array.isArray(fetched)||fetched.length!==selected.length)throw Error('A selected finite source is unavailable.');
  const fetchedIds=new Set();for(const row of fetched){const pin=selected.find(r=>r.task_id===row.task_id);if(!pin||fetchedIds.has(row.task_id)||row.result_id!==pin.result_id||row.created_at!==pin.created_at)throw Error('A selected finite receipt changed.');fetchedIds.add(row.task_id);const task=JSON.parse(row.task_json);if(task.taskId!==row.task_id||await hash(task,cryptoAPI)!==row.task_hash)throw Error('A selected finite task changed.');await retain({task,inputVersion:version,run:{id:row.result_id,createdAt:row.created_at,result:JSON.parse(row.result_json)}},{href:'run.html#task='+row.task_id,label:'Inspect saved output'});}
 }
 if(version==='raw'){
  const families=(await db.prepare(`SELECT saved.family_id,saved.revision,saved.case_id,saved.task_id,saved.result_hash,saved.created_at,
   json_extract(saved.task_json,'$.steps') AS steps,json_extract(saved.task_json,'$.pages[0].id') AS page_id,
   length(saved.task_json)+length(saved.result_json) AS source_bytes
   FROM family_case_results saved WHERE saved.family_id='deor-feedback-v1'
   AND json_extract(saved.task_json,'$.engine')=? AND json_extract(saved.task_json,'$.alphabet')=? AND json_extract(saved.task_json,'$.criterion')=?
   AND json_extract(saved.task_json,'$.steps') IN (SELECT value FROM json_each(?))
   AND EXISTS(SELECT 1 FROM json_each(?) requested JOIN json_each(saved.task_json,'$.pages') actual ON json_extract(requested.value,'$.id')=json_extract(actual.value,'$.id') AND json_extract(requested.value,'$.text')=json_extract(actual.value,'$.text'))
   ORDER BY saved.created_at DESC,saved.revision DESC,saved.case_id LIMIT 8193`).bind(E.ENGINE,alphabet,criterion,E.stable(steps),scope).all()).results;
  if(!Array.isArray(families)||families.length>MAX_ROWS+1)throw Error('The family source index is malformed.');if(families.length>MAX_ROWS)lookupComplete=false;
  const chosen=[];let plannedBytes=bytes;
  for(const row of families.slice(0,MAX_ROWS)){
   if(!stepSet.has(row.steps)||!sourceTexts.has(row.page_id)||!HEX.test(row.task_id)||!HEX.test(row.result_hash)||!Number.isSafeInteger(row.source_bytes)||row.source_bytes<1)throw Error('A family source reference is malformed.');
   const key=row.steps+'|'+row.page_id;if(represented.has(key))continue;
   if(plannedBytes+row.source_bytes>MAX_BYTES){lookupComplete=false;continue;}plannedBytes+=row.source_bytes;represented.add(key);chosen.push(row);
  }
  if(chosen.length){
   const loaded=(await db.prepare(`SELECT saved.* FROM json_each(?) proof JOIN family_case_results saved
    ON saved.family_id=json_extract(proof.value,'$.family_id') AND saved.revision=json_extract(proof.value,'$.revision')
     AND saved.case_id=json_extract(proof.value,'$.case_id') AND saved.task_id=json_extract(proof.value,'$.task_id')
     AND saved.result_hash=json_extract(proof.value,'$.result_hash') AND saved.created_at=json_extract(proof.value,'$.created_at')`).bind(E.stable(chosen)).all()).results;
   if(!Array.isArray(loaded)||loaded.length!==chosen.length)throw Error('A selected family source is unavailable.');const seenFamilies=new Set();
   for(const row of loaded){const key=row.family_id+'|'+row.revision+'|'+row.case_id;if(seenFamilies.has(key))throw Error('A selected family source is repeated.');seenFamilies.add(key);const checked=await validateFamilyReceipt(row,cryptoAPI);await retain(checked.source,{href:'run.html#family=deor-feedback-v1&case='+row.case_id+'&revision='+row.revision,label:'Inspect family output'});}
  }
 }
 for(const registry of [PublishedCounts,PublishedPrograms])for(const item of registry.entries){
  if(item.inputVersion!==version||!stepSet.has(E.stable(item.task.steps))||E.stable(item.task.criterion)!==criterion)continue;
  const proof=await readPublishedEvidence({recordId:item.recordId,revision:item.revision,caseId:item.caseId,crypto:cryptoAPI});if(!proof)throw Error('A published finite source is unavailable.');await retain({task:proof.task,inputVersion:proof.inputVersion,run:proof.run},{href:'library.html#/experiment/'+item.recordId,label:'Inspect published calculations'});
 }
 return {sources,sourceLinks,lookupComplete};
}
