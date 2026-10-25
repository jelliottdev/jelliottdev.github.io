'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const registry=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/experiments.json'),'utf8'));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['test source']});
const card=C.confirm(C.createDraft({source:{text:'PRIVATE ORIGINAL PROMPT'},aim:known('Find readable text'),method:known({operations:[{id:'vigenere',label:'Vigenere with key ABC',key:'ABC',offset:7}]}),scope:known({pages:['lp2-15','lp2-17'],description:'Only lines 2–3'})}),{id:'private-confirmation',at:'2026-10-24T12:00:00Z'});
const decode=text=>text.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
class Element{
 constructor(id,doc,markup=''){this.id=id;this.doc=doc;this.listeners={};this.html='';this.textContent='';this.hidden=/\shidden(?:\s|>)/.test(markup);this.disabled=/\sdisabled(?:\s|>)/.test(markup);this.value=decode(markup.match(/\bvalue="([^"]*)"/)?.[1]||markup.match(/<textarea[^>]*>([\s\S]*?)<\/textarea>/)?.[1]||'');this.selectionStart=this.selectionEnd=0;}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){this.doc.activeElement=this;}
 setSelectionRange(start,end){this.selectionStart=start;this.selectionEnd=end;}
 set innerHTML(text){this.html=text;if(this.id==='investigate'){this.doc.cache.clear();this.doc.preview={open:false};}}
 get innerHTML(){return this.html;}
 insertAdjacentHTML(where,text){this.html+=text;}
 replaceChildren(){this.html='';}
 remove(){}
}
function document(){
 const doc={cache:new Map(),activeElement:null,preview:{open:false},defaultView:{location:{search:'',hash:H.encode(card)}}};
 doc.host=new Element('investigate',doc);doc.print=new Element('print-snapshot',doc);
 doc.getElementById=id=>{
  if(id==='investigate')return doc.host;if(id==='print-snapshot')return doc.print;
  const pattern=new RegExp('<([a-z]+)\\b[^>]*\\bid="'+id+'"[^>]*>(?:[\\s\\S]*?<\\/\\1>)?','i'),markup=doc.host.html.match(pattern)?.[0];
  if(!markup)return null;if(!doc.cache.has(id))doc.cache.set(id,new Element(id,doc,markup));return doc.cache.get(id);
 };
 doc.querySelector=selector=>selector==='input[name=choice]:checked'?(doc.selectedChoice?{value:doc.selectedChoice}:null):selector==='.confirmed-card>.confirmed'?doc.preview:selector.startsWith('#')?doc.getElementById(selector.slice(1)):null;
 return doc;
}
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function setup(enabled=true,shared=true){
 const doc=document(),requests=[],research=[],timers=[];let serial=0;
 if(!shared)doc.defaultView.location.hash='';
 const app=I.createApp(doc,{id:()=>`00000000-0000-4000-8000-${String(++serial).padStart(12,'0')}`,renderCard:async()=>new Blob(['PNG']),schedule:fn=>{timers.push(fn);return timers.length-1;},unschedule:()=>{},fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',interpretationEndpoint:'https://mock.example/interpret',...(enabled?{proposalEndpoint:'https://mock.example/proposals'}:{})});
  if(url==='https://mock.example/interpret')return require('./mock_interpretation_response.cjs')(options);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  return new Promise(resolve=>(url.endsWith('/proposals')?requests:research).push({resolve,options}));
 }});
 await app.ready;
 assert.equal(requests.length,0);assert.equal(research.length,0,'Viewing the page or imported card never submits');
 if(!shared){
  doc.getElementById('idea').value='Use Vigenere with key ABC on LP2-15';doc.getElementById('intake').fire('submit');
  await require('./mock_interpretation_response.cjs').waitForReview(app);
  doc.selectedChoice='decipher';doc.getElementById('clarification').fire('submit');doc.selectedChoice=null;
 }
 assert.equal(I.intakeQuestions(app.getSnapshot().draft)[0].id,'evaluation');assert.equal(doc.getElementById('confirm'),null,'Deciphering intent alone cannot choose a criterion');
 const aimBefore=C.serialize(app.getSnapshot().draft.aim);doc.selectedChoice='inspect-output';doc.getElementById('clarification').fire('submit');doc.selectedChoice=null;assert.equal(app.getSnapshot().draft.rules.evaluation.value,'measurement');assert.equal(C.serialize(app.getSnapshot().draft.aim),aimBefore,'The explicit inspection criterion does not rewrite the aim');
 assert.equal(app.getSnapshot().stage,'review');assert.equal(requests.length,0,'Review is not confirmation');
 assert.equal(doc.getElementById('confirm').disabled,false,'Wait for actual registry/config readiness');
 assert.equal(doc.getElementById('collection-notice').hidden,!enabled,'Collection notice appears only when saving is configured, including a late config on imported review');
 doc.getElementById('confirm').fire('click');for(let i=0;i<3;i++)await turn();
 return {doc,app,requests,research,timers};
}
const receipt=status=>({id:'p_'+'a'.repeat(64),status,receivedAt:'2026-10-24T12:30:00Z'});
const turns=async()=>{await turn();await turn();};
(async()=>{
 const absent=await setup(false);assert.equal(absent.requests.length,0);assert.equal(absent.doc.getElementById('idea-save-status'),null);absent.app.destroy();
 const {doc,app,requests,research}=await setup(true,false);
 assert.equal(requests.length,1,'Explicit confirmation saves once');
 assert.equal(doc.getElementById('suggest-test'),null);assert.equal(doc.getElementById('proposal-panel'),null);assert.equal(doc.getElementById('send-proposal'),null,'No separate contribution form remains');
 const body=JSON.parse(requests[0].options.body);assert.deepEqual(Object.keys(body).sort(),['fragment','originalIdea','requestId']);
 assert.equal(body.originalIdea,'Use Vigenere with key ABC on LP2-15');assert.match(body.requestId,/^[a-f0-9-]{36}$/);
 const imported=H.decode(body.fragment).draft;assert.equal(imported.method.value.operations[0].label,body.originalIdea);assert.deepEqual(imported.scope.value.pages,['lp2-15']);
 research[0].resolve(Response.json({answer:null,sources:[],reason:'no-matching-records'}));for(let i=0;i<4;i++)await turn();assert.equal(requests.length,1,'Research completion does not save again');
 for(const code of [400,409,429,503]){
  requests.at(-1).resolve(Response.json({error:'Unavailable'},{status:code}));await turns();assert(doc.getElementById('idea-save-status')?.textContent==='Couldn’t save this idea.');assert(doc.getElementById('retry-save'));
  doc.getElementById('retry-save').fire('click');await turn();assert.deepEqual(JSON.parse(requests.at(-1).options.body),body,'Retries preserve the exact card, source wording and ID');
 }
 requests.at(-1).resolve(Response.json(receipt('already_received')));await turns();assert(doc.getElementById('idea-save-status')?.textContent==='Saved.');assert.equal(doc.getElementById('retry-save').hidden,true);
 assert(!/queued|new idea/i.test(doc.host.html),'A save receipt is not a novelty or queue classification');
 app.destroy();
 const shared=await setup();assert.equal(shared.requests.length,1);const sharedBody=JSON.parse(shared.requests[0].options.body);assert.deepEqual(Object.keys(sharedBody).sort(),['fragment','requestId']);assert(!JSON.stringify(sharedBody).includes('PRIVATE ORIGINAL'));
 const pending=shared.requests[0];shared.doc.getElementById('edit').fire('click');assert(pending.options.signal.aborted);pending.resolve(Response.json(receipt('received')));await turns();assert.equal(shared.doc.getElementById('idea-save-status'),null,'An older card cannot show a receipt while editing');
 shared.doc.getElementById('cancel-edit').fire('click');assert.notEqual(shared.doc.getElementById('idea-save-status')?.textContent,'Saved.');shared.app.destroy();
 const timed=await setup();const timeoutBody=JSON.parse(timed.requests[0].options.body);timed.timers[0]();assert(timed.requests[0].options.signal.aborted);timed.requests[0].resolve(Response.json(receipt('received')));await turns();assert(timed.doc.getElementById('idea-save-status')?.textContent==='Couldn’t save this idea.');
 timed.doc.getElementById('retry-save').fire('click');await turn();assert.deepEqual(JSON.parse(timed.requests[1].options.body),timeoutBody);timed.requests[1].resolve(Response.json(receipt('received')));await turns();assert(timed.doc.getElementById('idea-save-status')?.textContent==='Saved.');timed.app.destroy();
 const back=await setup();back.doc.getElementById('back').fire('click');assert(back.requests[0].options.signal.aborted);back.requests[0].resolve(Response.json(receipt('received')));await turns();assert.equal(back.app.getSnapshot().stage,'input');assert.equal(back.doc.getElementById('idea-save-status'),null);back.app.destroy();
 console.log('PASS confirmed-idea intake UI: explicit check only; no contribution form; exact active card + original human wording; imported summaries excluded; no AI results/history; endpoint-missing hidden; idempotent retries; saved-only receipt; error/timeout/edit/back races.');
})().catch(error=>{console.error(error);process.exitCode=1;});
