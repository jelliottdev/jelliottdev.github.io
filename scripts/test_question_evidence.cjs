/* Page aggregation uses verified receipts, never a fabricated whole-task result. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),E=require('../local-experiment.js'),Q=require('../question-evidence.js');
const fixture=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')),alphabet=fixture.alphabet,at='2026-10-25T12:00:00.000Z',criterion={kind:'word-affine-count',lag:2,a:1,b:0,boundaries:'non-rune'};
const hash=value=>crypto.createHash('sha256').update(E.stable(value)).digest('hex'),clone=value=>JSON.parse(JSON.stringify(value));
async function task({title='Requested question',pages=[{id:'lp2-00',text:'ᚠᚦᚠ ᚦᚩᚦ ᚦᚩᚠ-ᚠᚠᚠ'},{id:'lp2-01',text:'ᚦᚠᚠ ᚩᚢᚩ ᚩᚠᚩ-ᚩᚠᚠ'}],rules=criterion,letters=alphabet,steps=[]}={}){return E.prepare({title,pages,alphabet:letters,steps,criterion:rules});}
async function source(t,{version='raw',branded=false}={}){let result=E.run(t);if(branded)result=await E.verify(t,result);return {task:t,inputVersion:version,run:{id:hash(result),createdAt:at,result}};}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('disjoint differently titled sources aggregate exact per-page measurements and rational means',async()=>{
  const requested=await task(),sources=await Promise.all(requested.pages.map((page,i)=>task({title:'Independent batch '+i,pages:[page]}).then(source))),expected=E.run(requested).wordPairs,verify=E.verify;let calls=[];
  E.verify=async(t,...args)=>{calls.push(t.taskId);assert.notEqual(t.taskId,requested.taskId,'Do not rerun the requested whole plan');return verify(t,...args);};let actual;
  try{actual=await Q.summarize(requested,'raw',sources);}finally{E.verify=verify;}
  assert.equal(calls.length,2);assert.equal(actual.complete,true);assert.deepEqual(actual.remainingPages,[]);assert.deepEqual(actual.wordPairs,{opportunities:expected.opportunities,matches:expected.matches,expected:expected.expected});assert.equal(actual.scope,'covered-pages-only');assert.equal(actual.pages.length,2);assert.equal(actual.evidence.length,2);assert.equal(Q.inspect(actual),actual);assert(Object.isFrozen(actual.pages[0].source));assert.throws(()=>{actual.wordPairs.matches++;},TypeError);assert.throws(()=>Q.inspect(clone(actual)));assert.throws(()=>Q.inspect(Object.create(actual)));
  const original=actual.pages[0].matches;sources[0].run.result.wordPairs.pages[0].matches++;requested.pages[0].text+='ᚠ';assert.equal(actual.pages[0].matches,original);
 });
 await test('request and raw source snapshots cannot change while asynchronous validation is pending',async()=>{
  const requested=await task(),saved=await source(await task({title:'Captured mutable source'})),pending=Q.summarize(requested,'raw',[saved]);requested.pages[0].text+='ᚠ';saved.task.pages[0].text+='ᚢ';saved.run.result.wordPairs.matches++;saved.run.result.wordPairs.pages[0].matches++;saved.run.id='0'.repeat(64);
  const result=await pending;assert.equal(result.complete,true);assert.deepEqual(result.coveredPages,['lp2-00','lp2-01']);assert.notEqual(result.pages[0].source.resultId,saved.run.id);
 });
 await test('overlap contributes once, chooses deterministically, and branded results avoid a second replay',async()=>{
  const requested=await task(),a=await source(await task({title:'Overlapping source A'}),{branded:true}),b=await source(await task({title:'Overlapping source B'}),{branded:true}),verify=E.verify;
  E.verify=async()=>{throw Error('Verified frozen result must not replay');};let x,y;try{x=await Q.summarize(requested,'raw',[a,b]);y=await Q.summarize(requested,'raw',[b,a]);}finally{E.verify=verify;}
  assert.deepEqual(x,y);assert.equal(x.evidence.length,1);assert.equal(x.pages[0].source.taskId,[a.task.taskId,b.task.taskId].sort()[0]);assert.equal(x.wordPairs.opportunities,E.run(requested).wordPairs.opportunities);
 });
 await test('partial and empty aggregates explicitly describe covered pages only and cannot form a paired decision',async()=>{
  const requested=await task(),saved=await source(await task({pages:[requested.pages[0]]})),partial=await Q.summarize(requested,'raw',[saved]),empty=await Q.summarize(requested,'raw',[]);
  assert.equal(partial.complete,false);assert.deepEqual(partial.coveredPages,['lp2-00']);assert.deepEqual(partial.remainingPages,['lp2-01']);assert.deepEqual(partial.wordPairs,{opportunities:saved.run.result.wordPairs.opportunities,matches:saved.run.result.wordPairs.matches,expected:saved.run.result.wordPairs.expected});assert.deepEqual(empty.wordPairs,{opportunities:0,matches:0,expected:{numerator:'0',denominator:'1'}});assert.throws(()=>Q.paired(partial,empty),/complete/);
 });
 await test('different source version, exact bytes, alphabet and mathematical settings never supply coverage',async()=>{
  const requested=await task();
  for(const changed of [await source(await task(),{version:'reviewed'}),await source(await task({pages:requested.pages.map(p=>({...p,text:p.text+'ᚠ'}))})),await source(await task({rules:{...criterion,lag:1}})),await source(await task({rules:{...criterion,a:2}})),await source(await task({letters:alphabet.map((r,i)=>({...r,latin:i?'R'+i:'OTHER'}))}))]){const value=await Q.summarize(requested,'raw',[changed]);assert.equal(value.coveredPages.length,0);assert.equal(value.complete,false);}
 });
 await test('shape-consistent forged metrics and conflicting duplicate cases fail instead of supplying an answer',async()=>{
  const requested=await task(),saved=await source(await task({title:'Source forgery'})),forged=clone(saved);forged.run.result.wordPairs.matches++;forged.run.result.wordPairs.pages[0].matches++;forged.run.id=hash(forged.run.result);
  await assert.rejects(()=>Q.summarize(requested,'raw',[forged]),/do not match/);
  const second=await source(await task({title:'Conflicting second source'}));second.run.result.wordPairs.matches++;second.run.result.wordPairs.pages[0].matches++;second.run.id=hash(second.run.result);await assert.rejects(()=>Q.summarize(requested,'raw',[saved,second]),/Conflicting saved results/);
  const bad=clone(saved);bad.run.id='0'.repeat(64);await assert.rejects(()=>Q.summarize(requested,'raw',[bad]),/identity/);
 });
 await test('paired aggregates bind exact full scope, source version and rule while ignoring title and page order',async()=>{
  const a=await task(),b=await task({title:'Different question wording',pages:a.pages.slice().reverse(),rules:{...criterion,boundaries:'hyphen-period'}}),x=await Q.summarize(a,'raw',[await source(a)]),y=await Q.summarize(b,'raw',[await source(b)]),pair=Q.paired(x,y);assert.equal(pair.separate,x);assert.equal(pair.joined,y);assert.deepEqual(Q.paired(y,x),pair);assert.throws(()=>Q.paired(x,x),/opposite boundary/);
  for(const body of [{pages:b.pages.map(p=>({...p,text:p.text+'ᚠ'}))},{rules:{...b.criterion,lag:1}}]){const changed=await task({...body,rules:body.rules||b.criterion}),other=await Q.summarize(changed,'raw',[await source(changed)]);assert.throws(()=>Q.paired(x,other),/identical text/);}
  const reviewed=await Q.summarize(b,'reviewed',[await source(b,{version:'reviewed'})]);assert.throws(()=>Q.paired(x,reviewed),/source version/);assert.throws(()=>Q.paired(clone(x),y),/verified/);
 });
 await test('actual lag-six pages aggregate distributed proof to the full-run oracle with no target rerun',async()=>{
  const pages=fixture.pages.filter(p=>/^lp2-(?:[0-4]\d|5[0-5])$/.test(p.id)).map(p=>({id:p.id,text:p.raw})),rules={kind:'word-affine-count',lag:6,a:27,b:24,boundaries:'non-rune'},requested=await task({pages,rules}),saved=await Promise.all([pages.slice(0,28),pages.slice(28)].map((pages,i)=>task({title:'Archived batch '+i,pages,rules}).then(t=>source(t,{branded:true})))),expected=E.run(requested).wordPairs;
  const actual=await Q.summarize(requested,'raw',saved);assert.equal(actual.complete,true);assert.deepEqual(actual.wordPairs,{opportunities:965,matches:58,expected:{numerator:'2027633',denominator:'60060'}});assert.equal(actual.wordPairs.matches,expected.matches);assert.deepEqual(actual.wordPairs.expected,expected.expected);
  const joined=await task({pages,rules:{...rules,boundaries:'hyphen-period'}}),joinedProof=await Q.summarize(joined,'raw',[await source(joined,{branded:true})]);assert.deepEqual(joinedProof.wordPairs,{opportunities:1267,matches:77,expected:{numerator:'256123',denominator:'5720'}});assert.equal(Q.paired(actual,joinedProof).separate,actual);
 });
 await test('unsupported measurements, transformations, excessive source sets and browser export remain explicit',async()=>{
  await assert.rejects(()=>task({rules:{kind:'measurement'}}).then(t=>Q.summarize(t,'raw',[])),/supports/);await assert.rejects(()=>task({steps:[{op:'reverse',unit:'line'}]}).then(t=>Q.summarize(t,'raw',[])),/supports/);
  const requested=await task(),saved=await source(requested);await assert.rejects(()=>Q.summarize(requested,'raw',Array(76).fill(saved)),/75/);
  const context={LocalExperiment:E,ComputationEvidence:require('../computation-evidence.js'),crypto:crypto.webcrypto};vm.createContext(context);vm.runInContext(fs.readFileSync('question-evidence.js','utf8'),context);const aggregate=await context.QuestionEvidence.summarize(requested,'raw',[saved]);assert.equal(context.QuestionEvidence.inspect(aggregate),aggregate);assert.throws(()=>Q.inspect(aggregate),/verified/);
 });
 console.log('Question evidence: '+groups+' groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
