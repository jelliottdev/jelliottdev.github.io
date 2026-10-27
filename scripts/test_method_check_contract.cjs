/* Typed capability facts, not natural-language interpretation or scientific validation. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto}=require('node:crypto'),M=require('../method-check-contract.js'),V=require('../declarative-rune-program.js'),Controls=require('../declarative-plan-controls.js'),Language=require('../language-score.js'),J=require('../finite-json.js');
const clone=structuredClone;let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('typed choices resolve exactly and prose never becomes supported capability',()=>{
  assert.deepEqual(M.resolveEvaluation({kind:'output-measurements'}),{kind:'measurement'});assert.deepEqual(M.LANGUAGE_CRITERION,Language.criterion());assert(Object.isFrozen(M.LANGUAGE_CRITERION));
  for(const value of [{kind:'exact-prefix',values:[0,2]},{kind:'exact-prefix-set',openings:[{id:'one',values:[0]},{id:'two',values:[2,1]}]},Language.criterion()])assert.deepEqual(M.resolveEvaluation(value),value);
  for(const description of ['Report counts and IC.','Check significance against shuffled runes.','Measure readability.']){const value={kind:'described',description};assert.equal(M.resolveEvaluation(value),null);assert.equal(M.describeEvaluation(value),description);}
  assert.equal(M.resolveControl({kind:'described',description:'Run the three implementation checks.'}).supported,false);assert.equal(M.resolveRepresentation({kind:'described',description:'GP29'}).supported,false);
  assert.equal(M.resolveControl({kind:'implementation-sanity-v2'}).state,'planned');assert.equal(M.resolveRepresentation({kind:'gp29'}).maximum,28);
 });
 await test('short reader summaries preserve unknown requirements and never promise scientific results',()=>{
  const unknown={kind:'described',description:'Compare a predeclared null model, including the specified threshold.'};assert.equal(M.summarizeEvaluation(unknown),unknown.description);
  assert.match(M.summarizeEvaluation({kind:'output-measurements'}),/cannot establish/);assert.match(M.summarizeEvaluation({kind:'exact-prefix',values:[0]}),/not a complete reading/);assert.match(M.summarizeEvaluation({kind:'exact-prefix-set',openings:[{id:'one',values:[0]}]}),/not a complete reading/);assert.match(M.summarizeEvaluation(M.LANGUAGE_CRITERION),/not a translation/);
 });
 await test('aggregate named metrics and boundary semantics agree with invented actual V2 result',async()=>{
  const alphabet=require('../data/local-run-inputs.json').alphabet,A=alphabet[0].rune,B=alphabet[1].rune;
  const task=await V.prepare({title:'Invented typed measurement contract',alphabet,pages:[{id:'lp2-00',text:A+'!'+A+'\n'+B},{id:'lp2-01',text:B+B}],steps:[],criterion:M.resolveEvaluation({kind:'output-measurements'})},webcrypto),result=V.run(task);
  assert.deepEqual(Object.keys(result.metrics).sort(),[...M.FACTS.measurements.fields].sort());assert.deepEqual(result.metrics,{pages:2,runes:5,adjacentPairs:3,equalAdjacentPairs:2,ioc:0.4});
  assert(!Object.hasOwn(result.metrics,'histogram'));assert(!Object.hasOwn(result.metrics,'pagesMetrics'));assert.match(M.describeEvaluation({kind:'output-measurements'}),/aggregate/);assert.match(M.describeEvaluation({kind:'output-measurements'}),/no pair crosses a page boundary/);
 });
 await test('standard control choice means planned independent synthetic suite, never already passed or scientific null',async()=>{
  const alphabet=require('../data/local-run-inputs.json').alphabet,task=await V.prepare({title:'Invented contract collapse control',alphabet,pages:[{id:'lp2-00',text:alphabet[0].rune.repeat(3)}],steps:[{op:'collapse-adjacent-repeats',unit:'word',policy:'all-but-first'}],criterion:{kind:'measurement'}},webcrypto);
  const fact=M.resolveControl({kind:'implementation-sanity-v2'}),suite=await Controls.prepare(task,webcrypto);await Controls.validate(suite,task,webcrypto);assert.equal(suite.version,fact.referenceVersion);assert.deepEqual(suite.cases.map(c=>c.id),fact.caseIds);assert.equal(fact.state,'planned');assert(!Object.hasOwn(fact,'passed'));assert.match(fact.limit,/not a scientific null/);
 });
 await test('strict literal bounds, exact pins and unique openings reject unsupported aliases and hidden conditions',()=>{
  for(const input of [{kind:'measurement'},{kind:'output-measurements',significance:true},{kind:'exact-prefix',values:[]},{kind:'exact-prefix',values:[29]},{kind:'exact-prefix',values:[0.5]},{kind:'exact-prefix',values:Array(257).fill(0)},{kind:'exact-prefix-set',openings:[{id:'one',values:[0]},{id:'one',values:[1]}]},{kind:'exact-prefix-set',openings:[{id:'one',values:[0]},{id:'two',values:[0]}]},{kind:'exact-prefix-set',openings:[{id:'one\n',values:[0]}]},{...Language.criterion(),modelSha256:'0'.repeat(64)},{...Language.criterion(),extra:true},null])assert.throws(()=>M.validateEvaluation(input));
  assert.equal(M.validateEvaluation({kind:'exact-prefix',values:Array(256).fill(28)}).values.length,256);
  for(const input of [{kind:'implementation-sanity-v2',passed:true},{kind:'other'},null])assert.throws(()=>M.validateControl(input));
  for(const input of [{kind:'gp29',normalization:'fold'},{kind:'other'},null])assert.throws(()=>M.validateRepresentation(input));
 });
 await test('description limits, Unicode and accessors are strict and returned values are detached immutable JSON',()=>{
  for(const [validate,max] of [[M.validateEvaluation,500],[M.validateControl,400],[M.validateRepresentation,160]]){assert.equal(validate({kind:'described',description:'🧩'.repeat(max)}).description.length,max*2);for(const description of ['', ' ', 'x'.repeat(max+1),'bad\nline','\ud800'])assert.throws(()=>validate({kind:'described',description}));}
  let touched=0;const getter={kind:'exact-prefix'};Object.defineProperty(getter,'values',{enumerable:true,get(){touched++;return [0];}});assert.throws(()=>M.validateEvaluation(getter));assert.equal(touched,0);
  const original={kind:'exact-prefix-set',openings:[{id:'one',values:[0]}]},validated=M.validateEvaluation(original);original.openings[0].values[0]=1;assert.equal(validated.openings[0].values[0],0);assert(Object.isFrozen(validated.openings[0].values));assert(Object.isFrozen(M.FACTS.measurements.fields));assert(Object.isFrozen(M.EVALUATION_SCHEMA));
 });
 await test('UMD capability descriptions resolve without runner, I/O or target execution',()=>{
  const context={FiniteJSON:J,TextEncoder};vm.runInNewContext(fs.readFileSync(require.resolve('../method-check-contract.js'),'utf8'),context);const browser=context.MethodCheckContract;
  assert.equal(Object.hasOwn(context,'RuneLanguageScore'),false);assert.equal(JSON.stringify(browser.resolveEvaluation(M.LANGUAGE_CRITERION)),JSON.stringify(Language.criterion()));
  assert.equal(JSON.stringify(browser.resolveEvaluation({kind:'output-measurements'})),JSON.stringify(M.resolveEvaluation({kind:'output-measurements'})));assert.equal(browser.describeControl({kind:'implementation-sanity-v2'}),M.describeControl({kind:'implementation-sanity-v2'}));assert.equal(browser.resolveEvaluation({kind:'described',description:'An unimplemented evaluation'}),null);
 });
 console.log(groups+' method-check-contract groups passed; invented computations only, no source fetch or persistence.');
})().catch(error=>{console.error(error);process.exitCode=1;});
