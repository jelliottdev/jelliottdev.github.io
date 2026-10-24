/* Test-only evidence proposal. Never contacts a provider or bypasses validation. */
const I=require('../investigate.js'),P=require('../claim-interpretation.js'),C=require('../claim-specification.js');
module.exports=async function(options){
 const text=JSON.parse(options.body).text,draft=I.initialDraft(text),scope=draft.scope.status==='specified'?draft.scope.value:null;
 const candidate={schema:P.SCHEMA,outcome:draft.aim.status==='specified'?{id:C.normalizeOutcome(draft.aim.value).id,source:{start:0,quote:text}}:null,
  steps:draft.method.status==='specified'?[{id:'described_method',familyId:null,source:{start:0,quote:text},parameters:{}}]:[],
  scope:scope?.pages?.length?{pages:scope.pages,passage:scope.description||null,source:{start:0,quote:text}}:null,rules:{}};
 P.validateCandidate(text,candidate);
 return Response.json({candidate,sourceBinding:Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex')});
};
module.exports.acknowledge=(doc,app)=>{
 for(let i=0;i<4;i++){
  const question=I.intakeQuestions(app.getSnapshot().draft)[0];if(!question)return;
  if(!question.choices.some(choice=>choice.id==='undecided'))throw Error('Fixture must explicitly answer '+question.id);
  doc.selectedChoice='undecided';for(const radio of doc.querySelectorAll?.('input[name=choice]')||[])radio.checked=radio.value==='undecided';
  doc.getElementById('other-detail').value='';doc.getElementById('clarification').fire('submit');doc.selectedChoice=null;
 }
 throw Error('Fixture did not finish its explicit undecided answers');
};
