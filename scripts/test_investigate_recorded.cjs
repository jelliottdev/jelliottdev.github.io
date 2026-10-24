'use strict';
// Exact published evidence through real validation/rendering, without inference.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),R=require('../claim-research.js'),D=require('../recorded-comparison.js'),S=require('../assistant-search.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const documents=S.experimentDocs(registry.records),known=value=>C.field('specified',value),at='2026-10-24T12:00:00Z';
const snapshot=C.confirm(C.createDraft({source:{text:'Reverse each row on LP2-15'},aim:known('Find readable text'),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows',sourceText:'Reverse each row on LP2-15'}]}),scope:known({pages:['lp2-15']})}),{id:'recorded-ui',at});
const reply=D.compare({snapshot:R.prepare(snapshot).snapshot,documents});assert(reply,'Current published registry needs reviewed execution metadata');
const checked=I.validateAnswer(reply,documents,snapshot);assert.equal(checked.kind,'recorded-overlap');assert.equal(checked.answer,reply.answer);
for(const changed of [{...reply,answer:reply.answer.replace('LP2-15','all LP2 pages')},{...reply,kind:'proved'}, {...reply,sources:[...reply.sources].reverse()}, {...reply,sources:reply.sources.map((s,i)=>i? s:{...s,text:s.text+' '})}])assert.throws(()=>I.validateAnswer(changed,documents,snapshot));
for(const metadata of [undefined,{...reply.sources[0].recordedComparison,executed_pages:['lp2-56']}])assert.throws(()=>I.validateAnswer({...reply,sources:reply.sources.map((s,i)=>i?s:{...s,recordedComparison:metadata})},documents,snapshot));
const differentlyScoped=C.confirm(C.revise(snapshot,{scope:known({pages:['lp2-56']})}),{id:'different',at});assert.throws(()=>I.validateAnswer(reply,documents,differentlyScoped));
assert.throws(()=>I.validateAnswer(reply,documents));
function packetFor(kind,answer=reply.answer){return C.packetSnapshot(snapshot,C.bindResearch(snapshot,{id:'comparison',at,evidence:{snapshotId:'local-published-fixture',records:registry.records.filter(r=>reply.sources.some(s=>s.id===r.id)),documents:reply.sources,...(kind?{comparisonKind:kind}:{})},answer}));}
const html=I.packetHTML(packetFor('recorded-overlap'));
assert(!html.includes('AI interpretation'));assert(html.includes('How this relates to your idea'));
assert(html.indexOf('Recorded findings')<html.indexOf('How this relates to your idea'));
for(const source of reply.sources){const evidence=JSON.parse(source.text);assert(html.includes(evidence.reader_finding||evidence.finding),'Authored findings remain visible before the direct comparison');}
assert(I.packetHTML(packetFor(undefined)).includes('AI interpretation'),'Ordinary generated answers keep their attribution');
assert(I.packetHTML(packetFor('recorded-overlap','A changed assertion [1].')).includes('AI interpretation'),'A claimed direct kind alone cannot hide attribution');
// Transport removes redundant source provenance; both sides compare the exact card sent.
const provenanceDraft=C.revise(snapshot,{method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows',sourceText:'Original paraphrase retained as provenance.'}]})});
const provenanceSnapshot=C.confirm(provenanceDraft,{id:'provenance',at});
assert.equal(I.validateAnswer(reply,documents,provenanceSnapshot).answer,reply.answer);
// Boot order matters: the browser must have the shared pure comparator before UI use.
const entry=fs.readFileSync(require.resolve('../investigate.html'),'utf8');
assert(entry.indexOf('recorded-comparison.js')>entry.indexOf('claim-specification.js'));
assert(entry.indexOf('recorded-comparison.js')<entry.indexOf('src="investigate.js'));
console.log('PASS direct comparison UI: exact evidence/card/source order, tamper rejection, visible authored findings, print attribution, transport parity and browser dependency order.');
