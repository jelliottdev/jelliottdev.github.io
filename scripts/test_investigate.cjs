'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const C=require('../claim-specification'),I=require('../investigate'),S=require('../assistant-search');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const docs=S.experimentDocs(registry.records),at='2026-10-24T12:00:00Z';
let count=0;
const test=(name,fn)=>{fn();count++;console.log('PASS '+name);};
test('exact scope lists/ranges preserve holes; invalid shorthand is rejected',()=>{
 assert.deepEqual(I.parseScope('LP2-15, LP2-17').value.pages,['lp2-15','lp2-17']);
 assert.deepEqual(I.parseScope('LP2-15–17').value.pages,['lp2-15','lp2-16','lp2-17']);
 assert.throws(()=>I.parseScope('15–17'));assert.throws(()=>I.parseScope('LP2-99'));
 assert.equal(I.parseScope('').status,'unspecified');
});
test('arbitrary source is retained as editable method wording without an invented goal',()=>{
 const text='Try the odd columns, then my own key rule.';const d=I.initialDraft(text);
 assert.equal(d.source.text,text);assert.equal(d.method.value.operations[0].label,text);
 assert.equal(d.aim.status,'unspecified');assert.equal(d.rules.representation.status,'unspecified');
});
test('only known consequential reversal ambiguity is questioned',()=>{
 let d=I.initialDraft('Reverse the prime values of each row on LP2-15, keeping word boundaries.');
 assert.equal(C.questions(d)[0].id,'operation');
 d=C.clarify(d,'operation','reverse_row_runes');assert.equal(C.questions(d)[0].id,'word-boundary');
 d=C.clarify(d,'word-boundary','fixed_spaces');
 assert.equal(C.questions(d).length,0);assert(C.summary(d).includes('space positions'));
 assert(!C.summary(d).includes('prime values of each row'));
});
test('answer validation binds ID, href AND complete exact source text',()=>{
 const source=docs.find(d=>d.id==='fibonacci-stream-skip-grid');
 const answer={answer:'A bounded result [1].',sources:[source]};
 assert.equal(I.validateAnswer(answer,docs).sources[0],source);
 for(const changed of [{...source,text:source.text+'x'},{...source,href:'javascript:alert(1)'},{...source,id:'unknown'}])assert.throws(()=>I.validateAnswer({...answer,sources:[changed]},docs));
 assert.throws(()=>I.validateAnswer({...answer,answer:'Unsupported [2].'},docs));
 assert.throws(()=>I.validateAnswer({...answer,sources:[source,source]},docs));
});
test('source and answer HTML are escaped and native citations stay local',()=>{
 const s=docs.find(d=>d.id==='fibonacci-stream-skip-grid');
 const c=C.confirm(I.initialDraft('<img src=x onerror=alert(1)>'),{id:'x',at});
 const r=C.bindResearch(c,{id:'r',at,evidence:{snapshotId:'x',records:[registry.records.find(r=>r.id===s.id)],documents:[s]},answer:'<script>unsafe</script> [1].'});
 const html=I.packetHTML(C.packetSnapshot(c,r));
 assert(!html.includes('<script>'));assert(html.includes('&lt;script&gt;'));assert(html.includes('href="index.html#/experiments/fibonacci-stream-skip-grid"'));
 assert(html.includes('&lt;img'));
});
test('compact retrieval avoids unknown-field scaffolding on actual published records',()=>{
 for(const text of ['Fibonacci keys on LP2-15','Test fixed invertible Hill matrix keys in two-rune blocks on LP2-15','Compare word lengths with other languages']){
  const c=C.confirm(I.initialDraft(text),{id:'x',at}),q=C.retrievalQuery(c).query;
  assert(!q.includes('unspecified'));assert(!q.includes('searchProtocol'));
  assert.deepEqual(S.select(docs,q).map(d=>d.id),S.select(docs,text).map(d=>d.id));
 }
});
test('three-page request can omit hint only while full confirmed scope remains explicit',()=>{
 const c=C.confirm(I.initialDraft('Fibonacci keys on LP2-15–17'),{id:'x',at});
 const full=C.queryForResearch(c,{maxLength:6000}),compact=C.retrievalQuery(c);
 assert.equal(full.pages.length,3);assert(full.query.includes('lp2-16'));assert(compact.query.includes('LP2-16'));
 assert.equal(C.queryForResearch(c,{maxLength:20}).query,null);
});
console.log('PASS '+count+' investigate helper/retrieval tests; all research uses actual registry records and no inference.');

