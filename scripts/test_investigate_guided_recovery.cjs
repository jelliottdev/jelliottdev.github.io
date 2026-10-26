'use strict';
// Actual production controller with the shared DOM lifecycle fixture. No live AI or public writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),I=require('../investigate.js');
const harness=fs.readFileSync(require.resolve('./test_investigate_intake_focus.cjs'),'utf8');
const {makeDocument}=new Function('require',harness.slice(0,harness.indexOf('async function fixture()'))+'\nreturn {makeDocument};')(require);
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function fixture(reply){
 const doc=makeDocument();doc.defaultView.location.hash='';const calls=[],timers=[];
 const app=I.createApp(doc,{schedule:(fn,ms)=>{const timer={fn,ms};timers.push(timer);return timer;},unschedule:timer=>{timer.cancelled=true;},fetcher:async(url,options={})=>{
  calls.push({url,options});
  if(url==='data/experiments.json')return Response.json({experiments:[]});
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  if(url==='data/assistant.json')return Response.json({interpretationEndpoint:'https://mock.example/interpret',endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals'});
  if(url==='https://mock.example/interpret')return reply(options);
  throw Error('Unexpected endpoint '+url);
 }});await app.ready;
 const input=text=>{doc.getElementById('idea').value=text;doc.getElementById('idea').fire('input');};
 const submit=async text=>{input(text);doc.getElementById('intake').fire('submit');await turn();await turn();};
 const noWrites=()=>assert.deepEqual(calls.filter(c=>c.options.method==='POST').map(c=>c.url).filter(url=>!url.endsWith('/interpret')),[]);
 return {doc,app,calls,timers,input,submit,noWrites};
}
(async()=>{
 const original='Cumulative autokey';
 for(const [name,status,body]of [['unavailable',503,{reason:'unavailable'}],['timeout',503,{reason:'timeout'}],['invalid',503,{reason:'invalid-interpretation'}],['rate-limit',429,{reason:'rate-limit'}],['mismatched',200,{sourceBinding:'0'.repeat(64),candidate:{malicious:'discard this candidate'}}]]){
  const f=await fixture(()=>Response.json(body,{status}));try{
   assert(f.doc.getElementById('guided-clarification').hidden);await f.submit(original);
   assert.equal(f.app.getSnapshot().stage,'input',name);assert.equal(f.doc.getElementById('idea').value,original);assert.equal(f.doc.getElementById('guided-clarification').hidden,false);assert(f.doc.getElementById('interpretation-error').textContent);
   assert.equal(f.app.getSnapshot().draft,null);f.noWrites();f.doc.getElementById('guided-clarification').fire('click');
   const snapshot=f.app.getSnapshot();assert.equal(snapshot.stage,'review');assert.equal(snapshot.draft.source.text,original);assert.equal(snapshot.draft.method.value.operations[0].id,'described_method');assert.equal(snapshot.draft.method.value.operations[0].sourceText,original);assert.equal(snapshot.draft.aim.status,'unspecified');assert.equal(snapshot.draft.scope.status,'unspecified');assert.equal(snapshot.confirmed,null);assert.equal(snapshot.draft.rules.evaluation.status,'unspecified');assert(!JSON.stringify(snapshot.draft).includes('malicious'));f.noWrites();
   f.doc.selectedChoice='decipher';f.doc.getElementById('clarification').fire('submit');f.doc.selectedChoice='unsolved-lp2';f.doc.getElementById('clarification').fire('submit');
   assert.equal(f.app.getSnapshot().confirmed,null);f.noWrites();
  }finally{f.app.destroy();}
 }
 console.log('PASS unavailable, timeout, invalid, rate-limit and mismatched candidates stay inline; explicit recovery preserves wording and only asks questions');
 for(const text of ['Reverse the prime values in rows','Reverse the prime values of each row on LP2-15']){
  const f=await fixture(()=>{throw Error('No AI request expected');});try{await f.submit(text);const d=f.app.getSnapshot().draft;assert.equal(f.app.getSnapshot().stage,'review');assert.equal(d.method.value.operations[0].id,'ambiguous_reversal');assert(f.doc.host.innerHTML.includes('What should be reversed?'));if(text.includes('LP2-15'))assert.deepEqual(d.scope.value.pages,['lp2-15']);assert(!f.calls.some(c=>c.options.method==='POST'));}finally{f.app.destroy();}
 }
 for(const text of ['Reverse prime values in rows only on LP2-15','Reverse prime values in rows then subtract a key','Do not reverse prime values in rows','Reverse prime values in rows\nthen sum words']){
  const f=await fixture(()=>Response.json({reason:'invalid-interpretation'},{status:503}));try{await f.submit(text);assert.equal(f.app.getSnapshot().stage,'input',text);assert.equal(f.calls.filter(c=>c.url.endsWith('/interpret')).length,1);}finally{f.app.destroy();}
 }
 console.log('PASS exact scoped reversal reaches existing ambiguity; conditions, negations, newlines and additional steps never bypass interpretation');
 {
  let resolve;const f=await fixture(()=>new Promise(r=>{resolve=r;}));try{await f.submit(original);f.input('Another original idea');resolve(Response.json({reason:'invalid-interpretation'},{status:503}));await turn();assert.equal(f.doc.getElementById('guided-clarification').hidden,true);assert.equal(f.doc.getElementById('interpretation-error').textContent,'');assert.equal(f.app.getSnapshot().stage,'input');f.noWrites();}finally{f.app.destroy();}
 }
 {
  const f=await fixture(()=>Response.json({reason:'unavailable'},{status:503}));try{await f.submit(original);const stale=f.doc.getElementById('guided-clarification');f.input('Changed text');stale.fire('click');assert.equal(f.app.getSnapshot().stage,'input');assert.equal(stale.hidden,true);f.noWrites();}finally{f.app.destroy();}
 }
 {
  const f=await fixture(options=>new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(Object.assign(Error('Aborted'),{name:'AbortError'})))));try{await f.submit(original);const timer=f.timers.find(t=>t.ms===30000&&!t.cancelled);assert(timer);timer.fn();await turn();assert.equal(f.doc.getElementById('guided-clarification').hidden,false);f.noWrites();}finally{f.app.destroy();}
 }
 console.log('PASS edit/cancellation and stale responses cannot revive recovery; actual request abort offers guided clarification without writes');
 {
  const P=require('../claim-interpretation.js'),f=await fixture(async options=>{const text=JSON.parse(options.body).text;return Response.json({sourceBinding:Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex'),candidate:{schema:P.SCHEMA,outcome:null,steps:[],scope:null,rules:{}}});});
  try{await f.submit(original);await require('./mock_interpretation_response.cjs').waitForReview(f.app);const d=f.app.getSnapshot().draft;assert.equal(d.source.text,original);assert.equal(d.method.status,'unspecified');assert(I.intakeQuestions(d).some(q=>q.id==='method'));assert.equal(d.aim.status,'unspecified');assert.equal(d.scope.status,'unspecified');assert.equal(f.app.getSnapshot().confirmed,null);f.noWrites();}finally{f.app.destroy();}
 }
 {
  let count=0,resolve;const f=await fixture(()=>++count===1?Response.json({reason:'unavailable'},{status:503}):new Promise(r=>{resolve=r;}));try{await f.submit(original);const stale=f.doc.getElementById('guided-clarification');f.doc.getElementById('intake').fire('submit');await turn();assert(stale.hidden);stale.fire('click');assert.equal(f.app.getSnapshot().stage,'input');assert(f.app.getSnapshot().interpreting);resolve(Response.json({reason:'unavailable'},{status:503}));await turn();assert.equal(stale.hidden,false);f.noWrites();}finally{f.app.destroy();}
 }
 console.log('PASS valid empty interpretation retains original wording and asks for a method; retry hides recovery until its own failure');

})().catch(error=>{console.error(error);process.exitCode=1;});
