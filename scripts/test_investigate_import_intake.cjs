'use strict';
// Real createApp import path; service writes and AI are forbidden before confirmation.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['original']});
class Element{
 constructor(){this.listeners={};this.html='';this.value='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){}replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;this.onRender?.();}get innerHTML(){return this.html;}
 insertAdjacentHTML(_,value){this.html+=value;}
}
function documentFor(hash){
 const host=new Element(),print=new Element(),cache=new Map();host.onRender=()=>cache.clear();
 const doc={host,selectedChoice:null,defaultView:{location:{search:'',hash}},getElementById(id){
  if(id==='investigate')return host;if(id==='print-snapshot')return print;
  if(!host.html.includes('id="'+id+'"'))return null;
  if(!cache.has(id))cache.set(id,new Element());return cache.get(id);
 },querySelector(selector){if(selector==='input[name=choice]:checked')return this.selectedChoice?{value:this.selectedChoice}:null;return selector.startsWith('#')?this.getElementById(selector.slice(1)):null;}};return doc;
}
function original(fields={}){return C.confirm(C.createDraft({source:{text:'Reverse the runes in each line.'},method:known({operations:[{id:'reverse_runes',label:'Reverse rune order within each line',unit:'line'}]}),rules:{inputVersion:known('raw'),evaluation:known('measurement')},...fields}),{id:'original',at:'2026-10-24T12:00:00Z'});}
async function fixture(card){
 const hash=H.encode(card),decoded=H.decode(hash).draft,doc=documentFor(hash),requests=[];
 const app=I.createApp(doc,{fetcher:async(url,options)=>{
  requests.push({url,method:options?.method||'GET'});
  if(options?.method==='POST'||url.includes('private.invalid'))throw Error('Unexpected AI/save/run');
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://private.invalid/ask',proposalEndpoint:'https://private.invalid/proposals',interpretationEndpoint:'https://private.invalid/interpret'});
  return Response.json({documents:[]});
 }});await app.ready;return {app,doc,decoded,requests};
}
function choose(f,value){f.doc.selectedChoice=value;f.doc.getElementById('clarification').fire('submit');}
(async()=>{
 const first=await fixture(original());
 assert.deepEqual(first.app.getSnapshot().draft,first.decoded,'Import preserves all decoded fields without fabricated clarification provenance');
 assert.deepEqual(I.intakeQuestions(first.app.getSnapshot().draft).map(q=>q.id),['aim','scope']);
 assert(first.doc.host.html.includes('What outcome are you looking for?'));assert.equal(first.doc.getElementById('confirm'),null);
 choose(first,'undecided');assert(first.doc.host.html.includes('Which material should this apply to?'));assert.equal(first.doc.getElementById('confirm'),null);
 assert.equal(first.app.getSnapshot().draft.clarifications.length,1);assert.equal(first.app.getSnapshot().draft.clarifications[0].question,'aim');
 choose(first,'undecided');assert.deepEqual(I.intakeQuestions(first.app.getSnapshot().draft),[]);assert(first.doc.getElementById('confirm'));
 assert.equal(first.app.getSnapshot().draft.aim.status,'unspecified');assert.equal(first.app.getSnapshot().draft.scope.status,'unspecified');
 assert.deepEqual(first.app.getSnapshot().draft.method,first.decoded.method);assert.deepEqual(first.app.getSnapshot().draft.rules,first.decoded.rules);assert.deepEqual(first.app.getSnapshot().draft.source,first.decoded.source);
 assert(first.requests.every(r=>r.method==='GET'&&!r.url.includes('private.invalid')));assert.equal(first.app.getSnapshot().confirmed,null);first.app.destroy();
 const complete=await fixture(original({aim:known('Find readable text'),scope:known({pages:['lp2-15']})}));
 assert.deepEqual(complete.app.getSnapshot().draft,complete.decoded);assert.deepEqual(I.intakeQuestions(complete.app.getSnapshot().draft),[]);assert(complete.doc.getElementById('confirm'));complete.app.destroy();
 for(const [fields,expected]of [[{aim:known('Find readable text')},'scope'],[{scope:known({pages:['lp2-15']})},'aim']]){
  const f=await fixture(original(fields));assert.deepEqual(I.intakeQuestions(f.app.getSnapshot().draft).map(q=>q.id),[expected]);assert.equal(f.doc.getElementById('confirm'),null);assert.deepEqual(f.app.getSnapshot().draft,f.decoded);f.app.destroy();
 }
 console.log('PASS imported intake: aim then scope; explicit undecided only after choice; supplied fields/source retained; no AI/save/run before confirmation; complete cards do not reask.');
})().catch(error=>{console.error(error);process.exitCode=1;});
