'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync(require.resolve('../record-question-runtime.js'),'utf8');
const stages=[['finite-sequence-banks.js'],['finite-json.js','local-experiment.js','output-evaluators.js'],['computation-evidence.js','experiment-protocols.js','research-family.js','question-protocols.js','claim-specification.js','local-control.js'],['question-evidence.js','family-question-evidence.js','verified-evidence-client.js','claim-share.js'],['question-decisions.js','record-followups.js'],['task-variants.js'],['record-question-live.js']];
const exportsByFile={'output-evaluators.js':['OutputEvaluators','identify'],'finite-json.js':['FiniteJSON','capture'],'local-experiment.js':['LocalExperiment','checkIdentity'],'computation-evidence.js':['ComputationEvidence','compare'],'experiment-protocols.js':['ExperimentProtocols','describe'],'research-family.js':['ResearchFamily','snapshot'],'question-protocols.js':['QuestionProtocols','definition'],'question-evidence.js':['QuestionEvidence','summarize'],'family-question-evidence.js':['FamilyQuestionEvidence','summarize'],'verified-evidence-client.js':['VerifiedEvidenceClient','create'],'question-decisions.js':['QuestionDecisions','finite'],'task-variants.js':['TaskVariants','validate'],'record-question-live.js':['RecordQuestionLive','createController'],'claim-specification.js':['ClaimSpecification','createDraft'],'local-control.js':['LocalControl','compatible'],'claim-share.js':['ClaimShare','cardData'],'record-followups.js':['RecordFollowups','describeCard']};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
exportsByFile['finite-sequence-banks.js']=['FiniteSequenceBanks','resolve'];
function setup(){
 const appended=[],timers=new Map();let timer=0,throwAppend=false;
 const c={URL,Map,Promise,TextEncoder,TextDecoder,btoa,atob,location:{href:'https://liberpedia.test/sub/library.html#/experiment/one'},setTimeout(fn,delay){assert.equal(delay,10000);timers.set(++timer,fn);return timer;},clearTimeout(id){timers.delete(id);},document:{createElement(tag){assert.equal(tag,'script');return {remove(){this.removed=true;}};},head:{appendChild(script){if(throwAppend)throw Error('append failed');appended.push(script);}}}};
 vm.createContext(c);vm.runInContext(code,c);
 function complete(script,valid=true){script.done=true;const file=new URL(script.src).pathname.split('/').at(-1);if(valid){const [name,method]=exportsByFile[file];c[name]={[method](){}};}script.onload();}
 return {c,appended,timers,complete,setThrow:v=>{throwAppend=v;}};
}
async function finishStages(s,start=0){for(let i=start;i<stages.length;i++){await tick();const stage=s.appended.filter(script=>stages[i].includes(new URL(script.src).pathname.split('/').at(-1))&&!script.done&&!script.removed);assert.equal(stage.length,stages[i].filter(file=>{const [name,method]=exportsByFile[file];return !s.c[name]||typeof s.c[name][method]!=='function';}).length);for(const script of stage){script.done=true;s.complete(script);}}}
(async()=>{
 const s=setup();assert.equal(s.appended.length,0);const first=s.c.RecordQuestionRuntime.load(),second=s.c.RecordQuestionRuntime.load();assert.equal(first,second);assert.equal(s.appended.length,1);
 await finishStages(s);assert.equal(await first,s.c.RecordQuestionLive);assert.equal(s.appended.length,18);assert.equal(s.timers.size,0);
 for(const script of s.appended){const url=new URL(script.src);assert.equal(url.origin,'https://liberpedia.test');assert.equal(url.pathname,'/sub/'+url.pathname.split('/').at(-1));assert.equal(url.search,'?v=20261026-pooled-controls');assert.equal(url.hash,'');assert.equal(script.async,true);assert(!/language|model|data/.test(url.pathname));}
 await s.c.RecordQuestionRuntime.load();assert.equal(s.appended.length,18);console.log('PASS dormant, fixed same-origin assets, staged concurrent loading and completed reuse');
 for(const failure of ['network','timeout','export','append']){
  const f=setup();if(failure==='append')f.setThrow(true);const failed=f.c.RecordQuestionRuntime.load();const reject=assert.rejects(failed,/tools|tool/);
  if(failure==='network')f.appended[0].onerror();if(failure==='timeout')[...f.timers.values()][0]();if(failure==='export')f.complete(f.appended[0],false);
  if(failure!=='append')for(const script of f.appended.slice(1))f.complete(script);await reject;assert.equal(f.timers.size,0);if(failure!=='append')assert.equal(f.appended[0].removed,true);
  f.setThrow(false);const retried=f.c.RecordQuestionRuntime.load();await finishStages(f);assert.equal(await retried,f.c.RecordQuestionLive);console.log('PASS '+failure+' failure is retryable without retaining a rejected dependency');
 }
 const p=setup();const failed=p.c.RecordQuestionRuntime.load();
 for(const stage of stages.slice(0,2)){await tick();const group=p.appended.filter(script=>stage.includes(new URL(script.src).pathname.split('/').at(-1)));assert.equal(group.length,stage.length);for(const script of group)p.complete(script);}
 await tick();const group=p.appended.filter(script=>stages[2].includes(new URL(script.src).pathname.split('/').at(-1)));assert.equal(group.length,stages[2].length);const rejected=assert.rejects(failed);group[0].onerror();for(const script of group.slice(1))p.complete(script);await rejected;
 const retry=p.c.RecordQuestionRuntime.load();await tick();for(const file of stages.slice(0,2).flat())assert.equal(p.appended.filter(x=>new URL(x.src).pathname.endsWith('/'+file)).length,1);await finishStages(p,2);await retry;assert.equal(p.appended.filter(x=>new URL(x.src).pathname.endsWith('/'+stages[2][0])).length,2);assert.equal(p.timers.size,0);console.log('PASS successful earlier dependencies survive a later stage retry');
 const real=setup();vm.runInContext(fs.readFileSync(require.resolve('../record-question-model.js'),'utf8'),real.c);const actual=real.c.RecordQuestionRuntime.load();
 for(const stage of stages){await tick();for(const script of real.appended.filter(script=>stage.includes(new URL(script.src).pathname.split('/').at(-1)))){const file=new URL(script.src).pathname.split('/').at(-1);vm.runInContext(fs.readFileSync(require.resolve('../'+file),'utf8'),real.c,{filename:file});script.onload();}}
 assert.equal(await actual,real.c.RecordQuestionLive);assert.equal(typeof real.c.RecordQuestionLive.createController,'function');assert.equal(real.appended.length,18);
 const bank=JSON.parse(fs.readFileSync(require.resolve('../data/finite-sequence-banks.json'),'utf8')).banks[0];assert.deepEqual(Array.from(real.c.FiniteSequenceBanks.resolve(bank.id,bank.sha256,28)),bank.values.slice(28));assert.throws(()=>real.c.FiniteSequenceBanks.resolve(bank.id,'0'.repeat(64),28));
 assert.equal(new URL(real.appended[0].src).pathname.split('/').at(-1),'finite-sequence-banks.js');assert.equal(real.timers.size,0);console.log('PASS actual browser module exports and trusted sequence bank initialize in the fixed dependency stages');
 for(const finite of [false,true]){
  const r=setup(),loaded=[];const ready=r.c.RecordQuestionRuntime.loadReadiness({finite});let settled=false;ready.then(()=>{settled=true;},()=>{settled=true;});
  assert.deepEqual(r.appended.map(script=>new URL(script.src).pathname.split('/').at(-1)),finite?['finite-sequence-banks.js','repeating-key-banks.js']:['finite-sequence-banks.js']);
  for(let round=0;!settled&&round<30;round++){
   await tick();const pending=r.appended.filter(script=>!script.done&&!script.removed);assert(pending.length>0||settled,'readiness made no progress');
   for(const script of pending){const file=new URL(script.src).pathname.split('/').at(-1);if(file!=='finite-sequence-banks.js')assert.equal(typeof r.c.FiniteSequenceBanks?.resolve,'function','bank must finish before downstream browser modules');vm.runInContext(fs.readFileSync(require.resolve('../'+file),'utf8'),r.c,{filename:file});script.done=true;loaded.push(file);script.onload();}
  }
  assert.equal(await ready,r.c.FollowupReadiness);assert.equal(typeof r.c.FixedPlanCompiler.compile,'function');assert.equal(typeof r.c.RecordFollowups.describeCard,'function');
  assert.equal(loaded[0],'finite-sequence-banks.js');assert(loaded.indexOf('fixed-plan-compiler.js')>0);assert(loaded.indexOf('record-followups.js')>0);assert.equal(loaded.filter(file=>file==='finite-sequence-banks.js').length,1);assert.equal(r.timers.size,0);assert(!loaded.some(file=>/language-model-data|language-score/.test(file)));
  assert.deepEqual(Array.from(r.c.FiniteSequenceBanks.resolve(bank.id,bank.sha256,0)),bank.values);console.log('PASS actual '+(finite?'finite':'fixed')+' readiness loads trusted bank before compiler and followups without language data');
  if(finite){assert(loaded.indexOf('repeating-key-banks.js')<loaded.indexOf('finite-settings.js'));const declaration=vm.runInContext("(()=>{const bank=RepeatingKeyBanks.list()[0],field=v=>ClaimSpecification.field('specified',v),card=ClaimShare.cardData(ClaimSpecification.confirm(ClaimSpecification.createDraft({source:{text:'Private loader fixture'},aim:field('Solve LP2'),method:field({operations:[{id:'repeating_key',direction:'subtract',reset:'page'}]}),scope:field({pages:['lp2-00']}),rules:{evaluation:field('measurement'),searchBounds:field({kind:'finite-settings',version:1,parameters:[{operation:0,name:'key',valuesFrom:{bankId:bank.id,bankSha256:bank.sha256,start:2,count:3}}]})}}),{id:'fixture',at:'2026-10-26T00:00:00.000Z'}));return FiniteSettings.inspect(card);})()",r.c);assert.equal(declaration.parameters[0].values.length,3);assert.equal(loaded.filter(file=>file==='repeating-key-banks.js').length,1);}
 }
 console.log('9 record question runtime groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
