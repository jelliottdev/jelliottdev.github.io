/* Shared fixed-program compiler. Callers validate canonical cards before compilation. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,L=node?require('./local-experiment.js'):root.LocalExperiment,C=node?require('./claim-specification.js'):root.ClaimSpecification,Protocols=node?require('./experiment-protocols.js'):root.ExperimentProtocols,Evaluators=node?require('./output-evaluators.js'):root.OutputEvaluators;
const fail=reason=>({reason});
const MEASUREMENTS=Protocols.list(),MEASUREMENT_IDS=new Set(MEASUREMENTS.map(d=>d.operation.id)),MEASUREMENT_KINDS=new Set(MEASUREMENTS.map(d=>d.id));
const KEYED_REASON='A keyed step needs explicit GP indices (0–28), add or subtract, and a page, line or word reset.';
function missingRepeatingKeyChoice(card,operation,operationIndex){
 // A validation-only probe checks the unchanged surrounding program. Its
 // temporary completions never become an output plan or proposed parameter.
 const operations=card.method.value.operations;if(operations.length>8)return null;
 const eligible=op=>op?.id==='repeating_key'&&!Object.keys(op).some(k=>!['id','label','key','direction','reset'].includes(k))&&Array.isArray(op.key)&&op.key.length>0&&op.key.length<=256&&op.key.every(n=>Number.isInteger(n)&&n>=0&&n<=28)
  &&['direction','reset'].some(key=>!Object.hasOwn(op,key))&&(!Object.hasOwn(op,'direction')||['subtract','add'].includes(op.direction))&&(!Object.hasOwn(op,'reset')||['page','line','word'].includes(op.reset));
 if(!eligible(operation)||operations.filter(eligible).length!==1)return null;
 const rules=card.rules,globalReset=typeof rules.reset.value==='string'?(rules.reset.value.match(/^reset at each (page|line|word)$/i)?.[1].toLowerCase()||rules.reset.value):rules.reset.value;
 if(rules.reset.status==='specified'&&(!Object.hasOwn(operation,'reset')||globalReset!==operation.reset)||rules.reset.status==='not_applicable'||operations.length===1&&(rules.boundaryMode.status==='specified'||rules.initialState.status==='specified'))return null;
 const missing=['direction','reset'].filter(key=>!Object.hasOwn(operation,key)),parameter=missing[0];
 const completed={...operation,...Object.fromEntries(missing.map(key=>[key,key==='direction'?'subtract':'page']))},probe={...card,method:{...card.method,value:{...card.method.value,operations:operations.map((op,index)=>index===operationIndex?completed:op)}}},checked=compile(probe);
 if(checked.reason||!Array.isArray(checked.steps))return null;
 const choices=parameter==='direction'?[{id:'subtract',value:'subtract',label:'Subtract key indices'},{id:'add',value:'add',label:'Add key indices'}]:['page','line','word'].map(value=>({id:value,value,label:'Restart the key at each '+value}));
 return {state:'needs-clarification',field:'method',reason:KEYED_REASON,clarification:{version:1,kind:'keyed-operation',operationIndex,operationId:'repeating_key',parameter,choices}};
}
function evaluationIssue(card){
 const evaluation=card.rules.evaluation;
 if(C.normalizeOutcome(card.outcome).id==='decipher'&&evaluation.status!=='specified')return {state:'needs-clarification',field:'evaluation',reason:'Choose what this experiment should check before preparing it.'};
 if(evaluation.status!=='specified')return null;
 const value=evaluation.value;
 if(value==='readability'||value&&typeof value==='object'&&value.kind==='readability')return {state:'needs-adapter',field:'evaluation',reason:'Readable-text evaluation is not available yet. This idea has not been tested for readable text.'};
 const prefix=value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===2&&value.kind==='exact-prefix'&&Array.isArray(value.values)&&value.values.length>=1&&value.values.length<=256&&value.values.every(n=>Number.isInteger(n)&&n>=0&&n<=28);
 if(value!=='measurement'&&!prefix&&!Protocols.identify(value)&&!Evaluators.identify(value))return {state:'needs-adapter',field:'evaluation',reason:'The requested evaluation needs an adapter.'};
 return null;
}
function compile(card){
 const evaluation=evaluationIssue(card);if(evaluation)return evaluation;
 if(card.unresolved.length)return fail('The idea still has unresolved conditions.');
 if(card.method.status!=='specified'||!card.method.value.operations.length)return fail('An explicit supported method is needed.');
 if(card.scope.status!=='specified'||!Array.isArray(card.scope.value.pages)||!card.scope.value.pages.length||Object.keys(card.scope.value).some(k=>k!=='pages'))return fail('Select exact complete pages; passages and descriptive scope need an adapter.');
 const rules=card.rules,operations=card.method.value.operations,notes=[];
 if(Object.values(rules).some(rule=>rule.status==='unrestricted'))return fail('An explicitly unrestricted rule cannot be represented by one fixed experiment.');
 let inputVersion='raw',criterion={kind:'measurement'};
 const specified=k=>rules[k].status==='specified';
 const resetValue=value=>typeof value==='string'?(value.match(/^reset at each (page|line|word)$/i)?.[1].toLowerCase()||value):value;
 if(specified('inputVersion')){
  if(!['raw','reviewed'].includes(rules.inputVersion.value))return fail('The specified input version needs an adapter.');
  inputVersion=rules.inputVersion.value;
 }else notes.push('Proposed input: the archived raw transcription.');
 if(specified('representation')&&rules.representation.value!=='GP29')return fail('The specified representation needs an adapter.');
 notes.push('Use the canonical ordered 29-rune GP alphabet; preserve non-rune characters.');
 if(specified('unmapped')&&rules.unmapped.value!=='preserve')return fail('The rule for non-rune characters needs an adapter.');
 if(specified('wordBoundaries')&&rules.wordBoundaries.value!=='preserve')return fail('The word-boundary rule needs an adapter.');
 if(specified('evaluation')){
  const value=rules.evaluation.value;
  if(value==='measurement')criterion={kind:'measurement'};
  else if(value&&typeof value==='object'&&value.kind==='exact-prefix'&&Object.keys(value).length===2&&Object.hasOwn(value,'values'))criterion={kind:value.kind,values:value.values};
  else if(Protocols.identify(value))criterion={...value};
  else if(Evaluators.identify(value)){criterion=Evaluators.criterion();notes.push(Evaluators.describe(value).plan,Evaluators.describe(value).limit);}
  else return fail('The requested evaluation needs an adapter.');
 }else notes.push('Proposed evaluation: measure rune frequencies and adjacent repeats; no readability decision.');
 for(const key of ['searchBounds','searchProtocol','exceptionalCases'])if(specified(key))return fail('The specified '+key+' condition needs an adapter.');
 if(operations.some(op=>MEASUREMENT_IDS.has(op.id))){
  const op=operations[0],withoutFamily={...op};delete withoutFamily.declaredFamilyId;
  if(Object.hasOwn(op,'declaredFamilyId')&&(typeof op.declaredFamilyId!=='string'||!Object.hasOwn(C.METHOD_FAMILIES,op.declaredFamilyId)))return fail('A declared method family must use the maintained vocabulary.');
  const expected=Protocols.fromOperation(withoutFamily);
  if(operations.length!==1||!expected)return fail('The measurement needs one explicit supported operation.');
  if(L.stable(criterion)!==L.stable(expected))return fail('The measurement parameters and explicit evaluation must agree.');
  if(['boundaryMode','reset','initialState'].some(specified)||rules.wordBoundaries.status==='not_applicable')return fail('The measurement boundary conflicts with another supplied rule.');
  notes.push(Protocols.describe(criterion).compilerNote);
  return {pages:card.scope.value.pages,steps:[],inputVersion,criterion,notes};
 }
 if(MEASUREMENT_KINDS.has(criterion.kind))return fail('The evaluation needs its matching measurement operation.');
 const steps=[];let reverse=false,cumulative=false,keyed=false;
 const keyedModes={vigenere:'repeat',repeating_key:'repeat',plaintext_autokey:'plaintext-autokey',ciphertext_autokey:'ciphertext-autokey'};
 for(const [operationIndex,operation] of operations.entries()){
  const labels={reverse_row_runes:['Reverse rune order within rows','Reverse rune order within each row'],reverse_runes:['Reverse rune order within each line','Reverse rune order within each word','Reverse rune order within each page'],affine:['Affine','Affine substitution'],cumulative_difference:['Cumulative difference'],vigenere:['Vigenere','Vigenère'],repeating_key:['Repeating key','Repeating-key','Vigenere','Vigenère'],plaintext_autokey:['Plaintext autokey','Plaintext-autokey'],ciphertext_autokey:['Ciphertext autokey','Ciphertext-autokey'],finite_key:['Finite key stream'],interrupted_repeating_key:['Interrupted repeating key']};
  if(Object.hasOwn(operation,'label')&&(!labels[operation.id]||!labels[operation.id].includes(operation.label)))return fail('The operation wording contains details that need an execution adapter.');
  if(Object.keys(operation).some(k=>!['id','label','a','b','reset','unit','declaredFamilyId','key','direction','interrupts'].includes(k)))return fail('An operation contains parameters the runner cannot represent.');
  if(operation.id!=='interrupted_repeating_key'&&Object.hasOwn(operation,'interrupts'))return fail('Only an interrupted repeating key accepts literal interrupter indices.');
  if(operation.id!=='finite_key'&&operation.id!=='interrupted_repeating_key'&&!Object.hasOwn(keyedModes,operation.id)&&['key','direction'].some(k=>Object.hasOwn(operation,k)))return fail('This operation does not accept key parameters.');
  if(operation.id!=='reverse_runes'&&Object.hasOwn(operation,'unit'))return fail('This operation does not accept a reversal unit.');
  if(operation.id==='reverse_row_runes'){
   if(Object.keys(operation).some(k=>['a','b','reset'].includes(k)))return fail('The reversal has unsupported parameters.');
   reverse=true;
   if(specified('boundaryMode')&&!['fixed_spaces','within_words'].includes(rules.boundaryMode.value))return fail('This word-order rule needs a different reversal adapter.');
   if(specified('wordBoundaries')&&!specified('boundaryMode'))return fail('Choose how the reversal handles the preserved word boundaries.');
   steps.push({op:'reverse',unit:specified('boundaryMode')&&rules.boundaryMode.value==='within_words'?'word':'line'});
  }else if(operation.id==='reverse_runes'){
   if(!['line','word','page'].includes(operation.unit)||['a','b','reset'].some(k=>Object.hasOwn(operation,k)))return fail('A reversal needs an explicit line, word or page boundary.');
   if(operation.label!==undefined&&operation.label!=='Reverse rune order within each '+operation.unit)return fail('The reversal label conflicts with its boundary.');
   if(specified('boundaryMode')&&rules.boundaryMode.value!==(operation.unit==='word'?'within_words':'fixed_spaces'))return fail('The global boundary rule conflicts with a reversal step.');
   if(operation.unit==='page'&&specified('boundaryMode'))return fail('The global row boundary rule conflicts with a whole-page reversal.');
   reverse=true;steps.push({op:'reverse',unit:operation.unit});
  }else if(operation.id==='affine'){
   if(Object.hasOwn(operation,'reset')||!Number.isInteger(operation.a)||operation.a<0||operation.a>28||!Number.isInteger(operation.b)||operation.b<0||operation.b>28)return fail('An affine step needs explicit a and b indices from 0 to 28.');
   steps.push({op:'affine',a:operation.a,b:operation.b});
  }else if(operation.id==='cumulative_difference'){
   if(Object.hasOwn(operation,'a')||Object.hasOwn(operation,'b')||!['page','line','word'].includes(operation.reset))return fail('Cumulative difference needs an explicit page, line or word reset.');
   if(rules.reset.status==='not_applicable')return fail('An explicit reset conflicts with reset being marked not applicable.');
   if(specified('reset')&&resetValue(rules.reset.value)!==operation.reset)return fail('The global reset conflicts with an operation reset.');
   if(rules.initialState.status==='not_applicable')return fail('Cumulative difference requires an initial state, which is marked not applicable.');
   if(specified('initialState')&&rules.initialState.value!==0)return fail('Only initial state zero is supported.');
   cumulative=true;steps.push({op:'cumulative-difference',reset:operation.reset});
  }else if(operation.id==='interrupted_repeating_key'){
   if(operation.label!=='Interrupted repeating key')return fail('An interrupted repeating key needs its exact canonical label.');
   if(['a','b','unit'].some(k=>Object.hasOwn(operation,k))||!Array.isArray(operation.key)||!operation.key.length||operation.key.length>256||operation.key.some(n=>!Number.isInteger(n)||n<0||n>28)||!['subtract','add'].includes(operation.direction)||!['page','line','word'].includes(operation.reset)||!Array.isArray(operation.interrupts)||!operation.interrupts.length||operation.interrupts.length>29||operation.interrupts.some((n,i)=>!Number.isInteger(n)||n<0||n>28||i>0&&n<=operation.interrupts[i-1]))return fail('An interrupted repeating key needs explicit GP key indices (0–28), add or subtract, a page, line or word reset, and sorted unique literal interrupter indices (0–28).');
   if(rules.reset.status==='not_applicable')return fail('An explicit reset conflicts with reset being marked not applicable.');
   if(specified('reset')&&resetValue(rules.reset.value)!==operation.reset)return fail('The global reset conflicts with an operation reset.');
   keyed=true;steps.push({op:'interrupted-keyed-shift',key:[...operation.key],direction:operation.direction,reset:operation.reset,interrupts:[...operation.interrupts]});
  }else if(operation.id==='finite_key'||Object.hasOwn(keyedModes,operation.id)){
   if(['a','b','unit'].some(k=>Object.hasOwn(operation,k))||!Array.isArray(operation.key)||!operation.key.length||operation.key.length>(operation.id==='finite_key'?20000:256)||operation.key.some(n=>!Number.isInteger(n)||n<0||n>28)||!['subtract','add'].includes(operation.direction)||!['page','line','word'].includes(operation.reset))return missingRepeatingKeyChoice(card,operation,operationIndex)||fail(KEYED_REASON);
   if(rules.reset.status==='not_applicable')return fail('An explicit reset conflicts with reset being marked not applicable.');
   if(specified('reset')&&resetValue(rules.reset.value)!==operation.reset)return fail('The global reset conflicts with an operation reset.');
   keyed=true;steps.push(operation.id==='finite_key'?{op:'finite-shift',key:[...operation.key],direction:operation.direction,reset:operation.reset}:{op:'keyed-shift',key:[...operation.key],mode:keyedModes[operation.id],direction:operation.direction,reset:operation.reset});
  }else return fail('This method needs an execution adapter before a faithful local plan can be prepared.');
 }
 if(specified('boundaryMode')&&!reverse)return fail('The boundary-mode condition is not represented by these steps.');
 if(specified('initialState')&&!cumulative)return fail('The initial-state condition is not represented by these steps.');
 if(specified('reset')&&!cumulative&&!keyed)return fail('The reset or initial-state condition is not represented by these steps.');
 if(steps.some(s=>s.op==='reverse'))notes.push('Reversal changes rune positions only, leaving separators in place; a word ends at any non-rune character.');
 if(keyed)notes.push('Key values are explicit GP alphabet indices, not prime values or guessed letters; non-rune characters do not consume the key. Each specified boundary restarts the key and autokey history.');
 if(steps.some(s=>s.op==='interrupted-keyed-shift'))notes.push('Literal interrupter indices are tested against the current step input, copied unchanged, and do not advance the repeating key. Other runes consume one key value. Each declared reset starts at the first key value; there is no autokey feedback.');
 if(steps.some(s=>s.op==='finite-shift'))notes.push('Finite key streams never wrap or extend themselves. The supplied key must cover every complete segment before the task can be prepared.');
 if(cumulative)notes.push('Cumulative difference starts at zero at each specified boundary; pages never share state.');
 notes.push('Each page is processed separately, in the stated method-step order; headings are included.');
 if(card.outcome.status==='specified'&&card.outcome.value.outcomeId==='decipher')notes.push('This is a preliminary measurement for the deciphering idea, not a test of whether the output is readable.');
 return {pages:card.scope.value.pages,steps,inputVersion,criterion,notes};
}
 const api={compile};if(node)module.exports=api;else root.FixedPlanCompiler=api;
})(typeof globalThis!=='undefined'?globalThis:this);
