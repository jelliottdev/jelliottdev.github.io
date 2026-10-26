/* Source-review metadata only. This is not a branded executable domain. */
import E from '../../local-experiment.js';
import Settings from '../../finite-settings.js';
import Fixed from '../../fixed-plan-compiler.js';
import Evaluators from '../../output-evaluators.js';
import Json from '../../finite-json.js';
import Share from '../../claim-share.js';
const same=(a,b)=>E.stable(a)===E.stable(b),require=(v,m)=>{if(!v)throw Error(m);},bytes=v=>new TextEncoder().encode(E.stable(v)).byteLength;
const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
const hash=async(v,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
export async function describeFiniteSource(input,{crypto=globalThis.crypto,signal}={}){
 const card=Json.capture(input.card,{maxBytes:Share.MAX_BYTES,maxDepth:16,maxNodes:6000}),{alphabet,pages}=Json.capture({alphabet:input.alphabet,pages:input.pages},{maxBytes:2*1024*1024,maxDepth:16,maxNodes:6000});
 const live=()=>{if(signal?.aborted)throw Error('Finite source loading cancelled.');};live();
 // The shared grammar/canonical boundary checks all axes and the detached-size
 // budget once. Substituting validated literals does not change the other fields.
 const declaration=Settings.factored.inspect(card),version=card.rules.inputVersion,evaluation=card.rules.evaluation;
 require(version.status==='specified'&&['raw','reviewed'].includes(version.value),'The complete search needs an explicit source text version.');require(evaluation.status==='specified','The finite evaluation must be explicit.');
 const inspection=evaluation.value==='measurement',language=Evaluators.identify(evaluation.value),criterion=inspection?{kind:'measurement'}:evaluation.value;
 require(inspection||language||['exact-prefix','exact-prefix-set'].includes(criterion?.kind),'The finite source needs a maintained explicit evaluation.');
 require(same(pages.map(p=>p.id),card.scope.value.pages),'The complete source scope changed.');
 const ordered=pages.slice().sort((a,b)=>a.id.localeCompare(b.id)),shared=await E.prepare({title:'Validate shared finite inputs',pages:ordered,alphabet,steps:[],criterion},crypto);live();
 const base={...shared,title:'Validate finite program',taskId:'0'.repeat(64)},baseBytes=bytes(base),programs=[],members=[],seen=new Set(),axes=declaration.parameters;
 const variants=[];function visit(index,settings){if(index<axes.length){const axis=axes[index];for(const value of axis.values)visit(index+1,[...settings,{operation:axis.operation,name:axis.name,value}]);return;}variants.push(settings);}visit(0,[]);
 for(const settings of variants){
  live();const operations=card.method.value.operations.map(operation=>({...operation}));for(const setting of settings)operations[setting.operation][setting.name]=setting.value;
  const member={...card,method:{...card.method,value:{...card.method.value,operations}},rules:{...card.rules,searchBounds:{status:'not_applicable'}}},plan=Fixed.compile(member);
  require(!plan.reason&&!plan.state&&Array.isArray(plan.steps),'A declared setting needs an execution adapter: '+(plan.reason||'unsupported program'));
  require(plan.inputVersion===version.value&&same(plan.pages,card.scope.value.pages)&&same(plan.criterion,criterion),'A declared setting changed its common source, scope or evaluation.');
  // All supported operations preserve rune geometry. Only a finite key stream
  // has a geometry-dependent step bound; validate that over every real page.
  // Other programs still pass the maintained engine grammar on a small page.
  E.validateTask({...base,steps:plan.steps,pages:plan.steps.some(step=>step.op==='finite-shift')?shared.pages:[{id:ordered[0].id,text:''}]});
  require(baseBytes+bytes(plan.steps)-2<=2000000,'The task exceeds the local runner file limit.');
  const id=await hash({schema:'liberpedia-computation-protocol-v1',engine:E.ENGINE,inputVersion:version.value,alphabet:shared.alphabet,steps:plan.steps,criterion:shared.criterion},crypto);live();require(!seen.has(id),'Duplicate or changed computation protocol.');seen.add(id);programs.push({id,steps:plan.steps});members.push({programId:id,settings,notes:plan.notes});
 }
 programs.sort((a,b)=>a.id.localeCompare(b.id));const body={schema:inspection||language?'liberpedia-factored-finite-output-question-v1':'liberpedia-factored-finite-question-v2',...(inspection||language?{questionPolicy:inspection?'transformed-output-inspection-v1':'language-reference-comparison-v1'}:{}),engine:E.ENGINE,inputVersion:version.value,alphabet:shared.alphabet,pages:shared.pages,criterion:shared.criterion,programs,totalCases:programs.length*shared.pages.length};
 require(bytes({...body,id:'0'.repeat(64)})<=4*1024*1024,'The complete factored domain exceeds its metadata byte bound.');const id=await hash(body,crypto);live();return freeze({declaration,domain:{...body,id},members});
}
