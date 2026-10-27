'use strict';
/* Tab-local draft restoration only: no preparation, publication or target runs. */
const assert=require('node:assert/strict'),fs=require('node:fs'),{createRequire}=require('node:module');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const file=require.resolve('./test_saved_idea_refinement_ui.cjs'),source=fs.readFileSync(file,'utf8'),shared={exports:{}};
new Function('require','module','exports',source.slice(0,source.indexOf('let groups=0;'))+'\nmodule.exports={legacy,makeDocument};')(createRequire(file),shared,shared.exports);
const {legacy,makeDocument}=shared.exports,value=legacy(),fragment='#idea='+Buffer.from(JSON.stringify(value)).toString('base64url'),entry=JSON.stringify({search:'?refine=1',fragment}),at=Date.parse('2026-10-27T12:00:00.000Z'),copy=structuredClone;
const saved=draft=>({version:1,entry,at,raw:draft.source.text,stage:'review',draft,editing:false,baseline:null,overlay:{}});
function roundtrip(draft){const restored=I.readRecovery(JSON.stringify(saved(draft)),entry,at);assert(restored,'A valid refinement must survive reload');assert.equal(C.serialize(restored.draft),C.serialize(draft));return restored.draft;}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
await test('every keep change and research-first decision survives a question-scoped reload unchanged',()=>{
 let draft=roundtrip(I.refinementDraft(fragment));
 assert.equal(draft.clarifications.find(answer=>answer.question==='saved-refinement').revision,draft.revision);
 const answer=(choice,text='')=>{const question=I.intakeQuestions(draft)[0];assert(question);draft=roundtrip(I.answerIntake(draft,question.id,choice,text));};
 answer('background');answer('keep-saved');answer('family:transposition');answer('reverse-word');answer('specific','LP2-00–02');
 assert.equal(I.intakeQuestions(draft)[0].id,'evaluation');answer('research-first');
 assert.equal(draft.rules.evaluation.status,'unspecified');assert.equal(I.intakeQuestions(draft).length,0);
 assert.deepEqual(draft.scope.value.pages,['lp2-00','lp2-01','lp2-02']);
 const incomplete=H.cardData(C.confirm(draft,{id:'explicit-research-only',at:'2026-10-27T12:00:00.000Z'}));
 assert.equal(incomplete.rules.evaluation.status,'unspecified');assert(!C.serialize(incomplete).includes('inheritedSuggestions'));
 draft=roundtrip(C.revise(draft,{}));assert.equal(I.intakeQuestions(draft)[0].id,'evaluation');answer('keep-saved');
 assert.equal(draft.rules.evaluation.value,'measurement');
 assert.equal(I.readRecovery(JSON.stringify(saved(draft)),entry+'different-question',at),null);
});
await test('changed author aim scope and evaluation choices remain exact across reload without canonical metadata leakage',()=>{
 let draft=roundtrip(I.refinementDraft(fragment));
 const answer=(choice,text='')=>{draft=roundtrip(I.answerIntake(draft,I.intakeQuestions(draft)[0].id,choice,text));};
 answer('background');answer('measure');answer('family:transposition');answer('reverse-word');answer('keep-saved');answer('warning-opening');
 const before=C.serialize(draft),card=H.cardData(C.confirm(draft,{id:'explicit-changes',at:'2026-10-27T12:00:00.000Z'}));
 assert.equal(card.outcome.value.outcomeId,'measure');assert.equal(card.scope.value.pages.length,56);
 assert.deepEqual(card.rules.evaluation.value,C.EVALUATION_CHOICES.find(choice=>choice.id==='warning-opening').value);
 assert(!C.serialize(card).includes('inheritedSuggestions'));assert(!C.serialize(card).includes('previousSuggestion'));assert.equal(C.serialize(roundtrip(draft)),before);
});
await test('malformed nested suggestions and altered prior-answer metadata are rejected before mounting',()=>{
 const draft=I.refinementDraft(fragment);
 for(const mutate of [m=>delete m.revision,m=>m.extra=true,m=>m.method='not-json',m=>m.inheritedSuggestions={unknown:{}},m=>m.inheritedSuggestions={},
  m=>m.inheritedSuggestions.aim.value=null,m=>m.inheritedSuggestions.aim.extra=true,m=>m.inheritedSuggestions.scope.value.pages=['lp2-99'],
  m=>m.inheritedSuggestions.scope.value=['not-a-scope'],m=>m.inheritedSuggestions.evaluation.status='unspecified',
  m=>m.inheritedSuggestions.evaluation.provenance.kind='invented',m=>m.inheritedSuggestions.aim.value.detail='x'.repeat(50000)]){
  const bad=copy(draft);mutate(bad.clarifications.find(answer=>answer.question==='saved-refinement'));
  assert.equal(I.readRecovery(JSON.stringify(saved(bad)),entry,at),null);
 }
 let accepted=I.answerIntake(draft,I.intakeQuestions(draft)[0].id,'background');accepted=I.answerIntake(accepted,'aim','keep-saved');
 for(const mutate of [a=>a.previousSuggestion.value=null,a=>a.choice='undecided',a=>a.question='scope']){
  const bad=copy(accepted);mutate(bad.clarifications.find(answer=>answer.previousSuggestion));assert.equal(I.readRecovery(JSON.stringify(saved(bad)),entry,at),null);
 }
 assert.equal(C.serialize(value),C.serialize(legacy()),'The saved original never changes');
});
await test('corrupt tab storage falls back to the original source-note review with no requests that write or prepare',async()=>{
 const draft=I.refinementDraft(fragment);draft.clarifications.find(answer=>answer.question==='saved-refinement').inheritedSuggestions.aim.value=null;
 const doc=makeDocument(),calls=[];doc.defaultView.location.search='?refine=1';doc.defaultView.location.hash=fragment;
 doc.defaultView.sessionStorage={getItem:key=>key==='liberpedia-idea-draft-v1'?JSON.stringify(saved(draft)):null,setItem(){},removeItem(){}};
 const app=I.createApp(doc,{now:()=>new Date(at).toISOString(),fetcher:async(url,options={})=>{calls.push({url,options});assert.notEqual(options.method,'POST');if(url==='data/experiments.json')return Response.json({records:[]});if(url==='data/assistant-index.json')return Response.json({documents:[]});return Response.json({});}});
 try{await app.ready;const current=app.getSnapshot().draft;assert(current);assert.equal(current.source.text,draft.source.text);assert(I.intakeQuestions(current)[0].id.startsWith('source-note:'));assert.equal(current.aim.status,'unspecified');assert(doc.getElementById('investigate').innerHTML.includes('How should this part of your wording be used?'));assert.equal(calls.filter(call=>call.options.method==='POST').length,0);}finally{app.destroy();}
});
console.log(groups+' saved-refinement recovery groups passed; no saved-card changes or write requests.');
})().catch(error=>{console.error(error);process.exitCode=1;});
