import {createRequire} from 'node:module';
import vm from 'node:vm';
import Protocols from '../../experiment-protocols.js';
import {createHash} from 'node:crypto';
/* Deterministic planner: real SQLite, fixed injected pages, no AI/network. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {createPrepareTaskHandler,planCard} from './prepare-task.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
import PlanControls from '../../local-plan-controls.js';
import {fromWire} from './interpret-handler.mjs';
import {SCHEMA,toDraft} from './interpretation.mjs';
import {validateCandidate as validatePlanCandidate} from './propose-task-plan.mjs';
let id;
const origin='https://jelliottdev.github.io',parent='b'.repeat(64),at='2026-10-24T12:00:00.000Z';
const index=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8'));
const alphabet=index.alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const raw=alphabet.slice(0,3).map(r=>r.rune).join('')+' '+alphabet[0].rune,reviewed=raw+'\n'+alphabet[2].rune;
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
function card(extra={}){return H.cardData(C.confirm(C.createDraft({source:{text:'PRIVATE original idea'},aim:known('solve LP2'),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'}]}),scope:known({pages:['lp2-15']}),...extra,rules:{evaluation:known('measurement'),...extra.rules}}),{id:'test',at}));}
function fixture(data=card(),options={}){
 const sqlite=new DatabaseSync(':memory:');for(const migration of readdirSync(new URL('./migrations/',import.meta.url)).filter(name=>/^\d{4}_.*\.sql$/.test(name)).sort())sqlite.exec(readFileSync(new URL('./migrations/'+migration,import.meta.url),'utf8'));
 const cardHash=createHash('sha256').update(C.serialize(data)).digest('hex');id='p_'+cardHash;
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,cardHash,C.serialize(data),'unused',at);
 let reads=0,calls=0;const urls=[],rate=[];
 const env={SITE_ORIGIN:origin,PROPOSALS:{prepare(sql){assert(!sql.includes('original_idea'));assert(!sql.includes('proposal_submissions'));return {bind(...args){return {first:async()=>{reads++;return sqlite.prepare(sql).get(...args)||null;},all:async()=>{reads++;return {results:sqlite.prepare(sql).all(...args)};},run:async()=>sqlite.prepare(sql).run(...args)};}};}},PROPOSAL_LIMIT:{limit:async value=>{rate.push(value);return {success:true};}},AI:{run(){throw Error('Planner must not call AI');}}};
 const handle=createPrepareTaskHandler({now:()=>new Date(at),...(options.prepareControls?{prepareControls:options.prepareControls}:{}),fetcher:async(url,options)=>{calls++;urls.push(url);assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'manual');assert(options.signal);return Response.json({id:'lp2-15',raw,reviewed_text:reviewed});}});
 return {sqlite,env,handle,urls,rate,get reads(){return reads;},get calls(){return calls;}};
}
const request=(body={proposalId:id,parentTaskId:null},extra={})=>new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin,'content-type':'application/json','CF-Connecting-IP':'203.0.113.9',...extra},body:JSON.stringify(body)});
async function submit(f,body){const response=await f.handle(request(body),f.env);return {response,value:await response.json()};}
let count=0;async function test(name,fn){await fn();console.log('PASS '+name);count++;}
await test('deciphering requires an explicit evaluation before AI, source loading or task creation',async()=>{
 for(const evaluation of [C.field(),C.field('not_applicable'),C.field('unrestricted')]){
  const input=card({rules:{evaluation}}),before=structuredClone(input),plan=planCard(input);assert.equal(plan.state,'needs-clarification');assert.equal(plan.field,'evaluation');assert.deepEqual(input,before);
  const f=fixture(input),{response,value}=await submit(f);assert.equal(response.status,200);assert.deepEqual(value,{state:'needs-clarification',proposalId:id,field:'evaluation',reason:'Choose what this experiment should check before preparing it.'});assert.equal(f.calls,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM idea_computation_evidence').get().n,0);
 }
});
await test('readability requests stay unsupported rather than becoming measurements or prefixes',async()=>{
 for(const aim of ['solve LP2','Measure the output']){
  const input=card({aim:known(aim),rules:{evaluation:known({kind:'readability'})}}),before=structuredClone(input),plan=planCard(input);assert.equal(plan.state,'needs-adapter');assert.match(plan.reason,/Readable-text evaluation is not available/);assert.deepEqual(input,before);
  const f=fixture(input),{value}=await submit(f);assert.equal(value.state,'needs-adapter');assert.match(value.reason,/not been tested for readable text/);assert.equal(f.calls,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);
 }
 const inspect=card({rules:{evaluation:known('measurement')}}),snapshot=structuredClone(inspect),f=fixture(inspect),{value}=await submit(f);assert.equal(value.state,'plan-ready');assert.deepEqual(value.task.criterion,{kind:'measurement'});assert.deepEqual(inspect,snapshot);assert.equal(inspect.outcome.value.outcomeId,'decipher');assert(value.notes.some(note=>note.includes('not a test of whether the output is readable')));
 const descriptive=card({aim:known('Measure the output'),rules:{evaluation:C.field()}});assert(!planCard(descriptive).reason,'Existing descriptive aims retain their explicit proposed measurement behavior');
});
await test('definition-derived measurements agree in browser and backend compilers with exact legacy titles and notes',async()=>{
 const frontendSource=readFileSync(new URL('../../record-followups.js',import.meta.url),'utf8'),needle='const api={reference,validateOrigins,createWorkspace}';assert(frontendSource.includes(needle));
 const context={module:{exports:{}},require:createRequire(new URL('../../record-followups.js',import.meta.url)),btoa,TextEncoder,crypto};vm.createContext(context);vm.runInContext(frontendSource.replace(needle,'const api={cardProgram,reference,validateOrigins,createWorkspace}'),context);
 const criteria=[];
 for(const boundaries of ['non-rune','hyphen-period']){
  for(const table of ['canonical','reversed'])criteria.push({kind:'word-prime-sums',table,boundaries});
  for(const lag of [1,12])for(const a of [0,28])for(const b of [0,28])criteria.push({kind:'word-affine-count',lag,a,b,boundaries});
 }
 for(const criterion of criteria){
  const definition=Protocols.identify(criterion),description=Protocols.describe(criterion),{kind,...parameters}=criterion;
  assert(definition);const operation={id:definition.operation.id,label:definition.operation.label,...parameters};
  const input=card({method:known({operations:[operation]}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known(criterion)}}),before=structuredClone(input),plan=planCard(input),browser=context.module.exports.cardProgram(input);
  assert(!plan.reason,plan.reason);assert.deepEqual(plan.criterion,criterion);assert.deepEqual(JSON.parse(JSON.stringify(browser.criterion)),criterion);assert.deepEqual(JSON.parse(JSON.stringify(browser.steps)),plan.steps);assert.deepEqual(JSON.parse(JSON.stringify(browser.pages)),plan.pages);assert.equal(browser.inputVersion,plan.inputVersion);assert(plan.notes.includes(description.compilerNote));assert.deepEqual(input,before);
  const f=fixture(input),{response,value}=await submit(f);assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.equal(value.task.title,description.title);assert.equal(value.task.title,kind==='word-prime-sums'?'Word prime sums · '+criterion.table+' table · '+criterion.boundaries:'Within-word rune pairs · lag '+criterion.lag+' · '+criterion.boundaries);assert.deepEqual(value.task.criterion,criterion);
  if(kind==='word-affine-count'){const noLabel=structuredClone(input);delete noLabel.method.value.operations[0].label;assert.deepEqual(planCard(noLabel).criterion,criterion);assert.deepEqual(JSON.parse(JSON.stringify(context.module.exports.cardProgram(noLabel).criterion)),criterion);}
 }
 for(const definition of Protocols.list()){
  const criterion=definition.id==='word-prime-sums'?{kind:definition.id,table:'canonical',boundaries:'non-rune'}:{kind:definition.id,lag:6,a:27,b:24,boundaries:'non-rune'},operation={id:definition.operation.id,label:definition.operation.label,...Object.fromEntries(Object.entries(criterion).filter(([k])=>k!=='kind'))};
  const base=card({method:known({operations:[operation]}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known(criterion)}});
  for(const mutate of [c=>c.method.value.operations[0].unknown=true,c=>c.method.value.operations[0].label+=' except F',c=>c.method.value.operations[0].boundaries='spaces',c=>c.rules.evaluation.value.boundaries='hyphen-period',c=>c.method.value.operations[0].declaredFamilyId='unmaintained',c=>c.method.value.operations.push({id:'reverse_row_runes'}),c=>c.rules.evaluation.value.unknown=true,...(criterion.kind==='word-prime-sums'?[['table','custom']]:[['lag',0],['lag',13],['a',-1],['a',29],['b',-1],['b',29],['lag',1.5]]).map(([k,v])=>c=>{c.method.value.operations[0][k]=v;c.rules.evaluation.value[k]=v;})]){
   const input=structuredClone(base);mutate(input);let refused=false;try{refused=!!planCard(input).reason;}catch{refused=true;}assert(refused);assert.throws(()=>context.module.exports.cardProgram(input));
   const f=fixture(input);let ai=0;f.env.AI.run=()=>{ai++;throw Error('No canonical downgrade');};const {value}=await submit(f);assert.notEqual(value.state,'plan-ready');assert.equal(f.calls,0);assert.equal(ai,0);
  }
 }
});
await test('hosted Welcome wording maps numeric key and exact reset prose through interpretation to reviewed plan',async()=>{
 const text='Reproduce the Welcome opening on LP1-03 using Vigenere with key indices [23,10,1,10,9,10,16,26], subtract, reset at each page.';
 const evidence=quote=>({start:text.indexOf(quote),quote}),phrase=text.slice(text.indexOf('using'));
 const wire={schema:SCHEMA,outcome:{id:'reproduce',source:evidence('Reproduce the Welcome opening')},steps:[{id:'described_method',familyId:'polyalphabetic',source:evidence(phrase)}],scope:{source:evidence('LP1-03'),passage:null},rules:[{name:'reset',source:evidence('reset at each page')}]};
 const interpreted=fromWire(wire,text);assert.deepEqual(interpreted.steps[0].parameters,{});assert.equal(interpreted.steps[0].source.quote,phrase);
 const active=H.cardData(C.confirm(toDraft(text,interpreted).draft,{id:'reviewed-hosted-fixture',at})),before=structuredClone(active);
 assert.equal(active.rules.reset.value,'reset at each page');assert(!Object.hasOwn(active.method.value.operations[0],'key'));
 const step={op:'keyed-shift',key:[23,10,1,10,9,10,16,26],mode:'repeat',direction:'subtract',reset:'page'};
 const mapped=validatePlanCandidate(active,{version:1,steps:[{source:{operationIndex:0,start:0,quote:phrase},step}],unsupported:[]},{compile:planCard});
 assert(!mapped.reason,mapped.reason);assert.deepEqual(mapped.plan.steps,[step]);assert.deepEqual(mapped.plan.pages,['lp1-03']);assert.equal(mapped.card.rules.reset.value,'reset at each page');assert.equal(mapped.card.outcome.value.outcomeId,'reproduce');assert.deepEqual(active,before);
 for(const reset of ['page','line','word']){
  const operation={id:'vigenere',key:[1,2],direction:'subtract',reset},input=card({method:known({operations:[operation]}),rules:{reset:known('reset at each '+reset)}}),snapshot=structuredClone(input);
  assert.deepEqual(planCard(input).steps,[{op:'keyed-shift',key:[1,2],mode:'repeat',direction:'subtract',reset}]);assert.deepEqual(input,snapshot);
  for(const unsupported of ['unless supplied, reset at each '+reset,'reset at each '+reset+' except F','reset at each '+(reset==='word'?'page':'word')])assert(planCard(card({method:known({operations:[operation]}),rules:{reset:known(unsupported)}})).reason);
 }
});
await test('supported reversal proposes canonical source-bound task without task persistence or inference',async()=>{
 const f=fixture(),{response,value}=await submit(f);assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.match(value.preparation.id,/^prep_[a-f0-9]{64}$/);assert.equal(value.preparation.authority,'idea');assert.equal(value.parentTaskId,null);assert.equal(value.inputVersion,'raw');assert.deepEqual(value.task.alphabet,alphabet);assert.deepEqual(value.task.steps,[{op:'reverse',unit:'line'}]);assert.deepEqual(value.task.pages,[{id:'lp2-15',text:raw}]);await L.checkIdentity(value.task);
 assert(value.notes.some(n=>n.includes('preliminary measurement')));assert(value.notes.some(n=>n.includes('headings')));assert(!JSON.stringify(value).includes('PRIVATE'));assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.rate[0].key,'203.0.113.9');
 const python=readFileSync(new URL('../../scripts/reproduce_reading.py',import.meta.url),'utf8');assert.equal(python.match(/RUNES = "([^"]+)"/)[1],alphabet.map(r=>r.rune).join(''));assert.deepEqual(python.match(/LATIN = "([^"]+)"/)[1].split(' '),alphabet.map(r=>r.latin));
});
await test('preparation stores only an immutable exact admission receipt and is idempotent',async()=>{
 const f=fixture(),first=await submit(f),again=await submit(f);assert.deepEqual(again.value.preparation,first.value.preparation);
 const rows=f.sqlite.prepare('SELECT * FROM prepared_plans').all();assert.equal(rows.length,1);const row=rows[0];
 assert.equal(row.proposal_id,id);assert.equal(row.task_id,first.value.task.taskId);assert.equal(row.input_version,'raw');assert.equal(row.parent_task_id,null);
 assert.deepEqual(JSON.parse(row.basis_json).normalizedCard,card());assert.equal(JSON.parse(row.basis_json).kind,'compiled-card');
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
});
await test('generic preparation includes independently checked controls while keeping target criterion and identity',async()=>{
 const input=card({method:known({operations:[{id:'affine',a:7,b:7}]}),rules:{evaluation:known({kind:'exact-prefix',values:[1,2]})}});
 const f=fixture(input),{value}=await submit(f);assert.equal(value.state,'plan-ready');await PlanControls.validate(value.controls,value.task);
 assert.deepEqual(value.task.criterion,{kind:'exact-prefix',values:[1,2]});
 const same=await L.prepare({title:value.task.title,pages:value.task.pages,alphabet:value.task.alphabet,steps:value.task.steps,criterion:value.task.criterion});
 assert.deepEqual(same,value.task);assert.equal(value.controls.targetId,value.task.taskId);
 assert.equal(L.run(value.controls.cases[0].task).matches[0].matched,true);
 assert.equal(L.run(value.controls.cases[1].task).matches[0].matched,false);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
await test('generic preparation fails closed on failed stale and tampered controls without writing a task',async()=>{
 for(const failure of ['throw','stale','digest']){
  const f=fixture(card(),{prepareControls:async target=>{
   if(failure==='throw')throw Error('Reference disagrees');
   const suite=await PlanControls.prepare(target);
   if(failure==='stale')suite.targetId='f'.repeat(64);else suite.cases[0].expectedResultSha256='0'.repeat(64);
   return suite;
  }}),before=f.sqlite.prepare('SELECT total_changes() n').get().n;
  const {response,value}=await submit(f);assert.equal(response.status,422);assert.equal(value.state,undefined);
  assert.equal(value.error,'The runner checks failed. No experiment was created.');assert.equal(value.task,undefined);assert.equal(value.controls,undefined);
  assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 }
});
await test('ordered explicit affine/feedback/boundary rules and reviewed text remain exact',async()=>{
 const f=fixture(card({method:known({operations:[{id:'affine',a:28,b:3},{id:'cumulative_difference',reset:'word'},{id:'reverse_row_runes'}]}),rules:{boundaryMode:known('within_words'),wordBoundaries:known('preserve'),inputVersion:known('reviewed'),representation:known('GP29'),unmapped:known('preserve'),reset:known('word'),initialState:known(0),evaluation:known({kind:'exact-prefix',values:[1,2]})}}));
 const {value}=await submit(f);assert.equal(value.state,'plan-ready');assert.deepEqual(value.task.steps,[{op:'affine',a:28,b:3},{op:'cumulative-difference',reset:'word'},{op:'reverse',unit:'word'}]);assert.deepEqual(value.task.criterion,{kind:'exact-prefix',values:[1,2]});assert.equal(value.task.pages[0].text,reviewed);assert.equal(value.inputVersion,'reviewed');
});
await test('explicit keyed operations preserve GP indices, direction, resets, evaluation and source version',async()=>{
 for(const [op,label,mode]of [['vigenere','Vigenere','repeat'],['repeating_key','Repeating key','repeat'],['plaintext_autokey','Plaintext autokey','plaintext-autokey'],['ciphertext_autokey','Ciphertext autokey','ciphertext-autokey']]){
  for(const direction of ['subtract','add'])for(const reset of ['page','line','word']){
   const operation={id:op,label,key:[0,1,28],direction,reset},input=card({method:known({operations:[operation]}),rules:{reset:known(reset),inputVersion:known('reviewed'),evaluation:known({kind:'exact-prefix',values:[0,1]})}}),before=structuredClone(input),plan=planCard(input);
   assert(!plan.reason,plan.reason);assert.deepEqual(plan.steps,[{op:'keyed-shift',key:[0,1,28],mode,direction,reset}]);assert.equal(plan.inputVersion,'reviewed');assert.deepEqual(plan.criterion,{kind:'exact-prefix',values:[0,1]});assert.deepEqual(input,before);
  }
 }
 const f=fixture(card({method:known({operations:[{id:'vigenere',label:'Vigenere',key:[1,2,3],direction:'subtract',reset:'page'}]})})),{value}=await submit(f);assert.equal(value.state,'plan-ready');assert(value.task.title.includes('Repeating-key subtraction · 3-rune key · page resets'));assert(!value.task.title.includes('Cumulative'));await L.checkIdentity(value.task);assert.deepEqual(value.task.steps,[{op:'keyed-shift',key:[1,2,3],mode:'repeat',direction:'subtract',reset:'page'}]);assert.equal(f.calls,1);
});
await test('keyed plans reject omitted, guessed and unsupported parameters without source fetch',async()=>{
 const base={id:'vigenere',label:'Vigenere',key:[1,2,3],direction:'subtract',reset:'page'};
 const variants=[...['key','direction','reset'].map(key=>{const o={...base};delete o[key];return o;}),...[[],[29],[-1],[1.5],Array(257).fill(1),'ABC'].map(key=>({...base,key})),...['skip','phase','carry','mode'].map(key=>({...base,[key]:1})),{...base,label:'Vigenere except F'},{...base,a:1}];
 for(const operation of variants){const f=fixture(card({method:known({operations:[operation]})})),{value}=await submit(f);assert.equal(value.state,'needs-adapter');assert.equal(f.calls,0);}
 for(const rules of [{reset:known('word')},{initialState:known(0)},{exceptionalCases:known('Skip F')},{searchProtocol:known('Carry between pages')}])assert(planCard(card({method:known({operations:[base]}),rules})).reason);
 assert(planCard(card({method:known({operations:[{id:'reverse_row_runes',key:[1]}]})})).reason);
});
await test('explicit unrestricted choices and inapplicable consumed state never become a fixed plan',async()=>{
 for(const key of C.RULES){const input=card({rules:{[key]:C.field('unrestricted')}}),before=structuredClone(input);assert(planCard(input).reason,key);assert.deepEqual(input,before);const f=fixture(input),{value}=await submit(f);assert.equal(value.state,key==='evaluation'?'needs-clarification':'needs-adapter',key);assert.equal(f.calls,0);}
 for(const operation of [{id:'cumulative_difference',reset:'page'},{id:'vigenere',key:[1],direction:'subtract',reset:'page'}]){
  const input=card({method:known({operations:[operation]}),rules:{reset:C.field('not_applicable')}});assert(planCard(input).reason);assert.equal((await submit(fixture(input))).value.state,'needs-adapter');
 }
 assert(planCard(card({method:known({operations:[{id:'cumulative_difference',reset:'page'}]}),rules:{initialState:C.field('not_applicable')}})).reason);
 const ordinary=card({rules:{exceptionalCases:C.field('not_applicable'),searchBounds:C.field('not_applicable'),reset:C.field('not_applicable'),initialState:C.field('not_applicable')}}),before=structuredClone(ordinary),planned=planCard(ordinary);assert(!planned.reason,planned.reason);assert.deepEqual(ordinary,before);assert.equal(planned.inputVersion,'raw');assert.deepEqual(planned.criterion,{kind:'measurement'});
 const unknown=card({method:known({operations:[{id:'cumulative_difference',reset:'page'}]})});assert(!planCard(unknown).reason,'Unspecified reset and initial state can retain explicit proposed defaults');
});
await test('opaque, incomplete, passage and unhandled consequential rules require adapter before fetching',async()=>{
 const inputs=[
  card({method:known({operations:[{id:'vigenere',key:'FOO'}]})}),
  card({method:known({operations:[{id:'affine',a:2}]})}),
  card({method:known({operations:[{id:'cumulative_difference'}]})}),
  card({method:known({operations:[{id:'reverse_row_runes',label:'Reverse rows except the heading'}]})}),
  card({scope:C.field()}),card({scope:known({pages:['lp2-15'],description:'Only lines 2–3'})}),
  card({unresolved:[{kind:'unknown',text:'Skip some positions'}]}),
  ...Object.entries({exceptionalCases:'Except the heading',searchBounds:{keys:['ABC']},searchProtocol:'shuffle 2000 times',representation:'decimal primes',evaluation:'English readability',inputVersion:'another text',boundaryMode:'word_blocks',reset:'line',initialState:4}).map(([key,value])=>card({rules:{[key]:known(value)}})),
  card({method:known({operations:[{id:'cumulative_difference',reset:'word'}]}),rules:{reset:known('line')}}),
  card({method:known({operations:[{id:'reverse_row_runes',key:'SECRET'}]})})];
 for(const c of inputs){const f=fixture(c),{value}=await submit(f);assert.equal(value.state,'needs-adapter',JSON.stringify(c));assert.equal(f.calls,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);}
});
await test('strict route/method/origin/fields/bounds, configuration and rate protect DB',async()=>{
 const f=fixture();for(const extra of [{origin:'https://evil.example'},{origin:''}])assert.equal((await f.handle(request(undefined,extra),f.env)).status,403);
 assert.equal((await f.handle(new Request('https://worker.example/prepare-task',{headers:{origin}}),f.env)).status,405);
 assert.equal((await f.handle(new Request('https://worker.example/other',{headers:{origin}}),f.env)).status,404);
 assert.equal((await f.handle(request(undefined,{'content-type':'text/plain'}),f.env)).status,400);
 assert.equal((await f.handle(request(undefined,{'content-length':'32001'}),f.env)).status,400);
 for(const b of [{proposalId:id},{proposalId:id,parentTaskId:null,extra:true},{proposalId:'wrong',parentTaskId:null}])assert.equal((await submit(f,b)).response.status,400);
 assert.equal((await f.handle(request(),{...f.env,PROPOSAL_LIMIT:{limit:async()=>({success:false})}})).status,429);assert.equal(f.reads,0);
 assert.equal((await f.handle(request(),{...f.env,PROPOSALS:null})).status,503);
 const pre=new Request('https://worker.example/prepare-task',{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}});assert.equal((await f.handle(pre,f.env)).status,204);
});
await test('pure card planner and task-specific rate binding share production validation',async()=>{
 const input=card(),copy=structuredClone(input),plan=planCard(input);assert.deepEqual(input,copy);assert.deepEqual(plan.steps,[{op:'reverse',unit:'line'}]);assert.equal(plan.inputVersion,'raw');
 assert.throws(()=>planCard({...input,version:999}));
 const f=fixture();let limited=0;
 const env={...f.env,TASK_LIMIT:{limit:async()=>{limited++;return {success:true};}},PROPOSAL_LIMIT:{limit:async()=>{throw Error('Wrong limiter');}}};
 assert.equal((await f.handle(request(),env)).status,200);assert.equal(limited,1);
});
await test('multi-page loading stays at four workers with a shared cancellation signal',async()=>{
 const pages=Array.from({length:9},(_,i)=>'lp2-'+String(i).padStart(2,'0')),f=fixture(card({scope:known({pages})}));let active=0,max=0;const signals=[];
 const handle=createPrepareTaskHandler({fetcher:async(url,options)=>{assert.match(url,/^https:\/\/jelliottdev\.github\.io\/data\/pages\/lp2-0[0-8]\.json$/);signals.push(options.signal);active++;max=Math.max(max,active);await new Promise(resolve=>setTimeout(resolve,1));active--;return Response.json({id:url.split('/').pop().slice(0,-5),raw});}});
 const response=await handle(request(),f.env),value=await response.json();assert.equal(value.state,'plan-ready');assert.equal(max,4);assert(signals.every(signal=>signal===signals[0]));assert.deepEqual(value.task.pages.map(p=>p.id),pages);
});
await test('missing references and source fetch failures are recoverable, no task stored',async()=>{
 const f=fixture();assert.equal((await submit(f,{proposalId:'p_'+'c'.repeat(64),parentTaskId:null})).response.status,404);assert.equal((await submit(f,{proposalId:id,parentTaskId:parent})).response.status,404);
 const handle=createPrepareTaskHandler({fetcher:async()=>Response.json({id:'lp2-15',reviewed_text:reviewed})});assert.equal((await handle(request(),f.env)).status,422);
 const tooLarge=createPrepareTaskHandler({fetcher:async()=>Response.json({id:'lp2-15',raw:'X'.repeat(524289)})});assert.equal((await tooLarge(request(),f.env)).status,422);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
await test('official-source redirects cannot turn a valid AI mapping into an accepted plan',async()=>{
 const f=fixture(card({method:known({operations:[{id:'described_method',label:'please reverse every row'}]})}));let calls=0,aiCalls=0;
 const handle=createPrepareTaskHandler({fetcher:async(url,options)=>{calls++;assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'manual');return new Response(null,{status:302,headers:{location:'https://untrusted.example/page.json'}});}});
 const env={...f.env,AI:{run:async()=>{aiCalls++;return {choices:[{message:{content:JSON.stringify({version:1,steps:[{source:{operationIndex:0,start:7,quote:'reverse every row'},step:{op:'reverse',unit:'line'}}],unsupported:[]})}}]};}}};
 const response=await handle(request(),env),value=await response.json();assert.equal(aiCalls,1);assert.equal(calls,1,'No redirect destination is fetched');assert.equal(response.status,422);assert(!value.task);assert.notEqual(value.state,'plan-ready');assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
});
await test('large exact scopes use one aggregate fetch and preserve raw/reviewed text without fallback',async()=>{
 const ids=[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))];
 const pages=Array.from({length:55},(_,i)=>'lp2-'+String(i).padStart(2,'0'));
 const bundle={schema:'liberpedia-local-inputs-v1',alphabet,pages:ids.map((id,i)=>({id,raw:raw+'  \r\n'+i,reviewed_text:id==='lp1-00'?null:id==='lp2-00'?'':reviewed+'\r\n '+i}))};
 for(const version of ['raw','reviewed']){
  const f=fixture(card({scope:known({pages}),rules:{inputVersion:known(version)}}));let calls=0;
  const handle=createPrepareTaskHandler({fetcher:async(url,options)=>{calls++;assert.equal(url,origin+'/data/local-run-inputs.json');assert.equal(options.redirect,'manual');assert(options.signal);return Response.json(bundle);}});
  const response=await handle(request(),f.env),value=await response.json();assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.equal(calls,1,'55 pages must not incur55 subrequests');assert.deepEqual(value.task.alphabet,alphabet);assert.deepEqual(value.task.pages,pages.map(id=>({id,text:bundle.pages.find(p=>p.id===id)[version==='raw'?'raw':'reviewed_text']})));await L.checkIdentity(value.task);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 }
 for(const failure of ['null-reviewed','missing-reviewed','changed-alphabet','redirect','oversize']){
  const f=fixture(card({scope:known({pages}),rules:{inputVersion:known('reviewed')}})),altered=structuredClone(bundle);let calls=0;
  if(failure==='null-reviewed')altered.pages.find(p=>p.id==='lp2-00').reviewed_text=null;
  if(failure==='missing-reviewed')delete altered.pages.find(p=>p.id==='lp2-00').reviewed_text;
  if(failure==='changed-alphabet')altered.alphabet[0].latin='Different';
  const handle=createPrepareTaskHandler({fetcher:async url=>{calls++;assert.equal(url,origin+'/data/local-run-inputs.json');return failure==='redirect'?new Response(null,{status:302,headers:{location:'https://evil.example/source'}}):failure==='oversize'?new Response('{}',{headers:{'content-type':'application/json','content-length':'2097153'}}):Response.json(altered);}});
  const response=await handle(request(),f.env),value=await response.json();assert.equal(response.status,422,failure);assert(!value.task);assert.equal(calls,1,'Rejected aggregate never falls back to individual pages');assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 }
});
await test('explicit language comparison preserves decipher aim and compiles without measurement substitution',async()=>{
 const evaluator=(await import('../../output-evaluators.js')).default,criterion=evaluator.criterion();
 const input=card({rules:{evaluation:known(criterion)}}),before=structuredClone(input),plan=planCard(input);
 assert.deepEqual(plan.criterion,criterion);assert.deepEqual(plan.steps,[{op:'reverse',unit:'line'}]);assert.deepEqual(input,before);
 assert(plan.notes.some(note=>note.includes('does not identify the language')));
 const f=fixture(input),{response,value}=await submit(f);assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.deepEqual(value.task.criterion,criterion);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
 await PlanControls.validate(value.runnerControls||value.controls,value.task);
 const changed=card({rules:{evaluation:known({...criterion,modelSha256:'0'.repeat(64)})}});assert.equal(planCard(changed).state,'needs-adapter');
});
console.log('PASS '+count+' deterministic prepare-task groups; all source fetches mocked, no AI/task writes/deployment.');
