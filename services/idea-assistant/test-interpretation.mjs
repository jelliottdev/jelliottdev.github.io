/* Proposed candidates are mocked untrusted JSON. No model/network calls. */
import assert from 'node:assert/strict';
import C from '../../claim-specification.js';
import {SCHEMA,JSON_SCHEMA,PROMPT,validateInput,validateCandidate,toDraft,pagesFromSource,keyDeclarations} from './interpretation.mjs';
const copy=x=>JSON.parse(JSON.stringify(x));
const at=(raw,quote,start=raw.indexOf(quote))=>({start,quote});
const step=(raw,quote=raw,id='described_method',familyId=null)=>({id,familyId,source:at(raw,quote),parameters:{}});
const candidate=(raw,steps=[step(raw)])=>({schema:SCHEMA,outcome:null,steps,scope:null,rules:{}});
let groups=0;function test(name,fn){fn();groups++;console.log('PASS '+name);}
test('exported bounded schema and prompt do not call or confirm anything',()=>{
 assert.equal(JSON_SCHEMA.additionalProperties,false);assert(PROMPT.includes('must review and confirm'));assert(PROMPT.includes('negation'));assert.throws(()=>validateInput(''));assert.throws(()=>validateInput('x'.repeat(1501)));assert.equal(validateInput(' x '),' x ');
 const raw='Use the supplied rule.',result=toDraft(raw,candidate(raw));assert.equal(result.draft.source.text,raw);assert.equal(result.draft.status,'draft');assert.equal(result.draft.confirmation,null);assert.equal(result.draft.execution,'not_run');assert.equal(result.requiresConfirmation,true);assert.equal(result.meaningVerified,false);
});
test('row paraphrases activate the same consequential existing boundary question',()=>{
 for(const raw of ['Reverse each row on LP2-15, preserving word boundaries.','Try reversing rune order within each row on LP2-15, preserving word boundaries.','Reverse rune order within rows on LP2-15, preserving word boundaries.','Reverse the runes in every row on LP2-15, preserving word boundaries.']){
  const p=candidate(raw,[step(raw,raw,'reverse_row_runes','transposition')]);p.rules.wordBoundaries={status:'specified',value:'preserve',source:at(raw,'preserving word boundaries')};p.scope={pages:['lp2-15'],passage:null,source:at(raw,'LP2-15')};
  const result=toDraft(raw,p);assert.equal(result.draft.method.value.operations[0].id,'reverse_row_runes');assert.equal(result.draft.rules.wordBoundaries.value,'preserve');assert.deepEqual(result.questions.map(q=>q.id),['word-boundary']);assert.equal(C.completeness(result.draft).researchReady,false);assert.equal(result.draft.source.text,raw);
 }
});

test('literal key evidence may cite declaration, quoted token or exact value but must belong to its full parent step',()=>{
 const raw='Use Vigenere with key "A B" on LP2-43.';
 for(const quote of ['key "A B"','"A B"','A B',raw]){
  const p=candidate(raw);p.steps[0].parameters.key={value:'A B',source:at(raw,quote)};
  assert.equal(toDraft(raw,p).draft.method.value.operations[0].key,'A B');
 }
 const bare='Use cipher with key ABC.';for(const quote of ['key ABC','ABC']){const p=candidate(bare);p.steps[0].parameters.key={value:'ABC',source:at(bare,quote)};assert.equal(validateCandidate(bare,p).steps[0].parameters.key.value,'ABC');}
 const missing=candidate(raw,[step(raw,'Use Vigenere')]);missing.steps[0].parameters.key={value:'A B',source:at(raw,'"A B"')};assert.throws(()=>validateCandidate(raw,missing),/key/);
 const invented=candidate(raw);invented.steps[0].parameters.key={value:'different',source:at(raw,'"A B"')};assert.throws(()=>validateCandidate(raw,invented),/key/);
});

