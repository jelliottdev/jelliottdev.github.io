'use strict';
// Production intake and provider adapter, with local deferred HTTP fixtures only.
const assert=require('node:assert/strict'),fs=require('node:fs'),I=require('../investigate.js'),P=require('../claim-interpretation.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),F=require('../fixed-plan-compiler.js');
const harness=fs.readFileSync(require.resolve('./test_investigate_intake_focus.cjs'),'utf8');
const {makeDocument}=new Function('require',harness.slice(0,harness.indexOf('async function fixture()'))+'\nreturn {makeDocument};')(require);
const raw='Decrypt LP2 by reversing each row, keeping every F rune unchanged.';
const quote=(text,value)=>({start:text.indexOf(value),quote:value});
function wire(text=raw){return {schema:P.SCHEMA,outcome:{id:'decipher',source:quote(text,text)},steps:[{id:'reverse_row_runes',familyId:'transposition',source:quote(text,'reversing each row')}],scope:null,rules:[]};}
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function until(check,message){const end=Date.now()+5000;while(!check()){assert(Date.now()<end,message);await turn();}}
async function fixture(candidate,binding){
 const doc=makeDocument();doc.defaultView.location.hash='';const calls=[],timers=[];
 const app=I.createApp(doc,{id:()=>crypto.randomUUID(),schedule:(fn,ms)=>{const timer={fn,ms};timers.push(timer);return timer;},unschedule:timer=>{timer.cancelled=true;},fetcher:async(url,options={})=>{
  calls.push({url,options});
  if(url==='data/experiments.json')return Response.json(JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8')));
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  if(url==='data/assistant.json')return Response.json({interpretationEndpoint:'https://mock.example/interpret',endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals'});
  if(url==='https://mock.example/interpret')return Response.json({candidate,sourceBinding:binding});
  assert(['https://mock.example/ask','https://mock.example/proposals'].includes(url),'No live service or execution request is permitted: '+url);
  return new Promise((resolve,reject)=>options.signal?.addEventListener('abort',()=>reject(Object.assign(Error('Aborted'),{name:'AbortError'})),{once:true}));
 }});await app.ready;
 return {doc,app,calls,submit(text=raw){const input=doc.getElementById('idea');input.value=text;input.fire('input');input.focus();input.setSelectionRange(7,12);doc.getElementById('define-test').fire('click');return input;},answer(choice,text=''){doc.selectedChoice=choice;const detail=doc.getElementById('other-detail');if(detail)detail.value=text;doc.getElementById('clarification').fire('submit');doc.selectedChoice=null;},noResearch(){assert(!calls.some(call=>/\/(ask|proposals)$/.test(call.url)));}};
}
(async()=>{
 const Adapter=await import('../services/idea-assistant/interpret-handler.mjs'),candidate=Adapter.fromWire(wire(),raw),binding=await Adapter.sourceBinding(raw);
 {
  const f=await fixture(candidate,binding);try{
   f.submit();await until(()=>!f.app.getSnapshot().interpreting,'Interpretation did not settle');
   const snapshot=f.app.getSnapshot(),d=snapshot.draft;assert.equal(snapshot.stage,'review');assert.equal(d.source.text,raw);assert.equal(d.method.value.operations[0].sourceText,'reversing each row');assert.equal(d.aim.value.detail,raw);
   assert.equal(d.rules.exceptionalCases.status,'specified');assert.match(d.rules.exceptionalCases.value,/keeping every F rune unchanged/,'A broad goal quote cannot launder an omitted method constraint');assert.equal(snapshot.confirmed,null);f.noResearch();
   assert(I.intakeQuestions(d).some(q=>q.id==='scope'));f.answer('specific','LP2-15');assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'evaluation');f.answer('inspect-output');
   const reviewed=f.app.getSnapshot().draft;assert.match(reviewed.rules.exceptionalCases.value,/keeping every F rune unchanged/);assert(f.doc.host.innerHTML.includes('Exceptional cases:'));assert(f.doc.host.innerHTML.includes('keeping every F rune unchanged'),'The retained constraint must be visible at confirmation, not only inside original prose');assert(f.doc.host.innerHTML.includes('<summary>Original idea</summary><pre>'+raw+'</pre>'));assert(f.doc.getElementById('confirm'));assert.equal(f.app.getSnapshot().confirmed,null);f.noResearch();
   f.doc.getElementById('confirm').fire('click');await until(()=>f.calls.some(call=>call.url.endsWith('/ask')),'Explicit confirmation did not compare');const confirmed=f.app.getSnapshot().confirmed;assert(confirmed);assert.equal(confirmed.source.text,raw);assert.match(confirmed.rules.exceptionalCases.value,/keeping every F rune unchanged/);
   const saved=f.calls.find(call=>call.url.endsWith('/proposals'));assert(saved);const body=JSON.parse(saved.options.body),card=H.cardData(C.confirm(H.decode(body.fragment).draft,{id:'retained-review',at:'2026-10-26T12:00:00.000Z'}));assert.match(card.rules.exceptionalCases.value,/keeping every F rune unchanged/);
   const compiled=F.compile(card);assert.match(compiled.reason,/exceptionalCases condition needs an adapter/,'The retained omitted constraint itself must prevent execution as plain row reversal');
  }finally{f.app.destroy();}
 }
 console.log('PASS broad goal evidence cannot hide an omitted constraint in the reviewed, explicitly confirmed or saved idea');
 for(const kind of ['wrong-source-binding','invented-constraint-source']){
  const bad=structuredClone(candidate);if(kind==='invented-constraint-source')bad.steps[0].source={start:raw.indexOf('reversing'),quote:'reversing each row while copying F'};
  const f=await fixture(bad,kind==='wrong-source-binding'?'0'.repeat(64):binding);try{
   const input=f.submit();await until(()=>!f.app.getSnapshot().interpreting,'Rejected response did not settle');assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.app.getSnapshot().draft,null);assert.equal(f.doc.getElementById('idea'),input);assert.equal(input.value,raw);assert.equal(input.selectionStart,7);assert.equal(input.selectionEnd,12);assert.equal(f.doc.activeElement,input);assert(f.doc.getElementById('interpretation-error').textContent);assert.equal(f.doc.getElementById('guided-clarification').hidden,false);assert(!f.doc.getElementById('confirm'));f.noResearch();
   f.doc.getElementById('guided-clarification').fire('click');const recovered=f.app.getSnapshot();assert.equal(recovered.stage,'review');assert.equal(recovered.draft.source.text,raw);assert.equal(recovered.draft.method.value.operations[0].id,'described_method');assert.equal(recovered.draft.method.value.operations[0].sourceText,raw);assert.match(recovered.draft.method.value.operations[0].label,/keeping every F rune unchanged/);assert.equal(recovered.confirmed,null);f.noResearch();
  }finally{f.app.destroy();}
 }
 console.log('PASS wrong bindings and fabricated evidence stay inline with caret preserved; explicit guided recovery retains the full instruction');
 {
  const f=await fixture(candidate,binding);try{f.submit();await until(()=>f.app.getSnapshot().stage==='review','Review not reached');f.doc.getElementById('back').fire('click');assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.doc.getElementById('idea').value,raw);f.noResearch();}finally{f.app.destroy();}
 }
 console.log('PASS returning to edit recovers exact original text without research, save or execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
