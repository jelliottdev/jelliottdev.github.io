'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),I=require('../investigate.js'),W=require('../word-sum-intake.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),Compiler=require('../fixed-plan-compiler.js');
class Element{constructor(){this.listeners={};this.value='';this.html='';}addEventListener(t,fn){this.listeners[t]=fn;}fire(t){return this.listeners[t]?.({preventDefault(){},target:this});}focus(){}replaceChildren(){this.html='';}set innerHTML(v){this.html=v;this.onRender?.();}get innerHTML(){return this.html;}insertAdjacentHTML(_,v){this.html+=v;}}
function documentFixture(){const host=new Element(),cache=new Map();host.onRender=()=>cache.clear();return {host,selectedChoice:null,defaultView:{location:{hash:'',search:''}},getElementById(id){if(id==='investigate')return host;if(id==='print-snapshot')return new Element();if(!host.html.includes('id="'+id+'"'))return null;if(!cache.has(id))cache.set(id,new Element());return cache.get(id);},querySelector(s){return s==='input[name=choice]:checked'?(this.selectedChoice?{value:this.selectedChoice}:null):s.startsWith('#')?this.getElementById(s.slice(1)):null;}};}
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
async function fixture(){const doc=documentFixture(),calls=[],app=I.createApp(doc,{fetcher:async(url,options)=>{calls.push({url,method:options?.method||'GET'});assert(!options?.method||options.method==='GET','No interpretation or contribution request is allowed');if(url==='data/experiments.json')return Response.json(registry);if(url==='data/assistant.json')return Response.json({interpretationEndpoint:'https://forbidden.invalid/interpret'});return Response.json({documents:[]});}});await app.ready;return {doc,calls,app};}
function choose(f,value,text=''){f.doc.selectedChoice=value;f.doc.getElementById('other-detail').value=text;f.doc.getElementById('clarification').fire('submit');}
const aliases=[
 ['Sum each word using the usual GP prime table','canonical'],
 ['Add the usual GP prime values within each word','canonical'],
 ['Add standard gematria primus prime values in each word','canonical'],
 ['Use the reversed GP prime table and sum each word','reversed'],
 ['Sum the words using the reversed gematria prime table','reversed'],
 ['Use the reversed GP prime table (F=109, U=107\u2026) then sum words','reversed']
];
(async()=>{
 let flows=0;
 for(const [phrase,table]of aliases){const text=phrase+' on LP2-15, LP2-17';assert(W.matches(text),text);const f=await fixture();try{
  f.doc.getElementById('idea').value=text;f.doc.getElementById('intake').fire('submit');assert.equal(f.app.getSnapshot().stage,'review');assert.equal(f.app.getSnapshot().draft.source.text,text);
  choose(f,'decipher');let d=f.app.getSnapshot().draft;assert.deepEqual(d.scope.value.pages,['lp2-15','lp2-17']);assert.equal(I.intakeQuestions(d)[0].id,'word-sum-evaluation');assert.equal(d.rules.evaluation.status,'unspecified');assert.equal(f.doc.getElementById('confirm'),null);
  choose(f,'numeric-ledger');d=f.app.getSnapshot().draft;assert.equal(I.intakeQuestions(d)[0].id,'word-sum-boundaries');assert.equal(d.rules.evaluation.status,'unspecified');assert.equal(d.rules.representation.status,'unspecified');
  choose(f,'hyphen-period');d=f.app.getSnapshot().draft;assert.equal(d.source.text,text);assert.equal(C.normalizeOutcome(d.aim).id,'decipher');assert.deepEqual(d.scope.value.pages,['lp2-15','lp2-17']);const plan=Compiler.compile(H.cardData(C.confirm(d,{id:'private-alias-test',at:'2026-10-25T12:00:00Z'})));assert.deepEqual(plan.criterion,{kind:'word-prime-sums',table,boundaries:'hyphen-period'});assert.deepEqual(plan.steps,[]);assert.equal(f.app.getSnapshot().confirmed,null);assert(f.calls.every(c=>c.method==='GET'&&!c.url.includes('forbidden.invalid')));flows++;
 }finally{f.app.destroy();}}
 console.log('PASS '+flows+' source-bound alias event flows preserve original scope, explicit numeric consent, exact table, and no AI/save/run');
 for(const [phrase]of aliases)for(const tail of [' then reverse the totals',' except F',' and this proves the cipher','. I counted 137.',' only on odd words'])assert.equal(W.matches(phrase+' on LP2-15'+tail),false,phrase+tail);
 for(const phrase of ['Sum each word using the GP prime table','Use the reversed GP prime table (F=2, U=3) and sum each word','Use the usual GP prime table (F=109, U=107) and sum each word','Use the reversed GP prime table (F=109, U=3) and sum each word','Use the reversed GP prime table (F=109, U=107, EA=3) and sum each word','Sum each word using a custom GP prime table','Do not add the usual GP prime values within each word','Add the reversed GP prime values within each word'])assert.equal(W.matches(phrase),false,phrase);
 console.log('PASS compound claims, negation, unspecified/custom tables, and conflicting assignment examples remain opaque');
 const text=aliases[0][0]+' on LP2-15, LP2-17',d=I.initialDraft(text),field=v=>C.field('specified',v,{kind:'supplied',refs:['source']});d.aim=field('Measure totals');d.scope=field({pages:['lp2-15','lp2-16','lp2-17']});assert.equal(W.question(d),null);d.scope=field({pages:['lp2-15']});assert.equal(W.question(d),null);assert(!W.matches(aliases[0][0]+' on LP2-99'));assert(!W.matches(aliases[0][0]+' on LP2-15, lines 1-3'));
 console.log('PASS exact page-tail guard preserves holes and rejects partial or widened scope');
})().catch(error=>{console.error(error);process.exitCode=1;});
