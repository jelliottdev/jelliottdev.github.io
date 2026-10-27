/* Exact active archive metadata only. These links are not verified coverage. */
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import V from '../../task-parameter-variants.js';
import Programs from '../../published-opening-evidence-data.js';
import {publishedProgramIndex} from './published-evidence.mjs';
import {readEvidenceRegistryHash} from './factored-evidence-provider.mjs';

export const SCHEMA='liberpedia-archived-variation-navigation-v1';
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const need=(value,message)=>{if(!value)throw Error(message);};
const capture=value=>J.capture(value,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:250000});
const hash=async(value,crypto)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:E.stable(value)))),n=>n.toString(16).padStart(2,'0')).join('');
const signature=(engine,inputVersion,alphabetSha256,steps,criterion)=>E.stable([engine,inputVersion,alphabetSha256,steps,criterion]);

export async function archivedVariationNavigation({task,inputVersion},{crypto=globalThis.crypto,registry,programIndex,signal}={}){
 const original=capture(task),snapshot=E.stable(original),live=()=>{need(!signal?.aborted,'Archive navigation cancelled');need(E.stable(capture(task))===snapshot,'The navigation parent changed');};
 E.validateTask(original);need(['raw','reviewed'].includes(inputVersion),'Use an exact input edition');live();
 const index=await publishedProgramIndex({registry,programIndex});live();
 const embedded=registry===undefined?Programs:J.capture(registry,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000});
 need(embedded?.schema==='liberpedia-published-program-evidence-v1'&&Array.isArray(embedded.entries)&&embedded.entries.length<=1024,'Invalid program navigation registry');
 const bySignature=new Map(),add=item=>{const key=signature(E.ENGINE,item.inputVersion,item.alphabetSha256,item.steps,item.criterion);if(!bySignature.has(key))bySignature.set(key,[]);bySignature.get(key).push(item);};
 for(const item of index?.entries||[])add(item);
 // Only metadata is read here; neither a target nor another receipt is replayed.
 for(const entry of embedded.entries){
  E.validateTask(entry.task);need(['raw','reviewed'].includes(entry.inputVersion)&&typeof entry.recordId==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.recordId)&&entry.recordId.length<=100&&typeof entry.revision==='string'&&/^[a-f0-9]{64}$/.test(entry.revision)&&typeof entry.caseId==='string'&&/^[a-z0-9][a-z0-9-]*$/.test(entry.caseId)&&entry.caseId.length<=200,'Invalid embedded navigation pointer');
  add({recordId:entry.recordId,revision:entry.revision,caseId:entry.caseId,inputVersion:entry.inputVersion,alphabetSha256:await hash(entry.task.alphabet,crypto),steps:entry.task.steps,criterion:entry.task.criterion,pages:await Promise.all(entry.task.pages.map(async page=>({id:page.id,textSha256:await hash(page.text,crypto)})))});live();
 }
 const alphabetSha256=await hash(original.alphabet,crypto),pagePins=new Map(await Promise.all(original.pages.map(async page=>[page.id,await hash(page.text,crypto)]))),parentTaskHash=await hash(original,crypto);live();
 const choices=[];
 for(const item of V.suggestions(original)){
  const steps=V.changedSteps(original.steps,item.selection),candidates=bySignature.get(signature(original.engine,inputVersion,alphabetSha256,steps,original.criterion))||[];
  let best=null;
  for(const candidate of candidates){
   const matchingPageCount=candidate.pages.filter(page=>pagePins.get(page.id)===page.textSha256).length;if(!matchingPageCount)continue;
   const reference={recordId:candidate.recordId,revision:candidate.revision,caseId:candidate.caseId},tie=E.stable(reference);
   if(!best||matchingPageCount>best.matchingPageCount||matchingPageCount===best.matchingPageCount&&tie<best.tie)best={reference,matchingPageCount,tie};
  }
  if(best)choices.push({selection:item.selection,reference:best.reference,matchingPageCount:best.matchingPageCount});
 }
 need(choices.length<=2080,'Archive navigation exceeds its choice bound');live();
 const catalogGeneration=registry===undefined?await readEvidenceRegistryHash({programIndex,crypto}):await hash({index,registry:embedded},crypto);live();
 const value={schema:SCHEMA,parentTaskHash,inputVersion,catalogGeneration,choices};
 need(new TextEncoder().encode(E.stable(value)).byteLength<=2*1024*1024,'Archive navigation exceeds its response bound');
 return freeze(value);
}
