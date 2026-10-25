'use strict';
const assert=require('node:assert/strict');
const C=require('../claim-specification.js'),W=require('../word-sum-intake.js');
const text='Reverse the gematria prime table (F=109, U=107 ...) and sum the words';
const supplied={kind:'supplied',refs:['original wording']},f=value=>C.field('specified',value,supplied);
function draft(source=text){return C.createDraft({source:{text:source,materials:[{name:'source note'}]},
 aim:f({outcomeId:'measure',detail:'Inspect numerical structure'}),scope:f({pages:['lp2-15'],artifactNote:'keep this'}),
 method:f({operations:[{id:'described_method',label:source,sourceText:source}]})});}
let groups=0;const test=(name,fn)=>{fn();groups++;console.log('PASS '+name);};
test('strict full phrase detection and exact scope suffix',()=>{
 for(const s of [text,'Reverse the GP prime table and sum each word','Reverse the gematria primus table then sum words.'])assert(W.matches(s),s);
 assert(W.inspect(draft(text+' on LP2-15')));
 assert.equal(W.inspect(draft(text+' on LP2-16')),null);
 assert.equal(W.matches(text+' on LP2-99'),false);
});
test('missing aim/scope must be answered first; no mutation',()=>{
 const d=draft(),before=C.serialize(d);assert(W.question(d));assert.equal(C.serialize(d),before);
 for(const name of ['aim','scope']){const n=C.revise(d,{[name]:C.field()});assert.equal(W.question(n),null);assert.throws(()=>W.clarify(n,'hyphen-period'));}
 const n=C.revise(d,{scope:f({pages:['lp2-15'],description:'only the heading'})});assert.equal(W.inspect(n),null);
});
test('explicit choice builds exact primitive and retains source aim scope and constraints',()=>{
 for(const boundary of ['hyphen-period','non-rune']){
  const d=draft();d.rules.searchBounds=f({note:'retain an unsupported bound'});d.unresolved.push({kind:'unparsed_constraint',text:'keep this exact note'});
  const before=C.serialize(d),next=W.clarify(d,boundary);
  assert.equal(C.serialize(d),before);assert.deepEqual(next.source,d.source);assert.deepEqual(next.aim,d.aim);assert.deepEqual(next.scope,d.scope);
  assert.deepEqual(next.unresolved,d.unresolved);assert.deepEqual(next.rules.searchBounds,d.rules.searchBounds);
  assert.deepEqual(next.method.value.operations,[{id:'word_prime_sums',label:'Word prime sums',table:'reversed',boundaries:boundary}]);
  assert.deepEqual(next.rules.evaluation.value,{kind:'word-prime-sums',table:'reversed',boundaries:boundary});
  assert.equal(next.rules.representation.value,'GP29');assert.equal(next.rules.inputVersion.value,'raw');
  assert.equal(next.rules.evaluation.provenance.kind,'user_clarification');assert.equal(next.clarifications.at(-1).choice,boundary);
  assert.equal(W.question(next),null);
 }
 const q=W.question(draft());assert.match(q.context,/raw rune text/);assert.match(q.context,/does not decode/);assert(q.choices.every(c=>c.id==='as-described'||c.example));
});
test('two opaque source spans require complete ordered coverage',()=>{
 const d=draft(),split=text.indexOf(' and ');
 d.method.value.operations=[{id:'described_method',label:text.slice(0,split),sourceText:text.slice(0,split)},
  {id:'described_method',label:text.slice(split+5),sourceText:text.slice(split+5),declaredFamilyId:'prime-indices'}];
 assert(W.inspect(d));assert.equal(W.clarify(d,'hyphen-period').method.value.operations.length,1);
 for(const change of ['extra','swap','other','missing','different']){
  const n=structuredClone(d);
  if(change==='extra')n.method.value.operations[0].key=[1];
  if(change==='swap')n.method.value.operations.reverse();
  if(change==='other')n.method.value.operations[1].id='affine';
  if(change==='missing')n.method.value.operations[1].label='sum';
  if(change==='different')n.method.value.operations[0].sourceText='Reverse the prime values';
  assert.equal(W.inspect(n),null,change);
 }
});
test('negation extra methods code conflicting maps and partial table wording remain opaque',()=>{
 for(const s of ['Do not '+text,'Never '+text,text+' then apply Atbash',text+' if there are five dots',text+' except F',
  text+' without headings',text+'; use key DOG',text+'\nrun it',text+' {code}',
  text.replace('F=109','F=2'),text.replace('U=107','U=3'),text.replace('prime table','prime values'),
  'Reverse prime values and sum the words','Reverse the decimal digits of the GP prime table and sum the words',
  'Use 111 minus each gematria prime value and sum the words',text+' on LP2-15, words 1-3']){
  assert.equal(W.matches(s),false,s);assert.equal(W.inspect(draft(s)),null,s);
 }
});
test('existing rule conflicts are not overwritten and confirmed snapshots stay untouched',()=>{
 for(const [name,value] of Object.entries({representation:'latin',inputVersion:'reviewed',wordBoundaries:'remove',unmapped:'drop',
  boundaryMode:'within_words',reset:'word',initialState:0,evaluation:{kind:'measurement'}})){
  const d=draft();d.rules[name]=f(value);const before=C.serialize(d);assert.equal(W.inspect(d),null,name);
  assert.throws(()=>W.clarify(d,'non-rune'));assert.equal(C.serialize(d),before);
 }
 const d=draft();d.rules.representation=f('GP29');const next=W.clarify(d,'non-rune');assert.deepEqual(next.rules.representation,d.rules.representation);
 const confirmed=C.confirm(d,{id:'test',at:'2026-10-24T00:00:00Z'}),before=C.serialize(confirmed);
 assert.equal(W.inspect(confirmed),null);assert.throws(()=>W.clarify(confirmed,'hyphen-period'));assert.equal(C.serialize(confirmed),before);
});
test('leave described suppresses just this question; forged choices and canonical operations cannot be replaced',()=>{
 const d=draft(),next=W.clarify(d,'as-described');assert.deepEqual(next.method,d.method);assert.deepEqual(next.rules,d.rules);assert.equal(W.question(next),null);
 assert.throws(()=>W.clarify(d,'guess'));assert.throws(()=>W.clarify(next,'non-rune'));
 const split=text.indexOf(' and '),edited=C.revise(next,{method:f({operations:[
  {id:'described_method',label:text.slice(0,split),sourceText:text.slice(0,split)},
  {id:'described_method',label:text.slice(split+5),sourceText:text.slice(split+5)}]})});
 assert(W.question(edited),'an old acknowledgement must not hide an edited method');
 const forged=draft();forged.clarifications.push({question:'word-sum-boundaries',choice:'as-described',revision:1});
 assert(W.question(forged),'unbound historical acknowledgement must not suppress the question');
 const canonical=W.clarify(d,'non-rune');canonical.method.value.operations[0].boundaries='hyphen-period';assert.equal(W.inspect(canonical),null);
});
test('AI-proposed source provenance survives exact full-span clarification',()=>{const P=require('../claim-interpretation.js'),I=require('../investigate.js'),quote={start:0,quote:text},proposal={schema:P.SCHEMA,outcome:null,steps:[{id:'described_method',familyId:'prime-indices',source:quote,parameters:{}}],scope:null,rules:{}},interpreted=P.toDraft(text,proposal);let d=I.answerIntake(interpreted.draft,'aim','measure');d=I.answerIntake(d,'scope','specific','LP2-15');assert(W.inspect(d));const refs=d.method.value.operations[0].provenance.refs,before=C.serialize(d),next=W.clarify(d,'non-rune');assert.equal(C.serialize(d),before);assert(refs.every(ref=>next.method.provenance.refs.includes(ref)));assert.deepEqual(next.source,d.source);assert.deepEqual(next.aim,d.aim);assert.deepEqual(next.scope,d.scope);assert.equal(next.method.value.operations[0].id,'word_prime_sums');const bad=structuredClone(d);bad.method.value.operations[0].provenance.extra='discard me';assert.equal(W.inspect(bad),null);});
test('deciphering requires an explicit numerical-evaluation choice bound to unchanged aim and scope',()=>{let d=draft();d=C.revise(d,{aim:f({outcomeId:'decipher',detail:'Recover readable text'})});const before=C.serialize(d),q=W.question(d);assert.equal(q.id,'word-sum-evaluation');assert.throws(()=>W.clarify(d,'non-rune'));let next=W.clarify(d,'numeric-ledger');assert.equal(C.serialize(d),before);assert.equal(next.rules.evaluation.status,'unspecified');assert.deepEqual(next.aim,d.aim);assert.equal(W.question(next).id,'word-sum-boundaries');const revised=C.revise(next,{scope:f({pages:['lp2-16']})});assert.equal(W.question(revised).id,'word-sum-evaluation','Consent cannot be reused for a changed question');next=W.clarify(next,'hyphen-period');assert.equal(next.rules.evaluation.value.kind,'word-prime-sums');assert.deepEqual(next.aim,d.aim);const retained=W.clarify(d,'as-described');assert.deepEqual(retained.method,d.method);assert.deepEqual(retained.rules,d.rules);assert.equal(W.question(retained),null);const forged=structuredClone(d);forged.clarifications.push({question:'word-sum-evaluation',choice:'numeric-ledger',revision:1});assert.equal(W.question(forged).id,'word-sum-evaluation');});
console.log(groups+' word-sum intake groups passed');
