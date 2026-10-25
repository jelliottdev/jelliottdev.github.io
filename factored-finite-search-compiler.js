/* Full declared alternatives, compiled once against shared source text.
 * This prepares no target execution, task admission or public finding. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,H=node?require('./claim-share.js'):root.ClaimShare,J=node?require('./finite-json.js'):root.FiniteJSON,Inputs=node?require('./local-input-bundle.js'):root.LocalInputBundle,Settings=node?require('./finite-settings.js'):root.FiniteSettings,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,Q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion;
 const compiledBindings=new WeakMap();
 const captureCard=value=>J.capture(value,{maxBytes:H.MAX_BYTES,maxDepth:16,maxNodes:6000}),captureBundle=value=>J.capture(value,{maxBytes:2*1024*1024,maxDepth:16,maxNodes:6000});
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 async function compile(card,bundle,crypto=root.crypto){
  const original=captureCard(card),capturedBundle=captureBundle(bundle),source=Inputs.parse(capturedBundle),expanded=Settings.factored.expand(original);
  // Pin the full supplied source and card before any asynchronous identity work.
  const binding={card:E.stable(original),bundle:E.stable(capturedBundle)};
  if(original.rules.inputVersion.status!=='specified'||!['raw','reviewed'].includes(original.rules.inputVersion.value))throw Error('The complete search needs an explicit source text version.');
  if(original.rules.evaluation.status!=='specified'||original.rules.evaluation.value?.kind!=='exact-prefix')throw Error('The complete search needs an explicit exact opening.');
  const inputVersion=original.rules.inputVersion.value,criterion=original.rules.evaluation.value,pages=original.scope.value.pages.map(id=>{const row=source.pages.get(id),text=inputVersion==='raw'?row?.raw:row?.reviewed_text;if(typeof text!=='string')throw Error('A declared page has no text in this version.');return {id,text};});
  const programs=[],members=[];
  for(const variant of expanded.variants){
   const plan=Compiler.compile(variant.card);
   if(plan.reason||!Array.isArray(plan.steps))throw Error('A declared setting needs an execution adapter: '+(plan.reason||'unsupported program'));
   if(plan.inputVersion!==inputVersion||E.stable(plan.pages)!==E.stable(original.scope.value.pages)||E.stable(plan.criterion)!==E.stable(criterion))throw Error('A declared setting changed the common source, scope or opening.');
   programs.push({steps:plan.steps});members.push({steps:plan.steps,settings:variant.settings,notes:plan.notes});
  }
  const domain=await Q.bind({engine:E.ENGINE,inputVersion,alphabet:source.alphabet,pages,criterion,programs},crypto),identities=new Map(domain.programs.map(p=>[E.stable(p.steps),p.id]));
  const mapped=members.map(member=>{const programId=identities.get(E.stable(member.steps));if(!programId)throw Error('A validated program changed its ordered operations.');return {programId,settings:member.settings,notes:member.notes};});
  const output=freeze({declaration:expanded.declaration,domain,members:mapped});compiledBindings.set(output,binding);return output;
 }
 // This brand proves only compilation against these exact captured inputs.
 // It is not task admission, saved evidence, a target result or a public verdict.
 function inspect(compiled,inputs){const binding=compiledBindings.get(compiled);if(!binding)throw Error('Use this compiler’s original immutable compiled search.');if(!inputs||Object.keys(inputs).length!==2||!Object.hasOwn(inputs,'card')||!Object.hasOwn(inputs,'bundle'))throw Error('Supply the exact original card and source bundle.');const captured=J.capture(inputs,{maxBytes:2*1024*1024+H.MAX_BYTES,maxDepth:18,maxNodes:12000});if(binding.card!==E.stable(captureCard(captured.card))||binding.bundle!==E.stable(captureBundle(captured.bundle)))throw Error('The compiled search changed the original idea or official inputs.');return compiled;}
 const api={compile,inspect};if(node)module.exports=api;else root.FactoredFiniteSearchCompiler=api;
})(typeof globalThis!=='undefined'?globalThis:this);
