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
// Direct numeric operations use exact maintained metadata, never generic rule boilerplate.
const numericIds=['lp2-row-prime-sums','mixed-square-word-sums','obscura-sum-collision-control'];
const numericMetadata=new Map(numericIds.map(id=>[id,JSON.parse(fs.readFileSync(path.join(root,'experiments/records',id,'record.json'),'utf8')).discovery]));
for(const [id,d]of numericMetadata){assert(d?.operations.some(op=>op.action==='sum'&&op.operand==='prime-values'),id);assert(d.evaluation.includes('numeric-sums'));}
// Read current canonical metadata without regenerating any public artifact.
const withNumeric=records=>records.map(record=>numericMetadata.has(record.id)?{...record,discovery:numericMetadata.get(record.id)}:record);
const numericFull=S.experimentDocs(withNumeric(full.records)),numericCompact=S.experimentDocs(withNumeric(compact.records));
function sumsCard(table='reversed',tail=[],patch={}){
 const operations=[{id:'word_prime_sums',label:'Word prime sums',table,boundaries:'hyphen-period',...patch},...tail];
 return C.confirm(C.createDraft({source:{text:'Reverse the GP prime assignments and sum words'},aim:f({outcomeId:'measure',detail:'Inspect numerical structure'}),
  method:f({operations}),scope:f(scope),rules:{representation:f('GP29'),wordBoundaries:f('preserve'),inputVersion:f('raw'),unmapped:f('preserve'),
   evaluation:f({kind:'word-prime-sums',table,boundaries:'hyphen-period'})}}),{id:'numeric-discovery',at:'2026-10-24'});
}
const sums=prepare(sumsCard());
assert.deepEqual(sums.discovery.steps[0].operation,{action:'sum',operand:'prime-values',within:'word',table:'reversed'});
assert.match(sums.query,/Sum GP prime values within each word using the reversed prime table/);
for(const noise of ['hyphen-period','wordBoundaries','boundaryMode','evaluation','reset','unmapped'])assert(!sums.query.includes(noise),'Ranking uses readable method terms, not rule vocabulary: '+noise);
assert(sums.confirmedQuery.includes('hyphen-period'),'Exact constraints remain in comparison evidence');
const numericFound=S.select(numericFull,sums.query,sums.pages,sums.discovery);
assert(numericFound.length>0);assert(numericFound.filter(d=>d.kind==='experiment').every(d=>['mixed-square-word-sums','obscura-sum-collision-control'].includes(d.id)),'Word sums lead ahead of row sums or unrelated clocks');
assert.deepEqual(S.select(numericCompact,sums.query,sums.pages,sums.discovery),numericFound,'Current full/compact evidence has identical numeric retrieval');
assert.equal(JSON.stringify(browser.AssistantSearch.select(numericFull,sums.query,sums.pages,sums.discovery)),JSON.stringify(numericFound));
for(const doc of numericFound)assert.equal(doc.text,numericFull.find(d=>d.id===doc.id).text,'Canonical evidence retains actual table, targets and limitations for a reversed-table lead');
const researchBrowser={TextEncoder,TextDecoder,btoa,atob};for(const name of ['claim-specification.js','claim-share.js','claim-research.js'])vm.runInNewContext(fs.readFileSync(path.join(root,name),'utf8'),researchBrowser);
researchBrowser.requestJSON=JSON.stringify(sums.request);assert.equal(vm.runInNewContext('JSON.stringify(ClaimResearch.validate(JSON.parse(requestJSON)))',researchBrowser),JSON.stringify(R.validate(sums.request)),'Browser and Worker derive the same immutable numeric request and hints');
const exactWord={...numericFound[0],id:'synthetic-reversed-word',title:'Reversed word prime sums',discovery:{operations:[{action:'sum',operand:'prime-values',within:'word',table:'reversed'}],evaluation:['numeric-sums']}};
const exactRow={...exactWord,id:'synthetic-reversed-row',discovery:{operations:[{action:'sum',operand:'prime-values',within:'row',table:'reversed'}],evaluation:['numeric-sums']}};
assert.equal(S.select([...numericFull,exactWord],sums.query,sums.pages,sums.discovery)[0].id,exactWord.id,'Exact table wins at the preferred extent');
assert(!S.select([...numericFull,exactRow],sums.query,sums.pages,sums.discovery).some(d=>d.id===exactRow.id),'Word extent takes priority over an exact-table row record');
const huge={...exactWord,text:exactWord.text+'x'.repeat(9001)};assert.deepEqual(S.select([...numericFull,huge],sums.query,sums.pages,sums.discovery),[],'Oversized exact leading evidence cannot be replaced by a weaker table or shorter scope');
const sumsCompound=prepare(sumsCard('reversed',[{id:'described_method',label:'Apply Vigenere with key ABC',key:'ABC'}])),sumsCombined=S.select(numericFull,sumsCompound.query,sumsCompound.pages,sumsCompound.discovery);
assert(sumsCombined.some(d=>['mixed-square-word-sums','obscura-sum-collision-control'].includes(d.id)));assert(sumsCombined.some(d=>/vigen[eè]re/i.test(d.title+' '+d.text)),'Compound numeric and cipher steps each retain a lead');
assert(sumsCombined.filter(d=>d.kind==='experiment').reduce((n,d)=>n+d.text.length,0)<=9000);
for(const patch of [{label:'Do not sum words'},{label:'Word prime sums then Atbash'},{label:'Word prime sums only if a match appears'},
 {table:'reverse-digits'},{boundaries:'guess'},{declaredFamilyId:'feedback'},{key:'DOG'}]){
 const prepared=R.prepare(sumsCard('reversed',[],patch));assert(!prepared.discovery.steps[0].operation,'Invalid or qualified numeric operation cannot activate a hint: '+JSON.stringify(patch));
}
for(const change of [d=>d.rules.evaluation=f({kind:'word-prime-sums',table:'canonical',boundaries:'hyphen-period'}),d=>d.rules.representation=f('latin'),d=>d.rules.reset=f('word')]){
 const draft=C.revise(sumsCard(),{});change(draft);const prepared=R.prepare(C.confirm(draft,{id:'conflicting-numeric',at:'2026-10-24'}));assert(!prepared.discovery.steps[0].operation);
}
for(const operation of [{action:'sum',operand:'prime-values',within:'word'},{action:'sum',operand:'prime-values',within:'word',table:'reversed',extra:true},
 {action:'sum',operand:'digits',within:'word',table:'reversed'},{action:'sum',operand:'prime-values',within:'page',table:'reversed'}]){
 const discovery={steps:[{query:raw,operation}]};assert.deepEqual(S.select(numericFull,raw,scope.pages,discovery),S.select(numericFull,raw,scope.pages),'Malformed sum hints retain lexical fallback');
}
console.log('PASS numeric sum discovery: strict positive word/table/boundary semantics, canonical related leads retain actual evidence, extent then table preference, full/compact/browser/Worker parity, compound slots, budget and invalid fallback.');
console.log('PASS canonical discovery: operand distinctions, row English follow-up, ordered compound leads, exact scope/limits, full/compact/browser parity, no external overrides and malformed fallback. No coverage or novelty verdicts.');
