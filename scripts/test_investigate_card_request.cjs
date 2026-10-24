'use strict';
// Actual production event handlers and contract, with deferred local-only responses.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),R=require('../claim-research.js'),S=require('../assistant-search.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const evidence=S.experimentDocs(registry.records).find(d=>d.id==='lp2-known-vigenere-keys');
assert(evidence,'The answer fixture must cite a real published record');
const known=value=>C.field('specified',value,{kind:'supplied',refs:['original wording']});
const pages=['lp2-00','lp2-02','lp2-15','lp2-17'];
const original='Apply Vigenere with key FIRFUMFERENFE, then Atbash. Preserve word boundaries and reset on each page.';
const turn=()=>new Promise(resolve=>setImmediate(resolve));
// WebCrypto resolves off-thread; a bounded elapsed wait must yield real time.
async function until(predicate,message){const deadline=Date.now()+5000;while(Date.now()<deadline){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,1));}assert.fail(message);}
class Element{
 constructor(id){this.id=id;this.listeners={};this.disabled=false;this.textContent='';this.value='';this.hidden=false;this.html='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){}remove(){}replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;}get innerHTML(){return this.html;}
 insertAdjacentHTML(_,value){this.html+=value;}
}
function documentFixture(){
 const host=new Element('investigate'),print=new Element('print-snapshot'),cache=new Map();
 return {defaultView:{location:{search:''}},activeElement:null,host,print,
  getElementById(id){if(id==='investigate')return host;if(id==='print-snapshot')return print;
   if(!host.html.includes('id="'+id+'"')&&!cache.get('method-step-list')?.html.includes('id="'+id+'"'))return null;
   if(!cache.has(id))cache.set(id,new Element(id));return cache.get(id);},
  querySelector(selector){if(selector==='input[name=choice]:checked')return this.selectedChoice?{value:this.selectedChoice}:null;return selector.startsWith('#')?this.getElementById(selector.slice(1)):null;}};
}
async function fixture({gateBinding=false,legacy=false}={}){
 const doc=documentFixture(),requests=[],timers=[];let releaseBinding,bindingStarted=false,serial=0;
 const realBinding=R.binding;
 if(gateBinding)R.binding=async request=>{bindingStarted=true;await new Promise(resolve=>{releaseBinding=resolve;});return realBinding(request);};
 const app=I.createApp(doc,{id:()=> 'card-test-'+(++serial),now:()=> '2026-10-24T12:00:00Z',schedule:fn=>{timers.push(fn);return timers.length-1;},unschedule:()=>{},fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',interpretationEndpoint:'https://mock.example/interpret',...(!legacy?{researchContract:'card-v1'}:{})});
  if(url==='https://mock.example/interpret')return require('./mock_interpretation_response.cjs')(options);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  assert.equal(url,'https://mock.example/ask');return new Promise(resolve=>requests.push({resolve,options}));
 }});
 await app.ready;
 doc.getElementById('idea').value=original;doc.getElementById('intake').fire('submit');
 await until(()=>app.getSnapshot().stage==='review','Mocked interpretation did not reach review');
 require('./mock_interpretation_response.cjs').acknowledge(doc,app);
 const draft=app.getSnapshot().draft;
 draft.aim=C.normalizeAim(known('Find readable text'));
 draft.method=known({operations:[{id:'vigenere',label:'Vigenere',key:'FIRFUMFERENFE',offset:7},{id:'atbash',label:'Atbash',offset:3}]});
 draft.scope=known({pages,description:'Only lines 2–3 on the selected pages'});
 draft.rules={...draft.rules,wordBoundaries:known('preserve'),boundaryMode:known('within_words'),reset:known('per_page')};
 draft.unresolved=[];
 // Re-enter the ordinary review through production handlers after fixture specification.
 doc.getElementById('edit').fire('click');doc.getElementById('cancel-edit').fire('click');
 assert(doc.getElementById('confirm'));doc.getElementById('confirm').fire('click');assert.equal(app.getSnapshot().stage,'research',doc.host.html);
 if(gateBinding)assert(bindingStarted);else await until(()=>requests.length===1,'Comparison request did not become ready');
 return {doc,app,requests,timers,releaseBinding:()=>releaseBinding?.(),restore:()=>{app.destroy();R.binding=realBinding;}};
}
function reply(binding,answer=true){return {claimBinding:binding,...(answer?{answer:'This fixed-key comparison is bounded [1].',sources:[evidence]}:{answer:null,sources:[],reason:'no-matching-records'})};}
async function success(answer=true){
 const f=await fixture();try{
  const snapshot=f.app.getSnapshot().confirmed,sent=JSON.parse(f.requests[0].options.body),prepared=R.prepare(snapshot);
  assert.deepEqual(Object.keys(sent).sort(),['card','originalIdea','version']);assert.deepEqual(sent,prepared.request);
  assert.equal(sent.originalIdea,original);assert.deepEqual(sent.card.scope.value.pages,pages,'More than two exact page hints retain every hole');
  assert(!sent.card.scope.value.pages.includes('lp2-01'));assert.equal(sent.card.scope.value.description,'Only lines 2–3 on the selected pages');
  assert.deepEqual(sent.card.method.value.operations.map(o=>o.id),['vigenere','atbash']);assert.equal(sent.card.method.value.operations[0].key,'FIRFUMFERENFE');assert.equal(sent.card.method.value.operations[0].offset,7);
  assert.equal(sent.card.rules.wordBoundaries.value,'preserve');assert.equal(sent.card.rules.reset.value,'per_page');
  const validated=R.validate(sent);assert(validated.confirmedQuery.includes('FIRFUMFERENFE'));assert(validated.confirmedQuery.includes('per_page'));assert(validated.confirmedQuery.indexOf('"id":"vigenere"')<validated.confirmedQuery.indexOf('"id":"atbash"'));
  f.requests[0].resolve(Response.json(reply(await R.binding(sent),answer)));await until(()=>!f.app.getSnapshot().busy,'Bound response did not settle');
  const state=f.app.getSnapshot();assert(state.result&&state.packet);assert.equal(C.binding(state.packet.confirmed),C.binding(snapshot),'Reply packet stays attached to the exact confirmed snapshot');
  assert.deepEqual(state.packet.confirmed.scope.value.pages,pages);assert.equal(state.packet.confirmed.method.value.operations[0].key,'FIRFUMFERENFE');assert(Object.isFrozen(state.packet));
  assert.equal(!!state.result.noMatch,!answer);assert(f.doc.print.html.includes('FIRFUMFERENFE'));assert(f.doc.print.html.includes('Only lines 2–3'));
 }finally{f.restore();}
}
async function rejectedBindings(){
 for(const answer of [true,false])for(const kind of ['missing','different']){
  const f=await fixture();try{
   const data=reply(kind==='different'?'0'.repeat(64):undefined,answer);if(kind==='missing')delete data.claimBinding;
   f.requests[0].resolve(Response.json(data));await until(()=>!f.app.getSnapshot().busy,'Rejected response did not settle');
   assert.equal(f.app.getSnapshot().result,null,kind+' binding must block '+(answer?'answer':'no-match'));assert.equal(f.app.getSnapshot().packet,null);assert.equal(f.doc.print.html,'');
   assert(f.doc.host.html.includes('does not match your confirmed idea'));assert(!f.doc.host.html.includes('This fixed-key comparison is bounded'));
  }finally{f.restore();}
 }
}
async function stale(){
 const digest=await fixture({gateBinding:true});try{
  assert.equal(digest.requests.length,0);digest.doc.getElementById('edit').fire('click');digest.releaseBinding();await turn();await turn();
  assert.equal(digest.requests.length,0,'Editing while SHA binding is pending must stop the obsolete network request');assert.equal(digest.app.getSnapshot().confirmed,null);assert(digest.doc.getElementById('editor'));
 }finally{digest.restore();}
 for(const action of ['edit','back','cancel']){
  const f=await fixture();try{
   const body=JSON.parse(f.requests[0].options.body),hash=await R.binding(body);f.doc.getElementById(action).fire('click');assert(f.requests[0].options.signal.aborted);
   f.requests[0].resolve(Response.json(reply(hash)));await turn();await turn();assert.equal(f.app.getSnapshot().result,null);assert.equal(f.app.getSnapshot().packet,null,'Late reply cannot attach a packet after '+action);
   if(action==='cancel'){
    f.doc.getElementById('retry').fire('click');await until(()=>f.requests.length===2,'Retry did not issue a fresh request');assert.deepEqual(JSON.parse(f.requests[1].options.body),body);
    f.requests[1].resolve(Response.json(reply(hash,false)));await until(()=>!f.app.getSnapshot().busy,'Retry did not settle');assert(f.app.getSnapshot().result.noMatch);
   }
  }finally{f.restore();}
 }
}
function visibleParameters(){
 const draft=C.createDraft({source:{text:original},aim:known('Find readable text'),method:known({operations:[{id:'vigenere',label:'Vigenere',key:'<ABC>',offset:7},{id:'atbash',label:'Atbash',offset:3}]}),scope:known({pages}),rules:{reset:known('per_page')},unresolved:[{kind:'source_note',text:'Condition <unsafe>'}]});
 const html=I.rowsHTML(draft);assert(html.includes('&lt;ABC&gt;'),'Confirmation must show the actual escaped key, not just the method label');assert(!html.includes('<ABC>'));assert(html.includes('7'));assert(html.includes('3'));assert(html.includes('Condition &lt;unsafe&gt;'),'Remaining supplied notes stay visible and escaped');
}
(async()=>{
 await success();await success(false);await rejectedBindings();await stale();visibleParameters();
 const legacy=await fixture({legacy:true});try{const sent=JSON.parse(legacy.requests[0].options.body);assert.equal(typeof sent.query,'string');assert.equal(sent.version,undefined,'Absent feature flag keeps the legacy request');}finally{legacy.restore();}
 console.log('PASS card-v1 production journeys: exact page holes/order/key/rules/original, answer and no-match SHA binding, unchanged packet, async digest/network edit/cancel guards, retry, visible escaped parameters, and legacy configuration.');
})().catch(error=>{console.error(error);process.exitCode=1;});
