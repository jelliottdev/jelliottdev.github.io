'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto,createHash}=require('node:crypto'),Q=require('../factored-finite-question.js'),E=require('../local-experiment.js');
const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8'));
(async()=>{
 const options={engine:E.ENGINE,inputVersion:'raw',alphabet:bundle.alphabet,pages:bundle.pages.filter(p=>['lp2-15','lp2-16'].includes(p.id)).map(p=>({id:p.id,text:p.raw})),criterion:{kind:'exact-prefix',values:Array(12).fill(28)},programs:[{steps:[{op:'affine',a:1,b:0}]},{steps:[{op:'affine',a:2,b:1}]}]},domain=await Q.bind(options,webcrypto),acc=Q.createAccumulator(domain,webcrypto),refs=(await Q.cases(domain,{cursor:0,limit:12},webcrypto)).cases;
 const expected={domainId:domain.id,coveredCaseIds:[],missingCaseIds:refs.map(r=>r.id),matchingCaseIds:[]};
 assert.deepEqual(await Q.coverage(acc,[...refs].reverse()),expected);
 const selected=await Q.select(domain,[refs[0]],webcrypto),task=selected.cases[0].task,result=E.run(task),source={task,inputVersion:'raw',run:{id:createHash('sha256').update(E.stable(result)).digest('hex'),createdAt:'2026-10-25T12:00:00.000Z',result}},prepared=await Q.prepareAccept(acc,[source]);
 assert.deepEqual(await Q.coverage(acc,refs),expected,'Uncommitted receipts grant no selected coverage');Q.commitAccept(acc,prepared);
 const observed=await Q.coverage(acc,refs);assert.deepEqual(observed.coveredCaseIds,[refs[0].id]);assert.deepEqual(observed.missingCaseIds,refs.slice(1).map(r=>r.id));assert.deepEqual(observed.matchingCaseIds,[]);assert(Object.isFrozen(observed)&&Object.isFrozen(observed.coveredCaseIds));
 assert.deepEqual(await Q.coverage(acc,[refs[1]]),{domainId:domain.id,coveredCaseIds:[],missingCaseIds:[refs[1].id],matchingCaseIds:[]},'Only the selected addresses are reported');
 for(const bad of [[{...refs[0],id:'0'.repeat(64)}],[refs[0],refs[0]],Array(13).fill(refs[0]),[]])await assert.rejects(()=>Q.coverage(acc,bad));await assert.rejects(()=>Q.coverage({},refs));let gets=0;const hook={};Object.defineProperty(hook,'programId',{enumerable:true,get(){gets++;return refs[0].programId;}});await assert.rejects(()=>Q.coverage(acc,[hook]));assert.equal(gets,0);
 const runeIndex=new Map(bundle.alphabet.map((r,i)=>[r.rune,i]));options.criterion.values=Array.from(result.transformed[0].text).filter(r=>runeIndex.has(r)).slice(0,12).map(r=>runeIndex.get(r));const matchedDomain=await Q.bind(options,webcrypto),matchedAcc=Q.createAccumulator(matchedDomain,webcrypto),matchedRef={programId:refs[0].programId,pageId:refs[0].pageId};
 // Criterion is part of the program identity, so select the same steps under its new identity.
 matchedRef.programId=matchedDomain.programs.find(p=>E.stable(p.steps)===E.stable(task.steps)).id;const item=(await Q.select(matchedDomain,[matchedRef],webcrypto)).cases[0],hit=E.run(item.task);await Q.accept(matchedAcc,[{task:item.task,inputVersion:'raw',run:{id:createHash('sha256').update(E.stable(hit)).digest('hex'),createdAt:'2026-10-25T12:00:00.000Z',result:hit}}]);assert.deepEqual((await Q.coverage(matchedAcc,[matchedRef])).matchingCaseIds,[item.id]);
 console.log('3 selected factored coverage groups passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
