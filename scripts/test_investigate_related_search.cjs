'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),I=require('../investigate.js'),S=require('../assistant-search.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const fixtureSource=fs.readFileSync(require.resolve('./test_investigate_intake_focus.cjs'),'utf8');
const {makeDocument}=new Function('require',fixtureSource.slice(0,fixtureSource.indexOf('async function fixture()'))+'\nreturn {makeDocument};')(require);
const turn=()=>new Promise(r=>setImmediate(r));
async function settle(){await turn();await turn();}
async function fixture({config={},deferConfig=false,ask=null,session=null}={}){
 const doc=makeDocument(),requests=[];doc.defaultView.location.hash='';if(session)doc.defaultView.sessionStorage=session;
 let releaseConfig;
 const pendingConfig=new Promise(r=>{releaseConfig=r;});
 const app=I.createApp(doc,{fetcher:async(url,options={})=>{
  requests.push({url,options});
  if(url==='data/assistant.json')return deferConfig?pendingConfig:config===null?Response.json({}, {status:503}):Response.json(config);
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  if(url.endsWith('/ask')&&ask)return ask(options);
  if(url.endsWith('/interpret'))return Response.json({reason:'unavailable'},{status:503});
  throw Error('Unexpected request '+url);
 }});
 await app.ready;
 function submit(text){doc.getElementById('idea').value=text;doc.getElementById('intake').fire('submit');}
 function noWrites(){assert(!requests.some(r=>/\/(?:proposals|ideas|tasks|prepare-task|results)(?:$|[/?#])/.test(r.url)));}
 return {doc,app,requests,submit,noWrites,releaseConfig:()=>releaseConfig(Response.json(config)),destroy:()=>app.destroy()};
}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('rough question searches genuine local records without draft method aim scope confirmation or service',async()=>{
  const f=await fixture({config:null});try{
   const text='Could null runes be extra junk that we should remove?';f.submit(text);await settle();
   assert.equal(f.app.getSnapshot().stage,'search');assert.equal(f.app.getSnapshot().draft,null);assert.equal(f.app.getSnapshot().confirmed,null);
   assert.equal(f.doc.getElementById('idea').value,text);assert(f.doc.host.innerHTML.includes('Related research'));
   const docs=(S.related?S.related(S.experimentDocs(registry.records),text):S.select(S.experimentDocs(registry.records),text)).filter(d=>d.kind==='experiment');
   assert(docs.length);for(const d of docs)assert(f.doc.host.innerHTML.includes('library.html#/experiment/'+d.id));
   assert(!f.doc.getElementById('clarification'));assert(!f.doc.getElementById('confirm'));assert(f.doc.getElementById('define-test'));
   assert.equal(f.requests.filter(r=>r.options.method==='POST').length,0);f.noWrites();
  }finally{f.destroy();}
 });
 await test('configuration may remain stalled while local research is already usable',async()=>{
  const f=await fixture({deferConfig:true});try{f.submit('null runes');assert.equal(f.app.getSnapshot().stage,'search');assert(f.doc.host.innerHTML.includes('library.html#/experiment/'));f.noWrites();assert.equal(f.requests.filter(r=>r.options.method==='POST').length,0);}finally{f.destroy();f.releaseConfig();await settle();}
 });
 await test('long paste stays exact and searchable but optional test preparation explains its narrower bound',async()=>{
  const f=await fixture();try{const text='Discussion of null runes and possible interruptions.\n'.repeat(75);assert(text.length>1500&&text.length<8000);f.submit(text);await settle();assert.equal(f.doc.getElementById('idea').value,text);assert.equal(f.app.getSnapshot().stage,'search');assert(f.doc.host.innerHTML.includes('Related research'));f.doc.getElementById('define-test').fire('click');assert.equal(f.app.getSnapshot().stage,'search');assert.equal(f.doc.getElementById('idea').value,text);assert(f.doc.getElementById('interpretation-error').textContent.includes('1,500'));f.noWrites();}finally{f.destroy();}
 });
 await test('full rough paste survives reload as search rather than a falsely confirmed card',async()=>{
  const stored=new Map(),session={getItem:k=>stored.get(k)||null,setItem:(k,v)=>stored.set(k,v),removeItem:k=>stored.delete(k)},text='Long discussion about null runes and doublets.\n'.repeat(90);
  let f=await fixture({config:null,session});try{f.submit(text);await settle();assert.equal(f.doc.getElementById('idea').value,text);}finally{f.destroy();}
  f=await fixture({config:null,session});try{assert.equal(f.app.getSnapshot().stage,'search');assert.equal(f.app.getSnapshot().draft,null);assert.equal(f.app.getSnapshot().confirmed,null);assert.equal(f.doc.getElementById('idea').value,text);assert(f.doc.host.innerHTML.includes('Related research'));assert.equal(f.requests.filter(r=>r.options.method==='POST').length,0);f.noWrites();}finally{f.destroy();}
 });
 await test('remote related synthesis is optional exact raw query only and source bound; no experiment is created',async()=>{
  const docs=S.experimentDocs(registry.records),source=docs.find(d=>d.kind==='experiment');
  const f=await fixture({config:{endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals',researchIdeaEndpoint:'https://mock.example/ideas'},ask:async options=>{
   assert.deepEqual(JSON.parse(options.body),{kind:'related-research',query:'null runes'});
   return Response.json({comparisonKind:'related-research',answer:'This record discusses the topic [1].',sources:[source]});
  }});try{f.submit('null runes');await settle();assert(f.doc.host.innerHTML.includes('This record discusses the topic'));assert.equal(f.app.getSnapshot().confirmed,null);f.noWrites();assert.equal(f.requests.filter(r=>r.url.endsWith('/ask')).length,1);}finally{f.destroy();}
 });
 await test('AI errors and forged or stale replies cannot replace local results or open formal questions',async()=>{
  for(const failure of ['offline','forged','stale']){
   let resolve;const f=await fixture({config:{endpoint:'https://mock.example/ask'},ask:async()=>failure==='offline'?Response.json({}, {status:503}):failure==='forged'?Response.json({comparisonKind:'related-research',answer:'Untrusted claim [1].',sources:[{id:'invented',href:'https://evil.example',text:'fake'}]}):new Promise(r=>{resolve=r;})});
   try{f.submit('null runes');await settle();if(failure==='stale'){const input=f.doc.getElementById('idea');input.value='A different question';input.fire('input');resolve(Response.json({comparisonKind:'related-research',answer:'Stale answer [1].',sources:[S.experimentDocs(registry.records)[0]]}));await settle();assert.equal(f.doc.getElementById('idea').value,'A different question');assert(!f.doc.host.innerHTML.includes('Stale answer'));}else{assert(f.doc.host.innerHTML.includes('library.html#/experiment/'));assert(!f.doc.host.innerHTML.includes('Untrusted claim'));}assert.equal(f.app.getSnapshot().confirmed,null);assert(!f.doc.getElementById('clarification'));f.noWrites();}finally{f.destroy();}
  }
 });
 await test('a late valid summary preserves the editable text selection',async()=>{
  let resolve;const source=S.experimentDocs(registry.records).find(d=>d.kind==='experiment');
  const f=await fixture({config:{endpoint:'https://mock.example/ask'},ask:()=>new Promise(r=>{resolve=r;})});
  try{f.submit('null runes');await settle();const field=f.doc.getElementById('idea');field.focus();field.setSelectionRange(2,7);resolve(Response.json({comparisonKind:'related-research',answer:'A related record [1].',sources:[source]}));await settle();const restored=f.doc.getElementById('idea');assert.equal(f.doc.activeElement,restored);assert.equal(restored.value,'null runes');assert.equal(restored.selectionStart,2);assert.equal(restored.selectionEnd,7);f.noWrites();}finally{f.destroy();}
 });
 await test('only explicit Define a test enters existing formal clarification with original wording',async()=>{
  const f=await fixture();try{const text='Reverse prime values in rows';f.submit(text);assert.equal(f.app.getSnapshot().draft,null);f.doc.getElementById('define-test').fire('click');assert.equal(f.app.getSnapshot().stage,'review');assert.equal(f.app.getSnapshot().draft.source.text,text);assert(f.doc.getElementById('clarification'));assert.equal(f.app.getSnapshot().confirmed,null);f.noWrites();}finally{f.destroy();}
 });
 console.log(groups+' search-first entry groups passed; no target runner or public writes.');
})().catch(e=>{console.error(e);process.exitCode=1;});
