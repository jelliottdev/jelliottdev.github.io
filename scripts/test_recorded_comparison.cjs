'use strict';
/* Synthetic metadata and confirmed cards only; no model, fetch or experiment run. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const C=require('../claim-specification.js'),H=require('../claim-share.js'),M=require('../assistant-markdown.js'),R=require('../recorded-comparison.js');
const known=value=>C.field('specified',value),at='2026-10-24T12:00:00Z';
const make=(extra={})=>C.confirm(C.createDraft({source:{text:'Reverse each row on LP2-15'},aim:known({outcomeId:'decipher',detail:'Find readable text'}),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows',sourceText:'Reverse each row on LP2-15'}]}),scope:known({pages:['lp2-15']}),...extra}),{id:'fixture',at});
const metadata=(extra={})=>({version:1,operation:{action:'reverse',operand:'rune-order',within:'row'},executed_pages:['lp2-15','lp2-17'],evaluation:{kind:'known-opening',description:'The first 12 runes were checked against nine fixed openings.',limitation:'Other beginnings were not tested.'},input_description:'Archived rune rows, including headings, were retained.',reuse:'Complete candidate outputs and their source positions are saved.',...extra});
const doc=(id='arbitrary-route-record',m=metadata(),extra={})=>({id,title:'An authored record',kind:'experiment',recordType:'method',href:'#/experiments/'+id,text:JSON.stringify({record_type:{id:'method'},scope:{pages:['lp2-15','lp2-17','lp2-50']}}),recordedComparison:m,...extra});
const compare=(snapshot=make(),documents=[doc()])=>R.compare({snapshot,documents});
let groups=0;function test(name,fn){fn();groups++;console.log('PASS '+name);}
test('generic authored overlap retains exact source objects and limits, without a goal verdict',()=>{
 const d=doc(),before=JSON.stringify(d),s=make(),identity=C.binding(s),result=compare(s,[d]);
 assert.equal(result.kind,'recorded-overlap');assert.equal(result.sources[0],d);assert.equal(JSON.stringify(d),before);assert.equal(C.binding(s),identity);
 assert(result.answer.includes('LP2-15 [1]'));assert(result.answer.includes('matches the reversal step; other unspecified settings may differ'));
 for(const value of [metadata().input_description,metadata().evaluation.description])assert(result.answer.includes(value));
 for(const value of [metadata().reuse,metadata().evaluation.limitation])assert(!result.answer.includes(value),'Supporting facts are not repeated in the comparison');
 assert.equal(result.sources[0].recordedComparison.evaluation.limitation,metadata().evaluation.limitation,'Complete source metadata is retained');
 assert.deepEqual(M.citationNumbers(result.answer,1),[1]);assert.equal(result.answer.split('\n\n').length,2);assert(result.answer.split(/\s+/).length<=180);
 assert(!/failed|unreadable|solved|independent trials/i.test(result.answer));
});
test('two evaluation purposes retain citation binding and shared prose without duplication',()=>{
 const a=doc(),english=metadata({evaluation:{kind:'english-score',description:'Whole outputs were scored with a fixed English model.',limitation:'Scores do not establish plaintext or judge every route.'}}),b=doc('arbitrary-scored-record',english);
 const result=compare(make(),[{kind:'page',id:'lp2-15',text:'Page context'},a,b]);assert.deepEqual(result.sources,[a,b]);
 assert.deepEqual(M.citationNumbers(result.answer,2),[1,2]);assert(result.answer.includes(metadata().input_description+' [1, 2]'));
 assert(result.answer.includes(english.evaluation.description+' [2]'));assert(result.answer.includes(metadata().evaluation.description+' [1]'));
 const imported=H.decode(H.encode(make())).draft,shared=C.confirm(imported,{id:'shared',at});assert.equal(compare(shared,[a,b]).answer,result.answer);
});
test('separate authored metadata drives direct comparison without changing ordinary evidence text',()=>{
 const original=doc(),changed={...original,recordedComparison:metadata({input_description:'Rows including headings were reversed without retaining spaces.'})};
 assert.equal(changed.text,original.text);assert(!original.text.includes('recorded_comparison'));
 assert.notEqual(compare(make(),[changed]).answer,compare(make(),[original]).answer);
 assert.equal(compare(make(),[{...original,recordedComparison:metadata({executed_pages:['lp2-56']})}]),null);
 const embedded={...original,recordedComparison:undefined,text:JSON.stringify({...JSON.parse(original.text),recorded_comparison:metadata()})};
 assert.equal(compare(make(),[embedded]),null,'Embedded metadata cannot supply direct-comparison authority');
});
test('all requested pages must be executed by each retained source; partial sources are filtered',()=>{
 const snapshot=make({scope:known({pages:['lp2-15','lp2-17']}),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'}]})});
 const whole=doc(),partial=doc('partial',metadata({executed_pages:['lp2-15']}));assert.deepEqual(compare(snapshot,[partial,whole]).sources,[whole]);
 assert.equal(compare(snapshot,[partial,doc('other-partial',metadata({executed_pages:['lp2-17']}))]),null);
 assert.equal(compare(make({scope:known({pages:['lp2-50']})})),null);assert.equal(compare(make({scope:known({pages:['lp2-56']})})),null);
});
test('only exact supported canonical operation and positive labels qualify',()=>{
 const op=value=>make({method:known({operations:[value]})});
 for(const value of [{id:'family_selection',familyId:'transposition'}, {id:'described_method',label:'Reverse each row'}, {id:'reverse_word_order'},
  {id:'reverse_row_runes',label:'Reverse each row then Atbash'}, {id:'reverse_row_runes',sourceText:'Do not reverse each row'},
  {id:'reverse_row_runes',label:'Reverse each row except headings'}, {id:'reverse_row_runes',sourceText:'Reverse each row on LP2-17'},
  {id:'reverse_row_runes',parameters:{}}, {id:'reverse_row_runes',operand:'word-order'}, {id:'reverse_row_runes',declaredFamilyId:'feedback'}])assert.equal(compare(op(value)),null,JSON.stringify(value));
 for(const label of ['Reverse rune order within rows','Reverse each row','Read each row backwards'])assert(compare(op({id:'reverse_row_runes',label})));
 assert.equal(compare(make({method:known({operations:[{id:'reverse_row_runes'},{id:'atbash'}]})})),null);
});
test('all explicit rule states, including retained gaps, fall back rather than match unknown settings',()=>{
 for(const key of C.RULES)for(const field of [known(key==='boundaryMode'?'fixed_spaces':'retain'),C.field('not_applicable'),C.field('unrestricted')])assert.equal(compare(make({rules:{[key]:field}})),null,key+':'+field.status);
 assert.equal(compare(make({unresolved:[{kind:'source_note',text:'Keep the word gaps'}]})),null);
});
test('whole-page explicit scope and decipher category are required, with no unknown or qualified scope',()=>{
 for(const scope of [C.field(),known({pages:[]}),known({pages:['lp2-15'],description:'Only lines 2–3'}),known({pages:['lp2-15'],artifacts:[]}),known({pages:['lp2-15'],inputVersion:'other'})])assert.equal(compare(make({scope})),null);
 for(const aim of [C.field(),known('Test a pattern'),known({outcomeId:'unclassified',detail:'Explain the origin'})])assert.equal(compare(make({aim})),null);
 assert(compare(make({aim:known('solve LP2')})));assert(compare(make({aim:known('Find readable text')})));
});
test('metadata requires controlled exact fields, valid executed subset and unique normalized page lists',()=>{
 const base=metadata();
 for(const m of [null,{}, {...base,version:2},{...base,extra:true},{...base,operation:{...base.operation,within:'word'}},
  {...base,operation:{...base.operation,offset:0}},{...base,evaluation:{...base.evaluation,kind:'readable'}},
  {...base,evaluation:{...base.evaluation,pass:true}},{...base,executed_pages:[]},{...base,executed_pages:['lp2-15','lp2-15']},
  {...base,executed_pages:['lp2-17','lp2-15']},{...base,executed_pages:['lp2-56']},{...base,input_description:''},
  {...base,reuse:'x'.repeat(501)},{...base,reuse:'Forged citation [99].'},{...base,reuse:'Line one\nLine two'}])assert.equal(compare(make(),[doc('malformed',m)]),null,JSON.stringify(m));
 const invalidScope=doc();const evidence=JSON.parse(invalidScope.text);evidence.scope.pages=['lp2-17','lp2-15'];invalidScope.text=JSON.stringify(evidence);assert.equal(compare(make(),[invalidScope]),null);
});
test('discovery hints, audits, malformed evidence and mismatched citation destinations never qualify',()=>{
 const d=doc(),e=JSON.parse(d.text);e.discovery={operations:[metadata().operation],evaluation:['known-opening']};e.recorded_comparison=metadata();
 for(const bad of [{...d,recordedComparison:undefined,text:JSON.stringify(e)}, {...d,text:'{broken'}, {...d,text:'x'.repeat(64001)}, {...d,kind:'page'},
  {...d,recordType:'audit'}, {...d,href:'https://example.org'}, {...d,href:'#/experiments/another-id'}, {...d,id:'../../unsafe'},
  {...d,text:JSON.stringify({...JSON.parse(d.text),record_type:{id:'control'}})}])assert.equal(compare(make(),[bad]),null);
 assert.equal(compare(make(),[]),null);assert.equal(R.compare({snapshot:{},documents:[d]}),null);
});
test('at most two distinct sources, finite answer budget and deterministic browser parity',()=>{
 const documents=[doc('first'),doc('first'),doc('second'),doc('third')],result=compare(make(),documents);assert.deepEqual(result.sources,[documents[0],documents[2]]);
 const manyWords=Array(100).fill('word').join(' '),long=doc('long',metadata({input_description:manyWords,reuse:manyWords,evaluation:{kind:'known-opening',description:manyWords+' extra',limitation:manyWords}}));
 assert.equal(compare(make(),[long]),null);
 const browser={ClaimSpecification:C};vm.runInNewContext(fs.readFileSync(require.resolve('../recorded-comparison.js'),'utf8'),browser);
 assert.equal(JSON.stringify(browser.RecordedComparison.compare({snapshot:make(),documents})),JSON.stringify(result));
});
const Research=require('../claim-research.js'),Search=require('../assistant-search.js');
function sumSnapshot(table='reversed',extra={}){return make({aim:known({outcomeId:'measure',detail:'Inspect numeric structure'}),
 method:known({operations:[{id:'word_prime_sums',label:'Word prime sums',table,boundaries:'hyphen-period'}]}),
 rules:{representation:known('GP29'),inputVersion:known('raw'),wordBoundaries:known('preserve'),unmapped:known('preserve'),evaluation:known({kind:'word-prime-sums',table,boundaries:'hyphen-period'})},...extra});}
function sumDoc(id='arbitrary-word-sums',table='canonical',within='word',target=['lp1-05']){return doc(id,undefined,{recordType:'measurement',
 discovery:{operations:[{action:'sum',operand:'prime-values',within,table}],evaluation:['numeric-sums']},
 text:JSON.stringify({record_type:{id:'measurement'},scope:{pages:target,procedure:'Complete source procedure retained',exclusions:'No boundary or prime-table transfer'},finding:{result:'Scoped source finding'}})});}
test('numeric records deterministically describe related table and actual page scope without inferred equivalence',()=>{
 const documents=[sumDoc(),sumDoc('another-word-sum','canonical','word',['lp2-00','lp2-01'])],snapshot=sumSnapshot(),before=C.serialize(snapshot),result=compare(snapshot,documents);
 assert(result);assert.equal(result.kind,'recorded-overlap');assert.deepEqual(result.sources,Search.select(documents,Research.prepare(snapshot).query,Research.prepare(snapshot).pages,Research.prepare(snapshot).discovery));
 assert.equal(C.serialize(snapshot),before);assert.equal(result.sources[0],documents[0]);assert(result.answer.includes('(usual table)'));assert(result.answer.includes('Your idea uses the reversed prime table'));assert(!result.answer.includes('canonical'));
 assert(result.answer.includes('on LP1-05 (usual table)'));assert(result.answer.includes('on LP2-00–01 (usual table)'));
 assert(result.answer.includes('related work, not the same test'));assert(result.answer.includes('do not establish that your chosen word boundaries or way of evaluating the sums were tested'));
 assert(!/directly tests|selectivity|significant|p.value|algorithm|caus|decrypt|failed|unreadable|solved/i.test(result.answer));assert.deepEqual(M.citationNumbers(result.answer,2),[1,2]);assert(result.answer.split(/\s+/).length<=100,'Numeric explanation stays concise');
 assert.equal(result.sources[0].text,documents[0].text);assert.equal(JSON.parse(result.sources[0].text).scope.exclusions,'No boundary or prime-table transfer');
 const same=compare(sumSnapshot('canonical'),[documents[0]]);assert(same.answer.includes('use the usual prime table too'));assert(same.answer.includes('a shared summation step, not the same test'));assert(same.answer.includes('do not establish that your chosen word boundaries'));
 const row=compare(snapshot,[sumDoc('row-source','canonical','row',['lp2-15'])]);assert(row.answer.includes('within rows'));assert(row.answer.includes('these records use the usual table'));
});
test('numeric authored metadata and requested scope rules must be complete strict and source bound',()=>{
 const snapshot=sumSnapshot(),base=sumDoc();
 for(const change of [d=>delete d.discovery,d=>d.discovery.extra=true,d=>d.discovery.evaluation=['english-readability'],
  d=>d.discovery.operations[0].table='digits',d=>d.discovery.operations[0].extra=true,d=>d.discovery.operations[0].within='page',
  d=>d.href='#/experiments/wrong',d=>d.recordType='audit',d=>d.text='{broken',d=>d.text=JSON.stringify({record_type:{id:'measurement'},scope:{pages:[]}}),
  d=>d.text=JSON.stringify({record_type:{id:'measurement'},scope:{pages:['lp2-15','lp2-15']}}),
  d=>d.text=JSON.stringify({record_type:{id:'measurement'},scope:{pages:['lp2-17','lp2-15']}})]){
  const bad=structuredClone(base);change(bad);assert.equal(compare(snapshot,[bad]),null);
 }
 for(const change of [s=>s.rules.inputVersion=known('reviewed'),s=>s.rules.representation=known('latin'),s=>s.rules.searchBounds=known('up to 10'),
  s=>s.rules.reset=known('word'),s=>s.rules.evaluation=known({kind:'word-prime-sums',table:'canonical',boundaries:'hyphen-period'}),
  s=>s.method.value.operations[0].label='Word prime sums then Atbash',s=>s.method.value.operations[0].declaredFamilyId='feedback',
  s=>s.method.value.operations.push({id:'atbash',label:'Atbash'}),s=>s.unresolved.push({kind:'source_note',text:'retain'}),
  s=>s.scope=known({pages:['lp2-15'],description:'only a heading'})]){
  const draft=C.revise(snapshot,{});change(draft);assert.equal(compare(C.confirm(draft,{id:'unsupported-numeric',at}),[base]),null);
 }
 const huge={...base,text:base.text+' '.repeat(9001)};assert.equal(compare(snapshot,[huge]),null,'Never truncate leading complete source evidence');
});
test('numeric comparison keeps browser and Worker source order and legacy browser dependency fallback',()=>{
 const snapshot=sumSnapshot(),documents=[sumDoc('second-source','canonical','word',['lp2-17']),sumDoc('first-source','canonical','word',['lp1-05'])],result=compare(snapshot,documents);
 const browser={ClaimSpecification:C,ClaimResearch:Research,AssistantSearch:Search};vm.runInNewContext(fs.readFileSync(require.resolve('../recorded-comparison.js'),'utf8'),browser);
 assert.equal(JSON.stringify(browser.RecordedComparison.compare({snapshot,documents})),JSON.stringify(result));
 const legacy={ClaimSpecification:C};vm.runInNewContext(fs.readFileSync(require.resolve('../recorded-comparison.js'),'utf8'),legacy);
 assert.equal(legacy.RecordedComparison.compare({snapshot,documents}),null);assert(legacy.RecordedComparison.compare({snapshot:make(),documents:[doc()]}),'Old reverse comparison remains usable without optional numeric dependencies');
 const competing=sumDoc('same-table','reversed');assert.equal(compare(snapshot,[...documents,competing]).sources[0],competing,'Same S.select table preference supplies deterministic answer citations');
});
console.log(`PASS ${groups} recorded-comparison groups; no AI, network, static record-ID gates or experiment execution.`);
