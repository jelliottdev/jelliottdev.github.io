'use strict';
/* Named-opening evidence and execution: invented texts only. */
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto,createHash}=require('node:crypto');
const E=require('../local-experiment.js'),Evidence=require('../computation-evidence.js'),Controls=require('../local-plan-controls.js'),Control=require('../local-control.js'),Policy=require('../finite-question-policy.js'),Q=require('../finite-program-question.js'),Runner=require('../finite-search-runner.js');
const alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet,copy=structuredClone,hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),runes=v=>v.map(n=>alphabet[n].rune).join('');
const criterion={kind:'exact-prefix-set',openings:[{id:'short',values:[0]},{id:'long',values:[0,1]},{id:'other',values:[28]}]};
const receipt=(task,result)=>({task,inputVersion:'raw',run:{id:hash(result),createdAt:'2026-10-26T12:00:00.000Z',result}});
(async()=>{let n=0;async function test(name,fn){await fn();n++;console.log('PASS '+name);}
const task=await E.prepare({title:'Invented named openings',alphabet,pages:[{id:'lp2-00',text:runes([0,1,2])},{id:'lp2-01',text:' /\n'}],steps:[],criterion},webcrypto),result=E.run(task);
await test('saved evidence independently checks every ordered opening decision, even after result rehashing',async()=>{
 const good=receipt(task,result);assert.equal((await Evidence.compare(task,'raw',[good],webcrypto)).coveredPages.length,2);
 for(const alter of [r=>r.matches[0].matchingOpenings.reverse(),r=>r.matches[0].matchingOpenings.pop(),r=>r.matches[0].matchingOpenings.push('invented'),r=>r.matches[0].matched=false,r=>r.matches[1].matchingOpenings=['short'],r=>delete r.matches[0].matchingOpenings,r=>r.matches[0].extra=true]){
  const bad=copy(result);alter(bad);await assert.rejects(Evidence.compare(task,'raw',[receipt(task,bad)],webcrypto),/opening|matches/i);
 }
 const single=await E.prepare({...task,criterion:{kind:'exact-prefix',values:[0]}},webcrypto),old=receipt(single,E.run(single));assert.deepEqual((await Evidence.compare(task,'raw',[old],webcrypto)).coveredPages,[]);
});
await test('assessments separate pages without runes and never turn one hit into search completion',async()=>{
 const policy=Policy.describe(criterion);assert.equal(policy.completion,'all-cases');assert.equal(policy.id,'exact-prefix-set-v1');
 assert.deepEqual(Policy.assessValues(criterion,[]),{status:'no-runes',runes:0,matchingOpenings:[]});
 assert.deepEqual(Policy.assessValues(criterion,[0,1]),{status:'matched',runes:2,matchingOpenings:['short','long']});
 const assessment=Policy.inspect(await Policy.prepare(receipt(task,result),webcrypto));assert.equal(assessment.counts.noRunePages,1);assert.equal(assessment.counts.usablePages,1);assert.equal(assessment.counts.matchedPages,1);
});
await test('independent local controls cover positive and negative named-opening calculations without running the target',async()=>{
 const original=E.run;E.run=t=>{assert.notEqual(t.taskId,task.taskId,'Never evaluate the target while preparing controls');return original(t);};let suite;
 try{suite=await Controls.prepare(task,webcrypto);}finally{E.run=original;}
 assert.deepEqual(suite.cases.map(c=>E.run(c.task).matches[0].matched),[true,false]);
 const witness=await E.prepare({title:'Synthetic complete output',alphabet,pages:[{id:'lp1-00',text:runes([0,1,2])}],steps:[],criterion:{kind:'exact-prefix',values:[0,1,2]}},webcrypto);
 assert(Control.compatible(witness,task));const partial=await E.prepare({...witness,criterion:{kind:'exact-prefix',values:[0]}},webcrypto);assert(!Control.compatible(partial,task));
 const bad=copy(task);bad.criterion.openings[1].id='short';assert(!Control.compatible(witness,bad));
 const changed=copy(suite);changed.cases[0].task.criterion.openings.reverse();await assert.rejects(Controls.validate(changed,task,webcrypto));
});
await test('a matching set output cannot stop execution of the rest of the reviewed batch',async()=>{
 const programs=[];for(let b=0;b<2;b++)programs.push(await E.prepare({title:'Invented setting '+b,alphabet,pages:[{id:'lp2-00',text:runes([0,1,2])}],steps:[{op:'affine',a:1,b}],criterion:{kind:'exact-prefix-set',openings:[{id:'zero',values:[0]},{id:'one',values:[1]}]}},webcrypto));
 const domain=await Q.bind({programs,inputVersion:'raw'},webcrypto),ids=domain.cases.map(c=>c.id),selection=await Q.select(domain,ids,webcrypto),controls=[];
 for(const item of selection.cases)controls.push({caseId:item.id,suite:await Controls.prepare(item.task,webcrypto)});
 let calls=0;const executor={start(t){calls++;return {promise:Promise.resolve(E.run(t)),cancel(){}};}},value=await Runner.createRunner({executor,crypto:webcrypto}).start(domain,ids,controls).promise;
 assert.equal(value.matchingCaseIds.length,2);assert.deepEqual(value.completedCaseIds,ids);assert.deepEqual(value.missingCaseIds,[]);assert.equal(value.stopped,'batch-complete');assert.equal(calls,6);
});
console.log(n+' named opening evidence/control groups passed; all calculations use invented texts.');
})().catch(error=>{console.error(error);process.exitCode=1;});
