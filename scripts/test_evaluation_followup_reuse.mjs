/* Read-only evidence selection and local preparation; all writes stay in isolated SQLite. */
import assert from 'node:assert/strict';
import {fixture,idea,seed} from './test_ordinary_prefix_reuse.mjs';
import C from '../claim-specification.js';
const count=(f,table)=>f.sqlite.prepare('SELECT COUNT(*) n FROM '+table).get().n;
async function prepare(f,owner){const response=await f.prepare(new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin:'https://jelliottdev.github.io','content-type':'application/json'},body:JSON.stringify({proposalId:owner.id,parentTaskId:null,includeDerivedPrefixEvidence:true})}),f.env);const value=await response.json();assert.equal(response.status,200,JSON.stringify(value));return value;}
for(const pages of [['lp2-01'],['lp2-01','lp2-02']]){
 const f=fixture();try{
  const original=idea(f,['lp2-01'],'Solve LP2','measurement'),saved=await seed(f,original,['lp2-01'],'Actual saved output',{kind:'measurement'}),opening=idea(f,pages,'Solve LP2',C.EVALUATION_CHOICES.find(x=>x.id==='warning-opening').value),language=idea(f,pages,'Solve LP2',C.EVALUATION_CHOICES.find(x=>x.id==='language-samples').value),beforeResults=count(f,'local_task_results'),beforeTasks=count(f,'local_tasks'),checked=await prepare(f,opening);
  assert.deepEqual(checked.derivedCoverage.summary.coveredPages,['lp2-01']);assert.deepEqual(checked.derivedCoverage.summary.matchingPages,[]);assert.equal(checked.derivedCoverage.sources[0].task.taskId,saved.task.taskId);assert.equal(checked.derivedCoverage.sources[0].task.criterion.kind,'measurement');
  if(pages.length===1){assert.equal(checked.state,'derived-prefix-answer');assert.equal(checked.task,undefined);}else{assert.equal(checked.state,'plan-ready');assert.deepEqual(checked.task.pages.map(x=>x.id),['lp2-02']);}
  const scored=await prepare(f,language);assert.equal(scored.state,'plan-ready');assert.deepEqual(scored.task.pages.map(x=>x.id),pages);assert.deepEqual(scored.task.criterion,C.EVALUATION_CHOICES.find(x=>x.id==='language-samples').value);assert.equal(scored.derivedCoverage,undefined);assert.deepEqual(scored.coverage?.coveredPages||[],[]);assert.equal(count(f,'local_task_results'),beforeResults);assert.equal(count(f,'local_tasks'),beforeTasks);
  console.log('PASS '+pages.length+'-page evaluation follow-up: saved output answers Warning opening; language comparison requires a genuine scored run.');
 }finally{f.sqlite.close();}
}
console.log('2 evaluation follow-up reuse groups passed; preparation alone never invents a task result.');
