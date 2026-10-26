'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{createRequire}=require('node:module'),N=require('../pinned-domain-next-work.js'),L=require('../pinned-domain-case-ledger.js'),M=require('../pinned-domain-members.js'),E=require('../local-experiment.js'),{webcrypto}=require('node:crypto');
const filename=require.resolve('./test_pinned_domain_case_ledger.cjs'),source=fs.readFileSync(filename,'utf8'),shared={exports:{}};
vm.runInThisContext('(function(require,module,exports){'+source.slice(0,source.indexOf('\n(async()=>{'))+'\nmodule.exports={fixture};})',{filename})(createRequire(filename),shared,shared.exports);
const {fixture}=shared.exports;let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('private identity is required and bounded suggestions do not confer execution, results or reservation authority',async()=>{
  const f=await fixture(),ledger=await f.ledger(),before=L.inspect(ledger),work=N.select(f.parent,ledger);
  assert.equal(work.parentDomainId,before.parentDomainId);assert.equal(work.parentPlanSha256,before.parentPlanSha256);assert.equal(work.inputVersion,'raw');assert.equal(work.state,'scheduling-only');assert.deepEqual(work.jobs,[{selector:{globalSettingIndex:0,pageIds:f.ids},pageCases:2}]);assert.equal(work.pageCases,2);assert.equal(work.nextCursor,2);assert.equal(work.complete,false);assert(Object.values(work.checks).every(v=>v===false));assert(Object.isFrozen(work.jobs[0].selector.pageIds));assert.deepEqual(L.inspect(ledger),before);assert.deepEqual(N.select(f.parent,ledger),work);
  assert.throws(()=>N.select({},ledger));assert.throws(()=>N.select(f.parent,{}));const other=await fixture();assert.throws(()=>N.select(other.parent,ledger),/parent/);
 });
 await test('partial overlap and repeated receipts only remove exactly verified setting/page coordinates',async()=>{
  const f=await fixture(4),ledger=await f.ledger(),one=await f.source(0,['lp2-01']);await L.accept(ledger,one);await L.accept(ledger,one);await L.accept(ledger,await f.source(0,['lp2-01','lp2-03']));await L.accept(ledger,await f.source(1,['lp2-00','lp2-01','lp2-02']));
  const work=N.select(f.parent,ledger,{maxJobs:3,pagesPerJob:2});assert.deepEqual(work.jobs.map(j=>j.selector),[{globalSettingIndex:0,pageIds:['lp2-00','lp2-02']},{globalSettingIndex:1,pageIds:['lp2-03']},{globalSettingIndex:2,pageIds:['lp2-00','lp2-01']}]);assert.equal(work.pageCases,5);assert.equal(work.nextCursor,10);assert.equal(work.remainingNamedCases,167);assert.deepEqual(N.select(f.parent,ledger,{maxJobs:3,pagesPerJob:2}),work);assert.equal(L.inspect(ledger).verifiedNamedCases,5);
 });
 await test('pagination preserves parent order and can restart when an exhausted range leaves earlier work missing',async()=>{
  const f=await fixture(4),ledger=await f.ledger(),all=[];let cursor=0;
  do{const work=N.select(f.parent,ledger,{cursor,maxJobs:3,pagesPerJob:3});for(const job of work.jobs)for(const id of job.selector.pageIds)all.push(job.selector.globalSettingIndex+'|'+id);cursor=work.nextCursor;}while(cursor!==null);
  assert.equal(all.length,172);assert.equal(new Set(all).size,172);assert.deepEqual(all,Array.from({length:43},(_,index)=>f.ids.map(id=>index+'|'+id)).flat());const end=N.select(f.parent,ledger,{cursor:172});assert.deepEqual(end.jobs,[]);assert.equal(end.complete,false);assert.equal(end.remainingNamedCases,172);assert.equal(end.restartCursor,0);assert.equal(end.checks.outcomeInference,false);
 });
 await test('only complete verified coverage yields completion and no result outcome is inferred',async()=>{
  const f=await fixture(),ledger=await f.ledger();for(let index=0;index<43;index++)await L.accept(ledger,await f.source(index));const work=N.select(f.parent,ledger,{maxJobs:1024,pagesPerJob:75});assert.equal(work.complete,true);assert.equal(work.remainingNamedCases,0);assert.deepEqual(work.jobs,[]);assert.equal(work.nextCursor,null);assert.equal(work.restartCursor,null);assert(!Object.hasOwn(work,'negative'));assert(!Object.hasOwn(work,'matches'));assert.equal(work.checks.outcomeInference,false);
 });
 await test('strict bounds reject widening, getters and stale parent identities without running or deriving programs',async()=>{
  const f=await fixture(),ledger=await f.ledger();for(const options of [{cursor:-1},{cursor:87},{cursor:0.5},{maxJobs:0},{maxJobs:1025},{maxJobs:true},{pagesPerJob:0},{pagesPerJob:76},{pagesPerJob:1.5},{maxJobs:1024,pagesPerJob:75,execute:true},[],null])assert.throws(()=>N.select(f.parent,ledger,options));let reads=0;const getter={};Object.defineProperty(getter,'cursor',{enumerable:true,get(){reads++;return 0;}});assert.throws(()=>N.select(f.parent,ledger,getter));assert.equal(reads,0);
  const domain=structuredClone(f.domain);domain.aim.detail+=' changed';const stale=await M.prepare(domain,{bundle:f.bundle,crypto:webcrypto});assert.throws(()=>N.select(stale,ledger),/parent/);
  const module={exports:{}},code=fs.readFileSync(require.resolve('../pinned-domain-next-work.js'),'utf8');vm.runInThisContext('(function(require,module,exports){'+code+'\n})')((name)=>name==='./pinned-domain-members.js'?{inspect:M.inspect,derive(){throw Error('Must not derive target programs');}}:require('../'+name.slice(2)),module,module.exports);assert.deepEqual(module.exports.select(f.parent,ledger),N.select(f.parent,ledger));assert.equal(L.inspect(ledger).verifiedNamedCases,0);
 });
 console.log(groups+' bounded next-work groups passed; synthetic receipt fixtures only, no target work or writes.');
})().catch(error=>{console.error(error);process.exitCode=1;});
