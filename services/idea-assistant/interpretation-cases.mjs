/* Synthetic evaluation material, never saved user submissions or model output.
 * Candidates express intended supported meaning, not approved experiments.
 * Invariants deliberately do not prescribe generated display prose.
 */
import {SCHEMA} from './interpretation.mjs';
export const CORPUS_VERSION='synthetic-proposed-interpretation-cases-v1';
function evidence(text,quote,start=text.indexOf(quote)){
 if(start<0||text.slice(start,start+quote.length)!==quote)throw Error('Invalid synthetic case evidence');return {start,quote};
}
function make(id,text,{steps=[],outcome=null,scope=null,rules={},expect={}}={}){
 const candidate={schema:SCHEMA,outcome:outcome?{id:outcome.id,source:evidence(text,outcome.quote)}:null,
  steps:steps.map(s=>({id:s.id||'described_method',familyId:s.familyId??null,source:evidence(text,s.quote,s.start),parameters:s.key?{key:{value:s.key.value,source:evidence(text,s.key.quote,s.key.start)}}:{}})),
  scope:scope?{pages:scope.pages??null,passage:scope.passage??null,source:evidence(text,scope.quote)}:null,
  rules:Object.fromEntries(Object.entries(rules).map(([name,r])=>[name,{status:r.status||'specified',...(r.status&&r.status!=='specified'?{}:{value:r.value}),source:evidence(text,r.quote)}]))};
 return {id,synthetic:true,text,candidate,expect:{operationIds:steps.map(s=>s.id==='ambiguous_reversal'?'described_method':s.id||'described_method'),questionIds:[],unknownRules:['reset','inputVersion','evaluation','initialState'],...expect}};
}
export const INTERPRETATION_CASES=[
 make('row-boundary-plain','Reverse each row on LP2-15, preserving word boundaries.',{
  steps:[{id:'reverse_row_runes',familyId:'transposition',quote:'Reverse each row'}],scope:{pages:['lp2-15'],quote:'LP2-15'},rules:{wordBoundaries:{value:'preserve',quote:'preserving word boundaries'}},expect:{questionIds:['word-boundary'],pages:['lp2-15'],ruleValues:{wordBoundaries:'preserve'}}}),
 make('row-boundary-conversational','Try reversing rune order within each row on LP2-15, preserving word boundaries.',{
  steps:[{id:'reverse_row_runes',familyId:'transposition',quote:'reversing rune order within each row'}],scope:{pages:['lp2-15'],quote:'LP2-15'},rules:{wordBoundaries:{value:'preserve',quote:'preserving word boundaries'}},expect:{questionIds:['word-boundary'],pages:['lp2-15'],ruleValues:{wordBoundaries:'preserve'}}}),
 make('row-every-paraphrase','Please reverse every row on LP2-17.',{
  steps:[{id:'reverse_row_runes',familyId:'transposition',quote:'Please reverse every row'}],scope:{pages:['lp2-17'],quote:'LP2-17'},expect:{pages:['lp2-17']}}),
 make('decimal-digits-generic-values','Try reversing the decimal digits of each value.',{
  steps:[{id:'reverse_value_digits',quote:'Try reversing the decimal digits of each value.'}],expect:{unknownRules:['representation','unmapped','reset','inputVersion','evaluation','initialState']}}),
 make('prime-values-ambiguous-unit','Reverse the prime values in each row on LP2-15.',{
  steps:[{id:'ambiguous_reversal',quote:'Reverse the prime values in each row'}],scope:{pages:['lp2-15'],quote:'LP2-15'},expect:{questionIds:['operation'],pages:['lp2-15'],unresolvedKinds:['operation_ambiguity']}}),
 make('ordered-row-then-cipher-quoted-key','Reverse each row then use Vigenere with key "A B!?".',{
  steps:[{id:'reverse_row_runes',quote:'Reverse each row'},{familyId:'polyalphabetic',quote:'use Vigenere with key "A B!?".',key:{value:'A B!?',quote:'key "A B!?"'}}],expect:{keys:[null,'A B!?'],retainedTexts:['use Vigenere with key "A B!?".']}}),
 make('quoted-if-key-literal-evidence','Reverse each row then use Vigenere with key "IF".',{
  steps:[{id:'reverse_row_runes',quote:'Reverse each row'},{familyId:'polyalphabetic',quote:'use Vigenere with key "IF".',key:{value:'IF',quote:'IF'}}],expect:{keys:[null,'IF'],retainedTexts:['use Vigenere with key "IF".']}}),
 make('ordered-cipher-then-row','Shift alphabet indices by 3, then reverse each row.',{
  steps:[{familyId:'fixed-substitution',quote:'Shift alphabet indices by 3'},{id:'reverse_row_runes',quote:'reverse each row.'}],expect:{retainedTexts:['Shift alphabet indices by 3'],keys:[null,null]}}),
 make('exact-scope-holes','Use the supplied route on LP2-00–03 and LP2-05.',{
  steps:[{quote:'Use the supplied route'}],scope:{pages:['lp2-00','lp2-01','lp2-02','lp2-03','lp2-05'],quote:'LP2-00–03 and LP2-05'},expect:{pages:['lp2-00','lp2-01','lp2-02','lp2-03','lp2-05'],excludedPages:['lp2-04']}}),
 make('qualified-passage','Reverse each row on LP2-43, lines 2–3.',{
  steps:[{id:'reverse_row_runes',quote:'Reverse each row'}],scope:{pages:['lp2-43'],passage:'lines 2–3',quote:'LP2-43, lines 2–3'},expect:{pages:['lp2-43'],passage:'lines 2–3'}}),
 make('scope-exclusion-not-inferred','Use the route on LP2-00–55 except LP2-50.',{
  steps:[{quote:'Use the route on LP2-00–55 except LP2-50.'}],scope:{passage:'LP2-00–55 except LP2-50',quote:'LP2-00–55 except LP2-50'},expect:{pages:null,passage:'LP2-00–55 except LP2-50',retainedTexts:['except LP2-50']}}),
 make('aim-decipher-whole','Find plaintext across LP2. Use a numerical autokey.',{
  outcome:{id:'decipher',quote:'Find plaintext across LP2'},steps:[{familyId:'feedback',quote:'Use a numerical autokey.'}],expect:{outcomeId:'decipher',outcomeDetail:'Find plaintext across LP2',pages:null}}),
 make('aim-decipher-opening','Recover readable text for the first sentence. Use a numerical autokey.',{
  outcome:{id:'decipher',quote:'Recover readable text for the first sentence'},steps:[{familyId:'feedback',quote:'Use a numerical autokey.'}],expect:{outcomeId:'decipher',outcomeDetail:'Recover readable text for the first sentence',pages:null}}),
 make('aim-explicit-limited-criterion','Recover only the first twelve runes. Use a numerical autokey.',{
  outcome:{id:'decipher',quote:'Recover only the first twelve runes'},steps:[{familyId:'feedback',quote:'Use a numerical autokey.'}],expect:{outcomeId:'decipher',outcomeDetail:'Recover only the first twelve runes',pages:null}}),
 make('negated-operation-opaque','Do not reverse each row; keep the ciphertext order.',{
  steps:[{quote:'Do not reverse each row; keep the ciphertext order.'}],expect:{retainedTexts:['Do not reverse each row','keep the ciphertext order'],keys:[null],ruleValues:{}}}),
 make('conditional-reset-literal','Use Vigenere with key ABC. Reset the key at each word unless the word continues across a line.',{
  steps:[{familyId:'polyalphabetic',quote:'Use Vigenere with key ABC.',key:{value:'ABC',quote:'key ABC'}}],rules:{reset:{value:'Reset the key at each word unless the word continues across a line',quote:'Reset the key at each word unless the word continues across a line'}},expect:{keys:['ABC'],unknownRules:['inputVersion','evaluation','initialState'],ruleValues:{reset:'Reset the key at each word unless the word continues across a line'},retainedTexts:['unless the word continues across a line']}}),
 make('opaque-code-generic-table','for x in values: emit(table.get(reverse_digits(x), x))',{
  steps:[{quote:'for x in values: emit(table.get(reverse_digits(x), x))'}],expect:{retainedTexts:['table.get(reverse_digits(x), x)'],unknownRules:['representation','unmapped','reset','inputVersion','evaluation','initialState'],keys:[null]}}),
 make('fixed-space-variant','Reverse each row; keep original space positions.',{
  steps:[{id:'reverse_row_runes',quote:'Reverse each row'}],rules:{boundaryMode:{value:'fixed_spaces',quote:'keep original space positions'}},expect:{ruleValues:{boundaryMode:'fixed_spaces'},unknownRules:['wordBoundaries','reset','inputVersion','evaluation','initialState']}}),
 make('explicit-unrestricted-and-not-applicable','Use the supplied method. Search bounds unrestricted; key reset not applicable.',{
  steps:[{quote:'Use the supplied method.'}],rules:{searchBounds:{status:'unrestricted',quote:'Search bounds unrestricted'},reset:{status:'not_applicable',quote:'key reset not applicable'}},expect:{unknownRules:['inputVersion','evaluation','initialState'],ruleStates:{searchBounds:'unrestricted',reset:'not_applicable'}}}),
 make('repeated-source-occurrences','Reverse each row. Reverse each row.',{
  steps:[{id:'reverse_row_runes',quote:'Reverse each row.',start:0},{id:'reverse_row_runes',quote:'Reverse each row.',start:18}],expect:{keys:[null,null]}}),
 make('uninterpreted-compound-tail','Reverse each row then apply my custom shedding operation.',{
  steps:[{id:'reverse_row_runes',quote:'Reverse each row'}],expect:{retainedTexts:['apply my custom shedding operation'],uninterpretedIncludes:['apply my custom shedding operation'],keys:[null]}})
];
