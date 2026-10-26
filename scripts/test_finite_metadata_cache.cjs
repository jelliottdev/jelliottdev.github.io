'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),E=require('../local-experiment.js'),Settings=require('../finite-settings.js'),Storage=require('../finite-control-storage.js');
const record=JSON.parse(fs.readFileSync('experiments/records/lp2-known-vigenere-keys/record.json','utf8')),recipe=record.browser_followups.find(r=>r.kind==='finite-settings');
function fixture(){let members=0,inspections=0;require.cache[require.resolve('../finite-settings.js')].exports={...Settings,factored:{...Settings.factored,inspect(...args){inspections++;return Settings.factored.inspect(...args);},member(...args){members++;return Settings.factored.member(...args);}}};delete require.cache[require.resolve('../record-question-model.js')];return {model:require('../record-question-model.js'),counts:()=>({members,inspections}),copy:()=>structuredClone(recipe)};}
let groups=0;function test(name,fn){fn();groups++;console.log('PASS '+name);}
test('repeated and detached identical metadata reuse only immutable validated scalar counts without execution',()=>{
 const f=fixture(),r=f.copy(),before=JSON.stringify(r),run=E.run;E.run=()=>assert.fail('Metadata discovery cannot run programs');try{
  const first=f.model.finiteRecipe(r);assert.equal(first.programCount,42);assert.equal(first.caseCount,2352);assert(Object.isFrozen(first));assert.equal(f.counts().members,42);
  assert.equal(f.model.finiteRecipe(r),first);assert.equal(f.model.finiteRecipe(f.copy()),first);assert.equal(f.counts().members,42);assert.equal(JSON.stringify(r),before);assert.throws(()=>{first.caseCount=0;});
 }finally{E.run=run;}
});
test('a changed nested control or scope never borrows a cached successful declaration',()=>{
 const f=fixture(),r=f.copy();assert(f.model.finiteRecipe(r));
 for(const change of [v=>v.control.members[0].control.task.taskId='bad',v=>v.control.members[0].control.expected_result_sha256='bad',v=>v.control.members[0].settings[0].value='outside-declaration',v=>v.inputs.pages.pop(),v=>{if(v.control.criterion)v.control.criterion.values[0]=29;else v.control.members[0].control.task.criterion.values[0]=29;}]){const bad=f.copy();change(bad);assert.equal(f.model.finiteRecipe(bad),null);}
 const restored=f.copy();assert.equal(f.model.finiteRecipe(restored).caseCount,2352);
});
test('cache hits still inspect every descriptor and never invoke a newly installed getter',()=>{
 const f=fixture(),r=f.copy();assert(f.model.finiteRecipe(r));let reads=0;const value=r.control.members[0].control.task.title;Object.defineProperty(r.control.members[0].control.task,'title',{enumerable:true,configurable:true,get(){reads++;return value;}});assert.equal(f.model.finiteRecipe(r),null);assert.equal(reads,0);
});
test('inherited serialization hooks cannot be invoked by the metadata cache',()=>{
 const f=fixture(),r=f.copy();let calls=0;Object.setPrototypeOf(r,{toJSON(){calls++;throw Error('No hook');}});assert(f.model.finiteRecipe(r));assert(f.model.finiteRecipe(r));assert.equal(calls,0);assert.equal(f.counts().members,84,'Non-plain prototypes bypass only the cache');
});
test('the bounded eight-entry LRU evicts old metadata without changing validation',()=>{
 const f=fixture(),r=f.copy();assert(f.model.finiteRecipe(r));for(let i=0;i<8;i++){const next=f.copy();next.id='distinct-cache-'+i;assert(f.model.finiteRecipe(next));}assert.equal(f.counts().members,9*42);assert(f.model.finiteRecipe(r));assert.equal(f.counts().members,10*42,'Evicted metadata must pass member validation again');
});
test('missing settings tools cannot reuse previously validated metadata',()=>{
 const f=fixture(),r=f.copy();assert(f.model.finiteRecipe(r));const module=require.cache[require.resolve('../finite-settings.js')],prior=module.exports;try{module.exports={factored:null};assert.equal(f.model.finiteRecipe(r),null);module.exports={factored:{inspect(){}}};assert.equal(f.model.finiteRecipe(r),null);}finally{module.exports=prior;}assert.equal(f.model.finiteRecipe(r).caseCount,2352);assert.equal(f.counts().members,42);
});
test('oversized metadata is not retained and cannot prevent later small declarations from being checked',()=>{
 const f=fixture(),r=f.copy();r.cacheOnlyExtra='x'.repeat(2*1024*1024);assert(f.model.finiteRecipe(r));assert(f.model.finiteRecipe(r));assert.equal(f.counts().members,84);assert(f.model.finiteRecipe(f.copy()));assert.equal(f.counts().members,126);
});
console.log(groups+' finite metadata cache groups passed');

require.cache[require.resolve('../finite-settings.js')].exports=Settings;