test('explicit key declarations distinguish grammar from literal values and quoted condition words',()=>{
 for(const raw of ['Reset the key at each word.','Carry the key by row.','Use a key stream.','Set key length=3.'])assert.deepEqual(keyDeclarations(raw),[],raw);
 for(const [raw,value]of [['Use key ABC.','ABC'],['Use key=at.','at'],['Use key: "from".','from']]){
  const keys=keyDeclarations(raw);assert.equal(keys.length,1);assert.equal(keys[0].value,value);assert.equal(raw.slice(keys[0].source.start,keys[0].source.start+keys[0].source.quote.length),keys[0].source.quote);
 }
 const reset='Reset the key at each word.',falseKey=candidate(reset);falseKey.steps[0].parameters.key={value:'at',source:at(reset,'at')};assert.throws(()=>validateCandidate(reset,falseKey),/key/);
 const raw='Find readable text. Reverse each row then use Vigenere with key "IF; NOT." on LP2-43.',first='Reverse each row',tail='use Vigenere with key "IF; NOT." on LP2-43.';
 const p=candidate(raw,[step(raw,first,'reverse_row_runes'),step(raw,tail)]);p.outcome={id:'decipher',source:at(raw,'Find readable text.')};p.steps[1].parameters.key={value:'IF; NOT.',source:at(raw,'"IF; NOT."')};p.scope={pages:['lp2-43'],passage:null,source:at(raw,'LP2-43')};
 const result=toDraft(raw,p);assert.equal(result.draft.method.value.operations[0].id,'reverse_row_runes');assert.equal(result.draft.method.value.operations[1].key,'IF; NOT.');assert.deepEqual(result.draft.scope.value.pages,['lp2-43']);assert.equal(result.draft.source.text,raw);
 for(const input of ['',null,'x'.repeat(1501)])assert.throws(()=>keyDeclarations(input));
});

test('complete sentence boundaries and explicit limited reading criteria preserve their actual meaning',()=>{
 const raw='Use Vigenere with key ABC. Reset the key at each word unless the word continues across a line.',first='Use Vigenere with key ABC.',tail='Reset the key at each word unless the word continues across a line.';
 const p=candidate(raw,[step(raw,first),step(raw,tail)]);p.steps[0].parameters.key={value:'ABC',source:at(raw,'ABC')};p.rules.reset={status:'specified',value:tail,source:at(raw,tail)};assert.equal(toDraft(raw,p).draft.rules.reset.value,tail);
 const goal='Recover only the first twelve runes.',q=candidate(goal,[]);q.outcome={id:'decipher',source:at(goal,goal)};assert.equal(toDraft(goal,q).draft.aim.outcome.id,'decipher');assert.equal(toDraft(goal,q).draft.aim.outcome.detail,goal);
 for(const goal of ['Recover text only if the key is supplied.','Do not recover only the opening.']){const q=candidate(goal,[]);q.outcome={id:'decipher',source:at(goal,goal)};assert.throws(()=>validateCandidate(goal,q),/conditional outcome/);}
 const negative='Reverse each row only if the key is supplied.',r=candidate(negative,[step(negative,'Reverse each row','reverse_row_runes')]);assert.throws(()=>validateCandidate(negative,r),/conditional/);
});

test('literal keys cannot manufacture outcome, page scope, rule values or unrestricted state',()=>{
 for(const [literal,field]of [['decipher','outcome'],['LP2-15','scope'],['preserve word boundaries','rules']]){
  const raw='Use cipher with key "'+literal+'".',p=candidate(raw);
  if(field==='outcome')p.outcome={id:'decipher',source:at(raw,literal)};
  if(field==='scope')p.scope={pages:['lp2-15'],passage:null,source:at(raw,literal)};
  if(field==='rules')p.rules.wordBoundaries={status:'specified',value:'preserve',source:at(raw,literal)};
  assert.throws(()=>validateCandidate(raw,p),/literal key/);
 }
 const raw='Use cipher with key "LP2-15" on LP2-43.',p=candidate(raw);p.scope={pages:['lp2-15','lp2-43'],passage:null,source:at(raw,raw)};assert.throws(()=>validateCandidate(raw,p),/partial page/);p.scope.pages=['lp2-43'];assert.deepEqual(validateCandidate(raw,p).scope.pages,['lp2-43']);assert.deepEqual(pagesFromSource(raw),['lp2-43']);
 for(const [literal,key,status,value]of [['preserve word boundaries','wordBoundaries','specified','preserve'],['unrestricted','searchBounds','unrestricted'],['reset at each word','reset','specified','reset at each word']]){
  const text='Use cipher with key "'+literal+'".',q=candidate(text);q.rules[key]={status,...(value?{value}:{}),source:at(text,text)};assert.throws(()=>validateCandidate(text,q));
 }
});

