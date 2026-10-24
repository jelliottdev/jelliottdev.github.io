'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const C=require('../claim-specification.js'),H=require('../claim-share.js'),R=require('../claim-research.js'),Search=require('../assistant-search.js');
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
const make=(extra={})=>C.confirm(C.createDraft({source:{text:'Use these fixed numeric keys.'},aim:known({outcomeId:'decipher',detail:'Read a page'}),method:known({operations:[{id:'numeric_keystream',label:'Numeric keys with conditional skips',generator:'Fibonacci',modulus:29,maxConsecutiveSkips:3}]}),scope:known({pages:['lp2-15']}),...extra}),{id:'fixture',at:'2026-10-24T00:00:00Z'});
let count=0;async function test(name,fn){await fn();count++;console.log('PASS '+name);}
(async()=>{
 await test('browser UMD and Node expose the same pure request contract',()=>{
  const env={ClaimSpecification:C,ClaimShare:H,TextEncoder,TextDecoder,btoa,atob,crypto};vm.runInNewContext(fs.readFileSync(require.resolve('../claim-research.js'),'utf8'),env);
  assert.equal(env.ClaimResearch.VERSION,1);assert.equal(typeof env.ClaimResearch.prepare,'function');
 });
 await test('one canonical request derives exact order/params, scope prose/holes, aim detail and unknown rules',()=>{
  const s=make({method:known({operations:[{id:'vigenere',label:'Vigenere',key:'FOO',reset:'page'},{id:'atbash',label:'Atbash',offset:3}]}),scope:known({pages:['lp2-15','lp2-17'],description:'Only lines 2–3'}),rules:{wordBoundaries:known('preserve')}}),p=R.prepare(s);
  assert.deepEqual(Object.keys(p.request).sort(),['card','originalIdea','version']);assert.equal(p.request.originalIdea,s.source.text);
  assert(p.confirmedQuery.includes('Only lines 2–3'));assert(p.confirmedQuery.includes('"pages":["lp2-15","lp2-17"]'));assert(p.confirmedQuery.includes('"searchBounds":{"status":"unspecified"}'));assert(p.confirmedQuery.includes('Read a page'));
  assert(p.confirmedQuery.indexOf('"id":"vigenere"')<p.confirmedQuery.indexOf('"id":"atbash"'));assert(p.confirmedQuery.includes('"key":"FOO"'));assert(p.query.includes('FOO'));assert(p.query.includes('page'));assert(p.query.includes('3'));
  assert(!p.query.includes('outcomeId'));assert(!p.query.includes('unspecified'));assert(!p.query.includes('Decipher the text'));assert.deepEqual(p.pages,['lp2-15','lp2-17']);
  assert(p.confirmedQuery.includes('Unresolved constraints (not executed rules): []'));
  assert.deepEqual(R.validate(p.request).request,p.request);assert.equal(p.snapshot.execution,'not_run');
 });
 await test('full75page hints survive and never fill a hole; exact empty/unknown scopes stay distinct',()=>{
  const pages=[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))];
  const p=R.prepare(make({scope:known({pages})}));assert.equal(p.pages.length,75);assert.deepEqual(p.pages,pages);
  assert.deepEqual(R.prepare(make({scope:known({pages:['lp2-15','lp2-17']})})).pages,['lp2-15','lp2-17']);
  const empty=R.prepare(make({scope:known({pages:[]})})),unknown=R.prepare(make({scope:C.field()}));assert.deepEqual(empty.pages,[]);assert.deepEqual(unknown.pages,[]);assert.notDeepEqual(empty.request.card.scope,unknown.request.card.scope);
 });
 await test('structured method parameters fix the demonstrated numeric-generator retrieval loss on real records',()=>{
  const docs=Search.experimentDocs(JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8')).records),a=make(),b=make({method:known({operations:[{id:'numeric_keystream',label:'Numeric keys with conditional skips',generator:'prime numbers',modulus:29,maxConsecutiveSkips:3}]})});
  assert.equal(C.retrievalQuery(a).query,C.retrievalQuery(b).query,'Old display-only ranking loses generator');
  const pa=R.prepare(a),pb=R.prepare(b);assert.notEqual(pa.query,pb.query);assert(pa.query.includes('Fibonacci'));assert(pb.query.includes('prime numbers'));
  assert.equal(Search.select(docs,pa.query,pa.pages)[0].id,'fibonacci-stream-skip-grid');
  assert.equal(Search.select(docs,C.retrievalQuery(a).query,['lp2-15'])[0].id,'numeric-stream-skip-grid');
 });
 await test('page hints do not flood lexical ranking or erase literal method parameters',()=>{
  const pages=Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'));
  const prepared=R.prepare(make({scope:known({pages}),method:known({operations:[{id:'vigenere',label:'Vigenere',key:'LP2-15'}]})}));
  assert.deepEqual(prepared.pages,pages);assert(prepared.query.includes('LP2-15'),'A literal key that looks like a page ID remains exact');
  assert(!prepared.query.includes('LP2-57'),'Scope page IDs travel as hints, not repetitive keyword text');
  assert(prepared.confirmedQuery.includes('lp2-57'),'Full scope remains in comparison context');
 });
 await test('binding canonicalizes member order and changes for exact meaningful card or original wording',async()=>{
  const p=R.prepare(make()),hash=await R.binding(p.request);assert.match(hash,/^[a-f0-9]{64}$/);
  const reordered=JSON.parse(C.serialize(p.request));assert.equal(await R.binding(reordered),hash);
  for(const mutate of [r=>r.card.method.value.operations[0].generator='prime numbers',r=>r.card.scope.value.pages=['lp2-17'],r=>r.card.rules.reset={status:'unrestricted'},r=>r.card.outcome.value.detail='Recover the whole page',r=>r.originalIdea+=' Extra supplied detail.']){
   const r=JSON.parse(JSON.stringify(p.request));mutate(r);assert.notEqual(await R.binding(r),hash);
  }
 });
 await test('shared-link import has no fabricated original human wording or retained history/results',()=>{
  const shared=H.decode(H.encode(make())).draft,confirmed=C.confirm(shared,{id:'recipient',at:'2026-10-24T00:00:00Z'}),p=R.prepare(confirmed);
  assert(!Object.hasOwn(p.request,'originalIdea'));assert(p.confirmedQuery.includes('original human wording was not supplied'));
  assert(!JSON.stringify(p.request).includes('methodEdits'));assert(!JSON.stringify(p.request).includes('confirmation'));assert(!JSON.stringify(p.request).includes('research-result'));
 });
 await test('request rejects separate spoofable queries/pages, missing methods, invalid cards and every size overflow',()=>{
  const p=R.prepare(make());
  for(const extra of [{query:'different idea'},{confirmedQuery:'override'},{pages:['lp2-43']},{version:2}])assert.throws(()=>R.validate({...p.request,...extra}));
  assert.throws(()=>R.prepare(make({method:C.field()})),e=>e.code==='needs-clarification');
  const bad=JSON.parse(JSON.stringify(p.request));bad.card.scope.value.pages=['lp2-99'];assert.throws(()=>R.validate(bad),e=>e.code==='invalid-card');
  assert.throws(()=>R.validate({...p.request,originalIdea:'x'.repeat(8001)}),e=>e.code==='original-too-long');
  assert.throws(()=>R.validate({...p.request,originalIdea:'x'.repeat(5500)}),e=>e.code==='context-too-long');
  assert.throws(()=>R.prepare(make({method:known({operations:[{id:'vigenere',label:'Vigenere',key:'x'.repeat(1600)}]})})),e=>e.code==='query-too-long');
  const huge=JSON.parse(JSON.stringify(p.request));huge.card.scope.value.description='x'.repeat(12000);assert.throws(()=>R.validate(huge),e=>e.code==='invalid-card');
  const contextCard=JSON.parse(JSON.stringify(p.request));contextCard.card.method.value.operations[0].key='x'.repeat(1100);contextCard.originalIdea='中'.repeat(8000);assert.throws(()=>R.validate(contextCard),e=>['body-too-long','context-too-long'].includes(e.code));
  assert.throws(()=>R.validate({...p.request,originalIdea:null}),e=>e.code==='original-too-long');
  let touched=false;const getter={version:1};Object.defineProperty(getter,'card',{enumerable:true,get(){touched=true;return p.request.card;}});assert.throws(()=>R.validate(getter),e=>e.code==='invalid-request');assert.equal(touched,false);
  const arrayGetter=JSON.parse(JSON.stringify(p.request));Object.defineProperty(arrayGetter.card.method.value.operations,'0',{get(){touched=true;return {};}});assert.throws(()=>R.validate(arrayGetter),e=>e.code==='invalid-card');assert.equal(touched,false);
  assert.throws(()=>R.prepare(make({unresolved:[{kind:'custom',text:'Preserve this unresolved constraint'}]})),e=>e.code==='needs-clarification','Existing model policy blocks nonempty unresolved; never silently omit it');
 });
 console.log('PASS '+count+' claim-research groups; real registry retrieval, no hosted AI/network/deployment.');
})().catch(e=>{console.error(e);process.exitCode=1;});
