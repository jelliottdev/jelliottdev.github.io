'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto,createHash}=require('node:crypto');
const L=require('../local-experiment.js'),C=require('../computation-evidence.js'),clone=v=>JSON.parse(JSON.stringify(v));
const alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet;
const digest=v=>createHash('sha256').update(L.stable(v)).digest('hex');
async function task(overrides={}){return L.prepare({title:'An authored title',alphabet,pages:[{id:'lp2-00',text:'ᚠᚢ-ᚦ\nᚩᚱ'},{id:'lp2-01',text:'ᚠᚠ.ᚢᚩ'}],steps:[{op:'keyed-shift',key:[23,18,3,4],mode:'repeat',direction:'subtract',reset:'page'}],criterion:{kind:'exact-prefix',values:[24,7,24]},...overrides},webcrypto);}
function source(t,inputVersion='raw'){const result=L.run(t);return {task:clone(t),inputVersion,run:{id:digest(result),createdAt:'2026-10-24T12:00:00.000Z',result}};}
(async()=>{
 const first=await task(),renamed=await task({title:'Another category or aim'}),a=await C.describe(first,'raw',webcrypto),b=await C.describe(renamed,'raw',webcrypto);
 assert.notEqual(first.taskId,renamed.taskId);assert.deepEqual(a,b);
 const reverse=await task({pages:first.pages.slice().reverse()}),saved=source(reverse);assert.deepEqual((await C.describe(reverse,'raw',webcrypto)).pages,a.pages.slice().reverse());
 let result=await C.compare(renamed,'raw',[saved],webcrypto);assert.deepEqual(result.coveredPages,['lp2-00','lp2-01']);assert.deepEqual(result.remainingPages,[]);assert.equal(result.exactTaskId,reverse.taskId);assert.equal(result.evidence[0].resultId,saved.run.id);
 assert(saved.run.result.matches.every(m=>m.matched===false),'A failed opening is still covered tested work.');
 const one=await task({pages:[first.pages[0]]}),oneSource=source(one),two=await task({pages:[first.pages[1]]});
 result=await C.compare(first,'raw',[oneSource],webcrypto);assert.deepEqual(result.coveredPages,['lp2-00']);assert.deepEqual(result.remainingPages,['lp2-01']);assert.equal(result.exactTaskId,null);
 result=await C.compare(first,'raw',[oneSource,source(two)],webcrypto);assert.deepEqual(result.remainingPages,[]);assert.equal(result.exactTaskId,null,'A union does not relabel itself as a single saved task.');
 assert.equal((await C.compare(first,'raw',[oneSource,oneSource],webcrypto)).evidence.length,1);
 for(const change of [{steps:[{...first.steps[0],reset:'word'}]},{steps:[{...first.steps[0],key:[23,12,3,4]}]},{steps:[{...first.steps[0],direction:'add'}]},{criterion:{kind:'exact-prefix',values:[0]}},{alphabet:alphabet.slice().reverse()}]){
  const other=await task(change);assert.notEqual((await C.describe(other,'raw',webcrypto)).protocolId,a.protocolId);assert.deepEqual((await C.compare(other,'raw',[source(first)],webcrypto)).coveredPages,[]);
 }
 assert.notEqual((await C.describe(first,'reviewed',webcrypto)).protocolId,a.protocolId);assert.deepEqual((await C.compare(first,'reviewed',[source(first)],webcrypto)).coveredPages,[]);
 const changedText=await task({pages:[{...first.pages[0],text:first.pages[0].text+' '},first.pages[1]]});result=await C.compare(changedText,'raw',[source(first)],webcrypto);assert.deepEqual(result.coveredPages,['lp2-01']);
 for(const invalid of ['','RAW',null])await assert.rejects(C.describe(first,invalid,webcrypto));
 for(const alter of [s=>s.extra=true,s=>s.run.extra=true,s=>s.run.id='0'.repeat(64),s=>s.run.createdAt='invalid',s=>s.task.title='Changed unhashed',s=>s.run.result.taskId='0'.repeat(64),s=>s.run.result.schema='other',s=>s.run.result.engine='other',s=>s.run.result.runnerVersion='2',s=>s.run.result.transformed.reverse(),s=>s.run.result.transformed[0].text+='x',s=>s.run.result.metrics.runes++,s=>s.run.result.matches.pop(),s=>s.run.result.matches[0].matched=true]){
  const modified=source(first);alter(modified);await assert.rejects(C.compare(first,'raw',[modified],webcrypto));
 }
 const geometry=source(first);geometry.run.result.transformed[0].text=geometry.run.result.transformed[0].text.replace('-', '/');geometry.run.id=digest(geometry.run.result);await assert.rejects(C.compare(first,'raw',[geometry],webcrypto));
 const conflict=source(one);conflict.run.createdAt='2026-10-24T13:00:00.000Z';await assert.rejects(C.compare(first,'raw',[oneSource,conflict],webcrypto));
 // Check optional measurement envelopes without invoking the decoder during lookup.
 const measurements=[];for(const criterion of [{kind:'measurement'},{kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'},{kind:'word-affine-count',lag:1,a:27,b:24,boundaries:'hyphen-period'}]){const t=await task({steps:[],criterion});measurements.push([t,source(t)]);}
 const oldRun=L.run;L.run=()=>{throw Error('Lookup must not decode target text.');};
 try{
  assert.deepEqual((await C.compare(first,'raw',[saved],webcrypto)).remainingPages,[]);
  for(const [t,s] of measurements)assert.equal((await C.compare(t,'raw',[s],webcrypto)).coveredPages.length,2);
 }finally{L.run=oldRun;}
 for(const [t,s] of measurements.slice(1)){const corrupt=clone(s);if(corrupt.run.result.wordSums)corrupt.run.result.wordSums.pages.reverse();else corrupt.run.result.wordPairs.pages.reverse();corrupt.run.id=digest(corrupt.run.result);await assert.rejects(C.compare(t,'raw',[corrupt],webcrypto));}
 const context={LocalExperiment:L,TextEncoder,crypto:webcrypto};vm.createContext(context);vm.runInContext(fs.readFileSync('computation-evidence.js','utf8'),context);assert.equal(L.stable(await context.ComputationEvidence.describe(first,'raw',webcrypto)),L.stable(a));
 console.log('PASS exact protocol/page reuse independent of title and batching, honest failed-test coverage, source/result tamper rejection, measurement shapes and no target lookup execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
