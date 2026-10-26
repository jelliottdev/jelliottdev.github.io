/* Shared finite settings compilation; no inference, task creation or target execution. */
(function(root){'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,Evidence=node?require('./computation-evidence.js'):root.ComputationEvidence,Settings=node?require('./finite-settings.js'):root.FiniteSettings,Questions=node?require('./finite-program-question.js'):root.FiniteProgramQuestion,Share=node?require('./claim-share.js'):root.ClaimShare,Json=node?require('./finite-json.js'):root.FiniteJSON,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle;
const LIMITS=Object.freeze({expandedBytes:8*1024*1024,runeWork:2000000,sourceBytes:2*1024*1024});
function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}

async function compileFiniteSearch(card,bundle,cryptoAPI=globalThis.crypto){
 // Capture the supplied idea and source before the first asynchronous digest.
 // This function never interprets prose, changes an idea or writes a task.
 const original=Json.capture(card,{maxBytes:Share.MAX_BYTES,maxDepth:16,maxNodes:6000}),source=Inputs.parse(Json.capture(bundle,{maxBytes:LIMITS.sourceBytes,maxDepth:16,maxNodes:6000})),declaration=Settings.inspect(original);
 if(original.rules.inputVersion.status!=='specified'||!['raw','reviewed'].includes(original.rules.inputVersion.value))throw Error('A finite search needs an explicit raw or reviewed text version.');
 const version=original.rules.inputVersion.value,evaluation=original.rules.evaluation;
 if(evaluation.status!=='specified'||!['exact-prefix','exact-prefix-set'].includes(evaluation.value?.kind))throw Error('This finite search needs an explicit exact opening or opening-set check.');
 const pages=original.scope.value.pages.map(id=>{
  const row=source.pages.get(id),text=version==='raw'?row?.raw:row?.reviewed_text;
  if(typeof text!=='string')throw Error('A declared page has no text in the selected version.');
  return {id,text};
 });
 const runes=new Set(source.alphabet.map(row=>row.rune)),runeCount=pages.reduce((n,page)=>n+Array.from(page.text).filter(ch=>runes.has(ch)).length,0);
 // Reject over-budget declarations before allocating repeated task bodies.
 const sourceBytes=new TextEncoder().encode(E.stable({pages,alphabet:source.alphabet})).byteLength;
 if(declaration.programCount*sourceBytes>LIMITS.expandedBytes||declaration.programCount*runeCount>LIMITS.runeWork)throw Error('The complete declared search exceeds the supported work or input budget. Narrow the declared settings or pages; no cases were omitted.');
 const expanded=Settings.expand(original),compiled=[];
 let bytes=0;
 for(const [index,variant] of expanded.variants.entries()){
  const plan=Compiler.compile(variant.card);
  if(plan.reason||!Array.isArray(plan.steps))throw Error('Setting '+(index+1)+' needs an execution adapter: '+(plan.reason||'unsupported program'));
  if(plan.inputVersion!==version||E.stable(plan.pages)!==E.stable(original.scope.value.pages)||E.stable(plan.criterion)!==E.stable(evaluation.value))throw Error('A search member changed the shared pages, text version or opening check.');
  const input={title:'Declared finite search member',alphabet:source.alphabet,pages,steps:plan.steps,criterion:plan.criterion};
  bytes+=new TextEncoder().encode(E.stable(input)).byteLength;
  if(bytes>LIMITS.expandedBytes)throw Error('The complete declared programs exceed the supported size budget. No cases were omitted.');
  const task=await E.prepare(input,cryptoAPI),descriptor=await Evidence.describe(task,version,cryptoAPI);
  compiled.push({task,programId:descriptor.protocolId,settings:variant.settings,notes:plan.notes});
 }
 const domain=await Questions.bind({programs:compiled.map(item=>item.task),inputVersion:version},cryptoAPI);
 return freeze({declaration,domain,members:compiled.map(({programId,settings,notes})=>({programId,settings,notes}))});
}

const api={compile:compileFiniteSearch,LIMITS};if(node)module.exports=api;else root.FiniteSearchCompiler=api;
})(typeof globalThis!=='undefined'?globalThis:this);