// Minimal event-DOM harness: no browser engine, network or UI automation.
class Element{
 constructor(id){this.id=id;this.listeners={};this.disabled=false;this.textContent='';this.value='';this.hidden=false;this.html='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){} remove(){} replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;}get innerHTML(){return this.html;}
 insertAdjacentHTML(where,value){this.html+=value;}
}
function fakeDocument(search=''){
 const host=new Element('investigate'),print=new Element('print-snapshot'),cache=new Map();
 return {defaultView:{location:{search}},activeElement:null,
  getElementById(id){
   if(id==='investigate')return host;if(id==='print-snapshot')return print;
   if(!host.html.includes('id="'+id+'"'))return null;
   if(!cache.has(id))cache.set(id,new Element(id));return cache.get(id);
  },querySelector(selector){if(selector==='.privacy')return null;if(selector.startsWith('#'))return this.getElementById(selector.slice(1));return null;},
  host,print};
}
(async()=>{
 const doc=fakeDocument('?q=Fibonacci%20keys&pages=lp2-15&pages=lp2-17');
 let resolveOptional;const optional=new Promise(resolve=>{resolveOptional=resolve;});
 const app=I.createApp(doc,{fetcher:async url=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask'});
  return optional;
 },now:()=>at,id:()=> 'test-id'});
 assert(doc.host.html.includes('Fibonacci keys'));assert.equal(app.getSnapshot().stage,'input');
 await new Promise(resolve=>setTimeout(resolve,15));
 doc.getElementById('idea').value='Fibonacci keys';doc.getElementById('intake').fire('submit');
 assert.deepEqual(app.getSnapshot().draft.scope.value.pages,['lp2-15','lp2-17']);
 assert.equal(doc.getElementById('confirm').disabled,false,'Optional context cannot stall confirmation');
 doc.getElementById('edit').fire('click');
 const before=doc.host.innerHTML;doc.getElementById('edit-method').value='Unsaved method edit';
 resolveOptional(Response.json({documents:[]}));await new Promise(resolve=>setTimeout(resolve,10));
 assert.equal(doc.host.innerHTML,before);assert.equal(doc.getElementById('edit-method').value,'Unsaved method edit');
 assert.equal(app.getSnapshot().draft.source.text,'Fibonacci keys');
 app.destroy();console.log('PASS mocked event-DOM: legacy prefill/no autosubmit, exact page hints, optional index does not stall or erase editor.');
 const journey=fakeDocument('?q=Fibonacci%20keys%20on%20LP2-15');
 const requests=[],timers=[];let prints=0,serial=0;
 const application=I.createApp(journey,{fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask'});
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  return new Promise(resolve=>requests.push({resolve,options}));
 },now:()=>at,id:()=> 'test-'+(++serial),printer:()=>{prints++;},schedule:fn=>{timers.push(fn);return timers.length-1;},unschedule:()=>{}});
 await new Promise(resolve=>setTimeout(resolve,15));
 journey.getElementById('idea').value='Fibonacci keys on LP2-15';journey.getElementById('intake').fire('submit');
 journey.getElementById('confirm').fire('click');
 assert.equal(requests.length,1);assert.equal(application.getSnapshot().busy,true);
 const sent=JSON.parse(requests[0].options.body);
 assert.equal(sent.query,'Fibonacci keys on LP2-15. LP2-15');assert(sent.confirmedQuery.includes('Original wording'));assert.deepEqual(sent.pages,['lp2-15']);
 const evidence=docs.find(d=>d.id==='fibonacci-stream-skip-grid');
 const reply=()=>Response.json({answer:'The published Fibonacci stream test is bounded [1].',sources:[evidence]});
 requests[0].resolve(reply());await new Promise(resolve=>setTimeout(resolve,5));
 let state=application.getSnapshot();assert(state.result&&state.packet);assert(Object.isFrozen(state.packet));
 const frozen=C.serialize(state.packet),confirmedBinding=C.binding(state.confirmed);
 journey.getElementById('print').fire('click');assert.equal(prints,1);assert(journey.print.html.includes(state.result.answer.replace(' [1].','')));
 journey.getElementById('edit').fire('click');assert.equal(application.getSnapshot().confirmed,null);
 journey.getElementById('cancel-edit').fire('click');
 assert.equal(C.serialize(application.getSnapshot().packet),frozen);assert.equal(C.binding(application.getSnapshot().confirmed),confirmedBinding);
 // Retry while preserving an old answer is not exposed; edit then reconfirm.
 journey.getElementById('edit').fire('click');
 journey.getElementById('edit-aim').value='';journey.getElementById('edit-method').value='Fibonacci stream keys';journey.getElementById('edit-scope').value='LP2-15';journey.getElementById('edit-rules').value='';
 journey.getElementById('editor').fire('submit');journey.getElementById('confirm').fire('click');
 assert.equal(requests.length,2);const old=requests[1];
 journey.getElementById('cancel').fire('click');assert.equal(old.options.signal.aborted,true);assert.equal(application.getSnapshot().busy,false);
 journey.getElementById('retry').fire('click');assert.equal(requests.length,3);
 const current=requests[2];assert.equal(current.options.signal.aborted,false);
 timers[1]();assert.equal(current.options.signal.aborted,false,'An older timeout cannot abort the new request');
 old.resolve(reply());await new Promise(resolve=>setTimeout(resolve,5));
 assert.equal(application.getSnapshot().result,null,'Canceled late response cannot populate the current result');
 current.resolve(reply());await new Promise(resolve=>setTimeout(resolve,5));
 assert(application.getSnapshot().result&&application.getSnapshot().packet);
 const saved=application.getSnapshot().packet;
 journey.getElementById('back').fire('click');assert.equal(application.getSnapshot().stage,'input');assert.equal(application.getSnapshot().packet,null);
 assert.equal(saved.research.answer,'The published Fibonacci stream test is bounded [1].','Old frozen packet remains unchanged after leaving');
 application.destroy();console.log('PASS mocked full journey: success, exact print packet, edit/cancel restoration, new confirmation, cancel/retry, stale response guard and request-local timeout.');
})().catch(error=>{console.error(error);process.exitCode=1;});
