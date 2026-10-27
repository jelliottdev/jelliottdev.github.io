/* Explicit proposals only. Literal examples use invented inputs, never manuscript transformations. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{createHash,webcrypto}=require('node:crypto'),Start=require('../repeat-removal-start.js'),MD=require('../method-design.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),Description=require('../declarative-program-description.js'),V=require('../declarative-rune-program.js'),J=require('../finite-json.js');
const alphabet=require('../data/local-run-inputs.json').alphabet,A=alphabet[0].rune,field=value=>C.field('specified',value),settings=(unit='word',policy='all-but-first')=>({unit,policy,pages:['lp2-00','lp2-01'],inputVersion:'raw'});
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('all six explicit settings produce precise independent proposed procedure and exact typed step',()=>{
  for(const unit of ['word','line','page'])for(const policy of ['all-but-first','non-overlapping-pairs']){
   const result=Start.propose(settings(unit,policy)),p=result.proposal;assert.equal(p.schema,MD.TYPED_SCHEMA);assert.equal(p.name,'Remove repeated runes');assert.deepEqual(result.programSteps,[{op:'collapse-adjacent-repeats',unit,policy}]);assert.equal(p.steps.length,1);assert(!/report|score|significance|hypothesis/i.test(p.steps[0]));assert.deepEqual(p.keyUse,{kind:'not-used',material:'',application:''});assert.deepEqual(p.representation,{kind:'gp29'});assert.deepEqual(p.evaluation,{kind:'original-output-measurements'});assert.deepEqual(p.controls,[{kind:'implementation-sanity-v2'}]);assert.deepEqual(p.parameters,[]);assert.match(p.assumptions[0],/not a procedure stated by the original author/);assert.match(p.steps[0],/Keep all non-rune/);
   const task={schema:V.TASK,engine:V.ENGINE,taskId:'0'.repeat(64),title:p.name,alphabet,pages:[{id:'lp2-00',text:''}],steps:result.programSteps,criterion:{kind:'measurement'}},description=Description.describe(task);assert.equal(description.steps[0].repeatExample,policy==='all-but-first'?'AAA → A':'AAA → AA');assert.equal(Start.OPTIONS.policies.find(v=>v.value===policy).example,description.steps[0].repeatExample);
   assert.equal(/Every non-rune starts/.test(p.steps[0]),unit==='word');assert.equal(/carriage return or line feed/.test(p.steps[0]),unit==='line');assert.equal(/Ignore retained spaces, punctuation and line breaks/.test(p.steps[0]),unit==='page');assert(Object.isFrozen(result.programSteps[0]));
  }
 });
 await test('explicit ordered scopes and transcription are preserved with no implicit default or narrowing',()=>{
  const ids=require('../data/local-run-inputs.json').pages.map(p=>p.id),all=Start.propose({...settings(),pages:ids,inputVersion:'reviewed'});assert.equal(all.proposal.pages.length,75);assert.deepEqual(all.proposal.pages,ids);assert.equal(all.proposal.inputVersion,'reviewed');
  for(const key of ['unit','policy','pages','inputVersion']){const missing=settings();delete missing[key];assert.throws(()=>Start.propose(missing));}
  for(const patch of [{unit:'guess'},{policy:'guess'},{inputVersion:'current'},{pages:[]},{pages:['lp2-01','lp2-00']},{pages:['lp2-00','lp2-00']},{pages:['lp2-58']},{pages:['lp2-00\n']},{pages:[['lp2-00']]},{pages:ids.concat('lp2-00')},{parentId:'any'}])assert.throws(()=>Start.propose({...settings(),...patch}));
 });
 await test('invented triple and separator outcomes agree with every declared policy and boundary',async()=>{
  for(const unit of ['word','line','page'])for(const policy of ['all-but-first','non-overlapping-pairs']){
   const {programSteps}=Start.propose(settings(unit,policy)),task=await V.prepare({title:'Invented first-observation example',alphabet,pages:[{id:'lp2-00',text:A+A+A+'-'+A+'\n'+A}],steps:programSteps,criterion:{kind:'measurement'}},webcrypto),result=V.run(task);
   const expected=policy==='all-but-first'?(unit==='word'?A+'-'+A+'\n'+A:unit==='line'?A+'-\n'+A:A+'-\n'):(unit==='word'?A+A+'-'+A+'\n'+A:unit==='line'?A+A+'-\n'+A:A+A+'-\n'+A);
   assert.equal(result.transformed[0].text,expected);
  }
 });
 await test('canonical review roundtrip preserves parent original and whole explicitly proposed first check',async()=>{
  const parent=H.cardData(C.confirm(C.createDraft({source:{text:'Could extra runes explain the doubles in a first section?'},aim:field('Investigate the original question')}),{id:'first-observation-parent',at:'2026-10-27T00:00:00.000Z'})),before=C.serialize(parent),parentId='p_'+createHash('sha256').update(before).digest('hex');
  const {proposal}=Start.propose(settings()),fragment=await MD.toFragment(proposal,{parentId,parentCard:parent},webcrypto),draft=H.decode(fragment).draft;assert.equal(draft.status,'draft');assert.deepEqual(MD.readDraft(draft),{parentId,proposal});assert.equal(C.serialize(parent),before);assert.equal(draft.confirmation,null);
  const saved=H.cardData(C.confirm(draft,{id:'explicit-first-observation',at:'2026-10-27T00:00:00.000Z'}));assert.deepEqual(MD.readCard(saved),{parentId,proposal});assert.deepEqual(saved.scope.value.pages,['lp2-00','lp2-01']);assert.deepEqual(saved.rules.evaluation.value.check,{kind:'original-output-measurements'});
 });
 await test('maintained recipe matching requires exact whole canonical proposal and never guesses modified semantics',()=>{
  assert.equal(Start.RECIPE_VERSION,1);
  for(const unit of ['word','line','page'])for(const policy of ['all-but-first','non-overlapping-pairs'])for(const inputVersion of ['raw','reviewed']){const item=Start.propose({...settings(unit,policy),inputVersion});assert.deepEqual(Start.match(item.proposal),item.programSteps);const reordered=Object.fromEntries(Object.entries(item.proposal).reverse());assert.deepEqual(Start.match(reordered),item.programSteps);}
  const original=Start.propose(settings()).proposal;
  for(const mutate of [p=>p.name+=' with a condition',p=>p.hypothesis+=' A claim.',p=>p.steps[0]+=' Except at headings.',p=>p.steps.reverse().push('Keep a duplicate control rune.'),p=>p.evaluation={kind:'output-measurements'},p=>p.controls[0]={kind:'described',description:'A scientific random-deletion control.'},p=>p.assumptions[0]='This is the original author’s stated method.',p=>p.parameters=[{name:'Which duplicate',values:['first','second']}],p=>p.representation={kind:'described',description:'GP29'},p=>p.keyUse={kind:'proposed',material:'AFTER',application:'Use the key to decide which repetition to remove.'}]){const changed=structuredClone(original);mutate(changed);assert.equal(Start.match(changed),null);}
  assert.equal(Start.match(null),null);assert.equal(Start.match({...original,extra:true}),null);let reads=0;const getter={...original};Object.defineProperty(getter,'steps',{enumerable:true,get(){reads++;return original.steps;}});assert.equal(Start.match(getter),null);assert.equal(reads,0);
  const source=fs.readFileSync(require.resolve('../repeat-removal-start.js'),'utf8').replace('Keep the first rune of each repeated run','A revised display label only').replace("description:'Every non-rune starts a new group, including spaces, punctuation and line breaks.'","description:'Revised display boundary wording only.'"),context={MethodDesign:MD,FiniteJSON:J,TextEncoder};vm.runInNewContext(source,context);assert.deepEqual(JSON.parse(JSON.stringify(context.RepeatRemovalStart.match(original))),Start.match(original));
 });
 await test('pure deterministic builder is detached accessor-safe and UMD has no I/O or execution dependency',()=>{
  const value=settings(),before=JSON.stringify(value),a=Start.propose(value),b=Start.propose(value);assert.deepEqual(a,b);value.pages[0]='lp2-02';assert.deepEqual(a.proposal.pages,['lp2-00','lp2-01']);assert.notEqual(JSON.stringify(value),before);let reads=0;const bad=settings();Object.defineProperty(bad,'policy',{enumerable:true,get(){reads++;return 'all-but-first';}});assert.throws(()=>Start.propose(bad));assert.equal(reads,0);assert(!Object.hasOwn(Start.OPTIONS,'selected'));assert(Object.isFrozen(Start.OPTIONS.units));
  const context={MethodDesign:MD,FiniteJSON:J,TextEncoder};vm.runInNewContext(fs.readFileSync(require.resolve('../repeat-removal-start.js'),'utf8'),context);assert.deepEqual(JSON.parse(JSON.stringify(context.RepeatRemovalStart.propose(settings()))),a);
 });
 console.log(groups+' first repeat-removal check groups passed; explicit proposals, invented examples only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
