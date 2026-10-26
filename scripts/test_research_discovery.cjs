'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto,createHash}=require('node:crypto');
const D=require('../research-discovery.js'),B=require('../research-browser-model.js'),I=require('../research-index.js'),F=require('../record-followup-view.js'),H=require('../research-help.js'),W=require('../research-work.js'),Runtime=require('../research-help-runtime.js');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=b=>createHash('sha256').update(b).digest('hex'),clone=v=>structuredClone(v),tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 const index=read('data/experiment-index.json'),registry=read('data/experiments.json'),map=read('data/research-map.json'),before=JSON.stringify(index),full=B.build(map,registry),thin=B.build(map,index);
 assert.deepEqual(thin.views,full.views,'Graph and List retain every exact branch, leaf, label and member');
 for(const record of registry.records){
  const r=thin.records[record.id];assert(D.isRecord(r));assert.equal(F.available(r).length,0,'Discovery never masquerades as a full executable declaration');
  for(const key of ['finding','limitations','scope','reader_title','reader_intro','reader_test','reader_question','reader_finding','reader_limit','research_questions','next_steps','record_type','method_topics','family'])assert.deepEqual(r[key],full.records[record.id][key],record.id+': '+key);
  assert.deepEqual(D.available(r).map(x=>x.id),F.available(record).map(x=>x.id));assert.deepEqual(W.describe(r),W.describe(full.records[record.id]));
 }
 assert.deepEqual(H.choices(thin.records).map(g=>[g.record.id,g.checks.map(c=>c.id)]),H.choices(full.records).map(g=>[g.record.id,g.checks.map(c=>c.id)]));
 for(const query of ['','key','LP2-15','autokey','word boundaries','Welsh','spiral','DEOR'])for(const sort of ['title','title-desc','recent']){
  const state=I.state(new URLSearchParams({q:query,sort})),ids=data=>I.select(Object.values(data.records),state).allRecords.map(r=>r.id);assert.deepEqual(ids(thin),ids(full),query+'/'+sort);
 }
 assert.equal(JSON.stringify(index),before);assert(fs.statSync('data/experiment-index.json').size<fs.statSync('data/experiments.json').size*.35);
 console.log('PASS all335 record facts, navigation, authored follow-up availability and search/sort parity with no executable controls in discovery');
 let reads=0;const store=D.createStore({crypto:webcrypto,fetcher:async path=>{reads++;assert(!path.includes('experiments.json'));return new Response(fs.readFileSync(path));}});
 assert.equal(reads,0);const record=thin.records['lp2-panel-prime-openings'],checks=D.available(record);
 const [a,b]=await Promise.all([store.hydrate({record,check:checks[0]}),store.hydrate({record,check:checks[1]})]);
 assert.equal(reads,1,'One exact record shared across checks');assert.equal(a.check.kind,'finite-settings');assert.equal(a.check.control.members.length,32);assert.equal(b.check.control.members.length,32);assert.equal(D.isRecord(a.record),false);
 assert.deepEqual(F.available(a.record).map(r=>r.id),checks.map(r=>r.id));assert.equal((await store.load(record)).id,record.id);assert.equal(reads,1);
 const corrupt=clone(record);corrupt.record_source.sha256='0'.repeat(64);await assert.rejects(store.load(corrupt),/changed/);
 await assert.rejects(store.hydrate({record,check:{...checks[0],title:'Changed'}}),/summary/);
 const extra=clone(record);extra.followup_discovery.items[0].card={};assert.deepEqual(D.items(extra),[]);assert.deepEqual(F.available(extra),[]);
 for(const path of ['../outside.json','https://other.example/record.json','reference/experiments/other.json']){const bad=clone(index);bad.records[0].record_source.path=path;assert.throws(()=>D.normalize(bad));}
 console.log('PASS selected-only bounded hydration, exact bytes, shared record cache, descriptor mismatch and path rejection');
 let tries=0;const failing=D.createStore({crypto:webcrypto,fetcher:async path=>++tries===1?new Response('{}'):new Response(fs.readFileSync(path))});await assert.rejects(failing.load(record));assert.equal((await failing.load(record)).id,record.id);assert.equal(tries,2,'Failed fetch can be retried');failing.destroy();
 const oversized=D.createStore({crypto:webcrypto,maxBytes:8,fetcher:async()=>new Response('0123456789')});await assert.rejects(oversized.load(record),/size/);oversized.destroy();
 const stale=clone(record),bytes=Buffer.from(JSON.stringify({...a.record,id:'wrong'}));stale.record_source.sha256=sha(bytes);const mismatch=D.createStore({crypto:webcrypto,fetcher:async()=>new Response(bytes)});await assert.rejects(mismatch.load(stale),/summary/);mismatch.destroy();
 const releases=[];let loads=0;const delayed=D.createStore({crypto:webcrypto,fetcher:()=>{loads++;return new Promise(r=>{releases.push(r);});}}),first=delayed.load(record).catch(e=>e),second=delayed.load(thin.records['lp2-known-vigenere-keys']).catch(e=>e),third=delayed.load(thin.records['word-internal-affine-lags']).catch(e=>e);
 assert.equal(loads,2,'At most two full-record requests');delayed.destroy();releases[0](new Response(fs.readFileSync('reference/experiments/lp2-panel-prime-openings.json')));releases[1](new Response(fs.readFileSync('reference/experiments/lp2-known-vigenere-keys.json')));assert((await third) instanceof Error);assert((await second) instanceof Error);assert((await first) instanceof Error);
 // Settle the other in-flight request without allowing a stale selection to create a controller.
 let releaseHydration,created=0;const states=[],runtime=Runtime.create({hydrate:()=>new Promise(r=>releaseHydration=r),load:async()=>({createController(){created++;throw Error('Detached selection reached execution tools');}})}),controller=runtime.createReadiness({record,check:checks[0],onState:s=>states.push(s)}),pending=controller.activate();await tick();controller.destroy();releaseHydration(a);await pending;assert.equal(created,0);assert.deepEqual(states.map(s=>s.state),['loading']);runtime.destroy();
 let selected;const active=Runtime.create({hydrate:selection=>store.hydrate(selection),load:async flags=>{assert.deepEqual(flags,{finite:true,language:true});return {createController(args){selected=args;return {activate:async()=>({state:'remaining'}),retry:async()=>({state:'remaining'}),destroy(){}};}};}});await active.createReadiness({record,check:checks[0],onState(){}}).activate();assert.equal(selected.record.id,record.id);assert(selected.check.control.members.length===32);active.destroy();store.destroy();
 console.log('PASS retry, oversize/wrong-record rejection, two-request limit, closed chooser cancellation and full controls before readiness');
 const source=fs.readFileSync('research-browser.js','utf8'),html=fs.readFileSync('research.html','utf8');assert(source.includes("['data/research-map.json','data/experiment-index.json']"));assert(!source.includes("'data/experiments.json'"));assert(source.includes('previewGeneration!==generation'));assert(html.indexOf('research-discovery.js')<html.indexOf('research-browser-model.js'));
 console.log('PASS production map bootstrap uses discovery only and selected-preview completion is guarded against stale navigation');
})().catch(e=>{console.error(e);process.exitCode=1;});