test('to/through ranges expand exactly and are covered; alternatives and mixed-release ranges stay opaque',()=>{
 for(const join of ['to','through','–']){
  const raw='Use cipher on LP2-15 '+join+' LP2-17.',range='LP2-15 '+join+' LP2-17',p=candidate(raw,[step(raw,'Use cipher')]);p.scope={pages:['lp2-15','lp2-16','lp2-17'],passage:null,source:at(raw,range)};
  const result=toDraft(raw,p);assert.deepEqual(result.draft.scope.value.pages,['lp2-15','lp2-16','lp2-17']);assert.deepEqual(result.uninterpreted,[]);assert.equal(result.draft.source.text,raw);
 }
 assert.deepEqual(pagesFromSource('LP2-15 through LP2-17, LP2-19'),['lp2-15','lp2-16','lp2-17','lp2-19']);
 for(const raw of ['LP2-15 or LP2-17','LP2-15 and/or LP2-17','LP1-15 to LP2-03','LP2-15, 17'])assert.throws(()=>pagesFromSource(raw));
 assert.deepEqual(pagesFromSource('LP1-15, LP2-03'),['lp1-15','lp2-03']);
 for(const input of ['',null,'x'.repeat(1501)])assert.throws(()=>pagesFromSource(input));
});

test('normalization covers only its matched wording; by is grammar and other source conditions stay visible',()=>{
 const raw='Decipher LP2-15 by reversing rune order within each row, preserving word boundaries.',p=candidate(raw,[step(raw,'reversing rune order within each row','reverse_row_runes')]);p.outcome={id:'decipher',source:at(raw,'Decipher')};p.scope={pages:['lp2-15'],passage:null,source:at(raw,'LP2-15')};p.rules.wordBoundaries={status:'specified',value:'preserve',source:at(raw,raw)};
 const result=toDraft(raw,p);assert.deepEqual(result.uninterpreted,[]);assert.equal(result.draft.rules.exceptionalCases.status,'unspecified');assert.equal(result.draft.source.text,raw);
 const broad='Reverse each row, preserving word boundaries; preserve punctuation.',q=candidate(broad,[step(broad,'Reverse each row','reverse_row_runes')]);q.rules.wordBoundaries={status:'specified',value:'preserve',source:at(broad,broad)};
 const kept=toDraft(broad,q);assert(kept.draft.rules.exceptionalCases.value.includes('preserve punctuation'));assert(!kept.draft.rules.exceptionalCases.value.includes('preserving word boundaries'));assert.equal(kept.draft.source.text,broad);
});
test('digit versus value reversal stays distinct, with ambiguity reused from C.questions',()=>{
 for(const raw of ['Reverse decimal digits of each prime value.','Try reversing the digits of each value.']){
  const result=toDraft(raw,candidate(raw,[step(raw,raw,'reverse_value_digits')]));assert.equal(result.draft.method.value.operations[0].id,'reverse_value_digits');assert.equal(result.draft.rules.unmapped.status,'unspecified');assert.equal(result.draft.rules.representation.status,'unspecified');
 }
 const raw='Reverse prime values in each row.',result=toDraft(raw,candidate(raw,[step(raw,raw,'ambiguous_reversal')]));assert.deepEqual(result.questions.map(q=>q.id),['operation']);assert.equal(result.draft.unresolved[0].kind,'operation_ambiguity');
 assert.throws(()=>validateCandidate(raw,candidate(raw,[step(raw,raw,'reverse_value_digits')])),/unsupported known-operation/);
});
test('compound order and opaque tails survive, reordered/overlapping quote claims fail',()=>{
 const raw='Reverse each row then apply the supplied cipher with key "A B".',first='Reverse each row',tail='apply the supplied cipher with key "A B".';
 const p=candidate(raw,[step(raw,first,'reverse_row_runes'),step(raw,tail)]);p.steps[1].parameters.key={value:'A B',source:at(raw,'key "A B"')};
 const before=JSON.stringify(p),result=toDraft(raw,p),ops=result.draft.method.value.operations;
 assert.deepEqual(ops.map(o=>o.sourceText),[first,tail]);assert.equal(ops[1].key,'A B');assert(ops[1].provenance.refs.some(ref=>JSON.parse(ref).quote==='key "A B"'));assert(!Object.hasOwn(ops[1],'keyProvenance'));assert.equal(result.draft.rules.exceptionalCases.status,'unspecified');assert.equal(JSON.stringify(p),before);
 const reordered=copy(p);reordered.steps.reverse();assert.throws(()=>validateCandidate(raw,reordered),/source order/);
 const overlap=copy(p);overlap.steps[0]=step(raw,raw);assert.throws(()=>validateCandidate(raw,overlap),/overlap/);
 const allKnown=copy(p);allKnown.steps=[step(raw,raw,'reverse_row_runes')];assert.throws(()=>validateCandidate(raw,allKnown),/unsupported known-operation/);
});
test('only isolated finite grammar spans are omitted; meaningful residuals and original source stay exact',()=>{
 const raw='Try reverse each row then use Vigenere on LP2-15.',first='reverse each row',second='use Vigenere';
 const p=candidate(raw,[step(raw,first,'reverse_row_runes'),step(raw,second)]);p.scope={pages:['lp2-15'],passage:null,source:at(raw,'LP2-15')};
 const result=toDraft(raw,p);assert.deepEqual(result.uninterpreted,[]);assert.equal(result.draft.rules.exceptionalCases.status,'unspecified');assert.equal(result.draft.source.text,raw);assert.deepEqual(result.draft.method.value.operations.map(o=>o.sourceText),[first,second]);
 for(const connector of ['please','try','and','then','on','PLEASE try and then on','  (then)  ']){
  const text='Use cipher; '+connector,r=toDraft(text,candidate(text,[step(text,'Use cipher')]));assert.deepEqual(r.uninterpreted,[],connector);assert.equal(r.draft.source.text,text);
 }
 for(const meaningful of ['not','if','after','only','but','unless','except','before','then apply an omitted transform','try again','on condition','please 2','only then','then, try']){
  const text='Use cipher; '+meaningful,r=toDraft(text,candidate(text,[step(text,'Use cipher')]));assert(r.uninterpreted.some(s=>s.quote.includes(meaningful)),meaningful);assert(r.draft.rules.exceptionalCases.value.includes(meaningful));assert.equal(r.draft.source.text,text);
 }
});

