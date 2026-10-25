'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const C=require('../claim-specification.js');
const provenance={kind:'supplied',refs:['source:text']};
const known=value=>C.field('specified',value,provenance);
const method=id=>known({operations:[{id}]});
const at='2026-10-24T12:00:00.000Z';
const confirmed=d=>C.confirm(d,{id:'confirmation-'+d.revision,at});
const draft=(extra={})=>C.createDraft({source:{text:'Reverse rune order in rows on LP2-15 and LP2-17.'},
 method:method('reverse_row_runes'),scope:known({pages:['lp2-17','lp2-15','lp2-15']}),...extra});
let tests=0;
function test(name,fn){fn();tests++;console.log('PASS '+name);}

test('UMD browser and Node expose the same public API without DOM or network',()=>{
 const context={};vm.runInNewContext(fs.readFileSync(require.resolve('../claim-specification.js'),'utf8'),context);
 assert.equal(typeof context.ClaimSpecification.confirm,'function');
 assert.equal(context.ClaimSpecification.SCHEMA,C.SCHEMA);
});

test('plain evaluator choices explain availability and exact scope without changing criteria',()=>{
 const choices=C.EVALUATION_CHOICES;
 assert.deepEqual(choices.map(({id,value})=>({id,value})),[
  {id:'language-samples',value:{kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'}},
  {id:'readable-text',value:{kind:'readability'}},
  {id:'warning-opening',value:{kind:'exact-prefix',values:[24,7,24,4,9,21,17,18,20,10,18,1]}},
  {id:'inspect-output',value:'measurement'}
 ]);
 const byId=Object.fromEntries(choices.map(choice=>[choice.id,choice]));
 assert.match(byId['language-samples'].example,/eight fixed language samples/);
 assert.match(byId['language-samples'].example,/Similarity is not a translation/);
 assert.match(byId['readable-text'].label,/not available yet/);
 assert.match(byId['readable-text'].example,/cannot judge readability/);
 assert.match(byId['warning-opening'].label,/already-decoded opening/);
 assert.match(byId['warning-opening'].example,/first 12 runes.*decoded Warning passage.*page starts only/);
 assert.equal(byId['inspect-output'].label,'Show what the rule produces');
 assert.match(byId['inspect-output'].example,/runes and counts/);
 for(const choice of choices){
  assert(C.evaluationText(choice.value).startsWith(choice.label));
  assert(Object.isFrozen(choice));
 }
 assert.match(C.evaluationText(byId['warning-opening'].value),/page starts only/);
 assert.equal(C.evaluationText(byId['readable-text'].value),byId['readable-text'].label);
 assert.equal(C.evaluationText({kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'0'.repeat(64)}),null);
 assert.equal(C.evaluationText({kind:'exact-prefix',values:[24,7,24]}),null);
});
test('source fidelity, metadata-only material and no invented aim/method/GP defaults',()=>{
 const text='  def decode(x):\n    return x[::-1]\n';
 const d=C.fromText(text,[{name:'screenshot.png',bytes:450}]);
 assert.equal(d.source.text,text);assert.equal(d.source.materials[0].contentStatus,'metadata_only');
 assert.equal(d.aim.status,'unspecified');assert.equal(d.method.status,'unspecified');
 assert.equal(d.scope.status,'unspecified');assert.equal(d.rules.representation.status,'unspecified');
 assert.equal(C.completeness(d).researchReady,false);
});
test('four field states are distinct, with values only for specified fields',()=>{
 const fields=C.STATES.map(s=>s==='specified'?known([]):C.field(s));
 assert.equal(new Set(fields.map(C.serialize)).size,4);
 assert.throws(()=>C.field('unspecified',[]));assert.throws(()=>C.field('specified'));
 assert.throws(()=>C.field('specified','x',{kind:'inferred_truth',refs:[]}));
 assert.equal(known('maybe').provenance.kind,'supplied');
});
test('finite intent vocabulary unifies exact aliases while preserving wording and full meaning',()=>{
 const aims=['solve LP2','solving','solving LP2','decipher LP2','decrypt','find readable text'];
 const snapshots=aims.map(value=>confirmed(draft({aim:known(value)})));
 assert.deepEqual(Object.keys(C.OUTCOMES),['decipher','measure','reproduce','explain','verify_source']);
 assert(Object.isFrozen(C.OUTCOMES));
 for(let i=0;i<aims.length;i++){
  assert.equal(snapshots[i].aim.value,aims[i]);assert.equal(snapshots[i].aim.outcome.id,'decipher');
  assert.equal(C.outcomeLabel(snapshots[i].aim),'Decipher the text');
  assert.equal(C.reviewRows(snapshots[i])[0].tags[0].text,'Decipher the text');
 }
 assert.equal(new Set(snapshots.map(C.binding)).size,aims.length,'Canonical category is not exact meaning identity');
 const changed=C.revise(snapshots[0],{aim:known('Test a statistical effect')});
 assert.equal(changed.aim.outcome.id,'measure');assert.equal(changed.aim.value,'Test a statistical effect');
});
test('unknown, negative and partial wording cannot mint a category or promise full success',()=>{
 const before=C.serialize(C.OUTCOMES);
 for(const wording of ['Invent a moonlight category','Do not decrypt','Maybe solve LP2','Find partial readable output','def solve(x): return x']){
  const aim=C.normalizeAim(known(wording));assert.equal(aim.outcome.id,'unclassified');assert.equal(aim.outcome.detail,wording);assert.equal(aim.value,wording);
 }
 assert.equal(C.serialize(C.OUTCOMES),before);
 const aim=known({outcomeId:'decipher',wording:'Recover a partial opening',detail:'Only the first twelve runes; no full-page success claim'});
 const s=confirmed(draft({aim}));assert.equal(s.aim.outcome.id,'decipher');
 assert.deepEqual(s.aim.value,aim.value);assert(s.aim.outcome.detail.includes('no full-page success'));
 assert.equal(s.rules.evaluation.status,'unspecified');assert.equal(s.execution,'not_run');
 assert.equal(C.normalizeOutcome({outcomeId:'new_category',detail:'Keep the detail'}).id,'unclassified');
 for(const [id,label] of Object.entries(C.OUTCOMES))assert.equal(C.normalizeOutcome({outcomeId:'unclassified',wording:label,detail:label}).id,id);
 assert.equal(C.normalizeOutcome({outcomeId:'unclassified',wording:'Decipher the text',detail:'Estimate publication date'}).id,'unclassified');
 assert.equal(C.normalizeOutcome({outcomeId:'unclassified',wording:'Old wording',detail:'find readable text'}).id,'decipher');
 assert.equal(C.normalizeOutcome({outcomeId:'measure',wording:'Test a pattern',detail:'find readable text'}).id,'measure');
});
test('derived intent metadata is recomputed on create/revise and verified on deserialize',()=>{
 const forged={...known('solve LP2'),outcome:{id:'measure',label:'Wrong',detail:'discarded'}};
 const d=draft({aim:forged});assert.equal(d.aim.outcome.id,'decipher');
 const updated=C.revise(d,{scope:known({pages:['lp2-16']})});assert.equal(updated.aim.outcome.id,'decipher');
 const snapshot=JSON.parse(JSON.stringify(confirmed(d)));snapshot.aim.outcome.id='measure';
 assert.throws(()=>C.validateConfirmed(snapshot),/category metadata/);
});
test('intent retrieval preserves targeted wording without serializing category bookkeeping',()=>{
 const s=confirmed(draft({aim:known({outcomeId:'explain',wording:'Explain the line-six gap',detail:'Compare line6 with line7'})}));
 const q=C.retrievalQuery(s).query;assert(q.includes('line-six gap'));assert(q.includes('line6 with line7'));
 assert(!q.includes('outcomeId'));assert(!q.includes('"label"'));assert(!q.includes('[object Object]'));
 assert(C.queryForResearch(s,{maxLength:6000}).query.includes('Compare line6 with line7'));
 assert.equal(C.completeness(C.fromText('solve LP2')).researchReady,false,'Outcome text alone is not a method');
 const outcomeOnly=confirmed(C.fromText('solve LP2'));
 assert.deepEqual(C.retrievalQuery(outcomeOnly),{query:null,needsClarification:true,needsShorter:false});
 for(const outcomeId of Object.keys(C.OUTCOMES)){
  const standard=confirmed(draft({aim:known({outcomeId,wording:C.OUTCOMES[outcomeId],detail:C.OUTCOMES[outcomeId]})}));
  assert(!C.retrievalQuery(standard).query.includes(C.OUTCOMES[outcomeId]));
 }
});
test('method families use existing fixed IDs and preserve every ordered operation and parameter',()=>{
 const input=known({operations:[{id:'reverse_row_runes',reset:'page',offset:3},{id:'described_method',label:'Apply Vigenere with key FOO',key:'FOO'},{id:'prime_value_mapping',table:{status:'unspecified'}}]});
 const before=C.serialize(input),classified=C.classifyMethod(input);
 assert.deepEqual(classified.familyIds,['transposition','polyalphabetic','prime-indices']);
 assert.equal(classified.complete,true);assert.deepEqual(classified.operations.map(r=>r.operation),input.value.operations);
 assert.equal(C.serialize(input),before);
 const actual=JSON.parse(fs.readFileSync(require.resolve('../data/method-families.json'),'utf8')).families.map(f=>f.id);
 assert(Object.keys(C.METHOD_FAMILIES).every(id=>actual.includes(id)));
 assert.equal(C.classifyMethod(known({operations:[{id:'family_selection',familyId:'book-codes',label:C.METHODS['book-codes']}]})).operations[0].basis,'explicit_family');
 assert.deepEqual(C.classifyMethod(C.field()).familyIds,[]);
});
test('method classification does not infer from negative/code/compound snippets or generic value tables',()=>{
 for(const label of ['Do not use Caesar','Vigenere then Atbash','if (Caesar) { return key; }','Avoid Caesar','A note mentions Vigenere','Reverse decimal digits of each value']){
  assert.equal(C.classifyMethod(known({operations:[{id:'described_method',label}]})).operations[0].familyId,'unclassified',label);
 }
 assert.equal(C.classifyMethod(known({operations:[{id:'caesar_shift',label:'Caesar',sourceText:'Do not use Caesar'}]})).complete,false);
 assert.equal(C.classifyMethod(known({operations:[{id:'reverse_value_digits',label:'Reverse decimal digits of each prime value'}]})).operations[0].familyId,'prime-indices');
 assert.equal(C.classifyMethod(known({operations:[{id:'described_method',label:'Caesar with shift 3'}]})).operations[0].familyId,'fixed-substitution');
});
test('ordered step edits preserve untouched parameters/source and remap only related constraints',()=>{
 const d=draft({method:known({operations:[{id:'reverse_row_runes',reset:'row',sourceText:'Reverse rows'},
  {id:'vigenere',key:'FOO',reset:'page',nested:{offset:7}}]}),
  rules:{wordBoundaries:known('preserve'),boundaryMode:known('within_words')},
  unresolved:[{kind:'operation_ambiguity',operationIndex:0,text:'Which reverse?'},{kind:'custom',text:'Keep all exceptions'}]});
 const before=C.serialize(d),moved=C.applyMethodEdit(d,{type:'move',index:1,toIndex:0});
 assert.deepEqual(moved.method.value.operations,[d.method.value.operations[1],d.method.value.operations[0]]);
 assert.equal(moved.unresolved[0].operationIndex,1);assert.deepEqual(moved.unresolved[1],d.unresolved[1]);
 assert.deepEqual(moved.rules,d.rules);assert.deepEqual(moved.source,d.source);assert.equal(C.serialize(d),before);
 const added=C.applyMethodEdit(d,{type:'add',index:2,operation:{id:'atbash',sourceText:'Then Atbash'}});
 assert.deepEqual(added.method.value.operations.slice(0,2),d.method.value.operations);assert.deepEqual(added.rules,d.rules);
 const removed=C.applyMethodEdit(d,{type:'remove',index:0});
 assert.deepEqual(removed.method.value.operations,[d.method.value.operations[1]]);
 assert.deepEqual(removed.unresolved,[d.unresolved[1]]);assert.equal(removed.rules.boundaryMode.status,'unspecified');
 assert.deepEqual(removed.methodEdits.at(-1).retiredConstraints,[d.unresolved[0]]);
 assert.equal(C.applyMethodEdit(removed,{type:'remove',index:0}).method.status,'unspecified');
 const single=draft({unresolved:[{kind:'operation_ambiguity',text:'Reverse?'}]});
 const prepend=C.applyMethodEdit(single,{type:'add',index:0,operation:{id:'vigenere',key:'FOO'}});
 assert.equal(prepend.unresolved[0].operationIndex,1);
 assert.equal(C.clarify(prepend,'operation','reverse_value_digits').method.value.operations[1].id,'reverse_value_digits');
});
test('changed wording retires exact semantics with full history; category is separate from execution',()=>{
 const old={id:'vigenere',key:'FOO',reset:'page',sourceText:'Use Vigenere FOO',provenance:{kind:'supplied',refs:['line2']}};
 const d=draft({method:known({operations:[old,{id:'atbash'}]}),unresolved:[{kind:'operation_ambiguity',operationIndex:0,text:'Old question'},{kind:'custom',text:'Independent'}]});
 const changed=C.applyMethodEdit(d,{type:'wording',index:0,text:'Use a different cipher with key BAR'});
 const op=changed.method.value.operations[0];assert.equal(op.id,'described_method');assert.equal(op.key,undefined);assert.equal(op.reset,undefined);
 assert.equal(op.sourceText,old.sourceText);assert.equal(op.label,'Use a different cipher with key BAR');
 assert.deepEqual(changed.methodEdits.at(-1).previousOperation,old);assert.deepEqual(changed.unresolved,[d.unresolved[1]]);
 assert.deepEqual(changed.method.value.operations[1],d.method.value.operations[1]);
 const categorized=C.applyMethodEdit(d,{type:'category',index:0,familyId:'transposition'});
 assert.equal(categorized.method.value.operations[0].key,'FOO');assert.equal(C.classifyMethod(categorized.method).operations[0].basis,'category_conflict');
 const cleared=C.applyMethodEdit(categorized,{type:'category',index:0,familyId:null});assert.deepEqual(cleared.method.value.operations[0],old);
 const replaced=C.applyMethodEdit(d,{type:'replace',index:0,operation:{id:'caesar_shift',shift:3}});assert.equal(replaced.method.value.operations[0].key,undefined);
 assert.throws(()=>C.applyMethodEdit(d,{type:'move',index:0,toIndex:2}));assert.throws(()=>C.applyMethodEdit(d,{type:'category',index:0,familyId:'visitor-family'}));
});
test('editing a source-linked step requires review of its extracted rules without guessing replacements',()=>{
 const P=require('../claim-interpretation.js'),R=require('../claim-research.js');
 const raw='Use Vigenere with key ABC. Reset the key at each word. Use only black runes.';
 const step='Use Vigenere with key ABC. Reset the key at each word.',rule='Reset the key at each word.';
 const source=quote=>({start:raw.indexOf(quote),quote});
 const d=P.toDraft(raw,{schema:P.SCHEMA,outcome:null,
  steps:[{id:'described_method',familyId:'polyalphabetic',source:source(step),parameters:{}}],scope:null,
  rules:{reset:{status:'specified',value:rule,source:source(rule)},representation:{status:'specified',value:'Use only black runes.',source:source('Use only black runes.')}}}).draft;
 const changed=C.applyMethodEdit(d,{type:'wording',index:0,text:'Use Vigenere with key ABC. Reset the key at each page.'});
 assert.equal(changed.rules.reset.value,rule,'Old condition stays visible until explicitly resolved');
 assert.deepEqual(changed.rules.representation,d.rules.representation,'Independent source condition stays exact');
 assert.deepEqual(C.questions(changed).map(q=>q.id),['rule-review:reset']);
 assert.equal(C.completeness(changed).researchReady,false);assert.throws(()=>confirmed(changed));
 const replaced=C.clarify(changed,'rule-review:reset','replace','Reset the key at each page.');
 assert.equal(replaced.rules.reset.value,'Reset the key at each page.');assert.equal(C.questions(replaced).length,0);
 assert.equal(replaced.source.text,raw);assert.deepEqual(replaced.rules.representation,d.rules.representation);
 assert(!R.prepare(confirmed(replaced)).request.card.rules.reset.value.includes('word'));
 assert.throws(()=>C.clarify(changed,'rule-review:reset','replace','  '));
 const kept=C.clarify(changed,'rule-review:reset','keep');assert.equal(kept.rules.reset.value,rule);assert.equal(C.questions(kept).length,0);
 for(const resolved of [kept,replaced]){
  const editedAgain=C.applyMethodEdit(resolved,{type:'wording',index:0,text:'Use Vigenere with key ABC. Reset the key at each line.'});
  assert.deepEqual(C.questions(editedAgain).map(q=>q.id),['rule-review:reset'],'Resolving a review retains its dependency for later edits');
  assert.equal(C.questions(C.applyMethodEdit(resolved,{type:'remove',index:0}))[0].id,'rule-review:reset');
  const withSibling=C.applyMethodEdit(resolved,{type:'add',index:0,operation:{id:'atbash'}});
  assert.equal(C.questions(C.applyMethodEdit(withSibling,{type:'wording',index:0,text:'Apply Caesar shift 3'})).length,0,'A new sibling does not inherit the old dependency');
  const moved=C.applyMethodEdit(withSibling,{type:'move',index:1,toIndex:0});
  assert.equal(C.questions(C.applyMethodEdit(moved,{type:'wording',index:0,text:'Reset the key at each line.'}))[0].id,'rule-review:reset');
 }
 const removed=C.clarify(changed,'rule-review:reset','remove');assert.equal(removed.rules.reset.status,'unspecified');assert.equal(C.questions(removed).length,0);
 const manual=C.revise(changed,{rules:{reset:known('Restart each page')}});assert.equal(C.questions(manual).length,0);
 const again=C.applyMethodEdit(changed,{type:'wording',index:0,text:'Use a different key stream.'});assert.deepEqual(C.questions(again).map(q=>q.id),['rule-review:reset'],'Further edits cannot drop the pending decision');
 for(const edit of [{type:'remove',index:0},{type:'replace',index:0,operation:{id:'atbash'}}])assert.equal(C.questions(C.applyMethodEdit(d,edit))[0].id,'rule-review:reset');
 for(const edit of [{type:'wording',index:0,text:step},{type:'category',index:0,familyId:'polyalphabetic'},{type:'add',index:1,operation:{id:'atbash'}},{type:'move',index:0,toIndex:0}])assert.equal(C.questions(C.applyMethodEdit(d,edit)).length,0,'No rule review for unchanged meaning, category, new independent step or reorder');
 const invalid=C.createDraft({...d,rules:{...d.rules,reset:C.field('specified',rule,{kind:'proposed',refs:[JSON.stringify({source:'original wording',start:0,end:step.length,quote:'not the source'})]})}});
 assert.equal(C.questions(C.applyMethodEdit(invalid,{type:'wording',index:0,text:'Different method'})).length,0,'Unverified offsets cannot establish a dependency');
});

test('exact scope normalizes harmless order/duplicates but keeps holes and explicit empty sets',()=>{
 assert.deepEqual(draft().scope.value.pages,['lp2-15','lp2-17']);
 assert.deepEqual(C.pages(['lp2-57','lp1-16']),['lp1-16','lp2-57']);
 for(const invalid of [['lp2-58'],['lp1-17'],[15],['lp2-1']])assert.throws(()=>C.pages(invalid));
 assert.notDeepEqual(draft().scope,C.field());
 assert.deepEqual(draft({scope:known({pages:[]})}).scope.value.pages,[]);
 assert(!C.reviewRows(draft()).find(r=>r.label==='Scope').tags.some(t=>t.text==='LP2-16'));
});
test('source wording and interpretation can differ without overwriting either',()=>{
 const d=draft({source:{text:'Maybe reverse prime values?'}});
 assert.equal(d.source.text,'Maybe reverse prime values?');assert.equal(d.method.value.operations[0].id,'reverse_row_runes');
 assert(C.summary(d).includes('Aim not specified'));assert(!C.summary(d).includes('Solve LP2'));
});
test('three word-boundary meanings are distinct and confirmation requires their resolution',()=>{
 const d=draft({rules:{wordBoundaries:known('preserve')}});
 const q=C.questions(d)[0];assert.equal(q.id,'word-boundary');
 assert.deepEqual(q.choices.slice(0,3).map(c=>c.example),['BA EDC','ED CBA','CDE AB']);
 assert.throws(()=>confirmed(d));
 const bindings=[];
 for(const choice of ['within_words','fixed_spaces','word_blocks']){
  const next=C.clarify(d,'word-boundary',choice);assert.equal(C.questions(next).length,0);
  assert.equal(next.rules.boundaryMode.provenance.kind,'user_clarification');
  bindings.push(C.binding(confirmed(next)));
 }
 assert.equal(new Set(bindings).size,3);assert.equal(d.revision,1);
});
test('scope change preserves independent rules; method changes revalidate boundary meaning',()=>{
 const d=C.clarify(draft({rules:{wordBoundaries:known('preserve'),unmapped:known('keep_original')}}),'word-boundary','within_words');
 const scoped=C.revise(d,{scope:known({pages:['lp2-16']})});
 assert.equal(scoped.rules.boundaryMode.value,'within_words');
 const digits=C.revise(scoped,{method:method('reverse_value_digits')});
 assert.equal(digits.rules.unmapped.value,'keep_original');assert.equal(digits.rules.wordBoundaries.value,'preserve');
 const back=C.revise(digits,{method:method('reverse_row_runes')});
 assert.equal(C.questions(back)[0].id,'word-boundary');
});
test('Other and unrecognized constraints survive clarification without invented interpretation',()=>{
 let d=draft({unresolved:[{kind:'operation_ambiguity',text:'Reverse the prime values'}, {kind:'source_constraint',text:'Use only blue marks'}]});
 assert.equal(C.questions(d)[0].id,'operation');
 d=C.clarify(d,'operation','other','Rotate triangles clockwise');
 assert(d.unresolved.some(c=>c.text==='Rotate triangles clockwise'));
 assert.equal(C.completeness(d).researchReady,false);
 d=C.clarify(d,'operation','reverse_value_digits');
 assert(d.unresolved.some(c=>c.text==='Use only blue marks'));
 assert(d.unresolved.some(c=>c.text==='Rotate triangles clockwise'));
 assert.equal(C.completeness(d).researchReady,false);
});
test('compound method order and unknown parameters remain explicit',()=>{
 const a=draft({method:known({operations:[{id:'reverse_row_runes'},{id:'keyword_cipher',key:{status:'unspecified'}}]})});
 const b=draft({method:known({operations:[{id:'keyword_cipher',key:{status:'unspecified'}},{id:'reverse_row_runes'}]})});
 assert.notEqual(C.binding(confirmed(a)),C.binding(confirmed(b)));
 assert.deepEqual(a.method.value.operations[1].key,{status:'unspecified'});
 assert(C.completeness(a).missing.includes('method.value.operations.1.key'));
 const ambiguous=draft({method:known({operations:[{id:'unknown_reverse'},{id:'keyword_cipher',key:{status:'unspecified'}}]}),unresolved:[{kind:'operation_ambiguity',operationIndex:0}]});
 const clarified=C.clarify(ambiguous,'operation','reverse_value_digits');
 assert.equal(clarified.method.value.operations[1].id,'keyword_cipher');
 assert.equal(clarified.method.value.operations[1].key.status,'unspecified');
 const manual=draft({method:known({operations:[{id:'ambiguous',label:'Original ambiguous piece',key:'FOO'},{id:'cipher',key:'BAR'}]}),unresolved:[{kind:'operation_ambiguity',operationIndex:0}]});
 const chosen=C.clarify(manual,'operation','reverse_row_runes');
 assert.equal(chosen.method.value.operations[0].sourceText,'Original ambiguous piece');
 assert.equal(chosen.method.value.operations[0].key,'FOO');
 assert.deepEqual(chosen.method.value.operations[1],manual.method.value.operations[1]);
});
test('confirmation approves incomplete meaning and never marks work executed',()=>{
 const d=draft(),s=confirmed(d);
 assert.equal(s.status,'confirmed_incomplete');assert.equal(s.execution,'not_run');
 assert.equal(C.completeness(s).researchReady,true);assert.equal(C.completeness(s).executionReady,false);
 assert(Object.isFrozen(s)&&Object.isFrozen(s.scope.value.pages));
 const old=C.serialize(s);const next=C.revise(s,{rules:{unmapped:known('reject')}});
 assert.equal(next.status,'draft');assert.equal(next.confirmation,null);
 assert.equal(C.serialize(s),old);assert.equal(next.revision,s.revision+1);
 assert.throws(()=>{s.source.text='changed';});
});
test('fully specified protocol still is not a run',()=>{
 const rules=Object.fromEntries(C.RULES.map(k=>[k,C.field('not_applicable')]));
 rules.inputVersion=known('sha256:example');rules.evaluation=known('exact expected output');
 const s=confirmed(draft({aim:known('Check an invariant'),rules}));
 assert.equal(s.status,'confirmed_specified');assert.equal(s.execution,'not_run');
});
test('tampered confirmation and unsafe input are rejected',()=>{
 const s=JSON.parse(JSON.stringify(confirmed(draft())));s.canonical='This solves LP2';
 assert.throws(()=>C.validateConfirmed(s));
 assert.throws(()=>draft({scope:known({pages:['lp2-99']})}));
 assert.throws(()=>C.createDraft({source:JSON.parse('{"text":"x","__proto__":{"polluted":true}}')}));
 assert.throws(()=>C.revise(draft(),{source:{text:'replacement'}}));
});
test('compact review avoids a generic protocol questionnaire and keeps unresolved rules visible',()=>{
 const d=draft({method:method('reverse_value_digits')});
 const rows=C.reviewRows(d);assert.deepEqual(rows.map(r=>r.label),['Aim','Method','Scope','Rules']);
 assert.deepEqual(rows[3].tags.map(t=>t.id),['rule:unmapped']);
 assert.equal(rows[3].tags[0].unknown,true);
});
test('research query preserves source, exact scope, order/rules and never truncates',()=>{
 const s=confirmed(draft({rules:{unmapped:known('reject')}}));
 const q=C.queryForResearch(s);assert.equal(q.needsShorter,false);
 assert(q.query.includes(s.source.text));assert(q.query.includes('reject'));
 assert.deepEqual(q.pages,['lp2-15','lp2-17']);
 const small=C.queryForResearch(s,{maxLength:20});assert.equal(small.query,null);assert.equal(small.needsShorter,true);
 assert(small.length>20);
 const huge=confirmed(draft({source:{text:'x'.repeat(1500)}}));assert.equal(C.queryForResearch(huge).query,null);
});
test('actual published records remain full evidence, never synthetic coverage or family identity',()=>{
 const records=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8')).records.filter(r=>r.status==='published');
 assert(records.length>=321);
 const selected=records.filter(r=>['direct-hill-key-feasibility','relikd-autokey-interrupt-database'].includes(r.id));
 const s=confirmed(draft());
 const result=C.bindResearch(s,{id:'research-local',at,evidence:{snapshotId:'test-registry',records:selected},answer:'A scoped comparison, not a new test.',proposedTests:[{description:'Define an input',execution:'completed'}]});
 assert.deepEqual(result.evidence.records[1].scope,selected[1].scope);
 assert.equal(result.proposedTests[0].execution,'not_run');
 assert(!Object.hasOwn(result,'coverage'));assert(!Object.hasOwn(result,'novelty'));
 const packet=C.packetSnapshot(s,result);assert.equal(packet.research.answer,result.answer);
 assert.throws(()=>C.packetSnapshot(confirmed(C.revise(s,{scope:known({pages:['lp2-16']})})),result));
 assert.throws(()=>C.bindResearch(s,{id:'bad',at,evidence:{snapshotId:'x',records:[{id:'title-only',status:'published'}]},answer:'x'}));
});
console.log(`PASS ${tests} claim-specification tests; no inference, fetch, target science or fixture research imported.`);
