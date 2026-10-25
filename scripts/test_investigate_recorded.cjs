'use strict';
// Exact published evidence through real validation/rendering, without inference.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),R=require('../claim-research.js'),D=require('../recorded-comparison.js'),S=require('../assistant-search.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const documents=S.experimentDocs(registry.records),known=value=>C.field('specified',value),at='2026-10-24T12:00:00Z';
const snapshot=C.confirm(C.createDraft({source:{text:'Reverse each row on LP2-15'},aim:known('Find readable text'),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows',sourceText:'Reverse each row on LP2-15'}]}),scope:known({pages:['lp2-15']})}),{id:'recorded-ui',at});
const reply=D.compare({snapshot:R.prepare(snapshot).snapshot,documents});assert(reply,'Current published registry needs reviewed execution metadata');
const checked=I.validateAnswer(reply,documents,snapshot);assert.equal(checked.kind,'recorded-overlap');assert.equal(checked.answer,reply.answer);
assert(!/LP2-(?:49|50|55)/.test(reply.answer),'A page-15 comparison should not narrate unrelated page exceptions');
for(const changed of [{...reply,answer:reply.answer.replace('LP2-15','all LP2 pages')},{...reply,kind:'proved'}, {...reply,sources:[...reply.sources].reverse()}, {...reply,sources:reply.sources.map((s,i)=>i? s:{...s,text:s.text+' '})}])assert.throws(()=>I.validateAnswer(changed,documents,snapshot));
for(const metadata of [undefined,{...reply.sources[0].recordedComparison,executed_pages:['lp2-56']}])assert.throws(()=>I.validateAnswer({...reply,sources:reply.sources.map((s,i)=>i?s:{...s,recordedComparison:metadata})},documents,snapshot));
const differentlyScoped=C.confirm(C.revise(snapshot,{scope:known({pages:['lp2-56']})}),{id:'different',at});assert.throws(()=>I.validateAnswer(reply,documents,differentlyScoped));
assert.throws(()=>I.validateAnswer(reply,documents));
function packetFor(kind,answer=reply.answer){return C.packetSnapshot(snapshot,C.bindResearch(snapshot,{id:'comparison',at,evidence:{snapshotId:'local-published-fixture',records:registry.records.filter(r=>reply.sources.some(s=>s.id===r.id)),documents:reply.sources,...(kind?{comparisonKind:kind}:{})},answer}));}
const html=I.packetHTML(packetFor('recorded-overlap'));
assert(!html.includes('AI interpretation'));assert(html.includes('How this relates to your idea'));
assert(html.indexOf('What the records found')>=0);assert(html.indexOf('What the records found')<html.indexOf('How this relates to your idea'));
for(const source of reply.sources){const evidence=JSON.parse(source.text);assert(html.includes(evidence.reader_finding||evidence.finding),'Authored findings remain visible before the direct comparison');const limit=evidence.reader_limit||evidence.limitations;assert(limit&&html.replace(/&#39;/g,"'").includes(limit),'Short comparison does not hide the source limitations');}
assert(I.packetHTML(packetFor(undefined)).includes('AI interpretation'),'Ordinary generated answers keep their attribution');
assert(I.packetHTML(packetFor('recorded-overlap','A changed assertion [1].')).includes('AI interpretation'),'A claimed direct kind alone cannot hide attribution');
// Transport removes redundant source provenance; both sides compare the exact card sent.
const provenanceDraft=C.revise(snapshot,{method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows',sourceText:'Original paraphrase retained as provenance.'}]})});
const provenanceSnapshot=C.confirm(provenanceDraft,{id:'provenance',at});
assert.equal(I.validateAnswer(reply,documents,provenanceSnapshot).answer,reply.answer);
// A canonical numeric idea can receive a deterministic related-evidence answer
// without pretending that a prior table/word-boundary choice is equivalent.
const numeric=C.confirm(C.createDraft({source:{text:'Reverse the gematria prime table (F=109, U=107 ...) and sum the words'},aim:known({outcomeId:'measure',detail:'Measure the sums of the words'}),method:known({operations:[{id:'word_prime_sums',label:'Word prime sums',table:'reversed',boundaries:'non-rune'}]}),scope:known({pages:['lp2-15']}),rules:{representation:known('GP29'),inputVersion:known('raw'),evaluation:known({kind:'word-prime-sums',table:'reversed',boundaries:'non-rune'}),unmapped:known('preserve'),wordBoundaries:known('preserve')}}),{id:'numeric-recorded-ui',at});
const numericPrepared=R.prepare(numeric),numericSelected=S.select(documents,numericPrepared.query,numericPrepared.pages,numericPrepared.discovery),numericReply=D.compare({snapshot:numericPrepared.snapshot,documents:numericSelected});
assert(numericReply,'Generated canonical sum records should supply a deterministic numeric relation');assert.equal(numericReply.kind,'recorded-overlap');const numericChecked=I.validateAnswer(numericReply,documents,numeric);assert.equal(numericChecked.answer,numericReply.answer);assert(numericReply.sources.every(s=>documents.some(d=>d.id===s.id)));
const sourceWithOperation=numericReply.sources.find(s=>s.discovery?.operations?.length);assert(sourceWithOperation,'The generated evidence must carry its actual authored table/sum metadata');
for(const mutate of [
 s=>s.discovery.operations[0].table='reversed',
 s=>s.discovery.operations[0].within='invented-boundary',
 s=>s.discovery={operations:[],evaluation:[]},
 s=>delete s.discovery,
 s=>s.text+=' ',
 s=>s.href='#/experiments/unrecognized-source',
]){const altered=structuredClone(numericReply);mutate(altered.sources.find(s=>s.id===sourceWithOperation.id));assert.throws(()=>I.validateAnswer(altered,documents,numeric),'Transport metadata and evidence cannot replace the locally loaded source');}
assert.throws(()=>I.validateAnswer({...numericReply,answer:'The reversed table decrypted LP2-15 [1].'},documents,numeric));assert.throws(()=>I.validateAnswer({...numericReply,kind:'numeric-proof'},documents,numeric));assert.throws(()=>I.validateAnswer(numericReply,documents,snapshot),'A response for another confirmed method cannot inherit deterministic attribution');
const numericPacket=C.packetSnapshot(numeric,C.bindResearch(numeric,{id:'numeric-comparison',at,evidence:{snapshotId:'generated-published-registry',records:registry.records.filter(r=>numericReply.sources.some(s=>s.id===r.id)),documents:numericReply.sources,comparisonKind:'recorded-overlap'},answer:numericReply.answer})),numericHTML=I.packetHTML(numericPacket);
assert(!numericHTML.includes('AI interpretation'));assert(numericHTML.indexOf('What the records found')>=0);assert(numericHTML.indexOf('What the records found')<numericHTML.indexOf('How this relates to your idea'));
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
for(const source of numericReply.sources){const evidence=JSON.parse(source.text);assert(numericHTML.includes(escape(evidence.reader_finding||evidence.finding)),'Actual authored source findings remain visible');const scientificLimit=(evidence.reader_limit||evidence.limitations).split(/\s*Computational review\s*;/i)[0].trim();assert(scientificLimit);assert(numericHTML.includes(escape(scientificLimit)),'Actual scientific limits remain visible; process-review annotations are not substantive evidence');}
// Old reviewed execution records with no discovery annotation remain valid.
const oldDocuments=documents.map(d=>{const copy={...d};delete copy.discovery;return copy;}),oldReply=D.compare({snapshot:R.prepare(snapshot).snapshot,documents:oldDocuments});assert(oldReply);assert.equal(I.validateAnswer(oldReply,oldDocuments,snapshot).answer,oldReply.answer);
// Boot order matters: the browser must have the shared pure comparator before UI use.
const entry=fs.readFileSync(require.resolve('../investigate.html'),'utf8');
assert(entry.indexOf('recorded-comparison.js')>entry.indexOf('claim-specification.js'));
assert(entry.indexOf('recorded-comparison.js')<entry.indexOf('src="investigate.js'));
console.log('PASS direct comparison UI: exact evidence/card/source order, tamper rejection, visible authored findings, print attribution, transport parity and browser dependency order.');
