'use strict';
// Production createApp handlers; all interpretation/research/save requests are deferred mocks.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),P=require('../claim-interpretation.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function until(predicate,message){const end=Date.now()+5000;while(Date.now()<end){if(predicate())return;await turn();}assert.fail(message);}
class Element{
 constructor(id){this.id=id;this.listeners={};this.disabled=false;this.textContent='';this.value='';this.hidden=false;this.html='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){}remove(){}replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;}get innerHTML(){return this.html;}
 insertAdjacentHTML(_,value){this.html+=value;}
}
function documentFixture(search='',hash=''){
 const host=new Element('investigate'),print=new Element('print-snapshot'),cache=new Map();
 return {defaultView:{location:{search,hash}},activeElement:null,host,print,
  getElementById(id){if(id==='investigate')return host;if(id==='print-snapshot')return print;
   if(!host.html.includes('id="'+id+'"')&&!cache.get('method-step-list')?.html.includes('id="'+id+'"'))return null;
   if(!cache.has(id))cache.set(id,new Element(id));return cache.get(id);},
  querySelector(selector){if(selector==='input[name=choice]:checked')return this.selectedChoice?{value:this.selectedChoice}:null;return selector.startsWith('#')?this.getElementById(selector.slice(1)):null;}};
}
const raw='  Use Vigenere with key "A B" on LP2-00, LP2-02 and LP2-17.\nKeep word boundaries.  ';
const quote=(text,value)=>({start:text.indexOf(value),quote:value});
function candidate(text=raw){return {schema:P.SCHEMA,outcome:null,steps:[{id:'described_method',familyId:'polyalphabetic',source:quote(text,text),parameters:{key:{value:'A B',source:quote(text,'key "A B"')}}}],scope:{pages:['lp2-00','lp2-02','lp2-17'],passage:null,source:quote(text,'LP2-00, LP2-02 and LP2-17')},rules:{wordBoundaries:{status:'specified',value:'preserve',source:quote(text,'Keep word boundaries')}}};}
async function sourceBinding(text){return Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex');}
async function response(text=raw,proposed=candidate(text)){return Response.json({candidate:proposed,sourceBinding:await sourceBinding(text)});}
async function fixture({configured=true,delayConfig=false,search='',hash=''}={}){
 const doc=documentFixture(search,hash),requests=[],timers=[];let resolveConfig,serial=0;
 const config={endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals',...(configured?{interpretationEndpoint:'https://mock.example/interpret'}:{})};
 const app=I.createApp(doc,{id:()=> 'interpret-'+(++serial),schedule:fn=>{timers.push(fn);return timers.length-1;},unschedule:()=>{},fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return delayConfig?new Promise(resolve=>{resolveConfig=resolve;}):Response.json(config);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  assert.match(url,/^https:\/\/mock\.example\/(interpret|ask|proposals)$/);
  // Deliberately ignore abort: the UI must reject a late completed response itself.
  return new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
 }});
 if(!delayConfig)await app.ready;
 return {doc,app,requests,timers,releaseConfig:()=>resolveConfig(Response.json(config)),submit(text=raw){doc.getElementById('idea').value=text;doc.getElementById('intake').fire('submit');},destroy:()=>app.destroy()};
}
function answer(f,choice,text=''){f.doc.selectedChoice=choice;const detail=f.doc.getElementById('other-detail');if(detail)detail.value=text;f.doc.getElementById('clarification').fire('submit');f.doc.selectedChoice=null;}
async function accepted(){
 const f=await fixture();try{
  assert.equal(f.requests.length,0);f.submit();assert.equal(f.app.getSnapshot().stage,'interpreting');assert.equal(f.requests.length,1);assert.deepEqual(JSON.parse(f.requests[0].options.body),{text:raw});
  assert(f.doc.getElementById('cancel-interpretation'));assert(f.doc.getElementById('use-original'));assert.equal(f.doc.getElementById('confirm'),null);
  f.requests[0].resolve(await response());await until(()=>f.app.getSnapshot().stage==='review','Accepted candidate did not reach questions');
  const draft=f.app.getSnapshot().draft;assert.equal(draft.source.text,raw);assert.equal(draft.confirmation,null);assert.equal(draft.method.value.operations[0].key,'A B');assert.deepEqual(draft.scope.value.pages,['lp2-00','lp2-02','lp2-17']);assert.equal(draft.rules.wordBoundaries.value,'preserve');
  const visible=I.rowsHTML(draft);assert(visible.includes('A B'));assert(!/key provenance|keyProvenance|provenance|source:text:/i.test(visible),'Extracted evidence stays in provenance rather than visible method parameters');
  assert.equal(I.intakeQuestions(draft)[0].id,'aim','An unstated outcome remains a question, not an invented goal');assert.equal(f.requests.length,1);
  answer(f,'decipher');assert(f.doc.getElementById('confirm'));assert.equal(f.requests.length,1,'Answering questions cannot ask or save');
  f.doc.getElementById('edit').fire('click');assert.equal(f.requests.length,1);f.doc.getElementById('cancel-edit').fire('click');assert.equal(f.requests.length,1,'Editing does not reinterpret');
  f.doc.getElementById('confirm').fire('click');await until(()=>f.requests.some(r=>r.url.endsWith('/ask')),'Explicit research confirmation did not compare');
  assert.equal(f.requests.filter(r=>r.url.endsWith('/interpret')).length,1);assert.equal(f.requests.filter(r=>r.url.endsWith('/proposals')).length,1);assert.equal(f.app.getSnapshot().confirmed.source.text,raw);
 }finally{f.destroy();}
}
async function ambiguity(){
 const text='Reverse prime values in each row, preserving word boundaries.';
 const proposed={schema:P.SCHEMA,outcome:null,steps:[{id:'ambiguous_reversal',familyId:null,source:quote(text,text),parameters:{}}],scope:null,rules:{wordBoundaries:{status:'specified',value:'preserve',source:quote(text,'preserving word boundaries')}}};
 const f=await fixture();try{f.submit(text);f.requests[0].resolve(await response(text,proposed));await until(()=>f.app.getSnapshot().stage==='review','Ambiguous candidate not reviewed');
  assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'operation');assert.equal(f.doc.getElementById('confirm'),null);answer(f,'reverse_row_runes');
  assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'word-boundary','Paraphrased ambiguity must retain existing boundary decision');assert.equal(f.requests.length,1);
  const beforeOther=C.serialize(f.app.getSnapshot().draft);
  const explanation='Keep <whole words> in order, then apply my supplied rule.';answer(f,'other',explanation);
  const revised=f.app.getSnapshot().draft,custom=revised.unresolved.find(item=>item.kind==='custom_interpretation');assert.equal(custom.text,explanation);assert.equal(custom.question,'word-boundary');
  const before=C.serialize(revised),visible=I.rowsHTML(revised);assert(visible.includes('Keep &lt;whole words&gt; in order'));assert(!visible.includes('custom_interpretation'));assert(!visible.includes('&quot;question&quot;'));assert.equal(C.serialize(revised),before,'Readable display never removes structured constraints from the draft/binding');
  const mixed={...revised,unresolved:[{kind:'source_note',text:'Source note <literal>',provenance:{kind:'supplied',refs:['original']}},{kind:'unknown_structured_rule',text:'Keep this text',setting:{offset:7}}]};
  const fallback=I.rowsHTML(mixed);assert(fallback.includes('Source note &lt;literal&gt;'));assert(!fallback.includes('source_note'));assert(fallback.includes('unknown_structured_rule'));assert(fallback.includes('&quot;offset&quot;:7'),'Unknown structured constraints retain every safe field');
  const extended=I.rowsHTML({...revised,unresolved:[{kind:'source_note',text:'Keep this text',offset:9}]});assert(extended.includes('&quot;offset&quot;:9'),'Additional fields on a known note kind cannot disappear');
  f.doc.getElementById('cancel-edit').fire('click');
  assert.equal(C.serialize(f.app.getSnapshot().draft),beforeOther,'Cancel restores the exact state before the custom answer and editor opened');
  assert(!f.doc.host.html.includes('Your explanation is kept'),'Canceled editor guidance must also disappear');
  assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'word-boundary');
  answer(f,'within_words');
  assert(!f.app.getSnapshot().draft.unresolved.some(item=>item.text===explanation),'A canceled custom answer must not contradict the replacement choice');
  assert.equal(f.app.getSnapshot().draft.rules.boundaryMode.value,'within_words');
  assert.equal(f.app.getSnapshot().draft.source.text,text);
  assert.equal(f.requests.length,1,'Cancel and replacement answer never reinterpret, compare or save');

 }finally{f.destroy();}
}
async function failures(){
 for(const kind of ['outage','missing-binding','wrong-binding','invalid-candidate','timeout']){
  const f=await fixture();try{f.submit();const request=f.requests[0];
   if(kind==='outage')request.resolve(Response.json({error:'Unavailable'},{status:503}));
   else if(kind==='invalid-candidate'){const c=candidate();c.steps[0].parameters.key.value='INVENTED';request.resolve(await response(raw,c));}
   else if(kind==='timeout'){f.timers[0]();request.resolve(await response());}
   else request.resolve(Response.json({candidate:candidate(),...(kind==='wrong-binding'?{sourceBinding:'0'.repeat(64)}:{})}));
   await until(()=>!f.app.getSnapshot().interpreting,'Failed interpretation did not settle: '+kind);
   assert.equal(f.app.getSnapshot().stage,'interpreting');assert.equal(f.app.getSnapshot().draft,null);assert(f.doc.getElementById('retry-interpretation'));assert(f.doc.getElementById('use-original'));assert.equal(f.requests.length,1);
   f.doc.getElementById('use-original').fire('click');assert.equal(f.app.getSnapshot().stage,'review');assert.equal(f.app.getSnapshot().draft.source.text,raw);assert.equal(f.requests.length,1,'Fallback sends no research/save/interpretation request');
  }finally{f.destroy();}
 }
 const retry=await fixture();try{retry.submit();retry.requests[0].reject(Error('Offline'));await until(()=>!!retry.doc.getElementById('retry-interpretation'),'Retry was not offered');retry.doc.getElementById('retry-interpretation').fire('click');assert.equal(retry.requests.length,2);assert.deepEqual(JSON.parse(retry.requests[1].options.body),{text:raw});retry.requests[1].resolve(await response());await until(()=>retry.app.getSnapshot().stage==='review','Explicit retry did not work');}finally{retry.destroy();}
}
async function stale(){
 const f=await fixture();try{f.submit();const first=f.requests[0];f.doc.getElementById('cancel-interpretation').fire('click');assert(first.options.signal.aborted);assert.equal(f.app.getSnapshot().stage,'input');assert(f.doc.host.html.includes('Use Vigenere'));
  const secondText=raw.replace('A B','C D'),secondCandidate=candidate(secondText);secondCandidate.steps[0].parameters.key.value='C D';secondCandidate.steps[0].parameters.key.source=quote(secondText,'key "C D"');
  f.submit(secondText);const second=f.requests[1];first.resolve(await response());await turn();await turn();assert.equal(f.app.getSnapshot().stage,'interpreting');assert.equal(f.app.getSnapshot().draft,null);
  second.resolve(await response(secondText,secondCandidate));await until(()=>f.app.getSnapshot().stage==='review','Newest interpretation did not win');assert.equal(f.app.getSnapshot().draft.source.text,secondText);assert.equal(f.app.getSnapshot().draft.method.value.operations[0].key,'C D');
 }finally{f.destroy();}
 const fallback=await fixture();try{fallback.submit();fallback.doc.getElementById('use-original').fire('click');fallback.doc.getElementById('edit').fire('click');const before=fallback.doc.host.html;fallback.doc.getElementById('edit-method').value='Unsaved human revision';fallback.requests[0].resolve(await response());await turn();await turn();assert.equal(fallback.doc.host.html,before);assert.equal(fallback.doc.getElementById('edit-method').value,'Unsaved human revision');}finally{fallback.destroy();}
 const destroyed=await fixture();destroyed.submit();const before=destroyed.doc.host.html;destroyed.destroy();assert(destroyed.requests[0].options.signal.aborted);destroyed.requests[0].resolve(await response());await turn();await turn();assert.equal(destroyed.doc.host.html,before,'Destroy prevents all late DOM updates');
}
async function entryAndReadiness(){
 const waiting=await fixture({delayConfig:true});try{waiting.submit();assert.equal(waiting.requests.length,0);waiting.releaseConfig();await waiting.app.ready;await until(()=>waiting.requests.length===1,'Explicit pending submit did not resume after config');assert(waiting.requests[0].url.endsWith('/interpret'));waiting.requests[0].resolve(await response());await until(()=>waiting.app.getSnapshot().stage==='review','Config-delayed accepted proposal not reviewed');}finally{waiting.destroy();}
 const delayed=await fixture({delayConfig:true});try{delayed.submit();assert.equal(delayed.app.getSnapshot().stage,'interpreting');assert.equal(delayed.requests.length,0);delayed.doc.getElementById('use-original').fire('click');const draft=delayed.app.getSnapshot().draft;delayed.releaseConfig();await delayed.app.ready;await turn();assert.equal(delayed.requests.length,0,'Late config cannot start interpretation after fallback');assert.equal(delayed.app.getSnapshot().draft,draft);}finally{delayed.destroy();}
 const legacy=await fixture({configured:false});try{legacy.submit();assert.equal(legacy.app.getSnapshot().stage,'review');assert.equal(legacy.app.getSnapshot().draft.source.text,raw);assert.equal(legacy.requests.length,0,'No endpoint keeps synchronous local review after readiness');}finally{legacy.destroy();}
 const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
 const shared=C.confirm(C.createDraft({source:{text:'Original shared fixture'},aim:known('Find readable text'),method:known({operations:[{id:'described_method',label:'Inspect this exact relationship'}]}),scope:known({pages:['lp2-17']})}),{id:'shared',at:'2026-10-24T12:00:00Z'});
 const imported=await fixture({hash:H.encode(shared)});try{assert.equal(imported.app.getSnapshot().stage,'review');assert.equal(imported.requests.length,0);imported.doc.getElementById('edit').fire('click');imported.doc.getElementById('cancel-edit').fire('click');assert.equal(imported.requests.length,0,'Imported card viewing/editing never reinterprets or sends research/save');}finally{imported.destroy();}
 const hinted=await fixture({search:'?pages=lp2-15&pages=lp2-17'});try{hinted.submit();hinted.requests[0].resolve(await response());await until(()=>hinted.app.getSnapshot().stage==='review','Hinted candidate not reviewed');assert.deepEqual(hinted.app.getSnapshot().draft.scope.value.pages,['lp2-15','lp2-17']);assert.equal(hinted.app.getSnapshot().draft.source.text,raw);}finally{hinted.destroy();}
}
(async()=>{await accepted();await ambiguity();await failures();await stale();await entryAndReadiness();console.log('PASS production interpretation journeys: source-bound unconfirmed candidate, existing questions, exact key/page holes/original, explicit research/save only, failure/retry/fallback/cancel/stale/destroy/config/import guards.');})().catch(error=>{console.error(error);process.exitCode=1;});
