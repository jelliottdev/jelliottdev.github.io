'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),Runtime=require('../research-help-runtime.js');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 let active=0,max=0,started=0,destroyed=0;const releases=[],states=[];
 const tools={createController({onState}){return {activate(){active++;started++;max=Math.max(max,active);return new Promise(resolve=>releases.push(()=>{active--;onState({state:'results'});resolve({state:'results'});}));},retry(){return this.activate();},destroy(){destroyed++;}};}};
 const runtime=Runtime.create({load:async()=>tools}),controllers=Array.from({length:5},()=>runtime.createReadiness({record:{},check:{},onState:value=>states.push(value)})),pending=controllers.map(c=>c.activate());
 await tick();assert.equal(started,2);controllers[2].destroy();releases.shift()();await tick();assert.equal(started,3);releases.shift()();await tick();assert.equal(started,4);assert.equal(max,2);
 while(releases.length){releases.shift()();await tick();}await Promise.all(pending);assert.equal(started,4);assert.equal(states.filter(s=>s.state==='results').length,4);
 runtime.destroy();assert.equal(destroyed,4);assert.equal(await controllers[0].retry(),null);
 // A shared loader is the production path; closing settles the queued probes.
 let resolveLoad;const dependency=new Promise(r=>resolveLoad=r),shared=Runtime.create({load:()=>dependency}),seen=[],items=Array.from({length:4},()=>shared.createReadiness({onState:s=>seen.push(s)})),work=items.map(c=>c.activate());await tick();shared.destroy();resolveLoad(tools);await Promise.all(work);assert.deepEqual(seen.map(s=>s.state),['loading','loading','loading','loading']);
 let attempts=0;const retry=Runtime.create({load:async()=>{if(++attempts===1)throw Error('offline');return {createController({onState}){return {activate(){onState({state:'answered'});return Promise.resolve({state:'answered'});},retry(){return this.activate();},destroy(){}};}};}}),observed=[],c=retry.createReadiness({onState:s=>observed.push(s)});assert.equal(await c.activate(),null);assert.equal((await c.retry()).state,'answered');retry.destroy();assert.deepEqual(observed.map(s=>s.state),['loading','unavailable','loading','answered']);
 assert.throws(()=>Runtime.create({load:()=>{},limit:3}));
 const reads=new Map();let sourceSignal;const cached=Runtime.create({load:async()=>({createController({loadConfig,loadInputs,onState}){return {async activate(){assert.deepEqual(await loadConfig(),{kind:'data/assistant.json'});assert.deepEqual(await loadInputs(),{kind:'data/local-run-inputs.json'});onState({state:'results'});},retry(){return this.activate();},destroy(){}};}}),fetcher:async(path,options)=>{sourceSignal=options.signal;reads.set(path,(reads.get(path)||0)+1);return new Response(JSON.stringify({kind:path}));}}),cachedItems=Array.from({length:4},()=>cached.createReadiness({onState(){}}));await Promise.all(cachedItems.map(c=>c.activate()));assert.deepEqual([...reads.values()],[1,1]);cached.destroy();assert(sourceSignal.aborted);
 const html=fs.readFileSync('research.html','utf8');assert(html.indexOf('research-help-runtime.js')<html.indexOf('research-browser.js'));
 const source=fs.readFileSync('research-browser.js','utf8');assert(source.includes("dialog.addEventListener('close',clearHelp)"));assert(source.includes('runtime.destroy()'));
 console.log('PASS chooser lookup concurrency, queued cancellation, close during dependency load, retry and lifecycle integration');
 const context={URL,Map,Promise,location:{href:'https://liberpedia.test/research.html'},setTimeout,clearTimeout,document:{createElement(){return {remove(){}};},head:{appendChild(script){const file=new URL(script.src).pathname.slice(1);queueMicrotask(()=>{try{vm.runInContext(fs.readFileSync(file,'utf8'),context,{filename:file});script.onload();}catch(error){console.error(error);script.onerror();}});}}}};vm.createContext(context);
 for(const file of ['followup-context.js','record-question-runtime.js'])vm.runInContext(fs.readFileSync(file,'utf8'),context,{filename:file});
 assert.equal(context.FollowupReadiness,undefined);const loaded=await context.RecordQuestionRuntime.loadReadiness();assert.equal(typeof loaded.createController,'function');assert.equal(loaded,await context.RecordQuestionRuntime.loadReadiness());
 console.log('PASS actual lazy browser readiness modules initialize in order without mounting run workspace');
})().catch(error=>{console.error(error);process.exitCode=1;});
