/* Exact authored-family membership; saved snapshots remain independent of later edits. */
import E from '../../local-experiment.js';
import Control from '../../local-control.js';
import Settings from '../../finite-settings.js';
import Compiler from '../../fixed-plan-compiler.js';
import {loadSavedFiniteRecordPlan} from './finite-record-plans.mjs';
const same=(a,b)=>E.stable(a)===E.stable(b),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),HEX=/^[a-f0-9]{64}$/;
const hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');
const require=(v,m)=>{if(!v)throw Error(m);};
const memberDeclarations=new Map(),MAX_MEMBER_BYTES=16*1024*1024;let memberBytes=0;
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
function checkedMemberDeclaration(snapshot){
 const serialized=E.stable(snapshot),bytes=new TextEncoder().encode(serialized).byteLength;require(bytes<=2*1024*1024,'Stored finite snapshot exceeds its bound');const cached=memberDeclarations.get(serialized);if(cached){memberDeclarations.delete(serialized);memberDeclarations.set(serialized,cached);return cached;}
 const owned=JSON.parse(serialized),expanded=Settings.factored.expand(owned.card),members=owned.control.members;require(Array.isArray(members)&&members.length===expanded.variants.length,'Incomplete stored finite controls');const programs=new Map();
 for(let i=0;i<expanded.variants.length;i++){const variant=expanded.variants[i],plan=Compiler.compile(variant.card);require(!plan.reason&&same(members[i].settings,variant.settings),'Stored finite member changed');const key=E.stable([plan.steps,plan.criterion]);require(!programs.has(key),'Ambiguous stored finite member');programs.set(key,{settings:variant.settings,control:members[i].control});}
 freeze(owned);const entry={snapshot:owned,programs,bytes};while(memberDeclarations.size&&(memberDeclarations.size>=8||memberBytes+bytes>MAX_MEMBER_BYTES)){const first=memberDeclarations.keys().next().value;memberBytes-=memberDeclarations.get(first).bytes;memberDeclarations.delete(first);}memberDeclarations.set(serialized,entry);memberBytes+=bytes;return entry;
}
export function createAuthoredFiniteSourceLoader(fetcher=globalThis.fetch,{loadBundle}={}){
 const cache=new Map();return async origin=>{require(exact(origin,['recordId','followupId','recordSha256','protocolSha256'])&&HEX.test(origin.recordSha256)&&HEX.test(origin.protocolSha256),'Invalid authored finite origin');const key=E.stable(origin);if(!cache.has(key)){require(cache.size<8,'Too many authored finite sources');cache.set(key,loadSavedFiniteRecordPlan(origin,{fetcher,loadBundle}).then(source=>{require(same(source.origin,origin),'The authored finite source changed');return source;}));}return cache.get(key);};
}
export async function finiteSnapshotMember(task,snapshot){
 require(snapshot?.kind==='finite-settings'&&snapshot.control?.kind==='finite-program-controls','Invalid stored finite snapshot');
 const declaration=checkedMemberDeclaration(snapshot);snapshot=declaration.snapshot;const found=declaration.programs.get(E.stable([task.steps,task.criterion]));
 require(found,'Task is outside its authored finite family');
 const pins=snapshot.inputs,declaredPages=pins.pages.map(p=>p.id),remainingPages=task.pages.map(p=>p.id);
 require(same(declaredPages,snapshot.card.scope.value.pages)&&remainingPages.length>0&&same(remainingPages,declaredPages.filter(id=>remainingPages.includes(id)))&&await hash(task.alphabet)===pins.alphabet_sha256,'Stored finite scope or alphabet changed');
 for(const page of task.pages)require(await hash(page.text)===pins.pages.find(p=>p.id===page.id)?.text_sha256,'Stored finite page bytes changed');
 const control=found.control;await E.checkIdentity(control.task);require(same(control.task.steps,task.steps)&&same(control.task.alphabet,task.alphabet),'Stored finite witness changed');
 const count=Array.from(control.task.pages[0]?.text||'').filter(ch=>task.alphabet.some(r=>r.rune===ch)).length;
 require(control.task.pages.length===1&&control.task.criterion.kind==='exact-prefix'&&control.task.criterion.values.length===count&&count>0&&count<=256,'Stored finite witness must check its full output');
 const result=E.run(control.task);require(Control.passed(control.task,result)&&await hash(result)===control.expected_result_sha256,'Stored finite witness result changed');
 return {control,scopeRelation:{kind:'finite-settings-member',card:snapshot.card,settings:found.settings,declaredPages,remainingPages}};
}
// Read-only projection of an immutable snapshot admitted by the task writer.
// The caller must verify its persisted protocol digest before calling this.
// Fresh source/member admission continues through finiteSnapshotMember above.
export async function readAdmittedFiniteSnapshotMember(task,snapshot){
 require(snapshot?.kind==='finite-settings'&&snapshot.control?.kind==='finite-program-controls'&&Array.isArray(snapshot.control.members)&&snapshot.control.members.length>0&&snapshot.control.members.length<=1024,'Invalid admitted finite snapshot');
 const matches=snapshot.control.members.filter(member=>same(member?.control?.task?.steps,task.steps));require(matches.length===1,'The admitted task has no unique finite member');const found=matches[0],member=Settings.factored.member(snapshot.card,found.settings),plan=Compiler.compile(member.card);
 require(!plan.reason&&!plan.state&&same(plan.steps,task.steps)&&same(plan.criterion,task.criterion)&&same(member.settings,found.settings),'The admitted finite program or criterion changed');
 const pins=snapshot.inputs,declaredPages=pins.pages.map(p=>p.id),remainingPages=task.pages.map(p=>p.id);require(pins.version===plan.inputVersion&&same(declaredPages,snapshot.card.scope.value.pages)&&remainingPages.length>0&&same(remainingPages,declaredPages.filter(id=>remainingPages.includes(id)))&&await hash(task.alphabet)===pins.alphabet_sha256,'Admitted finite scope or alphabet changed');
 for(const page of task.pages)require(await hash(page.text)===pins.pages.find(p=>p.id===page.id)?.text_sha256,'Admitted finite page bytes changed');
 const control=found.control;await E.checkIdentity(control.task);require(HEX.test(control.expected_result_sha256)&&same(control.task.steps,task.steps)&&same(control.task.alphabet,task.alphabet),'Admitted finite witness changed');
 const runes=new Set(task.alphabet.map(r=>r.rune)),count=Array.from(control.task.pages[0]?.text||'').filter(ch=>runes.has(ch)).length;require(control.task.pages.length===1&&control.task.criterion.kind==='exact-prefix'&&control.task.criterion.values.length===count&&count>0&&count<=256,'Admitted finite witness must check its full output');
 return {control,scopeRelation:{kind:'finite-settings-member',card:snapshot.card,settings:found.settings,declaredPages,remainingPages}};
}
export async function checkedAuthoredFiniteMember({basis,card,task,inputVersion,loadAuthoredSource,fetcher}){
 require(exact(basis,['kind','origin','domainId','memberBasis'])&&basis.kind==='authored-finite-member-v1'&&HEX.test(basis.domainId)&&['finite-settings','factored-finite-settings','factored-output-settings','factored-inspection-settings','factored-page-group-v1'].includes(basis.memberBasis?.kind),'Invalid authored finite preparation basis');
 const source=await (loadAuthoredSource||createAuthoredFiniteSourceLoader(fetcher))(basis.origin);
 require(source.state==='finite-plan-ready'&&same(source.origin,basis.origin)&&same(source.card,card)&&source.inputVersion===inputVersion&&source.domain.domainId===basis.domainId,'The authored finite card, source or domain changed');
 require(basis.memberBasis.kind!=='factored-page-group-v1'||basis.memberBasis.domainId===basis.domainId,'The authored finite page-group domain changed');
 const projected=await finiteSnapshotMember(task,source.snapshot);require(same(projected.scopeRelation.settings,basis.memberBasis.settings),'Prepared finite settings changed');
 return {...source,task,control:projected.control,scopeRelation:projected.scopeRelation};
}
