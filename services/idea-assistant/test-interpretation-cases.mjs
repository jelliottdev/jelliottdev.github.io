/* Canonical target fixtures, not generated model prose or live evaluations. */
import assert from 'node:assert/strict';
import C from '../../claim-specification.js';
import Investigate from '../../investigate.js';
import {toDraft} from './interpretation.mjs';
import {CORPUS_VERSION,INTERPRETATION_CASES} from './interpretation-cases.mjs';

assert(INTERPRETATION_CASES.length>=12);assert.equal(new Set(INTERPRETATION_CASES.map(c=>c.id)).size,INTERPRETATION_CASES.length);
const outputs=new Map(),failures=[];
for(const item of INTERPRETATION_CASES){
 try{
  assert.equal(item.synthetic,true);const before=JSON.stringify(item),result=toDraft(item.text,item.candidate),d=result.draft,e=item.expect;
  assert.equal(d.source.text,item.text);assert.equal(d.status,'draft');assert.equal(d.execution,'not_run');assert.equal(d.confirmation,null);assert.equal(result.requiresConfirmation,true);assert.equal(result.meaningVerified,false);
  assert.deepEqual(d.method.value?.operations.map(o=>o.id)||[],e.operationIds);assert.deepEqual(result.questions.map(q=>q.id),e.questionIds);
  assert.equal(d.aim.status,item.candidate.outcome?'specified':'unspecified');
  assert.equal(d.scope.status,item.candidate.scope?'specified':'unspecified');
  for(const [index,operation]of (d.method.value?.operations||[]).entries()){
   assert.equal(operation.sourceText,item.candidate.steps[index].source.quote);assert.equal(operation.key??null,item.candidate.steps[index].parameters.key?.value??null);
   assert.equal(operation.provenance.kind,'proposed');
  }
  for(const key of C.RULES)if(!Object.hasOwn(item.candidate.rules,key)&&key!=='exceptionalCases')assert.equal(d.rules[key].status,'unspecified','Unstated rule invented: '+key);
  for(const field of [d.aim,d.method,d.scope,...Object.values(d.rules)].filter(f=>f.status!=='unspecified')){
   assert.equal(field.provenance.kind,'proposed');for(const reference of field.provenance.refs){const source=JSON.parse(reference);assert.equal(source.source,'original wording');assert.equal(source.end,source.start+source.quote.length);assert.equal(item.text.slice(source.start,source.end),source.quote);}
  }
  if(e.outcomeId)assert.equal(C.normalizeOutcome(d.aim).id,e.outcomeId);
  if(e.outcomeDetail)assert.equal(C.normalizeOutcome(d.aim).detail,e.outcomeDetail);
  if(e.noRepeatedIntake){const questions=Investigate.intakeQuestions(d);assert(!questions.some(q=>q.id==='aim'),'Explicit goal asked again');assert(!questions.some(q=>q.id==='scope'),'Explicit scope asked again');}
  if(e.outcomeMethodOverlap){const a=item.candidate.outcome.source,b=item.candidate.steps[0].source;assert(Math.max(a.start,b.start)<Math.min(a.start+a.quote.length,b.start+b.quote.length),'Expected goal/method source overlap');}
  if(Object.hasOwn(e,'pages'))assert.deepEqual(d.scope.value?.pages??null,e.pages);
  if(e.passage)assert.equal(d.scope.value.description,e.passage);
  for(const page of e.excludedPages||[])assert(!d.scope.value?.pages?.includes(page),'scope hole lost');
  for(const key of e.unknownRules)assert.equal(d.rules[key].status,'unspecified',key+' was invented');
  for(const [key,value]of Object.entries(e.ruleValues||{}))assert.equal(d.rules[key].value,value);
  for(const [key,state]of Object.entries(e.ruleStates||{}))assert.equal(d.rules[key].status,state);
  if(e.keys)assert.deepEqual(d.method.value.operations.map(o=>o.key??null),e.keys);
  const visible=[...(d.method.value?.operations.map(o=>o.label)||[]),...Object.values(d.rules).map(f=>typeof f.value==='string'?f.value:JSON.stringify(f.value)),d.scope.value?.description,C.normalizeOutcome(d.aim).detail,...d.unresolved.map(u=>u.text||'')].filter(Boolean).join('\n');
  for(const text of e.retainedTexts||[])assert(visible.includes(text),'meaningful text not visible: '+text);
  for(const text of e.uninterpretedIncludes||[])assert(result.uninterpreted.some(s=>s.quote.includes(text)));
  for(const kind of e.unresolvedKinds||[])assert(d.unresolved.some(u=>u.kind===kind));
  for(const s of [...item.candidate.steps.map(o=>o.source),...(item.candidate.scope?[item.candidate.scope.source]:[]),...(item.candidate.outcome?[item.candidate.outcome.source]:[]),...Object.values(item.candidate.rules).map(r=>r.source)])assert.equal(item.text.slice(s.start,s.start+s.quote.length),s.quote);
  assert.equal(JSON.stringify(item),before,'Fixture mutated');outputs.set(item.id,result);console.log('PASS '+item.id);
 }catch(error){failures.push({id:item.id,message:error.message});console.error('FAIL '+item.id+': '+error.message);}
}
// Relational assertions: category sameness does not collapse the intended
// criterion; synonymous row phrasings must expose the same ambiguity.
if(outputs.has('row-boundary-plain')&&outputs.has('row-boundary-conversational'))assert.deepEqual(outputs.get('row-boundary-plain').questions,outputs.get('row-boundary-conversational').questions);
if(outputs.has('aim-decipher-whole')&&outputs.has('aim-decipher-opening')){
 const a=outputs.get('aim-decipher-whole').draft.aim,b=outputs.get('aim-decipher-opening').draft.aim;
 assert.equal(C.normalizeOutcome(a).id,C.normalizeOutcome(b).id);assert.notEqual(C.normalizeOutcome(a).detail,C.normalizeOutcome(b).detail);
}
if(outputs.has('purpose-reproduce-prior-count')&&outputs.has('purpose-decipher-with-same-count')){
 const a=outputs.get('purpose-reproduce-prior-count').draft,b=outputs.get('purpose-decipher-with-same-count').draft;
 assert.equal(C.normalizeOutcome(a.aim).id,'reproduce');assert.equal(C.normalizeOutcome(b.aim).id,'decipher');assert.notEqual(C.normalizeOutcome(a.aim).detail,C.normalizeOutcome(b.aim).detail);
 const active=d=>d.method.value.operations.map(({id,label,key})=>({id,label,...(key?{key}:{})}));assert.deepEqual(active(a),active(b));assert.deepEqual(a.scope.value,b.scope.value);
}
assert.deepEqual(failures,[],'Legitimate source fixtures rejected or changed; report these validator gaps upstream, do not weaken the expected meaning.');
console.log('PASS '+INTERPRETATION_CASES.length+' '+CORPUS_VERSION+' cases; zero model/network calls, no claim of live generation accuracy');
