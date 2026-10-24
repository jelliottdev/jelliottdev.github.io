'use strict';
// Candidate discovery only: selected records retain their actual execution scope.
// Requires the current generated full and compact registries, never hosted calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const C=require('../claim-specification.js'),R=require('../claim-research.js'),S=require('../assistant-search.js');
const root=path.resolve(__dirname,'..');
const full=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'),'utf8'));
const compact=JSON.parse(fs.readFileSync(path.join(root,'data/checker-records.json'),'utf8'));
const fullDocs=S.experimentDocs(full.records),compactDocs=S.experimentDocs(compact.records);
const f=value=>C.field('specified',value),ids=docs=>docs.map(doc=>doc.id);
const scope={pages:['lp2-15','lp2-17'],description:'Only the first two visible rows; no joins across pages'};
function card(boundary=null,tail=[]){return C.confirm(C.createDraft({
 source:{text:'Reverse each row of runes. Preserve the exact supplied scope, boundaries and ordered later steps.'},
 aim:f({outcomeId:'decipher',wording:'Recover readable English',detail:'Recover a readable passage; a full solution is not claimed'}),
 method:f({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'},...tail]}),scope:f(scope),
 rules:boundary?{wordBoundaries:f('preserve'),boundaryMode:f(boundary)}:{}
}),{id:'discovery-regression',at:'2026-10-24T12:00:00Z'});}
function prepare(snapshot){const before=C.serialize(snapshot),prepared=R.prepare(snapshot);
 assert.equal(C.serialize(snapshot),before,'Discovery must not rewrite the confirmed meaning');
 assert.deepEqual(prepared.pages,scope.pages,'Exact holes stay separate from discovery hints');
 assert.deepEqual(prepared.request.card.scope.value,scope);
 assert(!Object.hasOwn(prepared.request,'discovery'),'Hints are derived, never caller-authoritative request fields');
 assert.throws(()=>R.validate({...prepared.request,discovery:{steps:[]}}),'External hints must not override canonical derivation');
 return prepared;}
const browser={};vm.runInNewContext(fs.readFileSync(path.join(root,'assistant-search.js'),'utf8'),browser);
function select(prepared,docs=fullDocs){return S.select(docs,prepared.query,prepared.pages,prepared.discovery);}
function parity(prepared){
 const found=select(prepared);
 assert.deepEqual(select(prepared,compactDocs),found,'Compact/full evidence and discovery metadata must agree exactly');
 assert.equal(JSON.stringify(browser.AssistantSearch.select(fullDocs,prepared.query,prepared.pages,prepared.discovery)),JSON.stringify(found),'Browser and Worker selection must agree');
 assert(found.filter(doc=>doc.kind==='experiment').reduce((sum,doc)=>sum+doc.text.length,0)<=9000);
 for(const doc of found){const original=fullDocs.find(d=>d.id===doc.id);assert.equal(doc.text,original.text,'No shortened procedure, exclusions or output limits');}
 return found;
}

const row=prepare(card());
assert.deepEqual(row.discovery.steps[0].operation,{action:'reverse',operand:'rune-order',within:'row'});
const rowFound=parity(row);
assert(rowFound.some(doc=>doc.id==='lp2-row-column-routes'),'The row-opening route test remains relevant');
assert(rowFound.some(doc=>doc.id==='lp2-row-column-english'),'The whole-page English-score follow-up is discoverable with the same row operation');
assert.deepEqual(S.classify(fullDocs,row.query,row.pages,row.discovery).tests.map(hit=>hit.document.id),ids(rowFound),'Visible tests and Worker evidence use the same structured candidates');
const oversized=fullDocs.map(doc=>doc.id===rowFound[0].id?{...doc,searchText:doc.searchText||doc.text,text:doc.text+'x'.repeat(9001)}:doc);
assert.deepEqual(select(row,oversized),[],'An oversized strongest complete source must refuse comparison rather than substitute a weaker lead');

const words=prepare(card('within_words'));
assert.deepEqual(words.discovery.steps[0].operation,{action:'reverse',operand:'rune-order',within:'word'});
assert.equal(parity(words)[0]?.id,'lp2-word-reversal','Within-word rune reversal must lead ahead of reversing word order');

const blocks=prepare(card('word_blocks'));
assert.deepEqual(blocks.discovery.steps[0].operation,{action:'reverse',operand:'word-order',within:'row'});
const blockFound=parity(blocks);
assert.equal(blockFound[0]?.id,'lp2-word-order-reversal');
assert.match(JSON.parse(blockFound[0].text).scope.procedure,/complete page/i,'Related page-wide record keeps its different extent visible');
assert.equal(blocks.request.card.rules.boundaryMode.value,'word_blocks');
assert.equal(blocks.request.card.scope.value.description,scope.description,'A related page-wide record cannot expand the requested two-row scope');

const compound=prepare(card('fixed_spaces',[{id:'described_method',label:'Apply Vigenere with key ABC',key:'ABC'}]));
assert.equal(compound.discovery.steps.length,2);
assert.deepEqual(compound.discovery.steps[0].operation,{action:'reverse',operand:'rune-order',within:'row'});
assert.match(compound.discovery.steps[1].query,/Vigenere/i);assert.match(compound.discovery.steps[1].query,/ABC/);
const combined=parity(compound);
assert(combined.some(doc=>doc.id==='lp2-row-column-routes'),'The first compound step must not disappear behind its later cipher');
assert(combined.some(doc=>doc.id!=='lp2-row-column-routes'&&/vigen[eè]re/i.test(doc.title+' '+doc.text)),'A later cipher lead is included before extra row-only siblings when budget permits');
assert(!combined.some(doc=>doc.id==='lp2-row-column-english'),'A second row-only record must not consume the compound second-step slot');
assert.deepEqual(compound.request.card.method.value.operations.map(op=>op.id),['reverse_row_runes','described_method']);

// Raw query users retain the existing lexical behavior. Unsupported, malformed
// or empty metadata cannot manufacture operation applicability.
const raw='Reverse the runes inside each word keeping word order unchanged';
const lexical=S.select(fullDocs,raw,scope.pages);
for(const bad of [undefined,null,{},[],{steps:[]},{steps:'reverse'},{steps:[{query:raw,operation:{action:'decrypt',operand:'everything',within:'anywhere'}}]}])
 assert.deepEqual(S.select(fullDocs,raw,scope.pages,bad),lexical,'Malformed/absent hints must fall back without guessed semantics');
const malformed=fullDocs.map(doc=>({...doc,discovery:{operations:'not an operation list'}}));
assert.deepEqual(ids(S.select(malformed,row.query,row.pages,row.discovery)),ids(S.select(malformed,row.query,row.pages)),'Malformed record discovery cannot activate structured candidate selection');
const unknown=C.confirm(C.createDraft({source:{text:'Reverse things in some custom way'},method:f({operations:[{id:'described_method',label:'Reverse things in some custom way'}]})}),{id:'opaque',at:'2026-10-24'});
assert(!R.prepare(unknown).discovery.steps[0].operation,'Opaque positive wording cannot acquire a canonical operation from a keyword');
for(const label of ['Do not reverse each row','Reverse each row only if the supplied check passes','Reverse each row then apply another unspecified operation']){
 const negative=C.confirm(C.createDraft({source:{text:label},method:f({operations:[{id:'reverse_row_runes',label}]})}),{id:'unsafe-canonical',at:'2026-10-24'});
 assert(!R.prepare(negative).discovery.steps[0].operation,'A canonical ID cannot override negative, conditional or compound active wording: '+label);
}
console.log('PASS canonical discovery: operand distinctions, row English follow-up, ordered compound leads, exact scope/limits, full/compact/browser parity, no external overrides and malformed fallback. No coverage or novelty verdicts.');
