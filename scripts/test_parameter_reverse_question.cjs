'use strict';
// Canonical declarations only: retained source text is never transformed here.
const assert=require('node:assert/strict'),fs=require('node:fs'),{spawnSync}=require('node:child_process'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),F=require('../fixed-plan-compiler.js'),Q=require('../task-parameter-question.js'),V=require('../task-parameter-variants.js');
const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')),alphabet=bundle.alphabet,field=value=>C.field('specified',value),units=['page','line','word'];
const cards=[],expected=[],RunView=require('../run.js');
for(const unit of units){const reverse={op:'reverse',unit},atbash={op:'affine',a:28,b:28};assert.equal(RunView.displayTaskTitle({steps:[reverse]},'machine title'),'Reverse rune order within each '+unit);assert.equal(RunView.displayTaskTitle({steps:[reverse,atbash]},'machine title'),'Reverse rune order within each '+unit+', then use the reversed alphabet');for(const steps of [[atbash,reverse],[reverse,{...atbash,b:27}],[reverse,atbash,reverse]])assert.equal(RunView.displayTaskTitle({steps},'unchanged'),'unchanged');}
function planData(card){const value=F.compile(card);assert(!value.reason,value.reason);return {pages:value.pages,steps:value.steps,criterion:value.criterion,inputVersion:value.inputVersion};}
async function check(parentCard,pages){
 const plan=planData(parentCard),parentTask=await E.prepare({title:'An exact original reversal question',alphabet,pages,steps:plan.steps,criterion:plan.criterion},webcrypto),before=E.stable({parentCard,parentTask});
 for(const item of V.list(parentTask).filter(choice=>choice.selection.parameter==='unit')){
  const input={parentCard,parentTask,inputVersion:plan.inputVersion,selection:item.selection},child=await Q.prepare(input,webcrypto);
  assert.deepEqual(await Q.validate(input,child,webcrypto),child);
  assert.deepEqual(child.card.outcome,parentCard.outcome);assert.deepEqual(child.task.pages,parentTask.pages);assert.deepEqual(child.task.criterion,parentTask.criterion);
  const steps=structuredClone(parentTask.steps);steps[item.selection.step].unit=item.selection.value;
  assert.deepEqual(child.task.steps,steps);assert.deepEqual(planData(child.card),{pages:pages.map(page=>page.id),steps,criterion:parentTask.criterion,inputVersion:plan.inputVersion});
  assert.equal(child.card.rules.boundaryMode.status,'unspecified');assert.equal(E.stable({parentCard,parentTask}),before);
  cards.push(child.card);expected.push(planData(child.card));
 }
}
(async()=>{
 const run=E.run,verify=E.verify;E.run=E.verify=()=>assert.fail('Question roundtrips must not transform source text');
 try{
  for(const id of ['lp2-row-column-routes','lp2-word-reversal']){
   const record=JSON.parse(fs.readFileSync('experiments/records/'+id+'/record.json','utf8')),recipe=record.browser_followups[0],plan=planData(recipe.card);
   await check(recipe.card,plan.pages.map(id=>({id,text:bundle.pages.find(page=>page.id===id).raw})));
  }
  assert.equal(cards.length,4);
  for(const unit of units)for(const criterion of [{kind:'measurement'},{kind:'exact-prefix',values:[0,1]},{kind:'exact-prefix-set',openings:[{id:'invented-first',values:[0,1]},{id:'invented-second',values:[2,3]}]}]){
   const card=H.cardData(C.confirm(C.createDraft({source:{text:'Invented reversal question'},aim:field('Solve LP2'),method:field({operations:[{id:'reverse_runes',label:'Reverse rune order within each '+unit,unit},{id:'affine',a:28,b:28}]}),scope:field({pages:['lp2-00','lp2-01']}),rules:{representation:field('GP29'),inputVersion:field('raw'),evaluation:field(criterion.kind==='measurement'?'measurement':criterion)}}),{id:'qa',at:'2026-10-26T00:00:00.000Z'}));
   await check(card,[{id:'lp2-00',text:'ᚠᚢ ᚦ.\r\nᚩᚱ!'},{id:'lp2-01',text:'ᚳ ᚷᚹ'}]);
  }
  assert.equal(cards.length,22);
  const legacy=structuredClone(cards[0]);legacy.method.value.operations[0]={id:'reverse_row_runes',label:'Reverse rune order within rows'};legacy.rules.boundaryMode={status:'specified',value:'fixed_spaces'};
  await check(legacy,[{id:'lp2-00',text:'ᚠᚢ ᚦ.\nᚩᚱ!'}]);
  assert.equal(cards.length,24);
  const python=spawnSync('python',['-c',"import json,sys;sys.path.insert(0,'scripts');from browser_followups import compile_card;print(json.dumps([compile_card(c) for c in json.load(sys.stdin)],ensure_ascii=True))"],{input:JSON.stringify(cards),encoding:'utf8',maxBuffer:4*1024*1024});
  assert.equal(python.status,0,python.stderr||python.error?.message);assert.deepEqual(JSON.parse(python.stdout),expected);
  console.log('PASS 24 canonical reversal variations: both retained source recipes, all six directed units, three criteria, legacy row boundaries and independent Python compilation. No source transformations or writes.');
 }finally{E.run=run;E.verify=verify;}
})().catch(error=>{console.error(error);process.exitCode=1;});
