'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{createHash,webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),F=require('../finite-program-question.js');
const alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet,runes=values=>values.map(v=>alphabet[v].rune).join(''),clone=v=>JSON.parse(JSON.stringify(v)),hash=v=>createHash('sha256').update(E.stable(v)).digest('hex');
const pages=[{id:'lp2-15',text:runes([0,1,2,3])+'\n'+runes([4,5])},{id:'lp2-16',text:runes([4,3,2,1])}],criterion={kind:'exact-prefix',values:[0,1,2]};
async function task(steps=[],selected=pages,title='Explicit idea'){return E.prepare({title,pages:selected,alphabet,steps,criterion});}
async function source(t){const result=E.run(t);return {task:t,inputVersion:'raw',run:{id:hash(result),createdAt:'2026-10-25T12:00:00.000Z',result}};}
(async()=>{
 let count=0;async function test(name,fn){await fn();count++;console.log('PASS '+name);}
 const a=await task(),b=await task([{op:'affine',a:1,b:1}]),domain=await F.bind({programs:[a,b],inputVersion:'raw'});
 await test('domain identity ignores title, input program order and page order while retaining exact semantics',async()=>{
  const renamed=await task([],pages.slice().reverse(),'Different aim or prose'),other=await F.bind({programs:[b,renamed],inputVersion:'raw'});assert.equal(domain.id,other.id);assert.deepEqual(domain,other);assert.equal(domain.totalCases,4);assert(Object.isFrozen(domain.programs[0].task.pages[0]));
  const reviewed=await F.bind({programs:[a,b],inputVersion:'reviewed'});assert.notEqual(domain.id,reviewed.id);
  const p=[{op:'affine',a:2,b:1},{op:'affine',a:3,b:2}],x=await F.bind({programs:[await task(p)],inputVersion:'raw'}),y=await F.bind({programs:[await task(p.slice().reverse())],inputVersion:'raw'});assert.notEqual(x.id,y.id);
  const mutated=clone(a);mutated.title='Caller edit';assert.equal(domain.id,other.id);assert.throws(()=>F.inspect(clone(domain)),/bound/);
 });
 await test('duplicate programs and changed common inputs, criteria, alphabet and bounds fail closed',async()=>{
  const renamed=await task([],pages,'Same calculation');await assert.rejects(()=>F.bind({programs:[a,renamed],inputVersion:'raw'}),/Duplicate/);
  const changedText=await task(b.steps,pages.map(p=>({...p,text:p.text+alphabet[0].rune}))),changedCriterion=await E.prepare({...b,criterion:{kind:'exact-prefix',values:[1,2]}}),changedAlphabet=await E.prepare({...b,alphabet:alphabet.map((r,i)=>({...r,prime:i===0?113:r.prime}))});
  for(const altered of [changedText,changedCriterion,changedAlphabet])await assert.rejects(()=>F.bind({programs:[a,altered],inputVersion:'raw'}),/same exact/);
  await assert.rejects(()=>F.bind({programs:[a],inputVersion:'other'}));
  await assert.rejects(()=>F.bind({programs:Array(1025).fill(a),inputVersion:'raw'}));
  const manyPages=await task([],Array.from({length:75},(_,i)=>({id:i<17?'lp1-'+String(i).padStart(2,'0'):'lp2-'+String(i-17).padStart(2,'0'),text:runes([0,1,2])})));await assert.rejects(()=>F.bind({programs:Array(55).fill(manyPages),inputVersion:'raw'}),/case bound/);
  const large=await task([],[{id:'lp2-15',text:alphabet[0].rune.repeat(20000)}]);await assert.rejects(()=>F.bind({programs:Array(101).fill(large),inputVersion:'raw'}),/rune-work/);
  await assert.rejects(()=>F.bind({programs:Array(200).fill(large),inputVersion:'raw'}),/byte bound/);
  const measurement=await E.prepare({...a,criterion:{kind:'measurement'}});await assert.rejects(()=>F.bind({programs:[measurement],inputVersion:'raw'}),/exact prefix/);
 });
 await test('selection contains only declared independently identified single-page ordinary tasks',async()=>{
  const chosen=await F.select(domain,domain.cases.slice(0,2).map(c=>c.id));assert.equal(chosen.domainId,domain.id);assert.equal(chosen.cases.length,2);for(const item of chosen.cases){await E.checkIdentity(item.task);assert.deepEqual(item.task.pages.map(p=>p.id),[item.pageId]);}
  for(const ids of [[],['0'.repeat(64)],[domain.cases[0].id,domain.cases[0].id],Array(13).fill(domain.cases[0].id)])await assert.rejects(()=>F.select(domain,ids));
 });
 await test('partial negative offers exact missing cases; early positive stops even with incomplete lookup',async()=>{
  const negative=await source(await task(b.steps,[pages[0]],'Another classification')),partial=await F.summarize(domain,[negative]);assert.equal(partial.coveredCaseIds.length,1);assert.equal(F.decision(partial).state,'missing-evidence');assert.equal(F.decision(partial).next.caseIds.length,3);
  const unknown=await F.summarize(domain,[negative],{lookupComplete:false});assert.equal(F.decision(unknown).state,'unavailable');assert.equal(F.decision(unknown).next.kind,'retry-evidence');
  const positive=await source(await task([],[pages[0]],'Independent idea')),found=await F.summarize(domain,[negative,positive],{lookupComplete:false});assert.equal(F.decision(found).answer,'prefix-found');assert.equal(found.complete,false);assert.equal(found.missingCaseIds.length,2);assert.throws(()=>F.decision(clone(found)),/independently verified/);
 });
 await test('complete negative closes only the exact declared domain; evidence unions batches without doublecounting',async()=>{
  const negativePrograms=[await task(b.steps),await task([{op:'affine',a:1,b:2}])],negativeDomain=await F.bind({programs:negativePrograms,inputVersion:'raw'}),sources=[];
  for(const program of negativePrograms)for(const page of pages)sources.push(await source(await task(program.steps,[page],page.id+' alternate source')));
  const full=await F.summarize(negativeDomain,[...sources,sources[0]],{lookupComplete:false});assert.equal(full.coveredCaseIds.length,4);assert(full.complete);assert.equal(F.decision(full).answer,'prefix-not-found');assert.equal(F.decision(full).next,null);assert.match(F.decision(full).limit,/broader deciphering aim/);
  const forward=await F.summarize(negativeDomain,sources),reverse=await F.summarize(negativeDomain,sources.slice().reverse());assert.deepEqual(forward,reverse);
 });
 await test('receipt hashes, real transformation replay, exact input bytes and versions prevent false coverage',async()=>{
  const s=await source(a),bad=clone(s);bad.run.id='0'.repeat(64);await assert.rejects(()=>F.summarize(domain,[bad]));
  const forged=clone(s),wrong=E.run(await task(b.steps));forged.run.result={...wrong,taskId:a.taskId};forged.run.id=hash(forged.run.result);await assert.rejects(()=>F.summarize(domain,[forged]),/result|match|computation/i);
  const changed=await source(await task([],pages.map(p=>({...p,text:p.text+alphabet[7].rune}))));assert.equal((await F.summarize(domain,[changed])).coveredCaseIds.length,0);
  const version=clone(s);version.inputVersion='reviewed';assert.equal((await F.summarize(domain,[version])).coveredCaseIds.length,0);
  const immutable=await F.summarize(domain,[s]);s.run.result.transformed[0].text='changed after proof';assert.equal(immutable.matchingCaseIds.length,1);assert(Object.isFrozen(immutable.evidence[0]));
 });
 await test('an actual 812-program affine domain remains bounded and an ordinary existing receipt stops the search',async()=>{
  const alternatives=[];for(let multiplier=1;multiplier<29;multiplier++)for(let offset=0;offset<29;offset++)alternatives.push(await task([{op:'affine',a:multiplier,b:offset}],[pages[0]]));
  const all=await F.bind({programs:alternatives,inputVersion:'raw'});assert.equal(all.totalCases,812);assert.equal((await F.select(all,all.cases.slice(0,12).map(c=>c.id))).cases.length,12);
  const proof=await F.summarize(all,[await source(alternatives[0])]);assert.equal(proof.coveredCaseIds.length,1);assert.equal(proof.missingCaseIds.length,811);assert.equal(F.decision(proof).answer,'prefix-found');
 });
 await test('caller accessors, serialization hooks and sparse or unsafe data are rejected without execution',async()=>{
  let calls=0;const getter={inputVersion:'raw'};Object.defineProperty(getter,'programs',{enumerable:true,get(){calls++;return [a];}});await assert.rejects(()=>F.bind(getter));
  const hooked=clone(a);hooked.toJSON=()=>{calls++;return a;};await assert.rejects(()=>F.bind({programs:[hooked],inputVersion:'raw'}));
  const receipt=await source(a);Object.defineProperty(receipt.run,'result',{enumerable:true,get(){calls++;return E.run(a);}});await assert.rejects(()=>F.summarize(domain,[receipt]));
  const options={};Object.defineProperty(options,'lookupComplete',{enumerable:true,get(){calls++;return true;}});await assert.rejects(()=>F.summarize(domain,[],options));
  const sparse=Array(1);await assert.rejects(()=>F.select(domain,sparse));assert.equal(calls,0);
 });
 await test('UMD browser entry uses the same pure fixed engine and identities',async()=>{
  const context=vm.createContext({LocalExperiment:E,ComputationEvidence:require('../computation-evidence.js'),FiniteJSON:require('../finite-json.js'),crypto:webcrypto,TextEncoder,Uint8Array});vm.runInContext(fs.readFileSync('finite-program-question.js','utf8'),context);const browser=await context.FiniteProgramQuestion.bind({programs:[b,a],inputVersion:'raw'});assert.equal(browser.id,domain.id);assert.equal(context.FiniteProgramQuestion.decision(await context.FiniteProgramQuestion.summarize(browser,[])).state,'missing-evidence');
 });
 console.log(count+' finite program question groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
