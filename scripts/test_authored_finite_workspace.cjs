'use strict';
/* Actual workspace/session with private transport fixtures, never hosted writes. */
const assert=require('node:assert/strict'),fs=require('node:fs'),{createHash}=require('node:crypto'),E=require('../local-experiment.js'),C=require('../claim-specification.js'),Router=require('../finite-workspace-router.js'),Legacy=require('../finite-search-workspace.js'),Full=require('../factored-finite-workspace.js');
const origin={recordId:'private-source',followupId:'private-followup',recordSha256:'1'.repeat(64),protocolSha256:'2'.repeat(64)};
const harness=fs.readFileSync(require.resolve('./test_factored_output_workspace.cjs'),'utf8'),prefix=harness.slice(0,harness.indexOf('(async()=>{let n=0;'));
assert(prefix.includes('async function fixture('));assert(prefix.includes('options={idea,'));
const makeFixture=new Function('require','sourceOrigin',prefix.replace('options={idea,','options={authoredOrigin:sourceOrigin,idea,')+'\nreturn fixture;')(require,origin);
const hash=value=>createHash('sha256').update(C.serialize(value)).digest('hex');
(async()=>{
 const initial=structuredClone(origin),f=await makeFixture();try{
  await f.app.ready;assert.equal(f.jobs.length,0);assert.deepEqual(f.calls.map(c=>c.action),['evidence']);assert.deepEqual(f.calls[0].body.authoredOrigin,initial);
  origin.recordSha256='9'.repeat(64);await f.app.prepare();assert.equal(f.jobs.length,0);assert.equal(f.calls.filter(c=>c.action==='create').length,0);
  await f.app.run();assert(f.jobs.length>0);assert.equal(f.calls.filter(c=>c.action==='results').length,0);await f.app.save();
  assert.deepEqual([...new Set(f.calls.map(c=>c.action))],['evidence','prepare','create','results']);for(const call of f.calls)assert.deepEqual(call.body.authoredOrigin,initial);
  console.log('PASS workspace captures exact origin once and sends it across explicit evidence/prepare/create/results without automatic execution or saving');
 }finally{f.app.destroy();}
 const fixtures=await makeFixture();fixtures.app.destroy();const source=structuredClone(initial),card=structuredClone(fixtures.idea.card);card.rules.evaluation={status:'specified',value:{kind:'exact-prefix',values:[28,28]}};const idea={id:'p_'+hash(card),card},base={...fixtures.options,idea,authoredOrigin:source,config:{factoredSearchEndpoint:'https://private.invalid/factored-search'},validEndpoint:(url,kind)=>url==='https://private.invalid/'+kind};
 const originalLegacy=Legacy.createWorkspace,originalFull=Full.createWorkspace,calls=[];function factory(kind){return(doc,host,options)=>{calls.push(kind);return{ready:Promise.resolve(),getState:()=>({kind,options}),destroy(){}};};}
 Legacy.createWorkspace=factory('legacy');Full.createWorkspace=factory('factored');
 try{const app=Router.createWorkspace({},fixtures.h,base);source.protocolSha256='8'.repeat(64);await app.ready;assert.deepEqual(calls,['factored']);assert.deepEqual(app.getState().options.authoredOrigin,initial);assert.equal(app.getState().options.precompiled.domain.totalCases,4);app.destroy();
  const before=calls.length,missing=Router.createWorkspace({},fixtures.h,{...base,config:{}});await assert.rejects(()=>missing.ready,/source-aware workspace/);assert.equal(calls.length,before);missing.destroy();
  console.log('PASS authored small-prefix domains use the full source-aware route and unavailable endpoints cannot silently strip origin via legacy fallback');
 }finally{Legacy.createWorkspace=originalLegacy;Full.createWorkspace=originalFull;}
 console.log('2 authored finite workspace groups passed; only explicit private synthetic fixture execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
