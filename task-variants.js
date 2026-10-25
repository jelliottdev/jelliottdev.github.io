/* Closed next-step variants. No inference, source fetching or target execution. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const P=typeof module==='object'&&module.exports?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const Q=typeof module==='object'&&module.exports?require('./question-evidence.js'):root.QuestionEvidence;
 function inspect(task){
  try{E.validateTask(task);}catch{return null;}
  if(task.steps.length)return null;
  const variant=P.describe(task.criterion)?.followups.find(v=>v.id==='word-boundaries');
  return variant?{kind:variant.id,from:variant.from,to:variant.to,label:variant.label,description:variant.description}:null;
 }
 async function prepare(parent,cryptoAPI=root.crypto){
  await E.checkIdentity(parent,cryptoAPI);
  const variant=inspect(parent);if(!variant)throw Error('This task has no supported word-boundary comparison.');
  const criterion=P.variant(parent.criterion,variant.kind),title=P.describe(criterion).title;
  return E.prepare({title,
   pages:JSON.parse(E.stable(parent.pages)),alphabet:JSON.parse(E.stable(parent.alphabet)),steps:[],
   criterion},cryptoAPI);
 }
 async function validate(parent,child,cryptoAPI=root.crypto){
  await E.checkIdentity(child,cryptoAPI);
  const expected=await prepare(parent,cryptoAPI);
  if(E.stable(expected)!==E.stable(child))throw Error('The comparison changed more than the fixed word-boundary rule.');
  return child;
 }
 // A descriptive decision over two independently verified, identical-input runs.
 // The null changes with grouping: never subtract its two means or imply a tail test.
 function decision(parent,before,child,after){
  const variant=inspect(parent);
  if(!variant||parent.criterion.kind!=='word-affine-count')return null;
  E.summary(parent,before);E.summary(child,after);
  if(E.stable(parent.pages)!==E.stable(child.pages)||E.stable(parent.alphabet)!==E.stable(child.alphabet)||child.steps.length||E.stable(P.variant(parent.criterion,variant.kind))!==E.stable(child.criterion))throw Error('The boundary decision needs the same text and rule.');
  const separate=parent.criterion.boundaries==='non-rune'?before.wordPairs:after.wordPairs;
  const joined=parent.criterion.boundaries==='hyphen-period'?before.wordPairs:after.wordPairs;
  return interpret(separate,joined);
 }
 function aggregateDecision(a,b){const {separate,joined}=Q.paired(a,b);return interpret(separate.wordPairs,joined.wordPairs);}
 function interpret(separate,joined){
  const above=sample=>BigInt(sample.matches)*BigInt(sample.expected.denominator)>BigInt(sample.expected.numerator);
  const shared={question:'Does the above-average count require joining across layout marks?',limit:'Each grouping uses its own rearrangement average. This is not a significance test or independent confirmation, and it does not establish which breaks are correct.'};
  if(!separate.opportunities||!joined.opportunities)return {...shared,id:'insufficient-pairs',heading:'Too few pairs to compare both groupings',finding:'One grouping has no pairs at the selected distance. This comparison cannot establish whether an above-average count persists.'};
  const strictAbove=above(separate),joinedAbove=above(joined);
  if(strictAbove&&joinedAbove)return {...shared,id:'excess-in-both',heading:'The above-average count remains without joining',finding:'Both groupings have more matches than their own random-order average. Joining across spaces, slashes and line breaks is not required for this descriptive excess.'};
  if(strictAbove)return {...shared,id:'excess-separate-only',heading:'Only the more finely split groups are above average',finding:'Separating at every non-rune gives an above-average count; joining until a hyphen or period does not. The comparison depends on how the groups are defined.'};
  if(joinedAbove)return {...shared,id:'excess-joined-only',heading:'Only the joined groups are above average',finding:'The above-average count appears when groups continue until a hyphen or period. It does not remain when every non-rune ends a group.'};
  return {...shared,id:'neither-above',heading:'Neither grouping is above its random-order average',finding:'Neither count exceeds the average for rearrangements within its own groups. This does not rule out the proposed rule or establish that the text is random.'};
 }
 const api={inspect,prepare,validate,decision,aggregateDecision};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.TaskVariants=api;
})(typeof globalThis!=='undefined'?globalThis:this);
