import {finiteSnapshotMember} from './authored-finite-origin.mjs';
/* Closed source relation for an exact reviewed remainder. Ordinary receipts stay ordinary. */
import E from '../../local-experiment.js';
import Compiler from '../../fixed-plan-compiler.js';
import {checkedEvidence} from './task-evidence.mjs';
const same=(a,b)=>E.stable(a)===E.stable(b),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:E.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
export async function scopeRelation(task,snapshot){
 if(snapshot?.kind==='finite-settings')return (await finiteSnapshotMember(task,snapshot)).scopeRelation;
 const declaredPages=snapshot.inputs.pages.map(p=>p.id),remainingPages=task.pages.map(p=>p.id);
 if(same(declaredPages,remainingPages))return null;
 const plan=Compiler.compile(snapshot.card);
 if(plan.reason||!remainingPages.length||remainingPages.length>=declaredPages.length||!same(remainingPages,declaredPages.filter(id=>remainingPages.includes(id)))||!same(plan.steps,task.steps)||!same(plan.criterion,task.criterion)||await hash(task.alphabet)!==snapshot.inputs.alphabet_sha256)throw Error('Stored remainder differs from its authored source');
 for(const page of task.pages)if(await hash(page.text)!==snapshot.inputs.pages.find(p=>p.id===page.id)?.text_sha256)throw Error('Stored remainder source bytes changed');
 return {kind:'remaining-pages',declaredPages,remainingPages};
}
export function metadata(reviewed,task){return {origin:reviewed.origin,control:reviewed.control,question:reviewed.question,scopeChange:reviewed.scopeChange,limitation:reviewed.limitation,...(task.pages.length<reviewed.task.pages.length?{scopeRelation:{kind:'remaining-pages',declaredPages:reviewed.task.pages.map(p=>p.id),remainingPages:task.pages.map(p=>p.id)}}:{})};}
export async function strictPrefixMatch({db,task,inputVersion,evidence}){
 if(task.criterion.kind!=='exact-prefix'||!evidence.length)return false;
 const {sources}=await checkedEvidence({db,task,inputVersion,evidence,includeSources:true}),pages=new Map(task.pages.map(p=>[p.id,p.text]));
 return sources.some(source=>source.task.pages.some(page=>pages.get(page.id)===page.text&&source.run.result.matches?.some(match=>match.page===page.id&&match.matched===true)));
}
export async function checkedRecordRemainder({basis,card,task,inputVersion,fetcher}){
 const strict=basis?.kind==='record-strict-evidence-remainder-v1';
 if(strict?!exact(basis,['kind','requestedTaskId','strictEvidence','origin','fullTaskHash','controlHash']):!exact(basis,['kind','remainderBasis','origin','fullTaskHash','controlHash'])||basis.kind!=='record-derived-prefix-remainder-v1'||basis.remainderBasis?.kind!=='ordinary-derived-prefix-remainder-v1')throw Error('Invalid authored remainder basis');
 const {loadSavedRecordPlan}=await import('./record-plans.mjs'),reviewed=await loadSavedRecordPlan(basis.origin,{fetcher});
 if(!same(reviewed.origin,basis.origin)||!same(reviewed.card,card)||reviewed.inputVersion!==inputVersion||!(strict?['measurement','word-affine-count','word-prime-sums','language-score'].includes(reviewed.task.criterion.kind):reviewed.task.criterion.kind==='exact-prefix')||await hash(reviewed.task)!==basis.fullTaskHash||await hash(reviewed.control)!==basis.controlHash||!same(reviewed.task.steps,task.steps)||!same(reviewed.task.criterion,task.criterion)||!same(reviewed.task.alphabet,task.alphabet)||!same(task.pages,reviewed.task.pages.filter(p=>task.pages.some(q=>q.id===p.id))))throw Error('The authored source, controls or remaining task changed');
 // A zero-covered first review may still request the complete task. The closed
 // evidence basis below remains responsible for the exact unanswered complement.
 return reviewed;
}
