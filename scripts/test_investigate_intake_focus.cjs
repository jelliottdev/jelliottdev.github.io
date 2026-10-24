'use strict';
// Production createApp with a DOM lifecycle fixture. No browser or network calls.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
const card=C.confirm(C.createDraft({source:{text:'Use a fixed Vigenere key on LP2-15'},aim:known('Find readable text'),method:known({operations:[{id:'vigenere',label:'Vigenere with key ABC',key:'ABC'}]}),scope:known({pages:['lp2-15']})}),{id:'fixture',at:'2026-10-24T12:00:00Z'});
const unescape=text=>text.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
class Element{
 constructor(doc,id='',markup=''){this.doc=doc;this.id=id;this.markup=markup;this.html='';this.listeners={};this.isConnected=true;this.disabled=/\sdisabled(?:\s|>)/.test(markup);this.hidden=/\shidden(?:\s|>)/.test(markup);this.value=unescape(markup.match(/\bvalue="([^"]*)"/)?.[1]||markup.match(/<textarea[^>]*>([\s\S]*?)<\/textarea>/)?.[1]||'');this.textContent='';this.selectionStart=this.selectionEnd=0;this.dataset={};}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(options){if(this.id==='edit'&&this.doc.requireVisibleEditFocus)assert(this.doc.details.find(d=>d.summary.textContent==='Your idea').open,'Open the disclosure before restoring focus to its action');this.focusOptions=options;this.doc.activeElement=this;}
 setSelectionRange(start,end){this.selectionStart=start;this.selectionEnd=end;}
 contains(node){return this.id==='investigate'?node?.isConnected&&node!==this.doc.body:false;}
 querySelectorAll(selector){if(selector==='details')return this.doc.details;if(selector==='summary')return this.doc.details.map(d=>d.summary);return [];}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
 set innerHTML(text){
  this.html=text;if(this.id!=='investigate')return;
  for(const node of [...this.doc.cache.values(),...this.doc.details.flatMap(d=>[d,d.summary])])node.isConnected=false;
  this.doc.cache.clear();this.doc.activeElement=this.doc.body;
  this.doc.details=[...text.matchAll(/<details\b([^>]*)>([\s\S]*?)<\/details>/g)].map(match=>{
   const detail=new Element(this.doc);detail.open=/\bopen\b/.test(match[1]);detail.className=match[1].match(/class="([^"]*)"/)?.[1]||'';
   detail.summary=new Element(this.doc);detail.summary.tagName='SUMMARY';detail.summary.textContent=unescape(match[2].match(/<summary[^>]*>([\s\S]*?)<\/summary>/)?.[1].replace(/<[^>]+>/g,'')||'');detail.querySelector=selector=>['summary',':scope > summary'].includes(selector)?detail.summary:null;
   detail.summary.closest=selector=>selector==='details'?detail:null;return detail;
  });
 }
 get innerHTML(){return this.html;}
 insertAdjacentHTML(_,text){this.html+=text;}
 replaceChildren(){this.html='';}
 remove(){this.isConnected=false;}
}
function makeDocument(){
 const doc={cache:new Map(),details:[],defaultView:{location:{search:'',hash:H.encode(card)}}};doc.body=new Element(doc,'body');doc.activeElement=doc.body;doc.host=new Element(doc,'investigate');doc.print=new Element(doc,'print-snapshot');
 doc.getElementById=id=>{
  if(id==='investigate')return doc.host;if(id==='print-snapshot')return doc.print;
  const live=doc.host.html+[...doc.cache.values()].filter(node=>node.isConnected).map(node=>node.html).join('');
  const markup=live.match(new RegExp('<([a-z][a-z0-9]*)\\b[^>]*\\bid="'+id+'"[^>]*>(?:[\\s\\S]*?<\\/\\1>)?','i'))?.[0];if(!markup)return null;
  if(!doc.cache.has(id))doc.cache.set(id,new Element(doc,id,markup));return doc.cache.get(id);
 };
 doc.querySelector=selector=>selector==='.confirmed-card>.confirmed'?doc.details.find(d=>d.className.split(' ').includes('confirmed')):selector.startsWith('#')?doc.getElementById(selector.slice(1)):null;
 return doc;
}
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function fixture(){
 const doc=makeDocument(),saves=[],research=[];
 const app=I.createApp(doc,{id:()=>crypto.randomUUID(),renderCard:async()=>new Blob(['PNG']),sharer:async()=>({status:'copied',url:'https://example.org/investigate.html#idea=sample'}),fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals'});
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  return new Promise((resolve,reject)=>{(url.endsWith('/proposals')?saves:research).push({resolve,options});options.signal.addEventListener('abort',()=>reject(Object.assign(Error('Aborted'),{name:'AbortError'})),{once:true});});
 }});
 await app.ready;doc.getElementById('confirm').focus();doc.getElementById('confirm').fire('click');
 assert.equal(doc.activeElement,doc.getElementById('review-title'),'Confirmation focuses the research heading before the deferred comparison completes');
 await turn();return {doc,app,saves,research};
}
async function run(kind){
 const {doc,app,saves,research}=await fixture();
 const idea=doc.details.find(d=>d.summary.textContent==='Your idea');idea.open=true;idea.summary.focus();
 const original=doc.details.find(d=>d.summary.textContent==='Original idea');original.open=true;
 if(kind==='save')saves[0].resolve(Response.json({id:'p_'+'a'.repeat(64),status:'received',receivedAt:'2026-10-24T12:30:00Z'}));
 else research[0].resolve(Response.json({answer:null,sources:[],reason:'no-matching-records'}));
 await turn();await turn();
 const current=doc.details.find(d=>d.summary.textContent==='Your idea'),source=doc.details.find(d=>d.summary.textContent==='Original idea');
 const observed={ideaOpen:current.open,sourceOpen:source.open,focus:doc.activeElement===current.summary?'Your idea summary':doc.activeElement.id||'unidentified'};
 app.destroy();assert.equal(current.open,true,kind+' completion closed Your idea: '+JSON.stringify(observed));assert.equal(source.open,true,kind+' completion closed Original idea');assert.equal(doc.activeElement,current.summary,kind+' completion lost focused summary');
 if(kind==='save')assert.equal(current,idea,'Saving updates status without replacing the card node');
}
function tree(){
 const doc={activeElement:null},details=[];
 function add(label,parent,open){const detail=new Element(doc);detail.open=open;detail.parentElement={closest:()=>parent};detail.summary=new Element(doc);detail.summary.textContent=label;detail.querySelector=()=>detail.summary;details.push(detail);return detail;}
 const idea=add('Your idea',null,true);add('Files',idea,false);add('Files',idea,true);
 const original=add('Original idea',null,false);add('Files',original,true);
 return {doc,details,host:{querySelectorAll:()=>details}};
}
async function selectionAndStage(){
 const {doc,app,saves,research}=await fixture();
 await doc.getElementById('share-idea').fire('click');
 const field=doc.getElementById('share-link');field.focus();field.setSelectionRange(9,20);
 research[0].resolve(Response.json({answer:null,sources:[],reason:'no-matching-records'}));await turn();await turn();
 const replacement=doc.getElementById('share-link');assert.equal(doc.activeElement,replacement);assert.equal(replacement.selectionStart,9);assert.equal(replacement.selectionEnd,20);assert.deepEqual(replacement.focusOptions,{preventScroll:true});
 doc.getElementById('edit').fire('click');const method=doc.getElementById('edit-method');method.value='Unsaved exact method';method.focus();method.setSelectionRange(3,9);
 saves[0].resolve(Response.json({id:'p_'+'b'.repeat(64),status:'received',receivedAt:'2026-10-24T12:30:00Z'}));await turn();await turn();
 assert.equal(doc.getElementById('edit-method'),method);assert.equal(method.value,'Unsaved exact method');assert.equal(doc.activeElement,method);assert.equal(method.selectionStart,3);assert.equal(method.selectionEnd,9,'An older save cannot replace an editing textarea/caret');
 doc.getElementById('cancel-edit').fire('click');assert.equal(doc.details.find(d=>d.summary.textContent==='Your idea').open,false,'Disclosure state does not leak across an editing-stage transition');
 doc.details.find(d=>d.summary.textContent==='Your idea').open=true;doc.getElementById('back').fire('click');
 doc.getElementById('idea').value='Find readable text using Vigenere with key XYZ on LP2-17';doc.getElementById('intake').fire('submit');doc.getElementById('confirm').fire('click');
 assert.deepEqual(app.getSnapshot().confirmed.scope.value.pages,['lp2-17']);assert.equal(doc.details.find(d=>d.summary.textContent==='Your idea').open,false,'A different confirmed card gets its own initial disclosure state');
 app.destroy();
}
async function focusedAction(){
 const {doc,app,research}=await fixture();doc.details.find(d=>d.summary.textContent==='Your idea').open=true;doc.getElementById('edit').focus();doc.requireVisibleEditFocus=true;
 research[0].resolve(Response.json({answer:null,sources:[],reason:'no-matching-records'}));await turn();await turn();assert.equal(doc.activeElement,doc.getElementById('edit'));assert.deepEqual(doc.activeElement.focusOptions,{preventScroll:true});app.destroy();
}
async function comparisonTransitionFocus(){
 for(const response of [Response.json({answer:null,sources:[],reason:'no-matching-records'}),Response.json({error:'Unavailable'},{status:503})]){
  const {doc,app,research}=await fixture();
  assert.equal(app.getSnapshot().busy,true);assert.equal(doc.activeElement.id,'review-title');
  doc.getElementById('back').focus();
  research[0].resolve(response);await turn();await turn();
  assert.equal(app.getSnapshot().busy,false);
  assert.equal(doc.activeElement,doc.getElementById('back'),'A later answer or error must not pull focus back from the user’s chosen control');
  app.destroy();
 }
}
(async()=>{
 const before=tree(),states=I.captureDisclosureState(before.host,before.details[0].summary),after=tree();after.details.forEach(detail=>detail.open=!detail.open);I.restoreDisclosureState(after.host,states);
 assert.deepEqual(after.details.map(detail=>detail.open),[true,false,true,false,true],'Nested and repeated-label disclosure paths preserve both open and closed states');assert.equal(after.doc.activeElement,after.details[0].summary);assert.deepEqual(after.doc.activeElement.focusOptions,{preventScroll:true});
 const outside={id:'unrelated-control'};after.doc.activeElement=outside;I.restoreDisclosureState(after.host,I.captureDisclosureState(before.host,outside));assert.equal(after.doc.activeElement,outside,'No focused summary means no focus movement');
 const results=await Promise.allSettled([run('save'),run('research'),selectionAndStage(),focusedAction(),comparisonTransitionFocus()]);
 const failed=results.filter(r=>r.status==='rejected');if(failed.length)throw Error(failed.map(r=>r.reason.message).join('\n'));
 console.log('PASS incoming save/research: persistent save-status card, exact nested open/closed paths, focused summary without scroll, selected share link, untouched editing textarea/caret, and no state leak across stages.');
})().catch(error=>{console.error(error);process.exitCode=1;});
