'use strict';
const assert=require('node:assert/strict');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const text='Reverse the gematria prime table (F=109, U=107 ...) and sum the words';
(async()=>{
 const {planCard}=await import('../services/idea-assistant/prepare-task.mjs');
 const fs=require('node:fs'),S=require('../assistant-search.js'),R=require('../claim-research.js'),E=require('../local-experiment.js'),alphabet=JSON.parse(fs.readFileSync(require.resolve('../data/local-run-inputs.json'),'utf8')).alphabet;
 const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8')).records;
 let leadDraft=I.initialDraft(text);leadDraft=I.answerIntake(leadDraft,'aim','measure');leadDraft=I.answerIntake(leadDraft,'scope','specific','LP2-15');leadDraft=I.answerIntake(leadDraft,'word-sum-boundaries','hyphen-period');
 const leadSpec=C.confirm(leadDraft,{id:'lead-preview',at:'2026-10-24T00:00:00Z'}),discovery=R.prepare(leadSpec).discovery;
 for(const id of ['obscura-sum-collision-control','lp2-row-prime-sums']){
  const record=registry.find(r=>r.id===id),doc=S.experimentDocs([record])[0],html=I.sourceHTML(doc,registry,{preview:true,discovery});
  assert.match(html,/Uses the usual prime values; your idea reverses them/);
  if(id==='lp2-row-prime-sums')assert.match(html,/It sums rows rather than words/);
  assert(html.includes(record.reader_finding||record.finding),'Differences cannot replace actual findings');
  const processRecord={...record,reader_limit:'A selected word list. Computational review; human review pending.'};assert.doesNotMatch(I.sourceHTML(doc,[processRecord],{preview:true,discovery}),/Computational review|human review pending/i);assert.match(I.sourceHTML(doc,[processRecord],{preview:true,discovery}),/A selected word list/);
  assert.doesNotMatch(I.sourceHTML(doc,registry,{preview:true}),/your idea reverses/,'No invented comparison without explicit target');
  const invalid={...record,discovery:{operations:[{action:'sum',operand:'prime-values',within:'word',table:'canonical',guess:true}]}};
  assert.doesNotMatch(I.sourceHTML(doc,[invalid],{preview:true,discovery}),/your idea reverses/,'Malformed metadata must not create a claimed difference');
 }

 for(const route of ['ask','interpret','proposals','ideas']){
  assert(I.validServiceEndpoint('http://127.0.0.1:8765/'+route,route,'http://127.0.0.1:8765/investigate.html'));
  assert(I.validServiceEndpoint('https://worker.example/'+route,route,'https://jelliottdev.github.io/investigate.html'));
  for(const page of ['https://jelliottdev.github.io/investigate.html','http://localhost:8765/investigate.html','http://127.0.0.1:8766/investigate.html','http://evil.example/investigate.html'])assert(!I.validServiceEndpoint('http://127.0.0.1:8765/'+route,route,page));
  for(const suffix of ['?q=1','#fragment','/extra'])assert(!I.validServiceEndpoint('http://127.0.0.1:8765/'+route+suffix,route,'http://127.0.0.1:8765/investigate.html'));
 }

 for(const table of ['canonical','reversed'])for(const outcome of Object.keys(C.OUTCOMES))for(const boundaries of ['hyphen-period','non-rune']){
  const source=table==='canonical'?'Sum the usual GP prime values within each word':text;let d=I.initialDraft(source);assert.equal(I.intakeQuestions(d)[0].id,'aim');
  d=I.answerIntake(d,'aim',outcome);assert.equal(I.intakeQuestions(d)[0].id,'scope');
  d=I.answerIntake(d,'scope','specific','LP2-15, LP2-17');
  if(outcome==='decipher'){const evaluation=I.intakeQuestions(d)[0];assert.equal(evaluation.id,'word-sum-evaluation');assert.match(evaluation.context,/does not test readable text/);assert.equal(d.rules.evaluation.status,'unspecified');d=I.answerIntake(d,evaluation.id,'numeric-ledger');assert.equal(d.rules.evaluation.status,'unspecified','Boundary is still unspecified; no criterion is manufactured yet');}
  const q=I.intakeQuestions(d)[0];assert.equal(q.id,'word-sum-boundaries');assert.match(q.context,/raw rune text/);assert.match(q.context,/does not decode/);
  d=I.answerIntake(d,q.id,boundaries);assert.equal(I.intakeQuestions(d).length,0);
  const confirmed=C.confirm(d,{id:'numeric-intake-test',at:'2026-10-24T00:00:00Z'}),card=H.cardData(confirmed),plan=planCard(card);
  assert.equal(plan.reason,undefined);assert.deepEqual(plan.steps,[]);assert.deepEqual(plan.pages,['lp2-15','lp2-17']);assert.deepEqual(plan.criterion,{kind:'word-prime-sums',table,boundaries});
  const synthetic=await E.prepare({title:'Word-sum intake software control',pages:[{id:'lp2-15',text:alphabet[0].rune+' / '+alphabet[1].rune+'-'+alphabet[28].rune}],alphabet,steps:plan.steps,criterion:plan.criterion}),output=await E.verify(synthetic,E.run(synthetic));assert.deepEqual(output.wordSums.pages[0].words.map(word=>word.sum),table==='reversed'?(boundaries==='non-rune'?[109,107,2]:[216,2]):(boundaries==='non-rune'?[2,3,109]:[5,109]));assert.deepEqual(output.matches,[],'Numeric word sums must not become a prefix or decryption success');assert(!Object.hasOwn(output,'readable'));
  assert.equal(C.normalizeOutcome(confirmed.aim).id,outcome);assert.equal(confirmed.source.text,source);assert.equal(plan.inputVersion,'raw');const html=I.rowsHTML(confirmed);assert.match(html,/Archived rune text/);assert.match(html,/29-rune GP alphabet/);assert.match(html,/Keep original separators/);assert.doesNotMatch(html,/&quot;kind&quot;/);
 }
 let undecided=I.initialDraft(text);undecided=I.answerIntake(undecided,'aim','undecided');undecided=I.answerIntake(undecided,'scope','undecided');assert.equal(I.intakeQuestions(undecided).length,0);assert.equal(undecided.method.value.operations[0].id,'described_method');
 let original=I.initialDraft(text);original=I.answerIntake(original,'aim','measure');original=I.answerIntake(original,'scope','unsolved-lp2');original=I.answerIntake(original,'word-sum-boundaries','as-described');assert.equal(I.intakeQuestions(original).length,0);assert.equal(original.method.value.operations[0].id,'described_method');assert.equal(original.rules.evaluation.status,'unspecified');
 let decipher=I.initialDraft(text);decipher=I.answerIntake(decipher,'aim','decipher');decipher=I.answerIntake(decipher,'scope','specific','LP2-15');const preservedMethod=C.serialize(decipher.method);assert.throws(()=>I.answerIntake(decipher,'word-sum-boundaries','non-rune'));decipher=I.answerIntake(decipher,'word-sum-evaluation','as-described');assert.equal(C.serialize(decipher.method),preservedMethod);assert.equal(decipher.rules.evaluation.status,'unspecified');assert.equal(I.intakeQuestions(decipher)[0].id,'evaluation');decipher=I.answerIntake(decipher,'evaluation','readable-text');assert.equal(planCard(H.cardData(C.confirm(decipher,{id:'keep-readable',at:'2026-10-25T00:00:00Z'}))).field,'evaluation');assert.deepEqual(decipher.rules.evaluation.value,{kind:'readability'});
 console.log('PASS word-sum intake flow:20 table/outcome/boundary combinations reach exact deterministic compiler; original wording, page holes and goal retained; undecided/original remain unresolved, never silently specialized.');
})().catch(error=>{console.error(error);process.exitCode=1;});
