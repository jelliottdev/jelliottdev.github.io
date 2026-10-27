/* Typed method-check choices. Capability facts are not intent matching or passed controls. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const J=node?require('./finite-json.js'):root.FiniteJSON;
 const LIMITS=Object.freeze({bytes:65536,nodes:20000,prefix:256,openings:32});
 const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
 const need=(ok,message)=>{if(!ok)throw Error(message);};
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
 const capture=value=>J.capture(value,{maxBytes:LIMITS.bytes,maxDepth:10,maxNodes:LIMITS.nodes});
 const object=properties=>({type:'object',additionalProperties:false,required:Object.keys(properties),properties});
 const literal=kind=>object({kind:{const:kind}});
 const described=length=>object({kind:{const:'described'},description:{type:'string',minLength:1,maxLength:length}});
 const values={type:'array',minItems:1,maxItems:LIMITS.prefix,items:{type:'integer',minimum:0,maximum:28}};
 // Intent metadata only: full scoring still requires the maintained runtime.
 const LANGUAGE_CRITERION=Object.freeze({kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'}),pinned=LANGUAGE_CRITERION;
 const EVALUATION_SCHEMA=freeze({anyOf:[literal('output-measurements'),literal('original-output-measurements'),object({kind:{const:'exact-prefix'},values}),object({kind:{const:'exact-prefix-set'},openings:{type:'array',minItems:1,maxItems:LIMITS.openings,items:object({id:{type:'string',pattern:'^[a-z][a-z0-9-]{0,63}$'},values})}}),object({kind:{const:'language-score'},modelId:{const:pinned.modelId},modelSha256:{const:pinned.modelSha256}}),described(500)]});
 const CONTROL_SCHEMA=freeze({anyOf:[literal('implementation-sanity-v2'),described(400)]});
 const REPRESENTATION_SCHEMA=freeze({anyOf:[literal('gp29'),described(160)]});
 const JSON_SCHEMA=freeze({evaluation:EVALUATION_SCHEMA,control:CONTROL_SCHEMA,representation:REPRESENTATION_SCHEMA});
 const FACTS=freeze({
  measurements:{scope:'all-output-pages',fields:['pages','runes','adjacentPairs','equalAdjacentPairs','ioc'],adjacency:'rune-only-within-each-page',ioc:'pooled-output-rune-frequencies',limit:'Aggregate descriptive measurements only. They do not test significance, filler, readability, a target language or decryption.'},
  representation:{kind:'gp29',minimum:0,maximum:28,limit:'This states the program representation, not that an arbitrary described representation means the same thing.'},
  control:{referenceVersion:2,state:'planned',caseIds:['layout-forward','layout-reversed','empty-separators'],limit:'These are synthetic implementation checks, not a scientific null comparison or a test of the hypothesis. Short finite keys can restrict the synthetic patterns that fit.'}
 });
 function plain(value,max){need(typeof value==='string'&&value.trim().length>0&&Array.from(value).length<=max&&!/[\u0000-\u001f\u007f-\u009f\u2028\u2029\ud800-\udfff]/u.test(value),'Use bounded nonempty plain description text.');}
 function description(value,max){need(exact(value,['kind','description'])&&value.kind==='described','Use the exact described check shape.');plain(value.description,max);}
 function sequence(value){need(Array.isArray(value)&&value.length>=1&&value.length<=LIMITS.prefix&&value.every(n=>Number.isSafeInteger(n)&&n>=0&&n<=28),'Use one to 256 literal rune indices from zero through twenty-eight.');}
 function validateEvaluation(input){
  const value=capture(input);need(value&&typeof value==='object'&&!Array.isArray(value),'Use a typed evaluation choice.');
  if(['output-measurements','original-output-measurements'].includes(value.kind))need(exact(value,['kind']),'Output measurements take no hidden conditions.');
  else if(value.kind==='exact-prefix'){need(exact(value,['kind','values']),'Use the exact literal opening shape.');sequence(value.values);}
  else if(value.kind==='exact-prefix-set'){
   need(exact(value,['kind','openings'])&&Array.isArray(value.openings)&&value.openings.length>=1&&value.openings.length<=LIMITS.openings,'Use one to 32 named literal openings.');
   const ids=new Set(),vectors=new Set();
   for(const opening of value.openings){need(exact(opening,['id','values'])&&typeof opening.id==='string'&&opening.id.length>=1&&opening.id.length<=64&&/^[a-z][a-z0-9-]{0,63}$/.test(opening.id)&&!ids.has(opening.id),'Use distinct exact opening identifiers.');sequence(opening.values);const vector=JSON.stringify(opening.values);need(!vectors.has(vector),'Named opening sequences must be distinct.');ids.add(opening.id);vectors.add(vector);}
  }else if(value.kind==='language-score')need(exact(value,['kind','modelId','modelSha256'])&&value.modelId===LANGUAGE_CRITERION.modelId&&value.modelSha256===LANGUAGE_CRITERION.modelSha256,'Use the exact maintained language-score metadata.');
  else if(value.kind==='described')description(value,500);
  else throw Error('This evaluation choice is not maintained.');
  return freeze(value);
 }
 function validateControl(input){const value=capture(input);if(value?.kind==='implementation-sanity-v2')need(exact(value,['kind']),'Standard synthetic checks take no hidden conditions.');else description(value,400);return freeze(value);}
 function validateRepresentation(input){const value=capture(input);if(value?.kind==='gp29')need(exact(value,['kind']),'GP29 takes no hidden representation conditions.');else description(value,160);return freeze(value);}
 function describeEvaluation(input){
  const value=validateEvaluation(input);
  if(value.kind==='described')return value.description;
  if(value.kind==='original-output-measurements')return 'Compare the same original and changed pages: rune counts, equal adjacent-pair counts and rates, and pooled index of coincidence. Pair counts ignore separators within each page; no pair crosses a page boundary. Use each side’s own pair denominator. This describes changes only; it does not test significance, filler, readability or decryption.';
  if(value.kind==='output-measurements')return 'Report aggregate output page and rune counts, adjacent rune-pair counts, equal adjacent rune-pair counts and index of coincidence. Adjacent pairs ignore separators within each page; no pair crosses a page boundary. Index of coincidence pools the output rune frequencies. No significance, readability or hypothesis verdict is requested.';
  if(value.kind==='exact-prefix')return 'Check each output page’s opening against these exact rune indices: '+value.values.join(', ')+'. A match is not a complete reading.';
  if(value.kind==='exact-prefix-set')return 'Check each output page’s opening against these exact named rune sequences: '+value.openings.map(opening=>opening.id+' ['+opening.values.join(', ')+']').join('; ')+'. A match is not a complete reading.';
  return 'Compare each output page with the eight maintained rune-language reference tables using 32 fixed shuffles. Pages with fewer than 40 output runes are insufficient. These scores do not identify a language or establish readability.';
 }
 function summarizeEvaluation(input){
  const value=validateEvaluation(input);
  if(value.kind==='described')return value.description;
  if(value.kind==='original-output-measurements')return 'Compare the original and changed text: rune counts, repeated pairs and rune concentration. A difference alone cannot establish filler, readable text or a solution.';
  if(value.kind==='output-measurements')return 'Count the output runes and repeated pairs. These counts alone cannot establish filler, readable text or a solution.';
  if(value.kind==='exact-prefix')return 'Check whether each output page starts with the specified rune sequence. A matching opening is not a complete reading.';
  if(value.kind==='exact-prefix-set')return 'Check whether each output page starts with one of the specified rune sequences. A matching opening is not a complete reading.';
  return 'Compare the output with eight fixed language samples. A high score is not a translation.';
 }
 function describeControl(input){const value=validateControl(input);return value.kind==='described'?value.description:'Plan to run the three independent version-two synthetic implementation checks before the selected text. They compare complete outputs, removal alignment and result arithmetic with an independent reference. This selection does not mean that the checks have passed or that the hypothesis has been tested.';}
 function describeRepresentation(input){const value=validateRepresentation(input);return value.kind==='described'?value.description:'Use the supplied ordered GP29 rune alphabet, represented by integer indices from 0 through 28.';}
 function resolveEvaluation(input){const value=validateEvaluation(input);if(value.kind==='described')return null;return ['output-measurements','original-output-measurements'].includes(value.kind)?freeze({kind:'measurement'}):value;}
 function resolveControl(input){const value=validateControl(input);return freeze({supported:value.kind==='implementation-sanity-v2',kind:value.kind,description:describeControl(value),limit:value.kind==='described'?'The described control has no maintained typed implementation.':FACTS.control.limit,...(value.kind==='implementation-sanity-v2'?{referenceVersion:2,state:'planned',caseIds:FACTS.control.caseIds}:{})});}
 function resolveRepresentation(input){const value=validateRepresentation(input);return freeze({supported:value.kind==='gp29',kind:value.kind,description:describeRepresentation(value),limit:value.kind==='described'?'The described representation has no maintained typed implementation.':FACTS.representation.limit,...(value.kind==='gp29'?{minimum:0,maximum:28}:{})});}
 const api=Object.freeze({LIMITS,LANGUAGE_CRITERION,EVALUATION_SCHEMA,CONTROL_SCHEMA,REPRESENTATION_SCHEMA,JSON_SCHEMA,FACTS,validateEvaluation,validateControl,validateRepresentation,describeEvaluation,summarizeEvaluation,describeControl,describeRepresentation,resolveEvaluation,resolveControl,resolveRepresentation});
 if(node)module.exports=api;else root.MethodCheckContract=api;
})(typeof globalThis!=='undefined'?globalThis:this);
