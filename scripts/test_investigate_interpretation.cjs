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
   if(!cache.has(id)){const element=new Element(id),tag=host.html.match(new RegExp('<[^>]+id="'+id+'"[^>]*>'));element.disabled=!!tag&&/\sdisabled(?:\s|>|=)/.test(tag[0]);cache.set(id,element);}return cache.get(id);},
  querySelector(selector){if(selector==='input[name=choice]:checked')return this.selectedChoice?{value:this.selectedChoice}:null;if(selector==='.privacy'){if(!cache.has('privacy'))cache.set('privacy',new Element('privacy'));return cache.get('privacy');}return selector.startsWith('#')?this.getElementById(selector.slice(1)):null;}};
}
const raw='  Use Vigenere with key "A B" on LP2-00, LP2-02 and LP2-17.\nKeep word boundaries.  ';
const quote=(text,value)=>({start:text.indexOf(value),quote:value});
function candidate(text=raw){return {schema:P.SCHEMA,outcome:null,steps:[{id:'described_method',familyId:'polyalphabetic',source:quote(text,text),parameters:{key:{value:'A B',source:quote(text,'key "A B"')}}}],scope:{pages:['lp2-00','lp2-02','lp2-17'],passage:null,source:quote(text,'LP2-00, LP2-02 and LP2-17')},rules:{wordBoundaries:{status:'specified',value:'preserve',source:quote(text,'Keep word boundaries')}}};}
async function sourceBinding(text){return Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex');}
async function response(text=raw,proposed=candidate(text)){return Response.json({candidate:proposed,sourceBinding:await sourceBinding(text)});}
async function fixture({configured=true,delayConfig=false,delayConfigAfterFailure=false,delayRegistry=false,failRegistry=false,failConfig=false,malformedConfig=false,search='',hash=''}={}){
 const doc=documentFixture(search,hash),requests=[],timers=[],loads=[];let resolveConfig,resolveRegistry,serial=0,registryCalls=0,configCalls=0;
 const config={endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals',...(configured?{interpretationEndpoint:'https://mock.example/interpret'}:{})};
 const app=I.createApp(doc,{id:()=> 'interpret-'+(++serial),schedule:fn=>{timers.push(fn);return timers.length-1;},unschedule:()=>{},fetcher:async(url,options)=>{
  loads.push(url);
  if(url==='data/experiments.json'){registryCalls++;if(delayRegistry&&registryCalls===1)return new Promise(resolve=>{resolveRegistry=resolve;});return failRegistry&&registryCalls===1?Response.json({error:'Unavailable'},{status:503}):Response.json(registry);}
  if(url==='data/assistant.json'){configCalls++;if((failConfig===true&&configCalls===1)||(Number.isInteger(failConfig)&&configCalls<=failConfig))return Response.json({error:'Unavailable'},{status:503});if(malformedConfig&&configCalls===1)return Response.json(null);return (delayConfig||delayConfigAfterFailure&&configCalls>1)?new Promise(resolve=>{resolveConfig=resolve;}):Response.json(config);}
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  assert.match(url,/^https:\/\/mock\.example\/(interpret|ask|proposals)$/);
  // Deliberately ignore abort: the UI must reject a late completed response itself.
  return new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
 }});
 if(!delayConfig&&!delayRegistry)await app.ready;
 return {doc,app,requests,timers,loads,releaseConfig:()=>resolveConfig(Response.json(config)),releaseRegistry:()=>resolveRegistry(Response.json(registry)),submit(text=raw){doc.getElementById('idea').value=text;doc.getElementById('intake').fire('submit');},destroy:()=>app.destroy()};
}
function answer(f,choice,text=''){f.doc.selectedChoice=choice;const detail=f.doc.getElementById('other-detail');if(detail)detail.value=text;f.doc.getElementById('clarification').fire('submit');f.doc.selectedChoice=null;}

function edit(f,text){const field=f.doc.getElementById('idea');field.value=text;field.fire('input');return field;}
function cancel(f){const field=f.doc.getElementById('idea');field.listeners.keydown({key:'Escape',preventDefault(){}});}
async function accepted(){
 const f=await fixture();try{
  const field=edit(f,raw),markup=f.doc.host.html;f.doc.activeElement=field;field.selectionStart=8;field.selectionEnd=12;
  f.submit();assert.equal(f.app.getSnapshot().stage,'input');assert(f.app.getSnapshot().interpreting);assert.equal(f.requests.length,1);assert.equal(f.doc.getElementById('idea'),field);assert.equal(f.doc.host.html,markup,'Loading does not replace the input form');assert.equal(field.value,raw);assert.equal(field.selectionStart,8);assert.equal(field.selectionEnd,12);
  assert(f.doc.getElementById('interpret-submit').disabled);assert.equal(f.doc.getElementById('interpret-submit').textContent,'Checking idea…');
  for(const id of ['cancel-interpretation','use-original','retry-interpretation','confirm'])assert.equal(f.doc.getElementById(id),null);
  f.submit();assert.equal(f.requests.length,1,'Repeated submit while pending cannot duplicate the request');
  f.requests[0].resolve(await response());await until(()=>f.app.getSnapshot().stage==='review','Valid candidate did not advance');
  const d=f.app.getSnapshot().draft;assert.equal(d.source.text,raw);assert.equal(d.confirmation,null);assert.equal(d.method.value.operations[0].key,'A B');assert.deepEqual(d.scope.value.pages,['lp2-00','lp2-02','lp2-17']);assert.equal(d.rules.wordBoundaries.value,'preserve');assert.equal(I.intakeQuestions(d)[0].id,'aim');assert.equal(f.requests.length,1);
  answer(f,'decipher');assert(f.doc.getElementById('confirm'));f.doc.getElementById('edit').fire('click');f.doc.getElementById('cancel-edit').fire('click');assert.equal(f.requests.length,1);
  f.doc.getElementById('confirm').fire('click');await until(()=>f.requests.some(r=>r.url.endsWith('/ask')),'Explicit confirm did not compare');assert.equal(f.requests.filter(r=>r.url.endsWith('/proposals')).length,1);assert.equal(f.app.getSnapshot().confirmed.source.text,raw);
 }finally{f.destroy();}
}
async function ambiguity(){
 const text='Reverse prime values in each row, preserving word boundaries.',proposed={schema:P.SCHEMA,outcome:null,steps:[{id:'ambiguous_reversal',familyId:null,source:quote(text,text),parameters:{}}],scope:null,rules:{wordBoundaries:{status:'specified',value:'preserve',source:quote(text,'preserving word boundaries')}}};
 const f=await fixture();try{f.submit(text);f.requests[0].resolve(await response(text,proposed));await until(()=>f.app.getSnapshot().stage==='review','Ambiguity not reviewed');assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'operation');answer(f,'reverse_row_runes');assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'word-boundary');answer(f,'within_words');assert.equal(f.app.getSnapshot().draft.rules.boundaryMode.value,'within_words');assert.equal(f.requests.length,1);}finally{f.destroy();}
}
async function tinyAmbiguity(){
 for(const text of ['Reverse prime values in rows','  Reverse the prime values in rows.  ','Reverse prime values in every row']){
  const f=await fixture();try{f.submit(text);assert.equal(f.app.getSnapshot().stage,'review');assert.equal(f.requests.length,0);assert.equal(f.app.getSnapshot().draft.source.text,text);assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'operation');assert(f.doc.host.html.includes('>Edit idea</button>'));assert(f.doc.host.html.includes('>Continue</button>'));assert(f.doc.host.html.includes('<p class="idea-wording">'+text+'</p>'));assert(!f.doc.host.html.includes('<summary>Original idea'));assert.equal(f.doc.getElementById('edit'),null,'Pending questions do not duplicate Edit idea with structured editing');answer(f,'reverse_value_digits');assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'aim');answer(f,'decipher');assert.equal(I.intakeQuestions(f.app.getSnapshot().draft)[0].id,'scope');answer(f,'undecided');assert(f.doc.getElementById('confirm'));assert(f.doc.getElementById('edit'),'Structured editing remains available after questions');assert.equal(f.requests.length,0);}finally{f.destroy();}
 }
 const custom=await fixture();try{custom.submit('Reverse prime values in rows');const before=C.serialize(custom.app.getSnapshot().draft);answer(custom,'other','Use a different exact rule.');assert(custom.doc.getElementById('editor'),'Other still opens the exact rule editor');custom.doc.getElementById('cancel-edit').fire('click');assert.equal(C.serialize(custom.app.getSnapshot().draft),before);assert.equal(I.intakeQuestions(custom.app.getSnapshot().draft)[0].id,'operation');assert.equal(custom.requests.length,0);}finally{custom.destroy();}
 for(const text of ['Do not reverse prime values in rows','Reverse prime values in rows with key ABC','Reverse prime values in rows then apply Atbash','Reverse prime values in rows only if marked']){const f=await fixture();try{f.submit(text);assert.equal(f.app.getSnapshot().stage,'input');assert(f.app.getSnapshot().interpreting);assert.equal(f.requests.length,1);assert.deepEqual(JSON.parse(f.requests[0].options.body),{text});}finally{f.destroy();}}
}
async function failures(){
 for(const kind of ['outage','busy','rate-limit','invalid-response','missing-binding','wrong-binding','invalid-candidate','timeout']){
  const f=await fixture();try{const field=edit(f,raw);field.selectionStart=3;field.selectionEnd=7;f.doc.activeElement=field;f.submit();const request=f.requests[0];
   if(kind==='busy')request.resolve(Response.json({reason:'busy'},{status:503}));
   else if(kind==='rate-limit')request.resolve(Response.json({reason:'untrusted message <script>'},{status:429}));
   else if(kind==='invalid-response')request.resolve(Response.json({reason:'invalid-interpretation'},{status:503}));
   else if(kind==='outage')request.resolve(Response.json({error:'Unavailable'},{status:503}));
   else if(kind==='invalid-candidate'){const c=candidate();c.steps[0].parameters.key.value='INVENTED';request.resolve(await response(raw,c));}
   else if(kind==='timeout'){f.timers[0]();request.resolve(await response());}
   else request.resolve(Response.json({candidate:candidate(),...(kind==='wrong-binding'?{sourceBinding:'0'.repeat(64)}:{})}));
   await until(()=>!f.app.getSnapshot().interpreting,'Failure did not settle');assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.app.getSnapshot().draft,null);assert.equal(f.doc.getElementById('idea'),field);assert.equal(field.value,raw);assert.equal(field.selectionStart,3);assert.equal(field.selectionEnd,7);assert.equal(f.doc.activeElement,field);
   const failureText=f.doc.getElementById('interpretation-error').textContent;assert(failureText.length>0);assert(!failureText.includes('<script>'));assert(failureText.includes(kind==='timeout'?'timed out':kind==='rate-limit'?'in a minute':['outage','busy'].includes(kind)?'temporarily unavailable':'interpreted reliably'));assert(!f.doc.getElementById('interpret-submit').disabled);assert.equal(f.doc.getElementById('interpret-submit').textContent,'Check idea');assert.equal(f.requests.length,1);assert(!f.doc.host.html.includes('Original idea'));assert(!f.doc.getElementById('use-original'));
   f.submit();assert.equal(f.requests.length,2,'Regular Check idea retries exact source');assert.deepEqual(JSON.parse(f.requests[1].options.body),{text:raw});f.requests[1].resolve(await response());await until(()=>f.app.getSnapshot().stage==='review','Regular retry did not advance');
  }finally{f.destroy();}
 }
}
async function stale(){
 const f=await fixture();try{f.submit();const old=f.requests[0],field=f.doc.getElementById('idea'),next=raw.replace('A B','C D'),p=candidate(next);p.steps[0].parameters.key.value='C D';p.steps[0].parameters.key.source=quote(next,'key "C D"');
  edit(f,next);assert(old.options.signal.aborted);assert(!f.app.getSnapshot().interpreting);assert(!f.doc.getElementById('interpret-submit').disabled);assert.equal(f.doc.getElementById('idea'),field);f.submit(next);old.resolve(await response());await turn();await turn();assert.equal(f.app.getSnapshot().draft,null);assert(f.app.getSnapshot().interpreting);
  f.requests[1].resolve(await response(next,p));await until(()=>f.app.getSnapshot().stage==='review','Newest response not accepted');assert.equal(f.app.getSnapshot().draft.source.text,next);assert.equal(f.app.getSnapshot().draft.method.value.operations[0].key,'C D');
 }finally{f.destroy();}
 for(const fail of [false,true]){const f=await fixture();try{f.submit();const request=f.requests[0];cancel(f);assert(request.options.signal.aborted);assert.equal(f.app.getSnapshot().stage,'input');assert(!f.app.getSnapshot().interpreting);if(fail)request.reject(Error('late'));else request.resolve(await response());await turn();await turn();assert.equal(f.app.getSnapshot().draft,null);assert.equal(f.doc.getElementById('interpretation-error').textContent,'');}finally{f.destroy();}}
 const destroyed=await fixture();destroyed.submit();const html=destroyed.doc.host.html;destroyed.destroy();assert(destroyed.requests[0].options.signal.aborted);destroyed.requests[0].resolve(await response());await turn();await turn();assert.equal(destroyed.doc.host.html,html);
 const hashing=await fixture(),reply=await response(),realDigest=crypto.subtle.digest;let releaseHash,hashStarted=false;
 try{hashing.submit();crypto.subtle.digest=function(...args){hashStarted=true;return new Promise(resolve=>{releaseHash=()=>resolve(realDigest.apply(this,args));});};hashing.requests[0].resolve(reply);await until(()=>hashStarted,'Interpretation binding digest did not start');edit(hashing,'New text while source binding is checked');releaseHash();await turn();await turn();assert.equal(hashing.app.getSnapshot().stage,'input');assert.equal(hashing.app.getSnapshot().draft,null);assert.equal(hashing.doc.getElementById('idea').value,'New text while source binding is checked');assert.equal(hashing.doc.getElementById('interpretation-error').textContent,'');}finally{crypto.subtle.digest=realDigest;hashing.destroy();}
}
async function entryAndReadiness(){
 const waiting=await fixture({delayConfig:true});try{waiting.submit();assert.equal(waiting.requests.length,0);assert.equal(waiting.app.getSnapshot().stage,'input');waiting.releaseConfig();await waiting.app.ready;await until(()=>waiting.requests.length===1,'Config wait not resumed');waiting.requests[0].resolve(await response());await until(()=>waiting.app.getSnapshot().stage==='review','Config-delayed response not reviewed');}finally{waiting.destroy();}
 const canceled=await fixture({delayConfig:true,delayRegistry:true});try{canceled.submit();edit(canceled,'Changed before configuration');canceled.releaseConfig();await turn();await turn();assert.equal(canceled.requests.length,0);assert.equal(canceled.app.getSnapshot().stage,'input');canceled.releaseRegistry();await canceled.app.ready;assert.equal(canceled.requests.length,0);}finally{canceled.destroy();}
 for(const options of [{configured:false}]){const f=await fixture(options);try{f.submit();await until(()=>!f.app.getSnapshot().interpreting,'Unavailable config did not settle');assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.app.getSnapshot().draft,null);assert.equal(f.requests.length,0,'Unavailable service cannot silently promote an unverified original');assert(f.doc.getElementById('interpretation-error').textContent);}finally{f.destroy();}}
 const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
 const shared=C.confirm(C.createDraft({source:{text:'Original shared fixture'},aim:known('Find readable text'),method:known({operations:[{id:'described_method',label:'Inspect this exact relationship'}]}),scope:known({pages:['lp2-17']})}),{id:'shared',at:'2026-10-24T12:00:00Z'});
 const imported=await fixture({hash:H.encode(shared)});try{assert.equal(imported.app.getSnapshot().stage,'review');assert.equal(imported.requests.length,0);imported.doc.getElementById('edit').fire('click');imported.doc.getElementById('cancel-edit').fire('click');assert.equal(imported.requests.length,0);}finally{imported.destroy();}
 const hinted=await fixture({search:'?pages=lp2-15&pages=lp2-17'});try{hinted.submit();hinted.requests[0].resolve(await response());await until(()=>hinted.app.getSnapshot().stage==='review','Hint not reviewed');assert.deepEqual(hinted.app.getSnapshot().draft.scope.value.pages,['lp2-15','lp2-17']);assert.equal(hinted.app.getSnapshot().draft.source.text,raw);}finally{hinted.destroy();}
}
async function configRetry(){
 for(const options of [{failConfig:2},{malformedConfig:true}]){
  const f=await fixture(options);try{
   assert.equal(f.loads.filter(url=>url==='data/assistant.json').length,1);
   const field=edit(f,raw);field.selectionStart=7;field.selectionEnd=11;f.doc.activeElement=field;
   if(options.failConfig){
    f.submit();await until(()=>!f.app.getSnapshot().interpreting,'Explicit failed config retry did not settle');
    assert.equal(f.loads.filter(url=>url==='data/assistant.json').length,2);assert.equal(f.requests.length,0);
    assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.app.getSnapshot().draft,null);assert(f.doc.getElementById('interpretation-error').textContent);
    await turn();await turn();assert.equal(f.loads.filter(url=>url==='data/assistant.json').length,2,'No automatic retry loop');
   }
   f.submit();await until(()=>f.requests.length===1,'Regular Check idea did not reload recovered configuration');
   assert.equal(f.doc.getElementById('idea'),field);assert.equal(field.value,raw);assert.equal(field.selectionStart,7);assert.equal(field.selectionEnd,11);
   assert.equal(f.loads.filter(url=>url==='data/assistant.json').length,options.failConfig?3:2);
   assert(f.requests.every(r=>r.url.endsWith('/interpret')),'Configuration recovery cannot ask or save');
   f.requests[0].resolve(await response());await until(()=>f.app.getSnapshot().stage==='review','Recovered interpretation did not advance');
   assert.equal(f.app.getSnapshot().draft.source.text,raw);assert.equal(f.app.getSnapshot().confirmed,null);
  }finally{f.destroy();}
 }
 for(const action of ['edit','escape','destroy']){
  const f=await fixture({failConfig:true,delayConfigAfterFailure:true});try{
   f.submit();assert(f.app.getSnapshot().interpreting);assert.equal(f.requests.length,0);
   if(action==='edit')edit(f,'Changed while configuration retry is pending');else if(action==='escape')cancel(f);else f.destroy();
   f.releaseConfig();await turn();await turn();assert.equal(f.requests.length,0,'Cancelled config recovery cannot submit interpretation');
   assert.equal(f.app.getSnapshot().draft,null);if(action!=='destroy')assert.equal(f.app.getSnapshot().stage,'input');
  }finally{f.destroy();}
 }
}
async function registryIndependentReview(){
 const f=await fixture({delayRegistry:true});try{f.submit();await until(()=>f.requests.length===1,'Slow registry blocked interpretation');f.requests[0].resolve(await response());await until(()=>f.app.getSnapshot().stage==='review','Slow registry blocked review');answer(f,'decipher');assert(f.doc.getElementById('confirm').disabled);f.doc.getElementById('confirm').fire('click');assert.equal(f.requests.length,1);assert.equal(f.app.getSnapshot().confirmed,null);f.releaseRegistry();await f.app.ready;assert(!f.doc.getElementById('confirm').disabled);assert.equal(f.requests.length,1);}finally{f.destroy();}
}
(async()=>{await accepted();await ambiguity();await tinyAmbiguity();await failures();await stale();await entryAndReadiness();await configRetry();await registryIndependentReview();console.log('PASS single-input interpretation: editable pending form/caret, inline failures and regular retry, exact tiny grammar, no unverified fallback, binding/key/scope validation, edit/Escape/stale/destroy/config/import guards; no automatic comparison/save.');})().catch(error=>{console.error(error);process.exitCode=1;});