test('negation and conditional context cannot be discarded into a positive operation',()=>{
 for(const raw of ['Do not reverse each row.','Reverse each row only if the key is supplied.','Unless it changes word order, reverse each row.','Never reverse each row; use another method.']){
  const quote=raw.match(/reverse each row/i)[0];assert.throws(()=>validateCandidate(raw,candidate(raw,[step(raw,quote,'reverse_row_runes')])),/negated\/conditional/);
  assert.throws(()=>validateCandidate(raw,candidate(raw,[step(raw,quote)])),/drops its negation/);
  const whole=toDraft(raw,candidate(raw));assert.equal(whole.draft.method.value.operations[0].label,raw);assert.equal(whole.draft.method.value.operations[0].id,'described_method');
 }
 const raw='Do not preserve word boundaries.',p=candidate(raw,[]);p.rules.wordBoundaries={status:'specified',value:'preserve',source:at(raw,'preserve word boundaries')};assert.throws(()=>validateCandidate(raw,p),/drops its negation/);
 const goal='I am not trying to solve LP2.',a=candidate(goal);a.outcome={id:'decipher',source:at(goal,'solve LP2')};assert.throws(()=>validateCandidate(goal,a),/negated\/conditional outcome/);a.outcome={id:'unclassified',source:at(goal,goal)};assert.equal(toDraft(goal,a).draft.aim.value.outcomeId,'unclassified');
 const scope='not LP2-15',b=candidate(scope);b.scope={pages:['lp2-15'],passage:null,source:at(scope,'LP2-15')};assert.throws(()=>validateCandidate(scope,b),/conditional\/excluded/);b.scope={pages:null,passage:'LP2-15',source:at(scope,'LP2-15')};assert.throws(()=>validateCandidate(scope,b),/negation\/condition/);b.scope={pages:null,passage:scope,source:at(scope,scope)};assert.equal(toDraft(scope,b).draft.scope.value.description,scope);
 const reset='Unless the word continues, reset the key at each word.',c=candidate(reset);c.rules.reset={status:'specified',value:'reset the key at each word',source:at(reset,'reset the key at each word')};assert.throws(()=>validateCandidate(reset,c),/drops its negation/);c.rules.reset={status:'specified',value:reset,source:at(reset,reset)};assert.equal(toDraft(reset,c).draft.rules.reset.value,reset);
 const state='Search bounds are not unrestricted.',d=candidate(state);d.rules.searchBounds={status:'unrestricted',source:at(state,'unrestricted')};assert.throws(()=>validateCandidate(state,d),/negated rule state/);
});
test('uninterpreted source remains visible even when broad rule/scope quotes cover it',()=>{
 const raw='On LP2-15 use key ABC; do not remove punctuation.',p=candidate(raw,[]);p.scope={pages:['lp2-15'],passage:null,source:at(raw,'LP2-15')};p.rules.initialState={status:'specified',value:'key ABC',source:at(raw,'key ABC')};
 const result=toDraft(raw,p);assert(result.draft.rules.exceptionalCases.value.includes('do not remove punctuation'));assert(result.uninterpreted.some(s=>s.quote.includes('do not remove punctuation')));assert.equal(result.draft.method.status,'unspecified');
 const compound='Reverse each row then use a custom undefined transform.',q=candidate(compound,[step(compound,'Reverse each row','reverse_row_runes')]);const second=toDraft(compound,q);assert(second.draft.rules.exceptionalCases.value.includes('custom undefined transform'));assert.equal(second.draft.source.text,compound);
 const broad='On LP2-15 use key ABC; preserve punctuation.',r=candidate(broad,[]);r.rules.initialState={status:'specified',value:'key ABC',source:at(broad,broad)};r.scope={pages:['lp2-15'],passage:null,source:at(broad,broad)};assert(toDraft(broad,r).draft.rules.exceptionalCases.value.includes('preserve punctuation'));
});
test('missing settings remain unknown; explicit literal rule values retain source provenance',()=>{
 const raw='Use Vigenere with key ABC on LP2-15; reset the key at each word.',p=candidate(raw,[step(raw,'Use Vigenere with key ABC on LP2-15','described_method','polyalphabetic')]);p.steps[0].parameters.key={value:'ABC',source:at(raw,'key ABC')};p.rules.reset={status:'specified',value:'reset the key at each word',source:at(raw,'reset the key at each word')};p.scope={pages:['lp2-15'],passage:null,source:at(raw,'LP2-15')};
 const result=toDraft(raw,p);assert.equal(result.draft.rules.reset.value,'reset the key at each word');assert.equal(result.draft.rules.reset.provenance.kind,'proposed');assert.equal(result.draft.rules.inputVersion.status,'unspecified');assert.equal(result.draft.rules.evaluation.status,'unspecified');assert.equal(result.draft.aim.status,'unspecified');
 const absent=toDraft('Use Vigenere.',candidate('Use Vigenere.'));assert(!Object.hasOwn(absent.draft.method.value.operations[0],'key'));assert.equal(absent.draft.rules.reset.status,'unspecified');
});
test('exact page holes/ranges and passage qualifiers never become fabricated whole pages',()=>{
 const raw='Apply to LP2-15, LP2-17–18, lines 2–3.',p=candidate(raw);p.scope={pages:['lp2-15','lp2-17','lp2-18'],passage:'lines 2–3',source:at(raw,raw)};assert.deepEqual(toDraft(raw,p).draft.scope.value,{pages:['lp2-15','lp2-17','lp2-18'],description:'lines 2–3'});
 const missing=copy(p);missing.scope.passage=null;assert.throws(()=>validateCandidate(raw,missing),/passage qualifier/);
 const invented=copy(p);invented.scope.pages.push('lp2-16');assert.throws(()=>validateCandidate(raw,invented),/invented\/partial/);
 const partial=copy(p);partial.scope.pages=['lp2-15'];assert.throws(()=>validateCandidate(raw,partial),/invented\/partial/);
 const excluded='LP2-15–18 except LP2-16',q=candidate(excluded);q.scope={pages:['lp2-15','lp2-16','lp2-17','lp2-18'],passage:null,source:at(excluded,excluded)};assert.throws(()=>validateCandidate(excluded,q),/conditional\/excluded/);q.scope={pages:null,passage:excluded,source:at(excluded,excluded)};assert.equal(toDraft(excluded,q).draft.scope.value.description,excluded);
 for(const phrase of ['apart from','other than','minus']){
  const raw='LP2-00–55 '+phrase+' LP2-50',p=candidate(raw);p.scope={pages:Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0')),passage:raw,source:at(raw,raw)};
  assert.throws(()=>validateCandidate(raw,p),/conditional\/excluded/,'Excluded page must not enter a derived page set');
  p.scope.pages=null;const preserved=toDraft(raw,p);assert.equal(preserved.draft.scope.value.description,raw);assert(!preserved.draft.scope.value.pages?.includes('lp2-50'));assert.equal(preserved.draft.source.text,raw);
 }
});
test('invented quotes, categories, parameters, values, states and derived claims rejected',()=>{
 const raw='Use cipher with key "ABC".',valid=candidate(raw);valid.steps[0].parameters.key={value:'ABC',source:at(raw,'key "ABC"')};
 const mutations=[p=>p.steps[0].source.quote='not in input',p=>p.steps[0].source.start=1,p=>p.steps[0].familyId='new-family',p=>p.steps[0].id='execute_code',p=>p.steps[0].parameters.modulus=29,p=>p.steps[0].parameters.key.value='AB',p=>p.steps[0].parameters.key.value='XYZ',p=>p.tags=['invented'],p=>p.outcome={id:'invented-goal',source:at(raw,raw)},p=>p.rules.reset={status:'specified',value:'page',source:at(raw,raw)},p=>p.rules.reset={status:'unrestricted',source:at(raw,raw)},p=>p.rules.reset={status:'not_applicable',source:at(raw,raw)},p=>p.confirmed=true];
 for(const mutate of mutations){const p=copy(valid);mutate(p);assert.throws(()=>validateCandidate(raw,p));}
 let invoked=false;const accessor={};Object.defineProperty(accessor,'schema',{enumerable:true,get(){invoked=true;return SCHEMA;}});assert.throws(()=>validateCandidate(raw,accessor));assert.equal(invoked,false);
 const accessorArray=copy(valid);Object.defineProperty(accessorArray.steps,'0',{get(){invoked=true;return valid.steps[0];}});assert.throws(()=>validateCandidate(raw,accessorArray));assert.equal(invoked,false);
 assert.throws(()=>validateCandidate(raw,'x'.repeat(24001)),/candidate size/);
});
test('repeated quotes require explicit occurrence offsets and cannot reassign key evidence',()=>{
 const raw='Use key ABC then use key ABC.',p=candidate(raw,[step(raw,'Use key ABC'),{...step(raw,'use key ABC.'),source:at(raw,'use key ABC.',17)}]);
 // The lower-case second step starts at the actual source offset, not the
 // first matching key token. Each key's occurrence belongs to its own step.
 p.steps[1].source.start=raw.indexOf('use key');p.steps[1].parameters.key={value:'ABC',source:at(raw,'key ABC',raw.lastIndexOf('key ABC'))};assert.equal(validateCandidate(raw,p).steps.length,2);
 p.steps[1].parameters.key.source.start=raw.indexOf('key ABC');assert.throws(()=>validateCandidate(raw,p),/invented\/unsupported key/);
 const repeated='Reverse each row. Reverse each row.',q=candidate(repeated,[step(repeated,'Reverse each row.','reverse_row_runes'),{...step(repeated,'Reverse each row.','reverse_row_runes'),source:at(repeated,'Reverse each row.',18)}]);assert.equal(validateCandidate(repeated,q).steps[1].source.start,18);
 q.steps[1].source.start=0;assert.throws(()=>validateCandidate(repeated,q),/overlap/);
});
console.log('PASS '+groups+' proposed interpretation groups; no model/network/execution/confirmation');
