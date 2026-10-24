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
test('actual321 published records remain full evidence, never synthetic coverage or family identity',()=>{
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
