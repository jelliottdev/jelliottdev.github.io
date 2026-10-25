'use strict';
const assert=require('node:assert/strict'),{webcrypto,createHash}=require('node:crypto'),Q=require('../factored-finite-question.js'),E=require('../local-experiment.js'),Registry=require('../output-evaluators.js');
const alphabet=require('../data/local-run-inputs.json').alphabet,copy=structuredClone,hash=v=>createHash('sha256').update(E.stable(v)).digest('hex');
const gate=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
async function fixture(mode,crypto=webcrypto){
 const options={engine:E.ENGINE,inputVersion:'raw',alphabet,pages:[{id:'lp2-15',text:alphabet.slice(0,8).map(v=>v.rune).join('')},{id:'lp2-17',text:''}],criterion:mode==='language'?Registry.criterion():mode==='inspection'?{kind:'measurement'}:{kind:'exact-prefix',values:[0,1]},programs:[{steps:[{op:'affine',a:1,b:0}]},{steps:[{op:'affine',a:2,b:1}]}]},bind=mode==='language'?Q.bindLanguageComparison:mode==='inspection'?Q.bindOutputInspection:Q.bind,domain=await bind(options,webcrypto),refs=(await Q.cases(domain,{cursor:0,limit:12},webcrypto)).cases,acc=mode==='prefix'?Q.createPrefixAccumulator(domain,crypto):['language','inspection'].includes(mode)?Q.createOutputAccumulator(domain,crypto):Q.createAccumulator(domain,crypto);
 return {domain,refs,acc};
}
const source=task=>{const result=E.run(task);return {task,inputVersion:'raw',run:{id:hash(result),createdAt:'2026-10-25T12:00:00.000Z',result}};};
(async()=>{let count=0;const test=async(name,fn)=>{await fn();count++;console.log('PASS '+name);};
await test('all policies resolve current coverage without task preparation and preserve task preparation input order',async()=>{
 for(const mode of ['strict','prefix','language','inspection']){
  const f=await fixture(mode),reversed=f.refs.slice().reverse(),original=E.prepare,calls=[];E.prepare=(body,...args)=>{calls.push(body);return original(body,...args);};
  let selected;try{const empty=await Q.coverage(f.acc,reversed);assert.deepEqual(empty.missingCaseIds,f.refs.map(r=>r.id));assert.equal(calls.length,0);selected=await Q.select(f.domain,reversed,webcrypto);assert.equal(calls.length,reversed.length);assert.deepEqual(calls.map(body=>[body.title,body.pages[0].id]),reversed.map(ref=>['Finite program '+ref.programId,ref.pageId]));assert.deepEqual(selected.cases.map(({task,...ref})=>ref),f.refs);}finally{E.prepare=original;}
  for(const item of selected.cases){const program=f.domain.programs.find(p=>p.id===item.programId),page=f.domain.pages.find(p=>p.id===item.pageId);assert.deepEqual(item.task,await E.prepare({title:'Finite program '+item.programId,pages:[page],alphabet:f.domain.alphabet,steps:program.steps,criterion:f.domain.criterion},webcrypto));}
  await Q.accept(f.acc,[source(selected.cases[0].task)]);const partial=await Q.coverage(f.acc,reversed);assert.deepEqual(partial.coveredCaseIds,[f.refs[0].id]);assert.deepEqual(partial.missingCaseIds,f.refs.slice(1).map(r=>r.id));
  await Q.accept(f.acc,selected.cases.map(item=>source(item.task)));const full=await Q.coverage(f.acc,reversed);assert.deepEqual(full.coveredCaseIds,f.refs.map(r=>r.id));assert.deepEqual(full.missingCaseIds,[]);assert.equal((await Q.summarize(f.acc,{lookupComplete:true})).coveredCases,f.refs.length);
 }
});
await test('forged sparse duplicate extra and accessor refs reject without constructing tasks or granting coverage',async()=>{
 const f=await fixture('strict'),original=E.prepare;let prepares=0,hooks=0;E.prepare=(...args)=>{prepares++;return original(...args);};
 try{const sparse=Array(2);sparse[1]=f.refs[0];const accessor=[{...f.refs[0]}];Object.defineProperty(accessor[0],'pageId',{enumerable:true,get(){hooks++;return 'lp2-15';}});for(const bad of [[],Array(13).fill(f.refs[0]),sparse,[f.refs[0],f.refs[0]],[{...f.refs[0],id:'0'.repeat(64)}],[{...f.refs[0],programId:'f'.repeat(64)}],[{...f.refs[0],pageId:'lp2-99'}],[{...f.refs[0],extra:true}],accessor])await assert.rejects(Q.coverage(f.acc,bad));assert.equal(prepares,0);assert.equal(hooks,0);assert.equal((await Q.summarize(f.acc)).coveredCases,0);assert.throws(()=>Q.createAccumulator(copy(f.domain)));}finally{E.prepare=original;}
});
await test('refs are captured before asynchronous hashing and every call reads current committed evidence',async()=>{
 const held=gate(),entered=gate();let blocked=true;const crypto={subtle:{digest:async(...args)=>{if(blocked){entered.resolve();await held.promise;}return webcrypto.subtle.digest(...args);}}},f=await fixture('strict',crypto),refs=copy(f.refs),reading=Q.coverage(f.acc,refs);await entered.promise;refs[0].id='f'.repeat(64);refs[0].pageId='lp2-99';blocked=false;
 const task=(await Q.select(f.domain,[f.refs[0]],webcrypto)).cases[0].task;await Q.accept(f.acc,[source(task)]);held.resolve();const current=await reading;assert.deepEqual(current.coveredCaseIds,[f.refs[0].id]);assert.deepEqual(current.missingCaseIds,f.refs.slice(1).map(r=>r.id));assert.deepEqual(await Q.coverage(f.acc,f.refs),current);
});
console.log(count+' exact factored reference-resolution groups passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
